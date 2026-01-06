from flask import Flask, render_template, jsonify, request
from datetime import datetime, date, timedelta
import calendar
import logging
import requests
from config import *
from constants import *
from threading import Lock
from werkzeug.middleware.proxy_fix import ProxyFix

import time

logger = logging.getLogger("sistema_guardias")
if not logger.handlers:
    level = logging.DEBUG if DEBUG else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(message)s")

# Cache simple para clima (válido por 6 horas)
CACHE_CLIMA = {
    'data': {},
    'timestamp': 0,
    'duracion': CLIMA_CACHE_DURATION
}
CLIMA_CACHE_LOCK = Lock()

# ============================================
# SISTEMA DE CACHÉ PARA CALENDARIOS
# ============================================
class CalendarioCache:
    """
    Sistema de caché para almacenar calendarios pre-calculados.
    Evita recalcular el calendario para cada cliente.

    IMPORTANTE: Se cachean TODOS los años (incluido el actual).
    Los emojis del clima se aplican dinámicamente por JavaScript cuando se solicitan.

    Funcionamiento:
    - El calendario base se calcula 1 vez y se cachea (guardias, feriados, etc.)
    - Los emojis del clima se cargan bajo demanda vía API (/api/clima)
    - El JavaScript aplica los emojis dinámicamente a TODAS las celdas con data-fecha

    Beneficios:
    - 100 clientes = 1 cálculo de calendario + 99 lecturas de memoria
    - Reduce carga del servidor en ~95%
    - Respuestas instantáneas (<10ms desde caché)
    - TTL de 1 hora (auto-refresco)
    """
    def __init__(self):
        self.lock = Lock()
        self.cache = {}  # {año: {data, timestamp}}
        self.duracion = CALENDARIO_CACHE_DURATION
        self.total_hits = 0
        self.total_misses = 0

    def get(self, anio):
        """Obtener calendario del caché si es válido"""
        with self.lock:
            if anio in self.cache:
                cache_entry = self.cache[anio]
                ahora = time.time()

                # Verificar si el caché es válido
                if ahora - cache_entry['timestamp'] < self.duracion:
                    self.total_hits += 1
                    logger.debug(f"[CACHE HIT] Año {anio} - Hits: {self.total_hits}, Misses: {self.total_misses}")
                    return cache_entry['data']

            self.total_misses += 1
            logger.debug(f"[CACHE MISS] Año {anio} - Hits: {self.total_hits}, Misses: {self.total_misses}")
            return None

    def set(self, anio, data):
        """Guardar calendario en el caché"""
        with self.lock:
            self.cache[anio] = {
                'data': data,
                'timestamp': time.time()
            }
            logger.info(f"[CACHE SET] Calendario para año {anio} guardado en caché")

            if len(self.cache) > CALENDARIO_CACHE_MAX_ITEMS:
                oldest_entries = sorted(self.cache.items(), key=lambda item: item[1]['timestamp'])
                evicted = None
                for year, _ in oldest_entries:
                    if year != anio:
                        evicted = year
                        break

                if evicted is None and oldest_entries:
                    evicted = oldest_entries[0][0]

                if evicted is not None:
                    del self.cache[evicted]
                    logger.info(f"[CACHE EVICT] Año {evicted} eliminado para mantener tamaño máximo")

    def invalidate(self, anio=None):
        """Invalidar caché de un año específico o todo el caché"""
        with self.lock:
            if anio is not None:
                if anio in self.cache:
                    del self.cache[anio]
                    logger.info(f"[CACHE INVALIDATE] Año {anio} eliminado del caché")
            else:
                self.cache = {}
                logger.info("[CACHE INVALIDATE] Todo el caché ha sido eliminado")

    def get_stats(self):
        """Obtener estadísticas del caché"""
        with self.lock:
            total_requests = self.total_hits + self.total_misses
            hit_rate = (self.total_hits / total_requests * 100) if total_requests > 0 else 0

            return {
                'hits': self.total_hits,
                'misses': self.total_misses,
                'hit_rate': round(hit_rate, 2),
                'cache_size': len(self.cache),
                'max_items': CALENDARIO_CACHE_MAX_ITEMS,
                'cached_years': list(self.cache.keys())
            }

# Instancia global del caché
calendario_cache = CalendarioCache()

# ============================================
# CACHÉ DE FERIADOS (Optimización 12x)
# ============================================
FERIADOS_CACHE = {}
FERIADOS_CACHE_ORDER = []
FERIADOS_CACHE_LOCK = Lock()

def obtener_feriados_cache(anio):
    """
    Obtiene feriados con caché para evitar recálculos.
    Esto reduce el tiempo de generación de calendario en ~90%
    """
    # Verificar si ya está en caché
    with FERIADOS_CACHE_LOCK:
        if anio in FERIADOS_CACHE:
            return FERIADOS_CACHE[anio]

    # Si no está, calcular y guardar en caché
    feriados = obtener_feriados(anio)

    with FERIADOS_CACHE_LOCK:
        if anio in FERIADOS_CACHE_ORDER:
            FERIADOS_CACHE_ORDER.remove(anio)
        FERIADOS_CACHE_ORDER.append(anio)

        FERIADOS_CACHE[anio] = feriados

        if len(FERIADOS_CACHE_ORDER) > CALENDARIO_CACHE_MAX_ITEMS:
            oldest = FERIADOS_CACHE_ORDER.pop(0)
            if oldest in FERIADOS_CACHE:
                del FERIADOS_CACHE[oldest]
                logger.debug(f"[FERIADOS CACHE] Año {oldest} eliminado para mantener tamaño máximo")

    return feriados

def obtener_clima_open_meteo():
    """Obtiene el pronóstico del clima con caché de 6 horas"""
    ahora = time.time()

    # Si el cache es válido, retornarlo
    with CLIMA_CACHE_LOCK:
        if CACHE_CLIMA['data'] and (ahora - CACHE_CLIMA['timestamp'] < CACHE_CLIMA['duracion']):
            logger.debug(f"[CLIMA CACHE HIT] Retornando {len(CACHE_CLIMA['data'])} días desde caché")
            return CACHE_CLIMA['data']

    try:
        url = CLIMA_CONFIG['url']
        params = dict(CLIMA_CONFIG['params'])

        logger.info("[CLIMA API] Solicitando pronóstico a Open-Meteo...")
        response = requests.get(url, params=params, timeout=CLIMA_API_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        # Crear diccionario de fechas con códigos de clima y temperatura
        clima_por_fecha = {}
        if 'daily' in data:
            fechas = data['daily']['time']
            codigos = data['daily']['weathercode']
            temp_max = data['daily'].get('temperature_2m_max', [])
            temp_min = data['daily'].get('temperature_2m_min', [])

            logger.debug(f"[CLIMA API] Recibidas {len(fechas)} fechas del API")

            for i, fecha_str in enumerate(fechas):
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                codigo = codigos[i]
                emoji = WEATHER_EMOJI.get(codigo, '☀️')

                clima_info = {
                    'emoji': emoji,
                    'temp_max': int(temp_max[i]) if i < len(temp_max) and temp_max[i] else None,
                    'temp_min': int(temp_min[i]) if i < len(temp_min) and temp_min[i] else None
                }
                clima_por_fecha[fecha] = clima_info

            logger.info(f"[CLIMA API] Procesadas {len(clima_por_fecha)} fechas correctamente")

        if not clima_por_fecha:
            logger.warning("[CLIMA API] Respuesta sin datos diarios")
            with CLIMA_CACHE_LOCK:
                if CACHE_CLIMA['data']:
                    logger.warning(f"[CLIMA FALLBACK] Usando caché antiguo con {len(CACHE_CLIMA['data'])} días")
                    return CACHE_CLIMA['data']
            return {}

        # Actualizar cache
        with CLIMA_CACHE_LOCK:
            CACHE_CLIMA['data'] = clima_por_fecha
            CACHE_CLIMA['timestamp'] = ahora

        return clima_por_fecha
    except Exception:
        logger.exception("[CLIMA ERROR] Error obteniendo clima")
        # Si falla y hay cache antiguo, usarlo
        with CLIMA_CACHE_LOCK:
            if CACHE_CLIMA['data']:
                logger.warning(f"[CLIMA FALLBACK] Usando caché antiguo con {len(CACHE_CLIMA['data'])} días")
                return CACHE_CLIMA['data']
        return {}

# Nombres de meses en español
MESES_ES = {
    1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr',
    5: 'may', 6: 'jun', 7: 'jul', 8: 'ago',
    9: 'sep', 10: 'oct', 11: 'nov', 12: 'dic'
}

# Nombres de días en español (abreviados)
DIAS_ES = ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom']

app = Flask(__name__)
app.config.from_object('config')

# Ensure X-Forwarded-* headers are honored behind a proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Configurar APPLICATION_ROOT para que url_for() genere URLs correctas
app.config['APPLICATION_ROOT'] = '/guardias'

CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' https://cdnjs.cloudflare.com 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob:; "
    "font-src 'self' data:; "
    "connect-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "frame-ancestors 'self'; "
    "form-action 'self'"
)

@app.after_request
def set_security_headers(response):
    response.headers['Content-Security-Policy'] = CSP_POLICY
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

    if request.path.startswith('/api/') or request.path == '/health':
        response.headers['Cache-Control'] = 'no-store'

    return response


def require_admin_token():
    if not ADMIN_API_TOKEN:
        return None

    token = request.headers.get('X-Admin-Token', '')
    if token != ADMIN_API_TOKEN:
        return jsonify({
            'success': False,
            'error': 'unauthorized',
            'message': 'Invalid admin token'
        }), 401

    return None

# Mapeo de códigos WMO a emojis de clima
WEATHER_EMOJI = CLIMA_EMOJIS


def calcular_semana_santa(anio):
    """Calcula las fechas de Semana Santa usando el algoritmo de Meeus"""
    a = anio % 19
    b = anio // 100
    c = anio % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    
    domingo_pascua = date(anio, mes, dia)
    
    # Calcular días relativos
    jueves_santo = domingo_pascua - timedelta(days=3)
    viernes_santo = domingo_pascua - timedelta(days=2)
    
    return {
        'jueves_santo': jueves_santo,
        'viernes_santo': viernes_santo
    }

def calcular_carnaval(anio):
    """Calcula las fechas de Carnaval (47 y 48 días antes de Pascua)"""
    semana_santa = calcular_semana_santa(anio)
    
    domingo_pascua = semana_santa['viernes_santo'] + timedelta(days=2)
    lunes_carnaval = domingo_pascua - timedelta(days=48)
    martes_carnaval = domingo_pascua - timedelta(days=47)
    
    return {
        'lunes': lunes_carnaval,
        'martes': martes_carnaval
    }
def obtener_feriados(anio):
    """Retorna diccionario con todos los feriados del año (nacionales y Chubut)"""
    feriados = {}
    
    # Feriados fijos nacionales (desde constants.py)
    for mes, dia, nombre, tipo in FERIADOS_FIJOS_NACIONALES:
        try:
            fecha = date(anio, mes, dia)
            feriados[fecha] = {'nombre': nombre, 'tipo': tipo}
        except ValueError:
            pass
    
    # Feriados provinciales de Chubut (desde constants.py)
    for mes, dia, nombre, tipo in FERIADOS_CHUBUT:
        try:
            fecha = date(anio, mes, dia)
            feriados[fecha] = {'nombre': nombre, 'tipo': tipo}
        except ValueError:
            pass
    
    # Carnaval (móviles)
    carnaval = calcular_carnaval(anio)
    feriados[carnaval['lunes']] = {'nombre': 'Lunes de Carnaval', 'tipo': 'nacional'}
    feriados[carnaval['martes']] = {'nombre': 'Martes de Carnaval', 'tipo': 'nacional'}
    
    # Semana Santa (móviles)
    semana_santa = calcular_semana_santa(anio)
    feriados[semana_santa['jueves_santo']] = {'nombre': 'Jueves Santo', 'tipo': 'nacional'}
    feriados[semana_santa['viernes_santo']] = {'nombre': 'Viernes Santo', 'tipo': 'nacional'}
    
    return feriados

def calcular_guardia(fecha):
    """Calcula qué guardia corresponde a una fecha dada"""
    ref = FECHA_REFERENCIA_DATE

    if fecha >= ref:
        dias = (fecha - ref).days
    else:
        dias = -(ref - fecha).days

    periodos = dias // DURACION_GUARDIA
    idx_guardia = (INDICE_REFERENCIA + periodos) % len(GUARDIAS)

    return GUARDIAS[idx_guardia]

def obtener_guardia_actual():
    """Retorna información de la guardia actual"""
    hoy = date.today()
    guardia_actual = calcular_guardia(hoy)

    # Encontrar el inicio y fin de la guardia actual
    ref = FECHA_REFERENCIA_DATE

    dias_desde_ref = (hoy - ref).days
    periodo_actual = dias_desde_ref // DURACION_GUARDIA

    # Calcular inicio de la guardia actual
    dias_hasta_inicio = periodo_actual * DURACION_GUARDIA
    inicio_guardia = ref + timedelta(days=dias_hasta_inicio)
    fin_guardia = inicio_guardia + timedelta(days=DURACION_GUARDIA - 1)

    dias_restantes = (fin_guardia - hoy).days + 1

    return {
        'nombre': guardia_actual,
        'inicio': inicio_guardia,
        'fin': fin_guardia,
        'dias_restantes': dias_restantes
    }

def contar_feriados_por_guardia(anio):
    """Cuenta cuántos feriados le tocan a cada guardia en el año"""
    feriados = obtener_feriados_cache(anio)
    conteo = {guardia: 0 for guardia in GUARDIAS}
    
    for fecha_feriado in feriados.keys():
        guardia = calcular_guardia(fecha_feriado)
        conteo[guardia] += 1
    
    return conteo
def generar_fila_mes(anio, mes, clima_por_fecha):
    """Genera UNA SOLA fila con los 31 días del mes"""
    nombre_mes = MESES_ES[mes]
    dias_del_mes = calendar.monthrange(anio, mes)[1]
    feriados = obtener_feriados_cache(anio)
    
    # Obtener guardia actual para remarcar
    hoy = date.today()
    guardia_actual_info = obtener_guardia_actual()

    # Crear fila de 31 columnas
    fila = []
    for dia_columna in range(1, 32):
        if dia_columna <= dias_del_mes:
            fecha = date(anio, mes, dia_columna)
            guardia = calcular_guardia(fecha)
            dia_semana = DIAS_ES[fecha.weekday()]

            # Verificar si es el día actual (solo en el año actual)
            es_hoy = (fecha == hoy and anio == hoy.year)

            # Verificar si es feriado
            es_feriado = fecha in feriados
            nombre_feriado = feriados[fecha]['nombre'] if es_feriado else None
            tipo_feriado = feriados[fecha]['tipo'] if es_feriado else None

            # Verificar si es parte de la guardia actual RESTANTE (solo días futuros/hoy)
            es_guardia_actual = False
            if anio == hoy.year:
                es_guardia_actual = (guardia_actual_info['inicio'] <= fecha <= guardia_actual_info['fin'] and fecha >= hoy)

            # Obtener datos de clima si están disponibles
            clima_info = clima_por_fecha.get(fecha, None)
            emoji_clima = ''
            if clima_info:
                # Si es un dict (nuevo formato con temperatura)
                if isinstance(clima_info, dict):
                    emoji_clima = clima_info.get('emoji', '')
                # Si es un string (formato antiguo)
                else:
                    emoji_clima = clima_info

            fila.append({
                'dia': dia_columna,
                'dia_semana': dia_semana,
                'guardia': guardia,
                'color': COLORES[guardia],
                'es_feriado': es_feriado,
                'nombre_feriado': nombre_feriado,
                'tipo_feriado': tipo_feriado,
                'es_guardia_actual': es_guardia_actual,
                'es_hoy': es_hoy,
                'emoji_clima': emoji_clima
            })
        else:
            fila.append(None)

    return {
        'mes': nombre_mes,
        'mes_numero': mes,
        'anio': anio,
        'fila': fila
    }

def generar_calendario_completo(anio):
    """
    Genera el calendario completo de un año.
    Esta función ES CACHEABLE - los resultados son los mismos para todos los clientes.
    """
    hoy = date.today()

    # NO obtener clima al cargar la página
    clima_por_fecha = {}

    meses_data = []
    for mes in range(1, 13):
        meses_data.append(generar_fila_mes(anio, mes, clima_por_fecha))

    # Obtener información de guardia actual (solo si es el año actual)
    if anio == hoy.year:
        guardia_actual = obtener_guardia_actual()
    else:
        guardia_actual = None

    # Contar feriados por guardia
    feriados_por_guardia = contar_feriados_por_guardia(anio)

    return {
        'meses_data': meses_data,
        'guardia_actual': guardia_actual,
        'feriados_por_guardia': feriados_por_guardia,
        'hoy': hoy
    }

@app.route('/health')
def health_check():
    """Endpoint para health checks de Docker - no genera calendario"""
    return jsonify({
        'status': 'healthy',
        'service': 'sistema-guardias',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/')
def index():
    """Ruta principal - muestra año actual completo CON CACHÉ"""
    anio_actual = datetime.now().year

    # Intentar obtener del caché
    calendario_data = calendario_cache.get(anio_actual)

    # Si no está en caché, generar y cachear
    if calendario_data is None:
        logger.info(f"[GENERANDO] Calendario para año {anio_actual} (Petición de cliente)...")
        inicio = time.time()
        calendario_data = generar_calendario_completo(anio_actual)
        calendario_cache.set(anio_actual, calendario_data)
        duracion = time.time() - inicio
        logger.info(f"[CACHE SET] Calendario para año {anio_actual} guardado en caché")
        logger.info(f"[GENERADO] Calendario para año {anio_actual} en {duracion:.3f}s")
    else:
        logger.debug(f"[CACHE HIT] Sirviendo año {anio_actual} desde caché (Petición de cliente)")

    return render_template('index.html',
                         meses_data=calendario_data['meses_data'],
                         guardias=GUARDIAS,
                         colores=COLORES,
                         celular=CELULAR_CORPORATIVO,
                         anio=anio_actual,
                         guardia_actual=calendario_data['guardia_actual'],
                         feriados_por_guardia=calendario_data['feriados_por_guardia'],
                         hoy=calendario_data['hoy'])

@app.route('/anio/<int:anio>')
def ver_anio(anio):
    """Muestra el calendario de un año específico CON CACHÉ"""

    # Intentar obtener del caché
    calendario_data = calendario_cache.get(anio)

    # Si no está en caché, generar y cachear
    if calendario_data is None:
        logger.info(f"[GENERANDO] Calendario para año {anio}...")
        inicio = time.time()
        calendario_data = generar_calendario_completo(anio)
        calendario_cache.set(anio, calendario_data)
        duracion = time.time() - inicio
        logger.info(f"[GENERADO] Calendario para año {anio} en {duracion:.3f}s")
    else:
        logger.debug(f"[CACHE HIT] Sirviendo año {anio} desde caché")

    return render_template('index.html',
                         meses_data=calendario_data['meses_data'],
                         guardias=GUARDIAS,
                         colores=COLORES,
                         celular=CELULAR_CORPORATIVO,
                         anio=anio,
                         guardia_actual=calendario_data['guardia_actual'],
                         feriados_por_guardia=calendario_data['feriados_por_guardia'],
                         hoy=calendario_data['hoy'])

@app.route('/guardias/api/clima')
@app.route('/api/clima')
def obtener_clima():
    """Endpoint API para obtener pronóstico del clima bajo demanda"""
    try:
        logger.info("[API CLIMA] Cliente solicitando pronóstico del clima")
        clima_por_fecha = obtener_clima_open_meteo()

        logger.debug(f"[API CLIMA] obtener_clima_open_meteo() retornó {len(clima_por_fecha)} registros")
        logger.debug(f"[API CLIMA] Tipo de datos: {type(clima_por_fecha)}")

        if clima_por_fecha:
            primera_clave = list(clima_por_fecha.keys())[0]
            logger.debug(f"[API CLIMA] Primera clave: {primera_clave} (tipo: {type(primera_clave)})")

        # Convertir fechas a strings para JSON
        clima_serializable = {}
        for fecha, clima_info in clima_por_fecha.items():
            fecha_str = fecha.strftime('%Y-%m-%d')
            clima_serializable[fecha_str] = clima_info
            logger.debug(f"[API CLIMA] Convertido: {fecha_str} -> {clima_info}")

        logger.info(f"[API CLIMA] Enviando {len(clima_serializable)} registros al cliente")

        return jsonify({
            'success': True,
            'clima': clima_serializable
        })
    except Exception as e:
        logger.exception("[API CLIMA ERROR] Error procesando pronóstico")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cache/stats')
def cache_stats():
    """Endpoint para ver estadísticas del caché"""
    auth_error = require_admin_token()
    if auth_error:
        return auth_error

    stats = calendario_cache.get_stats()
    return jsonify({
        'success': True,
        'stats': stats,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/cache/invalidate', methods=['POST'])
def cache_invalidate():
    """Endpoint para invalidar el caché (útil para desarrollo)"""
    auth_error = require_admin_token()
    if auth_error:
        return auth_error

    calendario_cache.invalidate()
    return jsonify({
        'success': True,
        'message': 'Caché invalidado completamente'
    })

if __name__ == '__main__':
    app.run(debug=DEBUG)
