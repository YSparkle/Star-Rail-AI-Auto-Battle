from typing import Dict, Type
from src.strategies import Strategy, MaterialFarmStrategy, AbyssStrategy


MODE_STRATEGY_MAP: Dict[str, Type[Strategy]] = {
    "material_farm": MaterialFarmStrategy,
    "abyss": AbyssStrategy,
}
