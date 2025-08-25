# ===== בסיס פייתון דק (Debian bookworm) =====
FROM python:3.11-slim

# למנוע דיאלוגים בזמן apt-get
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ===== ספריות מערכת ש־WeasyPrint צריך + פונטים עם עברית =====
# הערה: שמות החבילות נכונים ל-bookworm. כולל פונטים:
# - fonts-dejavu (כללי)
# - fonts-freefont-ttf (כולל עברית בסיסית)
# - fonts-noto-core (כולל Noto Sans Hebrew)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi8 \
    shared-mime-info \
    fonts-dejavu \
    fonts-freefont-ttf \
    fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

# ===== תיקיית עבודה =====
WORKDIR /app

# ===== התקנת תלויות פייתון =====
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# ===== קוד האפליקציה =====
# (כולל lesson_app/, templates/, static/, games.json, logo.png, run.py וכו')
COPY . /app

# ===== פורט שהאפליקציה מאזינה עליו =====
ENV PORT=8000
EXPOSE 8000

# ===== הרצה ב-Gunicorn =====
# וורקר אחד מספיק (החבילה החינמית), timeout נדיב ליצירת PDF.
CMD ["sh", "-c", "gunicorn -w 1 --timeout 120 --log-level info -b 0.0.0.0:${PORT:-8000} run:app"]
