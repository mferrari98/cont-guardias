import os
from datetime import datetime

# Datos que se configurarán desde .env (únicos datos sensibles/variables)
CELULAR_CORPORATIVO = os.getenv('CELULAR_CORPORATIVO', '+54 280 123-4567')
GUARDIAS = [g.strip() for g in os.getenv('GUARDIAS', 'Juan,Pedro,Maria,Ana').split(',') if g.strip()]
FECHA_REFERENCIA = os.getenv('FECHA_REFERENCIA', '2025-01-07')
GUARDIA_REFERENCIA = os.getenv('GUARDIA_REFERENCIA', 'Juan')

# Configuración FIJA (no necesita ser configurada)
DURACION_GUARDIA = 14  # Días por guardia
SECRET_KEY = os.getenv('SECRET_KEY', 'sistema-guardias-rotativas-2025-defecto')  # Clave configurable
DEBUG = False  # Siempre False en producción
HOST = '0.0.0.0'
PORT = 5000

# Calcular índice de guardia de referencia automáticamente
try:
    INDICE_REFERENCIA = GUARDIAS.index(GUARDIA_REFERENCIA)
except ValueError:
    INDICE_REFERENCIA = 0
    GUARDIA_REFERENCIA = GUARDIAS[0] if GUARDIAS else 'Juan'

# Colores FIJOS para las guardias (no necesita configuración)
COLORES_BASE = [
    "#A5C9E8",  # Azul claro
    "#A8E6B8",  # Verde claro
    "#F5E5A0",  # Amarillo claro
    "#F5C89B",  # Naranja claro
    "#FFB6C1",  # Rosa claro
    "#E6E6FA",  # Lavanda
    "#98FB98",  # Verde menta claro
    "#F0E68C",  # Caqui claro
]

# Asignar colores automáticamente a las guardias
COLORES = {}
for i, guardia in enumerate(GUARDIAS):
    COLORES[guardia] = COLORES_BASE[i % len(COLORES_BASE)]

# Configuración de APIs (fija)
CLIMA_API_URL = "http://api.weatherapi.com/v1/history.json"
CLIMA_API_KEY = ''  # Dejar vacío para deshabilitar API de clima
CLIMA_CACHE_DURATION = 6 * 60 * 60  # 6 horas