import pygame
import sys
from game.game import Game
from game.game_config import GameConfig
from game.menu import GameMenu

if __name__ == "__main__":
    pygame.init()
    
    # สร้าง config และ screen
    config = GameConfig()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("My Game")
    
    # สร้างเมนู
    menu = GameMenu(screen, config)
    
    # รันเมนูและรอการเลือก
    menu_action = menu.run()
    
    if menu_action == 'start':
        # สร้างและรันเกม
        game = Game(config)
        game.run()
    elif menu_action == 'settings':
        print("Settings not implemented yet")
        # TODO: เพิ่มหน้า settings
    elif menu_action == 'quit':
        pygame.quit()
        sys.exit()