# Constantes del Sistema de Guardias

# Meses en español
MESES_ES = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
]

# Feriados fijos nacionales (mes, día, nombre, tipo)
FERIADOS_FIJOS_NACIONALES = [
    (1, 1, 'Año Nuevo', 'nacional'),
    (3, 24, 'Día de la Memoria', 'nacional'),
    (4, 2, 'Día del Veterano y de los Caídos en la Guerra de Malvinas', 'nacional'),
    (5, 1, 'Día del Trabajador', 'nacional'),
    (5, 25, 'Día de la Revolución de Mayo', 'nacional'),
    (6, 20, 'Día Paso a la Inmortalidad del General Manuel Belgrano', 'nacional'),
    (7, 9, 'Día de la Independencia', 'nacional'),
    (8, 17, 'Paso a la Inmortalidad del General José de San Martín', 'nacional'),
    (10, 12, 'Día del Respeto a la Diversidad Cultural', 'nacional'),
    (11, 20, 'Día de la Soberanía Nacional', 'nacional'),
    (12, 8, 'Inmaculada Concepción de María', 'nacional'),
    (12, 25, 'Navidad', 'nacional'),
]

# Feriados provinciales de Chubut
FERIADOS_CHUBUT = [
    (4, 30, 'Plebiscito 1902 (Valle 16 de Octubre / Trevelin)', 'provincial'),
    (7, 28, 'Gesta Galesa (llegada de inmigrantes galeses)', 'provincial'),
    (10, 28, 'Fundación del Chubut', 'provincial'),
    (11, 3, 'Tehuelches y Mapuches declaran lealtad a la bandera Argentina', 'provincial'),
    (12, 13, 'Día del Petróleo', 'provincial'),
]

# Configuración de API de clima
CLIMA_CONFIG = {
    'url': 'https://api.open-meteo.com/v1/forecast',
    'params': {
        'latitude': -42.7692,
        'longitude': -65.0386,
        'daily': 'weathercode,temperature_2m_max,temperature_2m_min',
        'timezone': 'America/Argentina/Buenos_Aires',
        'forecast_days': 7
    }
}

# Emojis para clima (código Open-Meteo -> emoji)
CLIMA_EMOJIS = {
    0: '☀️',   # Despejado
    1: '🌤️',   # Principalmente despejado
    2: '⛅',   # Parcialmente nublado
    3: '☁️',   # Nublado
    45: '🌫️',  # Neblina
    48: '🌫️',  # Neblina con escarcha
    51: '🌦️',  # Llovizna ligera
    53: '🌦️',  # Llovizna moderada
    55: '🌦️',  # Llovizna densa
    56: '🌨️',  # Llovizna helada ligera
    57: '🌨️',  # Llovizna helada densa
    61: '🌧️',  # Lluvia ligera
    63: '🌧️',  # Lluvia moderada
    65: '🌧️',  # Lluvia intensa
    66: '🌨️',  # Lluvia helada ligera
    67: '🌨️',  # Lluvia helada intensa
    71: '🌨️',  # Nieve ligera
    73: '🌨️',  # Nieve moderada
    75: '❄️',  # Nieve intensa
    80: '⛈️',  # Chubascos ligeros
    81: '⛈️',  # Chubascos moderados
    82: '⛈️',  # Chubascos violentos
    95: '⛈️',  # Tormenta ligera
    96: '⛈️',  # Tormenta con granizo ligero
    99: '⛈️',  # Tormenta con granizo intensa
}

# Efectos visuales para clima
CLIMA_EFFECTS = {
    0: 'sunny',     # Sol brillante
    1: 'partly-sunny',
    2: 'cloudy',
    3: 'overcast',
    45: 'foggy',
    48: 'foggy',
    51: 'drizzle',
    53: 'drizzle',
    55: 'drizzle',
    61: 'rainy',
    63: 'rainy',
    65: 'heavy-rain',
    71: 'snowy',
    73: 'snowy',
    75: 'heavy-snow',
    80: 'showers',
    81: 'showers',
    82: 'heavy-showers',
    95: 'thunderstorm',
    96: 'thunderstorm',
    99: 'severe-thunderstorm',
}