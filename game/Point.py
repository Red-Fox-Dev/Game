import pygame
import math
from .Unit import Unit

class CapturePoint:
    def __init__(self, x, y, value=10):
        self.x = x
        self.y = y
        self.value = value  # เงินต่อวินาที
        self.owner = None
        self.value = 100  # ตัวอย่างค่า value ของจุดยึดครอง
        self.has_received_income = False  # สถานะว่าได้รับเงินในเทิร์นนี้หรือยัง
        self.capture_progress = 0
        self.capture_speed = 1
        self.income_interval = 1000  # ทุกๆ 1 วินาที
        self.last_income_time = pygame.time.get_ticks()
        
        # โหลด sprites
        self.neutral_sprite = pygame.image.load("assets/crystal_mine_nocap.png").convert_alpha()
        self.captured_sprite_blue = pygame.image.load("assets/sprites/bluel_mine_cap.png").convert_alpha()  # สำหรับผู้เล่น 1 (สีน้ำเงิน)
        self.captured_sprite_red = pygame.image.load("assets/sprites/red_mine_cap.png").convert_alpha()  # สำหรับผู้เล่น 2 (สีแดง)
        self.current_sprite = self.neutral_sprite
        
        # ปรับขนาด sprite (ถ้าจำเป็น)
        self.sprite_size = (32, 32)  # ปรับขนาดตามต้องการ
        self.neutral_sprite = pygame.transform.scale(self.neutral_sprite, self.sprite_size)
        self.captured_sprite_blue = pygame.transform.scale(self.captured_sprite_blue, self.sprite_size)
        self.captured_sprite_red = pygame.transform.scale(self.captured_sprite_red, self.sprite_size)
        
        # เอฟเฟกต์การกะพริบ
        self.pulse_speed = 0.005
        self.alpha = 255

    def update(self, game_objects, current_time):
        """
        อัปเดตสถานะของจุดยึดครอง
        คืนค่าเงินที่ควรได้รับหากมีเจ้าของ
        """
        unit_on_point = False
        capturing_unit = None

        # ตรวจสอบว่ามียูนิตอยู่บนจุดยึดครองหรือไม่
        for obj in game_objects:
            if isinstance(obj, Unit):  # ตรวจสอบว่า obj เป็น Unit หรือไม่
                if int(obj.x) == self.x and int(obj.y) == self.y:
                    unit_on_point = True
                    capturing_unit = obj
                    break

        # จัดการการยึดครอง
        if unit_on_point:
            # ถ้ายังไม่มีเจ้าของหรือเจ้าของคนปัจจุบันไม่ใช่เจ้าของใหม่
            if self.owner is None or self.owner != capturing_unit.owner:
                self.capture_progress += self.capture_speed
                
                if self.capture_progress >= 100:
                    # ยึดครองสำเร็จ
                    self.owner = capturing_unit.owner
                    
                    # เปลี่ยน sprite ตามผู้เล่นที่ยึดครอง
                    if self.owner == 0:  # ผู้เล่น 1 (สีน้ำเงิน)
                        self.current_sprite = self.captured_sprite_blue
                    else:  # ผู้เล่น 2 (สีแดง)
                        self.current_sprite = self.captured_sprite_red
                    
                    self.capture_progress = 100
        else:
            # ลดความคืบหน้าการยึดครองถ้าไม่มียูนิต
            self.capture_progress = max(0, self.capture_progress - self.capture_speed)
            
            # รีเซ็ตเจ้าของถ้าความคืบหน้าเป็น 0
            if self.capture_progress == 0:
                self.owner = None
                self.current_sprite = self.neutral_sprite

        # อัพเดทค่า alpha สำหรับเอฟเฟกต์กะพริบ 
        self.alpha = abs(math.sin(pygame.time.get_ticks() * self.pulse_speed)) * 55 + 200 

        # ส่งคืนเงินถ้ามีเจ้าของและถึงเวลาอัปเดตต่อเทิร์น
        if self.owner is not None:
            # เพิ่มตัวแปรสำหรับติดตามเวลาที่ผ่านไป
            if current_time - self.last_income_time >= self.income_interval:
                self.last_income_time = current_time
                return self.value  # คืนค่าเงินที่ควรได้รับต่อเทิร์น
        
        return self.value if self.owner is not None else 0

    def draw(self, screen, iso_map, camera, config):
        """วาดจุดยึดครองบนหน้าจอ"""
        # คำนวณตำแหน่งบนหน้าจอ
        iso_x, iso_y = iso_map.cart_to_iso(self.x, self.y)
        screen_x = iso_x * camera.zoom + config.OFFSET_X + camera.position.x
    
        # ปรับตำแหน่ง Y ให้สูงขึ้น
        screen_y = (iso_y * camera.zoom + config.OFFSET_Y + camera.position.y) - (config.TILE_HEIGHT * camera.zoom) - (camera.zoom)

        # สร้าง sprite ที่มีขนาดตามการซูม
        scaled_size = (int(self.sprite_size[0] * camera.zoom), 
                      int(self.sprite_size[1] * camera.zoom))
        scaled_sprite = pygame.transform.scale(self.current_sprite, scaled_size)

        # สร้าง surface ใหม่สำหรับ alpha
        alpha_sprite = scaled_sprite.copy()
        alpha_sprite.set_alpha(self.alpha)

        # วาด sprite
        screen.blit(alpha_sprite, (screen_x, screen_y))

        # วาดแถบความคืบหน้า
        if 0 < self.capture_progress < 100:
            bar_width = int(scaled_size[0] * 0.8)
            bar_height = int(scaled_size[1] * 0.1)
            bar_x = screen_x + (scaled_size[0] - bar_width) // 2
            bar_y = screen_y + scaled_size[1] + 5

            # พื้นหลังแถบ
            pygame.draw.rect(screen, (100, 100, 100), 
                           (bar_x, bar_y, bar_width, bar_height))
            
            # แถบความคืบหน้า
            progress_width = int(bar_width * (self.capture_progress / 100))
            pygame.draw.rect(screen, (0, 255, 0), 
                           (bar_x, bar_y, progress_width, bar_height))