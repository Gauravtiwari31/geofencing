# -----------------------------
# MoD Core - Dev-friendly base
# -----------------------------
    FROM ubuntu:22.04

    ENV DEBIAN_FRONTEND=noninteractive \
        PYTHONDONTWRITEBYTECODE=1 \
        PYTHONUNBUFFERED=1
    
    # Basic tools, Python, build deps, and geospatial/postgres client libs
    RUN apt-get update && \
        apt-get install -y --no-install-recommends \
            python3 python3-pip python3-venv \
            build-essential git curl wget ca-certificates openssl \
            postgresql-client libpq-dev \
            gdal-bin libgdal-dev proj-bin libproj-dev \
            libgeos-dev && \
        rm -rf /var/lib/apt/lists/* && \
        ln -sf /usr/bin/python3 /usr/bin/python && \
        pip install --no-cache-dir --upgrade pip
    
    # Working directory where you’ll mount your repo (FastAPI app, etc.)
    WORKDIR /workspace
    
    # (Optional) Create venv to keep the container clean even in dev shells
    # RUN python -m venv /opt/venv && . /opt/venv/bin/activate && pip install --upgrade pip
    # ENV PATH="/opt/venv/bin:$PATH"
    
    # Default shell; you’ll usually `docker run -it ...` and finish installs manually
    CMD ["/bin/bash"]
    
    # Example dev run (map MoD API to 2025, mount your code, and your certs):
    # docker build -t mod_core_base .
    # docker run -it --name mod-core -p 2025:2025 -v /mnt/c/git/geofencing/Ministry_of_Tourism_Application:/workspace -v /mnt/c/git/geofencing/Ministry_of_Tourism_Application/certs:/workspace/certs:ro --init --ipc=host --uts=host mod_core_base
    #
    # Inside the container (example):
    # pip install -r requirements.txt
    # uvicorn app.main:app --host 0.0.0.0 --port 2025 --ssl-keyfile certs/server.key --ssl-certfile certs/server.crt
    