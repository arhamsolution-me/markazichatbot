FROM registry.access.redhat.com/ubi10/python-312-minimal:1790644372

# Application settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=6070 \
    HOST=0.0.0.0 \
    HOME=/app \
    PATH=/app/.local/bin:$PATH \
    FASTEMBED_CACHE_PATH=/app/models/fastembed_cache

WORKDIR /app

# Install OS packages and apply available security updates
USER 0
RUN microdnf update -y && \
    microdnf install -y \
        curl \
        ca-certificates \
        libgomp \
        --setopt=install_weak_deps=0 && \
    microdnf clean all

# Prepare application directories for the non-root user
RUN mkdir -p /app/data/qdrant /app/models/fastembed_cache && \
    chown -R 1001:0 /app && \
    chmod -R g=u /app

# Install Python dependencies
COPY --chown=1001:0 backend/requirements.txt /app/requirements.txt

USER 0
# Upgrade pip/build tools and pin security-fixed versions for Trivy findings:
#   setuptools >=83.0.0  (CVE-2025-47273 HIGH, CVE-2026-59890 MEDIUM)
#   msgpack    >=1.2.1   (GHSA-6v7p-g79w-8964 HIGH)
#   urllib3    >=2.8.0   (CVE-2026-97687 HIGH, CVE-2026-97688 MEDIUM, CVE-2026-97689 HIGH)
RUN python -m pip install --no-cache-dir --upgrade \
        pip \
        "setuptools>=83.0.0" \
        wheel && \
    python -m pip install --no-cache-dir -r requirements.txt && \
    python -m pip install --no-cache-dir --upgrade \
        "msgpack>=1.2.1" \
        "urllib3>=2.8.0" \
        "setuptools>=83.0.0"

# Give the application user access to the installed packages and app files
RUN chown -R 1001:0 /app

USER 1001

# Pre-download FastEmbed model
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='BAAI/bge-small-en-v1.5')"

# Copy application source code
COPY --chown=1001:0 backend/app /app/app
COPY --chown=1001:0 backend/run_server.py /app/run_server.py

EXPOSE 6070

VOLUME ["/app/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:6070/ || exit 1

CMD ["python", "run_server.py"]
