# Sistema de Guardias

Backend Flask para gestionar cronogramas de guardias. Se expone via Nginx en
`/guardias/`.

## Configuracion necesaria
- Copiar `.env.example` a `.env` y ajustar valores.

## Desarrollo
```bash
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:5000 wsgi:app
```
