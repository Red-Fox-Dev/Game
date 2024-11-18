import pygame

class SpriteSheetLoader:
    """
    คลาสสำหรับโหลดและแยก sprite sheet เป็นเฟรมแต่ละเฟรม
    """
    @staticmethod
    def load_sprite_sheet(filename, frame_width=32, frame_height=32, color_key=None):
        """
        โหลด sprite sheet และแยกเป็นเฟรมย่อย

        :param filename: ชื่อไฟล์ sprite sheet
        :param frame_width: ความกว้างของแต่ละเฟรม (default: 32 pixels)
        :param frame_height: ความสูงของแต่ละเฟรม (default: 32 pixels)
        :param color_key: สีที่จะทำให้โปร่งใส (transparent)
        :return: list ของเฟรมทั้งหมด
        """
        # โหลดภาพ sprite sheet และแปลงเป็นรูปแบบที่มี alpha channel
        spritesheet = pygame.image.load(filename).convert_alpha()
        
        # ถ้ามีการกำหนด color_key ให้ตั้งค่าสีที่จะทำให้โปร่งใส
        if color_key:
            spritesheet.set_colorkey(color_key)
        
        frames = []  # ลิสต์สำหรับเก็บเฟรมทั้งหมด
        
        # หาขนาดทั้งหมดของ sprite sheet
        sheet_width = spritesheet.get_width()
        sheet_height = spritesheet.get_height()
        
        # คำนวณจำนวนคอลัมน์และแถว
        columns = sheet_width // frame_width   # จำนวนเฟรมในแนวนอน
        rows = sheet_height // frame_height    # จำนวนเฟรมในแนวตั้ง
        
        # วนลูปตัดแต่ละเฟรม
        for row in range(rows):
            for col in range(columns):
                # สร้าง Rect สำหรับตัดเฟรม
                frame = spritesheet.subsurface(
                    pygame.Rect(
                        col * frame_width,     # ตำแหน่ง x เริ่มต้น
                        row * frame_height,    # ตำแหน่ง y เริ่มต้น
                        frame_width,           # ความกว้างของเฟรม
                        frame_height           # ความสูงของเฟรม
                    )
                )
                frames.append(frame)
        
        return frame
