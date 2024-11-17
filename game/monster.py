import pygame
import random
from .SpriteSheetLoader import SpriteSheetLoader 

class Monster:
    def __init__(self, x, y, name="Monster", drop_value=50):  # เพิ่มแอตทริบิวต์ name
        self.x = x 
        self.y = y 
        self.health = 100  # พลังชีวิตของมอนสเตอร์ 
        self.max_health = 100  # พลังชีวิตสูงสุด 
        self.attack_power = 10  # พลังโจมตีของมอนสเตอร์ 
        self.unit_idle_frames = self.load_idle_animation()  # โหลดแอนิเมชัน idle 
        self.idle_frame_index = 0 
        self.idle_frame_duration = 100 
        self.last_frame_update_time = pygame.time.get_ticks() 
        self.image = self.unit_idle_frames[self.idle_frame_index]  # ใช้เฟรมแรกเป็นภาพเริ่มต้น 
        self.font = pygame.font.Font("assets/Fonts/PixgamerRegular-OVD6A.ttf", 20)  # โหลดฟอนต์สำหรับแสดงตัวเลข 
        self.name = name  # กำหนดชื่อของมอนสเตอร์
        self.drop_value = drop_value  # กำหนดค่าเงินที่ดรอป
        self.is_dead = False  # สถานะการตาย
        self.death_frames = self.load_death_animation()  # โหลดแอนิเมชันการตาย
        self.death_frame_index = 0
        self.death_frame_duration = 100  # ระยะเวลาแอนิเมชันการตาย
        self.last_death_frame_update_time = pygame.time.get_ticks()

    def load_idle_animation(self):
        """โหลดแอนิเมชัน idle สำหรับมอนสเตอร์"""
        return SpriteSheetLoader.load_sprite_sheet("assets/Monster/slime_idle.png", frame_width=32, frame_height=32)

    def load_death_animation(self):
        """โหลดแอนิเมชันการตายสำหรับมอนสเตอร์"""
        return SpriteSheetLoader.load_sprite_sheet("assets/Monster/slime_die.png", frame_width=32, frame_height=32)

    def take_damage(self, damage):
        """ลดพลังชีวิตของมอนสเตอร์เมื่อถูกโจมตี"""
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.is_dead = True  # ตั้งค่าสถานะการตายเมื่อพลังชีวิตเป็น 0
            print(f"{self.name} has been defeated! Dropping {self.drop_value} coins.")
            return self.drop_money()  # คืนค่าเงินที่ดรอปเมื่อมอนสเตอร์ถูกฆ่า
        return 0  # คืนค่า 0 ถ้ายังไม่ตาย

    def drop_money(self):
        """คืนค่าเงินที่ดรอปเมื่อมอนสเตอร์ถูกฆ่า"""
        return self.drop_value

    def update(self):
        """อัปเดตสถานะของมอนสเตอร์"""
        # อัปเดตเฟรมการตายถ้ามอนสเตอร์ตาย
        if self.is_dead:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_death_frame_update_time > self.death_frame_duration:
                self.death_frame_index += 1
                if self.death_frame_index >= len(self.death_frames):
                    self.death_frame_index = len(self.death_frames) - 1  # หยุดที่เฟรมสุดท้าย
                self.last_death_frame_update_time = current_time
        else:
            # อัปเดตเฟรม idle ถ้ามอนสเตอร์ยังมีชีวิตอยู่
            self.update_idle_frame()

    def update_idle_frame(self):
        """อัปเดตเฟรม idle ของมอนสเตอร์"""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_frame_update_time > self.idle_frame_duration:
            self.idle_frame_index = (self.idle_frame_index + 1) % len(self.unit_idle_frames)
            self.image = self.unit_idle_frames[self.idle_frame_index]  # อัปเดตภาพเป็นเฟรมถัดไป
            self.last_frame_update_time = current_time

    def draw(self, screen, camera, config):
        if self.is_dead:
            # วาดแอนิเมชันการตาย
            death_frame = self.death_frames[self.death_frame_index]
            scaled_death_frame = pygame.transform.scale(death_frame, (int(death_frame.get_width() * camera.zoom), int(death_frame.get_height() * camera.zoom)))
            iso_x, iso_y = self.cart_to_iso(self.x, self.y)
            screen_x = iso_x * camera.zoom + config.OFFSET_X + camera.position.x
            screen_y = iso_y * camera.zoom + config.OFFSET_Y + camera.position.y - (config.TILE_HEIGHT * camera.zoom)
            screen.blit(scaled_death_frame, (screen_x, screen_y))

            # อัปเดตเฟรมการตาย
            current_time = pygame.time.get_ticks()
            if current_time - self.last_death_frame_update_time > self.death_frame_duration:
                self.death_frame_index += 1
                if self.death_frame_index >= len(self.death_frames):
                    self.death_frame_index = len(self.death_frames) - 1  # หยุดที่เฟรมสุดท้าย
                self.last_death_frame_update_time = current_time
            
            return  # ออกจากฟังก์ชันไม่วาดมอนสเตอร์ถ้ายังตายอยู่

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
        """วาดหลอดเลือดของมอนสเตอร์"""
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

    def cart_to_iso(self, x, y):
        """แปลงพิกัดคาร์ทีเซียนเป็นพิกัดไอโซเมตริก"""
        iso_x = (x - y) * (32 // 2)  # ปรับตามขนาดของ tile
        iso_y = (x + y) * (16 // 2)  # ปรับตามขนาดของ tile
        return iso_x, iso_y