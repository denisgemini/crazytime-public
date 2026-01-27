# CrazyTime v2.5 - Checkpoint de Desarrollo
**Fecha:** Martes 27 Enero 2026
**Estado:** **v2.5 ESTABLE** / Optimizado / Integridad Cronológica Total

## 1. Estado Actual del Sistema
*   **Integridad:** Implementado el sistema de **Pseudo IDs** y **Vistas SQL**. Los tiros se procesan en orden cronológico real sin importar el desorden de la API.
*   **Alertas y Tracking:** Sincronizados al 100% con la vista `tiros_ordenados`.
*   **Dashboard:** UI actualizada con **Anillo Neón Azul Celeste** para umbrales. Refresco optimizado a 30 segundos para GCP Free Tier.
*   **Base de Datos:** SQLite optimizada con clase centralizada y métodos oficiales para todo el sistema.

## 2. Gran Tarea Pendiente: "Dashboard de Bolsillo"
*   **Script:** `scripts/generar_resumen.py` (Uso de **Pillow**, sin Pandas).
*   **Objetivo:** Infografía neón profesional enviada vía Telegram cada noche a las **22:05**.
*   **Corte Diario:** Rango de 22:00 a 22:00 (Hora Perú).

## 3. Comandos Útiles
```bash
# Ver duración real de tiros
python3 scripts/analyze_durations.py
# Iniciar sistema completo
python3 main.py & python3 dashboard/app.py &
# Subir cambios finales
git add . && git commit -m "End of Session: v2.5 Finalized" && git push origin master
```

## 4. Mapa de Archivos Actualizado
*   **Core Logic:** `core/database.py` (Contiene la Vista y Pseudo IDs).
*   **Dashboard:** `dashboard/app.py` (FastAPI optimizado).
*   **Analytics:** `analytics/pattern_tracker.py` (Cronológico).
*   **Alertas:** `alerting/alert_manager.py` (Cronológico).

---
*Sesión cerrada con éxito. El sistema está listo para el siguiente nivel visual.*