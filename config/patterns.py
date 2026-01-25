"""
config/patterns.py - Configuración de patrones del sistema.
"""

from dataclasses import dataclass
from typing import Literal

@dataclass
class Pattern:
    id: str
    name: str
    type: Literal["simple", "sequence"]
    value: str | list[str]
    thresholds: list[int]
    alert_level: Literal["vip", "tracking"]
    description: str

PACHINKO = Pattern(
    id="pachinko", name="Pachinko", type="simple", value="Pachinko",
    thresholds=[50, 110], alert_level="vip",
    description="Bonus game con ventanas en 61-90 y 121-150"
)

CRAZYTIME = Pattern(
    id="crazytime", name="Crazy Time", type="simple", value="CrazyTime",
    thresholds=[190, 250], alert_level="vip",
    description="Bonus principal con ventanas en 201-230 y 261-290"
)

NUMERO_10 = Pattern(
    id="numero_10", name="Número 10", type="simple", value="10",
    thresholds=[], alert_level="tracking",
    description="Número regular, solo tracking histórico"
)

SECUENCIA_2_5 = Pattern(
    id="seq_2_5", name="Secuencia 2→5", type="sequence", value=["2", "5"],
    thresholds=[], alert_level="tracking",
    description="Secuencia de dos números consecutivos"
)

SECUENCIA_5_2 = Pattern(
    id="seq_5_2", name="Secuencia 5→2", type="sequence", value=["5", "2"],
    thresholds=[], alert_level="tracking",
    description="Secuencia de dos números consecutivos"
)

VIP_PATTERNS = [PACHINKO, CRAZYTIME]
TRACKING_PATTERNS = [NUMERO_10, SECUENCIA_2_5, SECUENCIA_5_2]
ALL_PATTERNS = VIP_PATTERNS + TRACKING_PATTERNS
PATTERNS_BY_ID = {p.id: p for p in ALL_PATTERNS}

WINDOW_CONFIG = {"offset_after_threshold": 10, "window_size": 30}

def get_window_range(threshold: int) -> tuple[int, int]:
    start = threshold + WINDOW_CONFIG["offset_after_threshold"] + 1
    end = start + WINDOW_CONFIG["window_size"] - 1
    return (start, end)

PATTERN_IMAGES = {
    "pachinko": "pachinko.png",
    "crazytime": "crazytime.png",
    "numero_10": "10.png",
    "seq_2_5": "2-5.png",
    "seq_5_2": "5-2.png",
}

def get_pattern_image(pattern_id: str) -> str | None:
    return PATTERN_IMAGES.get(pattern_id)
