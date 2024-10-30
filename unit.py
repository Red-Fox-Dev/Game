from enum import Enum
from typing import Dict

# กำหนดประเภทของยูนิต
class UnitType(Enum):
    SOLDIER = 1  # ยูนิตประเภท Soldier
    ARCHER = 2   # ยูนิตประเภท Archer

    def get_info(self) -> Dict:
        # คืนค่าข้อมูลเกี่ยวกับยูนิตแต่ละประเภท
        if self == UnitType.SOLDIER:
            return {
                "name": "Soldier",  # ชื่อของยูนิต
                "description": "Strong melee unit",  # คำอธิบาย
                "max_hp": 100,  # HP สูงสุด
                "attack": 50,  # พลังโจมตี
                "move_range": 3,  # ระยะทางที่สามารถเคลื่อนที่ได้
                "attack_range": 1  # ระยะทางโจมตี
            }
        else:  # UnitType.ARCHER
            return {
                "name": "Archer",  # ชื่อของยูนิต
                "description": "Ranged attack unit",  # คำอธิบาย
                "max_hp": 75,  # HP สูงสุด
                "attack": 40,  # พลังโจมตี
                "move_range": 2,  # ระยะทางที่สามารถเคลื่อนที่ได้
                "attack_range": 3  # ระยะทางโจมตี
            }

    @staticmethod
    def get_cost(unit_type):
        """ กำหนดค่าใช้จ่ายสำหรับยูนิตประเภทต่าง ๆ """
        costs = {
            UnitType.SOLDIER: 50,
            UnitType.ARCHER: 100,
        }
        return costs.get(unit_type, 0)

# คลาสสำหรับยูนิต
class Unit:
    def __init__(self, unit_type: UnitType, x: int, y: int, player: int):
        # กำหนดค่าพื้นฐานของยูนิต
        self.unit_type = unit_type  # ประเภทของยูนิต
        self.x = x  # ตำแหน่ง x ของยูนิต
        self.y = y  # ตำแหน่ง y ของยูนิต
        self.player = player  # ผู้เล่นที่เป็นเจ้าของยูนิต
        self.moved = False  # สถานะการเคลื่อนที่
        self.attacked = False  # สถานะการโจมตี
        
        info = unit_type.get_info()  # เรียกข้อมูลของยูนิต
        self.max_hp = info["max_hp"]  # HP สูงสุด
        self.attack = info["attack"]  # พลังโจมตี
        self.move_range = info["move_range"]  # ระยะทางที่สามารถเคลื่อนที่ได้
        self.attack_range = info["attack_range"]  # ระยะทางโจมตี
        self.hp = self.max_hp  # กำหนด HP เริ่มต้นให้เท่ากับ HP สูงสุด

    def __str__(self):
        return f"{self.unit_type.get_info()['name']} (HP: {self.hp}/{self.max_hp}, Attack: {self.attack})"
