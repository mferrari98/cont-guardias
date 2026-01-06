# Imagen ultra-minimalista Flask
FROM python:3.12-alpine

WORKDIR /app

# Copiar requirements primero para mejor cache
COPY requirements.txt .

# Instalar dependencias Python con flags de optimización
RUN pip install --no-cache-dir --no-compile --no-binary :all: -r requirements.txt

# Copiar solo archivos necesarios (excluyendo .git, README, etc.)
COPY app.py wsgi.py config.py constants.py ./

# Copiar templates y static (minified)
COPY templates/ templates/
COPY static/css/guardias.min.css static/css/
COPY static/css/guardias.css static/css/
COPY static/js/guardias.min.js static/js/
COPY static/img/ static/img/

# Exponer el puerto
EXPOSE 5000

# Variables de entorno minimalistas
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check simple (sin curl/wget - usando Python)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Comando ultra-optimizado: 1 worker, single-thread para Alpine
CMD ["gunicorn", "--workers", "1", "--threads", "1", "--max-requests", "1000", "--max-requests-jitter", "100", "--bind", "0.0.0.0:5000", "wsgi:app"]