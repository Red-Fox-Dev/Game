import pygame
class GameObject:
    def __init__(self, x, y, image, properties=None):
        self.x = x
        self.y = y
        self.image = image
        self.properties = properties or {}
        self.hp = 100  # เพิ่ม HP
        self.max_hp = 100  # กำหนดค่า max HP
        self.selected = False  # ตัวแปรที่จะบอกว่า unit นี้ถูกเลือกหรือไม่

    def draw(self, screen, iso_map, camera, config):
        # แปลงตำแหน่งของยูนิตจากพิกัดคาร์ทิเซียนเป็นไอโซเมตริก
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

        # วาดยูนิต
        screen.blit(scaled_image, (screen_x, screen_y))

        # ถ้ายูนิตถูกเลือก ให้วาด HP bar
        if self.selected:
            self.draw_hp_bar(screen, screen_x, screen_y, camera)

    def take_damage(self, amount):
        """ลด HP ของ unit"""
        self.hp -= amount
        if self.hp <= 0:
            self.destroy()

    def destroy(self):
        """ลบ unit เมื่อ HP เป็นศูนย์"""
        # ลบ unit จากแผนที่
        self.iso_map.remove_object(self)

    def draw_hp_bar(self, screen, x, y, camera):
        """แสดง HP bar"""
        hp_bar_width = 50  # กำหนดความกว้างของ HP bar
        hp_bar_height = 8  # ความสูงของ HP bar
        hp_percentage = self.hp / self.max_hp  # คำนวณเปอร์เซ็นต์ HP

        # วาดพื้นหลังของ HP bar (สีเทา)
        pygame.draw.rect(screen, (100, 100, 100), (x, y - 10, hp_bar_width, hp_bar_height))

        # วาด HP bar ที่มีความยาวตามเปอร์เซ็นต์ของ HP
        pygame.draw.rect(screen, (255, 0, 0), (x, y - 10, hp_bar_width * hp_percentage, hp_bar_height))