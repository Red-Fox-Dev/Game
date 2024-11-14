import pygame
import pytmx
from typing import Tuple, Optional
from dataclasses import dataclass
# คำสั่งติดตั้ง pytmx: pip install pytmx

@dataclass
class GameConfig:
    """การตั้งค่าคอนฟิกสำหรับเกม"""
    SCREEN_WIDTH: int = 1280
    SCREEN_HEIGHT: int = 720
    TILE_WIDTH: int = 32
    TILE_HEIGHT: int = 16
    FPS: int = 60
    CAMERA_SPEED: int = 5
    MIN_ZOOM: float = 0.5
    MAX_ZOOM: float = 2.0
    ZOOM_SPEED: float = 0.1
    
    @property
    def OFFSET_X(self) -> int:
        # คำนวณตำแหน่งกึ่งกลางของหน้าจอในแกน X
        return self.SCREEN_WIDTH // 2
        
    @property
    def OFFSET_Y(self) -> int:
        # คำนวณตำแหน่งหนึ่งในสี่ของหน้าจอในแกน Y
        return self.SCREEN_HEIGHT // 4

class IsometricMap:
    """จัดการการแสดงผลแผนที่แบบไอโซเมตริกและการแปลงพิกัด"""
    def __init__(self, tmx_path: str, config: GameConfig):
        self.config = config
        self.tmx_data = pytmx.load_pygame(tmx_path)
        self.width = self.tmx_data.width * config.TILE_WIDTH
        self.height = self.tmx_data.height * config.TILE_HEIGHT
        self.selected_tile = None
        self.objects = []  # เพิ่มลิสต์สำหรับเก็บ objects

    def add_object(self, obj):
        self.objects.append(obj)

    def remove_object(self, obj):
        if obj in self.objects:
            self.objects.remove(obj)

    def cart_to_iso(self, x: float, y: float) -> Tuple[float, float]:
        """แปลงพิกัดคาร์ทีเซียนเป็นพิกัดไอโซเมตริก"""
        iso_x = (x - y) * (self.config.TILE_WIDTH // 2)
        iso_y = (x + y) * (self.config.TILE_HEIGHT // 2)
        return iso_x, iso_y

    def iso_to_cart(self, iso_x: float, iso_y: float) -> Tuple[float, float]:
        """แปลงพิกัดไอโซเมตริกเป็นพิกัดคาร์ทีเซียน"""
        cart_x = (iso_x / (self.config.TILE_WIDTH / 2) + iso_y / (self.config.TILE_HEIGHT / 2)) / 2
        cart_y = (iso_y / (self.config.TILE_HEIGHT / 2) - iso_x / (self.config.TILE_WIDTH / 2)) / 2
        return cart_x, cart_y

    def get_tile_coord_from_screen(self, screen_x: float, screen_y: float, camera, zoom: float) -> Tuple[int, int]:
        """แปลงพิกัดบนหน้าจอเป็นพิกัดของกระเบื้อง"""
        # ปรับพิกัดตามตำแหน่งกล้องและระดับการซูม
        adjusted_x = (screen_x - self.config.OFFSET_X - camera.position.x) / zoom
        adjusted_y = (screen_y - self.config.OFFSET_Y - camera.position.y) / zoom
        
        # แปลงเป็นพิกัดคาร์ทีเซียน
        cart_x, cart_y = self.iso_to_cart(adjusted_x, adjusted_y)
        
        # ปัดเศษพิกัดให้เป็นพิกัดของกระเบื้องที่ใกล้ที่สุด
        return int(cart_x), int(cart_y)
    

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

class GameObject:
    def __init__(self, x, y, image, properties=None):
        self.x = x
        self.y = y
        self.image = image
        self.properties = properties or {}

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

class Game:
    """คลาสหลักของเกมที่จัดการลูปของเกมและการแสดงผล"""
    def __init__(self, config: GameConfig):
        pygame.init()
        self.config = config
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.iso_map = IsometricMap("assets/Map1.tmx", config)
        self.camera = Camera(config, self.iso_map.width, self.iso_map.height)
        self.debug_font = pygame.font.Font("assets/Fonts/PixgamerRegular-OVD6A.ttf", 24)

        # สร้าง unit ทั้งสองฝั่งเมื่อเริ่มเกม
        self.spawn_initial_units()

    def spawn_initial_units(self):
        """สร้าง unit หรือวัตถุที่ต้องการเมื่อเริ่มเกม (ฝั่งซ้ายและขวา)"""
        object_image = pygame.image.load("assets/unit2_idle_blue.gif").convert_alpha()
        
        # สร้างตัวละครในฝั่งซ้าย
        left_start_x = 5
        left_start_y = 5
        for i in range(3):  # สร้างตัวละคร 3 ตัวในฝั่งซ้าย
            unit = GameObject(left_start_x + i, left_start_y, object_image)
            self.iso_map.add_object(unit)

        # สร้างตัวละครในฝั่งขวา
        right_start_x = 20
        right_start_y = 5
        for i in range(3):  # สร้างตัวละคร 3 ตัวในฝั่งขวา
            unit = GameObject(right_start_x + i, right_start_y, object_image)
            self.iso_map.add_object(unit)

    def draw_map(self):
        """วาดแผนที่ไอโซเมตริกพร้อมการชดเชยจากกล้องและการซูม"""
        for layer in self.iso_map.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    tile = self.iso_map.tmx_data.get_tile_image_by_gid(gid)
                    if tile:
                        # ปรับขนาดกระเบื้องตามระดับการซูมของกล้อง
                        if self.camera.zoom != 1.0:
                            new_width = int(tile.get_width() * self.camera.zoom)
                            new_height = int(tile.get_height() * self.camera.zoom)
                            tile = pygame.transform.scale(tile, (new_width, new_height))
                        
                        iso_x, iso_y = self.iso_map.cart_to_iso(x, y)
                        screen_x = iso_x * self.camera.zoom + self.config.OFFSET_X + self.camera.position.x
                        screen_y = iso_y * self.camera.zoom + self.config.OFFSET_Y + self.camera.position.y
                        self.screen.blit(tile, (screen_x, screen_y))
                        
                        # เน้นกระเบื้องที่ถูกเลือกหากตรงกับพิกัดปัจจุบัน
                        if (x, y) == self.iso_map.selected_tile:
                            self.draw_tile_highlight(x, y)
        for obj in self.iso_map.objects:
            obj.draw(self.screen, self.iso_map, self.camera, self.config)

    def draw_tile_highlight(self, tile_x: int, tile_y: int):
        """วาดเส้นไฮไลท์สีเหลืองรอบกระเบื้องที่ถูกเลือก"""
        iso_x, iso_y = self.iso_map.cart_to_iso(tile_x, tile_y)
        screen_x = iso_x * self.camera.zoom + self.config.OFFSET_X + self.camera.position.x
        screen_y = iso_y * self.camera.zoom + self.config.OFFSET_Y + self.camera.position.y
        
        # กำหนดมุมของกระเบื้องให้เป็นรูปทรงเพชร
        tile_width = self.config.TILE_WIDTH * self.camera.zoom
        tile_height = self.config.TILE_HEIGHT * self.camera.zoom
        
        points = [
            (screen_x, screen_y + tile_height//2),  # ด้านบน
            (screen_x + tile_width//2, screen_y),   # ด้านขวา
            (screen_x + tile_width, screen_y + tile_height//2),  # ด้านล่าง
            (screen_x + tile_width//2, screen_y + tile_height)   # ด้านซ้าย
        ]
        
        # วาดเส้นรอบไฮไลท์ของกระเบื้อง
        pygame.draw.lines(self.screen, (255, 255, 0), True, points, 2)

    def update_selected_tile(self):
        """อัปเดตกระเบื้องที่ถูกเลือกตามตำแหน่งเมาส์"""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        tile_x, tile_y = self.iso_map.get_tile_coord_from_screen(
            mouse_x, mouse_y, self.camera, self.camera.zoom)
        
        # ตรวจสอบว่าอยู่ในขอบเขตของแผนที่ก่อนอัปเดต
        if (0 <= tile_x < self.iso_map.tmx_data.width and 
            0 <= tile_y < self.iso_map.tmx_data.height):
            self.iso_map.selected_tile = (tile_x, tile_y)

    def draw_debug_info(self):
        """แสดงข้อมูลดีบักบนหน้าจอสำหรับการพัฒนา"""

        debug_info = [
            f"FPS: {int(self.clock.get_fps())}",
            f"Camera: ({int(self.camera.position.x)}, {int(self.camera.position.y)})",
            f"Zoom: {self.camera.zoom:.2f}",
            f"Selected Tile: {self.iso_map.selected_tile}"
        ]
        for i, text in enumerate(debug_info):
            surface = self.debug_font.render(text, True, (255, 255, 255))
            self.screen.blit(surface, (10, 10 + i * 25))

    def handle_events(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
        
        self.camera.handle_input(pygame.key.get_pressed(), events)
        return True
    
    def run(self):
        """ลูปหลักของเกม"""
        running = True
        while running:
            running = self.handle_events()
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
            
            # อัปเดตตำแหน่งกล้องและกระเบื้องที่ถูกเลือก
            self.camera.handle_input(pygame.key.get_pressed(), events)
            self.update_selected_tile()
            
            # วาดฉากของเกม
            self.screen.fill((0, 0, 0))
            self.draw_map()
            self.draw_debug_info()
            pygame.display.flip()
            
            # รักษาอัตราเฟรมเรต
            self.clock.tick(self.config.FPS)
        
        pygame.quit()

if __name__ == "__main__":
    # เริ่มเกมด้วยการตั้งค่าคอนฟิก
    config = GameConfig()
    game = Game(config)
    game.run()
