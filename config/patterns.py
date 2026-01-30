"""
config/patterns.py - Configuración de patrones del sistema (Arquitectura Desacoplada v2.7).
"""

from dataclasses import dataclass, field
from typing import Literal, List, Tuple

@dataclass
class Pattern:
    id: str
    name: str
    type: Literal["simple", "sequence"]
    value: str | list[str]
    # Nuevos campos desacoplados
    warning_thresholds: List[int] = field(default_factory=list)
    betting_windows: List[Tuple[int, int]] = field(default_factory=list)
    
    # Campo legacy para compatibilidad temporal (se eliminará)
    thresholds: List[int] = field(default_factory=list) 
    
    alert_level: Literal["vip", "tracking"] = "tracking"
    description: str = ""

# Definición Explícita de Patrones VIP
PACHINKO = Pattern(
    id="pachinko", name="Pachinko", type="simple", value="Pachinko",
    warning_thresholds=[50, 110],          # Solo avisos
    betting_windows=[(61, 90), (121, 150)], # Solo zonas de apuesta
    alert_level="vip",
    description="Bonus game"
)

CRAZYTIME = Pattern(
    id="crazytime", name="Crazy Time", type="simple", value="CrazyTime",
    warning_thresholds=[190, 250],
    betting_windows=[(201, 230), (261, 290)],
    alert_level="vip",
    description="Bonus principal"
)

# Patrones de Tracking (Sin alertas, pero con ventanas de estudio si se requiere)
NUMERO_10 = Pattern(
    id="numero_10", name="Número 10", type="simple", value="10",
    warning_thresholds=[], 
    betting_windows=[(61, 90)], # Ejemplo de ventana de estudio
    alert_level="tracking",
    description="Número regular"
)

SECUENCIA_2_5 = Pattern(
    id="seq_2_5", name="Secuencia 2→5", type="sequence", value=["2", "5"],
    warning_thresholds=[],
    betting_windows=[(61, 90)],
    alert_level="tracking",
    description="Secuencia"
)

SECUENCIA_5_2 = Pattern(
    id="seq_5_2", name="Secuencia 5→2", type="sequence", value=["5", "2"],
    warning_thresholds=[],
    betting_windows=[(61, 90)],
    alert_level="tracking",
    description="Secuencia"
)

VIP_PATTERNS = [PACHINKO, CRAZYTIME]
TRACKING_PATTERNS = [NUMERO_10, SECUENCIA_2_5, SECUENCIA_5_2]
ALL_PATTERNS = VIP_PATTERNS + TRACKING_PATTERNS
PATTERNS_BY_ID = {p.id: p for p in ALL_PATTERNS}

PATTERN_IMAGES = {
    "pachinko": "pachinko.png",
    "crazytime": "crazytime.png",
    "numero_10": "10.png",
    "seq_2_5": "2-5.png",
    "seq_5_2": "5-2.png",
}

def get_pattern_image(pattern_id: str) -> str | None:
    return PATTERN_IMAGES.get(pattern_id)

# Helper obsoleto pero mantenido por si acaso (ya no se usa en lógica nueva)
WINDOW_CONFIG = {"offset_after_threshold": 10, "window_size": 30}
def get_window_range(threshold: int) -> tuple[int, int]:
    start = threshold + WINDOW_CONFIG["offset_after_threshold"] + 1
    end = start + WINDOW_CONFIG["window_size"] - 1
    return (start, end)