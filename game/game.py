import pygame
import pytmx
from .game_config import GameConfig
from .iso_map import IsometricMap
from .camera import Camera
from .game_object import GameObject
from .Unit import Unit
from .Path import PathFinder
from .Point import CapturePoint
import random
import math
from .player import Player

class Game:
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
        self.walkable_tiles = []
        self.capture_points = []  # list เก็บจุดยึดครอง
        self.players = [Player("Player 1", starting_money=250), Player("Player 2", starting_money=250)]
        self.generate_capture_points(5)  # สร้างจุดยึดครองเริ่มต้น 5 จุด
        self.current_player_index = 0  # ใช้เพื่อระบุผู้เล่นปัจจุบัน
        self.current_round = 1  # ตัวแปรสำหรับเก็บรอบปัจจุบัน
        
        self.unit_idle_spritesheet = pygame.image.load("assets/sprites/unit2_idle_blue.png").convert_alpha()
        self.unit_idle_frames = []
        frame_width = 32  # กว้างของแต่ละเฟรม
        frame_height = 32  # สูงของแต่ละเฟรม
        number_of_frames = 4
        for i in range(number_of_frames):
            frame = self.unit_idle_spritesheet.subsurface((i * frame_width, 0, frame_width, frame_height))
            self.unit_idle_frames.append(frame)

        # สร้าง Unit สำหรับ Player 1 และ Player 2
        self.create_starting_units_for_players()

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
    
    def draw_round_display(self):
        """แสดงรอบปัจจุบันที่มุมขวาบนของหน้าจอ"""
        round_text = self.debug_font.render(f"Round: {self.current_round}", True, (255, 215, 0))  # ข้อความสีทอง
        text_rect = round_text.get_rect(topright=(self.config.SCREEN_WIDTH - 10, 10))  # ปรับให้ติดขอบขวาและห่างจากขอบบน 10 pixels
        self.screen.blit(round_text, text_rect)

    def switch_player(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
    
    def get_current_player(self):
        return self.players[self.current_player_index]
    
    def draw_money_display(self):
        """แสดงจำนวนเงินของผู้เล่นปัจจุบันบนหน้าจอ"""
        current_player = self.get_current_player()
        money_text = self.debug_font.render(f"{current_player.name} Money: ${current_player.money}", True, (255, 215, 0))
        self.screen.blit(money_text, (10, self.config.SCREEN_HEIGHT - 40))

        # แสดงจำนวนจุดที่ยึดได้
        captured_points = sum(1 for point in self.capture_points if point.owner == current_player.name)
        points_text = self.debug_font.render(f"Captured Points: {captured_points}/{len(self.capture_points)}", 
                                   True, (255, 215, 0))
        self.screen.blit(points_text, (10, self.config.SCREEN_HEIGHT - 70))

    def update_capture_points(self):
        """อัพเดทจุดยึดครองและรับเงินสำหรับผู้เล่นแต่ละคน"""
        current_time = pygame.time.get_ticks()
        for point in self.capture_points:
            income = point.update(self.iso_map.objects, current_time)
            if point.owner is not None:
                player = next((p for p in self.players if p.name == point.owner), None)
                if player:
                    player.update_money

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

    def end_turn(self):
        """สิ้นสุดเทิร์นของผู้เล่นปัจจุบันและสลับไปยังผู้เล่นถัดไป"""
        current_player = self.get_current_player()
        current_player.money += 100  # เพิ่มเงินให้ผู้เล่น 100 ในแต่ละเทิร์น
        self.switch_player()  # สลับผู้เล่น
        if self.current_player_index == 0:  # หากกลับมาที่ผู้เล่น 1
            self.current_round += 1  # เพิ่มรอบ

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

    def create_starting_units_for_players(self):
        """สร้างยูนิตเริ่มต้น 2 ตัวสำหรับผู้เล่นแต่ละคน"""
        # สร้างยูนิตสำหรับ Player 1
        player_1_start_positions = [(5, 5), (6, 5)]  # ตัวอย่างตำแหน่งเริ่มต้นของ Player 1
        for pos in player_1_start_positions:
            new_unit = self.create_unit_at_position(pos[0], pos[1])
            self.players[0].add_unit(new_unit)

        # สร้างยูนิตสำหรับ Player 2
        player_2_start_positions = [(24, 25), (25, 25)]  # ตัวอย่างตำแหน่งเริ่มต้นของ Player 2
        for pos in player_2_start_positions:
            new_unit = self.create_unit_at_position(pos[0], pos[1])
            self.players[1].add_unit(new_unit)

    def create_unit_at_position(self, x, y):
        """สร้างยูนิตใหม่ที่ตำแหน่งที่กำหนด"""
        new_unit = Unit(self.unit_idle_frames, x, y)  # ส่ง frames ที่มีกรอบภาพไปที่ Unit
        self.iso_map.add_object(new_unit)
        return new_unit
                
    def create_unit(self, x, y):
        """สร้าง unit ใหม่ที่ตำแหน่งที่กำหนด"""
        new_unit = Unit(self.unit_idle_frames, x, y)  # ส่ง x และ y ไปยัง Unit
        self.iso_map.add_object(new_unit)
        return new_unit
    
    def add_unit_at_mouse(self):
        """เพิ่มยูนิตที่ตำแหน่งเมาส์สำหรับผู้เล่นปัจจุบัน"""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        tile_x, tile_y = self.iso_map.get_tile_coord_from_screen(
            mouse_x, mouse_y, self.camera, self.camera.zoom)
        
        if 0 <= tile_x < self.iso_map.tmx_data.width and 0 <= tile_y < self.iso_map.tmx_data.height:
            if self.path_finder.is_walkable((tile_x, tile_y)):
                new_unit = self.create_unit(tile_x, tile_y)
                self.get_current_player().add_unit(new_unit)

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
        
        for obj in self.iso_map.objects:
            if isinstance(obj, Unit):  # ตรวจสอบว่า obj เป็น Unit หรือไม่
                obj.draw(self.screen, self.iso_map, self.camera, self.config)
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
                if event.key == pygame.K_TAB:  # ใช้ปุ่ม TAB เพื่อสลับผู้เล่น
                    self.switch_player()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if event.button == 1:  # คลิกซ้าย
                    # ตรวจสอบว่าคลิกที่ปุ่ม End Turn หรือไม่
                    button_x = self.config.SCREEN_WIDTH - 160  # ปรับให้ตรงกับตำแหน่งปุ่ม
                    button_y = self.config.SCREEN_HEIGHT - 60  # ปรับให้ตรงกับตำแหน่งปุ่ม
                    if (button_x <= mouse_x <= button_x + 150) and (button_y <= mouse_y <= button_y + 50):
                        self.end_turn()  # เรียกใช้ฟังก์ชันสิ้นสุดเทิร์น
                tile_x, tile_y = self.iso_map.get_tile_coord_from_screen(
                   mouse_x, mouse_y, self.camera, self.camera.zoom)

                if event.button == 1:  # คลิกซ้าย
                    # เลือก unit
                    found_unit = False
                    for obj in self.iso_map.objects:
                        if isinstance(obj, Unit) and int(obj.x) == tile_x and int(obj.y) == tile_y:
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
    
    def draw_end_turn_button(self):
        """วาดปุ่ม End Turn ที่มุมขวาล่างของหน้าจอ"""
        button_width = 150
        button_height = 50
        button_x = self.config.SCREEN_WIDTH - button_width - 10  # ห่างจากขอบขวา 10 pixels
        button_y = self.config.SCREEN_HEIGHT - button_height - 10  # ห่างจากขอบล่าง 10 pixels

        # ตรวจสอบว่ามีการเลื่อนเมาส์มาที่ปุ่มหรือไม่
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if (button_x <= mouse_x <= button_x + button_width) and (button_y <= mouse_y <= button_y + button_height):
            button_color = (255, 100, 100)  # เปลี่ยนสีเมื่อเลื่อนเมาส์มาที่ปุ่ม
        else:
            button_color = (255, 0, 0)  # สีปกติ

        # วาดปุ่ม
        pygame.draw.rect(self.screen, button_color, (button_x, button_y, button_width, button_height))  # วาดปุ่ม
        button_text = self.debug_font.render("End Turn", True, (255, 255, 255))  # ข้อความสีขาว
        text_rect = button_text.get_rect(center=(button_x + button_width // 2, button_y + button_height // 2))
        self.screen.blit(button_text, text_rect)

    def run(self):
        """ลูปหลักของเกม"""
        
        running = True
        while running:
            delta_time = self.clock.tick(self.config.FPS) / 1000.0
            running = self.handle_events()
            events = pygame.event.get()

                    # อัพเดตสถานะของยูนิต
            for obj in self.iso_map.objects:
                if isinstance(obj, Unit):  # ตรวจสอบว่า obj เป็น Unit หรือไม่
                    obj.update(delta_time)  # อัปเดตยูนิต

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

            # วาดฉากของเกม
            self.screen.fill((0, 0, 0))
            self.draw_map()
            self.draw_debug_info()
            self.draw_money_display()  # เรียกใช้ฟังก์ชันแสดงจำนวนเงิน
            self.draw_round_display()  # เรียกใช้ฟังก์ชันแสดงผลรอบ
            self.draw_end_turn_button()  # วาดปุ่ม End Turn
            pygame.display.flip()
        
            # รักษาอัตราเฟรมเรต
            self.clock.tick(self.config.FPS)
            
        
        pygame.quit()
