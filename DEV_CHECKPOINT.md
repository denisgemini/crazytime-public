# CrazyTime v2 Dashboard - Checkpoint de Desarrollo
**Fecha:** Lunes 26 Enero 2026
**Estado:** Estable / Funcional / Limpio

## 1. Estado Actual del Sistema
*   **Arquitectura:** FastAPI + Vanilla JS Modular.
*   **Modelo de Datos:** Implementado el **"Nuevo Modelo de Latidos"**.
    *   `timestamp` guarda el inicio real (`started_at`).
    *   `settled_at` guarda el fin del tiro.
    *   `latido` (Inicio actual - Fin anterior) grabado en BD.
    *   Filtro de duplicados de ±10s activo y funcional.
*   **Notificaciones:** Bot de Telegram configurado y probado (envía mensaje de inicio).

## 2. Tareas en Progreso (Prueba de Hoy)
*   **Resumen Diario Pro:** Creación de un script que genere el reporte diario desde este directorio.
    *   **Lógica de Apuesta:** Conteo de HITS/MISSES (Espera 11 tiros / Ventana 30 tiros) para umbrales VIP.
    *   **Salud Visual:** Gráfico de latidos (0-4s, 5s, 6-11s, >11s, Negativos).
    *   **Exportación:** Generación de CSV con tiros del día para reconstrucción de BD.
*   **Sincronización:** Telegram como puente para envío y descarga manual de datos para prueba.

## 3. Comandos de Interés
```bash
# Ver latidos actuales
python3 scripts/analyze_latidos.py
# Probar notificador
./venv/bin/python3 scripts/test_telegram.py
```

## 3. Mapa de Archivos Clave
Si necesitas editar algo, ve directo aquí:

*   **API / Backend:** `dashboard/app.py`
*   **Configuración Patrones:** `config/patterns.py` (Importado dinámicamente).
*   **Estilos:** `dashboard/static/css/styles.css` y `ticker_styles.css`.
*   **Grid Distancias:** `dashboard/static/js/render/tabs.js`
*   **Gráfica Barras:** `dashboard/static/js/render/charts.js`
*   **Ticker (Cinta):** `dashboard/static/js/render/ticker.js`
*   **Tarjetas/Ring:** `dashboard/static/js/render/cards.js`

## 4. Próximos Pasos
*   El sistema está listo para recibir mejoras visuales finales o nuevas funcionalidades.
*   **Pendiente:** (Espacio para nuevas tareas).

## 5. Comandos de Inicio
```bash
# Iniciar servidor
python dashboard/app.py
# O con uvicorn
uvicorn dashboard.app:app --host 0.0.0.0 --port 8000
```
