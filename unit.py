from enum import Enum
from typing import Dict

class UnitType(Enum):
    SOLDIER = 1
    ARCHER = 2

    def get_info(self) -> Dict:
        if self == UnitType.SOLDIER:
            return {
                "name": "Soldier",
                "description": "Strong melee unit",
                "max_hp": 100,
                "attack": 50,
                "move_range": 3,
                "attack_range": 1
            }
        else:
            return {
                "name": "Archer",
                "description": "Ranged attack unit",
                "max_hp": 75,
                "attack": 40,
                "move_range": 2,
                "attack_range": 3
            }

class Unit:
    def __init__(self, unit_type: UnitType, x: int, y: int, player: int):
        self.unit_type = unit_type
        self.x = x
        self.y = y
        self.player = player 
        self.moved = False
        self.attacked = False
        
        info = unit_type.get_info()
        self.max_hp = info["max_hp"]
        self.attack = info["attack"]
        self.move_range = info["move_range"]
        self.attack_range = info["attack_range"]
        self.hp = self.max_hp
