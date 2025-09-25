# -----------------------------------------
# Police SEDI - Dev-friendly base (Python)
# -----------------------------------------
    FROM ubuntu:22.04

    ENV DEBIAN_FRONTEND=noninteractive \
        PYTHONDONTWRITEBYTECODE=1 \
        PYTHONUNBUFFERED=1
    
    # Basic tools, Python, build deps, Node.js, and TLS/HTTP clients
    RUN apt-get update && \
        apt-get install -y --no-install-recommends \
            python3 python3-pip python3-venv \
            build-essential git curl wget ca-certificates openssl \
            postgresql-client libpq-dev \
            nodejs npm && \
        rm -rf /var/lib/apt/lists/* && \
        ln -sf /usr/bin/python3 /usr/bin/python && \
        pip install --no-cache-dir --upgrade pip
    
    WORKDIR /workspace
    CMD ["/bin/bash"]
    
    # Example dev run (map SEDI UI/API to 2035, mount code/certs):
    # docker build -t police_sedi_base .
    # docker run -it --name police-sedi -p 2035:2035 -v /mnt/c/git/geofencing/Police_Department_Application:/workspace -v /mnt/c/git/geofencing/Police_Department_Application/certs:/workspace/certs:ro --init --ipc=host --uts=host police_sedi_base
    #
    # Inside the container (examples):
    # pip install -r requirements.txt
    # # If SEDI is a small FastAPI app serving a static UI + consuming MoD SSE:
    # uvicorn sedi.main:app --host 0.0.0.0 --port 2035 \
    #   --ssl-keyfile certs/sedi.key --ssl-certfile certs/sedi.crt
    #
    # # If you have a React/Vite build already:
    # # - Serve the built assets with a simple Python HTTP server (dev-only):
    # # python -m http.server 2035
    