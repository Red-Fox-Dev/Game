import pygame
import random
from .SpriteSheetLoader import SpriteSheetLoader

class Boss:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 500  # พลังชีวิตของบอส
        self.max_health = 500  # พลังชีวิตสูงสุด
        self.attack_power = 40  # เพิ่มพลังโจมตีของบอส
        self.drop_value = 1200  # เงินที่บอสจะดรอปเมื่อมันตาย
        self.is_dead = False  # สถานะการตาย
        self.unit_idle_frames = self.load_idle_animation()  # โหลดแอนิเมชัน idle
        self.idle_frame_index = 0
        self.idle_frame_duration = 100
        self.last_frame_update_time = pygame.time.get_ticks()
        self.image = self.unit_idle_frames[self.idle_frame_index]  # ใช้เฟรมแรกเป็นภาพเริ่มต้น
        self.font = pygame.font.Font("assets/Fonts/PixgamerRegular-OVD6A.ttf", 20)  # โหลดฟอนต์สำหรับแสดงตัวเลข
        self.move_timer = 0  # ตัวแปรสำหรับจัดการการเคลื่อนไหว
        self.move_duration = 2000  # เวลาในการเคลื่อนที่ (มิลลิวินาที)
        self.direction = random.choice([(0, 1), (1, 0), (0, -1), (-1, 0)])  # ทิศทางเริ่มต้น

    def load_idle_animation(self):
        """โหลดแอนิเมชัน idle สำหรับบอส"""
        return SpriteSheetLoader.load_sprite_sheet("assets/sprites/AmongUsIdle.png", frame_width=32, frame_height=32)

    def draw(self, screen, camera, config):
        # แปลงพิกัด Cartesian เป็นพิกัดไอโซเมตริก
        iso_x, iso_y = self.cart_to_iso(self.x, self.y)
        screen_x = iso_x * camera.zoom + config.OFFSET_X + camera.position.x
        screen_y = iso_y * camera.zoom + config.OFFSET_Y + camera.position.y - (config.TILE_HEIGHT * camera.zoom)

        # อัปเดตเฟรม idle
        self.update_idle_frame()

        scaled_image = pygame.transform.scale(self.image, (int(self.image.get_width() * camera.zoom), int(self.image.get_height() * camera.zoom)))
        screen.blit(scaled_image, (screen_x, screen_y))

        # วาดหลอดเลือด
        self.draw_health_bar(screen, screen_x, screen_y, scaled_image)

    def draw_health_bar(self, screen, x, y, scaled_image):
        """วาดหลอดเลือดของบอส"""
        # พื้นหลังของหลอดเลือด
        bar_width = 50
        bar_height = 5
        bar_x = x + (scaled_image.get_width() - bar_width) // 2
        bar_y = y - 10  # ปรับตำแหน่ง Y ให้สูงขึ้น

        pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))  # สีพื้นหลัง
        health_ratio = self.health / self.max_health
        health_bar_width = int(bar_width * health_ratio)
        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, health_bar_width, bar_height))  # สีหลอดเลือด

        # วาดตัวเลขแสดงพลังชีวิต
        health_text = f"{self.health}/{self.max_health}"
        text_surface = self.font.render(health_text, True, (255, 255, 255))  # สีของตัวเลขเป็นสีขาว
        text_rect = text_surface.get_rect(center=(bar_x + bar_width // 2, bar_y - 15))  # ตำแหน่งของตัวเลขอยู่เหนือหลอดเลือด
        screen.blit(text_surface, text_rect)

    def update_idle_frame(self):
        """อัปเดตเฟรม idle ของบอส"""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_frame_update_time > self.idle_frame_duration:
            self.idle_frame_index = (self.idle_frame_index + 1) % len(self.unit_idle_frames)
            self.image = self.unit_idle_frames[self.idle_frame_index]  # อัปเดตภาพเป็นเฟรมถัดไป
            self.last_frame_update_time = current_time

    def cart_to_iso(self, x, y):
        iso_x = (x - y) * (32 // 2)  # ปรับตามขนาดของ tile
        iso_y = (x + y) * (16 // 2)  # ปรับตามขนาดของ tile
        return iso_x, iso_y

    def update(self):
        """อัปเดตสถานะของบอส"""
        current_time = pygame.time.get_ticks()
        if current_time - self.move_timer > self.move_duration:
            self.move_randomly()  # เรียกใช้ฟังก์ชันเพื่อเคลื่อนที่แบบสุ่ม
            self.move_timer = current_time  # รีเซ็ตตัวจับเวลา

    def move_randomly(self):
        """เคลื่อนที่บอสในทิศทางสุ่ม"""
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # ขึ้น, ขวา, ลง, ซ้าย
        self.direction = random.choice(directions)  # เลือกทิศทางแบบสุ่ม
        new_x = self.x + self.direction[0]
        new_y = self.y + self.direction[1]

        # ตรวจสอบว่าตำแหน่งใหม่อยู่ในขอบเขตของแผนที่
        if self.is_within_bounds(new_x, new_y):
            self.x = new_x
            self.y = new_y
            print(f"Boss moved to position: ({new_x}, {new_y})")  # แสดงข้อความยืนยันการเคลื่อนที่

    def is_within_bounds(self, x, y):
        """ตรวจสอบว่าตำแหน่งอยู่ในขอบเขตของแผนที่"""
        return 0 <= x < self.iso_map.tmx_data.width and 0 <= y < self.iso_map.tmx_data.height

    # ฟังก์ชันสำหรับจัดการการโจมตีของบอส
    def counterattack(self, target):
        if target.current_hp > 0:  # ตรวจสอบว่ามียูนิตที่ยังมีชีวิตอยู่
            target.current_hp -= self.attack_power  # ลดพลังชีวิตของยูนิต
            print(f"Boss counterattacked! {target.name} takes {self.attack_power} damage! Current HP: {target.current_hp}")
            if target.current_hp <= 0:
                print(f"{target.name} has been destroyed!")

    def take_damage(self, damage):
        """ลดพลังชีวิตของบอสเมื่อถูกโจมตี"""
        self.health -= damage
        if self.health <= 0:
            self.health = 0  # ไม่ให้พลังชีวิตต่ำกว่า 0
            self.is_dead = True  # ตั้งค่าสถานะการตายเมื่อพลังชีวิตเป็น 0
            print(f"Boss has been defeated! Dropped {self.drop_value} coins.")
            return self.drop_value  # คืนค่าเงินที่ดรอปเมื่อบอสถูกฆ่า
        print(f"Boss takes {damage} damage! Current health: {self.health}")
        return 0  # คืนค่า 0 ถ้ายังไม่ตาย
    
    def get_rect(self):
        """คืนค่า rect สำหรับ Boss"""
        width = self.image.get_width()  # ความกว้างของภาพบอส
        height = self.image.get_height()  # ความสูงของภาพบอส
        return pygame.Rect(self.x, self.y, width, height)  # คืนค่า rect