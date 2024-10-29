from enum import Enum
from typing import Dict
from unit import Unit, UnitType
import pygame

# กำหนดประเภทของอาคาร
class BuildingType(Enum):
    TOWER = 1  # อาคาร Tower
    BARRACKS = 2  # อาคาร Barracks

# คลาสสำหรับอาคาร
class Building:
    def __init__(self, building_type: BuildingType, x: int, y: int, player: int):
        # กำหนดค่าพื้นฐานของอาคาร
        self.building_type = building_type  # ประเภทของอาคาร
        self.x = x  # ตำแหน่ง x ของอาคาร
        self.y = y  # ตำแหน่ง y ของอาคาร
        self.player = player  # ผู้เล่นที่เป็นเจ้าของอาคาร

    def get_info(self) -> Dict:
        # คืนค่าข้อมูลเกี่ยวกับอาคาร
        if self.building_type == BuildingType.TOWER:
            return {
                "name": "Tower",  # ชื่อของอาคาร
                "description": "Defensive structure",  # คำอธิบาย
            }
        elif self.building_type == BuildingType.BARRACKS:
            return {
                "name": "Barracks",  # ชื่อของอาคาร
                "description": "Training unit structure",  # คำอธิบาย
            }

    def draw(self, surface, tile_size):
        # วาดอาคารลงบนหน้าจอ
        color = (0, 0, 255)  # สีของอาคาร (เช่น สีน้ำเงิน)
        pygame.draw.rect(surface, color, 
                         (self.x * tile_size, self.y * tile_size, tile_size, tile_size))  # วาดสี่เหลี่ยมตามตำแหน่งและขนาด

    def produce_unit(self, unit_type: UnitType):
        # สร้างยูนิตใหม่จากอาคาร
        new_unit = Unit(unit_type, self.x, self.y, self.player)  # สร้างยูนิตใหม่ที่ตำแหน่งและผู้เล่นเดียวกับอาคาร
        return new_unit  # คืนค่ายูนิตใหม่
