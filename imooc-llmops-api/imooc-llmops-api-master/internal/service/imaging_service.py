#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Read-only planning service for the imaging domain.
"""
import json
import io
import zipfile
import os
import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
from typing import Any
from uuid import UUID
from uuid import uuid5, NAMESPACE_DNS

import requests
from injector import inject
from requests import RequestException
from sqlalchemy import func, inspect

try:
    import numpy as np
    import pydicom
except ImportError:  # pragma: no cover - optional dependency for local demo
    np = None
    pydicom = None

from PIL import Image

from internal.core.imaging import IMAGING_WORKFLOW_TEMPLATES
from internal.model import (
    App,
    Dataset,
    Document,
    Workflow,
    ImagingStudy,
    ImagingSeries,
    ImagingInstance,
    ImagingAiResult,
    ImagingReport,
    ImagingReview,
    ImagingAuditLog,
)
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .cos_service import CosService
from .upload_file_service import UploadFileService


@inject
@dataclass
class ImagingService(BaseService):
    db: SQLAlchemy
    cos_service: CosService
    upload_file_service: UploadFileService
    ALLOWED_UPLOAD_SUFFIXES = {".dcm", ".dicom", ".zip"}

    @staticmethod
    def _storage_mode() -> str:
        return os.getenv("IMAGING_STORAGE_MODE", "local").strip().lower() or "local"

    def _should_use_cos(self) -> bool:
        return self._storage_mode() in {"cos", "hybrid"} and self.cos_service.is_configured()

    @staticmethod
    def _inference_timeout() -> int:
        try:
            return max(int(os.getenv("IMAGING_INFERENCE_TIMEOUT_SECONDS", "120")), 5)
        except ValueError:
            return 120

    @staticmethod
    def _inference_endpoint() -> str:
        endpoint = os.getenv("IMAGING_INFERENCE_ENDPOINT", "").strip()
        if endpoint:
            return endpoint

        base_url = os.getenv("IMAGING_INFERENCE_BASE_URL", "").strip().rstrip("/")
        if not base_url:
            return ""
        return f"{base_url}/v1/imaging/analyze"

    @staticmethod
    def _inference_api_key() -> str:
        return os.getenv("IMAGING_INFERENCE_API_KEY", "").strip()

    @classmethod
    def _real_inference_enabled(cls) -> bool:
        return bool(cls._inference_endpoint())

    @classmethod
    def _inference_headers(cls) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        api_key = cls._inference_api_key()
        if not api_key:
            return headers

        header_name = os.getenv("IMAGING_INFERENCE_API_HEADER", "Authorization").strip() or "Authorization"
        header_scheme = os.getenv("IMAGING_INFERENCE_API_SCHEME", "Bearer").strip()
        headers[header_name] = f"{header_scheme} {api_key}".strip() if header_scheme else api_key
        return headers

    @staticmethod
    def _stringify_dicom_value(value: Any, default: str = "") -> str:
        if value is None:
            return default
        if isinstance(value, (list, tuple)):
            return "\\".join(str(item) for item in value if item is not None) or default
        text = str(value).strip()
        return text or default

    def _extract_zip_archive(self, archive_path: str, target_dir: Path) -> list[Path]:
        extracted_files: list[Path] = []
        target_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.infolist():
                member_path = Path(member.filename)
                if member.is_dir():
                    continue
                if member_path.name.startswith("."):
                    continue

                safe_parts = [part for part in member_path.parts if part not in {"", ".", ".."}]
                if not safe_parts:
                    continue

                destination = target_dir.joinpath(*safe_parts)
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, destination.open("wb") as target:
                    target.write(source.read())
                extracted_files.append(destination)

        return extracted_files

    def _read_dicom_dataset(self, file_path: Path):
        if pydicom is None:
            return None

        try:
            return pydicom.dcmread(str(file_path), stop_before_pixels=True, force=True)
        except Exception:
            return None

    def _build_metadata_from_dataset(self, dataset, file_path: str, file_name: str) -> dict[str, Any]:
        return {
            "parser": "pydicom",
            "parser_status": "parsed",
            "file_name": file_name,
            "file_path": file_path,
            "file_type": Path(file_name).suffix.lower(),
            "patient_id": self._stringify_dicom_value(getattr(dataset, "PatientID", "")),
            "study_instance_uid": self._stringify_dicom_value(getattr(dataset, "StudyInstanceUID", "")),
            "series_instance_uid": self._stringify_dicom_value(getattr(dataset, "SeriesInstanceUID", "")),
            "study_date": self._stringify_dicom_value(getattr(dataset, "StudyDate", "")),
            "study_time": self._stringify_dicom_value(getattr(dataset, "StudyTime", "")),
            "study_description": self._stringify_dicom_value(getattr(dataset, "StudyDescription", "")),
            "series_description": self._stringify_dicom_value(getattr(dataset, "SeriesDescription", "")),
            "modality": self._stringify_dicom_value(getattr(dataset, "Modality", "")),
            "body_part_examined": self._stringify_dicom_value(getattr(dataset, "BodyPartExamined", "")),
            "slice_thickness": self._stringify_dicom_value(getattr(dataset, "SliceThickness", "")),
            "series_number": self._stringify_dicom_value(getattr(dataset, "SeriesNumber", "")),
            "instance_number": self._stringify_dicom_value(getattr(dataset, "InstanceNumber", "")),
            "rows": int(getattr(dataset, "Rows", 0) or 0),
            "columns": int(getattr(dataset, "Columns", 0) or 0),
            "window_center": self._stringify_dicom_value(getattr(dataset, "WindowCenter", "")),
            "window_width": self._stringify_dicom_value(getattr(dataset, "WindowWidth", "")),
            "manufacturer": self._stringify_dicom_value(getattr(dataset, "Manufacturer", "")),
        }

    def _aggregate_series(self, datasets: list[Any]) -> list[dict[str, Any]]:
        series_map: dict[str, dict[str, Any]] = {}

        for dataset in datasets:
            series_uid = self._stringify_dicom_value(getattr(dataset, "SeriesInstanceUID", "")) or "default-series"
            current = series_map.setdefault(
                series_uid,
                {
                    "name": self._stringify_dicom_value(getattr(dataset, "SeriesDescription", "")) or "默认序列",
                    "images": 0,
                    "slice_thickness": self._stringify_dicom_value(getattr(dataset, "SliceThickness", "")),
                    "series_number": self._stringify_dicom_value(getattr(dataset, "SeriesNumber", "")),
                },
            )
            current["images"] += 1

        ordered_items = sorted(
            series_map.values(),
            key=lambda item: (item.get("series_number", ""), item["name"]),
        )

        return [
            {
                "name": item["name"],
                "images": item["images"],
                "slice_thickness": f'{item["slice_thickness"]} mm' if item.get("slice_thickness") else "待补充",
            }
            for item in ordered_items
        ]

    def _build_instance_item(self, dataset, file_path: Path) -> dict[str, Any]:
        return {
            "series_uid": self._stringify_dicom_value(getattr(dataset, "SeriesInstanceUID", "")) or "default-series",
            "series_number": self._stringify_dicom_value(getattr(dataset, "SeriesNumber", "")),
            "series_description": self._stringify_dicom_value(getattr(dataset, "SeriesDescription", "")) or "默认序列",
            "slice_thickness": self._stringify_dicom_value(getattr(dataset, "SliceThickness", "")),
            "orientation": self._stringify_dicom_value(getattr(dataset, "ImageOrientationPatient", "")),
            "sop_instance_uid": self._stringify_dicom_value(getattr(dataset, "SOPInstanceUID", "")),
            "instance_number": self._stringify_dicom_value(getattr(dataset, "InstanceNumber", "")),
            "file_path": str(file_path),
            "window_width": self._stringify_dicom_value(getattr(dataset, "WindowWidth", "")),
            "window_center": self._stringify_dicom_value(getattr(dataset, "WindowCenter", "")),
            "rows": int(getattr(dataset, "Rows", 0) or 0),
            "columns": int(getattr(dataset, "Columns", 0) or 0),
        }

    def _build_inference_payload(self, study: dict[str, Any]) -> dict[str, Any]:
        study_id = str(study.get("id", ""))
        upload = dict(study.get("upload") or {})
        series = self._load_db_series(study_id) if study_id else []
        if not series:
            series = list(study.get("series") or [])

        instance_map = dict(study.get("instances_map") or {})
        if study_id and not instance_map:
            for series_item in series:
                series_id = str(series_item.get("id", "")).strip()
                if series_id and self._has_table("imaging_instance"):
                    instance_map[series_id] = self._load_db_instances(study_id, series_id)

        return {
            "study": {
                "id": study_id,
                "patient_code": study.get("patient_code", ""),
                "patient_name_masked": study.get("patient_name_masked", ""),
                "modality": study.get("modality", ""),
                "body_part": study.get("body_part", ""),
                "study_description": study.get("study_description", ""),
                "study_time": study.get("study_time", 0),
                "priority": study.get("priority", "normal"),
                "status": study.get("status", ""),
                "quality_status": study.get("quality_status", ""),
            },
            "dicom_metadata": dict(study.get("dicom_metadata") or {}),
            "series": series,
            "instances_map": instance_map,
            "upload": {
                "file_name": upload.get("file_name", ""),
                "stored_path": upload.get("stored_path", ""),
                "cos_url": upload.get("cos_url", ""),
                "cos_key": upload.get("cos_key", ""),
                "storage_mode": upload.get("storage_mode", "local"),
            },
            "requested_model": self._analysis_profile(study),
        }

    @classmethod
    def _normalize_external_inference_payload(cls, study: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        data = dict(payload.get("data") or payload)
        normalized = {
            "status": str(data.get("status", "completed") or "completed"),
            "task_type": str(data.get("task_type", "") or ""),
            "model_name": str(data.get("model_name", "") or ""),
            "model_version": str(data.get("model_version", "") or ""),
            "summary": str(data.get("summary", "") or ""),
            "findings": list(data.get("findings") or []),
            "measurements": list(data.get("measurements") or []),
            "overlays": list(data.get("overlays") or []),
            "updated_at": int(data.get("updated_at") or datetime.now().timestamp()),
        }
        return cls._normalize_analysis_payload(study, normalized)

    def _run_external_inference(self, study: dict[str, Any]) -> dict[str, Any]:
        endpoint = self._inference_endpoint()
        if not endpoint:
            raise ValueError("IMAGING_INFERENCE_ENDPOINT or IMAGING_INFERENCE_BASE_URL is not configured.")

        response = requests.post(
            endpoint,
            headers=self._inference_headers(),
            json=self._build_inference_payload(study),
            timeout=self._inference_timeout(),
        )
        response.raise_for_status()
        payload = response.json()
        return self._normalize_external_inference_payload(study, payload)

    def _group_instances_by_series(self, instances: list[dict[str, Any]]) -> list[dict[str, Any]]:
        series_map: dict[str, dict[str, Any]] = {}

        for item in instances:
            current = series_map.setdefault(
                item["series_uid"],
                {
                    "series_uid": item["series_uid"],
                    "series_number": item.get("series_number", ""),
                    "series_description": item.get("series_description", "") or "默认序列",
                    "slice_thickness": item.get("slice_thickness", ""),
                    "orientation": item.get("orientation", ""),
                    "image_count": 0,
                    "instances": [],
                },
            )
            current["image_count"] += 1
            current["instances"].append(item)

        return sorted(
            series_map.values(),
            key=lambda item: (item.get("series_number", ""), item["series_description"]),
        )

    def _build_demo_instance_map(self, grouped_series: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        instance_map: dict[str, list[dict[str, Any]]] = {}
        for series in grouped_series:
            instance_map[series["series_uid"]] = [
                {
                    "id": item["sop_instance_uid"] or str(
                        uuid5(NAMESPACE_DNS, f'{series["series_uid"]}-{item["instance_number"]}-{index}')
                    ),
                    "sop_instance_uid": item["sop_instance_uid"],
                    "instance_number": int(item["instance_number"] or 0),
                    "file_path": item["file_path"],
                    "thumbnail_path": "",
                    "window_width": item["window_width"],
                    "window_center": item["window_center"],
                    "rows": item["rows"],
                    "columns": item["columns"],
                }
                for index, item in enumerate(series["instances"])
            ]
        return instance_map

    def _persist_series_and_instances(self, study_id: str, grouped_series: list[dict[str, Any]]) -> None:
        if not (self._has_table("imaging_series") and self._has_table("imaging_instance")):
            return

        for series in grouped_series:
            series_item = self.create(
                ImagingSeries,
                study_id=UUID(study_id),
                series_uid=series["series_uid"],
                series_number=int(series["series_number"] or 0),
                series_description=series["series_description"],
                slice_thickness=series["slice_thickness"],
                image_count=series["image_count"],
                orientation=series["orientation"],
                meta={},
            )

            for instance in series["instances"]:
                self.create(
                    ImagingInstance,
                    study_id=UUID(study_id),
                    series_id=series_item.id,
                    sop_instance_uid=instance["sop_instance_uid"],
                    instance_number=int(instance["instance_number"] or 0),
                    file_path=instance["file_path"],
                    thumbnail_path="",
                    window_width=instance["window_width"],
                    window_center=instance["window_center"],
                    meta={
                        "rows": instance["rows"],
                        "columns": instance["columns"],
                    },
                )

    def _load_db_series(self, study_id: str) -> list[dict[str, Any]]:
        if not self._has_table("imaging_series"):
            return []

        items = self.db.session.query(ImagingSeries).filter(
            ImagingSeries.study_id == UUID(study_id)
        ).order_by(ImagingSeries.series_number.asc(), ImagingSeries.created_at.asc()).all()

        return [
            {
                "id": str(item.id),
                "series_uid": item.series_uid,
                "name": item.series_description or "默认序列",
                "images": item.image_count,
                "slice_thickness": f"{item.slice_thickness} mm" if item.slice_thickness else "待补充",
                "orientation": item.orientation,
            }
            for item in items
        ]

    def _load_db_instances(self, study_id: str, series_id: str) -> list[dict[str, Any]]:
        if not self._has_table("imaging_instance"):
            return []

        items = self.db.session.query(ImagingInstance).filter(
            ImagingInstance.study_id == UUID(study_id),
            ImagingInstance.series_id == UUID(series_id),
        ).order_by(ImagingInstance.instance_number.asc(), ImagingInstance.created_at.asc()).all()

        return [
            {
                "id": str(item.id),
                "sop_instance_uid": item.sop_instance_uid,
                "instance_number": item.instance_number,
                "file_path": item.file_path,
                "thumbnail_path": item.thumbnail_path,
                "window_width": item.window_width,
                "window_center": item.window_center,
                "rows": int((item.meta or {}).get("rows", 0) or 0),
                "columns": int((item.meta or {}).get("columns", 0) or 0),
            }
            for item in items
        ]

    @staticmethod
    def _placeholder_preview(label: str = "No Preview") -> bytes:
        image = Image.new("L", (512, 512), color=24)
        pixels = image.load()
        for y in range(512):
            for x in range(512):
                pixels[x, y] = int((x + y) / 4) % 255

        # Add a simple crosshair so the placeholder is recognizable.
        for index in range(512):
            pixels[index, 256] = 220
            pixels[256, index] = 220

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def _dicom_to_png_bytes(file_path: str) -> bytes:
        if pydicom is None or np is None or not file_path:
            return ImagingService._placeholder_preview()

        try:
            dataset = pydicom.dcmread(file_path, force=True)
            pixel_array = dataset.pixel_array.astype("float32")
            if pixel_array.ndim > 2:
                pixel_array = pixel_array[0]

            intercept = float(getattr(dataset, "RescaleIntercept", 0) or 0)
            slope = float(getattr(dataset, "RescaleSlope", 1) or 1)
            pixel_array = pixel_array * slope + intercept

            window_center = getattr(dataset, "WindowCenter", None)
            window_width = getattr(dataset, "WindowWidth", None)
            if isinstance(window_center, (list, tuple)):
                window_center = window_center[0]
            if isinstance(window_width, (list, tuple)):
                window_width = window_width[0]

            if window_center is not None and window_width not in (None, 0, "0"):
                center = float(window_center)
                width = max(float(window_width), 1.0)
                lower = center - width / 2
                upper = center + width / 2
                pixel_array = np.clip(pixel_array, lower, upper)
            else:
                pixel_array = np.clip(pixel_array, np.min(pixel_array), np.max(pixel_array))

            pixel_min = float(np.min(pixel_array))
            pixel_max = float(np.max(pixel_array))
            if pixel_max - pixel_min < 1e-6:
                normalized = np.zeros_like(pixel_array, dtype="uint8")
            else:
                normalized = ((pixel_array - pixel_min) / (pixel_max - pixel_min) * 255.0).astype("uint8")

            if getattr(dataset, "PhotometricInterpretation", "") == "MONOCHROME1":
                normalized = 255 - normalized

            image = Image.fromarray(normalized)
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            return buffer.getvalue()
        except Exception:
            return ImagingService._placeholder_preview()

    def _extract_dicom_payload(self, file_path: str, file_name: str) -> dict[str, Any]:
        metadata = {
            "parser": "fallback",
            "parser_status": "skipped",
            "file_name": file_name,
            "file_path": file_path,
            "file_type": Path(file_name).suffix.lower(),
            "patient_id": "",
            "study_instance_uid": "",
            "series_instance_uid": "",
            "study_date": "",
            "study_time": "",
            "study_description": "",
            "series_description": "",
            "modality": "",
            "body_part_examined": "",
            "slice_thickness": "",
            "series_number": "",
            "instance_number": "",
            "rows": 0,
            "columns": 0,
            "window_center": "",
            "window_width": "",
            "manufacturer": "",
            "extracted_files": 0,
            "parsed_instances": 0,
        }
        series = [
            {
                "name": "原始上传文件",
                "images": 1,
                "slice_thickness": "待解析",
            }
        ]
        instances: list[dict[str, Any]] = []

        if not file_path:
            metadata["parser_status"] = "missing_file"
            return {"metadata": metadata, "series": series, "instances": instances}

        suffix = Path(file_name).suffix.lower()
        if suffix == ".zip":
            extract_root = Path(file_path).with_suffix("")
            extract_dir = extract_root.parent / f"{extract_root.name}_unzipped"
            try:
                extracted_files = self._extract_zip_archive(file_path, extract_dir)
            except (OSError, zipfile.BadZipFile):
                metadata["parser_status"] = "zip_extract_failed"
                metadata["parser"] = "archive"
                return {"metadata": metadata, "series": series, "instances": instances}

            metadata["parser"] = "archive"
            metadata["extracted_files"] = len(extracted_files)

            if pydicom is None:
                metadata["parser_status"] = "zip_extracted_waiting_pydicom"
                series = [
                    {
                        "name": "压缩包内影像文件",
                        "images": len(extracted_files) or 1,
                        "slice_thickness": "待解析",
                    }
                ]
                return {"metadata": metadata, "series": series, "instances": instances}

            dataset_pairs = [
                (path, dataset)
                for path in extracted_files
                for dataset in [self._read_dicom_dataset(path)]
                if dataset is not None
            ]
            datasets = [dataset for _, dataset in dataset_pairs]
            if not datasets:
                metadata["parser_status"] = "zip_extracted_no_dicom"
                series = [
                    {
                        "name": "压缩包内文件",
                        "images": len(extracted_files) or 1,
                        "slice_thickness": "未识别到 DICOM",
                    }
                ]
                return {"metadata": metadata, "series": series, "instances": instances}

            metadata = {
                **metadata,
                **self._build_metadata_from_dataset(datasets[0], file_path, file_name),
                "parser": "pydicom+archive",
                "parser_status": "zip_parsed",
                "extracted_files": len(extracted_files),
                "parsed_instances": len(datasets),
            }
            instances = [self._build_instance_item(dataset, path) for path, dataset in dataset_pairs]
            series = self._aggregate_series(datasets)
            return {"metadata": metadata, "series": series, "instances": instances}

        if pydicom is None:
            metadata["parser_status"] = "pydicom_not_installed"
            return {"metadata": metadata, "series": series, "instances": instances}

        try:
            dataset = pydicom.dcmread(file_path, stop_before_pixels=True, force=True)
            metadata = {
                **metadata,
                **self._build_metadata_from_dataset(dataset, file_path, file_name),
                "parsed_instances": 1,
            }
            instances = [self._build_instance_item(dataset, Path(file_path))]
            series = [
                {
                    "name": metadata["series_description"] or "默认序列",
                    "images": 1,
                    "slice_thickness": f'{metadata["slice_thickness"]} mm' if metadata["slice_thickness"] else "待补充",
                }
            ]
        except Exception as exc:  # pragma: no cover - defensive fallback for malformed dicom
            metadata["parser_status"] = f"parse_failed:{exc.__class__.__name__}"

        return {"metadata": metadata, "series": series, "instances": instances}

    @staticmethod
    def _normalize_body_part(value: str, fallback: str = "Chest") -> str:
        normalized = str(value or "").strip().upper()
        if normalized in {"CHEST", "LUNG", "THORAX"}:
            return "Chest"
        if normalized in {"BRAIN", "HEAD", "CRANIUM"}:
            return "Brain"
        if normalized in {"ABDOMEN", "ABD", "ABDOMINAL"}:
            return "Abdomen"
        return str(value).strip() or fallback

    def _db_tables_ready(self) -> bool:
        inspector = inspect(self.db.engine)
        return inspector.has_table("imaging_report") and inspector.has_table("imaging_review")

    def _has_table(self, table_name: str) -> bool:
        return inspect(self.db.engine).has_table(table_name)

    def _load_persisted_state(self, account_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        if self._db_tables_ready():
            reports = {
                str(item.study_id): {
                    "content": item.draft_content,
                    "status": item.report_status,
                    "summary": item.doctor_notes,
                    "updated_at": int(item.updated_at.timestamp()) if item.updated_at else 0,
                }
                for item in self.db.session.query(ImagingReport).filter(
                    ImagingReport.study_id.isnot(None)
                ).all()
            }
            reviews = {
                str(item.study_id): {
                    "label": item.review_label,
                    "comment": item.comment,
                    "status": item.review_payload.get("status", item.review_label),
                    "updated_at": int(item.created_at.timestamp()) if item.created_at else 0,
                }
                for item in self.db.session.query(ImagingReview).filter(
                    ImagingReview.reviewer_id == UUID(account_id)
                ).all()
            }
            return reports, reviews

        account_state = self._load_state().get(account_id, {})
        return account_state.get("reports", {}), account_state.get("reviews", {})

    def _load_db_audit_logs(self, study_id: str) -> list[dict[str, Any]]:
        if not self._has_table("imaging_audit_log"):
            return []

        items = self.db.session.query(ImagingAuditLog).filter(
            ImagingAuditLog.study_id == UUID(study_id)
        ).order_by(ImagingAuditLog.created_at.desc()).all()

        return [
            {
                "id": str(item.id),
                "action": item.action,
                "target_type": item.target_type,
                "target_id": str(item.target_id) if item.target_id else "",
                "success": item.success,
                "details": item.details or {},
                "created_at": int(item.created_at.timestamp()) if item.created_at else 0,
            }
            for item in items
        ]

    def _load_db_review_logs(self, study_id: str) -> list[dict[str, Any]]:
        if not self._has_table("imaging_review"):
            return []

        items = self.db.session.query(ImagingReview).filter(
            ImagingReview.study_id == UUID(study_id)
        ).order_by(ImagingReview.created_at.desc()).all()

        return [
            {
                "id": str(item.id),
                "label": item.review_label,
                "comment": item.comment,
                "review_type": item.review_type,
                "reviewer_id": str(item.reviewer_id),
                "status": item.review_payload.get("status", item.review_label),
                "created_at": int(item.created_at.timestamp()) if item.created_at else 0,
            }
            for item in items
        ]

    def _load_db_studies(self, account_id: str) -> list[dict[str, Any]]:
        if not inspect(self.db.engine).has_table("imaging_study"):
            return []

        studies = self.db.session.query(ImagingStudy).filter(
            ImagingStudy.account_id == UUID(account_id)
        ).order_by(ImagingStudy.study_time.desc().nullslast()).all()

        return [
            {
                "id": str(item.id),
                "patient_code": item.accession_number or item.patient_uid,
                "patient_name_masked": item.patient_name_masked,
                "modality": item.modality,
                "body_part": item.body_part,
                "study_description": item.study_description,
                "study_time": int(item.study_time.timestamp()) if item.study_time else 0,
                "status": item.processing_status,
                "quality_status": item.quality_status,
                "ai_summary": item.meta.get("ai_summary", ""),
                "findings_count": len(item.meta.get("findings", [])),
                "report_status": item.meta.get("report_status", "not_started"),
                "priority": item.meta.get("priority", "normal"),
                "upload": item.meta.get("upload", {}),
                "dicom_metadata": item.meta.get("dicom_metadata", {}),
                "series": item.meta.get("series", []),
            }
            for item in studies
        ]

    @staticmethod
    def _analysis_profile(study: dict[str, Any]) -> dict[str, str]:
        body_part = str(study.get("body_part", "")).strip()
        modality = str(study.get("modality", "")).strip().upper()

        if body_part == "Chest" and modality == "CT":
            return {
                "task_type": "report_draft_assist",
                "model_name": "chest-ct-report-assistant",
                "model_version": "phase-1-mvp",
            }

        if body_part == "Brain" and modality == "CT":
            return {
                "task_type": "hemorrhage_triage",
                "model_name": "head-ct-triage-assistant",
                "model_version": "phase-2-preview",
            }

        return {
            "task_type": "quality_control",
            "model_name": "imaging-quality-gate",
            "model_version": "phase-0-baseline",
        }

    @classmethod
    def _normalize_analysis_payload(cls, study: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        profile = cls._analysis_profile(study)
        normalized = dict(payload)
        legacy_model_name = str(normalized.get("model_name", "")).strip()

        if not legacy_model_name or legacy_model_name == "imaging-mvp-demo":
            normalized["model_name"] = profile["model_name"]

        legacy_model_version = str(normalized.get("model_version", "")).strip().lower()
        if not legacy_model_version or legacy_model_version == "v0.1":
            normalized["model_version"] = profile["model_version"]

        legacy_task_type = str(normalized.get("task_type", "")).strip().lower()
        if not legacy_task_type or legacy_task_type == "detection":
            normalized["task_type"] = profile["task_type"]

        normalized["findings"] = list(normalized.get("findings") or [])
        normalized["measurements"] = list(normalized.get("measurements") or [])
        normalized["overlays"] = list(normalized.get("overlays") or [])
        normalized["updated_at"] = int(normalized.get("updated_at") or datetime.now().timestamp())
        return normalized

    @staticmethod
    def _should_expose_default_analysis(study: dict[str, Any]) -> bool:
        return str(study.get("status", "")).strip() in {
            "ai_completed",
            "doctor_review",
            "doctor_reviewed",
            "doctor_revision_needed",
            "doctor_rejected",
            "completed",
        } or int(study.get("findings_count", 0) or 0) > 0

    @classmethod
    def _default_analysis_payload(study: dict[str, Any]) -> dict[str, Any]:
        profile = cls._analysis_profile(study)

        if study["body_part"] == "Chest":
            findings = [
                {
                    "title": "右上肺结节",
                    "confidence": 0.93,
                    "description": "右上肺尖后段见 8 mm 实性结节，边界相对清晰。",
                    "location": "right upper lobe",
                    "size": "8 mm",
                    "risk_level": "medium",
                },
                {
                    "title": "右上肺微小结节",
                    "confidence": 0.74,
                    "description": "右上肺另见约 3 mm 微小结节，建议按指南随访。",
                    "location": "right upper lobe",
                    "size": "3 mm",
                    "risk_level": "low",
                },
            ]
            summary = "胸部 CT 结构化结果已生成，发现 2 条肺结节线索，可继续进入报告草拟与医生审核。"
        elif study["body_part"] == "Brain":
            findings = [
                {
                    "title": "未见明确急性出血",
                    "confidence": 0.88,
                    "description": "当前扫描未见明确高密度急性出血灶。",
                    "location": "intracranial",
                    "size": "",
                    "risk_level": "low",
                },
            ]
            summary = "头颅 CT 急诊初筛已完成，当前未见明确急性出血线索，建议医生结合原片复核。"
        else:
            findings = [
                {
                    "title": "运动伪影预警",
                    "confidence": 0.67,
                    "description": "轻度运动伪影影响下肺野可见度。",
                    "location": "lower lung field",
                    "size": "",
                    "risk_level": "low",
                },
            ]
            summary = "当前检查进入质控预警流程，建议先完成图像质量确认，再继续后续分析。"

        return {
            "status": "completed",
            "task_type": profile["task_type"],
            "model_name": profile["model_name"],
            "model_version": profile["model_version"],
            "summary": summary,
            "findings": findings,
            "measurements": [],
            "overlays": [],
            "updated_at": int(datetime.now().timestamp()),
        }

    @staticmethod
    def _state_file() -> Path:
        return Path(__file__).resolve().parents[4] / "storage" / "imaging_demo_state.json"

    @staticmethod
    def _upload_root() -> Path:
        return Path(__file__).resolve().parents[4] / "storage" / "imaging_uploads"

    @staticmethod
    def _read_file_bytes(file_path: str) -> bytes:
        return Path(file_path).read_bytes()

    def _build_upload_meta(
        self,
        account,
        upload_name: str,
        upload_suffix: str,
        upload_size: int,
        upload_path: str,
        study_uid: str,
        mime_type: str = "application/dicom",
    ) -> dict[str, Any]:
        upload_meta = {
            "file_name": upload_name,
            "file_suffix": upload_suffix,
            "file_size": upload_size,
            "stored_path": upload_path,
            "storage_mode": self._storage_mode(),
            "cos_key": "",
            "cos_url": "",
            "upload_file_id": "",
            "upload_history": [],
        }

        if not upload_name or not upload_path or not self._should_use_cos():
            if upload_name and upload_path and self._has_table("upload_file"):
                local_upload_record = self.upload_file_service.create_upload_file(
                    account_id=account.id,
                    name=upload_name,
                    key=upload_path,
                    size=upload_size,
                    extension=upload_suffix.lstrip("."),
                    mime_type=mime_type,
                    hash=hashlib.sha3_256(self._read_file_bytes(upload_path)).hexdigest(),
                )
                upload_meta["upload_file_id"] = str(local_upload_record.id)
                upload_meta["upload_history"] = [
                    {
                        "id": str(local_upload_record.id),
                        "name": local_upload_record.name,
                        "key": local_upload_record.key,
                        "storage": "local",
                        "mime_type": local_upload_record.mime_type,
                        "size": local_upload_record.size,
                    }
                ]
            return upload_meta

        if upload_name and upload_path and self._has_table("upload_file"):
            local_upload_record = self.upload_file_service.create_upload_file(
                account_id=account.id,
                name=upload_name,
                key=upload_path,
                size=upload_size,
                extension=upload_suffix.lstrip("."),
                mime_type=mime_type,
                hash=hashlib.sha3_256(self._read_file_bytes(upload_path)).hexdigest(),
            )
            upload_meta["upload_file_id"] = str(local_upload_record.id)
            upload_meta["upload_history"].append(
                {
                    "id": str(local_upload_record.id),
                    "name": local_upload_record.name,
                    "key": local_upload_record.key,
                    "storage": "local",
                    "mime_type": local_upload_record.mime_type,
                    "size": local_upload_record.size,
                }
            )

        extension = upload_suffix.lstrip(".")
        upload_record = self.cos_service.upload_bytes(
            content=self._read_file_bytes(upload_path),
            filename=upload_name,
            extension=extension,
            mime_type=mime_type,
            account=account,
            key_prefix=f"imaging/{study_uid}",
        )
        upload_meta["cos_key"] = upload_record.key
        upload_meta["cos_url"] = self.cos_service.get_file_url(upload_record.key)
        upload_meta["upload_history"].append(
            {
                "id": str(upload_record.id),
                "name": upload_record.name,
                "key": upload_record.key,
                "storage": "cos",
                "mime_type": upload_record.mime_type,
                "size": upload_record.size,
                "url": upload_meta["cos_url"],
            }
        )
        return upload_meta

    def _ensure_local_file(self, upload_meta: dict[str, Any]) -> str:
        stored_path = str(upload_meta.get("stored_path", "") or "")
        if stored_path and Path(stored_path).exists():
            return stored_path

        cos_key = str(upload_meta.get("cos_key", "") or "")
        if not cos_key or not self.cos_service.is_configured():
            return stored_path

        suffix = str(upload_meta.get("file_suffix", "") or "")
        temp_dir = Path(tempfile.gettempdir()) / "llmops-imaging-preview"
        temp_dir.mkdir(parents=True, exist_ok=True)
        local_path = temp_dir / f"{uuid5(NAMESPACE_DNS, cos_key)}{suffix}"
        if not local_path.exists():
            self.cos_service.download_file(cos_key, str(local_path))
        return str(local_path)

    def _load_state(self) -> dict[str, Any]:
        state_file = self._state_file()
        if not state_file.exists():
            return {}

        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _save_state(self, state: dict[str, Any]) -> None:
        state_file = self._state_file()
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_demo_studies(self, account_id: str) -> list[dict[str, Any]]:
        account_state = self._load_state().get(account_id, {})
        return account_state.get("studies", [])

    def _save_demo_study(self, account_id: str, study: dict[str, Any]) -> None:
        state = self._load_state()
        account_state = state.setdefault(account_id, {})
        studies = account_state.setdefault("studies", [])

        for index, item in enumerate(studies):
            if item.get("id") == study["id"]:
                studies[index] = study
                break
        else:
            studies.append(study)

        self._save_state(state)

    def _load_demo_analysis_map(self, account_id: str) -> dict[str, Any]:
        account_state = self._load_state().get(account_id, {})
        return account_state.get("analysis_results", {})

    def _save_demo_analysis_result(self, account_id: str, study_id: str, payload: dict[str, Any]) -> None:
        state = self._load_state()
        account_state = state.setdefault(account_id, {})
        analysis_results = account_state.setdefault("analysis_results", {})
        analysis_results[study_id] = payload
        self._save_state(state)

    def _append_demo_audit_log(
        self,
        account_id: str,
        study_id: str,
        action: str,
        target_type: str,
        target_id: str,
        details: dict[str, Any] | None = None,
        success: bool = True,
    ) -> None:
        state = self._load_state()
        account_state = state.setdefault(account_id, {})
        audit_logs = account_state.setdefault("audit_logs", [])
        audit_logs.append(
            {
                "id": str(uuid5(NAMESPACE_DNS, f"{study_id}-{action}-{len(audit_logs) + 1}")),
                "study_id": study_id,
                "action": action,
                "target_type": target_type,
                "target_id": target_id,
                "success": success,
                "details": details or {},
                "created_at": int(datetime.now().timestamp()),
            }
        )
        self._save_state(state)

    def _load_demo_audit_logs(self, account_id: str, study_id: str) -> list[dict[str, Any]]:
        account_state = self._load_state().get(account_id, {})
        items = account_state.get("audit_logs", [])
        return [
            item for item in reversed(items)
            if item.get("study_id") == study_id
        ]

    def _write_audit_log(
        self,
        account,
        study_id: str,
        action: str,
        target_type: str,
        target_id: str,
        details: dict[str, Any] | None = None,
        success: bool = True,
    ) -> None:
        if self._has_table("imaging_audit_log"):
            self.create(
                ImagingAuditLog,
                study_id=UUID(study_id),
                operator_id=account.id,
                action=action,
                target_type=target_type,
                target_id=UUID(target_id) if target_id else None,
                success=success,
                details=details or {},
            )
            return

        self._append_demo_audit_log(
            account_id=str(account.id),
            study_id=study_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            success=success,
        )

    def _find_study_or_none(self, study_id: str, account) -> dict[str, Any] | None:
        studies = self._load_db_studies(str(account.id))
        if not studies:
            studies = self._load_demo_studies(str(account.id)) + self._build_demo_studies(str(account.id))
        return next((item for item in studies if item["id"] == study_id), None)

    def _load_db_analysis_result(self, study_id: str) -> dict[str, Any] | None:
        if not self._has_table("imaging_ai_result"):
            return None

        item = self.db.session.query(ImagingAiResult).filter(
            ImagingAiResult.study_id == UUID(study_id)
        ).order_by(ImagingAiResult.created_at.desc()).first()

        if item is None:
            return None

        return {
            "task_id": str(item.id),
            "status": item.result_status,
            "task_type": item.task_type,
            "model_name": item.model_name,
            "model_version": item.model_version,
            "summary": item.summary,
            "findings": item.findings or [],
            "measurements": item.measurements or [],
            "overlays": item.overlays or [],
            "updated_at": int(item.created_at.timestamp()) if item.created_at else 0,
        }

    @staticmethod
    def _build_demo_studies(account_id: str) -> list[dict[str, Any]]:
        base_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        seed = f"llmops-imaging-{account_id}"
        return [
            {
                "id": str(uuid5(NAMESPACE_DNS, f"{seed}-study-1")),
                "patient_code": "RAD-2026-0001",
                "patient_name_masked": "Zhang**",
                "modality": "CT",
                "body_part": "Chest",
                "study_description": "胸部平扫 CT，用于肺结节随访复查",
                "study_time": int((base_time - timedelta(hours=2)).timestamp()),
                "status": "doctor_review",
                "quality_status": "qualified",
                "ai_summary": "胸部 CT 结构化结果已生成，报告草稿待医生审核。",
                "findings_count": 2,
                "report_status": "draft_ready",
                "priority": "normal",
                "upload": {},
                "dicom_metadata": {
                    "parser": "demo",
                    "parser_status": "demo",
                    "study_date": "20260425",
                    "modality": "CT",
                    "body_part_examined": "CHEST",
                    "study_description": "胸部平扫 CT，用于肺结节随访复查",
                    "series_description": "Lung kernel thin slice",
                    "slice_thickness": "1.0",
                    "rows": 512,
                    "columns": 512,
                    "manufacturer": "Demo Scanner",
                },
                "series": [
                    {
                        "id": str(uuid5(NAMESPACE_DNS, f"{seed}-study-1-series-1")),
                        "series_uid": str(uuid5(NAMESPACE_DNS, f"{seed}-study-1-series-uid-1")),
                        "name": "Lung kernel thin slice",
                        "images": 126,
                        "slice_thickness": "1.0 mm",
                        "orientation": "",
                    },
                    {
                        "id": str(uuid5(NAMESPACE_DNS, f"{seed}-study-1-series-2")),
                        "series_uid": str(uuid5(NAMESPACE_DNS, f"{seed}-study-1-series-uid-2")),
                        "name": "Mediastinal reconstruction",
                        "images": 126,
                        "slice_thickness": "5.0 mm",
                        "orientation": "",
                    },
                ],
                "instances_map": {
                    str(uuid5(NAMESPACE_DNS, f"{seed}-study-1-series-uid-1")): [
                        {
                            "id": str(uuid5(NAMESPACE_DNS, f"{seed}-study-1-instance-1")),
                            "sop_instance_uid": str(uuid5(NAMESPACE_DNS, f"{seed}-study-1-sop-1")),
                            "instance_number": 1,
                            "file_path": "demo://study-1/series-1/instance-1",
                            "thumbnail_path": "",
                            "window_width": "400",
                            "window_center": "40",
                            "rows": 512,
                            "columns": 512,
                        }
                    ],
                },
            },
            {
                "id": str(uuid5(NAMESPACE_DNS, f"{seed}-study-2")),
                "patient_code": "ER-2026-0148",
                "patient_name_masked": "Li**",
                "modality": "CT",
                "body_part": "Brain",
                "study_description": "头颅平扫 CT，用于头晕呕吐急诊排查",
                "study_time": int((base_time - timedelta(hours=6)).timestamp()),
                "status": "ai_completed",
                "quality_status": "qualified",
                "ai_summary": "头颅 CT 急诊初筛已完成，当前未见明确急性出血线索，待医生复核。",
                "findings_count": 1,
                "report_status": "pending_draft",
                "priority": "urgent",
                "upload": {},
                "dicom_metadata": {
                    "parser": "demo",
                    "parser_status": "demo",
                    "study_date": "20260425",
                    "modality": "CT",
                    "body_part_examined": "BRAIN",
                    "study_description": "头颅平扫 CT，用于头晕呕吐急诊排查",
                    "series_description": "Routine brain plain scan",
                    "slice_thickness": "5.0",
                    "rows": 512,
                    "columns": 512,
                    "manufacturer": "Demo Scanner",
                },
                "series": [
                    {
                        "id": str(uuid5(NAMESPACE_DNS, f"{seed}-study-2-series-1")),
                        "series_uid": str(uuid5(NAMESPACE_DNS, f"{seed}-study-2-series-uid-1")),
                        "name": "Routine brain plain scan",
                        "images": 42,
                        "slice_thickness": "5.0 mm",
                        "orientation": "",
                    },
                ],
                "instances_map": {},
            },
            {
                "id": str(uuid5(NAMESPACE_DNS, f"{seed}-study-3")),
                "patient_code": "DR-2026-0233",
                "patient_name_masked": "Wang**",
                "modality": "DR",
                "body_part": "Chest",
                "study_description": "胸部 DR 检查，用于发热筛查",
                "study_time": int((base_time - timedelta(days=1, hours=1)).timestamp()),
                "status": "awaiting_ai",
                "quality_status": "needs_review",
                "ai_summary": "胸部 DR 已进入质控队列，待确认运动伪影后再触发分析。",
                "findings_count": 0,
                "report_status": "not_started",
                "priority": "normal",
                "upload": {},
                "dicom_metadata": {
                    "parser": "demo",
                    "parser_status": "demo",
                    "study_date": "20260424",
                    "modality": "DR",
                    "body_part_examined": "CHEST",
                    "study_description": "胸部 DR 检查，用于发热筛查",
                    "series_description": "PA Chest",
                    "slice_thickness": "",
                    "rows": 2048,
                    "columns": 2048,
                    "manufacturer": "Demo Scanner",
                },
                "series": [
                    {
                        "id": str(uuid5(NAMESPACE_DNS, f"{seed}-study-3-series-1")),
                        "series_uid": str(uuid5(NAMESPACE_DNS, f"{seed}-study-3-series-uid-1")),
                        "name": "PA Chest",
                        "images": 1,
                        "slice_thickness": "单张投照",
                        "orientation": "",
                    },
                ],
                "instances_map": {},
            },
        ]

    @staticmethod
    def _build_feedback_stats(reviews: list[dict[str, Any]]) -> dict[str, Any]:
        total = len(reviews)
        approved = sum(1 for item in reviews if item["label"] == "approved")
        needs_revision = sum(1 for item in reviews if item["label"] == "needs_revision")
        rejected = sum(1 for item in reviews if item["label"] == "rejected")
        approval_rate = round((approved / total) * 100, 1) if total else 0

        return {
            "total_reviews": total,
            "approved": approved,
            "needs_revision": needs_revision,
            "rejected": rejected,
            "approval_rate": approval_rate,
        }

    def get_overview(self, account) -> dict[str, Any]:
        total_apps = self.db.session.query(func.count(App.id)).filter(App.account_id == account.id).scalar() or 0
        total_datasets = self.db.session.query(func.count(Dataset.id)).filter(Dataset.account_id == account.id).scalar() or 0
        total_documents = self.db.session.query(func.count(Document.id)).filter(Document.account_id == account.id).scalar() or 0
        total_workflows = self.db.session.query(func.count(Workflow.id)).filter(Workflow.account_id == account.id).scalar() or 0

        return {
            "title": "AI 医院影像智能处理中心",
            "summary": (
                "围绕真实医院影像科流程建设影像接入、AI 辅助检出、报告草拟、"
                "知识问答和审计分析能力，优先完成胸部 CT 报告助手的 MVP 闭环。"
            ),
            "positioning": [
                "影像接入与质控中心",
                "结构化报告与医生审核工作台",
                "面向医院私有化部署的影像 AI 平台",
            ],
            "scenes": [
                {
                    "name": "影像接入",
                    "value": "01",
                    "description": "支持 PACS、RIS 和手工上传，统一管理 DICOM 检查、序列和实例。",
                },
                {
                    "name": "辅助检出",
                    "value": "02",
                    "description": "优先支持胸部 CT 肺结节和头颅 CT 出血筛查等高价值窄场景。",
                },
                {
                    "name": "报告草拟",
                    "value": "03",
                    "description": "结合 AI 结果、指南知识库和医院模板生成报告初稿，由医生确认。",
                },
                {
                    "name": "质控分析",
                    "value": "04",
                    "description": "统计采纳率、误报漏报、耗时与访问日志，形成闭环分析能力。",
                },
            ],
            "phases": [
                {
                    "key": "phase-0",
                    "title": "Phase 0 影像基础设施",
                    "goal": "让平台具备真实影像数据管理能力。",
                    "deliverables": ["DICOM 导入", "检查和序列管理", "脱敏策略", "审计日志"],
                },
                {
                    "key": "phase-1",
                    "title": "Phase 1 报告助手 MVP",
                    "goal": "先落地低风险、高频价值的影像报告场景。",
                    "deliverables": ["模板管理", "指南知识库", "报告草稿生成", "医生编辑审核"],
                },
                {
                    "key": "phase-2",
                    "title": "Phase 2 专病 AI 检出",
                    "goal": "接入专病模型并形成医生反馈闭环。",
                    "deliverables": ["专病推理服务", "病灶标注可视化", "误报漏报反馈", "效果统计"],
                },
                {
                    "key": "phase-3",
                    "title": "Phase 3 医院系统集成",
                    "goal": "与 PACS、RIS、HIS 打通真实院内链路。",
                    "deliverables": ["PACS 对接", "RIS 回写", "高危告警", "多院区权限隔离"],
                },
            ],
            "guardrails": [
                "AI 结果仅作辅助参考，正式报告必须由医生确认。",
                "患者数据默认走脱敏和审计，优先支持院内私有化部署。",
                "正式环境模型版本和提示词版本需要可追溯、可回滚。",
            ],
            "metrics": {
                "apps": int(total_apps),
                "datasets": int(total_datasets),
                "documents": int(total_documents),
                "workflows": int(total_workflows),
                "workflow_templates": len(IMAGING_WORKFLOW_TEMPLATES),
            },
            "mvp": {
                "name": "胸部 CT 影像报告智能助手",
                "value": (
                    "优先建设 DICOM 上传、检查列表、知识库驱动的报告草稿、"
                    "医生审核和审计追踪的完整闭环。"
                ),
            },
        }

    def get_workflow_templates(self) -> list[dict[str, Any]]:
        templates = []
        for key, item in IMAGING_WORKFLOW_TEMPLATES.items():
            templates.append({
                "key": key,
                "name": item["name"],
                "scene": item["scene"],
                "steps": item["steps"],
                "outputs": item["outputs"],
            })
        return templates

    @staticmethod
    def get_mvp_tasks() -> list[dict[str, Any]]:
        return [
            {
                "key": "m1",
                "title": "影像基础设施",
                "owner": "Backend",
                "items": ["DICOM 导入", "检查/序列/实例模型", "脱敏与审计"],
            },
            {
                "key": "m2",
                "title": "影像中心前端",
                "owner": "Frontend",
                "items": ["影像中心规划页", "检查列表页", "报告工作台原型"],
            },
            {
                "key": "m3",
                "title": "报告助手闭环",
                "owner": "Backend + LLM",
                "items": ["模板管理", "知识库检索", "报告草稿生成", "医生审核保存"],
            },
            {
                "key": "m4",
                "title": "专病模型接入",
                "owner": "Algorithm",
                "items": ["推理服务", "结构化发现", "误报漏报反馈"],
            },
            {
                "key": "m5",
                "title": "上传与分析联调",
                "owner": "Frontend + Backend",
                "items": ["真实文件上传", "分析任务触发", "结果回显与审计"],
            },
        ]

    def get_studies(self, account) -> list[dict[str, Any]]:
        studies = self._load_db_studies(str(account.id))
        if not studies:
            studies = self._load_demo_studies(str(account.id)) + self._build_demo_studies(str(account.id))
        reports, reviews = self._load_persisted_state(str(account.id))
        analysis_results = self._load_demo_analysis_map(str(account.id))

        for study in studies:
            report = reports.get(study["id"])
            if report:
                study["report_status"] = report.get("status", study["report_status"])
                study["ai_summary"] = report.get("summary", study["ai_summary"])

            review = reviews.get(study["id"])
            if review:
                study["status"] = review.get("status", study["status"])

            analysis_result = analysis_results.get(study["id"])
            if analysis_result:
                analysis_result = self._normalize_analysis_payload(study, analysis_result)
                study["status"] = "ai_completed" if analysis_result.get("status") != "failed" else "failed"
                study["ai_summary"] = analysis_result.get("summary", study["ai_summary"])
                study["findings_count"] = len(analysis_result.get("findings", []))

        return studies

    def get_study_detail(self, study_id: str, account) -> dict[str, Any]:
        studies = self._load_db_studies(str(account.id))
        if not studies:
            studies = self._load_demo_studies(str(account.id)) + self._build_demo_studies(str(account.id))
        study = next((item for item in studies if item["id"] == study_id), None)
        if study is None:
            study = studies[0]

        self._write_audit_log(
            account=account,
            study_id=study["id"],
            action="study_detail_viewed",
            target_type="study",
            target_id=study["id"],
            details={"patient_code": study["patient_code"]},
        )

        analysis_result = self.get_analysis_result(study["id"], account)
        structured_findings = analysis_result.get("findings", [])

        template_name = "影像报告标准模板"

        if structured_findings:
            findings = [
                {
                    "title": item.get("title", ""),
                    "confidence": item.get("confidence", 0),
                    "description": item.get("description", ""),
                }
                for item in structured_findings
            ]
        elif study["body_part"] == "Chest":
            template_name = "胸部 CT 报告助手模板"
            findings = [
                {
                    "title": "Right upper lobe nodule",
                    "confidence": 0.93,
                    "description": "8 mm solid nodule with clear margin in the apical segment.",
                },
                {
                    "title": "Right upper lobe micronodule",
                    "confidence": 0.74,
                    "description": "3 mm tiny nodule, follow-up suggested according to guideline.",
                },
            ]
            report_draft = (
                "检查所见：右上肺见小结节影，最大约 8 mm，边界相对清晰；余肺野未见明显大片实变影，未见明显胸腔积液或纵隔明显肿大淋巴结。\n"
                "影像印象：右上肺结节，建议结合既往检查并按随访指南复查低剂量胸部 CT。"
            )
        elif study["body_part"] == "Brain":
            template_name = "头颅 CT 急诊初筛模板"
            findings = [
                {
                    "title": "No definite acute hemorrhage",
                    "confidence": 0.88,
                    "description": "No obvious hyperdense hemorrhagic focus identified on the current scan.",
                },
            ]
            report_draft = (
                "检查所见：脑实质密度大致对称，当前未见明确急性高密度出血灶，脑室系统形态大小未见明显异常。\n"
                "影像印象：本次头颅 CT 未见明确急性颅内出血征象，建议结合临床症状与医生复核结果判断。"
            )
        else:
            template_name = "影像质控复核模板"
            findings = [
                {
                    "title": "Quality warning",
                    "confidence": 0.67,
                    "description": "Mild motion artifact affects the lower lung field visibility.",
                },
            ]
            report_draft = (
                "检查所见：图像存在轻度运动伪影，对局部结构显示造成一定影响。\n"
                "影像印象：建议优先完成图像质量复核，必要时补充采集后再进入正式分析流程。"
            )

        if structured_findings and study["body_part"] == "Chest":
            template_name = "胸部 CT 报告助手模板"
            report_draft = (
                "检查所见：AI 结构化结果提示右上肺可见结节样病灶，其中较大者约 8 mm；其余胸部可见结构未提示明确高危异常。\n"
                "影像印象：右上肺结节待医生复核确认，建议结合既往影像并参考随访指南完善处置建议。"
            )
        elif structured_findings and study["body_part"] == "Brain":
            template_name = "头颅 CT 急诊初筛模板"
            report_draft = (
                "检查所见：AI 初筛未提示明确急性出血灶，脑实质密度分布基本对称。\n"
                "影像印象：当前未见明确急诊高危出血线索，建议由值班医生结合原始影像进一步复核。"
            )
        elif structured_findings:
            template_name = "影像质控复核模板"
            report_draft = (
                "检查所见：当前检查以质控预警为主，图像质量对后续判断存在一定影响。\n"
                "影像印象：建议先完成人工确认，再决定是否继续分析或补采图像。"
            )

        reports, reviews = self._load_persisted_state(str(account.id))
        report_state = reports.get(study["id"], {})
        review_state = reviews.get(study["id"], {})

        return {
            **study,
            "series": self._load_db_series(study["id"]) or study.get("series", []) or [
                {"name": "默认序列", "images": 1, "slice_thickness": "待补充"},
            ],
            "findings": findings,
            "report_draft": {
                "status": report_state.get("status", study["report_status"]),
                "content": report_state.get("content", report_draft),
                "template_name": template_name,
                "template_version": "v1.0",
            },
            "timeline": [
                {"label": "DICOM 导入", "value": "已完成"},
                {"label": "检查脱敏与元数据解析", "value": "已完成"},
                {"label": "图像质控", "value": study["quality_status"]},
                {"label": "AI 分析 / 结构化结果", "value": analysis_result.get("status", review_state.get("status", study["status"]))},
                {"label": "报告草拟", "value": report_state.get("status", study["report_status"])},
                {"label": "医生审核", "value": review_state.get("status", study["status"])},
            ],
            "review": {
                "label": review_state.get("label", ""),
                "comment": review_state.get("comment", ""),
                "updated_at": review_state.get("updated_at", 0),
            },
        }

    def get_study_series(self, study_id: str, account) -> list[dict[str, Any]]:
        study = self._find_study_or_none(study_id, account)
        if study is None:
            return []

        db_series = self._load_db_series(study_id)
        if db_series:
            return db_series

        series_items = study.get("series", [])
        if series_items:
            return series_items

        return [
            {
                "id": str(uuid5(NAMESPACE_DNS, f"{study_id}-default-series")),
                "series_uid": str(uuid5(NAMESPACE_DNS, f"{study_id}-default-series-uid")),
                "name": "默认序列",
                "images": 1,
                "slice_thickness": "待补充",
                "orientation": "",
            }
        ]

    def get_series_instances(self, study_id: str, series_id: str, account) -> list[dict[str, Any]]:
        study = self._find_study_or_none(study_id, account)
        if study is None:
            return []

        db_instances = []
        if self._has_table("imaging_series") and self._has_table("imaging_instance"):
            db_instances = self._load_db_instances(study_id, series_id)
        if db_instances:
            return db_instances

        series_items = study.get("series", [])
        series_item = next((item for item in series_items if item.get("id") == series_id), None)
        if series_item is None:
            return []

        instance_map = study.get("instances_map", {})
        instances = instance_map.get(series_item.get("series_uid", ""), [])
        if instances:
            return instances

        return [
            {
                "id": str(uuid5(NAMESPACE_DNS, f"{series_id}-default-instance")),
                "sop_instance_uid": "",
                "instance_number": 1,
                "file_path": study.get("upload", {}).get("stored_path", ""),
                "thumbnail_path": "",
                "window_width": study.get("dicom_metadata", {}).get("window_width", ""),
                "window_center": study.get("dicom_metadata", {}).get("window_center", ""),
                "rows": int(study.get("dicom_metadata", {}).get("rows", 0) or 0),
                "columns": int(study.get("dicom_metadata", {}).get("columns", 0) or 0),
            }
        ]

    def get_instance_preview(self, study_id: str, series_id: str, instance_id: str, account) -> bytes:
        instances = self.get_series_instances(study_id, series_id, account)
        instance = next((item for item in instances if item.get("id") == instance_id), None)
        if instance is None:
            return self._placeholder_preview()
        preview_source = str(instance.get("file_path", ""))
        if not preview_source:
            study = self._find_study_or_none(study_id, account)
            if study is not None:
                preview_source = self._ensure_local_file(study.get("upload", {}))
        return self._dicom_to_png_bytes(preview_source)

    def upload_dicom(self, payload: dict[str, Any], account, file_storage=None) -> dict[str, Any]:
        study_uid = str(uuid5(NAMESPACE_DNS, f"{account.id}-{datetime.now().timestamp()}-study"))
        accession_number = str(payload.get("accession_number", "")).strip() or study_uid[-12:].upper()
        patient_code = str(payload.get("patient_code", "")).strip() or accession_number
        upload_name = ""
        upload_suffix = ""
        upload_size = 0
        upload_path = ""
        dicom_payload = self._extract_dicom_payload("", "")

        if file_storage is not None and getattr(file_storage, "filename", ""):
            upload_name = Path(str(file_storage.filename)).name
            upload_suffix = Path(upload_name).suffix.lower()
            if upload_suffix not in self.ALLOWED_UPLOAD_SUFFIXES:
                upload_suffix = ".dcm"

            upload_dir = self._upload_root() / str(account.id) / datetime.now().strftime("%Y%m%d")
            upload_dir.mkdir(parents=True, exist_ok=True)
            saved_name = f"{study_uid}{upload_suffix}"
            destination = upload_dir / saved_name
            file_storage.save(destination)
            upload_path = str(destination)
            try:
                upload_size = destination.stat().st_size
            except OSError:
                upload_size = 0
            dicom_payload = self._extract_dicom_payload(upload_path, upload_name)

        dicom_metadata = dicom_payload["metadata"]
        grouped_series = self._group_instances_by_series(dicom_payload["instances"])
        parsed_modality = dicom_metadata.get("modality", "")
        parsed_body_part = dicom_metadata.get("body_part_examined", "")
        parsed_description = dicom_metadata.get("study_description", "")
        parsed_patient_code = dicom_metadata.get("patient_id", "")

        upload_meta = self._build_upload_meta(
            account=account,
            upload_name=upload_name,
            upload_suffix=upload_suffix,
            upload_size=upload_size,
            upload_path=upload_path,
            study_uid=study_uid,
            mime_type=getattr(file_storage, "mimetype", "application/octet-stream") if file_storage is not None else "application/octet-stream",
        )

        study = {
            "id": str(uuid5(NAMESPACE_DNS, f"{study_uid}-study-id")),
            "patient_code": parsed_patient_code or patient_code,
            "patient_name_masked": str(payload.get("patient_name_masked", "匿名患者")).strip() or "匿名患者",
            "modality": str(payload.get("modality", parsed_modality or "CT")).strip() or parsed_modality or "CT",
            "body_part": self._normalize_body_part(
                str(payload.get("body_part", parsed_body_part or "Chest")).strip() or parsed_body_part or "Chest"
            ),
            "study_description": str(payload.get("study_description", parsed_description or "手工上传的 DICOM 检查")).strip()
            or "手工上传的 DICOM 检查",
            "study_time": int(datetime.now().timestamp()),
            "status": "waiting",
            "quality_status": "pending",
            "ai_summary": "DICOM 已上传，等待质控检查和 AI 分析。",
            "findings_count": 0,
            "report_status": "not_started",
            "priority": str(payload.get("priority", "normal")).strip() or "normal",
            "upload": upload_meta,
            "dicom_metadata": dicom_metadata,
            "series": dicom_payload["series"],
            "instances_map": self._build_demo_instance_map(grouped_series),
        }

        if self._has_table("imaging_study"):
            item = self.create(
                ImagingStudy,
                account_id=account.id,
                study_uid=study_uid,
                accession_number=accession_number,
                patient_uid=patient_code,
                patient_name_masked=study["patient_name_masked"],
                modality=study["modality"],
                body_part=study["body_part"],
                study_description=study["study_description"],
                source_type=str(payload.get("source_type", "manual_upload")).strip() or "manual_upload",
                quality_status="pending",
                processing_status="waiting",
                study_time=datetime.now(),
                meta={
                    "priority": study["priority"],
                    "report_status": "not_started",
                    "findings": [],
                    "ai_summary": study["ai_summary"],
                    "upload": {
                        **upload_meta,
                    },
                    "dicom_metadata": dicom_metadata,
                    "series": dicom_payload["series"],
                },
            )
            study["id"] = str(item.id)
            self._persist_series_and_instances(study["id"], grouped_series)
        else:
            self._save_demo_study(str(account.id), study)

        self._write_audit_log(
            account=account,
            study_id=study["id"],
            action="dicom_uploaded",
            target_type="study",
            target_id=study["id"],
            details={
                "modality": study["modality"],
                "body_part": study["body_part"],
                "file_name": upload_name,
                "file_size": upload_size,
                "parser_status": dicom_metadata.get("parser_status", ""),
                "storage_mode": upload_meta.get("storage_mode", "local"),
                "cos_key": upload_meta.get("cos_key", ""),
            },
        )
        return {
            "study_id": study["id"],
            "status": "uploaded",
            "message": "DICOM 文件已上传，并已进入待处理队列。",
            "file_name": upload_name,
            "file_size": upload_size,
            "storage_mode": upload_meta.get("storage_mode", "local"),
            "cos_url": upload_meta.get("cos_url", ""),
        }

    def create_analysis_task(self, study_id: str, account) -> dict[str, Any]:
        study = self._find_study_or_none(study_id, account)
        if study is None:
            return {"study_id": study_id, "status": "not_found"}

        inference_error = ""
        if self._real_inference_enabled():
            try:
                payload = self._run_external_inference(study)
            except (RequestException, ValueError) as exc:
                payload = self._normalize_analysis_payload(
                    study,
                    {
                        "status": "failed",
                        "task_type": self._analysis_profile(study)["task_type"],
                        "model_name": self._analysis_profile(study)["model_name"],
                        "model_version": self._analysis_profile(study)["model_version"],
                        "summary": f"外部影像推理服务调用失败：{exc}",
                        "findings": [],
                        "measurements": [],
                        "overlays": [],
                        "updated_at": int(datetime.now().timestamp()),
                    },
                )
                inference_error = str(exc)
        else:
            payload = self._normalize_analysis_payload(study, self._default_analysis_payload(study))

        if self._has_table("imaging_ai_result") and self._has_table("imaging_study"):
            item = self.create(
                ImagingAiResult,
                study_id=UUID(study_id),
                model_name=payload["model_name"],
                model_version=payload["model_version"],
                task_type=payload["task_type"],
                finding_type=study["body_part"].lower(),
                confidence=str(max((entry["confidence"] for entry in payload["findings"]), default=0)),
                result_status=payload["status"],
                findings=payload["findings"],
                measurements=payload["measurements"],
                overlays=payload["overlays"],
                summary=payload["summary"],
                raw_payload=payload,
            )
            db_study = self.db.session.query(ImagingStudy).filter(
                ImagingStudy.id == UUID(study_id)
            ).one_or_none()
            if db_study is not None:
                meta = dict(db_study.meta or {})
                meta["findings"] = payload["findings"]
                meta["ai_summary"] = payload["summary"]
                meta["report_status"] = meta.get("report_status", "pending_draft") if payload["status"] != "failed" else meta.get("report_status", "not_started")
                meta["priority"] = meta.get("priority", study.get("priority", "normal"))
                self.update(
                    db_study,
                    processing_status="ai_completed" if payload["status"] != "failed" else "awaiting_ai",
                    quality_status="qualified" if db_study.quality_status == "pending" else db_study.quality_status,
                    meta=meta,
                )
            task_id = str(item.id)
        else:
            demo_study = dict(study)
            demo_study["status"] = "ai_completed" if payload["status"] != "failed" else "awaiting_ai"
            demo_study["quality_status"] = "qualified" if demo_study["quality_status"] == "pending" else demo_study["quality_status"]
            demo_study["ai_summary"] = payload["summary"]
            demo_study["findings_count"] = len(payload["findings"])
            if payload["status"] != "failed" and demo_study["report_status"] == "not_started":
                demo_study["report_status"] = "pending_draft"
            self._save_demo_study(str(account.id), demo_study)
            task_id = str(uuid5(NAMESPACE_DNS, f"{study_id}-analysis-task"))
            self._save_demo_analysis_result(
                str(account.id),
                study_id,
                {
                    "task_id": task_id,
                    **payload,
                },
            )

        self._write_audit_log(
            account=account,
            study_id=study_id,
            action="analysis_task_created",
            target_type="analysis",
            target_id=task_id,
            details={
                "task_type": payload["task_type"],
                "status": payload["status"],
                "inference_endpoint": self._inference_endpoint(),
                "error": inference_error,
            },
            success=payload["status"] != "failed",
        )
        return {
            "study_id": study_id,
            "task_id": task_id,
            "status": payload["status"],
            "task_type": payload["task_type"],
            "message": "已调用真实影像推理服务。" if self._real_inference_enabled() and not inference_error else (
                "外部影像推理服务调用失败。" if inference_error else "当前未配置真实影像推理服务，已使用默认演示结果。"
            ),
        }

    def get_analysis_result(self, study_id: str, account) -> dict[str, Any]:
        study = self._find_study_or_none(study_id, account)
        if study is None:
            return {"study_id": study_id, "status": "not_found", "findings": []}

        db_result = self._load_db_analysis_result(study_id)
        if db_result is not None:
            return {"study_id": study_id, **self._normalize_analysis_payload(study, db_result)}

        demo_result = self._load_demo_analysis_map(str(account.id)).get(study_id)
        if demo_result is not None:
            return {"study_id": study_id, **self._normalize_analysis_payload(study, demo_result)}

        if not self._should_expose_default_analysis(study):
            return {
                "study_id": study_id,
                "task_id": "",
                "status": "pending",
                "task_type": "",
                "model_name": "",
                "model_version": "",
                "summary": "当前检查尚未生成结构化分析结果，请先触发分析任务。",
                "findings": [],
                "measurements": [],
                "overlays": [],
                "updated_at": int(datetime.now().timestamp()),
            }

        payload = self._normalize_analysis_payload(study, self._default_analysis_payload(study))
        return {
            "study_id": study_id,
            "task_id": "",
            **payload,
        }

    def get_structured_findings(self, study_id: str, account) -> dict[str, Any]:
        result = self.get_analysis_result(study_id, account)
        return {
            "study_id": study_id,
            "status": result.get("status", "pending"),
            "summary": result.get("summary", ""),
            "findings": result.get("findings", []),
            "measurements": result.get("measurements", []),
        }

    def get_audit_logs(self, study_id: str, account) -> list[dict[str, Any]]:
        studies = self.get_studies(account)
        study = next((item for item in studies if item["id"] == study_id), None)
        if study is None:
            return []

        logs = self._load_db_audit_logs(study_id)
        if logs:
            return logs
        return self._load_demo_audit_logs(str(account.id), study_id)

    def get_review_logs(self, study_id: str, account) -> list[dict[str, Any]]:
        studies = self.get_studies(account)
        study = next((item for item in studies if item["id"] == study_id), None)
        if study is None:
            return []

        logs = self._load_db_review_logs(study_id)
        if logs:
            return logs

        _, reviews = self._load_persisted_state(str(account.id))
        review = reviews.get(study_id)
        if not review:
            return []

        return [
            {
                "id": str(uuid5(NAMESPACE_DNS, f"{study_id}-demo-review")),
                "label": review.get("label", ""),
                "comment": review.get("comment", ""),
                "review_type": "doctor_review",
                "reviewer_id": str(account.id),
                "status": review.get("status", ""),
                "created_at": review.get("updated_at", 0),
            }
        ]

    def get_feedback_stats(self, study_id: str, account) -> dict[str, Any]:
        reviews = self.get_review_logs(study_id, account)
        return self._build_feedback_stats(reviews)

    def save_report_draft(self, study_id: str, content: str, account) -> dict[str, Any]:
        if self._db_tables_ready():
            report = self.db.session.query(ImagingReport).filter(
                ImagingReport.study_id == UUID(study_id)
            ).one_or_none()
            if report is None:
                report = self.create(
                    ImagingReport,
                    study_id=UUID(study_id),
                    template_name="Imaging Draft Template",
                    template_version="v1.0",
                    generation_source="doctor_editing",
                    report_status="doctor_editing",
                    draft_content=content,
                    doctor_notes="Doctor updated the report draft and saved the latest version.",
                )
            else:
                self.update(
                    report,
                    draft_content=content,
                    report_status="doctor_editing",
                    doctor_notes="Doctor updated the report draft and saved the latest version.",
                )
            result = {
                "study_id": study_id,
                "status": "doctor_editing",
                "updated_at": int(report.updated_at.timestamp()) if report.updated_at else 0,
            }
            self._write_audit_log(
                account=account,
                study_id=study_id,
                action="report_draft_saved",
                target_type="report",
                target_id=str(report.id),
                details={"status": "doctor_editing"},
            )
            return result

        state = self._load_state()
        account_state = state.setdefault(str(account.id), {})
        reports = account_state.setdefault("reports", {})
        reports[study_id] = {
            "content": content,
            "status": "doctor_editing",
            "summary": "Doctor updated the report draft and saved the latest version.",
            "updated_at": int(datetime.now().timestamp()),
        }
        self._save_state(state)
        result = {
            "study_id": study_id,
            "status": "doctor_editing",
            "updated_at": reports[study_id]["updated_at"],
        }
        self._write_audit_log(
            account=account,
            study_id=study_id,
            action="report_draft_saved",
            target_type="report",
            target_id=study_id,
            details={"status": "doctor_editing"},
        )
        return result

    def submit_review(self, study_id: str, label: str, comment: str, account) -> dict[str, Any]:
        status_map = {
            "approved": "doctor_reviewed",
            "needs_revision": "doctor_revision_needed",
            "rejected": "doctor_rejected",
        }
        review_status = status_map.get(label, "doctor_reviewed")

        if self._db_tables_ready():
            report = self.db.session.query(ImagingReport).filter(
                ImagingReport.study_id == UUID(study_id)
            ).one_or_none()
            if report is None:
                report = self.create(
                    ImagingReport,
                    study_id=UUID(study_id),
                    template_name="Imaging Draft Template",
                    template_version="v1.0",
                    generation_source="doctor_review",
                    report_status="signed" if label == "approved" else "doctor_editing",
                    draft_content="",
                    doctor_notes="Doctor review submitted.",
                )
            else:
                self.update(
                    report,
                    report_status="signed" if label == "approved" else "doctor_editing",
                    doctor_notes=comment or "Doctor review submitted.",
                )

            review = self.db.session.query(ImagingReview).filter(
                ImagingReview.study_id == UUID(study_id),
                ImagingReview.reviewer_id == account.id,
            ).one_or_none()
            payload = {"status": review_status}
            if review is None:
                review = self.create(
                    ImagingReview,
                    study_id=UUID(study_id),
                    report_id=report.id,
                    reviewer_id=account.id,
                    review_type="doctor_review",
                    review_label=label,
                    comment=comment,
                    review_payload=payload,
                )
            else:
                self.update(
                    review,
                    review_label=label,
                    comment=comment,
                    review_payload=payload,
                    report_id=report.id,
                )
            result = {
                "study_id": study_id,
                "label": label,
                "status": review_status,
                "updated_at": int(review.created_at.timestamp()) if review.created_at else 0,
            }
            self._write_audit_log(
                account=account,
                study_id=study_id,
                action="study_review_submitted",
                target_type="review",
                target_id=str(review.id),
                details={"label": label, "status": review_status},
            )
            return result

        state = self._load_state()
        account_state = state.setdefault(str(account.id), {})
        reviews = account_state.setdefault("reviews", {})
        reports = account_state.setdefault("reports", {})

        reviews[study_id] = {
            "label": label,
            "comment": comment,
            "status": review_status,
            "updated_at": int(datetime.now().timestamp()),
        }

        report = reports.setdefault(study_id, {})
        report["status"] = "signed" if label == "approved" else "doctor_editing"
        report["updated_at"] = int(datetime.now().timestamp())
        if label == "approved":
            report["summary"] = "医生已通过当前草稿，检查可进入归档流程。"
        elif label == "needs_revision":
            report["summary"] = "医生要求补充修订后再进行最终签发。"
        else:
            report["summary"] = "医生驳回当前草稿，需人工重新编写。"

        self._save_state(state)
        result = {
            "study_id": study_id,
            "label": label,
            "status": reviews[study_id]["status"],
            "updated_at": reviews[study_id]["updated_at"],
        }
        self._write_audit_log(
            account=account,
            study_id=study_id,
            action="study_review_submitted",
            target_type="review",
            target_id=study_id,
            details={"label": label, "status": review_status},
        )
        return result
