# INSTRUCCIONES CRÍTICAS PARA EL AGENTE (GEMINI) - CrazyTime v2.6

Este archivo contiene las **Reglas de Oro** y **Prohibiciones** que el agente debe seguir sin excepción. El incumplimiento de estas reglas arruina la integridad del sistema.

## 🚫 PROHIBICIONES ABSOLUTAS (LO QUE NO DEBES HACER)
1. **JAMÁS** utilices la vista `tiros_ordenados` o el campo `pseudo_id` para lógica de tracking o cálculos. Usar siempre `id` real de la tabla `tiros`.
2. **JAMÁS** inicies por tu cuenta los procesos: `main.py`, `dashboard/app.py` o cualquier bot de Telegram.
3. **JAMÁS** mezcles lógica de "Umbrales" con "Análisis de Resultados". Los umbrales son solo alarmas de aviso en tiempo real.
4. **JAMÁS** cuentes como "Fallo" un tiro que salió ANTES de la ventana de apuesta. Si `distancia < inicio_ventana`, el tiro se ignora (no es ni acierto ni fallo).
5. **JAMÁS** guardes el estado del sistema en archivos JSON volátiles. Toda la persistencia de progreso debe residir en la tabla `system_state` de SQLite.
6. **JAMÁS** realices modificaciones de archivos sin aprobación explícita.

## ✅ VERDADES INMUTABLES (LO QUE DEBES SABER)
1. **Fuente de Verdad:** La tabla `tiros` (ID real) y la tabla `system_state` (Progreso y Distancias). **PROHIBIDO EL USO DE JSON EN DISCO.**
2. **Lógica de Ventana:**
   - **Umbral:** Señal de aviso (ej: 50).
   - **Ventana:** Zona de apuesta [Umbral+11, Umbral+40] (ej: [61-90]).
   - **Acierto (Win):** Tiro dentro de la ventana ([61-90]).
   - **Fallo (Loss):** Tiro DESPUÉS de la ventana (>90).
   - **Ignorado:** Tiro ANTES de la ventana (<61).
3. **Reporte Diario:** Debe ser festivo, estratégico y centrado exclusivamente en la rentabilidad de las ventanas (23:00 - 23:00).
4. **Intervalo:** Recolección cada 5 minutos (300s).

## 🎯 OBJETIVO ACTUAL
Monitoreo estratégico 100% SQLite con latencia cero en alertas.
