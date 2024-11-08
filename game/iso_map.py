import pygame
import pytmx
from .game_config import GameConfig
from typing import Tuple

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
