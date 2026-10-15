from dataclasses import dataclass


@dataclass
class AnaliseInput:
    username: str
    password: str
    analise: str
