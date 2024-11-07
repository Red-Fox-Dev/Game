import pygame
import math
class CapturePoint:
    def __init__(self, x, y, value=10):
        self.x = x
        self.y = y
        self.value = value
        self.owner = None
        self.capture_progress = 0
        self.capture_speed = 1
        self.income_interval = 1000
        self.last_income_time = pygame.time.get_ticks()
        
        # โหลด sprites
        self.neutral_sprite = pygame.image.load("assets/crystal_mine_nocap.png").convert_alpha()
        self.captured_sprite = pygame.image.load("assets/bluel_mine_cap.png").convert_alpha()
        self.current_sprite = self.neutral_sprite
        
        # ปรับขนาด sprite (ถ้าจำเป็น)
        self.sprite_size = (32, 32)  # ปรับขนาดตามต้องการ
        self.neutral_sprite = pygame.transform.scale(self.neutral_sprite, self.sprite_size)
        self.captured_sprite = pygame.transform.scale(self.captured_sprite, self.sprite_size)
        
        # เอฟเฟกต์การกะพริบ
        self.pulse_speed = 0.005
        self.alpha = 255

    def update(self, game_objects, current_time):
        unit_on_point = False
        for obj in game_objects:
            if int(obj.x) == self.x and int(obj.y) == self.y:
                unit_on_point = True
                if self.owner != obj:
                    self.capture_progress += self.capture_speed
                    if self.capture_progress >= 100:
                        self.owner = obj
                        self.current_sprite = self.captured_sprite
                        self.capture_progress = 100
                break

        if not unit_on_point:
            self.capture_progress = max(0, self.capture_progress - self.capture_speed)
            if self.capture_progress == 0:
                self.owner = None
                self.current_sprite = self.neutral_sprite

        # อัพเดทค่า alpha สำหรับเอฟเฟกต์กะพริบ
        self.alpha = abs(math.sin(pygame.time.get_ticks() * self.pulse_speed)) * 55 + 200

        if self.owner and current_time - self.last_income_time >= self.income_interval:
            return self.value
            self.last_income_time = current_time
        return 0
    def draw(self, screen, iso_map, camera, config):
        # คำนวณตำแหน่งบนหน้าจอ
        iso_x, iso_y = iso_map.cart_to_iso(self.x, self.y)
        screen_x = iso_x * camera.zoom + config.OFFSET_X + camera.position.x
        screen_y = iso_y * camera.zoom + config.OFFSET_Y + camera.position.y

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

        # วาดค่าเงินต่อวินาที
        font = pygame.font.Font(None, int(20 * camera.zoom))
        value_text = font.render(f"+{self.value}/s", True, (255, 255, 255))
        text_rect = value_text.get_rect(center=(screen_x + scaled_size[0]//2, 
                                              screen_y - 10))
        screen.blit(value_text, text_rect)