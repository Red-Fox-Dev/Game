import pygame
import sys
from enum import Enum
from typing import List, Tuple, Optional, Dict

# Initialize Pygame
pygame.init()

# Constants
TILE_SIZE = 64
GRID_WIDTH = 10
GRID_HEIGHT = 8
SIDEBAR_WIDTH = 200
SCREEN_WIDTH = GRID_WIDTH * TILE_SIZE + SIDEBAR_WIDTH
SCREEN_HEIGHT = GRID_HEIGHT * TILE_SIZE + 100
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 100, 0)
LIGHT_GRAY = (200, 200, 200)
TRANSPARENT_GREEN = (0, 255, 0, 128)

class Button:
    def __init__(self, x: int, y: int, width: int, height: int, text: str, enabled: bool = True):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = GRAY
        self.hover_color = DARK_GREEN
        self.disabled_color = LIGHT_GRAY
        self.text_color = WHITE
        self.font = pygame.font.Font(None, 24)
        self.is_hovered = False
        self.enabled = enabled

    def draw(self, screen):
        if not self.enabled:
            color = self.disabled_color
        else:
            color = self.hover_color if self.is_hovered else self.color
        
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event) -> bool:
        if not self.enabled:
            return False
            
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False

class UnitType(Enum):
    SOLDIER = 1
    ARCHER = 2

    def get_info(self) -> Dict:
        if self == UnitType.SOLDIER:
            return {
                "name": "Soldier",
                "description": "Strong melee unit",
                "max_hp": 100,
                "attack": 50,
                "move_range": 3,
                "attack_range": 1
            }
        else:
            return {
                "name": "Archer",
                "description": "Ranged attack unit",
                "max_hp": 75,
                "attack": 40,
                "move_range": 2,
                "attack_range": 3
            }

class Unit:
    def __init__(self, unit_type: UnitType, x: int, y: int, player: int):
        self.unit_type = unit_type
        self.x = x
        self.y = y
        self.player = player
        self.moved = False
        self.attacked = False
        
        info = unit_type.get_info()
        self.max_hp = info["max_hp"]
        self.attack = info["attack"]
        self.move_range = info["move_range"]
        self.attack_range = info["attack_range"]
        self.hp = self.max_hp

class GUI:
    def __init__(self, game):
        self.game = game
        self.action_buttons = {
            "move": Button(SCREEN_WIDTH - 190, 20, 180, 40, "Move"),
            "attack": Button(SCREEN_WIDTH - 190, 70, 180, 40, "Attack"),
            "wait": Button(SCREEN_WIDTH - 190, 120, 180, 40, "Wait"),
            "cancel": Button(SCREEN_WIDTH - 190, 170, 180, 40, "Cancel"),
            "end_turn": Button(SCREEN_WIDTH - 190, SCREEN_HEIGHT - 70, 180, 50, "End Turn")
        }
        self.mode = "normal"  # normal, move, attack
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 32)

    def draw_sidebar(self):
        # Draw sidebar background
        sidebar_rect = pygame.Rect(SCREEN_WIDTH - SIDEBAR_WIDTH, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(self.game.screen, GRAY, sidebar_rect)
        pygame.draw.line(self.game.screen, WHITE, (SCREEN_WIDTH - SIDEBAR_WIDTH, 0), 
                        (SCREEN_WIDTH - SIDEBAR_WIDTH, SCREEN_HEIGHT), 2)

        # Draw action buttons
        for button in self.action_buttons.values():
            button.draw(self.game.screen)

        # Draw unit info if selected
        if self.game.selected_unit:
            unit = self.game.selected_unit
            info = unit.unit_type.get_info()
            
            # Unit title
            title = self.title_font.render(info["name"], True, WHITE)
            self.game.screen.blit(title, (SCREEN_WIDTH - 190, 220))
            
            # Unit stats
            stats_text = [
                f"HP: {unit.hp}/{unit.max_hp}",
                f"Attack: {unit.attack}",
                f"Move Range: {unit.move_range}",
                f"Attack Range: {unit.attack_range}",
                f"Status: {'Acted' if unit.moved and unit.attacked else 'Ready'}"
            ]
            
            for i, text in enumerate(stats_text):
                surface = self.font.render(text, True, WHITE)
                self.game.screen.blit(surface, (SCREEN_WIDTH - 190, 260 + i * 25))

    def draw_game_info(self):
        # Draw current player and turn info
        player_color = BLUE if self.game.current_player == 1 else RED
        turn_text = self.title_font.render(f"Turn {self.game.turn}", True, WHITE)
        player_text = self.title_font.render(f"Player {self.game.current_player}", True, player_color)
        
        self.game.screen.blit(turn_text, (10, SCREEN_HEIGHT - 90))
        self.game.screen.blit(player_text, (10, SCREEN_HEIGHT - 50))

    def update_button_states(self):
        selected = self.game.selected_unit
        
        for button in self.action_buttons.values():
            button.enabled = True
        
        if not selected:
            self.action_buttons["move"].enabled = False
            self.action_buttons["attack"].enabled = False
            self.action_buttons["wait"].enabled = False
            self.action_buttons["cancel"].enabled = False
        else:
            if selected.moved:
                self.action_buttons["move"].enabled = False
            if selected.attacked:
                self.action_buttons["attack"].enabled = False

    def handle_button_events(self, event) -> bool:
        for action, button in self.action_buttons.items():
            if button.handle_event(event):
                if action == "move":
                    self.mode = "move"
                elif action == "attack":
                    self.mode = "attack"
                elif action == "wait":
                    if self.game.selected_unit:
                        self.game.selected_unit.moved = True
                        self.game.selected_unit.attacked = True
                        self.game.selected_unit = None
                    self.mode = "normal"
                elif action == "cancel":
                    self.game.selected_unit = None
                    self.mode = "normal"
                elif action == "end_turn":
                    self.game.end_turn()
                    self.game.selected_unit = None
                    self.mode = "normal"
                return True
        return False

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Strategy Game")
        self.clock = pygame.time.Clock()
        
        self.units: List[Unit] = []
        self.selected_unit: Optional[Unit] = None
        self.current_player = 1
        self.turn = 1
        
        self.gui = GUI(self)
        
        # Initialize some units
        self.units.append(Unit(UnitType.SOLDIER, 0, 0, 1))
        self.units.append(Unit(UnitType.ARCHER, 1, 1, 1))
        self.units.append(Unit(UnitType.SOLDIER, 8, 6, 2))
        self.units.append(Unit(UnitType.ARCHER, 7, 6, 2))

    def get_unit_at(self, x: int, y: int) -> Optional[Unit]:
        for unit in self.units:
            if unit.x == x and unit.y == y:
                return unit
        return None

    def is_valid_move(self, unit: Unit, x: int, y: int) -> bool:
        if x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT:
            return False
        if self.get_unit_at(x, y):
            return False
        distance = abs(unit.x - x) + abs(unit.y - y)
        return distance <= unit.move_range and not unit.moved

    def is_valid_attack(self, unit: Unit, target: Unit) -> bool:
        if unit.attacked or target.player == unit.player:
            return False
        distance = abs(unit.x - target.x) + abs(unit.y - target.y)
        return distance <= unit.attack_range

    def perform_attack(self, attacker: Unit, defender: Unit):
        defender.hp -= attacker.attack
        attacker.attacked = True
        if defender.hp <= 0:
            self.units.remove(defender)

    def end_turn(self):
        self.current_player = 3 - self.current_player
        if self.current_player == 1:
            self.turn += 1
        for unit in self.units:
            unit.moved = False
            unit.attacked = False

    def draw_grid(self):
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self.screen, WHITE, rect, 1)

    def draw_units(self):
        for unit in self.units:
            color = BLUE if unit.player == 1 else RED
            rect = pygame.Rect(unit.x * TILE_SIZE, unit.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(self.screen, color, rect)
            
            if unit.unit_type == UnitType.ARCHER:
                pygame.draw.circle(self.screen, WHITE, 
                                (unit.x * TILE_SIZE + TILE_SIZE//2, 
                                 unit.y * TILE_SIZE + TILE_SIZE//2), 10)
            
            # Draw HP bar
            hp_rect = pygame.Rect(unit.x * TILE_SIZE + 5, 
                                unit.y * TILE_SIZE + TILE_SIZE - 10,
                                (TILE_SIZE - 10) * (unit.hp / unit.max_hp),
                                5)
            pygame.draw.rect(self.screen, GREEN, hp_rect)

    def draw_range_overlay(self):
        if not self.selected_unit:
            return
            
        if self.gui.mode == "move":
            for x in range(GRID_WIDTH):
                for y in range(GRID_HEIGHT):
                    if self.is_valid_move(self.selected_unit, x, y):
                        rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE,
                                        TILE_SIZE, TILE_SIZE)
                        pygame.draw.rect(self.screen, GREEN, rect, 2)
        
        elif self.gui.mode == "attack":
            for unit in self.units:
                if self.is_valid_attack(self.selected_unit, unit):
                    rect = pygame.Rect(unit.x * TILE_SIZE, unit.y * TILE_SIZE,
                                    TILE_SIZE, TILE_SIZE)
                    pygame.draw.rect(self.screen, RED, rect, 2)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                # Handle GUI button events
                if self.gui.handle_button_events(event):
                    continue
                    
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x = event.pos[0] // TILE_SIZE
                    y = event.pos[1] // TILE_SIZE

                    if x >= GRID_WIDTH or y >= GRID_HEIGHT:
                        continue

                    clicked_unit = self.get_unit_at(x, y)

                    if self.gui.mode == "normal":
                        if clicked_unit and clicked_unit.player == self.current_player:
                            self.selected_unit = clicked_unit

                    elif self.gui.mode == "move":
                        if self.is_valid_move(self.selected_unit, x, y):
                            self.selected_unit.x = x
                            self.selected_unit.y = y
                            self.selected_unit.moved = True
                            self.gui.mode = "normal"

                    elif self.gui.mode == "attack":
                        if clicked_unit and self.is_valid_attack(self.selected_unit, clicked_unit):
                            self.perform_attack(self.selected_unit, clicked_unit)
                            self.gui.mode = "normal"

            # Update GUI button states
            self.gui.update_button_states()

            # Draw
            self.screen.fill(BLACK)
            self.draw_grid()
            self.draw_units()
            self.draw_range_overlay()
            self.gui.draw_sidebar()
            self.gui.draw_game_info()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()