import pygame
from typing import Dict
from button import Button
from unit import Unit, UnitType
from building import BuildingType

# ค่าคงที่สำหรับสีต่างๆ
GRAY = (128, 128, 128)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)

class GUI:
    def __init__(self, game):
        self.game = game  # เก็บอ้างอิงถึงออบเจ็กต์เกม
        self.action_buttons: Dict[str, Button] = {}  # สร้างพจนานุกรมสำหรับปุ่มการกระทำ
        self.mode = "normal"  # โหมดเริ่มต้น
        self.font = pygame.font.Font(None, 24)  # ฟอนต์สำหรับข้อความ
        self.title_font = pygame.font.Font(None, 32)  # ฟอนต์สำหรับหัวข้อ
        self.tooltip_text = ""  # ข้อความ tooltip
        self.tooltip_pos = (0, 0)  # ตำแหน่ง tooltip
        self.create_buttons()  # สร้างปุ่ม

    def create_buttons(self):
        self.update_button_positions()  # อัปเดตตำแหน่งปุ่ม

    def update_button_positions(self):
        sidebar_width = 200  # ความกว้างของ sidebar
        self.button_width = 180  # ความกว้างของปุ่ม
        self.button_height = 40  # ความสูงของปุ่ม
        button_y = 20  # ตำแหน่งเริ่มต้นในแนวตั้งของปุ่ม

        # สร้างปุ่มสำหรับการกระทำต่างๆ
        self.action_buttons = {
            "move": Button(self.game.screen_width - sidebar_width + 10, button_y, self.button_width, self.button_height, "Move"),
            "attack": Button(self.game.screen_width - sidebar_width + 10, button_y + 50, self.button_width, self.button_height, "Attack"),
            "wait": Button(self.game.screen_width - sidebar_width + 10, button_y + 100, self.button_width, self.button_height, "Wait"),
            "cancel": Button(self.game.screen_width - sidebar_width + 10, button_y + 150, self.button_width, self.button_height, "Cancel"),
            "end_turn": Button(self.game.screen_width - sidebar_width + 10, self.game.screen_height - 70, self.button_width, 50, "End Turn"),
            "build": Button(self.game.screen_width - sidebar_width + 10, button_y + 200, self.button_width, self.button_height, "Build"),
        }

    def show_tooltip(self, text, pos):
        """ แสดง tooltip ที่ตำแหน่งที่กำหนด """
        self.tooltip_text = text
        self.tooltip_pos = pos

    def draw_tooltip(self):
        """ วาด tooltip บนหน้าจอ """
        if self.tooltip_text:
            tooltip_surface = self.font.render(self.tooltip_text, True, WHITE)
            tooltip_rect = tooltip_surface.get_rect(center=self.tooltip_pos)
            pygame.draw.rect(self.game.screen, GRAY, tooltip_rect.inflate(10, 10))  # วาดพื้นหลัง
            self.game.screen.blit(tooltip_surface, tooltip_rect)  # วาดข้อความ tooltip

    def draw_sidebar(self):
        sidebar_width = 200  # กำหนดความกว้างของ sidebar
        sidebar_rect = pygame.Rect(self.game.screen_width - sidebar_width, 0, sidebar_width, self.game.screen_height)
        pygame.draw.rect(self.game.screen, GRAY, sidebar_rect)  # วาด sidebar

        # วาดปุ่มการกระทำ
        for action, button in self.action_buttons.items():
            button.draw(self.game.screen)

        # แสดงข้อมูลยูนิตที่ถูกเลือก
        if self.game.selected_unit:
            unit = self.game.selected_unit
            title = self.title_font.render(unit.unit_type.get_info()["name"], True, WHITE)
            self.game.screen.blit(title, (self.game.screen_width - sidebar_width + 10, 300))
            stats_text = [
                f"HP: {unit.hp}/{unit.max_hp}",
                f"Attack: {unit.attack}",
                f"Move Range: {unit.move_range}",
                f"Attack Range: {unit.attack_range}",
                f"Status: {'Acted' if unit.moved and unit.attacked else 'Ready'}"
            ]
            for i, text in enumerate(stats_text):
                surface = self.font.render(text, True, WHITE)
                self.game.screen.blit(surface, (self.game.screen_width - sidebar_width + 10, 350 + i * 25))

        # แสดงข้อมูลอาคารที่ถูกเลือก
        if self.game.selected_building:
            building_info = self.game.selected_building.get_info()
            title = self.title_font.render(building_info["name"], True, WHITE)
            self.game.screen.blit(title, (self.game.screen_width - sidebar_width + 10, 300))

            # สร้างปุ่มผลิตยูนิตถ้าคือ Tower
            if self.game.selected_building.building_type == BuildingType.TOWER:
                self.produce_soldier_button = Button(self.game.screen_width - sidebar_width + 10, 250, self.button_width, self.button_height, "Produce Soldier")
                self.produce_archer_button = Button(self.game.screen_width - sidebar_width + 10, 300, self.button_width, self.button_height, "Produce Archer")
                self.produce_soldier_button.draw(self.game.screen)
                self.produce_archer_button.draw(self.game.screen)

    def draw_game_info(self):
        # แสดงข้อมูลของผู้เล่น
        player_color = BLUE if self.game.current_player == 1 else RED
        player_text = self.title_font.render(f"Player {self.game.current_player}", True, player_color)
        player_money = self.game.money_system.check_balance(self.game.current_player)
        money_text = self.title_font.render(player_money, True, WHITE)
        round_text = self.title_font.render(f"Round {self.game.round}", True, WHITE)

        # กำหนดตำแหน่งของข้อความ
        player_x = 10
        player_y = self.game.screen_height - 90
        money_x = 10
        money_y = self.game.screen_height - 60
        turn_x = 10
        turn_y = self.game.screen_height - 30

        # วาดข้อความลงบนหน้าจอ
        self.game.screen.blit(player_text, (player_x, player_y))
        self.game.screen.blit(money_text, (money_x, money_y))
        self.game.screen.blit(round_text, (turn_x, turn_y))

        # วาด tooltip หากมี
        self.draw_tooltip()

    def update_button_states(self):
        selected = self.game.selected_unit  # ตรวจสอบยูนิตที่ถูกเลือก
        for button in self.action_buttons.values():
            button.enabled = True  # เปิดใช้งานปุ่มทั้งหมด

        # ปิดใช้งานปุ่มถ้าไม่มียูนิตที่ถูกเลือก
        if not selected:
            self.action_buttons["move"].enabled = False
            self.action_buttons["attack"].enabled = False
            self.action_buttons["wait"].enabled = False
            self.action_buttons["cancel"].enabled = False
            self.action_buttons["build"].enabled = False

    def handle_button_events(self, event) -> bool:
        # ตรวจสอบเหตุการณ์ที่เกิดจากปุ่ม
        for action, button in self.action_buttons.items():
            if button.handle_event(event):
                if action == "move":
                    self.mode = "move"  # เปลี่ยนโหมดเป็นการเคลื่อนที่
                elif action == "attack":
                    self.mode = "attack"  # เปลี่ยนโหมดเป็นการโจมตี
                elif action == "wait":
                    if self.game.selected_unit:
                        self.game.selected_unit.moved = True
                        self.game.selected_unit.attacked = True
                        self.game.selected_unit = None
                    self.mode = "normal"  # กลับไปที่โหมดปกติ
                elif action == "cancel":
                    self.game.selected_unit = None
                    self.game.selected_building = None
                    self.mode = "normal"  # กลับไปที่โหมดปกติ
                elif action == "end_turn":
                    self.game.end_turn()  # จบเทิร์น
                    self.game.selected_unit = None
                    self.game.selected_building = None
                    self.mode = "normal"  # กลับไปที่โหมดปกติ
                elif action == "build":
                    if self.game.selected_unit:
                        cost = 50  # ค่าก่อสร้างอาคาร
                        if self.game.money_system.subtract_money(cost, self.game.current_player):
                            self.mode = "build"  # เปลี่ยนโหมดเป็นการสร้าง
                        else:
                            print("Not enough money to build!")  # แจ้งเตือนถ้าเงินไม่พอ
                return True

        # ตรวจสอบเหตุการณ์ปุ่มผลิตยูนิต
        if self.game.selected_building and self.game.selected_building.building_type == BuildingType.TOWER:
            produce_soldier_button = Button(self.game.screen_width - 200 + 10, 250, self.button_width, self.button_height, "Produce Soldier")
            if produce_soldier_button.handle_event(event):
                cost = 50  # ค่าผลิต Soldier
                if self.game.money_system.subtract_money(cost, self.game.current_player):
                    new_unit = self.game.selected_building.produce_unit(UnitType.SOLDIER)  # ผลิต Soldier
                    self.game.units.append(new_unit)
                    self.mode = "normal"  # กลับไปที่โหมดปกติ
                else:
                    print("Not enough money to produce Soldier!")  # แจ้งเตือนถ้าเงินไม่พอ

            produce_archer_button = Button(self.game.screen_width - 200 + 10, 300, self.button_width, self.button_height, "Produce Archer")
            if produce_archer_button.handle_event(event):
                cost = 75  # ค่าผลิต Archer
                if self.game.money_system.subtract_money(cost, self.game.current_player):
                    new_unit = self.game.selected_building.produce_unit(UnitType.ARCHER)  # ผลิต Archer
                    self.game.units.append(new_unit)
                    self.mode = "normal"  # กลับไปที่โหมดปกติ
                else:
                    print("Not enough money to produce Archer!")  # แจ้งเตือนถ้าเงินไม่พอ

        return False  # ไม่มีเหตุการณ์ที่จับได้

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False  # ออกจากเกมถ้ากดปิดหน้าต่าง
            
            if event.type == pygame.VIDEORESIZE:  
                self.game.update_grid_size()  # อัปเดตขนาดกริดเมื่อมีการปรับขนาดหน้าต่าง
                self.update_button_positions()  # อัปเดตตำแหน่งปุ่ม

            if self.handle_button_events(event):
                continue  # หากมีเหตุการณ์ปุ่มถูกจับได้ ให้ข้ามไป

            # ตรวจสอบการคลิกเมาส์
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                x = event.pos[0] // self.game.tile_size  # คำนวณตำแหน่ง x
                y = event.pos[1] // self.game.tile_size  # คำนวณตำแหน่ง y

                clicked_unit = self.game.get_unit_at(x, y)
                if clicked_unit and clicked_unit.player == self.game.current_player:  # ตรวจสอบยูนิตที่ถูกเลือก
                    self.game.selected_unit = clicked_unit
                    self.mode = "build"  # เปลี่ยนโหมดเป็นการสร้าง

                # การเคลื่อนที่ของยูนิต
                if self.mode == "move" and self.game.selected_unit:
                    if self.game.is_valid_move(self.game.selected_unit, x, y):
                        self.game.selected_unit.x = x
                        self.game.selected_unit.y = y
                        self.game.selected_unit.moved = True
                        self.game.selected_unit = None
                        self.mode = "normal"  # กลับไปที่โหมดปกติ

                # การโจมตีของยูนิต
                elif self.mode == "attack" and self.game.selected_unit:
                    target_unit = self.game.get_unit_at(x, y)
                    if target_unit and target_unit.player != self.game.selected_unit.player:
                        damage = self.game.selected_unit.attack  # คำนวณความเสียหาย
                        target_unit.hp = max(0, target_unit.hp - damage)  # ลดเลือดไม่ให้ต่ำกว่า 0
        
                        # ตรวจสอบว่าเลือดหมดหรือไม่
                        if target_unit.hp == 0:
                            self.game.units.remove(target_unit)  # ลบยูนิตออกจากรายการ
                            print(f"{target_unit.unit_type.get_info()['name']} has been defeated!")  # แจ้งเตือน
            
                        self.game.selected_unit.attacked = True  # ทำเครื่องหมายว่ามีการโจมตีแล้ว
                        self.game.selected_unit = None
                        self.mode = "normal"  # กลับไปที่โหมดปกติ

                # การสร้างอาคาร
                elif self.mode == "build" and self.game.selected_unit:
                    self.game.create_building(BuildingType.TOWER, x, y, self.game.current_player)  # สร้าง Tower
                    self.game.selected_unit = None  
                    self.mode = "normal"  # กลับไปที่โหมดปกติ  

            # ตรวจสอบว่าเมาส์อยู่เหนือปุ่มผลิตยูนิตหรือไม่
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if self.game.selected_building and self.game.selected_building.building_type == BuildingType.TOWER:
                if self.produce_soldier_button.rect.collidepoint(mouse_x, mouse_y):
                    self.show_tooltip("Cost: 50", (mouse_x, mouse_y))  # แสดง tooltip สำหรับ Soldier
                elif self.produce_archer_button.rect.collidepoint(mouse_x, mouse_y):
                    self.show_tooltip("Cost: 75", (mouse_x, mouse_y))  # แสดง tooltip สำหรับ Archer
                else:
                    self.tooltip_text = ""  # ซ่อน tooltip ถ้าเมาส์ไม่ได้อยู่เหนือปุ่ม

        return True  # กลับสู่เกมถ้ายังไม่ได้ปิด
