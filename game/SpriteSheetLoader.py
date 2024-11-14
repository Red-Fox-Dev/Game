import pygame

class SpriteSheetLoader:
    @staticmethod
    def load_sprite_sheet(filename, frame_width=32, frame_height=32, color_key=None):
        spritesheet = pygame.image.load(filename).convert_alpha()
        if color_key:
            spritesheet.set_colorkey(color_key)
        
        frames = []
        sheet_width = spritesheet.get_width()
        sheet_height = spritesheet.get_height()
        
        columns = sheet_width // frame_width
        rows = sheet_height // frame_height
        
        for row in range(rows):
            for col in range(columns):
                frame = spritesheet.subsurface(
                    pygame.Rect(
                        col * frame_width, 
                        row * frame_height, 
                        frame_width, 
                        frame_height
                    )
                )
                frames.append(frame)
        
        return frames