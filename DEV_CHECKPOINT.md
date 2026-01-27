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

## 2. Tareas en Progreso (Próxima Sesión)
*   **Script: `scripts/generar_resumen.py`**
    *   **Lógica "Espera 11 / Apuesta 30"**: Algoritmo para contar HITS/MISSES basados en umbrales VIP.
    *   **Gráfico de Salud**: Generación de `salud_latidos.png` con `matplotlib` (Rangos: <0, 0-4s, 5s, 6-11s, >11s).
    *   **Exportación de Datos**: Generación de `tiros_hoy.csv` con historial completo (ID, Resultado, Inicio, Fin, Latido).
    *   **Envío Telegram**: Mensaje (Estadísticas) + Imagen (Salud) + Documento (CSV).
*   **Script: `scripts/descargar_datos.py`**
    *   Uso de `python-telegram-bot` para descargar el último CSV del bot.
    *   Inyección de datos del CSV a la base de datos local para sincronización manual de prueba.

## 3. Comandos de Interés
```bash
# Ver latidos actuales
python3 scripts/analyze_latidos.py
# Probar notificador
./venv/bin/python3 scripts/test_telegram.py
# Subir cambios (Git)
git add . && git commit -m "Desc..." && git push origin master
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
