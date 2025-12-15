# Sistema de Guardias

Aplicación web backend desarrollada en Flask para gestionar el cronograma de guardias rotativas del personal.

## ¿Qué es?
Sistema que automatiza la organización y seguimiento de turnos de guardia, permitiendo configurar participantes, duración y fechas de referencia.

## ¿Cómo funciona?
- **Framework**: Flask 3.0.0 como servidor web
- **Servidor WSGI**: Gunicorn 21.2.0 para producción
- **Configuración**: Variables de entorno para personalizar guardias y duración
- **Arquitectura**: Aplicación Flask tradicional con templates y archivos estáticos

La aplicación genera automáticamente cronogramas de guardias basados en una lista de participantes y una duración configurable. Se ejecuta en el puerto interno 5000 del contenedor y es accedida a través de Nginx en la ruta `/guardias/`.