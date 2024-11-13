import pygame
import pytmx
import pygame_gui
import random
from typing import Tuple, Optional
from dataclasses import dataclass
from queue import PriorityQueue
import math
from enum import Enum
from typing import Dict
# คำสั่งติดตั้ง pytmx: pip install pytmx

@dataclass
class GameConfig:
    """การตั้งค่าคอนฟิกสำหรับเกม"""
    SCREEN_WIDTH: int = 1280
    SCREEN_HEIGHT: int = 720
    TILE_WIDTH: int = 32
    TILE_HEIGHT: int = 16
    FPS: int = 60
    CAMERA_SPEED: int = 5
    MIN_ZOOM: float = 0.5
    MAX_ZOOM: float = 2.0
    ZOOM_SPEED: float = 0.1
    
    @property
    def OFFSET_X(self) -> int:
        # คำนวณตำแหน่งกึ่งกลางของหน้าจอในแกน X
        return self.SCREEN_WIDTH // 2
        
    @property
    def OFFSET_Y(self) -> int:
        # คำนวณตำแหน่งหนึ่งในสี่ของหน้าจอในแกน Y
        return self.SCREEN_HEIGHT // 4

class Tower:
    def __init__(self, x, y, player_id):
        self.x = x  # ตำแหน่ง X ของ Tower
        self.y = y  # ตำแหน่ง Y ของ Tower
        self.health = 100  # ค่าเริ่มต้นสุขภาพของ Tower
        self.attack_power = 10  # พลังโจมตีของ Tower
        self.attack_range = 3  # ระยะการโจมตีของ Tower
        self.player_id = player_id  # ระบุผู้เล่นที่เป็นเจ้าของ Tower
        self.image = self.load_image()  # ฟังก์ชันสำหรับโหลดภาพ Tower

    def load_image(self):
        """โหลดภาพตามผู้เล่น"""
        try:
            if self.player_id == 1:
                image = pygame.image.load("assets/sprites/building-blue.png").convert_alpha()  # สำหรับผู้เล่น 1
            elif self.player_id == 2:
                image = pygame.image.load("assets/sprites/building-red.png").convert_alpha()  # สำหรับผู้เล่น 2
            return image
        except pygame.error as e:
            print(f"Unable to load image: {e}")
            return None  # คืนค่า None หากไม่สามารถโหลดภาพได้

    def draw(self, screen, camera, config):
        """วาด Tower บนหน้าจอ"""
        if self.image is not None:  # ตรวจสอบว่าภาพถูกโหลดหรือไม่
            iso_x, iso_y = self.cart_to_iso(self.x, self.y)
            screen_x = iso_x * camera.zoom + config.OFFSET_X + camera.position.x
            screen_y = iso_y * camera.zoom + config.OFFSET_Y + camera.position.y - (config.TILE_HEIGHT * camera.zoom)

            # วาดภาพ Tower
            scaled_image = pygame.transform.scale(self.image, (int(self.image.get_width() * camera.zoom),
                                                                int(self.image.get_height() * camera.zoom)))
            screen.blit(scaled_image, (screen_x, screen_y))

            # วาดสถานะสุขภาพ
            self.draw_health_bar(screen, screen_x, screen_y)
        else:
            print("Tower image not available.")

    def draw_health_bar(self, screen, screen_x, screen_y):
        """วาดแถบสุขภาพของ Tower"""
        health_bar_length = 40
        health_ratio = self.health / 100  # สมมุติว่าค่าสุขภาพสูงสุดคือ 100
        pygame.draw.rect(screen, (255, 0, 0), (screen_x, screen_y - 10, health_bar_length, 5))  # แถบสุขภาพเต็ม
        pygame.draw.rect(screen, (0, 255, 0), (screen_x, screen_y - 10, health_bar_length * health_ratio, 5))  # แถบสุขภาพที่ลดลง

    def cart_to_iso(self, x, y):
        """แปลงพิกัดคาร์ทีเซียนเป็นพิกัดไอโซเมตริก"""
        iso_x = (x - y) * (32 // 2)  # ปรับตามขนาดของ tile
        iso_y = (x + y) * (16 // 2)  # ปรับตามขนาดของ tile
        return iso_x, iso_y

    def attack(self, target):
        """โจมตีเป้าหมาย"""
        if self.is_in_range(target):
            target.health -= self.attack_power  # ลดสุขภาพของเป้าหมายตามพลังโจมตี
            print(f"Attacked target! Target health is now {target.health}")

            # ตรวจสอบว่าต้องทำลายเป้าหมายหรือไม่
            if target.health <= 0:
                print("Target destroyed!")

    def is_in_range(self, target):
        """ตรวจสอบว่าเป้าหมายอยู่ในระยะการโจมตีหรือไม่"""
        distance = math.sqrt((self.x - target.x) ** 2 + (self.y - target.y) ** 2)
        return distance <= self.attack_range

    def heal(self, amount):
        """ฟังก์ชันสำหรับฟื้นฟูสุขภาพของ Tower"""
        self.health += amount
        if self.health > 100:  # สมมุติว่าค่าสุขภาพสูงสุดคือ 100
            self.health = 100
        print(f"Tower healed! Current health is {self.health}")

    def update(self):
        """ฟังก์ชันสำหรับอัปเดตสถานะของ Tower"""
        # สามารถเพิ่มฟังก์ชันการฟื้นฟูสุขภาพหรือการโจมตีเป้าหมายที่อยู่ในระยะได้ที่นี่
        pass

    def destroy(self):
        """ฟังก์ชันสำหรับจัดการการทำลาย Tower"""
        print("Tower has been destroyed!")

# กำหนดประเภทของยูนิต
class UnitType(Enum):
    SOLDIER = "soldier"
    ARCHER = "archer"

    @staticmethod
    def get_cost(unit_type):
        """ กำหนดค่าใช้จ่ายสำหรับยูนิตประเภทต่าง ๆ """
        costs = {
            UnitType.SOLDIER: 50,
            UnitType.ARCHER: 100,
        }
        return costs.get(unit_type, 0)

class Unit:
    def __init__(self, unit_idle_frames, unit_type, x=0, y=0, owner=None, name="Unit", move_range=5):
        self.unit_idle_frames = unit_idle_frames
        self.unit_type = unit_type  # เพิ่มการรับ unit_type
        self.idle_frame_index = 0
        self.idle_frame_duration = 100  # ระยะเวลาในการแสดงเฟรม (มิลลิวินาที)
        self.last_frame_update_time = pygame.time.get_ticks()
        self.x = x  # กำหนดตำแหน่งเริ่มต้น
        self.y = y  # กำหนดตำแหน่งเริ่มต้น
        self.image = self.unit_idle_frames[0]
        self.path = []
        self.moving = False
        self.speed = 1 
        self.owner = owner  # เจ้าของยูนิต
        self.name = name  # เพิ่มแอตทริบิวต์ name
        self.action_text = ""  # ฟิลด์ใหม่เพื่อเก็บข้อความการกระทำ
        self.has_actioned = False  # สถานะการทำ action ของยูนิต
        self.clicked_this_turn = False  # สถานะการคลิกในเทิร์นนี้
        self.move_range = move_range  # เพิ่มแอตทริบิวต์ move_range

        # เรียกใช้ get_info เพื่อกำหนดคุณสมบัติของยูนิต
        info = self.get_info()
        self.max_hp = info['max_hp']  # HP สูงสุด
        self.current_hp = self.max_hp  # HP ปัจจุบัน
        self.attack = info['attack']  # พลังโจมตี
        self.move_range = info['move_range']  # ระยะการเคลื่อนที่
        self.attack_range = info['attack_range']  # ระยะโจมตี
        self.create_tower_range = info['create_tower_range']  # ระยะการสร้าง Tower
    
    def get_info(self):
        """คืนค่าข้อมูลเกี่ยวกับยูนิต"""
        if self.unit_type == UnitType.SOLDIER:
            return { 
                "max_hp": 100, 
                "attack": 50, 
                "move_range": 3, 
                "attack_range": 1,
                "create_tower_range": 2  # เพิ่มคีย์นี้สำหรับ Soldier
            } 
        elif self.unit_type == UnitType.ARCHER:
            return { 
                "max_hp": 75, 
                "attack": 40, 
                "move_range": 2, 
                "attack_range": 3,
                "create_tower_range": 3  # เพิ่มคีย์นี้สำหรับ Archer
            } 
        else:
            return {}
    
    def draw_hp_bar(self, screen, x, y, max_hp, current_hp, zoom):
        """วาด HP Bar สำหรับยูนิต"""
        bar_width = 50 * zoom  # ปรับความกว้างของ HP Bar ตามซูม
        bar_height = 5 * zoom   # ปรับความสูงของ HP Bar ตามซูม
        hp_percentage = current_hp / max_hp  # คำนวณเปอร์เซ็นต์ของ HP

        # วาดกรอบของ HP Bar
        pygame.draw.rect(screen, (255, 0, 0), (x, y, bar_width, bar_height))  # กรอบสีแดง
        # วาด HP ที่เหลือ
        pygame.draw.rect(screen, (0, 255, 0), (x, y, bar_width * hp_percentage, bar_height))  # HP สีเขียว

        # วาดตัวเลข HP
        font = pygame.font.Font("assets/Fonts/PixgamerRegular-OVD6A.ttf", int(12 * zoom))  # ปรับขนาดฟอนต์ตามซูม
        hp_text = f"{current_hp}/{max_hp}"
        text_surface = font.render(hp_text, True, (255, 255, 255))  # ข้อความสีขาว
        text_rect = text_surface.get_rect(center=(x + bar_width / 2, y - 10 * zoom))  # ปรับตำแหน่งให้ตรงกลางเหนือ HP Bar
        screen.blit(text_surface, text_rect)  # วาดข้อความบนหน้าจอ

    def draw_info(self, screen, x, y):
        """วาดข้อมูลยูนิตบนหน้าจอ""" 
        font = pygame.font.Font("assets/Fonts/PixgamerRegular-OVD6A.ttf", 20) 
        info_surface = font.render(f"Name: {self.name}", True, (255, 255, 255)) 
        screen.blit(info_surface, (x, y + 50))  # ปรับตำแหน่ง Y ให้ต่ำกว่าข้อความรอบ

        hp_surface = font.render(f"HP: {self.current_hp}/{self.max_hp}", True, (255, 255, 255)) 
        screen.blit(hp_surface, (x, y + 80 + 50))  # ปรับตำแหน่ง Y

        attack_surface = font.render(f"Attack: {self.attack}", True, (255, 255, 255)) 
        screen.blit(attack_surface, (x, y + 110 + 50))  # ปรับตำแหน่ง Y

        move_range_surface = font.render(f"Move Range: {self.move_range}", True, (255, 255, 255)) 
        screen.blit(move_range_surface, (x, y + 140 + 50))  # ปรับตำแหน่ง Y

        attack_range_surface = font.render(f"Attack Range: {self.attack_range}", True, (255, 255, 255)) 
        screen.blit(attack_range_surface, (x, y + 170 + 50))  # ปรับตำแหน่ง Y
    
    def reset_action(self):
        """รีเซ็ตสถานะการทำ action ของยูนิต"""
        self.has_actioned = False  # ตั้งค่าสถานะการทำ action เป็น False
        self.clicked_this_turn = False  # รีเซ็ตสถานะการคลิก

    def perform_action(self, action_type):
        """ตรวจสอบว่ายูนิตสามารถทำ action ได้หรือไม่"""
        if not self.has_actioned:
            self.has_actioned = True  # ตั้งค่าสถานะว่าได้ทำ action ไปแล้ว
            return True  # อนุญาตให้ทำ action
        else:
            return False  # ไม่อนุญาตให้ทำ action

    def set_action_text(self, text):
        """ตั้งค่าข้อความการกระทำ"""
        self.action_text = text

    def set_destination(self, x, y, path_finder):
        """กำหนดจุดหมายและหาเส้นทาง"""
        self.path = path_finder.find_path((int(self.x), int(self.y)), (x, y))
        if self.path:
            self.path.pop(0)  # ลบตำแหน่งปัจจุบันออก
            self.moving = True

    def update(self, delta_time):
        if self.path and self.moving:
            next_pos = self.path[0]
            target_x, target_y = next_pos

            # คำนวณระยะทางที่ต้องเคลื่อนที่
            dx = target_x - self.x
            dy = target_y - self.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < 0.1:  # ถึงจุดหมายย่อยแล้ว
                self.x = target_x
                self.y = target_y
                self.path.pop(0)
                if not self.path:  # ถึงจุดหมายสุดท้าย
                    self.moving = False
                    self.reset_action()  # รีเซ็ตสถานะการทำ action
            else:
                # เคลื่อนที่ไปยังจุดหมายถัดไป
                move_x = (dx / distance) * self.speed * delta_time
                move_y = (dy / distance) * self.speed * delta_time
                self.x += move_x
                self.y += move_y

        # อัปเดตเฟรม idle
        current_time = pygame.time.get_ticks()
        if current_time - self.last_frame_update_time > self.idle_frame_duration:
            self.idle_frame_index = (self.idle_frame_index + 1) % len(self.unit_idle_frames)
            self.last_frame_update_time = current_time

    def draw(self, screen, iso_map, camera, config):
        iso_x, iso_y = iso_map.cart_to_iso(self.x, self.y)
        screen_x = iso_x * camera.zoom + config.OFFSET_X + camera.position.x
        screen_y = (iso_y * camera.zoom + config.OFFSET_Y + camera.position.y) - (config.TILE_HEIGHT * camera.zoom) - (10 * camera.zoom)

        # วาดเฟรม idle 
        current_frame = self.unit_idle_frames[self.idle_frame_index]
        if isinstance(current_frame, pygame.Surface):
            scaled_image = pygame.transform.scale(current_frame, 
            (int(current_frame.get_width() * camera.zoom), 
             int(current_frame.get_height() * camera.zoom)))
            screen.blit(scaled_image, (screen_x, screen_y))
        else:
            print("Error: current_frame is not a pygame.Surface")

        # วาดข้อมูลยูนิตถ้ามีการคลิก
        if self.clicked_this_turn:
            self.draw_info(screen, screen.get_width() - 200, 50)  # วาดข้อมูลที่ขวาบนของหน้าจอ

        # วาดข้อความการกระทำ
        if self.action_text:
            font = pygame.font.Font("assets/Fonts/PixgamerRegular-OVD6A.ttf", 24)
            text_surface = font.render(self.action_text, True, (255, 255, 255))
            screen.blit(text_surface, (screen_x, screen_y - 40))  # ปรับตำแหน่งให้สูงขึ้น

        # วาด HP Bar ข้างๆ ยูนิต
        hp_bar_x = screen_x
        hp_bar_y = screen_y - 10 * camera.zoom  # ปรับตำแหน่ง HP Bar ให้อยู่ด้านบนของยูนิต
        self.draw_hp_bar(screen, hp_bar_x, hp_bar_y, self.max_hp, self.current_hp, camera.zoom)  # ส่งค่าซูมไปยังฟังก์ชัน

class CapturePoint:
    def __init__(self, x, y, value=10):
        self.x = x
        self.y = y
        self.value = value
        self.owner = None
        self.capture_progress = 0
        self.capture_speed = 1
        self.income_interval = 1000
        self.last_income_time = pygame.time.get_ticks()
        
        # โหลด sprites
        self.neutral_sprite = pygame.image.load("assets/crystal_mine_nocap.png").convert_alpha()
        self.captured_sprite = pygame.image.load("assets/bluel_mine_cap.png").convert_alpha()
        self.current_sprite = self.neutral_sprite
        
        # ปรับขนาด sprite (ถ้าจำเป็น)
        self.sprite_size = (32, 32)  # ปรับขนาดตามต้องการ
        self.neutral_sprite = pygame.transform.scale(self.neutral_sprite, self.sprite_size)
        self.captured_sprite = pygame.transform.scale(self.captured_sprite, self.sprite_size)
        
        # เอฟเฟกต์การกะพริบ
        self.pulse_speed = 0.005
        self.alpha = 255

    def update(self, game_objects, current_time):
        unit_on_point = False
        for obj in game_objects:
            if isinstance(obj, Unit):  # ตรวจสอบว่า obj เป็น Unit หรือไม่
                if int(obj.x) == self.x and int(obj.y) == self.y:
                    unit_on_point = True
                    if self.owner != obj:
                        self.capture_progress += self.capture_speed
                        if self.capture_progress >= 100:
                            self.owner = obj
                            self.current_sprite = self.captured_sprite
                            self.capture_progress = 100
                    break

        if not unit_on_point:
            self.capture_progress = max(0, self.capture_progress - self.capture_speed)
            if self.capture_progress == 0:
                self.owner = None
                self.current_sprite = self.neutral_sprite

        # อัพเดทค่า alpha สำหรับเอฟเฟกต์กะพริบ 
        self.alpha = abs(math.sin(pygame.time.get_ticks() * self.pulse_speed)) * 55 + 200 

        if self.owner and current_time - self.last_income_time >= self.income_interval:
            return self.value
                   
        return 0
    def draw(self, screen, iso_map, camera, config):
        # คำนวณตำแหน่งบนหน้าจอ
        iso_x, iso_y = iso_map.cart_to_iso(self.x, self.y)
        screen_x = iso_x * camera.zoom + config.OFFSET_X + camera.position.x
    
        # ปรับตำแหน่ง Y ให้สูงขึ้น
        screen_y = (iso_y * camera.zoom + config.OFFSET_Y + camera.position.y) - (config.TILE_HEIGHT * camera.zoom) - (camera.zoom)

        # สร้าง sprite ที่มีขนาดตามการซูม
        scaled_size = (int(self.sprite_size[0] * camera.zoom), 
                      int(self.sprite_size[1] * camera.zoom))
        scaled_sprite = pygame.transform.scale(self.current_sprite, scaled_size)

        # สร้าง surface ใหม่สำหรับ alpha
        alpha_sprite = scaled_sprite.copy()
        alpha_sprite.set_alpha(self.alpha)

        # วาด sprite
        screen.blit(alpha_sprite, (screen_x, screen_y))

        # วาดแถบความคืบหน้า
        if 0 < self.capture_progress < 100:
            bar_width = int(scaled_size[0] * 0.8)
            bar_height = int(scaled_size[1] * 0.1)
            bar_x = screen_x + (scaled_size[0] - bar_width) // 2
            bar_y = screen_y + scaled_size[1] + 5

            # พื้นหลังแถบ
            pygame.draw.rect(screen, (100, 100, 100), 
                           (bar_x, bar_y, bar_width, bar_height))
            
            # แถบความคืบหน้า
            progress_width = int(bar_width * (self.capture_progress / 100))
            pygame.draw.rect(screen, (0, 255, 0), 
                           (bar_x, bar_y, progress_width, bar_height))

        # วาดค่าเงินต่อวินาที
        font = pygame.font.Font(None, int(20 * camera.zoom))
        value_text = font.render(f"+{self.value}/s", True, (255, 255, 255))
        text_rect = value_text.get_rect(center=(screen_x + scaled_size[0]//2, 
                                              screen_y - 10))
        screen.blit(value_text, text_rect)

#เดินทาง
class PathFinder:
    def __init__(self, iso_map):
        self.iso_map = iso_map
        self.directions = [(0, 1), (1, 0), (0, -1), (-1, 0),  # แนวตั้งและแนวนอน
                          (1, 1), (-1, -1), (1, -1), (-1, 1)]  # แนวทแยง

    def heuristic(self, a, b):
        """คำนวณระยะห่างแบบ Manhattan distance"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def get_neighbors(self, pos):
        """หา tile ที่สามารถเดินไปได้รอบๆ ตำแหน่งปัจจุบัน"""
        neighbors = []
        for dx, dy in self.directions:
            new_x, new_y = pos[0] + dx, pos[1] + dy
            if (0 <= new_x < self.iso_map.tmx_data.width and 
                0 <= new_y < self.iso_map.tmx_data.height):
                # เช็คว่าสามารถเดินผ่านได้
                if self.is_walkable((new_x, new_y)):
                    neighbors.append((new_x, new_y))
        return neighbors

    def is_walkable(self, pos):
        """เช็คว่า tile นี้สามารถเดินผ่านได้หรือไม่"""
        # ตรวจสอบคุณสมบัติของ tile จาก TMX
        for layer in self.iso_map.tmx_data.visible_layers:
            if hasattr(layer, 'data'):
                gid = layer.data[pos[1]][pos[0]]
                props = self.iso_map.tmx_data.get_tile_properties_by_gid(gid)
                if props and props.get('blocked', False):
                    return False
        return True

    def find_path(self, start, goal):
        """หาเส้นทางโดยใช้ A* algorithm"""
        frontier = PriorityQueue()
        frontier.put((0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}

        while not frontier.empty():
            current = frontier.get()[1]

            if current == goal:
                break

            for next_pos in self.get_neighbors(current):
                new_cost = cost_so_far[current] + 1
                if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                    cost_so_far[next_pos] = new_cost
                    priority = new_cost + self.heuristic(goal, next_pos)
                    frontier.put((priority, next_pos))
                    came_from[next_pos] = current

        # สร้างเส้นทาง
        path = []
        current = goal
        while current is not None:
            path.append(current)
            current = came_from.get(current)
        path.reverse()
        return path if path[0] == start else []

class IsometricMap:
    """จัดการการแสดงผลแผนที่แบบไอโซเมตริกและการแปลงพิกัด"""
    def __init__(self, tmx_path: str, config: GameConfig):
        self.config = config
        self.tmx_data = pytmx.load_pygame(tmx_path)
        self.width = self.tmx_data.width * config.TILE_WIDTH
        self.height = self.tmx_data.height * config.TILE_HEIGHT
        self.selected_tile = None
        self.objects = []  # เพิ่มลิสต์สำหรับเก็บ objects


    def add_object(self, obj):
        self.objects.append(obj)

    def remove_object(self, obj):
        if obj in self.objects:
            self.objects.remove(obj)

    def cart_to_iso(self, x: float, y: float) -> Tuple[float, float]:
        """แปลงพิกัดคาร์ทีเซียนเป็นพิกัดไอโซเมตริก"""
        iso_x = (x - y) * (self.config.TILE_WIDTH // 2)
        iso_y = (x + y) * (self.config.TILE_HEIGHT // 2)
        return iso_x, iso_y

    def iso_to_cart(self, iso_x: float, iso_y: float) -> Tuple[float, float]:
        """แปลงพิกัดไอโซเมตริกเป็นพิกัดคาร์ทีเซียน"""
        cart_x = (iso_x / (self.config.TILE_WIDTH / 2) + iso_y / (self.config.TILE_HEIGHT / 2)) / 2
        cart_y = (iso_y / (self.config.TILE_HEIGHT / 2) - iso_x / (self.config.TILE_WIDTH / 2)) / 2
        return cart_x, cart_y

    def get_tile_coord_from_screen(self, screen_x: float, screen_y: float, camera, zoom: float) -> Tuple[int, int]:
        """แปลงพิกัดบนหน้าจอเป็นพิกัดของกระเบื้อง"""
        # ปรับพิกัดตามตำแหน่งกล้องและระดับการซูม
        adjusted_x = (screen_x - self.config.OFFSET_X - camera.position.x) / zoom
        adjusted_y = (screen_y - self.config.OFFSET_Y - camera.position.y) / zoom
        
        # แปลงเป็นพิกัดคาร์ทีเซียน
        cart_x, cart_y = self.iso_to_cart(adjusted_x, adjusted_y)
        
        # ปัดเศษพิกัดให้เป็นพิกัดของกระเบื้องที่ใกล้ที่สุด
        return int(cart_x), int(cart_y)
    

class Camera:
    """จัดการการเคลื่อนที่ของกล้องและขอบเขตการเคลื่อนที่"""
    def __init__(self, config: GameConfig, map_width: int, map_height: int):
        self.config = config
        self.position = pygame.Vector2(0, 0)
        self.boundary = pygame.Rect(0, 0, map_width, map_height)
        self.zoom = 1.0
        
    def move(self, dx: int, dy: int):
        """ย้ายตำแหน่งของกล้องตามค่าความเปลี่ยนแปลง โดยรักษาขอบเขตการเคลื่อนที่"""
        self.position.x = max(min(self.position.x + dx, self.boundary.width), 
                            -self.boundary.width)
        self.position.y = max(min(self.position.y + dy, self.boundary.height), 
                        -self.boundary.height)
    
    def handle_input(self, keys, events):
        """จัดการอินพุตจากแป้นพิมพ์และล้อเมาส์สำหรับการเคลื่อนที่และการซูมกล้อง"""
        dx = dy = 0
        # ตรวจสอบปุ่มลูกศรเพื่อย้ายกล้อง
        if keys[pygame.K_LEFT]:  dx += self.config.CAMERA_SPEED
        if keys[pygame.K_RIGHT]: dx -= self.config.CAMERA_SPEED
        if keys[pygame.K_UP]:    dy += self.config.CAMERA_SPEED
        if keys[pygame.K_DOWN]:  dy -= self.config.CAMERA_SPEED
        
        # ปรับความเร็วการเคลื่อนที่ตามระดับการซูม
        dx *= self.zoom
        dy *= self.zoom
        self.move(dx, dy)
        
        # ซูมเข้าและออกโดยใช้ล้อเมาส์
        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                self.zoom = max(min(self.zoom + (event.y * self.config.ZOOM_SPEED), 
                                  self.config.MAX_ZOOM), self.config.MIN_ZOOM)

class GameObject:
    def __init__(self, x, y, image, properties=None):
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.image = image
        self.properties = properties or {}
        self.path = []
        self.speed = 1  # ความเร็วในการเคลื่อนที่
        self.moving = False

    def update(self, delta_time):
        """อัพเดทตำแหน่งของ object"""
        if self.path and self.moving:
            next_pos = self.path[0]
            target_x, target_y = next_pos

            # คำนวณระยะทางที่ต้องเคลื่อนที่
            dx = target_x - self.x
            dy = target_y - self.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < 0.1:  # ถึงจุดหมายย่อยแล้ว
                self.x = target_x
                self.y = target_y
                self.path.pop(0)
                if not self.path:  # ถึงจุดหมายสุดท้าย
                    self.moving = False
            else:
                # เคลื่อนที่ไปยังจุดหมายถัดไป
                move_x = (dx / distance) * self.speed * delta_time
                move_y = (dy / distance) * self.speed * delta_time
                self.x += move_x
                self.y += move_y

    def draw(self, screen, iso_map, camera, config):
        iso_x, iso_y = iso_map.cart_to_iso(self.x, self.y)
        screen_x = iso_x * camera.zoom + config.OFFSET_X + camera.position.x
        screen_y = iso_y * camera.zoom + config.OFFSET_Y + camera.position.y

        # ปรับขนาดตามการซูม
        if camera.zoom != 1.0:
            new_width = int(self.image.get_width() * camera.zoom)
            new_height = int(self.image.get_height() * camera.zoom)
            scaled_image = pygame.transform.scale(self.image, (new_width, new_height))
        else:
            scaled_image = self.image

        screen.blit(scaled_image, (screen_x, screen_y))

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
        self.selected_tower = None  # กำหนดค่าเริ่มต้นให้กับ selected_tower
        self.current_action = None  # เก็บ action ปัจจุบัน (move หรือ attack)
        self.last_time = pygame.time.get_ticks()
        self.walkable_tiles = []
        self.capture_points = []  # list เก็บจุดยึดครอง
        self.player_money = [250, 250]  # เงินเริ่มต้น 250 บาทสำหรับผู้เล่น 1 และ 2
        self.generate_capture_points(5)  # สร้างจุดยึดครองเริ่มต้น 5 จุด
        self.current_round = 1  # เริ่มต้นที่รอบ 1
        self.create_tower_button = None  # เพิ่มแอตทริบิวต์นี้
        self.towers = []  # กำหนด self.towers เป็นลิสต์สำหรับเก็บ Tower
        self.tower_created = [False, False]  # สถานะการสร้าง Tower สำหรับผู้เล่น 1 และ 2

        # สร้างเฟรม idle สำหรับยูนิต
        self.unit_idle_spritesheet = pygame.image.load("assets/sprites/unit2_idle_blue.png").convert_alpha()
        self.unit_idle_frames = []
        frame_width = 32  # กว้างของแต่ละเฟรม
        frame_height = 32  # สูงของแต่ละเฟรม
        number_of_frames = 4
        for i in range(number_of_frames):
            frame = self.unit_idle_spritesheet.subsurface((i * frame_width, 0, frame_width, frame_height))
            self.unit_idle_frames.append(frame)

        # สร้างยูนิตสำหรับผู้เล่น 1 และ 2
        self.player_units = []
        self.create_player_units()

        self.current_turn = 0  # 0 สำหรับผู้เล่น 1, 1 สำหรับผู้เล่น 2
        button_width = 120
        button_height = 50
        # กำหนดตำแหน่งของปุ่ม "End Turn"
        self.end_turn_button = pygame.Rect(config.SCREEN_WIDTH - button_width - 10, config.SCREEN_HEIGHT - button_height - 10, button_width, button_height)  # ปุ่ม "End Turn" ที่มุมขวาล่าง
        # กำหนดตำแหน่งของปุ่ม "Move" ให้อยู่ข้างบนปุ่ม "End Turn"
        self.move_button = pygame.Rect(self.end_turn_button.x, self.end_turn_button.y - button_height - 10, button_width, button_height)  # ขนาดของปุ่ม "Move" เท่ากับปุ่ม "End Turn"
        # กำหนดตำแหน่งของปุ่ม "Attack" ให้อยู่เหนือปุ่ม "Move"
        self.attack_button = pygame.Rect(self.move_button.x, self.move_button.y - button_height - 10, button_width, button_height)  # ขนาดของปุ่ม "Attack" เท่ากับปุ่ม "Move"
        # โหลดฟอนต์ใหม่
        self.font = pygame.font.Font("./assets/Fonts/PixgamerRegular-OVD6A.ttf", 28)

    def end_turn(self):
        """จบเทิร์นและรีเซ็ตสถานะ"""
        # เพิ่มเงินให้กับผู้เล่นที่จบเทิร์น 
        self.player_money[self.current_turn] += 100  # เพิ่มเงิน 100 บาทให้กับผู้เล่นที่มีเทิร์น 

        # รีเซ็ตสถานะการทำ action ของยูนิตทุกตัวเมื่อเริ่มเทิร์นใหม่ 
        for unit in self.player_units: 
            unit.reset_action()  # ฟังก์ชันนี้ต้องถูกสร้างในคลาส Unit 

        # เช็คว่าต้องเพิ่มรอบหรือไม่ 
        if self.current_turn == 1:  # ถ้าผู้เล่น 2 จบเทิร์น 
            self.current_round += 1  # เพิ่มรอบ 
            print(f"Round {self.current_round} started.") 

        # รีเซ็ตสถานะของยูนิตที่เลือก 
        if self.selected_unit: 
            self.selected_unit.has_actioned = False  # รีเซ็ตสถานะการทำ action ของยูนิต 
        self.selected_unit = None  # รีเซ็ตยูนิตที่เลือก 
        self.current_action = None  # รีเซ็ต action ปัจจุบัน 

        # รีเซ็ตสถานะการ สร้าง Tower สำหรับผู้เล่น
        self.tower_created = [False, False]  # รีเซ็ตสถานะการสร้าง Tower สำหรับผู้เล่น 1 และ 2 

        # เปลี่ยน turn ระหว่างผู้เล่น 
        self.current_turn = (self.current_turn + 1) % 2  # เปลี่ยน turn ระหว่างผู้เล่น 0 และ 1 
        print(f"Turn changed to player {self.current_turn + 1}.")  # แสดงข้อความเปลี่ยนเทิร์น

    def create_player_units(self):
        """สร้างยูนิตสำหรับผู้เล่น 1 และ 2"""
        # ยูนิตสำหรับผู้เล่น 1
        unit_idle_spritesheet1 = pygame.image.load("assets/sprites/unit1_idle_blue.png").convert_alpha()
        unit_idle_frames1 = self.load_idle_frames(unit_idle_spritesheet1)
        player1_unit1 = Unit(unit_idle_frames=unit_idle_frames1, unit_type=UnitType.SOLDIER, x=5, y=5, owner=0, name="Player 1 Soldier")

        unit_idle_spritesheet1_archer = pygame.image.load("assets/sprites/unit2_idle_blue.png").convert_alpha()
        unit_idle_frames1_archer = self.load_idle_frames(unit_idle_spritesheet1_archer)
        player1_unit2 = Unit(unit_idle_frames=unit_idle_frames1_archer, unit_type=UnitType.ARCHER, x=6, y=5, owner=0, name="Player 1 Archer")

        # ยูนิตสำหรับผู้เล่น 2
        unit_idle_spritesheet2 = pygame.image.load("assets/sprites/unit1_idle_red.png").convert_alpha()
        unit_idle_frames2 = self.load_idle_frames(unit_idle_spritesheet2)
        player2_unit1 = Unit(unit_idle_frames=unit_idle_frames2, unit_type=UnitType.SOLDIER, x=25, y=25, owner=1, name="Player 2 Soldier")

        unit_idle_spritesheet2_archer = pygame.image.load("assets/sprites/unit2_idle_red.png").convert_alpha()
        unit_idle_frames2_archer = self.load_idle_frames(unit_idle_spritesheet2_archer)
        player2_unit2 = Unit(unit_idle_frames=unit_idle_frames2_archer, unit_type=UnitType.ARCHER, x=26, y=25, owner=1, name="Player 2 Archer")

        self.player_units.extend([player1_unit1, player1_unit2, player2_unit1, player2_unit2])

        for unit in self.player_units:
            self.iso_map.add_object(unit)

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
                value = random.randint(5, 15)  # สุ่มค่าเงินที่จะได้รับต่อวินาที
                self.capture_points.append(CapturePoint(x, y, value))
    
    def load_idle_frames(self, spritesheet):
        """โหลดเฟรม idle จาก spritesheet"""
        frames = []
        frame_width = 32
        frame_height = 32
        number_of_frames = 4
        for i in range(number_of_frames):
            frame = spritesheet.subsurface((i * frame_width, 0, frame_width, frame_height))
            frames.append(frame)
        return frames
    
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

    def draw_create_unit_buttons(self, tower):
        """วาดปุ่มสำหรับสร้างยูนิตข้าง Tower"""
        button_width = 100
        button_height = 30
        tower_x = tower.x
        tower_y = tower.y

        # ปุ่มสำหรับสร้าง Soldier
        soldier_button = pygame.Rect(tower_x + 10, tower_y - 40, button_width, button_height)
        pygame.draw.rect(self.screen, (0, 255, 0), soldier_button)  # ปุ่มสีเขียว
        soldier_text = self.debug_font.render("Create Soldier", True, (255, 255, 255))
        self.screen.blit(soldier_text, (soldier_button.x + 5, soldier_button.y + 5))

        # ปุ่มสำหรับสร้าง Archer
        archer_button = pygame.Rect(tower_x + 10, tower_y - 80, button_width, button_height)
        pygame.draw.rect(self.screen, (0, 0, 255), archer_button)  # ปุ่มสีฟ้า
        archer_text = self.debug_font.render("Create Archer", True, (255, 255, 255))
        self.screen.blit(archer_text, (archer_button.x + 5, archer_button.y + 5))

        return soldier_button, archer_button

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
        """อัพเดทจุดยึดครองและรับเงิน"""
        current_time = pygame.time.get_ticks()
        for point in self.capture_points:
            income = point.update(self.iso_map.objects, current_time)
            if point.owner is not None:
                # เพิ่มเงินให้กับผู้เล่นที่เป็นเจ้าของจุดยึดครอง
                self.player_money[point.owner] += income  

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
        pygame.draw.rect(self.screen, (0, 255, 0), self.move_button)  # วาดปุ่มสีเขียว
        text_surface = self.font.render("Move", True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.move_button.center)
        self.screen.blit(text_surface, text_rect)

    def draw_attack_button(self):
        """วาดปุ่ม 'Attack' บนหน้าจอ"""
        pygame.draw.rect(self.screen, (255, 165, 0), self.attack_button)  # ปุ่มสีส้ม
        text_surface = self.font.render("Attack", True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.attack_button.center)
        self.screen.blit(text_surface, text_rect)

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

    def create_unit(self, x, y, unit_type):
        """สร้าง unit ใหม่ที่ตำแหน่งที่กำหนด"""
        new_unit = Unit(self.unit_idle_frames, unit_type, x, y)  # ส่ง x, y และ unit_type ไปยัง Unit
        self.iso_map.add_object(new_unit)
        print(f"{unit_type} created at position: ({x}, {y})")  # แสดงข้อความยืนยันการสร้าง Unit

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
                    new_tower = Tower(x, y, player_id)  # สร้าง Tower ใหม่ที่ตำแหน่ง (x, y) และส่ง player_id 
                    self.towers.append(new_tower)  # เพิ่ม Tower ลงในรายการ Tower 
                    self.tower_created[player_index] = True  # ตั้งค่าสถานะว่าผู้เล่นได้สร้าง Tower แล้ว
                    self.player_money[player_index] -= 100  # หักเงิน 50 บาทจากผู้เล่น
                    print(f"Tower created at position: ({x}, {y}) for Player {player_id}. Cost: 50.")  # แสดงข้อความยืนยันการสร้าง Tower 
                    return True  # คืนค่า True หากสร้าง Tower สำเร็จ 
                else: 
                    print("Cannot create tower: There is already a tower at this position.")  # แสดงข้อความหากมี Tower อยู่แล้ว 
            else: 
                print("Cannot create tower: Tile is out of unit's range.")  # แสดงข้อความหากอยู่นอกระยะ 
        else: 
            print("Cannot create tower at this position.")  # แสดงข้อความหากไม่สามารถสร้าง Tower ได้ 
        return False  # คืนค่า False หากไม่สามารถสร้าง Tower ได้ 

    def add_unit_at_mouse(self):
        """เพิ่ม unit ที่ตำแหน่งเมาส์"""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        tile_x, tile_y = self.iso_map.get_tile_coord_from_screen(
            mouse_x, mouse_y, self.camera, self.camera.zoom)
        
        if 0 <= tile_x < self.iso_map.tmx_data.width and 0 <= tile_y < self.iso_map.tmx_data.height:
            if self.path_finder.is_walkable((tile_x, tile_y)):
                self.create_unit(tile_x, tile_y)

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

        # เพิ่มความสูงของกรอบไฮไลท์
        highlight_width = int(32 * self.camera.zoom)
        highlight_height = int(32 * self.camera.zoom)  # เพิ่มความสูงเป็น 64

        # วาดกรอบสี่เหลี่ยมรอบ unit 
        pygame.draw.rect(self.screen, (255, 255, 0), 
                        (screen_x, screen_y, highlight_width, highlight_height), 2)

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

    def calculate_distance(self, unit_x, unit_y, target_x, target_y):
        """คำนวณระยะห่างระหว่างยูนิตและเป้าหมาย"""
        return math.sqrt((unit_x - target_x) ** 2 + (unit_y - target_y) ** 2)

    def move_unit(self, target_x, target_y):
        unit_info = self.get_info()  # ดึงข้อมูลเกี่ยวกับยูนิต
        move_range = unit_info['move_range']  # รับค่าระยะการเคลื่อนที่

        distance = self.calculate_distance(self.selected_unit.x, self.selected_unit.y, target_x, target_y)
        if distance <= move_range:
            # อัปเดตตำแหน่งของยูนิต
            self.selected_unit.x = target_x
            self.selected_unit.y = target_y

    def attack_enemy(self, enemy):
        unit_info = self.get_info()  # ดึงข้อมูลเกี่ยวกับยูนิต
        attack_range = unit_info['attack_range']  # รับค่าระยะการโจมตี

        distance = self.calculate_distance(self.selected_unit.x, self.selected_unit.y, enemy.x, enemy.y)
        if distance <= attack_range:
            # ดำเนินการโจมตี
            enemy.health -= unit_info['attack']  # ใช้ค่าการโจมตีจาก get_info

    def handle_events(self):
        events = pygame.event.get()
        current_time = pygame.time.get_ticks()
        delta_time = (current_time - self.last_time) / 1000.0
        self.last_time = current_time

        mouse_x, mouse_y = 0, 0

        for event in events:
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                tile_x, tile_y = self.iso_map.get_tile_coord_from_screen(mouse_x, mouse_y, self.camera, self.camera.zoom)

                if event.button == 1:  # คลิกซ้าย
                    if self.move_button.collidepoint(mouse_x, mouse_y):
                        if self.selected_unit is not None:
                            self.current_action = 'move'
                            self.select_action('move')
                        else:
                            print("กรุณาเลือกยูนิตก่อนที่จะเคลื่อนที่.")
                    elif self.attack_button.collidepoint(mouse_x, mouse_y):
                        if self.selected_unit is not None:
                            self.current_action = 'attack'
                            self.select_action('attack')
                        else:
                            print("กรุณาเลือกยูนิตก่อนที่จะโจมตี.")
                    elif self.end_turn_button.collidepoint(mouse_x, mouse_y):
                        self.end_turn()
                    elif self.create_tower_button is not None and self.create_tower_button.collidepoint(mouse_x, mouse_y):
                        if self.selected_unit is not None:
                            self.current_action = 'create_tower'
                            print("กรุณาเลือกตำแหน่งเพื่อสร้าง Tower.")
                        else:
                            print("กรุณาเลือกยูนิตก่อนที่จะสร้าง Tower.")
                    else:
                        found_unit = False
                        if self.selected_unit is not None:
                            self.selected_unit.clicked_this_turn = False

                        # ตรวจสอบว่าคลิกที่ Tower หรือไม่
                        for tower in self.towers:
                            if tower.x == tile_x and tower.y == tile_y:
                                self.selected_tower = tower
                                self.show_create_unit_buttons(tower)  # เรียกฟังก์ชันวาดปุ่มสร้างยูนิต
                                found_unit = True
                                break

                        for unit in self.player_units:
                            if int(unit.x) == tile_x and int(unit.y) == tile_y:
                                if unit.owner == self.current_turn:
                                    self.selected_unit = unit
                                    self.walkable_tiles = self.get_walkable_tiles(unit)
                                    self.selected_unit.clicked_this_turn = True
                                    found_unit = True
                                    self.current_action = None
                                    break

                        if not found_unit:
                            self.selected_unit = None
                            self.walkable_tiles = []

                elif event.button == 3:  # คลิกขวา
                    if self.selected_unit:
                        if self.current_action == 'move':
                            distance = self.calculate_distance(self.selected_unit.x, self.selected_unit.y, tile_x, tile_y)
                            if distance <= self.selected_unit.move_range:
                                self.selected_unit.set_destination(tile_x, tile_y, self.path_finder)
                                self.selected_unit.clicked_this_turn = True
                                self.selected_unit = None
                                self.walkable_tiles = []
                            else:
                                print("ยูนิตนี้ไม่สามารถเดินไปยังจุดนั้นได้ เนื่องจากอยู่นอกระยะการเดิน.")
                        elif self.current_action == 'create_tower':
                            distance = self.calculate_distance(self.selected_unit.x, self.selected_unit.y, tile_x, tile_y)
                            if distance <= self.selected_unit.create_tower_range:
                                self.create_tower(tile_x, tile_y)
                                self.current_action = None
                            else:
                                print("ตำแหน่ง ที่เลือกอยู่นอกระยะการสร้าง Tower.") 

            # อัพเดต objects
            for unit in self.player_units:
                unit.update(delta_time)

            self.camera.handle_input(pygame.key.get_pressed(), events)

        return True

    def show_create_unit_buttons(self, tower):
        """วาดปุ่มสำหรับสร้างยูนิตข้าง Tower"""
        soldier_button, archer_button = self.draw_create_unit_buttons(tower)
        self.soldier_button = soldier_button
        self.archer_button = archer_button

        # ตรวจสอบการคลิกที่ปุ่มสร้างยูนิต
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if self.soldier_button.collidepoint(mouse_x, mouse_y):
            self.create_unit(tower.x, tower.y, UnitType.SOLDIER)
        elif self.archer_button.collidepoint(mouse_x, mouse_y):
            self.create_unit(tower.x, tower.y, UnitType.ARCHER)
        
        # วาดปุ่มบนหน้าจอ
        pygame.draw.rect(self.screen, (0, 255, 0), soldier_button)  # ปุ่มสีเขียว
        soldier_text = self.debug_font.render("Create Soldier", True, (255, 255, 255))
        self.screen.blit(soldier_text, (soldier_button.x + 5, soldier_button.y + 5))

        pygame.draw.rect(self.screen, (0, 0, 255), archer_button)  # ปุ่มสีฟ้า
        archer_text = self.debug_font.render("Create Archer", True, (255, 255, 255))
        self.screen.blit(archer_text, (archer_button.x + 5, archer_button.y + 5))
    
    def select_action(self, action_type):
        """ให้ผู้เล่นเลือกว่าจะทำการ move หรือ attack"""
        if self.selected_unit is None:
            print("กรุณาเลือกยูนิตก่อนที่จะทำการเคลื่อนที่หรือโจมตี.")
            return  # ออกจากฟังก์ชันถ้าไม่มียูนิตที่เลือก

        if action_type == 'move':
            if self.selected_unit.perform_action(action_type):
                self.current_action = 'move'  # ตั้งค่า action ปัจจุบันเป็น move
                print(f"{self.selected_unit.name} is moving.")
                # เพิ่มโค้ดที่เกี่ยวข้องกับการเคลื่อนที่ยูนิตที่เลือก
                # เช่น การกำหนดจุดหมายให้กับยูนิต
            else:
                print(f"{self.selected_unit.name} has already acted this turn.")

        elif action_type == 'attack':
            if self.selected_unit.perform_action(action_type):
                self.current_action = 'attack'  # ตั้งค่า action ปัจจุบันเป็น attack
                print(f"{self.selected_unit.name} is attacking.")
                # เพิ่มโค้ดที่เกี่ยวข้องกับการโจมตียูนิตที่เลือก
                # เช่น การคำนวณความเสียหายและเป้าหมาย
            else:
                print(f"{self.selected_unit.name} has already acted this turn.")
        else:
            print("กรุณาเลือก 'move' หรือ 'attack'.")

    def select_action(self, action_type):
        """ให้ผู้เล่นเลือกว่าจะทำการ move หรือ attack"""
        if self.selected_unit is None:
            print("กรุณาเลือกยูนิตก่อนที่จะทำการเคลื่อนที่หรือโจมตี.")
            return  # ออกจากฟังก์ชันถ้าไม่มียูนิตที่เลือก

        if action_type == 'move':
            if self.selected_unit.perform_action(action_type):
                self.current_action = 'move'  # ตั้งค่า action ปัจจุบันเป็น move
                print(f"{self.selected_unit.name} is moving.")
            else:
                print(f"{self.selected_unit.name} has already acted this turn.")

        elif action_type == 'attack':
            if self.selected_unit.perform_action(action_type):
                self.current_action = 'attack'  # ตั้งค่า action ปัจจุบันเป็น attack
                print(f"{self.selected_unit.name} is attacking.")
            else:
                print(f"{self.selected_unit.name} has already acted this turn.")
        else:
            print("กรุณาเลือก 'move' หรือ 'attack'.")

    def run(self):
        """ลูปหลักของเกม"""
        running = True
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
            
            keys = pygame.key.get_pressed()
            self.camera.handle_input(keys, events)

            # อัปเดตตำแหน่งกล้องและกระเบื้องที่ถูกเลือก
            self.camera.handle_input(pygame.key.get_pressed(), events)
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
            pygame.display.flip()
        
            # รักษาอัตราเฟรมเรต
            self.clock.tick(self.config.FPS)
        
        pygame.quit()

if __name__ == "__main__":
    # เริ่มเกมด้วยการตั้งค่าคอนฟิก
    config = GameConfig()
    game = Game(config)
    game.run()