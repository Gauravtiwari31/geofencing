FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Basic tools + Python
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 python3-pip git curl wget ca-certificates openssl jq && \
    rm -rf /var/lib/apt/lists/* && \
    ln -sf /usr/bin/python3 /usr/bin/python && \
    pip install --no-cache-dir --upgrade pip

WORKDIR /workspace

# Backend deps (FastAPI/HTTPX/MQTT) + serve static frontend
RUN pip install --no-cache-dir uvicorn fastapi httpx paho-mqtt jinja2 python-multipart

# Copy app (you’ll mount in dev; these lines are here for CI builds)
# COPY backend/ /workspace/backend
# COPY frontend/ /workspace/frontend

# Default interactive shell; in dev you’ll run uvicorn manually
CMD ["/bin/bash"]

# Example:
# docker build -t tourist-sim .
# docker run -it --name tourist-sim -p 2040:2040 -v /mnt/c/git/geofencing/Tourist_Application:/workspace -v /mnt/c/git/geofencing/Tourist_Application/backend:/workspace/backend -v /mnt/c/git/geofencing/Tourist_Application/frontend:/workspace/frontend -v /mnt/c/git/geofencing/Tourist_Application/certs:/workspace/certs --init --ipc=host --uts=host tourist-sim
#
# Inside:
# python /workspace/backend/main.py  (or uvicorn backend.main:app --host 0.0.0.0 --port 2040)
