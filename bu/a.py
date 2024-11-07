import pygame
import pytmx
import random
from typing import Tuple, Optional
from dataclasses import dataclass
from queue import PriorityQueue
import math
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

class PathFinder:
    def __init__(self, iso_map):
        self.iso_map = iso_map
        self.directions = [(0, 1), (1, 0), (0, -1), (-1, 0),  # แนวตั้งและแนวนอน
                          (1, 1), (-1, -1), (1, -1), (-1, 1)]  # แนวทแยง

    def heuristic(self, a, b):
        """คำนวณระยะห่างแบบ Manhattan distance"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def get_neighbors(self, pos):
        """หา tile ที่สามารถเดินไปได้รอบๆ ตำแหน่งปัจจุบัน"""
        neighbors = []
        for dx, dy in self.directions:
            new_x, new_y = pos[0] + dx, pos[1] + dy
            if (0 <= new_x < self.iso_map.tmx_data.width and 
                0 <= new_y < self.iso_map.tmx_data.height):
                # เช็คว่าสามารถเดินผ่านได้
                if self.is_walkable((new_x, new_y)):
                    neighbors.append((new_x, new_y))
        return neighbors

    def is_walkable(self, pos):
        """เช็คว่า tile นี้สามารถเดินผ่านได้หรือไม่"""
        # ตรวจสอบคุณสมบัติของ tile จาก TMX
        for layer in self.iso_map.tmx_data.visible_layers:
            if hasattr(layer, 'data'):
                gid = layer.data[pos[1]][pos[0]]
                props = self.iso_map.tmx_data.get_tile_properties_by_gid(gid)
                if props and props.get('blocked', False):
                    return False
        return True

    def find_path(self, start, goal):
        """หาเส้นทางโดยใช้ A* algorithm"""
        frontier = PriorityQueue()
        frontier.put((0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}

        while not frontier.empty():
            current = frontier.get()[1]

            if current == goal:
                break

            for next_pos in self.get_neighbors(current):
                new_cost = cost_so_far[current] + 1
                if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                    cost_so_far[next_pos] = new_cost
                    priority = new_cost + self.heuristic(goal, next_pos)
                    frontier.put((priority, next_pos))
                    came_from[next_pos] = current

        # สร้างเส้นทาง
        path = []
        current = goal
        while current is not None:
            path.append(current)
            current = came_from.get(current)
        path.reverse()
        return path if path[0] == start else []

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
        self.target_x = x
        self.target_y = y
        self.image = image
        self.properties = properties or {}
        self.path = []
        self.speed = 1  # ความเร็วในการเคลื่อนที่
        self.moving = False

    def set_destination(self, x, y, path_finder):
        """กำหนดจุดหมายและหาเส้นทาง"""
        self.path = path_finder.find_path((int(self.x), int(self.y)), (x, y))
        if self.path:
            self.path.pop(0)  # ลบตำแหน่งปัจจุบันออก
            self.moving = True

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
        self.path_finder = PathFinder(self.iso_map)
        self.selected_unit = None
        self.last_time = pygame.time.get_ticks()
        self.unit_image = pygame.image.load("assets/unit2_idle_blue.gif").convert_alpha()  # โหลดภาพ unit
        self.walkable_tiles = []
        self.capture_points = []  # list เก็บจุดยึดครอง
        self.player_money = 0
        self.generate_capture_points(5)  # สร้างจุดยึดครองเริ่มต้น 5 จุด

    def generate_capture_points(self, count):
        """สร้างจุดยึดครองเริ่มต้น"""
        valid_positions = []
        for x in range(self.iso_map.tmx_data.width):
            for y in range(self.iso_map.tmx_data.height):
                if self.path_finder.is_walkable((x, y)):
                    valid_positions.append((x, y))

        if valid_positions:
            positions = random.sample(valid_positions, min(count, len(valid_positions)))
            for x, y in positions:
                value = random.randint(5, 15)  # สุ่มค่าเงินที่จะได้รับต่อวินาที
                self.capture_points.append(CapturePoint(x, y, value))
    def draw_capture_point_info(self):
        """วาดข้อมูลเกี่ยวกับจุดยึดครอง"""
        for point in self.capture_points:
            if point.owner is None:
                status_text = "Not Captured"
            else:
             status_text = "Captured by Player"  # หรือชื่อผู้เล่นถ้ามีการจัดการหลายผู้เล่น

            # คำนวณตำแหน่งการวาดข้อความ
            iso_x, iso_y = self.iso_map.cart_to_iso(point.x, point.y)
            screen_x = iso_x * self.camera.zoom + self.config.OFFSET_X + self.camera.position.x
            screen_y = iso_y * self.camera.zoom + self.config.OFFSET_Y + self.camera.position.y

            # วาดข้อความ
            status_surface = self.debug_font.render(status_text, True, (255, 255, 255))
            self.screen.blit(status_surface, (screen_x, screen_y - 45))  # ปรับตำแหน่งตามต้องการ
    
    def draw_money_display(self):
        """แสดงจำนวนเงินบนหน้าจอ"""
        money_text = self.debug_font.render(f"Money: ${self.player_money}", True, (255, 215, 0))
        self.screen.blit(money_text, (10, self.config.SCREEN_HEIGHT - 40))

        # แสดงจำนวนจุดที่ยึดได้
        captured_points = sum(1 for point in self.capture_points if point.owner is not None)
        points_text = self.debug_font.render(f"Captured Points: {captured_points}/{len(self.capture_points)}", 
                                           True, (255, 215, 0))
        self.screen.blit(points_text, (10, self.config.SCREEN_HEIGHT - 70))

    def update_capture_points(self):
        """อัพเดทจุดยึดครองและรับเงิน"""
        current_time = pygame.time.get_ticks()
        for point in self.capture_points:
            income = point.update(self.iso_map.objects, current_time)
            self.player_money += income

    def get_walkable_tiles(self, unit, max_distance=5):
        """หาช่องที่สามารถเดินไปได้ในระยะที่กำหนด"""
        walkable = []
        start_pos = (int(unit.x), int(unit.y))
        
        # ใช้ BFS เพื่อหาช่องที่เดินได้
        visited = {start_pos}
        queue = [(start_pos, 0)]  # (position, distance)
        
        while queue:
            pos, dist = queue.pop(0)
            if dist <= max_distance:
                walkable.append(pos)
                
                # ตรวจสอบช่องรอบๆ
                for dx, dy in self.path_finder.directions:
                    new_x, new_y = pos[0] + dx, pos[1] + dy
                    new_pos = (new_x, new_y)
                    
                    if (new_pos not in visited and 
                        0 <= new_x < self.iso_map.tmx_data.width and 
                        0 <= new_y < self.iso_map.tmx_data.height and
                        self.path_finder.is_walkable(new_pos)):
                        
                        visited.add(new_pos)
                        queue.append((new_pos, dist + 1))
        
        return walkable

    def draw_walkable_tiles(self):
        """วาด highlight ช่องที่สามารถเดินได้แบบโปร่งแสง"""
        if self.selected_unit and self.walkable_tiles:
            # สร้างเอฟเฟกต์กะพริบโดยใช้ฟังก์ชัน sine
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.005)) * 155 + 100
            highlight_color = (255, 255, 0, int(pulse))  # สีเหลืองที่มีความโปร่งใสเปลี่ยนแปลง

            for tile_x, tile_y in self.walkable_tiles:
                iso_x, iso_y = self.iso_map.cart_to_iso(tile_x, tile_y)
                screen_x = iso_x * self.camera.zoom + self.config.OFFSET_X + self.camera.position.x
                screen_y = iso_y * self.camera.zoom + self.config.OFFSET_Y + self.camera.position.y

                # กำหนดจุดสำหรับวาดกรอบรูปสี่เหลี่ยมข้าวหลามตัด
                points = [
                    (screen_x, screen_y + (self.config.TILE_HEIGHT * self.camera.zoom) // 2),
                    (screen_x + (self.config.TILE_WIDTH * self.camera.zoom) // 2, screen_y),
                    (screen_x + (self.config.TILE_WIDTH * self.camera.zoom), 
                     screen_y + (self.config.TILE_HEIGHT * self.camera.zoom) // 2),
                    (screen_x + (self.config.TILE_WIDTH * self.camera.zoom) // 2, 
                     screen_y + (self.config.TILE_HEIGHT * self.camera.zoom))
                ]

                # สร้าง surface แยกสำหรับการวาดกรอบที่มีความโปร่งใส
                highlight_surface = pygame.Surface((self.config.TILE_WIDTH * self.camera.zoom, 
                                                    self.config.TILE_HEIGHT * self.camera.zoom), 
                                                   pygame.SRCALPHA)

                # วาดกรอบบน highlight_surface
                pygame.draw.lines(highlight_surface, highlight_color, True, 
                                  [(p[0]-screen_x, p[1]-screen_y) for p in points], 2)

                # วาด highlight_surface ลงบนหน้าจอหลัก
                self.screen.blit(highlight_surface, (screen_x, screen_y))


    def create_unit(self, x, y):
        """สร้าง unit ใหม่ที่ตำแหน่งที่กำหนด"""
        new_unit = GameObject(x, y, self.unit_image)
        self.iso_map.add_object(new_unit)
        return new_unit
    
    def add_unit_at_mouse(self):
        """เพิ่ม unit ที่ตำแหน่งเมาส์"""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        tile_x, tile_y = self.iso_map.get_tile_coord_from_screen(
            mouse_x, mouse_y, self.camera, self.camera.zoom)
        
        if 0 <= tile_x < self.iso_map.tmx_data.width and 0 <= tile_y < self.iso_map.tmx_data.height:
            if self.path_finder.is_walkable((tile_x, tile_y)):
                self.create_unit(tile_x, tile_y)

    def draw_map(self):
        """วาดแผนที่ไอโซเมตริกพร้อมการชดเชยจากกล้องและการซูม"""
        # วาดแผนที่พื้นฐาน
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
        
        # วาด highlight ช่องที่เดินได้
        self.draw_walkable_tiles()  

        # วาด objects
        for obj in self.iso_map.objects:
            obj.draw(self.screen, self.iso_map, self.camera, self.config)
        # วาดจุดยึดครอง
        for point in self.capture_points:
            point.draw(self.screen, self.iso_map, self.camera, self.config)
        
        # วาดข้อมูลเกี่ยวกับจุดยึดครอง
        self.draw_capture_point_info()
        # วาด highlight unit ที่เลือก
        if self.selected_unit:
            self.draw_unit_highlight(self.selected_unit)

    def draw_unit_highlight(self, unit):
        """วาดเส้นไฮไลท์รอบ unit ที่ถูกเลือก"""
        iso_x, iso_y = self.iso_map.cart_to_iso(unit.x, unit.y)
        screen_x = iso_x * self.camera.zoom + self.config.OFFSET_X + self.camera.position.x
        screen_y = iso_y * self.camera.zoom + self.config.OFFSET_Y + self.camera.position.y
        
        # กำหนดขนาดของกรอบไฮไลท์
        highlight_size = int(32 * self.camera.zoom)  # สมมติว่า unit มีขนาด 32x32 pixels
        
        # วาดกรอบสี่เหลี่ยมรอบ unit
        pygame.draw.rect(self.screen, (255, 255, 0), 
                         (screen_x, screen_y, highlight_size, highlight_size), 2)

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
        current_time = pygame.time.get_ticks()
        delta_time = (current_time - self.last_time) / 1000.0
        self.last_time = current_time

        for event in events:
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_u:
                    self.add_unit_at_mouse()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                tile_x, tile_y = self.iso_map.get_tile_coord_from_screen(
                    mouse_x, mouse_y, self.camera, self.camera.zoom)

                if event.button == 1:  # คลิกซ้าย
                    # เลือก unit
                    found_unit = False
                    for obj in self.iso_map.objects:
                        if int(obj.x) == tile_x and int(obj.y) == tile_y:
                            self.selected_unit = obj
                            # อัพเดตช่องที่เดินได้
                            self.walkable_tiles = self.get_walkable_tiles(obj)
                            found_unit = True
                            break
                            
                    if not found_unit:
                        self.selected_unit = None
                        self.walkable_tiles = []

                elif event.button == 3 and self.selected_unit:  # คลิกขวา
                    if (tile_x, tile_y) in self.walkable_tiles:  # เช็คว่าเดินไปได้
                        self.selected_unit.set_destination(tile_x, tile_y, self.path_finder)
                        self.walkable_tiles = []  # ล้าง highlight หลังจากสั่งเดิน

        # อัพเดต objects
        for obj in self.iso_map.objects:
            obj.update(delta_time)

        self.camera.handle_input(pygame.key.get_pressed(), events)
        return True
    
    def remove_object_at_mouse(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        tile_x, tile_y = self.iso_map.get_tile_coord_from_screen(
            mouse_x, mouse_y, self.camera, self.camera.zoom)
    
        for obj in self.iso_map.objects:
            if obj.x == tile_x and obj.y == tile_y:
                self.iso_map.remove_object(obj)
                break





    def run(self):
        """ลูปหลักของเกม"""
        running = True
        while running:
            delta_time = self.clock.tick(self.config.FPS) / 1000.0
            running = self.handle_events()
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
            
            
            keys = pygame.key.get_pressed()
            self.camera.handle_input(keys, events)

            # อัปเดตตำแหน่งกล้องและกระเบื้องที่ถูกเลือก
            self.camera.handle_input(pygame.key.get_pressed(), events)
            self.update_selected_tile()
                # อัพเดทสถานะเกม

            self.update_capture_points()
            
            # วาดฉากของเกม
            self.screen.fill((0, 0, 0))
            self.draw_map()
            self.draw_debug_info()
            self.draw_money_display()  # เรียกใช้ฟังก์ชันแสดงจำนวนเงิน
            pygame.display.flip()
            
            # รักษาอัตราเฟรมเรต
            self.clock.tick(self.config.FPS)
        
        pygame.quit()

if __name__ == "__main__":
    # เริ่มเกมด้วยการตั้งค่าคอนฟิก
    config = GameConfig()
    game = Game(config)
    game.run()