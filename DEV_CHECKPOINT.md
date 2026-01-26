# CrazyTime v2 Dashboard - Checkpoint de Desarrollo
**Fecha:** Lunes 26 Enero 2026
**Estado:** Estable / Funcional / Limpio

## 1. Estado Actual del Sistema
El dashboard ha sido reconstruido y limpiado de código duplicado. Actualmente funciona bajo una arquitectura **FastAPI + Vanilla JS Modular**.

### Arquitectura
*   **Backend:** `dashboard/app.py` (FastAPI) corriendo en puerto **8000**.
*   **Frontend:** `dashboard/templates/index.html` (SPA simple).
*   **Lógica JS:** Modular en `dashboard/static/js/` (entrada vía `main.js`).
*   **Base de Datos:** SQLite en modo **WAL** (`data/db.sqlite3`).
*   **Datos en vivo:** Se leen los últimos 1000 tiros para estadísticas.

## 2. Cambios Recientes (La "Gran Limpieza")
*   🗑️ **Archivos Eliminados:** `app.js`, `renderer.js`, `heatmap.js` (causaban duplicidad).
*   🔧 **API Fix:** Se corrigió la lectura de `config/patterns.py` que devolvía texto crudo ("Id=...") en lugar de objetos JSON.
*   🎨 **UI Refactor:**
    *   **Ticker:** Estilo "Billetes de Neón" (1, 2, 5, 10) y Badges verticales para Bonos. Muestra los últimos 40 únicos.
    *   **Distance Grid:** Movido arriba. Celdas con bordes neón y colores por temperatura (Frío -> Caliente -> Extreme). Invertido para mostrar lo más reciente primero.
    *   **Heatmap:** Eliminado por inutilidad.
    *   **Distribution Chart:** Reemplazado por un histograma de los últimos 1000 resultados (Barras de neón).
    *   **Ring:** Ahora solo muestra el progreso al umbral 190 de Crazy Time.

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
