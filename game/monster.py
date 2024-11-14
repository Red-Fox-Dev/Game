import pygame
import random
from .SpriteSheetLoader import SpriteSheetLoader 

class Monster:
    def __init__(self, x, y, width, height, monster_type, sprite_paths, tile_size, map_width, map_height):
        self.x = x
        self.y = y
        self.width = width  # เพิ่มแอตทริบิวต์ width
        self.height = height  # เพิ่มแอตทริบิวต์ height
        self.monster_type = monster_type
        self.idle_frames = SpriteSheetLoader.load_sprite_sheet(sprite_paths["idle"])
        self.walk_frames = SpriteSheetLoader.load_sprite_sheet(sprite_paths["walk"])
        self.die_frames = SpriteSheetLoader.load_sprite_sheet(sprite_paths["die"])
        self.current_frame = 0
        self.animation_speed = 5
        self.current_animation = self.idle_frames
        self.animation_time = 0
        self.tile_size = tile_size
        self.health = 100
        self.max_health = 100
        self.is_dead = False
        self.map_width = map_width
        self.map_height = map_height
        self.rect = pygame.Rect(x, y, width, height)  # สร้าง rect จากตำแหน่งและขนาด
        
        # สร้างฟอนต์สำหรับแสดงเลข HP
        self.font = pygame.font.Font(None, 20)  # ใช้ฟอนต์พื้นฐาน ขนาด 20

    def move(self):
        """เคลื่อนที่มอนสเตอร์ในทิศทางสุ่ม"""
        if not self.is_dead:
            dx = random.choice([-1, 0, 1])  # เคลื่อนที่ซ้าย, ไม่เคลื่อนที่, เคลื่อนที่ขวา
            dy = random.choice([-1, 0, 1])  # เคลื่อนที่ขึ้น, ไม่เคลื่อนที่, เคลื่อนที่ลง
            
            new_x = self.x + dx
            new_y = self.y + dy
            
            # ตรวจสอบว่าตำแหน่งใหม่อยู่ในขอบเขตของแผนที่หรือไม่
            if 0 <= new_x < self.map_width and 0 <= new_y < self.map_height:
                self.x = new_x
                self.y = new_y
                self.current_animation = self.walk_frames  # เปลี่ยนไปที่อนิเมชันเดิน

    def take_damage(self, damage):
        if not self.is_dead:
            self.health -= damage
            if self.health <= 0:
                self.health = 0
                self.die()

    def die(self):
        self.is_dead = True
        self.current_animation = self.die_frames
        print(f"{self.monster_type} has died!")

    def is_alive(self):
        return self.health > 0

    def update(self, delta_time):
        if not self.is_dead:
            self.animation_time += delta_time
            if self.animation_time >= self.animation_speed:
                self.current_frame = (self.current_frame + 1) % len(self.current_animation)
                self.animation_time = 0
        else:
            if self.current_frame < len(self.current_animation) - 1:
                self.animation_time += delta_time
                if self.animation_time >= self.animation_speed:
                    self.current_frame += 1
                    self.animation_time = 0

    def draw(self, screen, iso_map, camera, config):
        iso_x, iso_y = iso_map.cart_to_iso(self.x, self.y)
        screen_x = iso_x * camera.zoom + config.OFFSET_X + camera.position.x
        screen_y = iso_y * camera.zoom + config.OFFSET_Y + camera.position.y
        
        # วาดมอนสเตอร์
        screen.blit(self.current_animation[self.current_frame], (screen_x, screen_y))
        
        # วาด HP bar
        self.draw_hp_bar(screen, screen_x, screen_y)

    def draw_hp_bar(self, screen, screen_x, screen_y):
        # คำนวณความกว้างของ HP bar ตาม HP ปัจจุบัน
        hp_bar_width = 50  # ความกว้างสูงสุดของ HP bar
        hp_ratio = self.health / self.max_health  # สัดส่วน HP
        current_hp_width = hp_bar_width * hp_ratio  # ความกว้างปัจจุบันของ HP bar

        # วาดพื้นหลังของ HP bar
        pygame.draw.rect(screen, (255, 0, 0), (screen_x, screen_y - 10, hp_bar_width, 5))  # แถบพื้นหลังสีแดง
        # วาด HP bar
        pygame.draw.rect(screen, (0, 255, 0), (screen_x, screen_y - 10, current_hp_width , 5))  # แถบ HP สีเขียว
        
        # สร้างข้อความ HP
        hp_text = f"{self.health}/{self.max_health}"
        text_surface = self.font.render(hp_text, True, (255, 255, 255))  # ข้อความสีขาว
        text_rect = text_surface.get_rect(center=(screen_x + hp_bar_width / 2, screen_y - 15))  # ตำแหน่งข้อความ
        
        # วาดข้อความ HP บนหน้าจอ
        screen.blit(text_surface, text_rect)