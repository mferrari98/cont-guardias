# Imagen minimalista Flask - sin curl ni herramientas extra
FROM python:3.12-alpine

WORKDIR /app

# Copiar requirements primero para mejor cache
COPY requirements.txt .

# Instalar dependencias Python --no-cache-dir y --no-deps donde sea posible
RUN pip install --no-cache-dir -r requirements.txt

# Copiar solo archivos necesarios
COPY app.py wsgi.py config.py constants.py ./

# Copiar templates y static
COPY templates/ templates/
COPY static/ static/

# Exponer el puerto
EXPOSE 5000

# Variables de entorno minimalistas
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Health check sin curl (usando wget incluido en Alpine)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:5000/health || exit 1

# Comando optimizado: 1 worker para Alpine (usa menos memoria)
CMD ["gunicorn", "--workers", "1", "--threads", "2", "--bind", "0.0.0.0:5000", "wsgi:app"]