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
        self.generate_capture_points(5)
        self.current_round = 1
        self.create_tower_button = None
        self.towers = []
        self.tower_created = [False, False]
        self.soldier_button = None
        self.archer_button = None
        self.unit_creation_button = None  # ปุ่มสำหรับสร้างยูนิต
        self.unit_type_to_create = None  # ประเภทของยูนิตที่จะสร้าง
        self.GRID_WIDTH = self.iso_map.tmx_data.width  # จำนวนช่องในแนวนอนจาก TMX
        self.GRID_HEIGHT = self.iso_map.tmx_data.height  # จำนวนช่องในแนวตั้งจาก TMX
        self.monsters = []  # กำหนด self.monsters เป็นลิสต์ว่าง
        self.monsters_created = False  # ตัวแปรเพื่อเก็บสถานะว่ามอนสเตอร์ถูกสร้างขึ้นแล้ว
        self.create_monsters()  # เรียกใช้ฟังก์ชันสร้างมอนสเตอร์
        self.last_turn_time = 0  # เวลาของเทิร์นล่าสุด
        self.turn_interval = 1000  # หรือค่าที่คุณต้องการ

        self.move_button_animation = {
        'scale': 1.0,
        'color': (0, 255, 0),
        'start_time': 0,
        'duration': 300,  # ระยะเวลา animation
        'active': False
        }
        self.attack_button_animation = {
            'scale': 1.0,
            'color': (255, 165, 0),
            'start_time': 0,
            'duration': 300,
            'active': False
        }

        # สร้างเฟรม idle สำหรับยูนิต
        self.unit_idle_spritesheet = pygame.image.load("assets/sprites/unit2_idle_blue.png").convert_alpha()
        self.unit_idle_frames = []
        frame_width = 32
        frame_height = 32
        number_of_frames = 4
        for i in range(number_of_frames):
            frame = self.unit_idle_spritesheet.subsurface((i * frame_width, 0, frame_width, frame_height))
            self.unit_idle_frames.append(frame)

        # สร้างยูนิตสำหรับผู้เล่น 1 และ 2
        self.units = []  # ลิสต์สำหรับเก็บยูนิตทั้งหมด
        self.player_units = []  # ลิสต์สำหรับเก็บยูนิตของผู้เล่น
        self.create_player_units()

        self.current_turn = 0
        button_width = 120
        button_height = 50
        self.end_turn_button = pygame.Rect(config.SCREEN_WIDTH - button_width - 10, config.SCREEN_HEIGHT - button_height - 10, button_width, button_height)
        self.move_button = pygame.Rect(self.end_turn_button.x, self.end_turn_button.y - button_height - 10, button_width, button_height)
        self.attack_button = pygame.Rect(self.move_button.x, self.move_button.y - button_height - 10, button_width, button_height)
        self.font = pygame.font.Font("./assets/Fonts/PixgamerRegular-OVD6A.ttf", 28)
    
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
    
        # รีเซ็ตสถานะการทำ action ของยูนิตทุกตัวเมื่อเริ่มเทิร์นใหม่ 
        for unit in self.player_units: 
            unit.reset_action()  # ฟังก์ชันนี้ต้องถูกสร้างในคลาส Unit 

        # เคลื่อนที่มอนสเตอร์เมื่อจบเทิร์น
        for monster in self.monsters:
            monster.move()  # ให้มอนสเตอร์เคลื่อนที่
            monster.update(0)  # อัปเดตอนิเมชันโดยไม่ใช้ delta_time

        # เช็คว่าต้องเพิ่มรอบหรือไม่ 
        if self.current_turn == 1:  # ถ้าผู้เล่น 2 จบเทิร์น 
            self.current_round += 1  # เพิ่มรอบ 
            print(f"Round {self.current_round} started.") 

        # รีเซ็ตสถานะของยูนิตที่เลือก 
        if self.selected_unit: 
            self.selected_unit.has_actioned = False  # รีเซ็ตสถานะการทำ action ของยูนิต 
        self.selected_unit = None  # รีเซ็ตยูนิตที่เลือก 
        self.current_action = None  # รีเซ็ต action ปัจจุบัน 

        # รีเซ็ตสถานะการสร้าง Tower สำหรับผู้เล่น
        self.tower_created = [False, False]  # รีเซ็ตสถานะการสร้าง Tower สำหรับผู้เล่น 1 และ 2 

        # เปลี่ยน turn ระหว่างผู้เล่น 
        self.current_turn = (self.current_turn + 1) % 2  # เปลี่ยน turn ระหว่างผู้เล่น 0 และ 1 
        print(f"Turn changed to player {self.current_turn + 1}.")  # แสดงข้อความเปลี่ยนเทิร์น

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
        for x in range(self.iso_map.tmx_data.width):
            for y in range(self.iso_map.tmx_data.height):
                if self.path_finder.is_walkable((x, y)):
                    valid_positions.append((x, y))

        if valid_positions:
            positions = random.sample(valid_positions, min(count, len(valid_positions)))
            for x, y in positions:
                value = random.randint(50, 100)  # สุ่มค่าเงินที่จะได้รับต่อเทิร์น
                self.capture_points.append(CapturePoint(x, y, value))

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
        tower_name_surface = font.render(f"Tower Name: {self.selected_tower.player_id}", True, (255, 255, 255))
        screen.blit(tower_name_surface, (x, y + 50))

        health_surface = font.render(f"Health: {self.selected_tower.health}", True, (255, 255, 255))
        screen.blit(health_surface, (x, y + 80 + 50))

        attack_power_surface = font.render(f"Attack Power: {self.selected_tower.attack_power}", True, (255, 255, 255))
        screen.blit(attack_power_surface, (x, y + 110 + 50))

        attack_range_surface = font.render(f"Attack Range: {self.selected_tower.attack_range}", True, (255, 255, 255))
        screen.blit(attack_range_surface, (x, y + 140 + 50))

    def draw_round_display(self):
        """วาดข้อความแสดงรอบของเกมบนหน้าจอ"""
        font = pygame.font.Font("assets/Fonts/PixgamerRegular-OVD6A.ttf", 36)  # ใช้ฟอนต์ที่ต้องการ
        round_text = f"Round: {self.current_round}"  # ข้อความแสดงรอบ
        text_surface = font.render(round_text, True, (255, 255, 255))  # วาดข้อความด้วยสีขาว
        text_rect = text_surface.get_rect(topright=(self.config.SCREEN_WIDTH - 10, 50))  # จัดตำแหน่งที่มุมขวาบน
        self.screen.blit(text_surface, text_rect)  # วาดข้อความลงบนหน้าจอ

    def draw_end_turn_button(self):
        """วาดปุ่ม 'End Turn' บนหน้าจอ"""
        pygame.draw.rect(self.screen, (255, 0, 0), self.end_turn_button)  # วาดปุ่มสีแดง
        text_surface = self.font.render("End Turn", True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.end_turn_button.center)
        self.screen.blit(text_surface, text_rect)

    def draw_create_unit_buttons(self, tower):
        """วาดปุ่ม 'Create Archer' และ 'Create Soldier' ข้างๆ Tower ที่ถูกคลิก""" 
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
        text_surface = font.render("Create Archer", True, (255, 255, 255)) 
        text_rect = text_surface.get_rect(center=self.archer_button.center) 
        self.screen.blit(text_surface, text_rect) 

        # ปุ่มสร้าง Soldier
        soldier_button_x = screen_x + 10  # ปรับตำแหน่ง X ให้อยู่ข้าง Tower 
        soldier_button_y = archer_button_y - button_height - 10  # ปรับตำแหน่ง Y ให้อยู่เหนือ Archer button 

        self.soldier_button = pygame.Rect(soldier_button_x, soldier_button_y, button_width, button_height) 
        pygame.draw.rect(self.screen, (0, 0, 255), self.soldier_button)  # วาดปุ่มสีน้ำเงิน 
        text_surface = font.render("Create Soldier", True, (255, 255, 255)) 
        text_rect = text_surface.get_rect(center=self.soldier_button.center) 
        self.screen.blit(text_surface, text_rect)


    def draw_capture_point_info(self):
        """วาดข้อมูลเกี่ยวกับจุดยึดครอง"""
        for point in self.capture_points:
            if point.owner is None:
                status_text = "Not Captured"
            else:
             status_text = "Captured by Player"  # หรือชื่อผู้เล่นถ้ามีการจัดการหลายผู้เล่น

            # คำนวณตำแหน่งการวาดข้อความ
            iso_x, iso_y = self.iso_map.cart_to_iso(point.x, point.y)
            screen_x = iso_x * self.camera.zoom + self.config.OFFSET_X + self.camera.position.x
            screen_y = iso_y * self.camera.zoom + self.config.OFFSET_Y + self.camera.position.y

            # วาดข้อความ
            status_surface = self.debug_font.render(status_text, True, (255, 255, 255))
            self.screen.blit(status_surface, (screen_x, screen_y - 45))  # ปรับตำแหน่งตามต้องการ
    
    def draw_money_display(self):
        """แสดงจำนวนเงินของผู้เล่นที่มีเทิร์นบนหน้าจอ"""
        current_player_index = self.current_turn  # ดึงหมายเลขผู้เล่นที่มีเทิร์น
        money_text = self.debug_font.render(f"Player {current_player_index + 1} Money: ${self.player_money[current_player_index]}", 
                                         True, (255, 215, 0))
    
        # ปรับตำแหน่ง Y ของข้อความให้สูงขึ้นจากตำแหน่งปุ่ม "End Turn"
        money_text_y = self.end_turn_button.top - 10  # 10 พิกเซลด้านบนของปุ่ม
        self.screen.blit(money_text, (10, money_text_y))  # แสดงเงินของผู้เล่นที่มีเทิร์น

        # แสดงจำนวนจุดที่ยึดได้
        captured_points = sum(1 for point in self.capture_points if point.owner is not None)
        points_text = self.debug_font.render(f"Captured Points: {captured_points}/{len(self.capture_points)}", 
                                          True, (255, 215, 0))
    
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
        text_surface = self.font.render("Move", True, (255, 255, 255))
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
        text_surface = self.font.render("Attack", True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=scaled_button.center)
        self.screen.blit(text_surface, text_rect)

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

        # ตรวจสอบว่า tower มีแอตทริบิวต์ owner
        if not hasattr(tower, 'owner'):
            print("ไม่สามารถสร้างยูนิตได้: ทาวเวอร์ไม่มีแอตทริบิวต์ owner.")
            return False

        print(f"กำลังสร้างยูนิต: {unit_type} ที่ {tower.x}, {tower.y}")

        # รับข้อมูลเจ้าของของทาวเวอร์
        player_index = tower.owner

        # คำนวณตำแหน่งใหม่ของยูนิตที่จะอยู่ข้างๆ ทาวเวอร์
        x = tower.x + 1   # ปรับตำแหน่ง X ให้ยูนิตอยู่ทางขวาของ Tower
        y = tower.y        # ปรับตำแหน่ง Y ให้อยู่ที่เดียวกับ Tower

        # ตรวจสอบว่าตำแหน่งยูนิตใหม่อยู่ภายในขอบเขตของหน้าจอ
        if x < 0 or x > self.config.SCREEN_WIDTH or y < 0 or y > self.config.SCREEN_HEIGHT:
            print("ไม่สามารถสร้างยูนิตได้: ตำแหน่งนอกขอบเขตของหน้าจอ.")
            return False

        # โหลดเฟรม idle สำหรับยูนิตที่ถูกสร้างตามเจ้าของ
        sprite_path = None
        if unit_type == UnitType.SOLDIER:
            sprite_path = "assets/sprites/unit1_idle_blue.png" if player_index == 0 else "assets/sprites/unit1_idle_red.png"
        elif unit_type == UnitType.ARCHER:
            sprite_path = "assets/sprites/unit2_idle_blue.png" if player_index == 0 else "assets/sprites/unit2_idle_red.png"
        else:
            print("ประเภทยูนิตไม่รู้จัก.")
            return False

        # โหลดสไปรต์และตรวจสอบความสำเร็จ
        try:
            unit_idle_spritesheet = pygame.image.load(sprite_path).convert_alpha()
            unit_idle_frames = self.load_idle_frames(unit_idle_spritesheet)
        except Exception as e:
            print(f"ไม่สามารถโหลดสไปรต์ได้: {e}")
            return False

        # สร้างยูนิตใหม่ที่ตำแหน่ง (x, y) ที่คำนวณไว้
        new_unit = Unit(unit_idle_frames, unit_type, x, y, owner=player_index)  # ส่ง owner ให้กับ constructor

        # ไม่ต้องเพิ่มยูนิตใหม่ลงในลิสต์
        print("ยูนิตถูกสร้างอยู่ที่ตำแหน่ง:", (x, y))
    
        return True  # คืนค่าความสำเร็จในการสร้างยูนิต

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
                # ตรวจสอบว่ามี Tower อยู่แล้วที่ตำแหน่งนี้หรือไม่ 
                if not self.is_tower_at_position(x, y): 
                    player_id = player_index + 1  # กำหนด player_id จาก current_turn (1 หรือ 2) 
                
                    # โหลดภาพสำหรับ Tower
                    if player_id == 1:
                        tower_image = pygame.image.load("assets/sprites/building-blue.png").convert_alpha()
                    else:
                        tower_image = pygame.image.load("assets/sprites/building-red.png").convert_alpha()
                
                    new_tower = Tower(x, y, player_id, tower_image)  # สร้าง Tower ใหม่
                    self.towers.append(new_tower)  # เพิ่ม Tower ลงในรายการ Tower 
                    self.tower_created[player_index] = True  # ตั้งค่าสถานะว่าผู้เล่นได้สร้าง Tower แล้ว 
                    self.player_money[player_index] -= 100  # หักเงิน 100 บาทจากผู้เล่น 
                    print(f"Tower created at position: ({x}, {y}) for Player {player_id}. Cost: 100.") # แสดงข้อความยืนยันการสร้าง Tower 
                    return True  # คืนค่า True หากสร้าง Tower สำเร็จ 
                else: 
                    print("Cannot create tower: There is already a tower at this position.") # แสดงข้อความหากมี Tower อยู่แล้ว 
            else: 
                print("Cannot create tower: Tile is out of unit's range.") # แสดงข้อความหากอยู่นอกระยะ 
        else: 
            print("Cannot create tower at this position.") # แสดงข้อความหากไม่สามารถสร้าง Tower ได้ 
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
                        
                        # เน้นกระเบื้องที่ถูกเลือกหากตรงกับพิกัดปัจจุบัน
                        if (x, y) == self.iso_map.selected_tile:
                            self.draw_tile_highlight(x, y)
        
         # วาดมอนสเตอร์ในแผนที่
        for monster in self.monsters:
            monster.draw(self.screen, self.iso_map, self.camera, self.config)  # เรียกใช้ฟังก์ชัน draw ของมอนสเตอร์

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
        # วาดข้อมูลเกี่ยวกับจุดยึดครอง
        self.draw_capture_point_info()

        # วาด highlight unit ที่เลือก
        if self.selected_unit:
            self.draw_unit_highlight(self.selected_unit)
           
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
        text_surface = font.render(turn_text, True, (255, 255, 255))  # วาดข้อความด้วยสีขาว
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
        pygame.draw.lines(self.screen, (255, 255, 0), True, points, 2)

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

        pygame.draw.rect(self.screen, (255, 255, 0), 
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
        for unit in self.player_units:
            unit.update(delta_time)

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
                self.current_action = 'attack'
                print("กรุณาเลือกเป้าหมายเพื่อโจมตี.")

                # เรียกฟังก์ชันเพื่อหามอนสเตอร์ที่ผู้เล่นคลิก
                target = self.get_target_monster(mouse_x, mouse_y)

                if target is not None:
                    # ถ้ามีเป้าหมายที่เลือก
                    self.selected_unit.attack(target)
                    print(f"{self.selected_unit.name} is attacking {target.monster_type if hasattr(target, 'monster_type') else 'target'}.")
                else:
                    print("ไม่มีเป้าหมายในระยะโจมตี.")
            else:
                print("กรุณาเลือกยูนิตก่อนที่จะโจมตี.")

        elif self.end_turn_button.collidepoint(mouse_x, mouse_y):
            self.end_turn()  # เรียกใช้ฟังก์ชัน end_turn ที่จะจัดการกับการเดินของมอนสเตอร์
            self.move_monsters()  # เพิ่มการเดินของมอนสเตอร์เมื่อกด End Turn
        elif self.create_tower_button and self.create_tower_button.collidepoint(mouse_x, mouse_y):
            if self.selected_unit:
                self.current_action = 'create_tower'
                print("กรุณาเลือกตำแหน่งเพื่อสร้าง Tower.")
            else:
                print("กรุณาเลือกยูนิตก่อนที่จะสร้าง Tower.")
        elif self.selected_tower:  # ตรวจสอบว่ามี Tower ที่เลือกอยู่
            # ตรวจสอบการคลิกปุ่มสร้าง Archer
            if self.archer_button.collidepoint(mouse_x, mouse_y):
                self.create_unit(self.selected_tower, UnitType.ARCHER)
            # ตรวจสอบการคลิกปุ่มสร้าง Soldier
            elif self.soldier_button.collidepoint(mouse_x, mouse_y):
                self.create_unit(self.selected_tower, UnitType.SOLDIER)
        else:
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
                    self.selected_tower = tower 
                    tower_clicked = True
                    print(f"Selected tower at position: ({tower.x}, {tower.y})")  # Debug print
                    break 

            # If no tower was clicked, clear the selected tower
            if not tower_clicked:
                self.selected_tower = None

            # Check if clicked on an opponent's unit
            for opponent_unit in self.player_units:
                if int(opponent_unit.x) == tile_x and int(opponent_unit.y) == tile_y:
                    if opponent_unit.owner != self.current_turn:
                        if self.current_action == 'attack':
                            self.selected_unit.attack(opponent_unit)
                            self.current_action = None
                        break

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
                        self.walkable_tiles = []
                    else:
                        print("ยูนิตนี้ไม่สามารถเดินไปยังจุดนั้นได้ เนื่องจากอยู่นอกระยะการเดิน.")
                elif self.current_action == 'create_tower':
                    distance = self.calculate_distance(self.selected_unit.x, self.selected_unit.y, tile_x, tile_y)
                    if distance <= self.selected_unit.create_tower_range:
                        self.create_tower(tile_x, tile_y)
                        self.current_action = None

    # ในฟังก์ชัน update ของเกม
    def update_game(self, delta_time):
        for monster in self.monsters:
            monster.move()  # ให้มอนสเตอร์เคลื่อนที่
            monster.update(delta_time)  # อัปเดตอนิเมชัน

    def move_monsters(self):
        """เคลื่อนที่มอนสเตอร์"""
        for monster in self.monsters:
            monster.move()  # เรียกใช้ฟังก์ชัน move() ของมอนสเตอร์
            monster.update(0)  # อัปเดตอนิเมชันของมอนสเตอร์โดยไม่ใช้ delta_time

    def get_target_monster(self, mouse_x, mouse_y):
        for monster in self.monsters:
            if (monster.x <= mouse_x <= monster.x + monster.width and
                monster.y <= mouse_y <= monster.y + monster.height):
                return monster  # คืนค่ามอนสเตอร์ที่ถูกเลือก
        return None  # หากไม่มีมอนสเตอร์ที่ถูกเลือก
    
    def create_monsters(self, num_monsters=3):
        slime_sprite_paths = {
        "idle": "assets/Monster/slime_idle.png",
        "walk": "assets/Monster/slime_run.png",
        "die": "assets/Monster/slime_die.png"
        }
        """สร้างมอนสเตอร์ในเกมแบบสุ่ม"""
        if self.monsters_created:
            return  # หากมอนสเตอร์ถูกสร้างขึ้นแล้ว ให้ไม่ทำอะไร

        occupied_positions = set()  # ใช้ชุดเพื่อเก็บตำแหน่งที่ถูก occupied

        for _ in range(num_monsters):
            while True:
                # สุ่มตำแหน่ง x และ y สำหรับมอนสเตอร์
                x = random.randint(0, self.GRID_WIDTH - 1)
                y = random.randint(0, self.GRID_HEIGHT - 1)

                # ตรวจสอบว่าตำแหน่งนี้ถูก occupied หรือไม่
                if (x, y) not in occupied_positions:
                    occupied_positions.add((x, y))  # เพิ่มตำแหน่งลงในชุด

                    # กำหนดขนาดของมอนสเตอร์
                    width = self.config.TILE_WIDTH  # หรือค่าความกว้างที่คุณต้องการ
                    height = self.config.TILE_HEIGHT  # หรือค่าความสูงที่คุณต้องการ

                    # สร้างมอนสเตอร์ Slime โดยส่ง width และ height ไปด้วย
                    self.monsters.append(Monster(x=x, y=y, width=width, height=height, monster_type="Slime", sprite_paths=slime_sprite_paths, tile_size=self.config.TILE_WIDTH, map_width=self.GRID_WIDTH, map_height=self.GRID_HEIGHT))
                    break  # ออกจากลูป while

        self.monsters_created = True  # ตั้งค่าว่ามอนสเตอร์ถูกสร้างขึ้นแล้ว

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

    def run(self):
        """ลูปหลักของเกม"""
        running = True
        pygame.mixer.init()  # เริ่มต้น mixer
        pygame.mixer.music.load("assets/sound/playing_music.mp3")  # โหลดเพลง
        pygame.mixer.music.play(-1)  # เล่นเพลงซ้ำตลอดไป

        # สร้างมอนสเตอร์เพียงครั้งเดียวเมื่อเริ่มเกม
        self.create_monsters()

        while running:
            delta_time = self.clock.tick(self.config.FPS) / 1000.0
            running = self.handle_events()
            events = pygame.event.get()

            # อัพเดตสถานะของยูนิต
            for obj in self.iso_map.objects:
                if isinstance(obj, Unit):  # ตรวจสอบว่า obj เป็น Unit หรือไม่
                    obj.update(delta_time)  # อัปเดตยูนิต

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

            # วาดฉากของเกม
            self.screen.fill((0, 0, 0))
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

            pygame.display.flip()
    
            # รักษาอัตราเฟรมเรต
            self.clock.tick(self.config.FPS)

        pygame.quit()