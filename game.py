import pygame
from unit import Unit, UnitType
from building import Building, BuildingType
from gui import GUI
from typing import List, Optional

# Constants
GRID_WIDTH = 40  # Number of tiles horizontally
GRID_HEIGHT = 24  # Number of tiles vertically
FPS = 60
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (181, 199, 235)
PLAYER_1_BUILDING_COLOR = (100, 100, 255)  # Color for Player 1's tower
PLAYER_2_BUILDING_COLOR = (255, 100, 100)  # Color for Player 2's tower
BUILDING_OUTLINE_COLOR = (0, 0, 128)  # Outline color for buildings

class Game:
    def __init__(self):
        # Set initial screen size
        self.screen_width, self.screen_height = 1900, 1024  # Default window size
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        pygame.display.set_caption("What war?")
        self.clock = pygame.time.Clock()

        # Calculate TILE_SIZE based on screen size
        self.update_grid_size()

        self.units: List[Unit] = []
        self.buildings: List[Building] = []
        self.selected_unit: Optional[Unit] = None
        self.current_player = 1
        self.turn = 1
        
        self.gui = GUI(self)

        # Initialize units
        self.units.append(Unit(UnitType.SOLDIER, 0, 1, 1))
        self.units.append(Unit(UnitType.ARCHER, 1, 2, 1))
        self.units.append(Unit(UnitType.SOLDIER, GRID_WIDTH - 2, GRID_HEIGHT - 2, 2))
        self.units.append(Unit(UnitType.ARCHER, GRID_WIDTH - 1, GRID_HEIGHT - 1, 2))

    def update_grid_size(self):
        # Update tile size based on current screen size
        self.screen_width, self.screen_height = self.screen.get_size()
        self.tile_size = min(self.screen_width // (GRID_WIDTH + 1), self.screen_height // GRID_HEIGHT)

        # Adjust the grid size to fit next to the sidebar
        self.grid_width = GRID_WIDTH * self.tile_size
        self.grid_height = GRID_HEIGHT * self.tile_size

    def get_unit_at(self, x: int, y: int) -> Optional[Unit]:
        for unit in self.units:
            if unit.x == x and unit.y == y:
                return unit
        return None

    def is_valid_move(self, unit: Unit, x: int, y: int) -> bool:
        return abs(unit.x - x) <= unit.move_range and abs(unit.y - y) <= unit.move_range

    def end_turn(self):
        self.current_player = 1 if self.current_player == 2 else 2
        self.turn += 1
        for unit in self.units:
            unit.moved = False
            unit.attacked = False
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.VIDEORESIZE:  # Handle window resize
                self.update_grid_size()
                self.gui.update_button_positions()  # Update button positions

            if self.gui.handle_button_events(event):
                continue  # If a GUI button was clicked, skip the rest.

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                x = event.pos[0] // self.tile_size
                y = event.pos[1] // self.tile_size

                clicked_unit = self.get_unit_at(x, y)
                if clicked_unit and clicked_unit.player == self.current_player:
                    self.selected_unit = clicked_unit

                if self.gui.mode == "move" and self.selected_unit:
                    if self.is_valid_move(self.selected_unit, x, y):
                        self.selected_unit.x = x
                        self.selected_unit.y = y
                        self.selected_unit.moved = True
                        self.selected_unit = None
                        self.gui.mode = "normal"

                elif self.gui.mode == "attack" and self.selected_unit:
                    target_unit = self.get_unit_at(x, y)
                    if target_unit and target_unit.player != self.selected_unit.player:
                        target_unit.hp -= self.selected_unit.attack
                        self.selected_unit.attacked = True
                        self.selected_unit = None
                        self.gui.mode = "normal"

                elif self.gui.mode == "build" and self.selected_unit:
                    self.create_building(BuildingType.TOWER, x, y, self.current_player)
                    self.selected_unit = None  # Deselect unit after building
                    self.gui.mode = "normal"  # Switch back to normal mode

        return True

    def draw_hp_bar(self, unit: Unit):
        hp_ratio = unit.hp / unit.max_hp
        hp_bar_width = self.tile_size
        hp_bar_height = 5  # Height of the HP bar

        # Draw background
        pygame.draw.rect(self.screen, RED, 
                         (unit.x * self.tile_size, unit.y * self.tile_size - hp_bar_height - 2, hp_bar_width, hp_bar_height))

        # Draw HP bar
        pygame.draw.rect(self.screen, GREEN, 
                         (unit.x * self.tile_size, unit.y * self.tile_size - hp_bar_height - 2, hp_bar_width * hp_ratio, hp_bar_height))

        # Draw HP text above the HP bar
        font = pygame.font.Font(None, 24)
        hp_text = f"{unit.hp}/{unit.max_hp}"
        text_surface = font.render(hp_text, True, WHITE)
        
        # Adjust text position to be above the HP bar
        text_rect = text_surface.get_rect(center=(unit.x * self.tile_size + hp_bar_width // 2, 
                                                   unit.y * self.tile_size - hp_bar_height - 10))
        self.screen.blit(text_surface, text_rect)

    def run(self):
        running = True
        while running:
            running = self.handle_events()

            self.screen.fill(BLACK)

            # Draw grid
            for x in range(GRID_WIDTH):
                for y in range(GRID_HEIGHT):
                    rect = pygame.Rect(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
                    pygame.draw.rect(self.screen, WHITE, rect, 1)

            # Draw units and their HP bars
            for unit in self.units:
                color = BLUE if unit.player == 1 else RED
                pygame.draw.rect(self.screen, color, 
                                 (unit.x * self.tile_size, unit.y * self.tile_size, self.tile_size, self.tile_size))
                self.draw_hp_bar(unit)  # Call the function to draw HP bar and text

            # Draw buildings with outlines
            for building in self.buildings:
                building_rect = pygame.Rect(building.x * self.tile_size, building.y * self.tile_size, self.tile_size, self.tile_size)

                # Set building color based on player
                if building.player == 1:
                    building_color = PLAYER_1_BUILDING_COLOR
                else:
                    building_color = PLAYER_2_BUILDING_COLOR

                pygame.draw.rect(self.screen, building_color, building_rect)  # Draw building color
                pygame.draw.rect(self.screen, BUILDING_OUTLINE_COLOR, building_rect, 2)  # Draw building outline
                
                
                font = pygame.font.Font(None, 24)
                text_surface = font.render("Tower", True, WHITE)
                text_rect = text_surface.get_rect(center=(building.x * self.tile_size + self.tile_size // 2, 
                                                           building.y * self.tile_size + self.tile_size // 2))
                self.screen.blit(text_surface, text_rect)

            # Show movement range when selecting a unit
            if self.selected_unit and self.gui.mode == "move":
                move_range = self.selected_unit.move_range
                for dx in range(-move_range, move_range + 1):
                    for dy in range(-move_range, move_range + 1):
                        if abs(dx) + abs(dy) <= move_range:
                            target_x = self.selected_unit.x + dx
                            target_y = self.selected_unit.y + dy
                            if 0 <= target_x < GRID_WIDTH and 0 <= target_y < GRID_HEIGHT:
                                move_rect = pygame.Rect(target_x * self.tile_size, target_y * self.tile_size, self.tile_size, self.tile_size)
                                pygame.draw.rect(self.screen, GREEN, move_rect, 2)  # Draw green outline

            self.gui.draw_sidebar()
            self.gui.draw_game_info()
            self.gui.update_button_states()

            pygame.display.flip()
            self.clock.tick(FPS)
    
    def create_building(self, building_type: BuildingType, x: int, y: int, player: int):
        if not (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT):
            return  

        if self.get_unit_at(x, y) is not None:
            return  

        new_building = Building(building_type, x, y, player)
        self.buildings.append(new_building)  
        print(f"Building created at ({x}, {y}) by player {player}")


