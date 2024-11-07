import pygame
import math
from .game_object import GameObject
import time

class Unit(GameObject):
    def __init__(self, frames, x, y):
        super().__init__(x, y, frames[0])
        self.unit_idle_frames = frames  # กำหนด unit_idle_frames
        self.current_frame = 0
        self.x = x
        self.y = y
        self.destination = None
        self.speed = 3.0
        self.path = []
        self.selected = False

        self.last_frame_update_time = time.time()  # กำหนดเวลาตอนเริ่มต้น
        self.idle_frame_duration = 0.2  # ระยะเวลาที่ต้องรอระหว่างการอัพเดตเฟรม (0.2 วินาที)

    def update(self, delta_time):
        """ฟังก์ชันที่ใช้ในการอัพเดตยูนิต"""
        current_time = time.time()  # เวลาปัจจุบัน
        # เช็คว่าเวลาผ่านไปมากกว่าระยะเวลาอัพเดตเฟรมหรือยัง
        if current_time - self.last_frame_update_time > self.idle_frame_duration:
            self.last_frame_update_time = current_time  # อัพเดตเวลาเมื่อเปลี่ยนเฟรม
            self.current_frame = (self.current_frame + 1) % len(self.unit_idle_frames)

    def set_destination(self, x, y, path_finder):
        """กำหนดจุดหมายและหาเส้นทาง"""
        self.path = path_finder.find_path((int(self.x), int(self.y)), (x, y))
        if self.path:
            self.path.pop(0)  # ลบตำแหน่งปัจจุบันออก
            self.moving = True

    def update(self, delta_time):
        """ฟังก์ชันที่ใช้ในการอัพเดตยูนิต"""
        current_time = time.time()
        if current_time - self.last_frame_update_time > self.idle_frame_duration:
            self.last_frame_update_time = current_time
            self.current_frame = (self.current_frame + 1) % len(self.unit_idle_frames)
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

    def draw(self, screen, iso_map, camera, config):
        current_frame = self.unit_idle_frames[self.current_frame]  # ใช้เฟรมปัจจุบัน
        iso_x, iso_y = iso_map.cart_to_iso(self.x, self.y)
        screen_x = iso_x * camera.zoom + config.OFFSET_X + camera.position.x
        screen_y = iso_y * camera.zoom + config.OFFSET_Y + camera.position.y
        screen.blit(current_frame, (screen_x, screen_y))  # แสดงภาพที่เฟรมปัจจุบัน


    def update_game_objects(self, delta_time):
        for obj in self.iso_map.objects:
            obj.update()