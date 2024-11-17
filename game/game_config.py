from dataclasses import dataclass

@dataclass
class GameConfig:
    """การตั้งค่าคอนฟิกสำหรับเกม"""
    SCREEN_WIDTH: int = 1280
    SCREEN_HEIGHT: int = 720
    TILE_WIDTH: int = 32
    TILE_HEIGHT: int = 16
    FPS: int = 120
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
