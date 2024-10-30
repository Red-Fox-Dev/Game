from enum import Enum
from typing import Dict
import pygame
from unit import Unit, UnitType

# กำหนดประเภทของอาคาร
class BuildingType(Enum):
    TOWER = 1  # อาคาร Tower
    BARRACKS = 2  # อาคาร Barracks

# คลาสสำหรับอาคาร
class Building:
    def __init__(self, building_type: BuildingType, x: int, y: int, player: int):
        self.building_type = building_type
        self.x = x
        self.y = y
        self.player = player
        self.rect = pygame.Rect(x * 50, y * 50, 50, 50)  # กำหนด rect สำหรับการตรวจสอบการชน

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

    def draw(self, surface):
        color = (0, 0, 255)  # สีของอาคาร (เช่น สีน้ำเงิน)
        pygame.draw.rect(surface, color, self.rect)  # วาดสี่เหลี่ยมตามตำแหน่งและขนาด

    def produce_unit(self, unit_type: UnitType):
        new_unit = Unit(unit_type, self.x, self.y, self.player)  # สร้างยูนิตใหม่ที่ตำแหน่งและผู้เล่นเดียวกับอาคาร
        return new_unit  # คืนค่ายูนิตใหม่

class Tower(Building):
    def __init__(self, x: int, y: int, player: int):
        super().__init__(BuildingType.TOWER, x, y, player)
