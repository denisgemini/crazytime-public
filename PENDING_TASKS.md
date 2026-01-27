# 📋 Tareas Pendientes de Optimización e Integridad (v2.5+)

Este archivo detalla las mejoras necesarias para corregir los "cables sueltos" y asegurar que el sistema sea 100% robusto en GCP Free Tier.

## 🛠️ Fase 1: Alineación de Lógica y Tiempos
- [ ] **Sincronizar PatternTracker con Pseudo IDs:** Modificar `analytics/pattern_tracker.py` para que procese los tiros basándose en la cronología real (`timestamp`/`pseudo_id`) y no por el `id` de inserción.
- [ ] **Sincronizar Alertas con Pseudo IDs:** Asegurar que `alerting/alert_manager.py` evalúe las distancias usando la misma vista cronológica que el Dashboard.
- [ ] **Corregir Naming en Collector:** Renombrar internamente el flujo de datos para que sea claro que `timestamp` = `started_at` y evitar confusiones en futuros desarrollos.

## 🚀 Fase 2: Rendimiento y Dashboard (GCP Free Tier)
- [ ] **Centralizar Base de Datos en App:** Refactorizar `dashboard/app.py` para que utilice la clase `core.database.Database` en lugar de abrir conexiones manuales (optimización WAL mode).
- [ ] **Caché de Configuración:** Evitar importaciones dinámicas repetitivas en las rutas de FastAPI para reducir el uso de CPU.
- [ ] **Eliminar redundancias en Dashboard:** Asegurar que todos los componentes visuales (Cards, Ticker, Stats) consuman exclusivamente de la vista `tiros_ordenados`.

## 🧹 Fase 3: Limpieza y Mantenimiento
- [ ] **Limpiar Root:** Eliminar archivos de error/versión (e.g., `=0.109.0`, `=1.0.0`, etc.).
- [ ] **Gestionar Backups:** Decidir si mantener `dashboard_backup/` o eliminarlo para reducir peso del repo.
- [ ] **Actualizar DEV_CHECKPOINT:** Reflejar estos cambios en el estado de integridad del sistema.

## 📊 Fase 4: Reportes y Visualización
- [ ] **Script `generar_resumen.py`:** Implementar el reporte diario de Telegram usando la nueva lógica de Pseudo IDs.
- [ ] **Integrar Alertas de Integridad:** Añadir los logs de bloqueos y anomalías al reporte de Telegram.

---
*Nota: No marcar como completado hasta haber verificado que no rompe el flujo 24/7.*
