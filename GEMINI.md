# INSTRUCCIONES CRÍTICAS PARA EL AGENTE (GEMINI) - CrazyTime v3.0 (Pure SQLite)

Este archivo contiene las **Reglas de Oro** y **Prohibiciones** que el agente debe seguir sin excepción. El incumplimiento de estas reglas arruina la integridad del sistema.

## 🚫 PROHIBICIONES ABSOLUTAS (LO QUE NO DEBES HACER)
1. **JAMÁS** utilices archivos JSON para persistir el estado. Toda la información (progreso, alertas enviadas, distancias) debe residir en la tabla `system_state` de SQLite.
2. **JAMÁS** utilices la vista `tiros_ordenados` para lógica de tracking. Usar siempre `id` real de la tabla `tiros`.
3. **JAMÁS** inicies por tu cuenta los procesos: `main.py`, `dashboard/app.py` o cualquier bot de Telegram.
4. **JAMÁS** mezcles lógica de "Aviso de Umbral" con "Reporte de Hit". Son eventos independientes que deben evaluarse por separado.
5. **JAMÁS** realices modificaciones de archivos sin aprobación explícita.

## ✅ VERDADES INMUTABLES (LO QUE DEBES SABER)
1. **Fuente de Verdad Única:** La tabla `tiros` (datos históricos) y la tabla `system_state` (estado de módulos). **El sistema es 100% independiente del disco.**
2. **Lógica de Ventana Estratégica:**
   - **Espera (Current Wait):** Distancia desde el último Hit hasta el momento actual.
   - **Target (Threshold):** Marca de aviso para entrar al casino (ej: 50).
   - **Ventana de Apuesta:** Rango configurado para disparar (ej: [61-90]).
3. **Memoria de Impacto:** En caso de HIT, se debe preservar la `prev_distance` para asegurar que las alertas de umbral cruzadas en el mismo ciclo no se pierdan.
4. **Intervalo de Recolección:** 5 minutos (300s) para estabilidad, con Escalera de Recuperación infinita (soporta hasta 72h de caída).

## 🎯 OBJETIVO ACTUAL
Estabilizar el sistema de alertas SQLite para garantizar que ningún umbral se pierda, incluso durante apariciones simultáneas en el mismo lote.