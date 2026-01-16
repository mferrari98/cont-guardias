import os
import logging
from datetime import datetime

logger = logging.getLogger("sistema_guardias")

# Datos que se configurarán desde .env (únicos datos sensibles/variables)
CELULAR_CORPORATIVO = os.getenv('CELULAR_CORPORATIVO', '+54 280 123-4567')
DEFAULT_GUARDIAS = 'Juan,Pedro,Maria,Ana'
GUARDIAS = [g.strip() for g in os.getenv('GUARDIAS', DEFAULT_GUARDIAS).split(',') if g.strip()]
if not GUARDIAS:
    GUARDIAS = [g.strip() for g in DEFAULT_GUARDIAS.split(',') if g.strip()]

FECHA_REFERENCIA_RAW = os.getenv('FECHA_REFERENCIA', '2025-01-07')
FECHA_REFERENCIA = FECHA_REFERENCIA_RAW
GUARDIA_REFERENCIA = os.getenv('GUARDIA_REFERENCIA', 'Juan')
if GUARDIA_REFERENCIA not in GUARDIAS:
    logger.warning('GUARDIA_REFERENCIA invalida: %s. Usando %s', GUARDIA_REFERENCIA, GUARDIAS[0])
    GUARDIA_REFERENCIA = GUARDIAS[0]

try:
    FECHA_REFERENCIA_DATE = datetime.strptime(FECHA_REFERENCIA_RAW, '%Y-%m-%d').date()
except ValueError:
    logger.warning('FECHA_REFERENCIA invalida: %s. Usando 2025-01-07', FECHA_REFERENCIA_RAW)
    FECHA_REFERENCIA_DATE = datetime.strptime('2025-01-07', '%Y-%m-%d').date()
    FECHA_REFERENCIA = '2025-01-07'

# Configuración FIJA (no necesita ser configurada)
DURACION_GUARDIA = 14  # Días por guardia
DEFAULT_SECRET_KEY = 'sistema-guardias-rotativas-2025-defecto'
SECRET_KEY = os.getenv('SECRET_KEY', DEFAULT_SECRET_KEY)  # Clave configurable
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
HOST = '0.0.0.0'
PORT = 5000

if not DEBUG and SECRET_KEY == DEFAULT_SECRET_KEY:
    logger.warning('SECRET_KEY por defecto en uso. Configurar SECRET_KEY en .env')

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
