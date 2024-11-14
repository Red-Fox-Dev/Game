import pygame
import math

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