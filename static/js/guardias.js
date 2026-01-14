// ============================================
// INICIALIZACIÓN
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    highlightToday();
    // aplicarDegradadoGuardiaActual(); // ELIMINADO: ya no mostramos días restantes
    initLeyendaFilter();
    initControls();

    // NO cargar pronóstico automáticamente
    // El usuario debe hacer click en el botón
});

// ============================================
// CONTROLES Y DATOS DE PAGINA
// ============================================
function getAnioActual() {
    const calendario = document.getElementById('calendario-captura');
    const anioValue = calendario ? calendario.getAttribute('data-anio') : '';
    const anio = anioValue ? Number(anioValue) : NaN;
    return Number.isFinite(anio) ? anio : new Date().getFullYear();
}

function initControls() {
    const btnClima = document.getElementById('btn-clima');
    if (btnClima) {
        btnClima.addEventListener('click', solicitarPronostico);
    }

    const yearButtons = document.querySelectorAll('[data-year-delta]');
    yearButtons.forEach(button => {
        button.addEventListener('click', () => {
            const deltaValue = button.getAttribute('data-year-delta') || '0';
            const delta = Number(deltaValue);
            if (!Number.isFinite(delta)) {
                return;
            }
            cambiarAnio(delta);
        });
    });

    const btnDownload = document.getElementById('btn-download');
    if (btnDownload) {
        btnDownload.addEventListener('click', descargarCalendario);
    }
}

function cambiarAnio(delta) {
    const anioActual = getAnioActual();
    window.location.href = '/guardias/anio/' + (anioActual + delta);
}

function descargarCalendario() {
    const elemento = document.getElementById('calendario-captura');
    const btnDownload = document.getElementById('btn-download');

    if (!elemento || !btnDownload) {
        return;
    }

    const anioActual = getAnioActual();

    btnDownload.textContent = 'Generando...';
    btnDownload.disabled = true;

    const wrapper = document.createElement('div');
    wrapper.style.cssText = `
        background: ${getComputedStyle(elemento).backgroundColor};
        padding: 20px;
        display: inline-block;
    `;

    const titulo = document.createElement('h2');
    titulo.textContent = 'Cronograma de Guardias ' + anioActual;
    titulo.style.cssText = `
        text-align: center;
        margin-bottom: 15px;
        color: ${getComputedStyle(document.body).color};
        font-family: ${getComputedStyle(document.body).fontFamily};
    `;

    const tablaClone = elemento.cloneNode(true);
    const anchoTabla = elemento.scrollWidth || elemento.offsetWidth;
    const altoTabla = elemento.scrollHeight || elemento.offsetHeight;
    tablaClone.style.overflow = 'visible';
    tablaClone.style.width = `${anchoTabla}px`;
    tablaClone.style.maxWidth = 'none';

    wrapper.appendChild(titulo);
    wrapper.appendChild(tablaClone);
    document.body.appendChild(wrapper);

    const anchoWrapper = wrapper.scrollWidth;
    const altoWrapper = wrapper.scrollHeight;

    html2canvas(wrapper, {
        backgroundColor: getComputedStyle(document.body).backgroundColor,
        scale: 2,
        width: anchoWrapper,
        height: altoWrapper,
        windowWidth: anchoWrapper,
        windowHeight: altoWrapper
    }).then(canvas => {
        const link = document.createElement('a');
        link.download = 'cronograma-guardias-' + anioActual + '.png';
        link.href = canvas.toDataURL();
        link.click();

        document.body.removeChild(wrapper);

        btnDownload.textContent = 'Descargar calendario';
        btnDownload.disabled = false;
    });
}

// ============================================
// CARGAR PRONÓSTICO ASÍNCRONO AL INICIAR
// ============================================
function getClimaUrl(btn) {
    if (btn && btn.dataset && btn.dataset.climaUrl) {
        return btn.dataset.climaUrl;
    }

    const path = window.location.pathname || '';
    return path.includes('/guardias') ? '/guardias/api/clima' : '/api/clima';
}

function cargarPronosticoAsincrono() {
    const btn = document.getElementById('btn-clima');
    if (!btn) return;

    const climaUrl = getClimaUrl(btn);

    // Cambiar icono del botón a "cargando"
    btn.innerHTML = '<span class="btn-icon">⏳</span>';
    btn.disabled = true;
    btn.title = 'Cargando pronóstico...';

    fetch(climaUrl)
        .then(response => response.json())
        .then(data => {
            console.log('Respuesta del API:', data);
            const tieneDatos = data && data.clima && Object.keys(data.clima).length > 0;

            if (data.success && tieneDatos) {
                aplicarPronostico(data.clima);

                // Volver al icono original y ocultar el botón
                btn.innerHTML = '<span class="btn-icon">🌤️</span>';
                btn.title = 'Pronóstico cargado';
                btn.style.opacity = '0.5';
                btn.disabled = true;

                // Mostrar notificación
                mostrarNotificacion('✅ Pronóstico cargado correctamente');
            } else {
                btn.innerHTML = '<span class="btn-icon">❌</span>';
                btn.title = 'Error al cargar - Click para reintentar';
                btn.disabled = false;
                mostrarNotificacion('❌ Error al cargar el pronóstico');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            btn.innerHTML = '<span class="btn-icon">🌤️</span>';
            btn.title = 'Error - Click para reintentar';
            btn.disabled = false;
            mostrarNotificacion('❌ Error de conexión');
        });
}

// ============================================
// NOTIFICACIÓN FLOTANTE
// ============================================
function mostrarNotificacion(mensaje) {
    // Eliminar notificación anterior si existe
    const notifAnterior = document.getElementById('notificacion-clima');
    if (notifAnterior) {
        notifAnterior.remove();
    }

    const notif = document.createElement('div');
    notif.id = 'notificacion-clima';
    notif.className = 'notificacion-clima';
    notif.textContent = mensaje;
    document.body.appendChild(notif);

    // Animar entrada
    setTimeout(() => notif.classList.add('show'), 10);

    // Eliminar después de 3 segundos
    setTimeout(() => {
        notif.classList.remove('show');
        setTimeout(() => notif.remove(), 300);
    }, 3000);
}

// ============================================
// SOLICITAR PRONÓSTICO MANUALMENTE (POR SI FALLA)
// ============================================
function solicitarPronostico() {
    const btn = document.getElementById('btn-clima');
    if (!btn) return;

    const climaUrl = getClimaUrl(btn);

    btn.innerHTML = '<span class="btn-clima-text">⏳</span>';
    btn.disabled = true;
    btn.title = 'Cargando...';
    btn.style.opacity = '1';

    fetch(climaUrl)
        .then(response => response.json())
        .then(data => {
            console.log('Respuesta manual del API:', data);
            const tieneDatos = data && data.clima && Object.keys(data.clima).length > 0;

            if (data.success && tieneDatos) {
                aplicarPronostico(data.clima);
                btn.innerHTML = '<span class="btn-clima-text">✅ Cargado</span>';
                btn.title = 'Pronóstico cargado';
                btn.style.opacity = '0.7';
                btn.disabled = true;
                mostrarNotificacion('✅ Pronóstico cargado correctamente');
            } else {
                btn.innerHTML = '<span class="btn-clima-text">❌ Error</span>';
                btn.title = 'Error - Click para reintentar';
                btn.disabled = false;
                mostrarNotificacion('❌ Error al cargar');
                setTimeout(() => {
                    btn.innerHTML = '<span class="btn-clima-text">Solicitar Pronóstico</span>';
                }, 2000);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            btn.innerHTML = '<span class="btn-clima-text">❌ Error</span>';
            btn.title = 'Error - Click para reintentar';
            btn.disabled = false;
            mostrarNotificacion('❌ Error de conexión');
            setTimeout(() => {
                btn.innerHTML = '<span class="btn-clima-text">Solicitar Pronóstico</span>';
            }, 2000);
        });
}

// ============================================
// APLICAR PRONÓSTICO A LAS CELDAS
// ============================================
function aplicarPronostico(climaData) {
    console.log('Aplicando pronóstico a las celdas:', Object.keys(climaData).length, 'fechas');
    console.log('Datos completos:', climaData);
    console.log('Primera fecha en datos:', Object.keys(climaData)[0]);

    // Obtener fecha de hoy en formato YYYY-MM-DD (zona horaria local)
    const hoy = new Date();
    const año = hoy.getFullYear();
    const mes = String(hoy.getMonth() + 1).padStart(2, '0');
    const dia = String(hoy.getDate()).padStart(2, '0');
    const hoyStr = `${año}-${mes}-${dia}`;
    console.log('Fecha de hoy (local):', hoyStr);

    let celdasActualizadas = 0;
    let celdasEncontradas = 0;

    Object.keys(climaData).forEach(fecha => {
        const climaInfo = climaData[fecha];
        const celdas = document.querySelectorAll(`.dia-celda[data-fecha="${fecha}"]`);
        celdasEncontradas += celdas.length;

        // El API puede retornar string (solo emoji) o objeto {emoji, temp_max, temp_min}
        let emoji;
        let tempMax = null;
        let tempMin = null;

        if (typeof climaInfo === 'string') {
            emoji = climaInfo;
            console.log(`Fecha ${fecha}: formato STRING, no hay temperaturas`);
        } else if (typeof climaInfo === 'object') {
            emoji = climaInfo.emoji;
            tempMax = climaInfo.temp_max;
            tempMin = climaInfo.temp_min;
            console.log(`Fecha ${fecha}: formato OBJETO, temp_max=${tempMax}, temp_min=${tempMin}`);
        } else {
            console.error(`Formato inesperado para fecha ${fecha}:`, climaInfo);
            return;
        }

        console.log(`Fecha ${fecha}: encontradas ${celdas.length} celdas, emoji: ${emoji}`);

        celdas.forEach(celda => {
            const fechaCelda = celda.getAttribute('data-fecha');
            const esGuardiaRestante = celda.classList.contains('guardia-actual-highlight');
            const esHoy = celda.classList.contains('today');

            console.log(`  - Celda fecha="${fechaCelda}": guardia-restante=${esGuardiaRestante}, hoy=${esHoy}`);

            // Aplicar emoji a TODAS las celdas que tengan pronóstico (no solo guardia actual o hoy)
            // Esto permite ver el pronóstico completo cuando se solicita
            let emojiSpan = celda.querySelector('.clima-emoji');
            if (!emojiSpan) {
                emojiSpan = document.createElement('span');
                emojiSpan.className = 'clima-emoji';
                celda.appendChild(emojiSpan);
            }
            emojiSpan.textContent = emoji;

            const maxVal = (tempMax !== null && tempMax !== undefined && tempMax !== '') ? Number(tempMax) : null;
            const minVal = (tempMin !== null && tempMin !== undefined && tempMin !== '') ? Number(tempMin) : null;
            let tempAvg = null;

            if (Number.isFinite(maxVal) && Number.isFinite(minVal)) {
                tempAvg = Math.round((maxVal + minVal) / 2);
            } else if (Number.isFinite(maxVal)) {
                tempAvg = Math.round(maxVal);
            } else if (Number.isFinite(minVal)) {
                tempAvg = Math.round(minVal);
            }

            const tempSpan = celda.querySelector('.clima-temp');
            if (tempSpan) {
                tempSpan.remove();
            }

            celdasActualizadas++;

            // Guardar datos de temperatura en el elemento
            celda.setAttribute('data-temp-max', tempMax ?? '');
            celda.setAttribute('data-temp-min', tempMin ?? '');
            celda.setAttribute('data-temp-avg', tempAvg ?? '');

            // Guardar info para tooltip personalizado
            celda.setAttribute('data-clima-emoji', emoji);

            // Agregar eventos para tooltip personalizado
            celda.addEventListener('mouseenter', mostrarTooltipClima);
            celda.addEventListener('mouseleave', ocultarTooltipClima);
        });
    });

    console.log(`Total de celdas encontradas: ${celdasEncontradas}`);
    console.log(`Total de celdas actualizadas con pronóstico: ${celdasActualizadas}`);
}

// ============================================
// TOOLTIP PERSONALIZADO DE CLIMA
// ============================================
function mostrarTooltipClima(event) {
    const celda = event.currentTarget;
    const guardia = celda.getAttribute('data-guardia');
    const emoji = celda.getAttribute('data-clima-emoji');
    const tempAvg = celda.getAttribute('data-temp-avg');

    // Crear tooltip
    const tooltip = document.createElement('div');
    tooltip.id = 'clima-tooltip-custom';
    tooltip.className = 'clima-tooltip-custom';

    let contenido = `<div class="tooltip-guardia-name">${guardia}</div>`;
    contenido += `<div class="tooltip-clima-emoji">${emoji}</div>`;

    if (tempAvg && tempAvg !== 'null' && tempAvg !== '') {
        contenido += `<div class="tooltip-temps">Temp. media: ${tempAvg}°C</div>`;
    }

    tooltip.innerHTML = contenido;
    document.body.appendChild(tooltip);

    // Posicionar tooltip
    const rect = celda.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();

    tooltip.style.left = rect.left + (rect.width / 2) - (tooltipRect.width / 2) + 'px';
    tooltip.style.top = rect.top - tooltipRect.height - 10 + window.scrollY + 'px';
}

function ocultarTooltipClima() {
    const tooltip = document.getElementById('clima-tooltip-custom');
    if (tooltip) {
        tooltip.remove();
    }
}

// ============================================
// MODO OSCURO CON TOGGLE MEJORADO
// ============================================
function initTheme() {
    const themeCheckbox = document.getElementById('theme-checkbox');
    const html = document.documentElement;

    const THEME_STORAGE_KEY = 'portal_theme';
    const LEGACY_THEME_STORAGE_KEY = 'theme';

    const applyTheme = (value) => {
        const nextTheme = value === 'light' ? 'light' : 'dark';
        html.setAttribute('data-theme', nextTheme);
        if (themeCheckbox) {
            themeCheckbox.checked = nextTheme === 'dark';
        }
        return nextTheme;
    };

    const persistTheme = (value) => {
        localStorage.setItem(THEME_STORAGE_KEY, value);
        localStorage.setItem(LEGACY_THEME_STORAGE_KEY, value);
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: value } }));
    };

    // Cargar tema guardado o usar dark por defecto
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY)
        || localStorage.getItem(LEGACY_THEME_STORAGE_KEY)
        || 'dark';
    const appliedTheme = applyTheme(savedTheme);
    persistTheme(appliedTheme);

    // Listener para cambios
    if (themeCheckbox) {
        themeCheckbox.addEventListener('change', function() {
            const newTheme = this.checked ? 'dark' : 'light';
            const updatedTheme = applyTheme(newTheme);
            persistTheme(updatedTheme);
        });
    }

    window.addEventListener('storage', function(event) {
        if (event.key === THEME_STORAGE_KEY || event.key === LEGACY_THEME_STORAGE_KEY) {
            if (event.newValue) {
                applyTheme(event.newValue);
            }
        }
    });

    window.addEventListener('themeChanged', function(event) {
        const customEvent = event;
        if (customEvent.detail && customEvent.detail.theme) {
            applyTheme(customEvent.detail.theme);
        }
    });
}

// ============================================
// DESTACAR DÍA ACTUAL
// ============================================
function highlightToday() {
    // Buscar todas las celdas que tienen data-es-hoy="True"
    const todasLasCeldas = document.querySelectorAll('.dia-celda[data-es-hoy="True"]');

    todasLasCeldas.forEach(celda => {
        celda.classList.add('today');
    });
}

// ============================================
// DEGRADADO GRADUAL EN DÍAS RESTANTES DE GUARDIA
// ============================================
// FUNCIÓN ELIMINADA: Ya no mostramos indicadores de días restantes
// Solo mantenemos el indicador del día actual

// ============================================
// FILTRO DE LEYENDA CON TOOLTIP
// ============================================
let filtroActivo = null;

function initLeyendaFilter() {
    const leyendaItems = document.querySelectorAll('.leyenda-item');

    leyendaItems.forEach(item => {
        item.style.cursor = 'pointer';

        // Click para filtrar
        item.addEventListener('click', function() {
            const guardiaName = this.getAttribute('data-guardia');
            const feriadosCount = this.getAttribute('data-feriados');

            if (filtroActivo === guardiaName) {
                desactivarFiltro();
                filtroActivo = null;
                ocultarTooltip();
            } else {
                activarFiltro(guardiaName);
                filtroActivo = guardiaName;
                mostrarInfoGuardia(guardiaName, feriadosCount);
            }
        });
    });
}

function activarFiltro(guardiaName) {
    const leyendaItems = document.querySelectorAll('.leyenda-item');
    const todasLasCeldas = document.querySelectorAll('.dia-celda');

    leyendaItems.forEach(item => {
        if (item.getAttribute('data-guardia') === guardiaName) {
            item.style.opacity = '1';
            item.style.transform = 'scale(1.05)';
            item.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.3)';
        } else {
            item.style.opacity = '0.4';
            item.style.filter = 'grayscale(100%)';
        }
    });

    todasLasCeldas.forEach(celda => {
        const guardiaData = celda.getAttribute('data-guardia');

        if (guardiaData && guardiaData === guardiaName) {
            celda.style.opacity = '1';
            celda.style.filter = 'none';
        } else {
            celda.style.opacity = '0.3';
            celda.style.filter = 'grayscale(80%)';
        }
    });
}

function desactivarFiltro() {
    const leyendaItems = document.querySelectorAll('.leyenda-item');
    const todasLasCeldas = document.querySelectorAll('.dia-celda');

    leyendaItems.forEach(item => {
        item.style.opacity = '1';
        item.style.transform = 'scale(1)';
        item.style.boxShadow = '';
        item.style.filter = 'none';
    });

    todasLasCeldas.forEach(celda => {
        celda.style.opacity = '1';
        celda.style.filter = 'none';
    });
}

// ============================================
// CALCULAR Y MOSTRAR INFO DE GUARDIA
// ============================================
function mostrarInfoGuardia(guardiaName, feriadosCount) {
    const hoy = new Date();
    const info = calcularProximaGuardia(guardiaName, hoy);

    ocultarTooltip();

    const tooltip = document.createElement('div');
    tooltip.id = 'guardia-tooltip';
    tooltip.className = 'guardia-tooltip';

    let mensaje = '';
    if (info.estaDeGuardia) {
        mensaje = `
            <div class="tooltip-title">${guardiaName}</div>
            <div class="tooltip-detail"><strong>Guardia actual</strong></div>
            <div class="tooltip-detail">Hasta: ${info.fechaFin}</div>
            <div class="tooltip-detail">Quedan: ${info.diasRestantes} días</div>
            <div class="tooltip-feriados">
                <div class="feriados-count">${feriadosCount} feriados/año</div>
            </div>
        `;
    } else {
        mensaje = `
            <div class="tooltip-title">${guardiaName}</div>
            <div class="tooltip-detail"><strong>Próxima guardia</strong></div>
            <div class="tooltip-detail">En ${info.diasHastaProxima} días</div>
            <div class="tooltip-detail">${info.fechaProxima}</div>
            <div class="tooltip-feriados">
                <div class="feriados-count">${feriadosCount} feriados/año</div>
            </div>
        `;
    }

    tooltip.innerHTML = mensaje;
    document.body.appendChild(tooltip);
}

function ocultarTooltip() {
    const tooltip = document.getElementById('guardia-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

function calcularProximaGuardia(guardiaName, fechaActual) {
    // Buscar todas las celdas de esta guardia
    const celdasGuardia = [];
    const todasLasCeldas = document.querySelectorAll('.dia-celda');

    todasLasCeldas.forEach(celda => {
        const guardiaData = celda.getAttribute('data-guardia');
        const fechaData = celda.getAttribute('data-fecha');

        if (guardiaData === guardiaName && fechaData) {
            const fecha = new Date(fechaData);
            celdasGuardia.push(fecha);
        }
    });

    // Ordenar fechas
    celdasGuardia.sort((a, b) => a - b);

    // Verificar si está de guardia hoy
    const hoyStr = fechaActual.toISOString().split('T')[0];

    let guardiaActualInicio = null;
    let guardiaActualFin = null;
    let estaDeGuardia = false;

    // Buscar el bloque de guardia actual
    for (let i = 0; i < celdasGuardia.length; i++) {
        const fechaStr = celdasGuardia[i].toISOString().split('T')[0];

        if (fechaStr === hoyStr) {
            estaDeGuardia = true;

            // Buscar inicio del bloque
            guardiaActualInicio = celdasGuardia[i];
            for (let j = i - 1; j >= 0; j--) {
                const diff = (celdasGuardia[j + 1] - celdasGuardia[j]) / (1000 * 60 * 60 * 24);
                if (diff <= 1) {
                    guardiaActualInicio = celdasGuardia[j];
                } else {
                    break;
                }
            }

            // Buscar fin del bloque
            guardiaActualFin = celdasGuardia[i];
            for (let j = i + 1; j < celdasGuardia.length; j++) {
                const diff = (celdasGuardia[j] - celdasGuardia[j - 1]) / (1000 * 60 * 60 * 24);
                if (diff <= 1) {
                    guardiaActualFin = celdasGuardia[j];
                } else {
                    break;
                }
            }

            break;
        }
    }

    if (estaDeGuardia) {
        const diasRestantes = Math.ceil((guardiaActualFin - fechaActual) / (1000 * 60 * 60 * 24)) + 1;

        return {
            estaDeGuardia: true,
            diasRestantes: diasRestantes,
            fechaInicio: formatearFecha(guardiaActualInicio),
            fechaFin: formatearFecha(guardiaActualFin)
        };
    } else {
        // Encontrar la próxima fecha
        const proximaFecha = celdasGuardia.find(fecha => fecha > fechaActual);

        if (proximaFecha) {
            const diasHasta = Math.ceil((proximaFecha - fechaActual) / (1000 * 60 * 60 * 24));

            return {
                estaDeGuardia: false,
                diasHastaProxima: diasHasta,
                fechaProxima: formatearFecha(proximaFecha)
            };
        }
    }

    return {
        estaDeGuardia: false,
        diasHastaProxima: 0,
        fechaProxima: 'No disponible'
    };
}

function formatearFecha(fecha) {
    const dia = fecha.getDate();
    const mes = fecha.getMonth() + 1;
    const anio = fecha.getFullYear();
    return `${dia.toString().padStart(2, '0')}/${mes.toString().padStart(2, '0')}/${anio}`;
}
