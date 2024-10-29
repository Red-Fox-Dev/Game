import pygame
from typing import Dict
from button import Button
from unit import Unit  
from building import BuildingType

# Constants
GRAY = (128, 128, 128)
WHITE = (255, 255, 255)

class GUI:
    def __init__(self, game):
        self.game = game
        self.action_buttons: Dict[str, Button] = {}
        self.create_buttons()
        self.mode = "normal"
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 32)

    def create_buttons(self):
        self.update_button_positions()

    def update_button_positions(self):
        sidebar_width = 200
        self.button_width = 180
        self.button_height = 40
        button_y = 20

        self.action_buttons = {
            "move": Button(self.game.screen_width - sidebar_width + 10, button_y, self.button_width, self.button_height, "Move"),
            "attack": Button(self.game.screen_width - sidebar_width + 10, button_y + 50, self.button_width, self.button_height, "Attack"),
            "wait": Button(self.game.screen_width - sidebar_width + 10, button_y + 100, self.button_width, self.button_height, "Wait"),
            "cancel": Button(self.game.screen_width - sidebar_width + 10, button_y + 150, self.button_width, self.button_height, "Cancel"),
            "end_turn": Button(self.game.screen_width - sidebar_width + 10, self.game.screen_height - 70, self.button_width, 50, "End Turn"),
            "build": Button(self.game.screen_width - sidebar_width + 10, button_y + 200, self.button_width, self.button_height, "Build"),
        }

    def draw_sidebar(self):
        self.update_button_positions()  # Update button positions before drawing
        sidebar_width = 200
        sidebar_rect = pygame.Rect(self.game.screen_width - sidebar_width, 0, sidebar_width, self.game.screen_height)
        pygame.draw.rect(self.game.screen, GRAY, sidebar_rect)

        # Draw buttons
        for action, button in self.action_buttons.items():
            button.draw(self.game.screen)

        if self.game.selected_unit:
            unit = self.game.selected_unit
            info = unit.unit_type.get_info()
            title = self.title_font.render(info["name"], True, WHITE)
            self.game.screen.blit(title, (self.game.screen_width - sidebar_width + 10, 300))  # Adjust position
            stats_text = [
                f"HP: {unit.hp}/{unit.max_hp}",
                f"Attack: {unit.attack}",
                f"Move Range: {unit.move_range}",
                f"Attack Range: {unit.attack_range}",
                f"Status: {'Acted' if unit.moved and unit.attacked else 'Ready'}"
            ]
            for i, text in enumerate(stats_text):
                surface = self.font.render(text, True, WHITE)
                self.game.screen.blit(surface, (self.game.screen_width - sidebar_width + 10, 350 + i * 25))  # Adjust position

    def draw_game_info(self):
        player_color = (0, 0, 255) if self.game.current_player == 1 else (255, 0, 0)
        turn_text = self.title_font.render(f"Turn {self.game.turn}", True, WHITE)
        player_text = self.title_font.render(f"Player {self.game.current_player}", True, player_color)

        turn_x = 10
        turn_y = self.game.screen_height - 90
        player_x = 10
        player_y = self.game.screen_height - 50

        self.game.screen.blit(turn_text, (turn_x, turn_y))
        self.game.screen.blit(player_text, (player_x, player_y))

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

    def handle_button_events(self, event) -> bool:
        for action, button in self.action_buttons.items():
            if button.handle_event(event):  # Assuming Button class has a handle_event method
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
                    if self.game.selected_unit:
                        self.mode = "build"  # Set to build mode
                return True
        return False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.VIDEORESIZE:  
                self.game.update_grid_size()
                self.update_button_positions()

            # Handle button events first
            if self.handle_button_events(event):
                continue  # Skip the rest if a button was pressed

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                x = event.pos[0] // self.game.tile_size
                y = event.pos[1] // self.game.tile_size

                clicked_unit = self.game.get_unit_at(x, y)
                if clicked_unit and clicked_unit.player == self.game.current_player:
                    self.game.selected_unit = clicked_unit
                    self.mode = "build"  # Set to build mode when a unit is selected

                if self.mode == "move" and self.game.selected_unit:
                    if self.game.is_valid_move(self.game.selected_unit, x, y):
                        self.game.selected_unit.x = x
                        self.game.selected_unit.y = y
                        self.game.selected_unit.moved = True
                        self.game.selected_unit = None
                        self.mode = "normal"

                elif self.mode == "attack" and self.game.selected_unit:
                    target_unit = self.game.get_unit_at(x, y)
                    if target_unit and target_unit.player != self.game.selected_unit.player:
                        target_unit.hp -= self.game.selected_unit.attack
                        self.game.selected_unit.attacked = True
                        self.game.selected_unit = None
                        self.mode = "normal"

                elif self.mode == "build" and self.game.selected_unit:
                    self.game.create_building(BuildingType.TOWER, x, y, self.game.current_player)
                    self.game.selected_unit = None  
                    self.mode = "normal"  

        return True
