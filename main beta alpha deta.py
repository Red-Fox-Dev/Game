import pygame
import sys
from enum import Enum
from typing import List, Tuple, Optional, Dict

# Initialize Pygame
pygame.init()

# Constants
TILE_SIZE = 48
GRID_WIDTH = 16  
GRID_HEIGHT = 16  
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
        color = self.disabled_color if not self.enabled else (self.hover_color if self.is_hovered else self.color)
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
        elif event.type == pygame.MOUSEBUTTONDOWN and self.is_hovered:
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

class BuildingType(Enum):   # class ของสิ่งก่อสร้าง
    TOWER = 1
    BARRACKS = 2

    def get_info(self) -> Dict:
        if self == BuildingType.TOWER:
            return {
                "name": "Tower",
                "description": "Defensive structure",
            }
        else:
            return {
                "name": "Barracks",
                "description": "Training unit structure",
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

class Building:
    def __init__(self, building_type: BuildingType, x: int, y: int, player: int):
        self.building_type = building_type
        self.x = x
        self.y = y
        self.player = player

class GUI:
    def __init__(self, game):
        self.game = game
        self.action_buttons = {
            "move": Button(SCREEN_WIDTH - 190, 20, 180, 40, "Move"),
            "attack": Button(SCREEN_WIDTH - 190, 70, 180, 40, "Attack"),
            "wait": Button(SCREEN_WIDTH - 190, 120, 180, 40, "Wait"),
            "cancel": Button(SCREEN_WIDTH - 190, 170, 180, 40, "Cancel"),
            "end_turn": Button(SCREEN_WIDTH - 190, SCREEN_HEIGHT - 70, 180, 50, "End Turn"),
            "build": Button(SCREEN_WIDTH - 190, 220, 180, 40, "Build")
        }
        self.mode = "normal"
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 32)

    def draw_sidebar(self):
        sidebar_rect = pygame.Rect(SCREEN_WIDTH - SIDEBAR_WIDTH, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(self.game.screen, GRAY, sidebar_rect)
        pygame.draw.line(self.game.screen, WHITE, (SCREEN_WIDTH - SIDEBAR_WIDTH, 0), 
                        (SCREEN_WIDTH - SIDEBAR_WIDTH, SCREEN_HEIGHT), 2)

        for button in self.action_buttons.values():
            button.draw(self.game.screen)

        if self.game.selected_unit:
            unit = self.game.selected_unit
            info = unit.unit_type.get_info()
            title = self.title_font.render(info["name"], True, WHITE)
            self.game.screen.blit(title, (SCREEN_WIDTH - 190, 260))
            stats_text = [
                f"HP: {unit.hp}/{unit.max_hp}",
                f"Attack: {unit.attack}",
                f"Move Range: {unit.move_range}",
                f"Attack Range: {unit.attack_range}",
                f"Status: {'Acted' if unit.moved and unit.attacked else 'Ready'}"
            ]
            for i, text in enumerate(stats_text):
                surface = self.font.render(text, True, WHITE)
                self.game.screen.blit(surface, (SCREEN_WIDTH - 190, 300 + i * 25))

    def draw_game_info(self):
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
            self.action_buttons["build"].enabled = False
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
                elif action == "build":
                    self.mode = "build"
                return True
        return False

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("What war?")
        self.clock = pygame.time.Clock()
        
        self.units: List[Unit] = []
        self.buildings: List[Building] = []
        self.selected_unit: Optional[Unit] = None
        self.current_player = 1
        self.turn = 1
        
        self.gui = GUI(self)

        # Initialize units
        self.units.append(Unit(UnitType.SOLDIER, 0, 1, 1))
        self.units.append(Unit(UnitType.ARCHER, 1, 2, 1))
        self.units.append(Unit(UnitType.SOLDIER, 14, 14, 2))
        self.units.append(Unit(UnitType.ARCHER, 15, 15, 2))

    def get_unit_at(self, x: int, y: int) -> Optional[Unit]:
        for unit in self.units:
            if unit.x == x and unit.y == y:
                return unit
        return None

    def get_building_at(self, x: int, y: int) -> Optional[Building]:
        for building in self.buildings:
            if building.x == x and building.y == y:
                return building
        return None

    def is_valid_move(self, unit: Unit, x: int, y: int) -> bool:
        if x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT:
            return False
        if self.get_unit_at(x, y) or self.get_building_at(x, y):
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

    def build_structure(self, building_type: BuildingType, x: int, y: int):
        if self.get_building_at(x, y) or self.get_unit_at(x, y):
            return False  # Cannot build here
        new_building = Building(building_type, x, y, self.current_player)
        self.buildings.append(new_building)
        return True

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
                                (unit.x * TILE_SIZE + TILE_SIZE // 2, 
                                 unit.y * TILE_SIZE + TILE_SIZE // 2), 10)
            
            # HP bar
            hp_remaining_rect = pygame.Rect(unit.x * TILE_SIZE + 5, 
                                unit.y * TILE_SIZE - 10,
                                (TILE_SIZE - 10) * (unit.hp / unit.max_hp),
                                5)
            hp_lost_rect = pygame.Rect(unit.x * TILE_SIZE + 5 + (TILE_SIZE - 10) * (unit.hp / unit.max_hp), 
                                        unit.y * TILE_SIZE - 10,
                                        (TILE_SIZE - 10) * ((unit.max_hp - unit.hp) / unit.max_hp),
                                        5)

            pygame.draw.rect(self.screen, GREEN, hp_remaining_rect)
            pygame.draw.rect(self.screen, RED, hp_lost_rect)

            # HP text
            hp_text = f"{unit.hp}/{unit.max_hp}"
            hp_surface = pygame.font.Font(None, 20).render(hp_text, True, WHITE)
            text_rect = hp_surface.get_rect(center=(unit.x * TILE_SIZE + TILE_SIZE // 2, unit.y * TILE_SIZE - 15))
            self.screen.blit(hp_surface, text_rect)

    def draw_buildings(self):
        for building in self.buildings:
            color = BLUE if building.player == 1 else RED
            rect = pygame.Rect(building.x * TILE_SIZE, building.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(self.screen, color, rect)

            # Building info
            info = building.building_type.get_info()
            text_surface = pygame.font.Font(None, 20).render(info["name"], True, WHITE)
            text_rect = text_surface.get_rect(center=(building.x * TILE_SIZE + TILE_SIZE // 2, building.y * TILE_SIZE + TILE_SIZE // 2))
            self.screen.blit(text_surface, text_rect)

    def draw_range_overlay(self):
        if not self.selected_unit:
            return
            
        if self.gui.mode == "move":
            for x in range(GRID_WIDTH):
                for y in range(GRID_HEIGHT):
                    if self.is_valid_move(self.selected_unit, x, y):
                        rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        pygame.draw.rect(self.screen, GREEN, rect, 2)
        
        elif self.gui.mode == "attack":
            for unit in self.units:
                if self.is_valid_attack(self.selected_unit, unit):
                    rect = pygame.Rect(unit.x * TILE_SIZE, unit.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    pygame.draw.rect(self.screen, RED, rect, 2)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if self.gui.handle_button_events(event):
                    continue
                    
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x = event.pos[0] // TILE_SIZE
                    y = event.pos[1] // TILE_SIZE

                    if x >= GRID_WIDTH or y >= GRID_HEIGHT:
                        continue

                    clicked_unit = self.get_unit_at(x, y)
                    clicked_building = self.get_building_at(x, y)

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

                    elif self.gui.mode == "build":
                        if self.build_structure(BuildingType.TOWER, x, y):
                            self.gui.mode = "normal" 

            # Update GUI 
            self.gui.update_button_states()

            # Draw everything
            self.screen.fill(BLACK)
            self.draw_grid()
            self.draw_units()
            self.draw_buildings()
            self.draw_range_overlay()
            self.gui.draw_sidebar()
            self.gui.draw_game_info()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
