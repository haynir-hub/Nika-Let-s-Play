# ---- Base Python ----
FROM python:3.11-slim

# WeasyPrint system deps (Debian bookworm names)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi8 \
    shared-mime-info \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Python deps
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . /app

# Render supplies PORT via env
ENV PORT=8000
EXPOSE 8000

# TEMP: run via Python to get full traceback (easier to debug)
CMD ["python", "run.py"]
