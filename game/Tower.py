import pygame
import math

class Tower:
    def __init__(self, x, y, player_id, image):
        self.x = x  # ตำแหน่ง X ของ Tower
        self.y = y  # ตำแหน่ง Y ของ Tower
        self.health = 100  # ค่าเริ่มต้นสุขภาพของ Tower
        self.attack_power = 10  # พลังโจมตีของ Tower
        self.attack_range = 3  # ระยะการโจมตีของ Tower
        self.player_id = player_id  # ระบุผู้เล่นที่เป็นเจ้าของ Tower
        self.image = image  # ใช้ image ที่ส่งเข้ามาแทนการโหลดใหม่
        self.width = self.image.get_width()  # กำหนดความกว้างจากภาพ
        self.height = self.image.get_height()  # กำหนดความสูงจากภาพ
        self.owner = player_id  # เพิ่มแอตทริบิวต์ owner

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