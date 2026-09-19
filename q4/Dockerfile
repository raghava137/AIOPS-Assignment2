# Multi-stage build.
#
# Stage 1 installs the dependencies into a virtualenv using the full
# python:3.12 image, which carries gcc, the dev headers and pip's build
# tooling needed to build any package without a prebuilt wheel.
#
# Stage 2 starts from python:3.12-slim and copies ONLY the finished venv
# across. The compilers, headers, apt lists and pip cache stay behind in the
# builder and never appear in a layer of the final image.

# --- Stage 1: build ---
FROM python:3.12 AS builder

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Stage 2: minimal runtime ---
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
# uvicorn lives in the venv, so the venv's bin must come first on PATH
ENV PATH="/opt/venv/bin:$PATH"

COPY app.py model.joblib ./

EXPOSE 8080
ARG APP_VERSION=v1
ENV APP_VERSION=$APP_VERSION
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
