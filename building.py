import pygame
from enum import Enum
from typing import Dict

class BuildingType(Enum):
    TOWER = 1
    BARRACKS = 2

class Building:
    def __init__(self, building_type: BuildingType, x: int, y: int, player: int):
        self.building_type = building_type
        self.x = x
        self.y = y
        self.player = player

    def get_info(self) -> Dict:
        if self.building_type == BuildingType.TOWER:
            return {
                "name": "Tower",
                "description": "Defensive structure",
            }
        elif self.building_type == BuildingType.BARRACKS:
            return {
                "name": "Barracks",
                "description": "Training unit structure",
            }

    def draw(self, surface, tile_size):
        color = (0, 0, 255)  # Color for buildings (e.g., blue)
        pygame.draw.rect(surface, color, 
                         (self.x * tile_size, self.y * tile_size, tile_size, tile_size))