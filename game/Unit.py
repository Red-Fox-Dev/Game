import pygame
import math
from .game_object import GameObject
from .SpriteSheetLoader import SpriteSheetLoader
from enum import Enum

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
        self.unit_type = unit_type
        self.image = self.unit_idle_frames[0]
        self.idle_frame_index = 0
        self.idle_frame_duration = 100
        self.last_frame_update_time = pygame.time.get_ticks()
        self.x = x
        self.y = y
        self.path = []
        self.moving = False
        self.speed = 1
        self.owner = owner
        self.name = name
        self.action_text = ""
        self.has_actioned = False
        self.clicked_this_turn = False
        self.move_range = move_range
        self.moved_this_turn = False  # เพิ่มแอตทริบิวต์นี้เพื่อเก็บสถานะการเคลื่อนที่
        
        # เรียกใช้ get_info เพื่อกำหนดคุณสมบัติของยูนิต
        info = self.get_info()
        self.max_hp = info['max_hp']
        self.current_hp = self.max_hp
        self.attack_value = info['attack']
        self.move_range = info['move_range']
        self.attack_range = info['attack_range']
        self.create_tower_range = info['create_tower_range']

        # แอนิเมชันการโจมตี
        self.attack_frames = self.load_attack_animation()  # โหลดแอนิเมชันการโจมตี
        self.attack_frame_index = 0
        self.is_attacking = False
     
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
    
    def calculate_distance(self, target_x, target_y):
        """คำนวณระยะห่างระหว่างยูนิตและเป้าหมาย"""
        return math.sqrt((self.x - target_x) ** 2 + (self.y - target_y) ** 2)

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

        attack_surface = font.render(f"Attack: {self.attack_value}", True, (255, 255, 255)) 
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
        if not self.has_actioned:  # ตรวจสอบว่ายูนิตยังไม่ทำการแอคชั่นในเทิร์นนี้
            self.has_actioned = True  # ตั้งค่าสถานะว่าได้ทำ action ไปแล้ว
            return True  # อนุญาตให้ทำ action
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

        # อัปเดตเฟรมการโจมตี
        if self.is_attacking:
            self.attack_frame_index += 1
            if self.attack_frame_index >= len(self.attack_frames):
                self.attack_frame_index = 0
                self.is_attacking = False  # รีเซ็ตสถานะการโจ มตี

    def draw(self, screen, iso_map, camera, config):
        if self.current_hp <= 0:
            return  # ถ้า HP เป็น 0 ไม่วาดยูนิต

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

        # วาดแอนิเมชันการโจมตีถ้ากำลังโจมตี
        if self.is_attacking:
            attack_frame = self.attack_frames[self.attack_frame_index]
            scaled_attack_frame = pygame.transform.scale(attack_frame, 
        (int(attack_frame.get_width() * camera.zoom), 
         int(attack_frame.get_height() * camera.zoom)))
            screen.blit(scaled_attack_frame, (screen_x, screen_y))

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

    def load_attack_animation(self):
        """โหลดแอนิเมชันการโจมตีตามประเภทของยูนิต"""
        if self.unit_type == UnitType.SOLDIER:
            return SpriteSheetLoader.load_sprite_sheet("assets/sprites/unit1_attack_blue.png", frame_width=32, frame_height=32)
        elif self.unit_type == UnitType.ARCHER:
            return SpriteSheetLoader.load_sprite_sheet("assets/sprites/unit1_attack_red.png", frame_width=32, frame_height=32)
        elif self.unit_type == UnitType.SOLDIER_2:  # สำหรับผู้เล่นที่ 2
            return SpriteSheetLoader.load_sprite_sheet("assets/sprites/unit2_attack_blue.png", frame_width=32, frame_height=32)
        elif self.unit_type == UnitType.ARCHER_2:  # สำหรับผู้เล่นที่ 2
            return SpriteSheetLoader.load_sprite_sheet("assets/sprites/unit2_attack_red.png", frame_width=32, frame_height=32)
        return []
    
    def attack(self, target):
        """โจมตีเป้าหมาย"""
        if self.is_in_range(target):
            self.is_attacking = True  # ตั้งค่าสถานะการโจมตีเป็น True
            target.current_hp -= self.attack_value
            print(f"{self.name} attacked {target.name}! {target.name}'s HP is now {target.current_hp}.")
            if target.current_hp <= 0:
                print(f"{target.name} has been destroyed!")
                # คุณอาจต้องการทำการลบยูนิตนี้จากลิสต์ของยูนิตในเกมที่กำลังทำงานอยู่ที่นี่
    
    def reset_move_status(self):
        """ฟังก์ชันนี้ใช้ในการรีเซ็ตสถานะการเคลื่อนที่เมื่อเริ่มเทิร์นใหม่"""
        self.moved_this_turn = False

    def is_in_range(self, target):
        """ตรวจสอบว่าเป้าหมายอยู่ในระยะการโจมตีหรือไม่"""
        distance = self.calculate_distance(target.x, target.y)
        return distance <= self.attack_range