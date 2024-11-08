import pygame
import math
from .game_object import GameObject
import time

class Unit:
    def __init__(self, idle_frames, x=0, y=0, owner=None, max_hp=100):
        self.unit_idle_frames = idle_frames
        self.idle_frame_index = 0
        self.idle_frame_duration = 100  # ระยะเวลาในการแสดงเฟรม (มิลลิวินาที)
        self.last_frame_update_time = pygame.time.get_ticks()
        self.x = x  # กำหนดตำแหน่งเริ่มต้น
        self.y = y  # กำหนดตำแหน่งเริ่มต้น
        self.image = self.unit_idle_frames[0]
        self.path = []
        self.moving = False
        self.speed = 1
        self.owner = owner  # กำหนด owner
        self.max_hp = max_hp  # กำหนดค่า max HP
        self.current_hp = max_hp  # เริ่มต้น HP เท่ากับ max HP

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
            else:
                # เคลื่อนที่ไปยังจุดหมายถัดไป
                move_x = (dx / distance) * self.speed * delta_time
                move_y = (dy / distance) * self.speed * delta_time
                self.x += move_x
                self.y += move_y
        current_time = pygame.time.get_ticks()
        if current_time - self.last_frame_update_time > self.idle_frame_duration:
            self.idle_frame_index = (self.idle_frame_index + 1) % len(self.unit_idle_frames)
            self.last_frame_update_time = current_time

    def draw_hp_bar(self, screen, screen_x, screen_y, camera):
        bar_width = 32 * camera.zoom  # ความกว้างของหลอด HP
        bar_height = 5 * camera.zoom   # ความสูงของหลอด HP
        hp_ratio = self.current_hp / self.max_hp  # คำนวณสัดส่วน HP

        # วาดพื้นหลังของหลอด HP
        pygame.draw.rect(screen, (255, 0, 0), (screen_x, screen_y - 10, bar_width, bar_height))  # สีแดงสำหรับพื้นหลัง

        # วาดหลอด HP
        pygame.draw.rect(screen, (0, 255, 0), (screen_x, screen_y - 10, bar_width * hp_ratio, bar_height))  # สีเขียวสำหรับ HP

        # วาดเลข HP ข้างบนหลอด HP
        font = pygame.font.Font(None, int(20 * camera.zoom))  # กำหนดฟอนต์
        hp_text = f"{int(self.current_hp)}/{int(self.max_hp)}"  # สร้างข้อความ HP
        text_surface = font.render(hp_text, True, (255, 255, 255))  # สร้าง surface ของข้อความ
        text_rect = text_surface.get_rect(center=(screen_x + bar_width / 2, screen_y - 15))  # กำหนดตำแหน่งข้อความให้ตรงกลางหลอด HP
        screen.blit(text_surface, text_rect)  # วาดข้อความลงบนหน้าจอ

    def take_damage(self, amount):
        self.current_hp = max(self.current_hp - amount, 0)  # ลด HP และไม่ให้ต่ำกว่า 0

    def draw(self, screen, iso_map, camera, config):
        iso_x, iso_y = iso_map.cart_to_iso(self.x, self.y)
        screen_x = iso_x * camera.zoom + config.OFFSET_X + camera.position.x
        screen_y = iso_y * camera.zoom + config.OFFSET_Y + camera.position.y

        # วาดเฟรม idle
        current_frame = self.unit_idle_frames[self.idle_frame_index]  # ใช้เฟรมปัจจุบัน
        if isinstance(current_frame, pygame.Surface):  # ตรวจสอบว่ามันเป็น Surface หรือไม่
            scaled_image = pygame.transform.scale(current_frame, (int(current_frame.get_width() * camera.zoom),
                                                                  int(current_frame.get_height() * camera.zoom)))  # ปรับขนาดตามการซูม
            screen.blit(scaled_image, (screen_x, screen_y))

            # วาด HP bar
            self.draw_hp_bar(screen, screen_x, screen_y, camera)

    def update_game_objects(self, delta_time):
        for obj in self.iso_map.objects:
            obj.update()