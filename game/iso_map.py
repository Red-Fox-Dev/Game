import pytmx
from .game_config import GameConfig
from typing import Tuple

class IsometricMap:
    """
    คลาสสำหรับจัดการแผนที่แบบ Isometric
    - จัดการการแสดงผลแผนที่
    - แปลงพิกัดระหว่างรูปแบบต่างๆ
    - จัดการ objects บนแผนที่
    """
    def __init__(self, tmx_path: str, config: GameConfig):
        """
        กำหนดค่าเริ่มต้นสำหรับแผนที่ Isometric
        
        :param tmx_path: พาธไปยังไฟล์ TMX (Tiled Map XML)
        :param config: object ที่เก็บการตั้งค่าเกม
        """
        self.config = config
        # โหลดข้อมูลแผนที่จากไฟล์ TMX
        self.tmx_data = pytmx.load_pygame(tmx_path)
        # คำนวณขนาดแผนที่ทั้งหมด
        self.width = self.tmx_data.width * config.TILE_WIDTH 
        self.height = self.tmx_data.height * config.TILE_HEIGHT
        # กำหนดค่าเริ่มต้นสำหรับ tile ที่ถูกเลือก
        self.selected_tile = None
        self.objects = []  # เพิ่มลิสต์สำหรับเก็บ objects


    def add_object(self, obj):
        """
        เพิ่ม object ลงในแผนที่
        
        :param obj: object ที่ต้องการเพิ่ม
        """
        self.objects.append(obj)

    def remove_object(self, obj):
        """
        ลบ object ออกจากแผนที่
        
        :param obj: object ที่ต้องการลบ
        """
        if obj in self.objects:
            self.objects.remove(obj)

    def cart_to_iso(self, x: float, y: float) -> Tuple[float, float]:
        """
        แปลงพิกัดจากระบบคาร์ทีเซียน (x,y) เป็นพิกัด Isometric
        
        :param x: พิกัด x ในระบบคาร์ทีเซียน
        :param y: พิกัด y ในระบบคาร์ทีเซียน
        :return: tuple ของพิกัด (x,y) ในระบบ Isometric
        """

        iso_x = (x - y) * (self.config.TILE_WIDTH // 2)
        iso_y = (x + y) * (self.config.TILE_HEIGHT // 2)
        return iso_x, iso_y

    def iso_to_cart(self, iso_x: float, iso_y: float) -> Tuple[float, float]:

        """
        แปลงพิกัดจากระบบ Isometric เป็นพิกัดคาร์ทีเซียน
        
        :param iso_x: พิกัด x ในระบบ Isometric
        :param iso_y: พิกัด y ในระบบ Isometric
        :return: tuple ของพิกัด (x,y) ในระบบคาร์ทีเซียน
        """
        # ใช้สูตรคณิตศาสตร์ในการแปลงพิกัด
        cart_x = (iso_x / (self.config.TILE_WIDTH / 2) + iso_y / (self.config.TILE_HEIGHT / 2)) / 2
        cart_y = (iso_y / (self.config.TILE_HEIGHT / 2) - iso_x / (self.config.TILE_WIDTH / 2)) / 2
        return cart_x, cart_y

    def get_tile_coord_from_screen(self, screen_x: float, screen_y: float, camera, zoom: float) -> Tuple[int, int]:
        """
        แปลงพิกัดจากหน้าจอเป็นพิกัดของ tile บนแผนที่
        
        :param screen_x: พิกัด x บนหน้าจอ
        :param screen_y: พิกัด y บนหน้าจอ
        :param camera: object กล้องที่ใช้ในการมองแผนที่
        :param zoom: ระดับการซูมปัจจุบัน
        :return: tuple ของพิกัด tile (x,y) บนแผนที่
        """
        # ปรับพิกัดตามตำแหน่งกล้องและการซูม
        adjusted_x = (screen_x - self.config.OFFSET_X - camera.position.x) / zoom
        adjusted_y = (screen_y - self.config.OFFSET_Y - camera.position.y) / zoom
        
        # แปลงเป็นพิกัดคาร์ทีเซียน
        cart_x, cart_y = self.iso_to_cart(adjusted_x, adjusted_y)
        
        # ปัดเศษพิกัดให้เป็นพิกัดของกระเบื้องที่ใกล้ที่สุด
        return int(cart_x), int(cart_y)
