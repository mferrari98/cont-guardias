# Sistema de Guardias Rotativas

Sistema web para gestionar cronograma de guardias. Dockerizado con opción de red compartida.

## Requisitos
- Docker y Docker Compose
- Git

## Instalación
```bash
git clone <URL>
cd sistema-guardias-rotativas
cp .env.example .env
nano .env
```

## Despliegue

### Opción 1: Individual (puerto 8080)
```bash
./deploy.sh standalone
# o
docker-compose -f docker-compose.standalone.yml up --build
```
Acceso: http://localhost:8080

### Opción 2: Producción con Nginx
```bash
./deploy.sh production
```
- Acceso vía proxy Nginx
- Red interna: `proyectos_network`
- Ver `nginx.conf.example` para configuración

## Configuración (.env)
```bash
CELULAR_CORPORATIVO=tu_teléfono
GUARDIAS=Nombre1,Nombre2,Nombre3,Nombre4
FECHA_REFERENCIA=2025-01-07
GUARDIA_REFERENCIA=Nombre1
DURACION_GUARDIA=14
SECRET_KEY=tu_clave_secreta
```

## Tecnologías
- Flask (Python)
- Docker + Docker Compose
- Gunicorn

## Comandos Útiles
```bash
docker-compose -f docker-compose.standalone.yml logs -f
docker-compose -f docker-compose.production.yml down
```