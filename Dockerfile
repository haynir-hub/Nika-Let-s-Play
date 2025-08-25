FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0 \
    shared-mime-info fonts-dejavu && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
ENV PORT=8000
EXPOSE 8000
CMD ["sh","-c","gunicorn -b 0.0.0.0:${PORT:-8000} run:app"]
