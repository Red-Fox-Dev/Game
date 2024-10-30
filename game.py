import pygame
from unit import Unit, UnitType
from building import Building, BuildingType, Tower
from gui import GUI
from typing import List, Optional
from money_system import MoneySystem  

# ค่าคงที่
GRID_WIDTH = 40  # ความกว้างของกริด
GRID_HEIGHT = 24  # ความสูงของกริด
FPS = 60  # เฟรมเรต
# สีต่าง ๆ
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (181, 199, 235)
PLAYER_1_BUILDING_COLOR = (100, 100, 255)  # สีของอาคารของผู้เล่น 1
PLAYER_2_BUILDING_COLOR = (255, 100, 100)  # สีของอาคารของผู้เล่น 2
BUILDING_OUTLINE_COLOR = (0, 0, 128)  # สีเส้นขอบของอาคาร

class Game:
    def __init__(self):
        # เริ่มต้นหน้าต่างเกม
        self.screen_width, self.screen_height = 1900, 1024
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        pygame.display.set_caption("What war?")  # ตั้งชื่อหน้าต่าง
        self.clock = pygame.time.Clock()  # นาฬิกาเพื่อควบคุมเฟรมเรต
        # เริ่มต้นระบบเงิน
        self.money_system = MoneySystem(init_amount_player1=250, init_amount_player2=250, reward=100, build_cost=50)
        self.update_grid_size()  # อัปเดตขนาดกริด
        self.tower_count = {1: 0, 2: 0}  # นับจำนวนหอคอยของแต่ละผู้เล่น
        
        # รายการสำหรับยูนิตและอาคาร
        self.units: List[Unit] = []
        self.buildings: List[Building] = []
        self.selected_unit: Optional[Unit] = None  # ยูนิตที่เลือก
        self.selected_building: Optional[Building] = None  # อาคารที่เลือก
        self.current_player = 1  # ผู้เล่นปัจจุบัน
        self.round = 1  # รอบปัจจุบัน
        
        self.gui = GUI(self)  # เริ่มต้น GUI
        self.initialize_units()  # สร้างยูนิตเริ่มต้น

    def update_grid_size(self):
        # อัปเดตขนาดกริดตามขนาดหน้าจอ
        self.screen_width, self.screen_height = self.screen.get_size()
        self.tile_size = min(self.screen_width // (GRID_WIDTH + 1), self.screen_height // GRID_HEIGHT)

    def initialize_units(self):
        # สร้างยูนิตเริ่มต้นสำหรับผู้เล่นทั้งสอง
        self.units.append(Unit(UnitType.SOLDIER, 0, 1, 1))  # ยูนิตของผู้เล่น 1
        self.units.append(Unit(UnitType.ARCHER, 1, 2, 1))  # ยูนิตของผู้เล่น 1
        self.units.append(Unit(UnitType.SOLDIER, GRID_WIDTH - 2, GRID_HEIGHT - 2, 2))  # ยูนิตของผู้เล่น 2
        self.units.append(Unit(UnitType.ARCHER, GRID_WIDTH - 1, GRID_HEIGHT - 1, 2))  # ยูนิตของผู้เล่น 2

    def get_unit_at(self, x: int, y: int) -> Optional[Unit]:
        # ตรวจสอบว่ามียูนิตอยู่ที่ตำแหน่งกริดที่ระบุหรือไม่
        for unit in self.units:
            if unit.x == x and unit.y == y:
                return unit
        return None

    def get_building_at(self, x: int, y: int) -> Optional[Building]:
        # ตรวจสอบว่ามีอาคารอยู่ที่ตำแหน่งกริดที่ระบุหรือไม่
        for building in self.buildings:
            if building.x == x and building.y == y:
                return building
        return None

    def is_valid_move(self, unit: Unit, x: int, y: int) -> bool:
        # ตรวจสอบว่ายูนิตสามารถเคลื่อนที่ไปยังตำแหน่งที่ระบุได้หรือไม่
        return abs(unit.x - x) <= unit.move_range and abs(unit.y - y) <= unit.move_range

    def end_turn(self):
        # สิ้นสุดเทิร์นของผู้เล่นปัจจุบัน
        self.money_system.add_money(self.money_system.reward, self.current_player)  # เพิ่มเงินให้ผู้เล่น
        self.current_player = 2 if self.current_player == 1 else 1  # เปลี่ยนผู้เล่น
        if self.current_player == 1:
            self.round += 1  # เพิ่มรอบสำหรับผู้เล่น 1
        for unit in self.units:
            unit.moved = False  # รีเซ็ตสถานะการเคลื่อนที่ของยูนิตทั้งหมด
            unit.attacked = False  # รีเซ็ตสถานะการโจมตี

        self.selected_unit = None  # รีเซ็ตยูนิตที่เลือก
        self.selected_building = None  # รีเซ็ตอาคารที่เลือก
        self.gui.mode = "normal"  # เปลี่ยนโหมด GUI

    def handle_events(self):
        # จัดการกับเหตุการณ์ต่าง ๆ ที่เกิดขึ้นในเกม
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False  # ออกจากเกมเมื่อปิดหน้าต่าง
            
            if event.type == pygame.VIDEORESIZE:
                self.update_grid_size()  # อัปเดตขนาดกริดเมื่อเปลี่ยนขนาดหน้าต่าง
                self.gui.update_button_positions()  # อัปเดตตำแหน่งปุ่ม GUI

            if self.gui.handle_button_events(event):
                continue  # หากมีการจัดการปุ่มใน GUI ก็ไม่ต้องทำอะไรต่อ

            if event.type == pygame.MOUSEBUTTONDOWN:
                x = event.pos[0] // self.tile_size  # คำนวณตำแหน่งกริดจากตำแหน่งเมาส์
                y = event.pos[1] // self.tile_size

                if event.button == 1:  # คลิกซ้าย
                    clicked_unit = self.get_unit_at(x, y)  # ตรวจสอบยูนิตที่ถูกคลิก
                    clicked_building = self.get_building_at(x, y)  # ตรวจสอบอาคารที่ถูกคลิก

                    if clicked_unit and clicked_unit.player == self.current_player and not clicked_unit.moved:
                        self.selected_unit = clicked_unit  # เลือกยูนิต
                        self.gui.mode = "select"  # เปลี่ยนโหมดเป็นเลือกยูนิต

                    elif clicked_building and clicked_building.player == self.current_player:
                        self.selected_building = clicked_building  # เลือกอาคาร
                        if isinstance(self.selected_building, Tower):
                            self.gui.show_unit_selection_menu(self.selected_building)  # แสดงเมนูเลือกยูนิต

                    if self.gui.mode == "build" and self.selected_unit:
                        self.add_tower(x, y)  # เพิ่มหอคอย
                        self.selected_unit.moved = True  # ตั้งค่าสถานะการเคลื่อนที่ของยูนิต
                        self.selected_unit = None  # รีเซ็ตยูนิตที่เลือก
                        self.gui.mode = "normal"  # เปลี่ยนกลับเป็นโหมดปกติ

                    if self.gui.mode == "move" and self.selected_unit:
                        if self.is_valid_move(self.selected_unit, x, y):  # ตรวจสอบการเคลื่อนที่
                            if self.get_building_at(x, y) is None and self.get_unit_at(x, y) is None:
                                self.selected_unit.x = x  # อัปเดตตำแหน่งยูนิต
                                self.selected_unit.y = y
                                self.selected_unit.moved = True  # ตั้งค่าสถานะการเคลื่อนที่ของยูนิต
                                self.selected_unit = None  # รีเซ็ตยูนิตที่เลือก
                                self.gui.mode = "normal"  # เปลี่ยนกลับเป็นโหมดปกติ

                    elif self.gui.mode == "attack" and self.selected_unit:
                        target_unit = self.get_unit_at(x, y)  # ตรวจสอบยูนิตเป้าหมาย
                        if target_unit and target_unit.player != self.selected_unit.player:
                            target_unit.hp = max(0, target_unit.hp - self.selected_unit.attack)  # ลด HP ของยูนิตเป้าหมาย
                            if target_unit.hp == 0:
                                self.units.remove(target_unit)  # ลบยูนิตที่ถูกโจมตีออกจากรายการ
                                print(f"{target_unit.unit_type.get_info()['name']} has been defeated!")  # แสดงข้อความเมื่อยูนิตถูกทำลาย
                            self.selected_unit.moved = True  # ตั้งค่าสถานะการเคลื่อนที่ของยูนิต
                            self.selected_unit = None  # รีเซ็ตยูนิตที่เลือก
                            self.gui.mode = "normal"  # เปลี่ยนกลับเป็นโหมดปกติ

                elif event.button == 3:  # คลิกขวา
                    if self.selected_unit:
                        self.selected_unit = None  # รีเซ็ตยูนิตที่เลือก
                        self.gui.mode = "normal"  # เปลี่ยนกลับเป็นโหมดปกติ
                    elif self.selected_building:
                        self.selected_building = None  # รีเซ็ตอาคารที่เลือก
                        self.gui.mode = "normal"  # เปลี่ยนกลับเป็นโหมดปกติ

        return True

    def handle_button_events(self, event) -> bool:
        # จัดการเหตุการณ์ปุ่มใน GUI
        for action, button in self.gui.action_buttons.items():
            if button.handle_event(event):  # หากปุ่มถูกกด
                if action == "move":
                    self.gui.mode = "move"  # เปลี่ยนโหมดเป็นเคลื่อนที่
                elif action == "attack":
                    self.gui.mode = "attack"  # เปลี่ยนโหมดเป็นโจมตี
                elif action == "wait":
                    if self.selected_unit:
                        self.selected_unit.moved = True  # ตั้งค่าสถานะการเคลื่อนที่ของยูนิต
                        self.selected_unit.attacked = True  # ตั้งค่าสถานะการโจมตีของยูนิต
                        self.selected_unit = None  # รีเซ็ตยูนิตที่เลือก
                    self.gui.mode = "normal"  # เปลี่ยนกลับเป็นโหมดปกติ
                elif action == "cancel":
                    self.selected_unit = None  # รีเซ็ตยูนิตที่เลือก
                    self.selected_building = None  # รีเซ็ตอาคารที่เลือก
                    self.gui.mode = "normal"  # เปลี่ยนกลับเป็นโหมดปกติ
                elif action == "end_turn":
                    self.end_turn()  # สิ้นสุดเทิร์น
                    self.selected_unit = None  # รีเซ็ตยูนิตที่เลือก
                    self.selected_building = None  # รีเซ็ตอาคารที่เลือก
                    self.gui.mode = "normal"  # เปลี่ยนกลับเป็นโหมดปกติ
                elif action == "build":
                    if isinstance(self.selected_building, Tower):
                        self.gui.show_unit_selection_menu(self.selected_building)  # แสดงเมนูเลือกยูนิตถ้าหากเลือกหอคอย
                    else:
                        print("No building selected or not a Tower.")  # แสดงข้อความเมื่อไม่ได้เลือกอาคารที่ถูกต้อง
                elif action == "create_unit":
                    if self.money_system.amount(self.current_player) >= self.money_system.build_cost:
                        self.money_system.add_money(-self.money_system.build_cost, self.current_player)  # หักเงินในการสร้างยูนิต
                        self.create_unit(UnitType.SOLDIER, 0, 0, self.current_player)  # สร้างยูนิตใหม่
                    else:
                        print("Not enough money to create a unit.")  # แสดงข้อความเมื่อเงินไม่พอ
                return True
        return False

    def draw_hp_bar(self, unit: Unit):
        # วาดแถบ HP ของยูนิต
        hp_ratio = unit.hp / unit.max_hp  # คำนวณสัดส่วน HP
        hp_bar_width = self.tile_size  # ความกว้างของแถบ HP
        hp_bar_height = 5  # ความสูงของแถบ HP

        # วาดแถบพื้นหลังของ HP
        pygame.draw.rect(self.screen, RED, 
                         (unit.x * self.tile_size, unit.y * self.tile_size - hp_bar_height - 2, hp_bar_width, hp_bar_height))

        # วาดแถบ HP ตามสัดส่วน
        pygame.draw.rect(self.screen, GREEN, 
                         (unit.x * self.tile_size, unit.y * self.tile_size - hp_bar_height - 2, hp_bar_width * hp_ratio, hp_bar_height))

        # วาดข้อความแสดงค่า HP
        font = pygame.font.Font(None, 24)
        hp_text = f"{unit.hp}/{unit.max_hp}"  # ข้อความแสดง HP
        text_surface = font.render(hp_text, True, WHITE)  # สร้างพื้นผิวข้อความ
        
        text_rect = text_surface.get_rect(center=(unit.x * self.tile_size + hp_bar_width // 2, 
                                                   unit.y * self.tile_size - hp_bar_height - 10))
        self.screen.blit(text_surface, text_rect)  # แสดงข้อความบนหน้าจอ

    def run(self):
        # ฟังก์ชันหลักในการทำงานของเกม
        running = True
        while running:
            running = self.handle_events()  # จัดการเหตุการณ์

            self.screen.fill(BLACK)  # ล้างหน้าจอด้วยสีดำ

            # วาดกริด
            for x in range(GRID_WIDTH):
                for y in range(GRID_HEIGHT):
                    rect = pygame.Rect(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
                    pygame.draw.rect(self.screen, WHITE, rect, 1)  # วาดกรอบกริด

            # วาดยูนิต
            for unit in self.units:
                if unit.hp > 0:  # ตรวจสอบว่ายูนิตมี HP มากกว่า 0 หรือไม่
                    color = BLUE if unit.player == 1 else RED  # กำหนดสีของยูนิตตามผู้เล่น
                    pygame.draw.rect(self.screen, color, 
                                     (unit.x * self.tile_size, unit.y * self.tile_size, self.tile_size, self.tile_size))  # วาดยูนิต
                    self.draw_hp_bar(unit)  # วาดแถบ HP ของยูนิต

            # วาดอาคาร
            for building in self.buildings:
                building_rect = pygame.Rect(building.x * self.tile_size, building.y * self.tile_size, self.tile_size, self.tile_size)
                building_color = PLAYER_1_BUILDING_COLOR if building.player == 1 else PLAYER_2_BUILDING_COLOR  # กำหนดสีของอาคารตามผู้เล่น
                pygame.draw.rect(self.screen, building_color, building_rect)  # วาดอาคาร
                pygame.draw.rect(self.screen, BUILDING_OUTLINE_COLOR, building_rect, 2)  # วาดเส้นขอบอาคาร

                font = pygame.font.Font(None, 24)
                text_surface = font.render("Tower", True, WHITE)  # ข้อความแสดงประเภทอาคาร
                text_rect = text_surface.get_rect(center=(building.x * self.tile_size + self.tile_size // 2, 
                                                           building.y * self.tile_size + self.tile_size // 2))
                self.screen.blit(text_surface, text_rect)  # แสดงข้อความบนหน้าจอ

            # วาดพื้นที่เคลื่อนที่ของยูนิตที่ถูกเลือก
            if self.selected_unit:
                for dx in range(-self.selected_unit.move_range, self.selected_unit.move_range + 1):
                    for dy in range(-self.selected_unit.move_range, self.selected_unit.move_range + 1):
                        if abs(dx) + abs(dy) <= self.selected_unit.move_range:  # ตรวจสอบพื้นที่เคลื่อนที่
                            target_x = self.selected_unit.x + dx
                            target_y = self.selected_unit.y + dy
                            if 0 <= target_x < GRID_WIDTH and 0 <= target_y < GRID_HEIGHT:
                                build_rect = pygame.Rect(target_x * self.tile_size, target_y * self.tile_size, self.tile_size, self.tile_size)
                                pygame.draw.rect(self.screen, YELLOW, build_rect, 2)  # วาดพื้นที่เคลื่อนที่

            # แสดงเมนูการเลือกยูนิตถ้าเลือกอาคาร
            if self.selected_building and isinstance(self.selected_building, Tower):
                self.gui.show_unit_selection_menu(self.selected_building)

            # วาดแถบด้านข้างและข้อมูลเกม
            self.gui.draw_sidebar()  # วาดแถบด้านข้าง
            self.gui.draw_game_info()  # วาดข้อมูลเกม
            self.gui.update_button_states()  # อัปเดตสถานะของปุ่มใน GUI

            pygame.display.flip()  # อัปเดตหน้าจอ
            self.clock.tick(FPS)  # ควบคุมเฟรมเรต

    def create_unit(self, unit_type: UnitType, x: int, y: int, player: int):
        # สร้างยูนิตใหม่
        if not (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT):  # ตรวจสอบว่าตำแหน่งอยู่ในกริด
            return

        if self.get_unit_at(x, y) is not None:  # ตรวจสอบว่ามียูนิตอยู่แล้วหรือไม่
            return

        new_unit = Unit(unit_type, x, y, player)  # สร้างยูนิตใหม่
        self.units.append(new_unit)  # เพิ่มยูนิตลงในรายการ
        print(f"Unit created at ({x}, {y}) by player {player}")  # แสดงข้อความเมื่อสร้างยูนิต
        self.create_unit_around_tower(new_unit)  # สร้างยูนิตรอบ ๆ หอคอย

    def create_building(self, building_type: BuildingType, x: int, y: int, player: int):
        # สร้างอาคารใหม่
        if not (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT):  # ตรวจสอบว่าตำแหน่งอยู่ในกริด
            return

        if self.get_unit_at(x, y) is not None:  # ตรวจสอบว่ามียูนิตอยู่แล้วหรือไม่
            return

        if building_type == BuildingType.TOWER:  # ถ้าเป็นหอคอย
            if self.tower_count[player] >= 1:  # ตรวจสอบว่าผู้เล่นมีหอคอยแล้วหรือไม่
                print(f"Player {player} already has a tower. Cannot build another.")  # แสดงข้อความเมื่อไม่สามารถสร้างได้
                return
            else:
                self.tower_count[player] += 1  # เพิ่มจำนวนหอคอยของผู้เล่น

        new_building = Building(building_type, x, y, player)  # สร้างอาคารใหม่
        self.buildings.append(new_building)  # เพิ่มอาคารลงในรายการ
        print(f"Building created at ({x}, {y}) by player {player}")  # แสดงข้อความเมื่อสร้างอาคาร

    def add_tower(self, x: int, y: int):
        # เพิ่มหอคอยในตำแหน่งที่กำหนด
        if self.tower_count[self.current_player] < 1:  # ตรวจสอบว่าผู้เล่นมีหอคอยอยู่แล้วหรือไม่
            if self.is_valid_move(self.selected_unit, x, y) and self.get_building_at(x, y) is None:  # ตรวจสอบการเคลื่อนที่
                if self.money_system.amount(self.current_player) >= self.money_system.build_cost:  # ตรวจสอบว่าเงินเพียงพอหรือไม่
                    self.money_system.add_money(-self.money_system.build_cost, self.current_player)  # หักเงินในการสร้าง
                    self.create_building(BuildingType.TOWER, x, y, self.current_player)  # สร้างหอคอย
                    print(f"Tower created at ({x}, {y}) by player {self.current_player}")  # แสดงข้อความเมื่อสร้างหอคอย
                else:
                    print("Not enough money to build.")  # แสดงข้อความเมื่อเงินไม่พอ
        else:
            print(f"Player {self.current_player} already has a tower. Cannot build another.")  # แสดงข้อความเมื่อผู้เล่นมีหอคอยแล้ว

    def create_unit_around_tower(self, tower: Building):
        # สร้างยูนิตรอบ ๆ หอคอย
        possible_positions = [
            (tower.x - 1, tower.y), (tower.x + 1, tower.y),
            (tower.x, tower.y - 1), (tower.x, tower.y + 1),
            (tower.x - 1, tower.y - 1), (tower.x - 1, tower.y + 1),
            (tower.x + 1, tower.y - 1), (tower.x + 1, tower.y + 1)
        ]

        for x, y in possible_positions:
            if self.is_valid_move(self.selected_unit, x, y) and self.get_unit_at(x, y) is None:  # ตรวจสอบตำแหน่งว่าสามารถสร้างได้หรือไม่
                new_unit = Unit(UnitType.SOLDIER, x, y, self.current_player)  # สร้างยูนิตใหม่
                self.units.append(new_unit)  # เพิ่มยูนิตลงในรายการ
                print(f"Unit created at ({x}, {y}) with name: {new_unit.unit_type.get_info()['name']}")  # แสดงข้อความเมื่อสร้างยูนิต
                break  # ออกจากลูปหลังจากสร้างยูนิตหนึ่งตัว
