ARG PYTHON_IMAGE=python:3.11-slim
FROM ${PYTHON_IMAGE}

WORKDIR /app

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_DEFAULT_TIMEOUT=120

ARG APT_MIRROR=deb.debian.org
ARG PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_EXTRA_INDEX_URL=
ARG PYTHON_REQUIREMENTS_FILE=requirements-linux.txt

# Replace Debian mirrors when building in mainland China while remaining
# compatible with both sources.list and debian.sources layouts.
RUN sed -i "s/deb.debian.org/${APT_MIRROR}/g" /etc/apt/sources.list.d/debian.sources 2>/dev/null || true \
    && sed -i "s/security.debian.org/${APT_MIRROR}/g" /etc/apt/sources.list.d/debian.sources 2>/dev/null || true \
    && sed -i "s/deb.debian.org/${APT_MIRROR}/g" /etc/apt/sources.list 2>/dev/null || true \
    && sed -i "s/security.debian.org/${APT_MIRROR}/g" /etc/apt/sources.list 2>/dev/null || true \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        g++ \
        libpq-dev \
        pkg-config \
        libmagic1 \
        libmagic-dev \
        poppler-utils \
        libglib2.0-0 \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY constraints.txt requirements.txt requirements-linux.txt ./

# Prefer wheels first to reduce Linux source-build failures.
RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --prefer-binary \
        --index-url ${PIP_INDEX_URL} \
        --extra-index-url ${PIP_EXTRA_INDEX_URL} \
        -r ${PYTHON_REQUIREMENTS_FILE}

COPY . .

EXPOSE 8000

CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "app.http.app:app"]
