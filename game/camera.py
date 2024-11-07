import pygame
from .game_config import GameConfig

class Camera:
    """จัดการการเคลื่อนที่ของกล้องและขอบเขตการเคลื่อนที่"""
    def __init__(self, config: GameConfig, map_width: int, map_height: int):
        self.config = config
        self.position = pygame.Vector2(0, 0)
        self.boundary = pygame.Rect(0, 0, map_width, map_height)
        self.zoom = 1.0
        
    def move(self, dx: int, dy: int):
        """ย้ายตำแหน่งของกล้องตามค่าความเปลี่ยนแปลง โดยรักษาขอบเขตการเคลื่อนที่"""
        self.position.x = max(min(self.position.x + dx, self.boundary.width), 
                            -self.boundary.width)
        self.position.y = max(min(self.position.y + dy, self.boundary.height), 
                        -self.boundary.height)
    
    def handle_input(self, keys, events):
        """จัดการอินพุตจากแป้นพิมพ์และล้อเมาส์สำหรับการเคลื่อนที่และการซูมกล้อง"""
        dx = dy = 0
        # ตรวจสอบปุ่มลูกศรเพื่อย้ายกล้อง
        if keys[pygame.K_LEFT]:  dx += self.config.CAMERA_SPEED
        if keys[pygame.K_RIGHT]: dx -= self.config.CAMERA_SPEED
        if keys[pygame.K_UP]:    dy += self.config.CAMERA_SPEED
        if keys[pygame.K_DOWN]:  dy -= self.config.CAMERA_SPEED
        
        # ปรับความเร็วการเคลื่อนที่ตามระดับการซูม
        dx *= self.zoom
        dy *= self.zoom
        self.move(dx, dy)
        
        # ซูมเข้าและออกโดยใช้ล้อเมาส์
        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                self.zoom = max(min(self.zoom + (event.y * self.config.ZOOM_SPEED), 
                                  self.config.MAX_ZOOM), self.config.MIN_ZOOM)
