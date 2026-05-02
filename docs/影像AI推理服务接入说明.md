# 影像 AI 推理服务接入说明

## 1. 当前实现说明

LLMOps 现在已经支持把 `/space/imaging/studies` 的“病灶识别”接到真实外部影像推理服务。

后端入口：

- `imooc-llmops-api/imooc-llmops-api-master/internal/service/imaging_service.py`
- 方法：`create_analysis_task()`

调用逻辑：

1. 前端触发“结构化分析”
2. 后端读取当前检查的基础信息、DICOM 元数据、序列、实例路径、存储引用
3. 后端向外部影像推理服务发起 HTTP POST
4. 推理服务返回结构化结果
5. 平台回写 `ImagingAiResult` 和检查摘要

## 2. 需要配置的环境变量

在 `imooc-llmops-api/imooc-llmops-api-master/.env` 中配置：

```env
IMAGING_INFERENCE_ENDPOINT=
IMAGING_INFERENCE_BASE_URL=
IMAGING_INFERENCE_API_KEY=
IMAGING_INFERENCE_API_HEADER=Authorization
IMAGING_INFERENCE_API_SCHEME=Bearer
IMAGING_INFERENCE_TIMEOUT_SECONDS=120
```

说明：

- `IMAGING_INFERENCE_ENDPOINT`
  直接填写完整推理接口地址，例如：
  `http://127.0.0.1:9000/v1/imaging/analyze`

- `IMAGING_INFERENCE_BASE_URL`
  如果你只想配基础地址，例如：
  `http://127.0.0.1:9000`
  系统会自动拼接成：
  `/v1/imaging/analyze`

- `IMAGING_INFERENCE_API_KEY`
  这是你需要提供的核心 API Key。
  如果你的医学影像 AI 服务要求鉴权，就把对应密钥填在这里。

- `IMAGING_INFERENCE_API_HEADER`
  默认是 `Authorization`，适用于大多数服务。

- `IMAGING_INFERENCE_API_SCHEME`
  默认是 `Bearer`，实际请求头会变成：
  `Authorization: Bearer <IMAGING_INFERENCE_API_KEY>`

## 3. 你现在需要准备什么 API Key

这次接入不是直接调用 OpenAI、Moonshot、Qwen 之类通用大模型 API。

你需要准备的是：

- 你自己的影像推理服务 API Key
  或
- 第三方医学影像 AI 平台分配给你的 API Key

换句话说，当前“病灶识别”所需的不是 `OPENAI_API_KEY`，而是：

```env
IMAGING_INFERENCE_API_KEY=你的影像推理服务密钥
```

## 4. 推理服务需要实现的 HTTP 接口

建议你的推理服务提供：

- `POST /v1/imaging/analyze`

请求头示例：

```http
Authorization: Bearer <IMAGING_INFERENCE_API_KEY>
Content-Type: application/json
```

请求体示例：

```json
{
  "study": {
    "id": "study-id",
    "patient_code": "RAD-2026-0001",
    "patient_name_masked": "Zhang**",
    "modality": "CT",
    "body_part": "Chest",
    "study_description": "胸部平扫 CT",
    "study_time": 1770000000,
    "priority": "normal",
    "status": "awaiting_ai",
    "quality_status": "qualified"
  },
  "dicom_metadata": {},
  "series": [],
  "instances_map": {},
  "upload": {
    "file_name": "demo.zip",
    "stored_path": "D:/.../study.zip",
    "cos_url": "",
    "cos_key": "",
    "storage_mode": "local"
  },
  "requested_model": {
    "task_type": "report_draft_assist",
    "model_name": "chest-ct-report-assistant",
    "model_version": "phase-1-mvp"
  }
}
```

## 5. 推理服务返回格式

返回体建议如下：

```json
{
  "status": "completed",
  "task_type": "report_draft_assist",
  "model_name": "lung-nodule-detector-prod",
  "model_version": "2026.04",
  "summary": "胸部 CT 结构化分析完成，发现 2 条结节线索。",
  "findings": [
    {
      "title": "右上肺结节",
      "confidence": 0.93,
      "description": "右上肺尖后段见 8 mm 实性结节。",
      "location": "right upper lobe",
      "size": "8 mm",
      "risk_level": "medium"
    }
  ],
  "measurements": [],
  "overlays": [],
  "updated_at": 1770000000
}
```

也支持包装在：

```json
{
  "data": {
    "...": "..."
  }
}
```

## 6. 落地建议

如果你的推理服务和 LLMOps 不在同一台机器上，建议：

- 使用 `IMAGING_STORAGE_MODE=hybrid` 或 `cos`
- 让推理服务通过 `cos_url` 或共享存储路径读取 DICOM / 压缩包

如果你的推理服务就是本地部署的 Python 推理服务，建议：

- `IMAGING_INFERENCE_BASE_URL=http://127.0.0.1:9000`
- `IMAGING_INFERENCE_API_KEY=...`

## 7. 当前回退行为

如果没有配置 `IMAGING_INFERENCE_ENDPOINT` 或 `IMAGING_INFERENCE_BASE_URL`：

- 系统仍会回退到当前默认演示结果

如果配置了真实服务但调用失败：

- 页面会显示“分析失败”
- 审计日志会记录失败信息
- 可以在详情页重新触发分析
