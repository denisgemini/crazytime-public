# Servicio de Análisis CrazyTime v2.5

## Descripción General del Proyecto

**CrazyTime Analytics** es un sistema de monitoreo persistente y análisis estadístico para el juego "Crazy Time". Rastrea resultados específicos del juego ("patrones"), calcula la "distancia" (número de giros) entre apariciones y predice ventanas de apuesta óptimas basadas en datos históricos.

El sistema está diseñado para funcionar 24/7 (optimizado para el nivel gratuito de GCP) y proporciona alertas en tiempo real a través de Telegram y un panel de control web visual.

### Conceptos Clave

*   **Patrón (Pattern):** Un resultado objetivo (ej. "Pachinko", "Crazy Time") o una secuencia (ej. "2" seguido de "5").
*   **Distancia (Distance):** El número de giros transcurridos desde la última aparición de un patrón.
*   **Umbral (Threshold):** Una distancia predefinida que activa una señal de "Aviso".
*   **Ventana (Window):** Una zona de apuesta específica que se abre poco después de alcanzar un umbral.
    *   **Lógica:** La ventana comienza en el `Umbral + 11` y termina en el `Umbral + 40`.
*   **Acierto/Fallo (Hit/Loss):**
    *   **Acierto:** El patrón ocurre *dentro* de la Ventana.
    *   **Fallo:** El patrón ocurre *después* de que la Ventana se cierra (Distancia > Umbral + 40).

## Arquitectura

El sistema consta de dos componentes principales independientes que comparten una base de datos:

1.  **Servicio Recolector (`main.py`):**
    *   Ejecuta un bucle infinito (cada 3 minutos).
    *   Obtiene los últimos datos de giros de la API del proveedor del juego.
    *   Actualiza la base de datos SQLite (`data/db.sqlite3`).
    *   Analiza patrones y actualiza el estado (`data/.tracker_state.json`).
    *   Envía notificaciones de Telegram a través del módulo `alerting/`.

2.  **API del Dashboard (`dashboard/app.py`):**
    *   Una aplicación **FastAPI**.
    *   Sirve la interfaz web (`templates/index.html` + `static/`).
    *   Proporciona endpoints REST (`/api/status`, `/api/patterns`, etc.) para el frontend.
    *   Lee de la base de datos SQLite compartida y de los archivos JSON de estado.

## Stack Tecnológico

*   **Lenguaje:** Python 3.x
*   **Framework Web:** FastAPI (con Uvicorn)
*   **Base de Datos:** SQLite
*   **Notificaciones:** python-telegram-bot
*   **Dependencias:** `requests`, `python-dotenv`, `openpyxl`, `Pillow`

## Estructura del Proyecto

*   `main.py`: Punto de entrada para el servicio de recolección de datos en segundo plano.
*   `dashboard/`: Contiene la app FastAPI (`app.py`), plantillas y activos estáticos.
*   `core/`: Lógica central para la conexión a la base de datos (`database.py`) y cliente API.
*   `config/`: Archivos de configuración, incluyendo `patterns.py` (definiciones de patrones y umbrales).
*   `alerting/`: Lógica para el envío de notificaciones de Telegram.
*   `analytics/`: Módulos de análisis estadístico (`window_analyzer.py`).
*   `scripts/`: Scripts de utilidad para mantenimiento, instalación y pruebas.
*   `data/`: Almacena la base de datos SQLite, logs y archivos JSON de estado.

## Configuración e Instalación

1.  **Configuración del Entorno:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Configuración:**
    *   Asegúrate de que exista el archivo `.env` con las claves de API necesarias (Token de Telegram, etc.).
    *   Revisa `config/patterns.py` para ajustar los umbrales o patrones.

## Ejecución del Sistema

### 1. Servicio en Segundo Plano (Recolector)
Ejecuta esto para comenzar a recolectar datos y enviar alertas:
```bash
python main.py
```

### 2. Panel de Control Web (Dashboard)
Ejecuta el servidor FastAPI para ver el dashboard:
```bash
python dashboard/app.py
# Acceso en http://localhost:8000
```

### 3. Despliegue en Producción (Systemd)
El proyecto incluye un script para instalarse como servicio de systemd:
```bash
sudo ./scripts/install_service.sh
```
*   **Iniciar:** `sudo systemctl start crazytime`
*   **Logs:** `tail -f data/logs/service.log`

## Guías de Desarrollo

*   **Base de Datos:** El sistema utiliza una base de datos SQLite compartida. Asegúrate de que los permisos del directorio `data/` permitan tanto al servicio como al dashboard leer/escribir.
*   **Archivos de Estado:** Los archivos JSON en `data/` se utilizan para una persistencia de estado ligera (ej. ID del último giro procesado) para evitar consultas innecesarias a la DB.
*   **Logs:** Los registros se escriben en `data/logs/`. Revísalos para depurar problemas del recolector.
*   **Pruebas:** Los scripts de utilidad en `scripts/` (ej. `test_telegram.py`) pueden usarse para verificar componentes individuales.