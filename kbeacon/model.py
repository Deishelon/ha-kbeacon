from dataclasses import dataclass


@dataclass(frozen=True)
class KInfo:
    m_voltage: int
    temperature: float
    humidity: float
