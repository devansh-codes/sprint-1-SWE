"""
Sprint 1 - 5x5 Matrix Game with GUI
"""

import pygame
import sys
import random
import hashlib
from datetime import datetime
from typing import Optional, Tuple, List
import json
from pathlib import Path

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
CELL_SIZE = 60
GRID_OFFSET_X = 350
GRID_OFFSET_Y = 150
BUTTON_WIDTH = 120
BUTTON_HEIGHT = 40

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_GRAY = (240, 240, 240)
BLUE = (100, 149, 237)
GREEN = (144, 238, 144)
RED = (255, 99, 71)
YELLOW = (255, 255, 153)
DARK_GRAY = (100, 100, 100)


class AuthManager:
    """Handles player registration and authentication."""

    USERS_FILE = Path("users.json")

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def _load_users(self) -> dict:
        if self.USERS_FILE.exists():
            with open(self.USERS_FILE, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}

    def _save_users(self, users: dict):
        with open(self.USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)

    def register(self, username: str, password: str) -> Tuple[bool, str]:
        """Register a new player. Returns (success, message)."""
        if not username.strip() or not password:
            return False, "Username and password cannot be empty."
        users = self._load_users()
        if username in users:
            return False, "Username already exists. Please log in."
        users[username] = self._hash_password(password)
        self._save_users(users)
        return True, "Registration successful! You can now log in."

    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """Authenticate a player. Returns (success, message)."""
        if not username.strip() or not password:
            return False, "Username and password cannot be empty."
        users = self._load_users()
        if username not in users:
            return False, "Username not found. Please register first."
        if users[username] != self._hash_password(password):
            return False, "Incorrect password."
        return True, f"Welcome, {username}!"


class GameBoard:
    """Manages the game board state and logic."""
    
    def __init__(self):
        self.level = 1
        self.inner_board = [[None for _ in range(5)] for _ in range(5)]
        self.outer_ring = [None] * 24  # 24 cells for outer ring
        self.next_number = 1
        self.score = 0
        self.last_position = None
        self.history = []  # For undo functionality
        self.player_name = "Player"
        self.first_number_pos = None  # Store position of number 1 for Level 1
        
    def initialize_level_1(self, random_start=True):
        """Initialize Level 1 with number 1 placed randomly or in same position."""
        # Clear the board
        self.inner_board = [[None for _ in range(5)] for _ in range(5)]
        self.outer_ring = [None] * 24
        self.level = 1

        # Place number 1
        if random_start or self.first_number_pos is None:
            row = random.randint(0, 4)
            col = random.randint(0, 4)
            self.first_number_pos = (row, col)
        else:
            row, col = self.first_number_pos

        self.inner_board[row][col] = 1
        self.next_number = 2
        self.score = 0
        self.last_position = ('inner', row, col)
        self.history = [('inner', row, col, 1, 0)]  # (board_type, row, col, number, score_before)
    
    def initialize_level_2(self):
        """Initialize Level 2 by keeping inner board and clearing outer ring."""
        self.level = 2
        # Keep inner_board as-is (25 numbers remain)
        # Clear outer_ring (24 cells)
        self.outer_ring = [None] * 24
        # Level 2 places numbers 2-25 on the outer ring (24 numbers for 24 cells)
        self.next_number = 2
        # Clear history for Level 2
        self.history = []
    
    def place_number(self, row: int, col: int, board_type: str = 'inner', ring_idx: int = None) -> Tuple[bool, str]:
        """
        Place the next number at the specified position.
        Returns (success, message).
        """
        if self.level == 1:
            # Level 1: place on inner board with adjacency rule
            if board_type != 'inner':
                return False, "Only inner board available in Level 1!"
            if row < 0 or row >= 5 or col < 0 or col >= 5:
                return False, "Out of bounds!"
            if self.inner_board[row][col] is not None:
                return False, "Cell already occupied!"
            
            # Adjacency check: must be exactly 1 step from predecessor
            if self.last_position is not None:
                _, last_r, last_c = self.last_position
                dr = abs(row - last_r)
                dc = abs(col - last_c)
                if dr > 1 or dc > 1 or (dr == 0 and dc == 0):
                    return False, "Must be adjacent (1 step) to the previous number!"
            
            # Scoring: +1 point for diagonal placement from predecessor
            score_before = self.score
            if self.last_position is not None:
                _, last_r, last_c = self.last_position
                if abs(row - last_r) == 1 and abs(col - last_c) == 1:
                    self.score += 1
            
            # Place number
            self.inner_board[row][col] = self.next_number
            self.last_position = ('inner', row, col)
            self.history.append(('inner', row, col, self.next_number, score_before))
            self.next_number += 1
            return True, f"Number {self.next_number - 1} placed! Score: {self.score}"
        
        else:
            # Level 2: place on outer ring based on inner board position rules
            if board_type != 'outer' or ring_idx is None:
                return False, "In Level 2, place numbers on the outer ring!"
            if self.outer_ring[ring_idx] is not None:
                return False, "Cell already occupied!"
            
            # Check if ring cell is a valid position for the current next_number
            valid_indices = self._get_valid_ring_indices(self.next_number)
            if ring_idx not in valid_indices:
                return False, f"Invalid position for {self.next_number}! Must align with its row/column on inner board."
            
            # Place number
            score_before = self.score
            self.outer_ring[ring_idx] = self.next_number
            self.last_position = ('outer', ring_idx)
            self.history.append(('outer', ring_idx, None, self.next_number, score_before))
            self.next_number += 1
            return True, f"Number {self.next_number - 1} placed on outer ring!"
    
    def _find_number_on_inner_board(self, number: int) -> Optional[Tuple[int, int]]:
        """Find the (row, col) of a number on the inner board."""
        for r in range(5):
            for c in range(5):
                if self.inner_board[r][c] == number:
                    return (r, c)
        return None
    
    def _get_valid_ring_indices(self, number: int) -> List[int]:
        """
        Get valid outer ring indices for placing a number based on its inner board position.
        Row/column ends = 4 positions. Main diagonal corners if applicable.
        """
        pos = self._find_number_on_inner_board(number)
        if pos is None:
            return []
        
        r, c = pos
        valid = set()
        
        # Row/column end positions (the 4 "blue" cells)
        valid.add(c + 1)       # Top of column
        valid.add(7 + r)       # Right of row
        valid.add(17 - c)      # Bottom of column
        valid.add(23 - r)      # Left of row
        
        # Diagonal positions (the "yellow" cells) if on a main diagonal
        if r == c:             # Main diagonal (top-left to bottom-right)
            valid.add(0)       # Top-left corner
            valid.add(12)      # Bottom-right corner
        if r + c == 4:         # Anti-diagonal (top-right to bottom-left)
            valid.add(6)       # Top-right corner
            valid.add(18)      # Bottom-left corner
        
        # Filter out already-occupied cells
        return [idx for idx in valid if self.outer_ring[idx] is None]
    
    def has_valid_moves(self) -> bool:
        """Check if the player has any valid moves available."""
        if self.level == 1:
            if self.last_position is None:
                return True
            _, last_r, last_c = self.last_position
            # Check all 8 adjacent cells
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = last_r + dr, last_c + dc
                    if 0 <= nr < 5 and 0 <= nc < 5 and self.inner_board[nr][nc] is None:
                        return True
            return False
        else:
            # Level 2: check if current next_number has valid ring positions
            if self.next_number > 25:
                return False
            return len(self._get_valid_ring_indices(self.next_number)) > 0
    
    def undo(self) -> bool:
        """Undo the last move. Returns True if successful."""
        if self.level == 1 and len(self.history) <= 1:
            # Keep at least number 1 in Level 1
            return False
        if self.level == 2 and len(self.history) == 0:
            return False
        
        # Pop last move from history
        last_move = self.history.pop()
        board_type = last_move[0]
        
        # Restore board state
        if board_type == 'inner':
            row, col = last_move[1], last_move[2]
            self.inner_board[row][col] = None
        else:  # outer ring
            ring_idx = last_move[1]
            self.outer_ring[ring_idx] = None
        
        # Restore score and decrement next_number
        self.score = last_move[4]
        self.next_number -= 1
        
        # Update last_position to previous move
        if len(self.history) > 0:
            prev_move = self.history[-1]
            if prev_move[0] == 'inner':
                self.last_position = ('inner', prev_move[1], prev_move[2])
            else:
                self.last_position = ('outer', prev_move[1])
        else:
            self.last_position = None
        
        return True
    
    def clear_board(self, random_restart=True):
        """Clear the board for restart."""
        if self.level == 1:
            # Always keep number 1 in the same original square when clearing
            self.initialize_level_1(random_start=False)
        else:  # Level 2
            self.initialize_level_2()
    
    def is_valid_placement(self, row: int, col: int) -> bool:
        """Check if a placement is valid (not checking number sequence)."""
        # Check if row, col is within bounds
        if row < 0 or row >= 5 or col < 0 or col >= 5:
            return False
        # Check if cell is empty
        return self.inner_board[row][col] is None
    
    def is_level_complete(self) -> bool:
        """Check if current level is complete."""
        if self.level == 1:
            # Level 1: all 25 cells filled (next_number > 25)
            return self.next_number > 25
        else:  # Level 2
            # Level 2: numbers 2-25 placed on outer ring (next_number > 25)
            return self.next_number > 25
    
    def save_game_log(self):
        """Save completed game to log file."""
        log_entry = {
            "player_name": self.player_name,
            "date_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": self.level,
            "score": self.score,
            "inner_board": self.inner_board,
            "outer_ring": self.outer_ring if self.level == 2 else None
        }
        
        log_file = Path("game_log.json")
        
        # Load existing logs or create new list
        if log_file.exists():
            with open(log_file, 'r') as f:
                try:
                    logs = json.load(f)
                except json.JSONDecodeError:
                    logs = []
        else:
            logs = []
        
        # Append new log
        logs.append(log_entry)
        
        # Save back to file
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)


class Button:
    """Simple button UI element."""
    
    def __init__(self, x, y, width, height, text, color=BLUE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = tuple(min(c + 30, 255) for c in color)
        self.is_hovered = False
        
    def draw(self, screen, font):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=5)
        
        text_surface = font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False


class SoundManager:
    """Manages game sounds and audio feedback."""
    
    def __init__(self):
        self.enabled = True
        # Create sound effects using pygame
        # We'll generate simple beep sounds programmatically
        try:
            # Valid placement sound (higher pitch, shorter)
            self.valid_sound = self._generate_beep(frequency=800, duration=100)
            # Invalid placement sound (lower pitch, longer)
            self.invalid_sound = self._generate_beep(frequency=200, duration=200)
            # Success sound (ascending tones)
            self.success_sound = self._generate_beep(frequency=1000, duration=300)
        except:
            # If sound generation fails, disable sounds
            self.enabled = False
            self.valid_sound = None
            self.invalid_sound = None
            self.success_sound = None
    
    def _generate_beep(self, frequency=440, duration=100):
        """Generate a simple beep sound."""
        if not NUMPY_AVAILABLE:
            return None
            
        try:
            sample_rate = 22050
            n_samples = int(round(duration * sample_rate / 1000))
            
            # Generate sine wave
            buf = np.zeros((n_samples, 2), dtype=np.int16)
            max_sample = 2 ** (16 - 1) - 1
            
            for i in range(n_samples):
                t = float(i) / sample_rate
                # Add fade out to avoid clicks
                amplitude = max_sample * (1.0 - float(i) / n_samples) * 0.3
                value = int(amplitude * np.sin(2.0 * np.pi * frequency * t))
                buf[i][0] = value
                buf[i][1] = value
            
            sound = pygame.sndarray.make_sound(buf)
            return sound
        except:
            # If sound generation fails, return None
            return None
    
    def play_valid_sound(self):
        """Play sound for valid number placement."""
        if self.enabled and self.valid_sound:
            self.valid_sound.play()
    
    def play_invalid_sound(self):
        """Play sound for invalid placement."""
        if self.enabled and self.invalid_sound:
            self.invalid_sound.play()
    
    def play_success_sound(self):
        """Play sound for level completion."""
        if self.enabled and self.success_sound:
            self.success_sound.play()


class LoginScreen:
    """Login and registration screen shown before the game starts."""

    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.auth = AuthManager()

        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 28)

        cx = WINDOW_WIDTH // 2
        self.username_rect = pygame.Rect(cx - 150, 280, 300, 40)
        self.password_rect = pygame.Rect(cx - 150, 360, 300, 40)

        self.login_btn = Button(cx - 160, 430, 140, 40, "Login", GREEN)
        self.register_btn = Button(cx + 20, 430, 140, 40, "Register", BLUE)

        self.username = ""
        self.password = ""
        self.active_field = "username"  # "username" or "password"
        self.message = "Log in or register to play."
        self.message_color = BLACK

    def draw(self):
        self.screen.fill(WHITE)

        title = self.font_large.render("5x5 Matrix Game", True, BLACK)
        self.screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 100)))

        subtitle = self.font_medium.render("Player Login", True, DARK_GRAY)
        self.screen.blit(subtitle, subtitle.get_rect(center=(WINDOW_WIDTH // 2, 155)))

        # Username field
        u_label = self.font_small.render("Username:", True, BLACK)
        self.screen.blit(u_label, (WINDOW_WIDTH // 2 - 150, 255))
        u_border = BLUE if self.active_field == "username" else GRAY
        pygame.draw.rect(self.screen, WHITE, self.username_rect)
        pygame.draw.rect(self.screen, u_border, self.username_rect, 2)
        u_text = self.font_small.render(self.username, True, BLACK)
        self.screen.blit(u_text, (self.username_rect.x + 8, self.username_rect.y + 10))

        # Password field
        p_label = self.font_small.render("Password:", True, BLACK)
        self.screen.blit(p_label, (WINDOW_WIDTH // 2 - 150, 335))
        p_border = BLUE if self.active_field == "password" else GRAY
        pygame.draw.rect(self.screen, WHITE, self.password_rect)
        pygame.draw.rect(self.screen, p_border, self.password_rect, 2)
        p_text = self.font_small.render("*" * len(self.password), True, BLACK)
        self.screen.blit(p_text, (self.password_rect.x + 8, self.password_rect.y + 10))

        self.login_btn.draw(self.screen, self.font_small)
        self.register_btn.draw(self.screen, self.font_small)

        msg = self.font_small.render(self.message, True, self.message_color)
        self.screen.blit(msg, msg.get_rect(center=(WINDOW_WIDTH // 2, 510)))

        pygame.display.flip()

    def run(self) -> Optional[str]:
        """Run the login screen. Returns authenticated username, or exits on quit."""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEMOTION:
                    self.login_btn.handle_event(event)
                    self.register_btn.handle_event(event)

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.username_rect.collidepoint(event.pos):
                        self.active_field = "username"
                    elif self.password_rect.collidepoint(event.pos):
                        self.active_field = "password"
                    elif self.login_btn.rect.collidepoint(event.pos):
                        success, msg = self.auth.login(self.username, self.password)
                        self.message = msg
                        self.message_color = GREEN if success else RED
                        if success:
                            return self.username
                    elif self.register_btn.rect.collidepoint(event.pos):
                        success, msg = self.auth.register(self.username, self.password)
                        self.message = msg
                        self.message_color = GREEN if success else RED

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_TAB:
                        self.active_field = "password" if self.active_field == "username" else "username"
                    elif event.key == pygame.K_RETURN:
                        success, msg = self.auth.login(self.username, self.password)
                        self.message = msg
                        self.message_color = GREEN if success else RED
                        if success:
                            return self.username
                    elif event.key == pygame.K_BACKSPACE:
                        if self.active_field == "username":
                            self.username = self.username[:-1]
                        else:
                            self.password = self.password[:-1]
                    else:
                        if self.active_field == "username":
                            self.username += event.unicode
                        else:
                            self.password += event.unicode

            self.draw()
            self.clock.tick(60)


class GameGUI:
    """Main game GUI using Pygame."""
    
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("5x5 Matrix Game - Sprint 1")
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 28)
        
        # Game objects
        self.game_board = GameBoard()
        self.sound_manager = SoundManager()
        
        # UI Buttons
        self.create_buttons()
        
        # Game state
        self.running = True
        self.message = "Welcome! Click on a cell to place numbers."
        self.message_color = BLACK
        
        # Initialize game
        self.game_board.initialize_level_1()
        
    def create_buttons(self):
        """Create UI buttons."""
        button_y = WINDOW_HEIGHT - 80
        spacing = BUTTON_WIDTH + 20
        start_x = (WINDOW_WIDTH - (spacing * 4 - 20)) // 2
        
        self.new_game_btn = Button(start_x, button_y, BUTTON_WIDTH, BUTTON_HEIGHT, "New Game", GREEN)
        self.clear_btn = Button(start_x + spacing, button_y, BUTTON_WIDTH, BUTTON_HEIGHT, "Clear", YELLOW)
        self.undo_btn = Button(start_x + spacing * 2, button_y, BUTTON_WIDTH, BUTTON_HEIGHT, "Undo", BLUE)
        self.level2_btn = Button(start_x + spacing * 3, button_y, BUTTON_WIDTH, BUTTON_HEIGHT, "Level 2", RED)
        
    def draw_board(self):
        """Draw the game board (inner 5x5 and outer ring for Level 2)."""
        # Highlight last placed position in Level 1
        last_inner_pos = None
        if self.game_board.level == 1 and self.game_board.last_position is not None:
            last_inner_pos = (self.game_board.last_position[1], self.game_board.last_position[2])
        
        # Draw inner 5x5 grid
        for row in range(5):
            for col in range(5):
                x = GRID_OFFSET_X + col * CELL_SIZE
                y = GRID_OFFSET_Y + row * CELL_SIZE
                
                # Highlight the last placed cell
                if last_inner_pos and (row, col) == last_inner_pos:
                    pygame.draw.rect(self.screen, YELLOW, (x, y, CELL_SIZE, CELL_SIZE))
                else:
                    pygame.draw.rect(self.screen, WHITE, (x, y, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(self.screen, BLACK, (x, y, CELL_SIZE, CELL_SIZE), 2)
                
                # Draw number if present
                number = self.game_board.inner_board[row][col]
                if number is not None:
                    text = self.font_medium.render(str(number), True, BLACK)
                    text_rect = text.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                    self.screen.blit(text, text_rect)
        
        # Draw outer ring for Level 2
        if self.game_board.level == 2:
            self.draw_outer_ring()
    
    def draw_outer_ring(self):
        """Draw the outer ring of 24 cells for Level 2."""
        ring_positions = self._get_ring_positions()
        
        # Corner indices: top-left=0, top-right=6, bottom-right=12, bottom-left=18
        corner_indices = {0, 6, 12, 18}
        
        # Draw each ring cell
        for idx, (x, y) in enumerate(ring_positions):
            # Green for corners only
            if idx in corner_indices:
                cell_color = GREEN
            else:
                cell_color = LIGHT_GRAY
            
            pygame.draw.rect(self.screen, cell_color, (x, y, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(self.screen, DARK_GRAY, (x, y, CELL_SIZE, CELL_SIZE), 2)
            
            # Draw number if present
            number = self.game_board.outer_ring[idx]
            if number is not None:
                text = self.font_medium.render(str(number), True, BLACK)
                text_rect = text.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                self.screen.blit(text, text_rect)
    
    def draw_ui(self):
        """Draw UI elements (next number, score, level, etc.) in a clear area beside and below the grid."""
        # Title (top left)
        title = self.font_large.render("5x5 Matrix Game", True, BLACK)
        self.screen.blit(title, (30, 30))

        # Next number display (left side)
        next_text = self.font_medium.render(f"Next Number: {self.game_board.next_number}", True, BLUE)
        self.screen.blit(next_text, (30, 100))

        # Score display (left side)
        score_text = self.font_medium.render(f"Score: {self.game_board.score}", True, GREEN)
        self.screen.blit(score_text, (30, 150))

        # Level display (left side)
        level_text = self.font_medium.render(f"Level: {self.game_board.level}", True, RED)
        self.screen.blit(level_text, (30, 200))

        # Player name (left side)
        player_text = self.font_small.render(f"Player: {self.game_board.player_name}", True, BLACK)
        self.screen.blit(player_text, (30, 250))

        # Message display (well below grid, accounting for Level 2 outer ring)
        # Level 2 outer ring extends to y = GRID_OFFSET_Y + 6 * CELL_SIZE = 510
        msg_text = self.font_small.render(self.message, True, self.message_color)
        msg_rect = msg_text.get_rect(center=(WINDOW_WIDTH // 2, 560))
        self.screen.blit(msg_text, msg_rect)

        # Draw buttons (bottom center)
        self.new_game_btn.draw(self.screen, self.font_small)
        self.clear_btn.draw(self.screen, self.font_small)
        self.undo_btn.draw(self.screen, self.font_small)
        self.level2_btn.draw(self.screen, self.font_small)
    
    def handle_cell_click(self, pos):
        """Handle mouse click on game board cells."""
        mouse_x, mouse_y = pos
        
        # Check inner 5x5 grid (only for Level 1)
        if self.game_board.level == 1:
            for row in range(5):
                for col in range(5):
                    x = GRID_OFFSET_X + col * CELL_SIZE
                    y = GRID_OFFSET_Y + row * CELL_SIZE
                    cell_rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                    
                    if cell_rect.collidepoint(pos):
                        # Try to place number
                        success, msg = self.game_board.place_number(row, col, 'inner')
                        
                        if success:
                            self.sound_manager.play_valid_sound()
                            self.message = msg
                            self.message_color = GREEN
                            
                            # Check if level is complete
                            if self.game_board.is_level_complete():
                                self.sound_manager.play_success_sound()
                                self.message = f"Level 1 Complete! Score: {self.game_board.score}"
                                self.message_color = BLUE
                                self.game_board.save_game_log()
                            # Check for dead end
                            elif not self.game_board.has_valid_moves():
                                self.message = "Dead end! Use Undo to rollback."
                                self.message_color = RED
                        else:
                            self.sound_manager.play_invalid_sound()
                            self.message = msg
                            self.message_color = RED
                        return
        elif self.game_board.level == 2:
            # In Level 2, clicking inner board does nothing
            for row in range(5):
                for col in range(5):
                    x = GRID_OFFSET_X + col * CELL_SIZE
                    y = GRID_OFFSET_Y + row * CELL_SIZE
                    cell_rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                    if cell_rect.collidepoint(pos):
                        self.message = "Inner board is locked in Level 2!"
                        self.message_color = RED
                        self.sound_manager.play_invalid_sound()
                        return
        
        # Check outer ring for Level 2
        if self.game_board.level == 2:
            # Calculate outer ring cell positions
            ring_positions = self._get_ring_positions()
            
            for idx, (x, y) in enumerate(ring_positions):
                cell_rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                if cell_rect.collidepoint(pos):
                    # Try to place number in outer ring
                    success, msg = self.game_board.place_number(0, 0, 'outer', ring_idx=idx)
                    
                    if success:
                        self.sound_manager.play_valid_sound()
                        self.message = msg
                        self.message_color = GREEN
                        
                        # Check if level is complete
                        if self.game_board.is_level_complete():
                            self.sound_manager.play_success_sound()
                            self.message = f"Level 2 Complete! Final Score: {self.game_board.score}"
                            self.message_color = BLUE
                            self.game_board.save_game_log()
                        # Check for dead end
                        elif not self.game_board.has_valid_moves():
                            self.message = "Dead end! Use Undo to rollback."
                            self.message_color = RED
                    else:
                        self.sound_manager.play_invalid_sound()
                        self.message = msg
                        self.message_color = RED
                    return
    
    def _get_ring_positions(self):
        """Get list of outer ring cell positions."""
        ring_positions = []
        
        # Top row (7 cells: entire top edge)
        for i in range(7):
            ring_positions.append((GRID_OFFSET_X - CELL_SIZE + i * CELL_SIZE, GRID_OFFSET_Y - CELL_SIZE))
        
        # Right column (5 cells: right side, excluding corners)
        for i in range(1, 6):
            ring_positions.append((GRID_OFFSET_X + 5 * CELL_SIZE, GRID_OFFSET_Y - CELL_SIZE + i * CELL_SIZE))
        
        # Bottom row (7 cells: entire bottom edge, right to left)
        for i in range(6, -1, -1):
            ring_positions.append((GRID_OFFSET_X - CELL_SIZE + i * CELL_SIZE, GRID_OFFSET_Y + 5 * CELL_SIZE))
        
        # Left column (5 cells: left side, excluding corners)
        for i in range(5, 0, -1):
            ring_positions.append((GRID_OFFSET_X - CELL_SIZE, GRID_OFFSET_Y - CELL_SIZE + i * CELL_SIZE))
        
        return ring_positions
    
    def handle_new_game(self):
        """Start a new game at Level 1."""
        self.game_board.initialize_level_1(random_start=True)
        self.message = "New game started! Place numbers sequentially."
        self.message_color = BLACK
    
    def handle_clear(self):
        """Clear the board based on current level."""
        # For simplicity, always use random restart for Level 1
        self.game_board.clear_board(random_restart=True)
        
        if self.game_board.level == 1:
            self.message = "Board cleared! Number 1 placed randomly."
        else:
            self.message = "Outer ring cleared! Inner board remains."
        self.message_color = BLACK
    
    def handle_undo(self):
        """Undo the last move."""
        if self.game_board.undo():
            self.message = f"Move undone! Next number: {self.game_board.next_number}"
            self.message_color = BLUE
        else:
            self.message = "Cannot undo! Must keep at least the first number."
            self.message_color = RED
    
    def handle_level_2(self):
        """Activate Level 2."""
        # Check if Level 1 is complete
        if self.game_board.level == 1:
            if self.game_board.is_level_complete():
                self.game_board.initialize_level_2()
                self.message = "Level 2! Place numbers 2-25 on the outer ring (green = valid)."
                self.message_color = GREEN
            else:
                self.message = "Complete Level 1 first (fill all 25 cells)!"
                self.message_color = RED
        else:
            self.message = "Already in Level 2!"
            self.message_color = RED
    
    def handle_events(self):
        """Handle all pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            # Button events
            if self.new_game_btn.handle_event(event):
                self.handle_new_game()
            if self.clear_btn.handle_event(event):
                self.handle_clear()
            if self.undo_btn.handle_event(event):
                self.handle_undo()
            if self.level2_btn.handle_event(event):
                self.handle_level_2()
            
            # Cell click
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_cell_click(event.pos)
    
    def run(self):
        """Main game loop."""
        while self.running:
            self.screen.fill(WHITE)
            
            self.handle_events()
            self.draw_board()
            self.draw_ui()
            
            pygame.display.flip()
            self.clock.tick(60)  # 60 FPS
        
        pygame.quit()
        sys.exit()


def main():
    """Entry point for the game."""
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("5x5 Matrix Game - Sprint 1")
    clock = pygame.time.Clock()

    login = LoginScreen(screen, clock)
    player_name = login.run()

    game = GameGUI()
    game.game_board.player_name = player_name
    game.message = f"Welcome, {player_name}! Click on a cell to place numbers."
    game.run()


if __name__ == "__main__":
    main()
