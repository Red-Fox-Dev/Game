import pygame
import pytmx
from .game_config import GameConfig
from .iso_map import IsometricMap
from .camera import Camera
from .game_object import GameObject
from .Unit import Unit
from .Path import PathFinder
from .Point import CapturePoint
import random
import math
from .Unit import Unit,UnitType
from .Tower import Tower
from .monster import Monster
from .Boss import Boss


class Game:
    def __init__(self, config: GameConfig):
        pygame.init()
        self.config = config
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.iso_map = IsometricMap("assets/Map1.tmx", config)
        self.camera = Camera(config, self.iso_map.width, self.iso_map.height)
        self.debug_font = pygame.font.Font("assets/Fonts/PixgamerRegular-OVD6A.ttf", 24)
        self.path_finder = PathFinder(self.iso_map)
        self.selected_unit = None
        self.selected_tower = None
        self.current_action = None
        self.last_time = pygame.time.get_ticks()
        self.walkable_tiles = []
        self.capture_points = []
        self.player_money = [250, 250]
        self.income_next_turn = [0, 0]  # เงินที่ได้จากจุดยึดครองในเทิร์นถัดไป
        self.current_round = 1
        self.create_tower_button = None
        self.towers = []
        self.tower_created = [False, False]
        self.unit_creation_button = None  # ปุ่มสำหรับสร้างยูนิต
        self.unit_type_to_create = None  # ประเภทของยูนิตที่จะสร้าง
        self.GRID_WIDTH = self.iso_map.tmx_data.width  # จำนวนช่องในแนวนอนจาก TMX
        self.GRID_HEIGHT = self.iso_map.tmx_data.height  # จำนวนช่องในแนวตั้งจาก TMX
        self.last_turn_time = 0  # เวลาของเทิร์นล่าสุด
        self.turn_interval = 1000  # หรือค่าที่คุณต้องการ
        self.boss = None  # สร้างตัวแปรสำหรับบอส
        self.boss_spawn_rounds = 5  # จำนวนรอบที่บอสจะเกิดใหม่
        self.monsters = []  # สร้างตัวแปรสำหรับมอนสเตอร์
        self.monster_count = 0  # จำนวนมอนสเตอร์ที่มีอยู่
        self.turns_since_last_spawn = 0  # จำนวนเทิร์นตั้งแต่การเกิดใหม่ครั้งล่าสุด
        self.boss_spawn_sound = pygame.mixer.Sound("sound/Boss_spawn.mp3")
        self.boss_spawn_sound.set_volume(0.3)
        self.turns_since_last_boss_move = 0  # ตัวแปรใหม่สำหรับติดตามจำนวนเทิร์นที่บอสไม่เคลื่อนที่

        self.move_button_animation = {
        'scale': 1.0,
        'color': (0, 255, 0),
        'start_time': 0,
        'duration': 500,  # ระยะเวลา animation
        'active': False
        }
        self.attack_button_animation = {
            'scale': 1.0,
            'color': (255, 165, 0),
            'start_time': 0,
            'duration': 500,
            'active': False
        }

        # กำหนดตำแหน่งและขนาดของปุ่ม
        button_width = 120
        button_height = 50
        button_x = 10  # ตำแหน่ง x ของปุ่ม
        button_y_archer = 10  # ตำแหน่ง y ของปุ่ม Archer
        button_y_soldier = button_y_archer + button_height + 10  # ตำแหน่ง y ของปุ่ม Soldier
        button_y_mage = button_y_soldier + button_height + 10  # ตำแหน่ง y ของปุ่ม Mage
        button_y_cavalry = button_y_mage + button_height + 10  # กำหนดตำแหน่ง y ของปุ่ม Cavalry
        
        self.archer_button = pygame.Rect(button_x, button_y_archer, button_width, button_height)  # กำหนดตำแหน่งและขนาดของปุ่ม Archer
        self.soldier_button = pygame.Rect(button_x, button_y_soldier, button_width, button_height)  # กำหนดตำแหน่งและขนาดของปุ่ม Soldier
        self.mage_button = pygame.Rect(button_x, button_y_mage, button_width, button_height)  # กำหนดตำแหน่งและขนาดของปุ่ม Mage
        self.cavalry_button = pygame.Rect(button_x, button_y_cavalry, button_width, button_height)  # ปุ่ม Cavalry
        self.end_turn_button = pygame.Rect(config.SCREEN_WIDTH - button_width - 10, config.SCREEN_HEIGHT - button_height - 10, button_width, button_height)
        self.move_button = pygame.Rect(self.end_turn_button.x, self.end_turn_button.y - button_height - 10, button_width, button_height)
        self.attack_button = pygame.Rect(self.move_button.x, self.move_button.y - button_height - 10, button_width, button_height)
        self.game_over_screen = False  # สถานะการแสดงหน้าจอ Game Over
        self.game_over_background = pygame.image.load("assets/BG/Backgroud.jpg").convert()  # โหลดพื้นหลัง Game Over
        self.font = pygame.font.Font("./assets/Fonts/PixgamerRegular-OVD6A.ttf", 28)

        # สร้างยูนิตสำหรับผู้เล่น 1 และ 2
        self.units = []  # ลิสต์สำหรับเก็บยูนิตทั้งหมด
        self.player_units = []  # ลิสต์สำหรับเก็บยูนิตของผู้เล่น
        self.create_player_units()
        self.generate_capture_points(5)

        self.current_turn = 0
        self.spawn_boss()  # เรียกใช้ฟังก์ชันเพื่อสุ่มเกิดบอส
        self.spawn_monster()  # เรียกใช้ฟังก์ชันเพื่อสุ่มเกิดมอนสเตอร์
        
        self.winner = None  # ประกาศตัวแปร winner ที่นี่
        
    def end_turn(self):
        """จบเทิร์นและรีเซ็ตสถานะ"""
        # เพิ่มเงินให้กับผู้เล่นที่จบเทิร์นจากจุดยึดครอง
        for point in self.capture_points:
            if point.owner is not None:
                self.player_money[point.owner] += point.value  # เพิ่มเงินจากจุดยึดครอง

        # เคลียร์ข้อมูลเงินในเทิร์นถัดไป
        self.income_next_turn[self.current_turn] = 0  # เคลียร์ข้อมูลเงินในเทิร์นถัดไป

        # เพิ่มเงินเพิ่ม 100 หน่วยให้กับผู้เล่นเมื่อจบเทิร์น
        self.player_money[self.current_turn] += 100  # เพิ่มเงิน 100 หน่วย

        # รีเซ็ตการเคลื่อนที่และการโจมตีสำหรับยูนิตทั้งหมดของผู้เล่น
        for unit in self.player_units:
            unit.moved_this_turn = False
            unit.attacked_this_turn = False  # รีเซ็ตสถานะการโจมตี

        # เช็คว่าผู้เล่นมียูนิตเหลืออยู่หรือไม่
        if not any(unit.current_hp > 0 for unit in self.player_units if unit.owner == self.current_turn):
            print(f"Player {self.current_turn + 1} has no units left. Game Over!")
            self.game_over()  # เรียกใช้ฟังก์ชันจบเกม

        # เช็คว่าผู้เล่นฝ่ายตรงข้ามมียูนิตเหลืออยู่หรือไม่
        if not any(unit.current_hp > 0 for unit in self.player_units if unit.owner != self.current_turn):
            print(f"Player {self.current_turn + 1} has defeated Player {2 if self.current_turn == 1 else 1}. Game Over!")
            self.game_over()  # เรียกใช้ฟังก์ชันจบเกม

        # เช็คว่าต้องเพิ่มรอบหรือไม่
        if self.current_turn == 1:  # ถ้าผู้เล่น 2 จบเทิร์น
            self.current_round += 1  # เพิ่มรอบ
            print(f"Round {self.current_round} started.")

            # เรียกใช้ฟังก์ชัน spawn_boss ถ้าเป็นรอบที่ 3
            if self.current_round == 3 and self.boss is None:  # ตรวจสอบว่าบอสยังไม่ถูกสร้าง
                self.spawn_boss()  # เรียกใช้ฟังก์ชันเพื่อสร้างบอส

        # รีเซ็ตสถานะของยูนิตที่เลือก
        if self.selected_unit:
            self.selected_unit.has_actioned = False  # รีเซ็ตสถานะการทำ action ของยูนิต
        self.selected_unit = None  # รีเซ็ตยูนิตที่เลือก
        self.current_action = None  # รีเซ็ต action ปัจจุบัน

        # รีเซ็ตสถานะการสร้าง Tower สำหรับผู้เล่น
        self.tower_created = [False, False]  # รีเซ็ตสถานะการสร้าง Tower สำหรับผู้เล่น 1 และ 2

        # เรียกใช้ฟังก์ชัน move_monsters
        self.move_monsters()

        # เพิ่มจำนวนเทิร์นที่ผ่านไป
        self.turns_since_last_spawn += 1
        self.turns_since_last_boss_move += 1  # เพิ่มจำนวนเทิร์นที่บอสไม่เคลื่อนที่

        # ตรวจสอบว่าเป็นเทิร์นที่ 2 หรือไม่
        if self.turns_since_last_spawn >= 2:
            self.spawn_monster()  # เรียกฟังก์ชันเพื่อสร้างมอนสเตอร์ใหม่
            self.turns_since_last_spawn = 0  # รีเซ็ตจำนวนเทิร์นที่ผ่านไป

        # ตรวจสอบว่าเป็นเทิร์นที่ 2 หรือไม่เพื่อให้บอสเคลื่อนที่
        if self.turns_since_last_boss_move >= 4:
            self.move_boss()  # เรียกฟังก์ชันเพื่อเคลื่อนที่บอส
            self.turns_since_last_boss_move = 0  # รีเซ็ตจำนวนเทิร์นที่บอสไม่เคลื่อนที่

        # เปลี่ยน turn ระหว่างผู้เล่น
        self.current_turn = (self.current_turn + 1) % 2  # เปลี่ยน turn ระหว่างผู้เล่น 0 และ 1
        print(f"Turn changed to player {self.current_turn + 1}.")  # แสดงข้อความเปลี่ยนเทิร์น

        # เช็คว่าผู้เล่นฝ่ายตรงข้ามมียูนิตเหลืออยู่หรือไม่
        if not any(unit.current_hp > 0 for unit in self.player_units if unit.owner != self.current_turn):
            print(f"Player {self.current_turn + 1} has defeated Player {2 if self.current_turn == 1 else 1}. Game Over!")
            self.game_over(self.current_turn)  # ส่ง current_turn ไปยังฟังก์ชัน game_over

        if self.boss and self.boss.is_dead:
            self.boss = None  # รีเซ็ตบอสเมื่อมันตาย
            self.current_round += 1  # เพิ่มรอบเมื่อบอสตาย
            print(f"Round {self.current_round} started. Boss will respawn.")

        # ตรวจสอบว่าต้องสร้างบอสใหม่หรือไม่
        if self.current_round <= self.boss_spawn_rounds:
            self.spawn_boss()  # สร้างบอสใหม่ในรอบถัดไป

    def create_player_units(self):
        """สร้างยูนิตสำหรับผู้เล่น 1 และ 2"""
        try:
            # ข้อมูลยูนิตสำหรับผู้เล่น
            player_data = [
                {
                    "sprite": "assets/sprites/unit1_idle_blue.png",
                    "archer_sprite": "assets/sprites/unit2_idle_blue.png",
                    "owner": 0,
                    "unit_name": "Player 1",
                    "position": (5, 5)  # ตำแหน่งสำหรับ Player 1
                },
                {
                    "sprite": "assets/sprites/unit1_idle_red.png",
                    "archer_sprite": "assets/sprites/unit2_idle_red.png",
                    "owner": 1,
                    "unit_name": "Player 2",
                    "position": (25, 25)  # ตำแหน่งสำหรับ Player 2
                }
            ]

            # สร้างยูนิตสำหรับผู้เล่น 1 และ 2
            for player in player_data:
                unit_idle_spritesheet = pygame.image.load(player["sprite"]).convert_alpha()
                unit_idle_frames = self.load_idle_frames(unit_idle_spritesheet)
                soldier_unit = Unit(unit_idle_frames=unit_idle_frames, unit_type=UnitType.SOLDIER, 
                                x=player["position"][0], y=player["position"][1], 
                                owner=player["owner"], name=f"{player['unit_name']} Soldier")

                unit_idle_spritesheet_archer = pygame.image.load(player["archer_sprite"]).convert_alpha()
                unit_idle_frames_archer = self.load_idle_frames(unit_idle_spritesheet_archer)
                archer_unit = Unit(unit_idle_frames=unit_idle_frames_archer, unit_type=UnitType.ARCHER, 
                               x=player["position"][0] + 1, y=player["position"][1], 
                               owner=player["owner"], name=f"{player['unit_name']} Archer")

                self.player_units.extend([soldier_unit, archer_unit])

            for unit in self.player_units:
                self.iso_map.add_object(unit)

        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการสร้างยูนิต: {e}")

    def generate_capture_points(self, count):
        """สร้างจุดยึดครองเริ่มต้น"""
        valid_positions = []
        min_distance = 4  # กำหนดระยะห่างขั้นต่ำระหว่างจุดยึดครอง
        unit_min_distance = 5  # กำหนดระยะห่างขั้นต่ำระหว่างจุดยึดครองกับยูนิต

        for x in range(self.iso_map.tmx_data.width):
            for y in range(self.iso_map.tmx_data.height):
                if self.path_finder.is_walkable((x, y)):
                    # ตรวจสอบว่าตำแหน่งนี้ห่างจากจุดยึดครองอื่น ๆ
                    if all(self.calculate_distance(x, y, cp.x, cp.y) >= min_distance for cp in self.capture_points):
                        # ตรวจสอบว่าตำแหน่งนี้ห่างจากยูนิตของผู้เล่น 1
                        if all(self.calculate_distance(x, y, unit.x, unit.y) >= unit_min_distance for unit in self.player_units if unit.owner == 0):
                            # ตรวจสอบว่าตำแหน่งนี้ห่างจากยูนิตของผู้เล่น 2
                            if all(self.calculate_distance(x, y, unit.x, unit.y) >= unit_min_distance for unit in self.player_units if unit.owner == 1):
                                valid_positions.append((x, y))

        if valid_positions:
            positions = random.sample(valid_positions, min(count, len(valid_positions)))
            for x, y in positions:
                value = random.randint(50, 100)  # สุ่มค่าเงินที่จะได้รับต่อเทิร์น
                self.capture_points.append(CapturePoint(x, y))

    def handle_mouse_click(self, mouse_pos, tower):
        """ตรวจสอบการคลิกที่ปุ่มสร้างยูนิต"""
        if tower:  # ตรวจสอบว่ามี Tower ที่เลือกอยู่
            # ตรวจสอบการคลิกปุ่มสร้าง Archer
            if self.archer_button.collidepoint(mouse_pos):
                self.create_unit(tower, UnitType.ARCHER)
                print("สร้าง Archer ที่ Tower")
            # ตรวจสอบการคลิกปุ่มสร้าง Soldier
            elif self.soldier_button.collidepoint(mouse_pos):
                self.create_unit(tower, UnitType.SOLDIER)
                print("สร้าง Soldier ที่ Tower")

    def load_idle_frames(self, spritesheet):
        frames = []
        # สมมุติว่า spritesheet มีการแบ่งเฟรมเป็นแถวและคอลัมน์
        frame_width = 32  # ความกว้างของแต่ละเฟรม
        frame_height = 32  # ความสูงของแต่ละเฟรม
        for i in range(0, spritesheet.get_height(), frame_height):
            for j in range(0, spritesheet.get_width(), frame_width):
                frame = spritesheet.subsurface((j, i, frame_width, frame_height))
                frames.append(frame)
        return frames

    def draw_info(self, screen, x, y):
        """วาดข้อมูล Tower บนหน้าจอ"""
        font = pygame.font.Font("assets/Fonts/PixgamerRegular-OVD6A.ttf", 20)
    
        # สมมุติว่า Tower มีชื่อและสุขภาพ
        tower_name_surface = font.render(f"Tower Name: {self.selected_tower.player_id}", True, (0, 0, 0))
        screen.blit(tower_name_surface, (x, y + 50))

        health_surface = font.render(f"Health: {self.selected_tower.health}", True, (0, 0, 0))
        screen.blit(health_surface, (x, y + 80 + 50))

        attack_power_surface = font.render(f"Attack Power: {self.selected_tower.attack_power}", True, (0, 0, 0))
        screen.blit(attack_power_surface, (x, y + 110 + 50))

        attack_range_surface = font.render(f"Attack Range: {self.selected_tower.attack_range}", True, (0, 0, 0))
        screen.blit(attack_range_surface, (x, y + 140 + 50))

    def draw_round_display(self):
        """วาดข้อความแสดงรอบของเกมบนหน้าจอ"""
        font = pygame.font.Font("assets/Fonts/PixgamerRegular-OVD6A.ttf", 36)  # ใช้ฟอนต์ที่ต้องการ
        round_text = f"Round: {self.current_round}"  # ข้อความแสดงรอบ
        text_surface = font.render(round_text, True, (0, 0, 0))  # วาดข้อความด้วยสีขาว
        text_rect = text_surface.get_rect(topright=(self.config.SCREEN_WIDTH - 10, 50))  # จัดตำแหน่งที่มุมขวาบน
        self.screen.blit(text_surface, text_rect)  # วาดข้อความลงบนหน้าจอ

    def draw_end_turn_button(self):
        """วาดปุ่ม 'End Turn' บนหน้าจอ"""
        pygame.draw.rect(self.screen, (255, 0, 0), self.end_turn_button)  # วาดปุ่มสีแดง
        text_surface = self.font.render("End Turn", True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=self.end_turn_button.center)
        self.screen.blit(text_surface, text_rect)

    def draw_create_unit_buttons(self, tower):
        """วาดปุ่ม 'Create Archer', 'Create Soldier' และ 'Create Mage' ข้างๆ Tower ที่ถูกคลิก""" 
        iso_x, iso_y = self.iso_map.cart_to_iso(tower.x, tower.y)
        screen_x = iso_x * self.camera.zoom + self.config.OFFSET_X + self.camera.position.x
        screen_y = iso_y * self.camera.zoom + self.config.OFFSET_Y + self.camera.position.y - (self.config.TILE_HEIGHT * self.camera.zoom)

        button_width = 100 
        button_height = 30 

        # ปุ่มสร้าง Archer
        archer_button_x = screen_x + 10  # ปรับตำแหน่ง X ให้อยู่ข้าง Tower 
        archer_button_y = screen_y - button_height - 10  # ปรับตำแหน่ง Y ให้อยู่เหนือ Tower 

        self.archer_button = pygame.Rect(archer_button_x, archer_button_y, button_width, button_height) 
        pygame.draw.rect(self.screen, (0, 255, 0), self.archer_button)  # วาดปุ่มสีเขียว 
        font = pygame.font.Font("assets/Fonts/PixgamerRegular-OVD6A.ttf", 20) 
        text_surface = font.render("Create Archer", True, (0, 0, 0)) 
        text_rect = text_surface.get_rect(center=self.archer_button.center) 
        self.screen.blit(text_surface, text_rect) 

        # ปุ่มสร้าง Soldier
        soldier_button_x = screen_x + 10  # ปรับตำแหน่ง X ให้อยู่ข้าง Tower 
        soldier_button_y = archer_button_y - button_height - 10  # ปรับตำแหน่ง Y ให้อยู่เหนือ Archer button 

        self.soldier_button = pygame.Rect(soldier_button_x, soldier_button_y, button_width, button_height) 
        pygame.draw.rect(self.screen, (0, 0, 255), self.soldier_button)  # วาดปุ่มสีน้ำเงิน 
        text_surface = font.render("Create Soldier", True, (0, 0, 0)) 
        text_rect = text_surface.get_rect(center=self.soldier_button.center) 
        self.screen.blit(text_surface, text_rect) 

        # ปุ่มสร้าง Mage
        mage_button_x = screen_x + 10  # ปรับตำแหน่ง X ให้อยู่ข้าง Tower 
        mage_button_y = soldier_button_y - button_height - 10  # ปรับตำแหน่ง Y ให้อยู่เหนือ Soldier button 

        self.mage_button = pygame.Rect(mage_button_x, mage_button_y, button_width, button_height) 
        pygame.draw.rect(self.screen, (255, 0, 255), self.mage_button)  # วาดปุ่มสีม่วง 
        text_surface = font.render("Create Mage", True, (0, 0, 0)) 
        text_rect = text_surface.get_rect(center=self.mage_button.center) 
        self.screen.blit(text_surface, text_rect)

        # ปุ่มสร้าง Cavalry
        cavalry_button_x = screen_x + 10  # ปรับตำแหน่ง X ให้อยู่ข้าง Tower 
        cavalry_button_y = mage_button_y - button_height - 10  # ปรับตำแหน่ง Y ให้อยู่เหนือ Mage button 

        self.cavalry_button = pygame.Rect(cavalry_button_x, cavalry_button_y, button_width, button_height) 
        pygame.draw.rect(self.screen, (255, 165, 0), self.cavalry_button)  # วาดปุ่มสีส้ม 
        text_surface = font.render("Create Cavalry", True, (0, 0, 0)) 
        text_rect = text_surface.get_rect(center=self.cavalry_button.center) 
        self.screen.blit(text_surface, text_rect)

    def draw_money_display(self):
        """แสดงจำนวนเงินของผู้เล่นที่มีเทิร์นบนหน้าจอ"""
        current_player_index = self.current_turn  # ดึงหมายเลขผู้เล่นที่มีเทิร์น
        # เปลี่ยนขนาดฟอนต์ให้ใหญ่ขึ้น
        large_font = pygame.font.Font("assets/Fonts/PixgamerRegular-OVD6A.ttf", 32)  # เปลี่ยนขนาดฟอนต์เป็น 36
        money_text = large_font.render(f"Player {current_player_index + 1} Money: ${self.player_money[current_player_index]}", 
                                   True, (205, 28, 24))  # เปลี่ยนสีตัวอักษรเป็นสีดำ
    
        # ปรับตำแหน่ง Y ของข้อความให้สูงขึ้นจากตำแหน่งปุ่ม "End Turn"
        money_text_y = self.end_turn_button.top - 10  # 10 พิกเซลด้านบนของปุ่ม
        self.screen.blit(money_text, (10, money_text_y))  # แสดงเงินของผู้เล่นที่มีเทิร์น

        # แสดงจำนวนจุดที่ยึดได้
        captured_points = sum(1 for point in self.capture_points if point.owner is not None)
        points_text = large_font.render(f"Captured Points: {captured_points}/{len(self.capture_points)}", 
                                    True, (205, 28, 24))  # เปลี่ยนสีตัวอักษรเป็นสีดำ
    
        # ปรับตำแหน่ง Y ของข้อความจำนวนจุดที่ยึดได้ให้สูงขึ้นจากปุ่ม "End Turn"
        points_text_y = money_text_y - 30  # 30 พิกเซลด้านบนของข้อความเงิน
        self.screen.blit(points_text, (10, points_text_y))  # แสดงจำนวนจุดที่ยึดได้

    def update_capture_points(self):
        """อัพเดทจุดยึดครอง"""
        current_time = pygame.time.get_ticks()
        for point in self.capture_points:
            point.update(self.iso_map.objects, current_time)

            # เช็คว่ามีเจ้าของ
            if point.owner is not None:
                # อาจจะมีการจัดการอื่น ๆ ที่เกี่ยวข้องกับเจ้าของจุดยึดครอง
                pass  # คุณสามารถเพิ่มโค้ดเพิ่มเติมได้ที่นี่ถ้าต้องการ

    def get_walkable_tiles(self, unit, max_distance=5):
        """หาช่องที่สามารถเดินไปได้ในระยะที่กำหนด"""
        walkable = []
        start_pos = (int(unit.x), int(unit.y))
        
        # ใช้ BFS เพื่อหาช่องที่เดินได้
        visited = {start_pos}
        queue = [(start_pos, 0)]  # (position, distance)
        
        while queue:
            pos, dist = queue.pop(0)
            if dist <= max_distance:
                walkable.append(pos)
                
                # ตรวจสอบช่องรอบๆ
                for dx, dy in self.path_finder.directions:
                    new_x, new_y = pos[0] + dx, pos[1] + dy
                    new_pos = (new_x, new_y)
                    
                    if (new_pos not in visited and 
                        0 <= new_x < self.iso_map.tmx_data.width and 
                        0 <= new_y < self.iso_map.tmx_data.height and
                        self.path_finder.is_walkable(new_pos)):
                        
                        visited.add(new_pos)
                        queue.append((new_pos, dist + 1))
        
        return walkable

    def draw_move_button(self):
        """วาดปุ่ม 'Move' บนหน้าจอ"""
        current_time = pygame.time.get_ticks()
        anim = self.move_button_animation

        if anim['active']:
            # คำนวณเวลาที่ผ่านไป
            elapsed_time = current_time - anim['start_time']
        
            # คำนวณ scale และสีแบบ sine wave
            if elapsed_time < anim['duration']:
                # Animation scale
                progress = elapsed_time / anim['duration']
                scale = 1 + math.sin(progress * math.pi * 2) * 0.2

                # Animation สี
                r = int(anim['color'][0] + math.sin(progress * math.pi * 2) * 100)
                g = int(anim['color'][1] + math.sin(progress * math.pi * 2) * 100)
                b = int(anim['color'][2] + math.sin(progress * math.pi * 2) * 100)
                color = (max(0, min(r, 255)), max(0, min(g, 255)), max(0, min(b, 255)))
            else:
                # หยุด animation
                anim['active'] = False
                scale = 1
                color = anim['color']
        else:
            scale = 1
            color = anim['color']

        # คำนวณขนาดปุ่มที่จะวาด
        scaled_width = int(self.move_button.width * scale)
        scaled_height = int(self.move_button.height * scale)
    
        # คำนวณตำแหน่งใหม่เพื่อให้ปุ่มอยู่กึ่งกลาง
        scaled_x = self.move_button.x - (scaled_width - self.move_button.width) // 2
        scaled_y = self.move_button.y - (scaled_height - self.move_button.height) // 2
    
        scaled_button = pygame.Rect(scaled_x, scaled_y, scaled_width, scaled_height)
    
        # วาดปุ่ม
        pygame.draw.rect(self.screen, color, scaled_button)
    
        # วาดข้อความ
        text_surface = self.font.render("Move", True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=scaled_button.center)
        self.screen.blit(text_surface, text_rect)

    def draw_attack_button(self):
        """วาดปุ่ม 'Attack' บนหน้าจอ"""
        current_time = pygame.time.get_ticks()
        anim = self.attack_button_animation

        if anim['active']:
            # คำนวณเวลาที่ผ่านไป
            elapsed_time = current_time - anim['start_time']
        
            # คำนวณ scale และสีแบบ sine wave
            if elapsed_time < anim['duration']:
                # Animation scale
                progress = elapsed_time / anim['duration']
                scale = 1 + math.sin(progress * math.pi * 2) * 0.2
            
                # Animation สี
                r = int(anim['color'][0] + math.sin(progress * math.pi * 2) * 100)
                g = int(anim['color'][1] + math.sin(progress * math.pi * 2) * 100)
                b = int(anim['color'][2] + math.sin(progress * math.pi * 2) * 100)
                color = (max(0, min(r, 255)), max(0, min(g, 255)), max(0, min(b, 255)))
            else:
                # หยุด animation
                anim['active'] = False
                scale = 1
                color = anim['color']
        else:
            scale = 1
            color = anim['color']

        # คำนวณขนาดปุ่มที่จะวาด
        scaled_width = int(self.attack_button.width * scale)
        scaled_height = int(self.attack_button.height * scale)
    
        # คำนวณตำแหน่งใหม่เพื่อให้ปุ่มอยู่กึ่งกลาง
        scaled_x = self.attack_button.x - (scaled_width - self.attack_button.width) // 2
        scaled_y = self.attack_button.y - (scaled_height - self.attack_button.height) // 2
    
        scaled_button = pygame.Rect(scaled_x, scaled_y, scaled_width, scaled_height)
    
        # วาดปุ่ม
        pygame.draw.rect(self.screen, color, scaled_button)
    
        # วาดข้อความ
        text_surface = self.font.render("Attack", True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=scaled_button.center)
        self.screen.blit(text_surface, text_rect)
    
    def move_boss(self):
        """ฟังก์ชันเพื่อเคลื่อนที่บอส"""
        if self.boss and not self.boss.is_dead:  # ตรวจสอบว่าบอสยังมีชีวิตอยู่
            # สุ่มเลือกทิศทางการเคลื่อนที่
            direction = random.choice(self.path_finder.directions)  # เลือกทิศทางแบบสุ่ม

            new_x = self.boss.x + direction[0]  # อัปเดตตำแหน่ง X
            new_y = self.boss.y + direction[1]  # อัปเดตตำแหน่ง Y

            # ตรวจสอบว่าตำแหน่งใหม่อยู่ในขอบเขตของแผนที่
            if (0 <= new_x < self.iso_map.tmx_data.width) and (0 <= new_y < self.iso_map.tmx_data.height):
                # ตรวจสอบว่าตำแหน่งใหม่เดินได้หรือไม่
                if self.path_finder.is_walkable((new_x, new_y)):
                    # อัปเดตตำแหน่งบอส
                    self.boss.x = new_x
                    self.boss.y = new_y
                    print(f"Boss moved to position: ({new_x}, {new_y})")  # แสดงข้อความยืนยันการเคลื่อนที่

    def move_monsters(self):
        for monster in self.monsters:
            if not monster.is_dead:  # ตรวจสอบว่ามอนสเตอร์ยังมีชีวิตอยู่
                # สุ่มเลือกทิศทางการเคลื่อนที่
                direction = random.choice(self.path_finder.directions)  # เลือกทิศทางแบบสุ่ม

                new_x = monster.x + direction[0]  # อัปเดตตำแหน่ง X
                new_y = monster.y + direction[1]  # อัปเดตตำแหน่ง Y

                # ตรวจสอบว่าตำแหน่งใหม่อยู่ในขอบเขตของแผนที่
                if (0 <= new_x < self.iso_map.tmx_data.width) and (0 <= new_y < self.iso_map.tmx_data.height):
                    # ตรวจสอบว่าตำแหน่งใหม่เดินได้หรือไม่
                    if self.path_finder.is_walkable((new_x, new_y)):
                        # อัปเดตตำแหน่งมอนสเตอร์
                        monster.x = new_x
                        monster.y = new_y
                        print(f"{monster.name} moved to position: ({new_x}, {new_y})")  # แสดงข้อความยืนยันการเคลื่อนที่
                else:
                    print(f"{monster.name} cannot move to position: ({new_x}, {new_y}) - out of bounds")  # แสดงข้อความเมื่อมอนสเตอร์ไม่สามารถเคลื่อนที่

    def spawn_monster(self):
        if self.monster_count < 5:  # ตรวจสอบว่าจำนวนมอนสเตอร์น้อยกว่า 5 หรือไม่
            valid_positions = []

            # สุ่มตำแหน่งที่อยู่ภายในขอบของแผนที่
            for x in range(1, self.iso_map.tmx_data.width - 1):  # เริ่มจาก 1 ถึง width - 1
                for y in range(1, self.iso_map.tmx_data.height - 1):  # เริ่มจาก 1 ถึง height - 1
                    if self.path_finder.is_walkable((x, y)) and not self.is_near_units(x, y):
                        # ตรวจสอบระยะห่างจากมอนสเตอร์ที่มีอยู่แล้ว
                        if all(self.calculate_distance(x, y, monster.x, monster.y) >= 3 for monster in self.monsters):
                            # ตรวจสอบระยะห่างจากยูนิตของผู้เล่น
                            if all(self.calculate_distance(x, y, unit.x, unit.y) >= 5 for unit in self.player_units):
                                valid_positions.append((x, y))

            if valid_positions:
                x, y = random.choice(valid_positions)  # สุ่มตำแหน่งจาก valid_positions
                monster = Monster(x, y, name="Monster")  # สร้างมอนสเตอร์ที่ตำแหน่งที่สุ่มได้
                self.monsters.append(monster)  # เพิ่มมอนสเตอร์ลงในรายการ
                self.monster_count += 1  # เพิ่มจำนวนมอนสเตอร์
                print(f"Monster spawned at position: ({x}, {y})")  # แสดงพิกัดที่มอนสเตอร์เกิด

    def remove_monster(self, monster):
        if monster in self.monsters:
            self.monsters.remove(monster)  # ลบมอนสเตอร์จากรายการ
            self.monster_count -= 1  # ลดจำนวนมอนสเตอร์
            print(f"{monster.name} has been removed.")
    
    def draw_message(self, message, duration=500):
        """วาดข้อความลงบนหน้าจอ"""
        font = pygame.font.Font("assets/Fonts/PixgamerRegular-OVD6A.ttf", 48)  # ใช้ฟอนต์ที่ต้องการ
        text_surface = font.render(message, True, (255, 0, 0))  # สีแดง
        text_rect = text_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 30))  # จัดตำแหน่งกลาง
        self.screen.blit(text_surface, text_rect)  # วาดข้อความลงบนหน้าจอ
        pygame.display.flip()  # อัปเดตหน้าจอ
        pygame.time.delay(duration)  # รอเป็นระยะเวลาที่กำหนด

    def spawn_boss(self):
        # ตรวจสอบว่าบอสยังไม่ถูกสร้างและรอบปัจจุบันเป็นรอบที่ 3 หรือรอบที่ 5, 10, 15, ...
        if self.boss is None and (self.current_round == 3 or (self.current_round > 3 and (self.current_round - 3) % 5 == 0)):
            valid_positions = []

            # สุ่มตำแหน่งที่อยู่ภายในขอบของแผนที่
            for x in range(1, self.iso_map.tmx_data.width - 1):  # เริ่มจาก 1 ถึง width - 1
                for y in range(1, self.iso_map.tmx_data.height - 1):  # เริ่มจาก 1 ถึง height - 1
                    if self.path_finder.is_walkable((x, y)) and not self.is_near_units(x, y):
                        # ตรวจสอบระยะห่างจากยูนิตของผู้เล่น
                        if all(self.calculate_distance(x, y, unit.x, unit.y) >= 5 for unit in self.player_units):
                            valid_positions.append((x, y))

            if valid_positions:
                x, y = random.choice(valid_positions)  # สุ่มตำแหน่งจาก valid_positions
                self.boss = Boss(x, y)  # สร้างบอสที่ตำแหน่งที่สุ่มได้
                self.boss_spawn_sound.play()
                print(f"Among US!! spawned at position: ({x}, {y})")  # แสดงพิกัดที่บอสเกิด
                self.draw_message("Among US!! has spawned!", duration=500)  # แสดงข้อความเมื่อบอสเกิด

    def is_near_units(self, x, y, distance=2):
        """ตรวจสอบว่ามียูนิตใกล้ตำแหน่งที่กำหนดหรือไม่"""
        for unit in self.player_units:
            if self.calculate_distance(unit.x, unit.y, x, y) < distance:
                return True
        return False
    
    def calculate_distance(self, x1, y1, x2, y2):
        """คำนวณระยะห่างระหว่างสองจุดในพิกัด 2D"""
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    
    def draw_walkable_tiles(self):
        """วาด highlight ช่องที่สามารถเดินได้แบบโปร่งแสง"""
        if self.selected_unit and self.walkable_tiles:
            # สร้างเอฟเฟกต์กะพริบโดยใช้ฟังก์ชัน sine
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.005)) * 155 + 100
            highlight_color = (255, 255, 0, int(pulse))  # สีเหลืองที่มีความโปร่งใสเปลี่ยนแปลง

            for tile_x, tile_y in self.walkable_tiles:
                # ตรวจสอบว่าช่องนี้อยู่ในระยะการเดินของยูนิต
                distance = self.calculate_distance(self.selected_unit.x, self.selected_unit.y, tile_x, tile_y)
                if distance <= self.selected_unit.move_range:  # ตรวจสอบระยะการเดิน
                    iso_x, iso_y = self.iso_map.cart_to_iso(tile_x, tile_y)
                    screen_x = iso_x * self.camera.zoom + self.config.OFFSET_X + self.camera.position.x
                    screen_y = iso_y * self.camera.zoom + self.config.OFFSET_Y + self.camera.position.y

                    # กำหนดจุดสำหรับวาดกรอบรูปสี่เหลี่ยมข้าวหลามตัด
                    points = [
                    (screen_x, screen_y + (self.config.TILE_HEIGHT * self.camera.zoom) // 2),
                    (screen_x + (self.config.TILE_WIDTH * self.camera.zoom) //  2, screen_y),
                    (screen_x + (self.config.TILE_WIDTH * self.camera.zoom), 
                     screen_y + (self.config.TILE_HEIGHT * self.camera.zoom) // 2),
                    (screen_x + (self.config.TILE_WIDTH * self.camera.zoom) // 2, 
                     screen_y + (self.config.TILE_HEIGHT * self.camera.zoom))
                    ]

                    # สร้าง surface แยกสำหรับการวาดกรอบที่มีความโปร่งใส
                    highlight_surface = pygame.Surface((self.config.TILE_WIDTH * self.camera.zoom, 
                                                    self.config.TILE_HEIGHT * self.camera.zoom), 
                                                   pygame.SRCALPHA)

                    # วาดกรอบบน highlight_surface
                    pygame.draw.lines(highlight_surface, highlight_color, True, 
                                  [(p[0]-screen_x, p[1]-screen_y) for p in points], 2)

                    # วาด highlight_surface ลงบนหน้าจอหลัก
                    self.screen.blit(highlight_surface, (screen_x, screen_y))

    def create_unit(self, tower, unit_type):
        # ตรวจสอบว่าทาวเวอร์ที่ส่งเข้ามามีอยู่จริง
        if tower is None:
            print("ไม่สามารถสร้างยูนิตได้: ทาวเวอร์ไม่ถูกเลือก.")
            return False

        # รับข้อมูลเจ้าของของทาวเวอร์
        player_index = tower.owner

        # ดึงค่าใช้จ่ายสำหรับยูนิตประเภทที่เลือก
        unit_cost = UnitType.get_cost(unit_type)

        # ตรวจสอบว่าผู้เล่นมีเงินเพียงพอในการสร้างยูนิตหรือไม่
        if self.player_money[player_index] < unit_cost:
            print(f"ผู้เล่น {player_index + 1} ไม่มีเงินเพียงพอในการสร้างยูนิตประเภท {unit_type}. ต้องการ {unit_cost}.")
            return False

        # คำนวณตำแหน่งใหม่ของยูนิตที่จะอยู่ข้างๆ ทาวเวอร์
        x = tower.x +  1   # ปรับตำแหน่ง X ให้ยูนิตอยู่ทางขวาของ Tower
        y = tower.y        # ปรับตำแหน่ง Y ให้อยู่ที่เดียวกับ Tower

        # กำหนดสีหรือสไปรต์ตามผู้เล่น
        if unit_type == UnitType.SOLDIER:
            sprite_path = "assets/sprites/unit1_idle_blue.png" if player_index == 0 else "assets/sprites/unit1_idle_red.png"
        elif unit_type == UnitType.ARCHER:
            sprite_path = "assets/sprites/unit2_idle_blue.png" if player_index == 0 else "assets/sprites/unit2_idle_red.png"
        elif unit_type == UnitType.MAGE:  # เพิ่มเงื่อนไขสำหรับ Mage
            sprite_path = "assets/sprites/mage_blue.png" if player_index == 0 else "assets/sprites/mage_red.png"
        elif unit_type == UnitType.CAVALRY:  # เพิ่มเงื่อนไขสำหรับ Cavalry
            sprite_path = "assets/sprites/House-blue.png" if player_index == 0 else "assets/sprites/House-red.png"

        # โหลดเฟรม idle สำหรับยูนิตที่ถูกสร้าง
        unit_idle_spritesheet = pygame.image.load(sprite_path).convert_alpha()
        unit_idle_frames = self.load_idle_frames(unit_idle_spritesheet)

        # สร้างยูนิตใหม่ที่ตำแหน่ง (x, y) ที่คำนวณไว้
        new_unit = Unit(unit_idle_frames, unit_type, x, y, owner=player_index)  # ส่ง owner ให้กับ constructor

        # เพิ่มยูนิตใหม่ลงในลิสต์ของผู้เล่น
        self.player_units.append(new_unit)  # เพิ่มยูนิตใหม่ลงในลิสต์ของผู้เล่น
        self.iso_map.add_object(new_unit)  # เพิ่มยูนิตลงในแผนที่

        # หักค่าใช้จ่ายจากเงินของผู้เล่น
        self.player_money[player_index] -= unit_cost

        print(f"ยูนิตถูกสร้างอยู่ที่ตำแหน่ง: ({x}, {y}) สำหรับผู้เล่น {player_index + 1}. ค่าใช้จ่าย: {unit_cost}")  # แสดงข้อมูลเจ้าของยูนิต
        return True

    def is_tower_at_position(self, x, y):
        """ตรวจสอบว่ามี Tower อยู่ที่ตำแหน่งที่กำหนดหรือไม่"""
        for tower in self.towers:
            if tower.x == x and tower.y == y:
                return True
        return False

    def create_tower(self, x, y):
        """สร้าง Tower ที่ตำแหน่งที่กำหนด"""
        player_index = self.current_turn  # ใช้ current_turn เพื่อระบุผู้เล่น

        if self.tower_created[player_index]:
            print(f"Player {player_index + 1} can only create one tower per turn.")
            return False  # ไม่อนุญาตให้สร้าง Tower อีก

        # ตรวจสอบว่าผู้เล่นมีเงินเพียงพอหรือไม่
        if self.player_money[player_index] < 100:
            print(f"Player {player_index + 1} does not have enough money to create a tower.")
            return False  # ไม่สามารถสร้าง Tower ได้เนื่องจากเงินไม่เพียงพอ

        # ตรวจสอบว่าตำแหน่งนั้นสามารถสร้าง Tower ได้หรือไม่
        if self.path_finder.is_walkable((x, y)):  # ตรวจสอบว่า Tile เดินได้
            # ตรวจสอบระยะการเคลื่อนที่ของ Unit
            distance = self.calculate_distance(self.selected_unit.x, self.selected_unit.y, x, y)
            if distance <= self.selected_unit.move_range:  # ตรวจสอบว่าตำแหน่งอยู่ในระยะ
                if not self.is_tower_at_position(x, y): 
                    player_id = player_index   # กำหนด player_id จาก current_turn (1 หรือ 2)

                    # โหลดภาพสำหรับ Tower
                    if player_id == 0:
                        tower_image = pygame.image.load("assets/sprites/building-blue.png").convert_alpha()
                    else:
                        tower_image = pygame.image.load("assets/sprites/building-red.png").convert_alpha()

                    new_tower = Tower(x, y, player_id, tower_image)  # สร้าง Tower ใหม่
                    self.towers.append(new_tower)  # เพิ่ม Tower ลงในรายการ Tower
                    self.tower_created[player_index] = True  # ตั้งค่าสถานะว่าผู้เล่นได้สร้าง Tower แล้ว
                    self.player_money[player_index] -= 100  # หักเงิน 100 บาทจากผู้เล่น
                    print(f"Tower created at position: ({x}, {y}) for Player {player_id}. Cost: 100.")  # แสดงข้อความยืนยันการสร้าง Tower
                    print(f"Tower owner is Player {player_index + 1}.")  # Debug print
                    return True  # คืนค่า True หากสร้าง Tower สำเร็จ
                else:
                    print("Cannot create tower: There is already a tower at this position.")
            else:
                print("Cannot create tower: Tile is out of unit's range.")
        else:
            print("Cannot create tower at this position.")
        return False  # คืนค่า False หากไม่สามารถสร้าง Tower ได้

    def draw_create_tower_button(self, attack_button_x, attack_button_y):
        """วาดปุ่ม 'Create Tower' ด้านบนปุ่ม Attack"""
        button_width = 100
        button_height = 30
        button_x = attack_button_x  # ใช้ตำแหน่ง X ของปุ่ม Attack
        button_y = attack_button_y - button_height - 10  # ปรับตำแหน่ง Y ให้อยู่เหนือปุ่ม Attack

        self.create_tower_button = pygame.Rect(button_x, button_y, button_width, button_height)
        pygame.draw.rect(self.screen, (0, 0, 255), self.create_tower_button)  # วาดปุ่มสีฟ้า
        font = pygame.font.Font("assets/Fonts/PixgamerRegular-OVD6A.ttf", 20)
        text_surface = font.render("Create Tower", True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.create_tower_button.center)
        self.screen.blit(text_surface, text_rect)

    def draw_map(self):
        """วาดแผนที่ไอโซเมตริกพร้อมการชดเชยจากกล้องและการซูม"""
        # วาดแผนที่พื้นฐาน
        for layer in self.iso_map.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    tile = self.iso_map.tmx_data.get_tile_image_by_gid(gid)
                    if tile:
                        # ปรับขนาดกระเบื้องตามระดับการซูมของกล้อง
                        if self.camera.zoom != 1.0:
                            new_width = int(tile.get_width() * self.camera.zoom)
                            new_height = int(tile.get_height() * self.camera.zoom)
                            tile = pygame.transform.scale(tile, (new_width, new_height))
                        
                        iso_x, iso_y = self.iso_map.cart_to_iso(x, y)
                        screen_x = iso_x * self.camera.zoom + self.config.OFFSET_X + self.camera.position.x
                        screen_y = iso_y * self.camera.zoom + self.config.OFFSET_Y + self.camera.position.y
                        self.screen.blit(tile, (screen_x, screen_y))
                        
                       
        
        # วาด highlight ช่องที่เดินได้
        self.draw_walkable_tiles()  

        for tower in self.towers:
            tower.draw(self.screen, self.camera, self.config)  # วาด Tower

        # วาด objects
        for obj in self.iso_map.objects:
            obj.draw(self.screen, self.iso_map, self.camera, self.config)
        # วาดจุดยึดครอง
        for point in self.capture_points:
            point.draw(self.screen, self.iso_map, self.camera, self.config)
        
        for obj in self.iso_map.objects:
            if isinstance(obj, Unit):  # ตรวจสอบว่า obj เป็น Unit หรือไม่
                obj.draw(self.screen, self.iso_map, self.camera, self.config)
        
        for unit in self.units :  # ใช้ self.units หรือ self.iso_map.objects
            unit.draw(self.screen, self.iso_map, self.camera, self.config)
        
        # ตรวจสอบว่าเทิร์นของผู้เล่นตรงกับยูนิตที่ถูกเลือก
        if self.selected_unit and self.selected_unit.clicked_this_turn and self.selected_unit.owner == self.current_turn:
            self.selected_unit.draw_attackable_targets(self.screen, self.iso_map, self.camera, self.config)

        # วาด highlight unit ที่เลือก
        if self.selected_unit:
            self.draw_unit_highlight(self.selected_unit)

        # วาด highlight กระเบื้องที่ถูกเลือก
        if self.iso_map.selected_tile:
            self.draw_tile_highlight(*self.iso_map.selected_tile)

        # วาดบอสถ้ามี
        if self.boss:
            self.boss.draw(self.screen, self.camera, self.config)
        
        # วาดมอนสเตอร์ทั้งหมด
        for monster in self.monsters:
            monster.draw(self.screen, self.camera, self.config)  # วาดมอนสเตอร์

    def draw_unit_highlight(self, unit):
        """วาดเส้นไฮไลท์รอบ unit ที่ถูกเลือก"""
        
        iso_x, iso_y = self.iso_map.cart_to_iso(unit.x, unit.y)
        screen_x = iso_x * self.camera.zoom + self.config.OFFSET_X + self.camera.position.x
        screen_y = iso_y * self.camera.zoom + self.config.OFFSET_Y + self.camera.position.y - (self.config.TILE_HEIGHT * self.camera.zoom)

        # วาดปุ่มสร้าง Tower
        self.draw_create_tower_button(screen_x, screen_y)

    def draw_turn_display(self):
        """วาดข้อความแสดงเทิร์นของผู้เล่นบนหน้าจอ"""
        font = pygame.font.Font("assets/Fonts/PixgamerRegular-OVD6A.ttf", 36)  # ใช้ฟอนต์ที่ต้องการและขนาด 36
        turn_text = f"Player {self.current_turn + 1}'s Turn"  # ข้อความแสดงเทิร์น
        text_surface = font.render(turn_text, True, (0, 0, 0))  # วาดข้อความด้วยสีขาว
        text_rect = text_surface.get_rect(topright=(self.config.SCREEN_WIDTH - 10, 10))  # จัดตำแหน่งที่มุมขวาบน
        self.screen.blit(text_surface, text_rect)  # วาดข้อความลงบนหน้าจอ

    def draw_tile_highlight(self, tile_x: int, tile_y: int):
        """วาดเส้นไฮไลท์สีเหลืองรอบกระเบื้องที่ถูกเลือก"""
        iso_x, iso_y = self.iso_map.cart_to_iso(tile_x, tile_y)
        screen_x = iso_x * self.camera.zoom + self.config.OFFSET_X + self.camera.position.x
        screen_y = iso_y * self.camera.zoom + self.config.OFFSET_Y + self.camera.position.y
        
        # กำหนดมุมของกระเบื้องให้เป็นรูปทรงเพชร
        tile_width = self.config.TILE_WIDTH * self.camera.zoom
        tile_height = self.config.TILE_HEIGHT * self.camera.zoom
        
        points = [
            (screen_x, screen_y + tile_height//2),  # ด้านบน
            (screen_x + tile_width//2, screen_y),   # ด้านขวา
            (screen_x + tile_width, screen_y + tile_height//2),  # ด้านล่าง
            (screen_x + tile_width//2, screen_y + tile_height)   # ด้านซ้าย
        ]
        
        # วาดเส้นรอบไฮไลท์ของกระเบื้อง
        pygame.draw.lines(self.screen, (255, 0, 0), True, points, 2)

    def update_selected_tile(self):
        """อัปเดตกระเบื้องที่ถูกเลือกตามตำแหน่งเมาส์"""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        tile_x, tile_y = self.iso_map.get_tile_coord_from_screen(
            mouse_x, mouse_y, self.camera, self.camera.zoom)
        
        # ตรวจสอบว่าอยู่ในขอบเขตของแผนที่ก่อนอัปเดต
        if (0 <= tile_x < self.iso_map.tmx_data.width and 
            0 <= tile_y < self.iso_map.tmx_data.height):
            self.iso_map.selected_tile = (tile_x, tile_y)

    def draw_debug_info(self):
        """แสดงข้อมูลดีบักบนหน้าจอสำหรับการพัฒนา"""

        debug_info = [
            f"FPS: {int(self.clock.get_fps())}",
            f"Camera: ({int(self.camera.position.x)}, {int(self.camera.position.y)})",
            f"Zoom: {self.camera.zoom:.2f}",
            f"Selected Tile: {self.iso_map.selected_tile}"
        ]
        for i, text in enumerate(debug_info):
            surface = self.debug_font.render(text, True, (255, 255, 255))
            self.screen.blit(surface, (10, 10 + i * 25))

    def move_unit(self, target_x, target_y):
        unit_info = self.get_info()  # ดึงข้อมูลเกี่ยวกับยูนิต
        move_range = unit_info['move_range']  # รับค่าระยะการเคลื่อนที่

        distance = self.calculate_distance(self.selected_unit.x, self.selected_unit.y, target_x, target_y)
        if distance <= move_range:
            # อัปเดตตำแหน่งของยูนิต
            self.selected_unit.x = target_x
            self.selected_unit.y = target_y

    def draw_tower_highlight(self, tower):
        """วาดเส้นไฮไลท์รอบ Tower ที่ถูกเลือก""" 
        print("Drawing tower highlight...")  # Debug print 
        iso_x, iso_y = self.iso_map.cart_to_iso(tower.x, tower.y) 
        screen_x = iso_x * self.camera.zoom + self.config.OFFSET_X + self.camera.position.x 
        screen_y = iso_y * self.camera.zoom + self.config.OFFSET_Y + self.camera.position.y - (self.config.TILE_HEIGHT * self.camera.zoom) 

        highlight_width = int(32 * self.camera.zoom) 
        highlight_height = int(32 * self.camera.zoom) 

        pygame.draw.rect(self.screen, (0, 0, 0), 
                     (screen_x, screen_y, highlight_width, highlight_height), 2) 

        print("Highlight drawn.")  # Debug print 
        self.draw_create_unit_buttons(tower)  # Call the updated function to draw unit buttons

    def attack_enemy(self, target):
        """โจมตีเป้าหมาย"""
        if self.is_in_range(target):  # ตรวจสอบว่าต้องอยู่ในระยะการโจมตี
            target.current_hp -= self.attack  # ลดพลังชีวิตของเป้าหมาย
            print(f"{self.name} attacked {target.name}! {target.name}'s HP is now {target.current_hp}.")
            
            if target.current_hp <= 0:
                print(f"{target.name} has been destroyed!")
        else:
            print(f"{target.name} is out of attack range!")
    
    def is_in_range(self, target):
        """ตรวจสอบว่าเป้าหมายอยู่ในระยะการโจมตีหรือไม่"""
        distance = self.calculate_distance(self.x, self.y, target.x, target.y)
        return distance <= self.attack_range

    def handle_events(self):
        events = pygame.event.get()
        current_time = pygame.time.get_ticks()
        delta_time = (current_time - self.last_time) / 1000.0
        self.last_time = current_time

        mouse_x, mouse_y = 0, 0

        for event in events:
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                tile_x, tile_y = self.iso_map.get_tile_coord_from_screen(mouse_x, mouse_y, self.camera, self.camera.zoom)

                if event.button == 1:  # Left click
                    self.handle_left_click(mouse_x, mouse_y, tile_x, tile_y)
                elif event.button == 3:  # Right click
                    self.handle_right_click(tile_x, tile_y)

        # Update objects
        for unit in self.player_units:  # ใช้ self.player_units หรือ self.units ตามที่คุณมี
            unit.update(delta_time, self.player_units, self.boss, self.monsters)  # ส่ง all_units เป็นอาร์กิวเมนต์ที่สอง

        self.camera.handle_input(pygame.key.get_pressed(), events)

        return True

    def handle_left_click(self, mouse_x, mouse_y, tile_x, tile_y):
        # Check for action buttons first
        if self.move_button.collidepoint(mouse_x, mouse_y):
            if self.selected_unit:
                self.current_action = 'move'
                self.select_action('move')
            else:
                print("กรุณาเลือกยูนิตก่อนที่จะเคลื่อนที่.")

        elif self.attack_button.collidepoint(mouse_x, mouse_y):
            if self.selected_unit:
                if not self.selected_unit.attacked_this_turn:  # ตรวจสอบว่ามีการโจมตีในเทิร์นนี้หรือไม่
                    self.current_action = 'attack'
                    print("กรุณาเลือกเป้าหมายเพื่อโจมตี.")

                    # เรียกฟังก์ชันเพื่อหาวัตถุเป้าหมายที่ผู้เล่นคลิก
                    target = self.get_target_object(mouse_x, mouse_y)

                    if target is not None:
                        # ถ้ามีเป้าหมายที่เลือก
                        self.selected_unit.attack(target, self)  # ส่ง self เป็นอาร์กิวเมนต์ game
                        self.selected_unit.attacked_this_turn = True  # ตั้งค่าสถานะว่ามีการโจมตีแล้ว
                        self.selected_unit.is_attacking = True  # เริ่มแอนิเมชันการโจมตี
                        print(f"{self.selected_unit.name} is attacking {target.object_type}.")
                    else:
                        print("ไม่มีเป้าหมายในระยะโจมตี.")
                else:
                    print("ยูนิตนี้ได้โจมตีในเทิร์นนี้แล้ว.")
            else:
                print("กรุณาเลือกยูนิตก่อนที่จะโจมตี.")

        elif self.end_turn_button.collidepoint(mouse_x, mouse_y):
            self.end_turn()  # เรียกใช้ฟังก์ชัน end_turn ที่จะจัดการกับการเดินของมอนสเตอร์
        elif self.create_tower_button and self.create_tower_button.collidepoint(mouse_x, mouse_y):
            if self.selected_unit:
                self.current_action = 'create_tower'
                print("กรุณาเลือกตำแหน่งเพื่อสร้าง Tower.")
            else:
                print("กรุณาเลือกยูนิตก่อนที่จะสร้าง Tower.")
        elif self.archer_button.collidepoint(mouse_x, mouse_y):
            if self.selected_tower:
                self.create_unit(self.selected_tower, UnitType.ARCHER)
                # รีเซ็ตการเลือกหลังจากสร้างยูนิต
                self.selected_tower = None
                self.selected_unit = None
        elif self.soldier_button.collidepoint(mouse_x, mouse_y):
            if self.selected_tower:
                self.create_unit(self.selected_tower, UnitType.SOLDIER)
                # รีเซ็ตการเลือกหลังจากสร้างยูนิต
                self.selected_tower = None
                self.selected_unit = None
        elif self.mage_button.collidepoint(mouse_x, mouse_y):  # เพิ่มเงื่อนไขสำหรับ Mage
            if self.selected_tower:
                self.create_unit(self.selected_tower, UnitType.MAGE)  # สร้างยูนิต Mage
                self.selected_tower = None
                self.selected_unit = None
        elif self.cavalry_button.collidepoint(mouse_x, mouse_y):  # เพิ่มเงื่อนไขสำหรับ Cavalry
            if self.selected_tower:
                self.create_unit(self.selected_tower, UnitType.CAVALRY)  # สร้างยูนิต Cavalry
                self.selected_tower = None
                self.selected_unit = None
        else:
            # Reset selected tower when clicking elsewhere
            self.selected_tower = None

            found_unit = False
            if self.selected_unit:
                self.selected_unit.clicked_this_turn = False

            # Check if clicked on a player's unit
            for unit in self.player_units:
                if int(unit.x) == tile_x and int(unit.y) == tile_y:
                    if unit.owner == self.current_turn and unit.current_hp > 0:  # ตรวจสอบ HP
                        self.selected_unit = unit
                        self.walkable_tiles = self.get_walkable_tiles(unit)
                        self.selected_unit.clicked_this_turn = True
                        found_unit = True
                        self.current_action = None
                        break

            # Check if clicked on a tower
            tower_clicked = False 
            for tower in self.towers: 
                if int(tower.x) == tile_x and int(tower.y) == tile_y: 
                    if tower.owner == self.current_turn:  # ตรวจสอบว่า Tower เป็นของผู้เล่นคนปัจจุบันหรือไม่
                        self.selected_tower = tower 
                        tower_clicked = True 
                        print(f"Selected tower at position: ({tower.x}, {tower.y})")  # Debug print 
                    break 

            # If no tower was clicked, clear the selected tower
            if not tower_clicked:
                self.selected_tower = None

            # ตรวจสอบว่ามีการโจมตี
            for opponent_unit in self.player_units:
                if int(opponent_unit.x) == tile_x and int(opponent_unit.y) == tile_y:
                    if opponent_unit.owner != self.current_turn:
                        if self.current_action == 'attack' and self.selected_unit and not self.selected_unit.attacked_this_turn:
                            self.selected_unit.attack(opponent_unit, self)  # ส่ง self เป็นอาร์กิวเมนต์เกม
                            self.selected_unit.attacked_this_turn = True  # ตั้งค่าสถานะว่าได้โจมตีแล้ว
                            self.current_action = None
                        break

            # Check if clicked on the boss 
            if self.boss is not None and int(self.boss.x) == tile_x and int(self.boss.y) == tile_y: 
                if self.current_action == 'attack' and self.selected_unit and not self.selected_unit.attacked_this_turn: 
                    self.selected_unit.attack(self.boss, self)  # ส่ง game เข้าไปด้วย 
                    self.selected_unit.attacked_this_turn = True  # ตั้งค่าสถานะว่าได้โจมตีแล้ว 
                    self.current_action = None 
                    print(f"{self.selected_unit.name} is attacking the Boss!") 
            
                    # ตรวจสอบว่าบอสยังมีชีวิตอยู่ก่อนที่จะตอบโต้
                    if self.boss and not self.boss.is_dead:
                        self.boss.counterattack(self.selected_unit)  # ส่งยูนิตที่โจมตีบอส 
                    else:
                        print("The boss is dead and cannot counterattack.")
                
            # Check if clicked on a monster
            for monster in self.monsters:  # สมมุติว่ามีลิสต์ monsters ที่เก็บมอนสเตอร์ทุกประเภท
                if int(monster.x) == tile_x and int(monster.y) == tile_y:
                    if self.current_action == 'attack' and self.selected_unit and not self.selected_unit.attacked_this_turn:
                        self.selected_unit.attack(monster, self)
                        self.selected_unit.attacked_this_turn = True  # ตั้งค่าสถานะว่าได้โจมตีแล้ว
                        self.current_action = None
                        print(f"{self.selected_unit.name} is attacking {monster.name}!")  # ใช้ monster.name เพื่อแสดงชื่อมอนสเตอร์
                    break  # ออกจากลูปหลังจากตรวจสอบแล้ว

            if not found_unit:
                self.selected_unit = None
                self.walkable_tiles = []





    def handle_right_click(self, tile_x, tile_y):
        if self.selected_unit:
            if not self.selected_unit.moved_this_turn:  # ตรวจสอบว่ายูนิตยังไม่เคลื่อนที่ในเทิร์นนี้
                if self.current_action == 'move':
                    distance = self.calculate_distance(self.selected_unit.x, self.selected_unit.y, tile_x, tile_y)
                    if distance <= self.selected_unit.move_range:
                        self.selected_unit.set_destination(tile_x, tile_y, self.path_finder)
                        self.selected_unit.clicked_this_turn = True
                        self.selected_unit.moved_this_turn = True  # ตั้งค่าสถานะว่ามีการเคลื่อนที่แล้ว
                        self.walkable_tiles = []
                    else:
                        print("ยูนิตนี้ไม่สามารถเดินไปยังจุดนั้นได้ เนื่องจากอยู่นอกระยะการเดิน.")
                elif self.current_action == 'create_tower':
                    distance = self.calculate_distance(self.selected_unit.x, self.selected_unit.y, tile_x, tile_y)
                    if distance <= self.selected_unit.create_tower_range:
                        self.create_tower(tile_x, tile_y)
                        self.current_action = None
                        self.selected_unit.moved_this_turn = True  # ตั้งค่าสถานะว่ามีการสร้างหอคอยแล้ว

    # ในฟังก์ชัน update ของเกม
    def update_game(self, delta_time): 
        for unit in self.player_units:  # ใช้ self.player_units 
            unit.update(delta_time)  # อัปเดตยูนิต 

        for monster in self.monsters:  # อัปเดตมอนสเตอร์ 
            monster.update() 

        # อัปเดตบอสถ้ามี 
        if self.boss: 
            self.boss.update()  # อัปเดตบอส 

            # ตรวจสอบว่าบอสต้องเคลื่อนที่หรือไม่
            if self.current_round % 4 == 0:  # ทุกๆ 4 รอบ
                self.move_boss()  # ให้บอสเคลื่อนที่

            # ตรวจสอบว่าบอสตายหรือไม่ 
            if self.boss.health <= 0: 
                print(f"The Boss has been defeated! Dropped {self.boss.drop_value} coins.") 
                # เพิ่มเงินที่ดรอปให้กับผู้เล่น 
                for unit in self.player_units: 
                    if unit.owner == self.boss.owner:  # สมมุติว่าบอสมีแอตทริบต์ owner 
                        unit.current_hp += self.boss.drop_value  # หรือเพิ่มให้กับผู้เล่นโดยตรง 
                self.boss = None  # ลบบอสออกจากเกม 
    
    def get_target_object(self, mouse_x, mouse_y):
        """ค้นหาวัตถุเป้าหมายที่ผู้เล่นคลิก"""
        tile_x, tile_y = self.iso_map.get_tile_coord_from_screen(mouse_x, mouse_y, self.camera, self.camera.zoom)

        # ตรวจสอบว่ามียูนิตอยู่ที่ตำแหน่งที่คลิกหรือไม่
        for unit in self.player_units:
            if int(unit.x) == tile_x and int(unit.y) == tile_y:
                return unit  # คืนค่าหน่วยที่ถูกคลิก

        # ตรวจสอบว่ามีทาวเวอร์อยู่ที่ตำแหน่งที่คลิกหรือไม่
        for tower in self.towers:
            if int(tower.x) == tile_x and int(tower.y) == tile_y:
                return tower  # คืนค่าทาวเวอร์ที่ถูกคลิก

        return None  # ถ้าไม่มีวัตถุที่ถูกคลิก

    def select_action(self, action_type):
        current_time = pygame.time.get_ticks()
        """ให้ผู้เล่นเลือกว่าจะทำการ move หรือ attack"""
        if self.selected_unit is None:
            print("กรุณาเลือกยูนิตก่อนที่จะทำการเคลื่อนที่หรือโจมตี.")
            return

        if action_type == 'move':
            if self.selected_unit.perform_action(action_type):
                self.current_action = 'move'
                # เริ่ม animation
                self.move_button_animation['active'] = True
                self.move_button_animation['start_time'] = current_time
                print(f"{self.selected_unit.name} is moving.")
            else:
                print(f"{self.selected_unit.name} has already acted this turn.")

        elif action_type == 'attack':
            if self.selected_unit.perform_action(action_type):
                self.current_action = 'attack'
                # เริ่ม animation
                self.attack_button_animation['active'] = True
                self.attack_button_animation['start_time'] = current_time
                print(f"{self.selected_unit.name} is attacking.")
        else:
                print(f"{self.selected_unit.name} has already acted this turn.")

    def game_over(self, current_turn):
        """จัดการการสิ้นสุดเกม"""
        print(f"Player {current_turn + 1} has no units left. Game Over!")  # แสดงข้อความเมื่อไม่มีผู้เล่นเหลืออยู่

        # คุณสามารถกำหนดผู้ชนะได้ตามที่ต้องการที่นี่
        if current_turn == 0:
            self.winner = 2  # Player 2 ชนะ
        else:
            self.winner = 1  # Player 1 ชนะ

        print(f"Player {self.winner} wins!")  # แสดงข้อความผู้ชนะ

    def reset_game(self):
        config = GameConfig()
        game = Game(config)
        game.run()

    def draw_game_over(self):
        """วาดหน้าจอ Game Over"""
        # สร้างพื้นหลังสีดำโปร่งใส
        game_over_background = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        game_over_background.fill((0, 0, 0))  # สีดำ
        game_over_background.set_alpha(128)  # ความโปร่งใส 0-255 (255 = ไม่โปร่งใส, 0 = โปร่งใสทั้งหมด)

        # วาดพื้นหลังลงบนหน้าจอ
        self.screen.blit(game_over_background, (0, 0))

        font = pygame.font.Font("assets/Fonts/PixgamerRegular-OVD6A.ttf", 72)
        # วาดข้อความผู้ชนะตามเทิร์นของผู้เล่น
        if self.winner is not None:
            winner_text = font.render(f"Player {self.winner} wins!", True, (255, 255, 0))
        else:
            winner = 1 if self.current_turn == 0 else 2  # ผู้เล่นที่ชนะ
            winner_text = font.render(f"Player {winner} wins Game Over!", True, (239,191,4))

        # จัดตำแหน่งข้อความผู้ชนะให้แสดงที่ด้านบนกลางของหน้าจอ
        winner_rect = winner_text.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(winner_text, winner_rect)

        # วาดข้อความเพิ่มเติม เช่น "Press R to Restart" หรือ "Press Q to Quit"
        restart_text = font.render("Press R to Restart", True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 50))
        self.screen.blit(restart_text, restart_rect)

        quit_text = font.render("Press Q to Quit", True, (255, 255, 255))
        quit_rect = quit_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 120))
        self.screen.blit(quit_text, quit_rect)

        # ตรวจสอบการกดปุ่มเพื่อรีสตาร์ทหรือออกจากเกม
        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:  # กด R เพื่อเริ่มใหม่
            pygame.mixer.music.stop()  # หยุดเพลงก่อนรีสตาร์ท
            self.reset_game()  # ฟังก์ชันนี้ต้องถูกสร้างเพื่อรีเซ็ตเกม
        elif keys[pygame.K_q]:  # กด Q เพื่อออกจากเกม
            pygame.mixer.music.stop()  # หยุดเพลงก่อนออกจากเกม
            pygame.quit()  # ปิดเกม
    
    def run(self):
        """ลูปหลักของเกม"""
        pygame.display.set_caption("WAHT!!  strategy GOOD GAMING cheir")  # เปลี่ยนชื่อเกมที่แสดงในหน้าต่าง
        running = True
        self.game_over_screen = False  # สถานะการแสดงหน้าจอ Game Over
        self.win_music_played = False  # สถานะการเล่นเพลงชนะ
        pygame.mixer.init()  # เริ่มต้น mixer
        pygame.mixer.music.load("sound/playing_music.mp3")  # โหลดเพลง
        pygame.mixer.music.set_volume(0.2)  # ลดเสียงเพลงพื้นหลังลงเหลือ 50%
        pygame.mixer.music.play(-1)  # เล่นเพลงซ้ำตลอดไป

        while running:
            delta_time = self.clock.tick(self.config.FPS) / 1000.0
            running = self.handle_events()
            events = pygame.event.get()

            # อัพเดตสถานะของยูนิต
            for obj in self.iso_map.objects:
                if isinstance(obj, Unit):  # ตรวจสอบว่า obj เป็น Unit หรือไม่
                    obj.update(delta_time, self.player_units, self.boss, self.monsters)  # อัปเดตยูนิต

            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_RETURN:  # เปลี่ยนปุ่มเป็น Enter สำหรับ "End Turn"
                        self.end_turn()  # เรียกใช้ฟังก์ชัน end_turn

            keys = pygame.key.get_pressed()
            self.camera.handle_input(keys, events)

            # อัปเดตตำแหน่งกล้องและกระเบื้องที่ถูกเลือก
            self.update_selected_tile()

            # อัพเดทสถานะเกม
            self.update_capture_points()

            # ตรวจสอบว่าผู้เล่นมียูนิตเหลืออยู่หรือไม่
            if not any(unit.current_hp > 0 for unit in self.player_units if unit.owner != self.current_turn):  # ตรวจสอบยูนิตของฝ่ายตรงข้าม
                self.game_over_screen = True  # ตั้งค่าสถานะให้แสดงหน้าจอ Game Over

            # วาดฉากของเกม
            self.screen.fill((0, 151, 167))
            self.draw_map()
            self.draw_move_button()  # วาดปุ่ม "Move"
            self.draw_attack_button()  # วาดปุ่ม "Attack"
            self.draw_end_turn_button()  # วาดปุ่ม "End Turn"
            self.draw_turn_display()  # วาดข้อความแสดงเทิร์นของผู้เล่น
            self.draw_money_display()  # วาดข้อความแสดงเงินของผู้เล่นที่มีเทิร์น
            self.draw_round_display()  # วาดข้อความแสดงรอบของเกม
            self.draw_debug_info()

            # วาดปุ่มสร้างยูนิตถ้ามี Tower ที่เลือก
            if self.selected_tower:
                self.draw_create_unit_buttons(self.selected_tower)  # วาดปุ่มสร้างยูนิต

            # ตรวจสอบการคลิกเมาส์
            mouse_pos = pygame.mouse.get_pos()
            if pygame.mouse.get_pressed()[0]:  # ถ้าคลิกซ้าย
                self.handle_mouse_click(mouse_pos, self.selected_tower)  # ส่งตำแหน่งเมาส์และทาวเวอร์ที่เลือก

            if self.game_over_screen:
                self.draw_game_over()  # เรียกฟังก์ชันวาดหน้าจอ Game Over
                
                # โหลดและเล่นเพลงชนะถ้ายังไม่เคยเล่น
                if not self.win_music_played:
                    pygame.mixer.music.load("sound/Victory Final Fantasy VII Music.mp3")  # โหลดเพลงชนะ
                    pygame.mixer.music.play(-1)  # เล่นเพลงชนะซ้ำตลอดไป
                    self.win_music_played = True 
            pygame.display.flip()

            # รักษาอัตราเฟรมเรต
            self.clock.tick(self.config.FPS)

        pygame.quit()