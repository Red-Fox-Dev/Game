import pygame
from unit import Unit, UnitType
from building import Building, BuildingType
from gui import GUI
from typing import List, Optional

# Constants
GRID_WIDTH = 40  # จำนวนช่องในแนวนอน
GRID_HEIGHT = 24  # จำนวนช่องในแนวตั้ง
FPS = 60  # อัตราเฟรมต่อวินาที
BLACK = (0, 0, 0)  # สีดำ
WHITE = (255, 255, 255)  # สีขาว
GREEN = (0, 255, 0)  # สีเขียว
RED = (255, 0, 0)  # สีแดง
BLUE = (181, 199, 235)  # สีน้ำเงิน
PLAYER_1_BUILDING_COLOR = (100, 100, 255)  # สีสำหรับอาคารของผู้เล่น 1
PLAYER_2_BUILDING_COLOR = (255, 100, 100)  # สีสำหรับอาคารของผู้เล่น 2
BUILDING_OUTLINE_COLOR = (0, 0, 128)  # สีกรอบสำหรับอาคาร

class Game:
    def __init__(self):
        self.screen_width, self.screen_height = 1900, 1024  # ขนาดหน้าต่างเริ่มต้น
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        pygame.display.set_caption("What war?")  # ตั้งชื่อหน้าต่าง
        self.clock = pygame.time.Clock()  # สร้างนาฬิกาเพื่อควบคุม FPS

        self.update_grid_size()  # อัปเดตขนาดของกริด

        self.units: List[Unit] = []  # รายการยูนิต
        self.buildings: List[Building] = []  # รายการอาคาร
        self.selected_unit: Optional[Unit] = None  # ยูนิตที่ถูกเลือก
        self.selected_building: Optional[Building] = None  # อาคารที่ถูกเลือก
        self.current_player = 1  # ผู้เล่นปัจจุบัน
        self.turn = 1  # เลขตาที่เล่นอยู่
        
        self.gui = GUI(self)  # สร้าง GUI
        self.initialize_units()  # เริ่มต้นยูนิต

    def update_grid_size(self):
        self.screen_width, self.screen_height = self.screen.get_size()  # อัปเดตขนาดหน้าจอ
        self.tile_size = min(self.screen_width // (GRID_WIDTH + 1), self.screen_height // GRID_HEIGHT)  # คำนวณขนาดของแต่ละช่อง

    def initialize_units(self):
        # เริ่มต้นยูนิตสำหรับผู้เล่น 1 และผู้เล่น 2
        self.units.append(Unit(UnitType.SOLDIER, 0, 1, 1))
        self.units.append(Unit(UnitType.ARCHER, 1, 2, 1))
        self.units.append(Unit(UnitType.SOLDIER, GRID_WIDTH - 2, GRID_HEIGHT - 2, 2))
        self.units.append(Unit(UnitType.ARCHER, GRID_WIDTH - 1, GRID_HEIGHT - 1, 2))

    def get_unit_at(self, x: int, y: int) -> Optional[Unit]:
        # ตรวจสอบว่ามียูนิตอยู่ที่ตำแหน่ง (x, y) หรือไม่
        for unit in self.units:
            if unit.x == x and unit.y == y:
                return unit
        return None

    def get_building_at(self, x: int, y: int) -> Optional[Building]:
        # ตรวจสอบว่ามีอาคารอยู่ที่ตำแหน่ง (x, y) หรือไม่
        for building in self.buildings:
            if building.x == x and building.y == y:
                return building
        return None

    def is_valid_move(self, unit: Unit, x: int, y: int) -> bool:
        # ตรวจสอบว่าการเคลื่อนที่ของยูนิตเป็นไปตามกฎหรือไม่
        return abs(unit.x - x) <= unit.move_range and abs(unit.y - y) <= unit.move_range

    def end_turn(self):
        # เปลี่ยนผู้เล่นและรีเซ็ตสถานะของยูนิต
        self.current_player = 1 if self.current_player == 2 else 2
        self.turn += 1
        for unit in self.units:
            unit.moved = False
            unit.attacked = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False  # ปิดโปรแกรมเมื่อกดปุ่มปิด

            if event.type == pygame.VIDEORESIZE:  
                self.update_grid_size()  # อัปเดตขนาดกริดเมื่อปรับขนาดหน้าต่าง
                self.gui.update_button_positions()  # เรียกฟังก์ชันจาก GUI

            # จัดการกับเหตุการณ์ปุ่มก่อน
            if self.gui.handle_button_events(event):  # ใช้ self.gui แทน self
                continue  # ข้ามการจัดการเหตุการณ์ต่อไปหากมีการกดปุ่ม

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                x = event.pos[0] // self.tile_size
                y = event.pos[1] // self.tile_size

                clicked_unit = self.get_unit_at(x, y)  # ตรวจสอบยูนิตที่ถูกคลิก
                clicked_building = self.get_building_at(x, y)  # ตรวจสอบอาคารที่ถูกคลิก

                if clicked_unit and clicked_unit.player == self.current_player:
                    self.selected_unit = clicked_unit  # เลือกยูนิต

                elif clicked_building and clicked_building.player == self.current_player:
                    self.selected_building = clicked_building  # เลือกอาคาร

                # จัดการการเคลื่อนที่
                if self.gui.mode == "move" and self.selected_unit:
                    if self.is_valid_move(self.selected_unit, x, y):
                        self.selected_unit.x = x
                        self.selected_unit.y = y
                        self.selected_unit.moved = True
                        self.selected_unit = None
                        self.gui.mode = "normal"

                # จัดการการโจมตี
                elif self.gui.mode == "attack" and self.selected_unit:
                    target_unit = self.get_unit_at(x, y)
                    if target_unit and target_unit.player != self.selected_unit.player:
                        target_unit.hp -= self.selected_unit.attack
                        self.selected_unit.attacked = True
                        self.selected_unit = None
                        self.gui.mode = "normal"

                # จัดการการสร้างอาคาร
                elif self.gui.mode == "build" and self.selected_unit:
                    self.create_building(BuildingType.TOWER, x, y, self.current_player)
                    self.selected_unit = None  
                    self.gui.mode = "normal"  

        return True

    def draw_hp_bar(self, unit: Unit):
        # วาดแถบ HP ของยูนิต
        hp_ratio = unit.hp / unit.max_hp
        hp_bar_width = self.tile_size
        hp_bar_height = 5  # ความสูงของแถบ HP

        # วาดพื้นหลัง
        pygame.draw.rect(self.screen, RED, 
                         (unit.x * self.tile_size, unit.y * self.tile_size - hp_bar_height - 2, hp_bar_width, hp_bar_height))

        # วาดแถบ HP
        pygame.draw.rect(self.screen, GREEN, 
                         (unit.x * self.tile_size, unit.y * self.tile_size - hp_bar_height - 2, hp_bar_width * hp_ratio, hp_bar_height))

        # วาดข้อความ HP บนแถบ HP
        font = pygame.font.Font(None, 24)
        hp_text = f"{unit.hp}/{unit.max_hp}"
        text_surface = font.render(hp_text, True, WHITE)
        
        # ปรับตำแหน่งข้อความให้อยู่เหนือแถบ HP
        text_rect = text_surface.get_rect(center=(unit.x * self.tile_size + hp_bar_width // 2, 
                                                   unit.y * self.tile_size - hp_bar_height - 10))
        self.screen.blit(text_surface, text_rect)

    def run(self):
        running = True
        while running:
            running = self.handle_events()  # จัดการเหตุการณ์

            self.screen.fill(BLACK)  # ล้างหน้าจอด้วยสีดำ

            # วาดกริด
            for x in range(GRID_WIDTH):
                for y in range(GRID_HEIGHT):
                    rect = pygame.Rect(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
                    pygame.draw.rect(self.screen, WHITE, rect, 1)  # วาดกรอบช่อง

            # วาดยูนิตและแถบ HP ของพวกเขา
            for unit in self.units:
                color = BLUE if unit.player == 1 else RED  # กำหนดสีตามผู้เล่น
                pygame.draw.rect(self.screen, color, 
                                 (unit.x * self.tile_size, unit.y * self.tile_size, self.tile_size, self.tile_size))
                self.draw_hp_bar(unit)  # เรียกฟังก์ชันเพื่อวาดแถบ HP และข้อความ

            # วาดอาคารพร้อมกรอบ
            for building in self.buildings:
                building_rect = pygame.Rect(building.x * self.tile_size, building.y * self.tile_size, self.tile_size, self.tile_size)

                # กำหนดสีของอาคารตามผู้เล่น
                building_color = PLAYER_1_BUILDING_COLOR if building.player == 1 else PLAYER_2_BUILDING_COLOR

                pygame.draw.rect(self.screen, building_color, building_rect)  # วาดสีของอาคาร
                pygame.draw.rect(self.screen, BUILDING_OUTLINE_COLOR, building_rect, 2)  # วาดกรอบอาคาร
                
                font = pygame.font.Font(None, 24)
                text_surface = font.render("Tower", True, WHITE)  # วาดข้อความ "Tower"
                text_rect = text_surface.get_rect(center=(building.x * self.tile_size + self.tile_size // 2, 
                                                           building.y * self.tile_size + self.tile_size // 2))
                self.screen.blit(text_surface, text_rect)

            # แสดงขอบเขตการเคลื่อนที่เมื่อเลือกยูนิต
            if self.selected_unit and self.gui.mode == "move":
                move_range = self.selected_unit.move_range
                for dx in range(-move_range, move_range + 1):
                    for dy in range(-move_range, move_range + 1):
                        if abs(dx) + abs(dy) <= move_range:
                            target_x = self.selected_unit.x + dx
                            target_y = self.selected_unit.y + dy
                            if 0 <= target_x < GRID_WIDTH and 0 <= target_y < GRID_HEIGHT:
                                move_rect = pygame.Rect(target_x * self.tile_size, target_y * self.tile_size, self.tile_size, self.tile_size)
                                pygame.draw.rect(self.screen, GREEN, move_rect, 2)  # วาดกรอบสีเขียว

            self.gui.draw_sidebar()  # วาดแถบด้านข้าง
            self.gui.draw_game_info()  # วาดข้อมูลเกม
            self.gui.update_button_states()  # อัปเดตสถานะของปุ่ม

            pygame.display.flip()  # แสดงผลการเปลี่ยนแปลงทั้งหมด
            self.clock.tick(FPS)  # ควบคุม FPS
    
    def create_building(self, building_type: BuildingType, x: int, y: int, player: int):
        # สร้างอาคารใหม่ที่ตำแหน่ง (x, y) หากตำแหน่งนั้นว่าง
        if not (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT):
            return  # ตำแหน่งไม่ถูกต้อง

        if self.get_unit_at(x, y) is not None:
            return  # ตำแหน่งนั้นมียูนิตอยู่แล้ว

        new_building = Building(building_type, x, y, player)  # สร้างอาคารใหม่
        self.buildings.append(new_building)  # เพิ่มอาคารใหม่ในรายการ
        print(f"Building created at ({x}, {y}) by player {player}")  # แสดงข้อความเมื่อสร้างอาคาร
