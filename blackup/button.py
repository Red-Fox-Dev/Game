import pygame

class Button:
    def __init__(self, x, y, width, height, text):
        # สร้างปุ่มที่ตำแหน่ง (x, y) ด้วยขนาดที่กำหนดและข้อความ
        self.rect = pygame.Rect(x, y, width, height)  # กำหนดพื้นที่ของปุ่ม
        self.text = text  # ข้อความที่จะแสดงบนปุ่ม
        self.enabled = True  # สถานะของปุ่ม (เปิดใช้งานหรือไม่)
        self.color = (100, 100, 100)  # สีพื้นฐานของปุ่ม
        self.hover_color = (150, 150, 150)  # สีเมื่อเมาส์อยู่เหนือปุ่ม
        self.current_color = self.color  # สีปัจจุบันของปุ่ม
        self.font = pygame.font.Font(None, 24)  # กำหนดฟอนต์สำหรับข้อความ

    def draw(self, surface):
        # วาดปุ่มบนหน้าจอ
        pygame.draw.rect(surface, self.current_color, self.rect)  # วาดสี่เหลี่ยม (ปุ่ม)
        text_surface = self.font.render(self.text, True, (255, 255, 255))  # สร้างพื้นผิวข้อความ
        text_rect = text_surface.get_rect(center=self.rect.center)  # ปรับตำแหน่งข้อความให้อยู่กลางปุ่ม
        surface.blit(text_surface, text_rect)  # วาดข้อความบนปุ่ม

    def handle_event(self, event):
        # จัดการกับเหตุการณ์ที่เกิดขึ้นกับปุ่ม
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # ตรวจสอบว่ามีการคลิกซ้ายบนปุ่มหรือไม่
            if self.enabled and self.rect.collidepoint(event.pos):
                return True  # คืนค่าจริงถ้าคลิกปุ่ม

        if event.type == pygame.MOUSEMOTION:
            # ตรวจสอบตำแหน่งเมาส์เพื่อเปลี่ยนสีปุ่มเมื่อเมาส์อยู่เหนือ
            if self.rect.collidepoint(event.pos):
                self.current_color = self.hover_color  # เปลี่ยนเป็นสีเมื่อ hover
            else:
                self.current_color = self.color  # กลับไปสีปกติ

        return False  # คืนค่าเท็จถ้าไม่มีการคลิกที่ปุ่ม
