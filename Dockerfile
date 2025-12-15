# Usar una imagen base de Python Alpine más ligera
FROM python:3.12-alpine

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para Pillow y curl
RUN apk add --no-cache \
    jpeg-dev \
    zlib-dev \
    musl-dev \
    gcc \
    curl \
    && rm -rf /var/cache/apk/*

# Copiar el archivo de requisitos y instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Exponer el puerto en el que corre la aplicación
EXPOSE 5000

# Variables de entorno por defecto
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Comando para ejecutar la aplicación con Gunicorn (menos workers para Alpine)
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "wsgi:app"]