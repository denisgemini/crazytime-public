# 📋 Tareas Pendientes de Optimización e Integridad (v2.5+)

Este archivo detalla las mejoras necesarias para asegurar que el sistema sea 100% robusto en GCP Free Tier.

## 🛠️ Fase 1: Alineación de Lógica y Tiempos
- [x] **Sincronizar PatternTracker con Pseudo IDs:** Modificado para procesar tiros basándose en la cronología real (`tiros_ordenados`).
- [x] **Sincronizar Alertas con Pseudo IDs:** `AlertManager` ahora evalúa distancias usando `pseudo_id`.
- [ ] **Corregir Naming en Collector:** (Postpuesto por retrocompatibilidad) Renombrar internamente el flujo de datos para que sea claro que `timestamp` = `started_at`.

## 🚀 Fase 2: Rendimiento y Dashboard (GCP Free Tier)
- [x] **Centralizar Base de Datos en App:** `dashboard/app.py` utiliza ahora la clase `core.database.Database` oficial (WAL mode).
- [x] **Caché de Configuración:** Implementado caché de patrones para evitar importaciones dinámicas y reducir CPU.
- [x] **Eliminar redundancias en Dashboard:** Todos los componentes consumen de la vista `tiros_ordenados`.
- [x] **Optimización de Refresh:** Subido intervalo de actualización de 3s a 30s (ahorro de red y CPU).

## 🧹 Fase 3: Limpieza y Mantenimiento
- [x] **Limpiar Root:** Eliminados archivos basura (`=0.109.0`, etc.).
- [x] **Gestionar Backups:** Carpeta `dashboard_backup/` eliminada.
- [x] **Análisis de Duraciones:** Script `scripts/analyze_durations.py` creado y ejecutado (Promedio ~45s/tiro).

## 📊 Fase 4: Reportes y Visualización (PRÓXIMA SESIÓN)
- [ ] **Dashboard de Bolsillo (Pillow):** Crear script `generar_resumen.py` que genere una infografía neón profesional.
  - [ ] **Diseño Neón:** Fondo oscuro, tarjetas con resplandor, fuentes Orbitron/Rajdhani.
  - [ ] **Lógica 11/30:** Simulación de hits/misses basada en cronología real.
  - [ ] **Envío Telegram:** Mensaje con imagen adjunta y CSV de backup a las 22:05 cada día.
- [ ] **Integrar Alertas de Integridad:** Añadir logs de anomalías al reporte de Telegram.

---
*Nota: Sistema estable v2.5 corriendo en GCP.*