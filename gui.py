import pygame
from typing import Dict
from button import Button
from unit import Unit, UnitType 
from building import BuildingType

# ค่าคงที่สำหรับสีต่างๆ
GRAY = (128, 128, 128)
WHITE = (255, 255, 255)

class GUI:
    def __init__(self, game):
        # กำหนดค่าพื้นฐานสำหรับ GUI
        self.game = game
        self.action_buttons: Dict[str, Button] = {}  # ดิกชันนารีสำหรับปุ่มการกระทำ
        self.mode = "normal"  # โหมดปกติ
        self.font = pygame.font.Font(None, 24)  # ฟอนต์สำหรับข้อความ
        self.title_font = pygame.font.Font(None, 32)  # ฟอนต์สำหรับชื่อ
        self.create_buttons()  # สร้างปุ่ม

    def create_buttons(self):
        # สร้างปุ่มทั้งหมดและกำหนดตำแหน่ง
        self.update_button_positions()

    def update_button_positions(self):
        # กำหนดตำแหน่งและขนาดของปุ่ม
        sidebar_width = 200
        self.button_width = 180
        self.button_height = 40
        button_y = 20

        # สร้างปุ่มการกระทำต่างๆ
        self.action_buttons = {
            "move": Button(self.game.screen_width - sidebar_width + 10, button_y, self.button_width, self.button_height, "Move"),
            "attack": Button(self.game.screen_width - sidebar_width + 10, button_y + 50, self.button_width, self.button_height, "Attack"),
            "wait": Button(self.game.screen_width - sidebar_width + 10, button_y + 100, self.button_width, self.button_height, "Wait"),
            "cancel": Button(self.game.screen_width - sidebar_width + 10, button_y + 150, self.button_width, self.button_height, "Cancel"),
            "end_turn": Button(self.game.screen_width - sidebar_width + 10, self.game.screen_height - 70, self.button_width, 50, "End Turn"),
            "build": Button(self.game.screen_width - sidebar_width + 10, button_y + 200, self.button_width, self.button_height, "Build"),
        }

    def draw_sidebar(self):
        # วาดแถบด้านข้าง
        sidebar_width = 200
        sidebar_rect = pygame.Rect(self.game.screen_width - sidebar_width, 0, sidebar_width, self.game.screen_height)
        pygame.draw.rect(self.game.screen, GRAY, sidebar_rect)  # วาดแถบสีเทา

        # วาดปุ่มการกระทำ
        for action, button in self.action_buttons.items():
            button.draw(self.game.screen)

        # แสดงข้อมูลยูนิตที่เลือก
        if self.game.selected_unit:
            unit = self.game.selected_unit
            info = unit.unit_type.get_info()  # รับข้อมูลยูนิต
            title = self.title_font.render(info["name"], True, WHITE)
            self.game.screen.blit(title, (self.game.screen_width - sidebar_width + 10, 300))  # ปรับตำแหน่ง
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

        # แสดงข้อมูลของอาคารที่เลือก
        if self.game.selected_building:
            building_info = self.game.selected_building.get_info()
            title = self.title_font.render(building_info["name"], True, WHITE)
            self.game.screen.blit(title, (self.game.screen_width - sidebar_width + 10, 300))

            # เพิ่มปุ่มผลิตถ้าสร้างอาคารเป็น Tower
            if self.game.selected_building.building_type == BuildingType.TOWER:
                produce_soldier_button = Button(self.game.screen_width - sidebar_width + 10, 250, self.button_width, self.button_height, "Produce Soldier")
                produce_soldier_button.draw(self.game.screen)

                # ปุ่มผลิต Archer
                produce_archer_button = Button(self.game.screen_width - sidebar_width + 10, 300, self.button_width, self.button_height, "Produce Archer")
                produce_archer_button.draw(self.game.screen)

    def draw_game_info(self):
        # วาดข้อมูลเกม เช่น เทิร์นและผู้เล่นปัจจุบัน
        player_color = (0, 0, 255) if self.game.current_player == 1 else (255, 0, 0)
        turn_text = self.title_font.render(f"Turn {self.game.turn}", True, WHITE)
        player_text = self.title_font.render(f"Player {self.game.current_player}", True, player_color)

        turn_x = 10
        turn_y = self.game.screen_height - 90
        player_x = 10
        player_y = self.game.screen_height - 50

        self.game.screen.blit(turn_text, (turn_x, turn_y))  # วาดข้อความเทิร์น
        self.game.screen.blit(player_text, (player_x, player_y))  # วาดข้อความผู้เล่น

    def update_button_states(self):
        # อัปเดตสถานะของปุ่มตามยูนิตที่เลือก
        selected = self.game.selected_unit
        for button in self.action_buttons.values():
            button.enabled = True  # เปิดใช้งานปุ่มทั้งหมด
        
        # ปิดการใช้งานปุ่มถ้าไม่มีการเลือกยูนิต
        if not selected:
            self.action_buttons["move"].enabled = False
            self.action_buttons["attack"].enabled = False
            self.action_buttons["wait"].enabled = False
            self.action_buttons["cancel"].enabled = False
            self.action_buttons["build"].enabled = False

    def handle_button_events(self, event) -> bool:
        # จัดการกับเหตุการณ์ปุ่ม
        for action, button in self.action_buttons.items():
            if button.handle_event(event):
                if action == "move":
                    self.mode = "move"  # เปลี่ยนเป็นโหมดการเคลื่อนที่
                elif action == "attack":
                    self.mode = "attack"  # เปลี่ยนเป็นโหมดการโจมตี
                elif action == "wait":
                    if self.game.selected_unit:
                        self.game.selected_unit.moved = True  # ทำเครื่องหมายว่ายูนิตได้ทำการเคลื่อนที่แล้ว
                        self.game.selected_unit.attacked = True  # ทำเครื่องหมายว่ายูนิตได้โจมตีแล้ว
                        self.game.selected_unit = None  # ยกเลิกการเลือกยูนิต
                    self.mode = "normal"  # กลับสู่โหมดปกติ
                elif action == "cancel":
                    self.game.selected_unit = None  # ยกเลิกการเลือกยูนิต
                    self.game.selected_building = None  # ยกเลิกการเลือกอาคาร
                    self.mode = "normal"  # กลับสู่โหมดปกติ
                elif action == "end_turn":
                    self.game.end_turn()  # จบเทิร์น
                    self.game.selected_unit = None  # ยกเลิกการเลือกยูนิต
                    self.game.selected_building = None  # ยกเลิกการเลือกอาคาร
                    self.mode = "normal"  # กลับสู่โหมดปกติ
                elif action == "build":
                    if self.game.selected_unit:
                        self.mode = "build"  # เปลี่ยนเป็นโหมดสร้าง
                return True

        # จัดการกับปุ่มผลิตสำหรับ Tower
        if self.game.selected_building and self.game.selected_building.building_type == BuildingType.TOWER:
            # ตรวจสอบว่าปุ่มผลิต Soldier ถูกคลิก
            produce_soldier_button = Button(self.game.screen_width - 200 + 10, 250, self.button_width, self.button_height, "Produce Soldier")
            if produce_soldier_button.handle_event(event):
                new_unit = self.game.selected_building.produce_unit(UnitType.SOLDIER)  # ผลิต Soldier
                self.game.units.append(new_unit)  # เพิ่มยูนิตใหม่
                self.mode = "normal"  # กลับสู่โหมดปกติ
                return True

            # ตรวจสอบว่าปุ่มผลิต Archer ถูกคลิก
            produce_archer_button = Button(self.game.screen_width - 200 + 10, 300, self.button_width, self.button_height, "Produce Archer")
            if produce_archer_button.handle_event(event):
                new_unit = self.game.selected_building.produce_unit(UnitType.ARCHER)  # ผลิต Archer
                self.game.units.append(new_unit)  # เพิ่มยูนิตใหม่
                self.mode = "normal"  # กลับสู่โหมดปกติ
                return True

        return False

    def handle_events(self):
        # จัดการกับเหตุการณ์ต่างๆ
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False  # ปิดเกม
            
            if event.type == pygame.VIDEORESIZE:  
                self.game.update_grid_size()  # อัปเดตขนาดของกริด
                self.update_button_positions()  # อัปเดตตำแหน่งปุ่ม

            # จัดการกับเหตุการณ์ปุ่มก่อน
            if self.handle_button_events(event):
                continue  # ข้ามส่วนที่เหลือถ้ามีการกดปุ่ม

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                x = event.pos[0] // self.game.tile_size  # คำนวณตำแหน่ง x
                y = event.pos[1] // self.game.tile_size  # คำนวณตำแหน่ง y

                clicked_unit = self.game.get_unit_at(x, y)  # ตรวจสอบยูนิตที่ถูกคลิก
                if clicked_unit and clicked_unit.player == self.game.current_player:
                    self.game.selected_unit = clicked_unit  # เลือกยูนิต
                    self.mode = "build"  # เปลี่ยนเป็นโหมดสร้างเมื่อเลือกยูนิต

                if self.mode == "move" and self.game.selected_unit:
                    if self.game.is_valid_move(self.game.selected_unit, x, y):  # ตรวจสอบการเคลื่อนที่ที่ถูกต้อง
                        self.game.selected_unit.x = x  # ปรับตำแหน่งยูนิต
                        self.game.selected_unit.y = y
                        self.game.selected_unit.moved = True  # ทำเครื่องหมายว่ายูนิตได้เคลื่อนที่แล้ว
                        self.game.selected_unit = None  # ยกเลิกการเลือกยูนิต
                        self.mode = "normal"  # กลับสู่โหมดปกติ

                elif self.mode == "attack" and self.game.selected_unit:
                    target_unit = self.game.get_unit_at(x, y)  # ตรวจสอบยูนิตเป้าหมาย
                    if target_unit and target_unit.player != self.game.selected_unit.player:
                        target_unit.hp -= self.game.selected_unit.attack  # ลด HP ของยูนิตเป้าหมาย
                        self.game.selected_unit.attacked = True  # ทำเครื่องหมายว่ายูนิตได้โจมตีแล้ว
                        self.game.selected_unit = None  # ยกเลิกการเลือกยูนิต
                        self.mode = "normal"  # กลับสู่โหมดปกติ

                elif self.mode == "build" and self.game.selected_unit:
                    self.game.create_building(BuildingType.TOWER, x, y, self.game.current_player)  # สร้างอาคาร Tower
                    self.game.selected_unit = None  # ยกเลิกการเลือกยูนิต  
                    self.mode = "normal"  # กลับสู่โหมดปกติ  

        return True
