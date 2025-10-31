import pygame
import sys

class GameMenu:
    def __init__(self, screen, config):
        self.screen = screen
        self.config = config
        self.width = config.SCREEN_WIDTH
        self.height = config.SCREEN_HEIGHT
        
        # Colors
        self.BG_COLOR = (135, 206, 250)  # Sky blue background
        self.TITLE_COLOR = (255, 255, 255)
        self.BUTTON_COLOR = (30, 144, 255)
        self.BUTTON_HOVER_COLOR = (0, 191, 255)
        self.TEXT_COLOR = (255, 255, 255)
        
        # Fonts
        self.title_font = pygame.font.Font(None, 74)
        self.button_font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 36)
        
        # Buttons
        self.buttons = self._create_buttons()
        self.selected_button = 0
        
    def _create_buttons(self):
        button_width = 300
        button_height = 60
        button_spacing = 20
        start_y = self.height // 2 - 50
        
        buttons = [
            {
                'text': 'Start Game',
                'rect': pygame.Rect(
                    self.width // 2 - button_width // 2,
                    start_y,
                    button_width,
                    button_height
                ),
                'action': 'start'
            },
            {
                'text': 'Settings',
                'rect': pygame.Rect(
                    self.width // 2 - button_width // 2,
                    start_y + button_height + button_spacing,
                    button_width,
                    button_height
                ),
                'action': 'settings'
            },
            {
                'text': 'Quit Game',
                'rect': pygame.Rect(
                    self.width // 2 - button_width // 2,
                    start_y + (button_height + button_spacing) * 2,
                    button_width,
                    button_height
                ),
                'action': 'quit'
            }
        ]
        return buttons
    
    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            
            # Keyboard
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_button = (self.selected_button - 1) % len(self.buttons)
                elif event.key == pygame.K_DOWN:
                    self.selected_button = (self.selected_button + 1) % len(self.buttons)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    return self.buttons[self.selected_button]['action']
                elif event.key == pygame.K_ESCAPE:
                    return 'quit'
            
            # Mouse
            if event.type == pygame.MOUSEMOTION:
                for i, button in enumerate(self.buttons):
                    if button['rect'].collidepoint(mouse_pos):
                        self.selected_button = i
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    for button in self.buttons:
                        if button['rect'].collidepoint(mouse_pos):
                            return button['action']
        
        return None
    
    def draw(self):
        # Draw background
        self.screen.fill(self.BG_COLOR)
        
        # Draw title with shadow
        shadow_text = self.title_font.render('MY GAME', True, (0, 0, 0))
        shadow_rect = shadow_text.get_rect(center=(self.width // 2 + 3, 153))
        self.screen.blit(shadow_text, shadow_rect)
        
        title_text = self.title_font.render('MY GAME', True, self.TITLE_COLOR)
        title_rect = title_text.get_rect(center=(self.width // 2, 150))
        self.screen.blit(title_text, title_rect)
        
        # Draw buttons
        for i, button in enumerate(self.buttons):
            # Select button color
            is_selected = (i == self.selected_button)
            color = self.BUTTON_HOVER_COLOR if is_selected else self.BUTTON_COLOR
            
            # Draw button
            pygame.draw.rect(self.screen, color, button['rect'], border_radius=10)
            pygame.draw.rect(self.screen, self.TEXT_COLOR, button['rect'], 3, border_radius=10)
            
            # Draw text
            text = self.button_font.render(button['text'], True, self.TEXT_COLOR)
            text_rect = text.get_rect(center=button['rect'].center)
            self.screen.blit(text, text_rect)
        
        # Draw instructions
        hint_text = self.small_font.render('Use Arrow Keys ↑↓ or Mouse | Enter/Space to Select', True, (255, 255, 255))
        hint_rect = hint_text.get_rect(center=(self.width // 2, self.height - 50))
        self.screen.blit(hint_text, hint_rect)
        
        pygame.display.flip()
    
    def run(self):
        clock = pygame.time.Clock()
        
        while True:
            action = self.handle_events()
            
            if action == 'start':
                return 'start'
            elif action == 'settings':
                return 'settings'
            elif action == 'quit':
                return 'quit'
            
            self.draw()
            clock.tick(60)