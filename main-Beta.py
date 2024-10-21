import pygame
import random

class Game:
    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GRASS_COLOR = (100, 200, 100)
    ROAD_COLOR = (150, 150, 150)
    PLAYER1_COLOR = (200, 0, 0)  # Red
    PLAYER2_COLOR = (0, 0, 200)  # Blue
    SELECTED_COLOR = (255, 255, 0)
    MOVE_RANGE_COLOR = (100, 100, 255, 128)  # Semi-transparent blue

    def __init__(self):
        pygame.init()
        self.WINDOW_SIZE = (1024, 768)
        self.TILE_SIZE = 64
        self.GRID_SIZE = (16, 12)
        self.MOVEMENT_RANGE = 2

        self.screen = pygame.display.set_mode(self.WINDOW_SIZE)
        pygame.display.set_caption("Wargroove-like Game")

        self.game_map = [[0 for _ in range(self.GRID_SIZE[0])] for _ in range(self.GRID_SIZE[1])]
        self.units = {1: [], 2: []}
        self.selected_unit = None
        self.current_player = 1

        self.initialize_game()

    def initialize_game(self):
        for row in range(self.GRID_SIZE[1]):
            for col in range(self.GRID_SIZE[0]):
                if random.random() < 0.7:
                    self.game_map[row][col] = 0  # Grass
                else:
                    self.game_map[row][col] = 1  # Road

        for player in [1, 2]:
            for _ in range(5):
                unit_x = random.randint(0, self.GRID_SIZE[0] - 1)
                unit_y = random.randint(0, self.GRID_SIZE[1] - 1)
                self.units[player].append((unit_x, unit_y))

    def get_grid_pos(self, mouse_pos):
        return (mouse_pos[0] // self.TILE_SIZE, mouse_pos[1] // self.TILE_SIZE)

    def get_valid_moves(self, unit):
        valid_moves = []
        for dx in range(-self.MOVEMENT_RANGE, self.MOVEMENT_RANGE + 1):
            for dy in range(-self.MOVEMENT_RANGE, self.MOVEMENT_RANGE + 1):
                if abs(dx) + abs(dy) <= self.MOVEMENT_RANGE:
                    new_x, new_y = unit[0] + dx, unit[1] + dy
                    if 0 <= new_x < self.GRID_SIZE[0] and 0 <= new_y < self.GRID_SIZE[1]:
                        valid_moves.append((new_x, new_y))
        return valid_moves

    def switch_player(self):
        self.current_player = 3 - self.current_player  # Switch between 1 and 2

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    self.handle_mouse_click(event.pos)
        return True

    def handle_mouse_click(self, mouse_pos):
        grid_pos = self.get_grid_pos(mouse_pos)
        clicked_unit = next((unit for unit in self.units[self.current_player] if unit == grid_pos), None)
        
        if clicked_unit:
            self.selected_unit = clicked_unit
        elif self.selected_unit:
            valid_moves = self.get_valid_moves(self.selected_unit)
            if grid_pos in valid_moves:
                self.units[self.current_player].remove(self.selected_unit)
                self.units[self.current_player].append(grid_pos)
                self.switch_player()
            self.selected_unit = None

    def draw(self):
        self.screen.fill(self.WHITE)
        self.draw_map()
        self.draw_move_highlights()
        self.draw_units()
        self.draw_player_indicator()
        pygame.display.flip()

    def draw_map(self):
        for row in range(self.GRID_SIZE[1]):
            for col in range(self.GRID_SIZE[0]):
                tile = self.game_map[row][col]
                x = col * self.TILE_SIZE
                y = row * self.TILE_SIZE

                if tile == 0:
                    pygame.draw.rect(self.screen, self.GRASS_COLOR, (x, y, self.TILE_SIZE, self.TILE_SIZE))
                elif tile == 1:
                    pygame.draw.rect(self.screen, self.ROAD_COLOR, (x, y, self.TILE_SIZE, self.TILE_SIZE))

                pygame.draw.rect(self.screen, self.BLACK, (x, y, self.TILE_SIZE, self.TILE_SIZE), 1)

    def draw_move_highlights(self):
        if self.selected_unit:
            valid_moves = self.get_valid_moves(self.selected_unit)
            for move in valid_moves:
                x, y = move[0] * self.TILE_SIZE, move[1] * self.TILE_SIZE
                highlight_surface = pygame.Surface((self.TILE_SIZE, self.TILE_SIZE), pygame.SRCALPHA)
                highlight_surface.fill(self.MOVE_RANGE_COLOR)
                self.screen.blit(highlight_surface, (x, y))

    def draw_units(self):
        for player, player_units in self.units.items():
            for unit in player_units:
                x = unit[0] * self.TILE_SIZE
                y = unit[1] * self.TILE_SIZE
                color = self.PLAYER1_COLOR if player == 1 else self.PLAYER2_COLOR
                pygame.draw.circle(self.screen, color, (x + self.TILE_SIZE // 2, y + self.TILE_SIZE // 2), self.TILE_SIZE // 3)
                
                if unit == self.selected_unit:
                    pygame.draw.rect(self.screen, self.SELECTED_COLOR, (x, y, self.TILE_SIZE, self.TILE_SIZE), 3)

    def draw_player_indicator(self):
        font = pygame.font.Font(None, 36)
        text = font.render(f"Player {self.current_player}'s Turn", True, self.BLACK)
        self.screen.blit(text, (10, 10))

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.draw()
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()