import pygame
import math
from .game_object import GameObject
from .SpriteSheetLoader import SpriteSheetLoader
from enum import Enum
from .Boss import Boss
from .monster import Monster

# กำหนดประเภทของยูนิต
class UnitType(Enum):
    SOLDIER = "soldier"
    ARCHER = "archer"
    MAGE = "mage"  # เพิ่มประเภทยูนิตใหม่
    CAVALRY = "cavalry"  # เพิ่มประเภทยูนิต Cavalry

    @staticmethod
    def get_cost(unit_type):
        """ กำหนดค่าใช้จ่ายสำหรับยูนิตประเภทต่าง ๆ """
        costs = {
            UnitType.SOLDIER: 70,
            UnitType.ARCHER: 100,
            UnitType.MAGE: 230,  # กำหนดค่าใช้จ่ายสำหรับ Mage
            UnitType.CAVALRY: 320  # กำหนดค่าใช้จ่ายสำหรับ Cavalry
        }
        return costs.get(unit_type, 0)

class Unit:
    def __init__(self, unit_idle_frames, unit_type, x=0, y=0, owner=None, name="Unit", move_range=5):
        self.unit_idle_frames = unit_idle_frames
        self.unit_type = unit_type
        self.image = self.unit_idle_frames[0]
        self.idle_frame_index = 0
        self.idle_frame_duration = 100
        self.attack_frame_duration = 250
        self.last_frame_update_time = pygame.time.get_ticks()
        self.last_attack_frame_update_time = pygame.time.get_ticks()  # ติดตามเวลาสำหรับการอัปเดตเฟรมการโจมตี
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
        self.attacked_this_turn = False  # เพิ่มตัวแปรนี้เพื่อเก็บสถานะการโจมตี

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
                "attack": 45, 
                "move_range": 3, 
                "attack_range": 1,
                "create_tower_range": 2  # เพิ่มคีย์นี้สำหรับ Soldier
            } 
        elif self.unit_type == UnitType.ARCHER:
            return { 
                "max_hp": 75, 
                "attack": 30, 
                "move_range": 2, 
                "attack_range": 3,
                "create_tower_range": 3  # เพิ่มคีย์นี้สำหรับ Archer
            } 
        elif self.unit_type == UnitType.MAGE:  # เพิ่มเงื่อนไขสำหรับ Mage
            return {
                "max_hp": 50,
                "attack": 70,
                "move_range": 4,
                "attack_range": 5,
                "create_tower_range": 1  # เพิ่มคีย์นี้สำหรับ Mage
            }
        elif self.unit_type == UnitType.CAVALRY:  # เพิ่มเงื่อนไขสำหรับ Cavalry
            return {
                "max_hp": 150,
                "attack": 70,
                "move_range": 6,
                "attack_range": 2,
                "create_tower_range": 2  # เพิ่มคีย์นี้สำหรับ Cavalry
            }
        else:
            return {}
    
    def calculate_distance(self, target_x, target_y):
        """คำนวณระยะห่างระหว่างยูนิตและเป้าหมาย"""
        return math.sqrt((self.x - target_x) ** 2 + (self.y - target_y) ** 2)

    def draw_hp_bar(self, screen, x, y, max_hp, current_hp, zoom):
        """วาด HP Bar สำหรับยูนิต"""
        bar_width = 30 * zoom  # ปรับความกว้างของ HP Bar ให้เล็กลง
        bar_height = 3 * zoom   # ปรับความสูงของ HP Bar ให้เล็กลง
        hp_percentage = current_hp / max_hp  # คำนวณเปอร์เซ็นต์ของ HP

        # วาดกรอบของ HP Bar
        pygame.draw.rect(screen, (255, 0, 0), (x, y, bar_width, bar_height))  # กรอบสีแดง
        # วาด HP ที่เหลือ
        pygame.draw.rect(screen, (0, 255, 0), (x, y, bar_width * hp_percentage, bar_height))  # HP สีเขียว

    def draw_info(self, screen, x, y):
        """วาดข้อมูลยูนิตบนหน้าจอ"""
        font = pygame.font.Font("assets/Fonts/PixgamerRegular-OVD6A.ttf", 20)

        # โหลดภาพพื้นหลังสำหรับข้อมูลยูนิต
        background_image = pygame.image.load("assets/BG/bg_info.png").convert()  # เปลี่ยนเป็น path ของภาพพื้นหลังที่คุณต้องการ
        background_rect = background_image.get_rect()  # รับขนาดของพื้นหลัง
        background_rect.topleft = (x - 5, y + 50 - 5)  # ตั้งตำแหน่งของพื้นหลังให้ตรงกับข้อมูลยูนิต

        # วาดพื้นหลัง
        screen.blit(background_image, background_rect)

        info_surface = font.render(f"Name: {self.name}", True, (255, 255, 255))
        screen.blit(info_surface, (x, y + 50))  # ปรับตำแหน่ง Y ให้ต่ำกว่าข้อความรอบ

        # ขยับ HP ลง 1 บรรทัด
        hp_surface = font.render(f"HP: {self.current_hp}/{self.max_hp}", True, (255, 255, 255))
        screen.blit(hp_surface, (x, y + 50 + 30))  # ปรับตำแหน่ง Y ลง 1 บรรทัด (30 พิกเซล)

        # วาด HP Bar ข้างๆ ข้อมูล HP
        bar_width = 100  # ความกว้างของ HP Bar
        bar_height = 5   # ความสูงของ HP Bar
        hp_bar_x = x + 100  # ปรับตำแหน่ง X ของ HP Bar
        hp_bar_y = y + 50 + 30  # ปรับตำแหน่ง Y ของ HP Bar

        # วาดกรอบของ HP Bar
        pygame.draw.rect(screen, (255, 0, 0), (hp_bar_x, hp_bar_y, bar_width, bar_height))  # กรอบสีแดง
        hp_percentage = self.current_hp / self.max_hp  # คำนวณเปอร์เซ็นต์ของ HP
        # วาด HP ที่เหลือ
        pygame.draw.rect(screen, (0, 255, 0), (hp_bar_x, hp_bar_y, bar_width * hp_percentage, bar_height))  # HP สีเขียว

        # ขยับ Attack ลง 1 บรรทัด
        attack_surface = font.render(f"Attack: {self.attack_value}", True, (255, 255, 255))
        screen.blit(attack_surface, (x, y + 50 + 60))  # ปรับตำแหน่ง Y ลง 1 บรรทัด (30 พิกเซล)

        # ขยับ Move Range ลง 1 บรรทัด
        move_range_surface = font.render(f"Move Range: {self.move_range}", True, (255, 255, 255))
        screen.blit(move_range_surface, (x, y + 50 + 90))  # ปรับตำแหน่ง Y ลง 1 บรรทัด (30 พิกเซล)

        # ขยับ Attack Range ลง 1 บรรทัด
        attack_range_surface = font.render(f"Attack Range: {self.attack_range}", True, (255, 255, 255))
        screen.blit(attack_range_surface, (x, y + 50 + 120))  # ปรับตำแหน่ง Y ลง 1 บรรทัด (30 พิกเซล)
    
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
            current_time = pygame.time.get_ticks()
            if current_time - self.last_attack_frame_update_time > self.attack_frame_duration:
                self.attack_frame_index += 1
                if self.attack_frame_index >= len(self.attack_frames):
                    self.attack_frame_index = 0
                    self.is_attacking = False  # รีเซ็ตสถานะการโจมตี
                self.last_attack_frame_update_time = current_time  # อัปเดตเวลาสำหรับการอัปเดตเฟรมการโจมตี

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
        """โหลดแอนิเมชันการโจมตีตามประเภทของยูนิตและเจ้าของ"""
        if self.unit_type == UnitType.SOLDIER:
            if self.owner == 0:  # ผู้เล่น 1
                return SpriteSheetLoader.load_sprite_sheet("assets/sprites/unit1_attack_blue.png", frame_width=32, frame_height=32)
            else:  # ผู้เล่น 2
                return SpriteSheetLoader.load_sprite_sheet("assets/sprites/unit1_attack_red.png", frame_width=32, frame_height=32)
        elif self.unit_type == UnitType.ARCHER:
            if self.owner == 0:  # ผู้เล่น 1
                return SpriteSheetLoader.load_sprite_sheet("assets/sprites/unit2_attack_blue.png", frame_width=32, frame_height=32)
            else:  # ผู้เล่น 2
                return SpriteSheetLoader.load_sprite_sheet("assets/sprites/unit2_attack_red.png", frame_width=32, frame_height=32)
        elif self.unit_type == UnitType.MAGE:
            if self.owner == 0:  # ผู้เล่น 1
                return SpriteSheetLoader.load_sprite_sheet("assets/sprites/Blue-mage-attack.png", frame_width=32, frame_height=32)
            else:  # ผู้เล่น 2
                return SpriteSheetLoader.load_sprite_sheet("assets/sprites/red-mage-attack.png", frame_width=32, frame_height=32)
        elif self.unit_type == UnitType.CAVALRY:
            if self.owner == 0:  # ผู้เล่น 1
                return SpriteSheetLoader.load_sprite_sheet("assets/sprites/House-blue-attack.png", frame_width=32, frame_height=32)
            else:  # ผู้เล่น 2
                return SpriteSheetLoader.load_sprite_sheet("assets/sprites/House-red-attack.png", frame_width=32, frame_height=32)
        return []
    
    def attack(self, target, game):
        """โจมตีเป้าหมาย"""
        if self.attacked_this_turn:  # ตรวจสอบว่ามีการโจมตีในเทิร์นนี้หรือไม่
            print(f"{self.name} has already attacked this turn.")
            return  # ออกจากฟังก์ชันถ้าโจมตีแล้ว

        if isinstance(target, Boss):
            if self.is_in_range(target):
                target.take_damage(self.attack_value)
                print(f"{self.name} attacked the Boss! Boss's HP is now {target.health}.")
                self.attacked_this_turn = True  # ตั้งค่าสถานะว่าได้โจมตีแล้ว
                self.is_attacking = True  # เริ่มแอนิเมชันการโจมตี
                if target.is_dead:
                    print(f"Boss has been defeated! Dropped {target.drop_value} coins.")
                    game.player_money[self.owner] += target.drop_value
                    game.boss = None
        elif isinstance(target, Monster):
            if self.is_in_range(target):
                dropped_money = target.take_damage(self.attack_value)
                print(f"{self.name} attacked the {target.name}! {target.name}'s HP is now {target.health}.")
                self.attacked_this_turn = True  # ตั้งค่าสถานะว่าได้โจมตีแล้ว
                self.is_attacking = True  # เริ่มแอนิเมชันการโจมตี
                if target.is_dead:
                    print(f"{target.name} has been defeated! Dropped {dropped_money} coins.")
                    game.player_money[self.owner] += dropped_money
                    game.monsters.remove(target)
        else:
            if self.is_in_range(target):
                self.is_attacking = True  # เริ่มแอนิเมชันการโจมตี
                target.current_hp -= self.attack_value
                print(f"{self.name} attacked {target.name}! {target.name}'s HP is now {target.current_hp}.")
                if target.current_hp <= 0:
                    print(f"{target.name} has been destroyed!")
    
    def reset_move_status(self):
        """ฟังก์ชันนี้ใช้ในการรีเซ็ตสถานะการเคลื่อนที่เมื่อเริ่มเทิร์นใหม่"""
        self.moved_this_turn = False

    def is_in_range(self, target):
        """ตรวจสอบว่าเป้าหมายอยู่ในระยะการโจมตีหรือไม่"""
        distance = self.calculate_distance(target.x, target.y)
        return distance <= self.attack_range