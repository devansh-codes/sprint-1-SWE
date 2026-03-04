"""
5x5 Matrix Game with GUI - Sprint 2

Module organization (User Story 12 - Code Refactoring):
  Section 1: Imports and Constants
  Section 2: Authentication (AuthManager)
  Section 3: Game Logic (GameBoard) with Solution Solver (User Story 13)
  Section 4: UI Components (Button)
  Section 5: Audio (SoundManager)
  Section 6: Pre-game Screens (LoginScreen, TimeLimitScreen)
  Section 7: Main Game GUI (GameGUI)
  Section 8: Entry Point (main)
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
ORANGE = (255, 165, 0)  # Used for solution display (User Story 13)


# =============================================================================
# Section 2: Authentication
# =============================================================================

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


# =============================================================================
# Section 3: Game Logic (with Solution Solver - User Story 13)
# =============================================================================

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

        # Solution display state (User Story 13)
        self.solution_cells = set()        # (row, col) auto-filled by solver
        self.solution_ring_indices = set()  # ring indices auto-filled by solver
        self.showing_solution = False
        
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
        self._clear_solution()
    
    def initialize_level_2(self):
        """Initialize Level 2 by keeping inner board and clearing outer ring."""
        self.level = 2
        self.outer_ring = [None] * 24
        self.next_number = 2
        self.history = []
        self._clear_solution()

    def initialize_level_3(self):
        """Initialize Level 3."""
        self.level = 3
        # Keep outer ring from Level 2, clear inner grid except 1
        for r in range(5):
            for c in range(5):
                if self.inner_board[r][c] != 1:
                    self.inner_board[r][c] = None
        self.next_number = 2
        self.history = []
        self._clear_solution()

def place_number(self, row: int, col: int, board_type: str = 'inner', ring_idx: int = None) -> Tuple[bool, str]:
    """
    Place the next number at the specified position.
    Returns (success, message).

    User Story 10: +1 per successful placement (all levels), -1 per undo/clear.
    Level rules:
      - Level 1: inner board adjacency rule (8-direction).
      - Level 2: outer ring placement rule based on inner position.
      - Level 3: inner board adjacency + intersection rule + corner diagonal rule (see Level 3.pdf).
    """

    # ---------- Level 1 and Level 3: place on inner board ----------
    if self.level in (1, 3):
        if board_type != 'inner':
            return False, "Only inner board placements are allowed in this level!"
        if row < 0 or row >= 5 or col < 0 or col >= 5:
            return False, "Out of bounds!"
        if self.inner_board[row][col] is not None:
            return False, "Cell already occupied!"

        # Must be adjacent to the previous number (same rule as Level 1)
        if self.last_position is not None:
            _, last_r, last_c = self.last_position
            dr = abs(row - last_r)
            dc = abs(col - last_c)
            if dr > 1 or dc > 1 or (dr == 0 and dc == 0):
                return False, "Must be adjacent (1 step) to the previous number!"

        # Level 3 additional constraints
        if self.level == 3:
            valid_cells = set(self.get_level3_valid_cells(self.next_number))
            if (row, col) not in valid_cells:
                return False, f"Invalid Level 3 position for {self.next_number}!"

        score_before = self.score
        self.score += 1  # US10

        self.inner_board[row][col] = self.next_number
        self.last_position = ('inner', row, col)
        self.history.append(('inner', row, col, self.next_number, score_before))
        self.next_number += 1
        return True, f"Number {self.next_number - 1} placed! Score: {self.score}"

    # ---------- Level 2: place on outer ring ----------
    if self.level == 2:
        if board_type != 'outer' or ring_idx is None:
            return False, "In Level 2, place numbers on the outer ring!"
        if self.outer_ring[ring_idx] is not None:
            return False, "Cell already occupied!"

        valid_indices = self._get_valid_ring_indices(self.next_number)
        if ring_idx not in valid_indices:
            return False, f"Invalid position for {self.next_number}! Must align with its row/column on inner board."

        score_before = self.score
        self.score += 1  # US10

        self.outer_ring[ring_idx] = self.next_number
        self.last_position = ('outer', ring_idx)
        self.history.append(('outer', ring_idx, None, self.next_number, score_before))
        self.next_number += 1
        return True, f"Number {self.next_number - 1} placed on outer ring! Score: {self.score}"

    return False, "Unknown level state."

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
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = last_r + dr, last_c + dc
                if 0 <= nr < 5 and 0 <= nc < 5 and self.inner_board[nr][nc] is None:
                    return True
        return False

    if self.level == 2:
        if self.next_number > 25:
            return False
        return len(self._get_valid_ring_indices(self.next_number)) > 0

    if self.level == 3:
        if self.next_number > 25:
            return False
        return len(self.get_level3_valid_cells(self.next_number)) > 0

    return False

    def get_valid_adjacent_empty_cells(self):
        """
        Return list of (row, col) pairs for empty cells that are valid
        placements for the next number in Level 1 (8-direction neighborhood
        around the last placed number).
        """
        if self.level != 1 or self.last_position is None:
            return []

        _, last_r, last_c = self.last_position
        valid_cells = []

        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = last_r + dr, last_c + dc
                if 0 <= nr < 5 and 0 <= nc < 5 and self.inner_board[nr][nc] is None:
                    valid_cells.append((nr, nc))

        return valid_cells


def get_level2_valid_ring_indices(self, number: int) -> List[int]:
    """Helper for UI hints in Level 2."""
    return self._get_valid_ring_indices(number)

def get_level3_valid_cells(self, number: int) -> List[Tuple[int, int]]:
    """Compute valid inner-board cells for Level 3 for the given number."""
    if self.level != 3:
        return []

    top = self.outer_ring[0:7]
    right = self.outer_ring[7:12]      # rows 0..4
    bottom = self.outer_ring[12:19]    # cols 4..0
    left = self.outer_ring[19:24]      # rows 4..0

    rows = set()
    cols = set()

    # row ends
    for r in range(5):
        left_end = left[4 - r]   # left is bottom->top
        right_end = right[r]
        if left_end == number or right_end == number:
            rows.add(r)

    # column ends
    for c in range(5):
        top_end = top[c + 1]          # top indices 1..5 correspond to cols 0..4
        bottom_end = bottom[4 - c]    # bottom is right->left
        if top_end == number or bottom_end == number:
            cols.add(c)

    if not rows or not cols:
        return []

    corner_numbers = {self.outer_ring[0], self.outer_ring[6], self.outer_ring[12], self.outer_ring[18]}
    diagonal_required = number in corner_numbers

    valid = []
    for r in rows:
        for c in cols:
            if self.inner_board[r][c] is None:
                if diagonal_required and not (r == c or r + c == 4):
                    continue
                valid.append((r, c))

    # adjacency to last placed number
    if self.last_position and self.last_position[0] == 'inner':
        _, last_r, last_c = self.last_position
        valid = [(r, c) for (r, c) in valid if (abs(r - last_r) <= 1 and abs(c - last_c) <= 1 and not (r == last_r and c == last_c))]

    return valid
    
def undo(self) -> bool:
    """Undo the last move. Returns True if successful. (US10: -1 per undo)"""
    if self.level in (1, 3) and len(self.history) <= 1:
        return False
    if self.level == 2 and len(self.history) == 0:
        return False

    last_move = self.history.pop()
    board_type = last_move[0]

    if board_type == 'inner':
        row, col = last_move[1], last_move[2]
        self.inner_board[row][col] = None
    else:
        ring_idx = last_move[1]
        self.outer_ring[ring_idx] = None

    self.score = max(0, self.score - 1)
    self.next_number -= 1

    if len(self.history) > 0:
        prev_move = self.history[-1]
        if prev_move[0] == 'inner':
            self.last_position = ('inner', prev_move[1], prev_move[2])
        else:
            self.last_position = ('outer', prev_move[1])
    else:
        self.last_position = None

    self._clear_solution()
    return True

def clear_board(self, random_restart=True):
    """Clear the board for restart. (US10: -1 per cell rolled back/cleared)"""
    if self.level == 1:
        removed = sum(1 for r in range(5) for c in range(5) if self.inner_board[r][c] is not None) - 1
        self.score = max(0, self.score - max(0, removed))
        self.initialize_level_1(random_start=False)

    elif self.level == 2:
        removed = sum(1 for v in self.outer_ring if v is not None)
        self.score = max(0, self.score - removed)
        self.initialize_level_2()

    elif self.level == 3:
        removed = sum(1 for r in range(5) for c in range(5) if self.inner_board[r][c] is not None) - 1
        self.score = max(0, self.score - max(0, removed))
        self.initialize_level_3()

    def is_valid_placement(self, row: int, col: int) -> bool:
        """Check if a placement is valid (not checking number sequence)."""
        # Check if row, col is within bounds
        if row < 0 or row >= 5 or col < 0 or col >= 5:
            return False
        # Check if cell is empty
        return self.inner_board[row][col] is None
    
def is_level_complete(self) -> bool:
    """Check if current level is complete."""
    if self.level in (1, 3):
        return self.next_number > 25
    if self.level == 2:
        return self.next_number > 25
    return False

def save_game_log(self):
    """Save completed game to log file."""
    log_entry = {
        "player_name": self.player_name,
        "date_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "level": self.level,
        "score": self.score,
        "inner_board": self.inner_board,
        "outer_ring": self.outer_ring if self.level >= 2 else None
    }

    log_file = Path("game_log.json")
    if log_file.exists():
        with open(log_file, 'r') as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    else:
        logs = []

    logs.append(log_entry)

    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)

    def _clear_solution(self):
        """Clear any displayed solution."""
        self.solution_cells = set()
        self.solution_ring_indices = set()
        self.showing_solution = False

def solve_and_display(self):
    """Attempt to find and display a solution for unfinished cells (US13)."""
    self._clear_solution()

    if self.level == 1:
        return self._solve_level_1()
    elif self.level == 2:
        return self._solve_level_2()
    elif self.level == 3:
        return self._solve_level_3()
    else:
        return False, "Solution not available for this level."

    def _solve_level_1(self):
        """Solve Level 1 using backtracking from the current board state."""
        if self.is_level_complete():
            return False, "Level already complete!"

        # Remember which cells the player placed
        player_cells = set()
        for r in range(5):
            for c in range(5):
                if self.inner_board[r][c] is not None:
                    player_cells.add((r, c))

        # Try solving from current state
        board_copy = [row[:] for row in self.inner_board]
        last_r, last_c = self.last_position[1], self.last_position[2]
        next_num = self.next_number

        if self._backtrack_level_1(board_copy, last_r, last_c, next_num):
            # Solution found from current state
            for r in range(5):
                for c in range(5):
                    if (r, c) not in player_cells and board_copy[r][c] is not None:
                        self.inner_board[r][c] = board_copy[r][c]
                        self.solution_cells.add((r, c))
            self.showing_solution = True
            self.next_number = 26
            return True, "Solution displayed! Orange cells are auto-filled."

        # No solution from current state - clear and solve from scratch
        start_r, start_c = self.first_number_pos
        self.inner_board = [[None for _ in range(5)] for _ in range(5)]
        self.inner_board[start_r][start_c] = 1

        board_copy = [row[:] for row in self.inner_board]
        if self._backtrack_level_1(board_copy, start_r, start_c, 2):
            self.solution_cells = set()
            for r in range(5):
                for c in range(5):
                    self.inner_board[r][c] = board_copy[r][c]
                    if (r, c) != (start_r, start_c):
                        self.solution_cells.add((r, c))
            self.showing_solution = True
            self.next_number = 26
            self.score = 0
            self.history = [('inner', start_r, start_c, 1, 0)]
            self.last_position = None
            return True, "No solution from your moves. Board cleared. Full solution in orange."

        return False, "Could not find any solution!"

    def _backtrack_level_1(self, board, last_r, last_c, next_num):
        """
        Backtracking solver for Level 1.
        Uses Warnsdorff's heuristic to prefer cells with fewer onward moves.
        """
        if next_num > 25:
            return True

        neighbors = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = last_r + dr, last_c + dc
                if 0 <= nr < 5 and 0 <= nc < 5 and board[nr][nc] is None:
                    neighbors.append((nr, nc))

        # Warnsdorff's heuristic: try cells with fewer onward moves first
        def count_onward(r, c):
            count = 0
            for dr2 in [-1, 0, 1]:
                for dc2 in [-1, 0, 1]:
                    if dr2 == 0 and dc2 == 0:
                        continue
                    nr2, nc2 = r + dr2, c + dc2
                    if 0 <= nr2 < 5 and 0 <= nc2 < 5 and board[nr2][nc2] is None:
                        count += 1
            return count

        neighbors.sort(key=lambda pos: count_onward(pos[0], pos[1]))

        for nr, nc in neighbors:
            board[nr][nc] = next_num
            if self._backtrack_level_1(board, nr, nc, next_num + 1):
                return True
            board[nr][nc] = None

        return False

    def _solve_level_2(self):
        """Solve Level 2 using backtracking from the current outer ring state."""
        if self.is_level_complete():
            return False, "Level already complete!"

        # Remember which ring cells the player placed
        player_ring = set()
        for idx in range(24):
            if self.outer_ring[idx] is not None:
                player_ring.add(idx)

        # Try solving from current state
        ring_copy = self.outer_ring[:]
        next_num = self.next_number

        if self._backtrack_level_2(ring_copy, next_num):
            for idx in range(24):
                if idx not in player_ring and ring_copy[idx] is not None:
                    self.outer_ring[idx] = ring_copy[idx]
                    self.solution_ring_indices.add(idx)
            self.showing_solution = True
            self.next_number = 26
            return True, "Solution displayed! Orange cells are auto-filled."

        # No solution from current state - clear and solve from scratch
        self.outer_ring = [None] * 24
        ring_copy = [None] * 24

        if self._backtrack_level_2(ring_copy, 2):
            for idx in range(24):
                self.outer_ring[idx] = ring_copy[idx]
                if ring_copy[idx] is not None:
                    self.solution_ring_indices.add(idx)
            self.showing_solution = True
            self.next_number = 26
            self.score = 0
            self.history = []
            return True, "No solution from your moves. Ring cleared. Full solution in orange."

        return False, "Could not find any solution for Level 2!"

    def _backtrack_level_2(self, ring, next_num):
        """Backtracking solver for Level 2 outer ring placement."""
        if next_num > 25:
            return True

        pos = self._find_number_on_inner_board(next_num)
        if pos is None:
            return False

        r, c = pos
        valid = set()
        valid.add(c + 1)
        valid.add(7 + r)
        valid.add(17 - c)
        valid.add(23 - r)
        if r == c:
            valid.add(0)
            valid.add(12)
        if r + c == 4:
            valid.add(6)
            valid.add(18)

        available = [idx for idx in valid if ring[idx] is None]

        for idx in available:
            ring[idx] = next_num
            if self._backtrack_level_2(ring, next_num + 1):
                return True
            ring[idx] = None

        return False


def _solve_level_3(self):
    """Solve Level 3 using backtracking."""
    if self.is_level_complete():
        return False, "Level already complete!"

    # player-filled cells for coloring
    player_cells = {(r, c) for r in range(5) for c in range(5) if self.inner_board[r][c] is not None}

    # find position of 1
    one_pos = None
    for r in range(5):
        for c in range(5):
            if self.inner_board[r][c] == 1:
                one_pos = (r, c)
                break
        if one_pos:
            break
    if one_pos is None:
        return False, "Invalid Level 3 state: missing number 1."

    # find last placed number
    max_num = 1
    last_r, last_c = one_pos
    for r in range(5):
        for c in range(5):
            v = self.inner_board[r][c]
            if isinstance(v, int) and v > max_num:
                max_num = v
                last_r, last_c = r, c

    board_copy = [row[:] for row in self.inner_board]
    if self._backtrack_level_3(board_copy, last_r, last_c, max_num + 1):
        for r in range(5):
            for c in range(5):
                if (r, c) not in player_cells and board_copy[r][c] is not None:
                    self.inner_board[r][c] = board_copy[r][c]
                    self.solution_cells.add((r, c))
        self.showing_solution = True
        self.next_number = 26
        return True, "Solution displayed! Orange cells are auto-filled."

    # clear to only 1 and solve
    self.inner_board = [[None for _ in range(5)] for _ in range(5)]
    self.inner_board[one_pos[0]][one_pos[1]] = 1
    board_copy = [row[:] for row in self.inner_board]
    if self._backtrack_level_3(board_copy, one_pos[0], one_pos[1], 2):
        self.solution_cells = set()
        for r in range(5):
            for c in range(5):
                self.inner_board[r][c] = board_copy[r][c]
                if (r, c) != one_pos:
                    self.solution_cells.add((r, c))
        self.showing_solution = True
        self.next_number = 26
        return True, "No solution from your moves. Inner grid cleared. Full solution in orange."

    return False, "Could not find any solution for Level 3!"

def _backtrack_level_3(self, board, last_r, last_c, next_num):
    if next_num > 25:
        return True

    # compute candidates using Level 3 rules
    saved_inner = self.inner_board
    saved_last = self.last_position
    saved_level = self.level
    try:
        self.level = 3
        self.inner_board = board
        self.last_position = ('inner', last_r, last_c)
        candidates = self.get_level3_valid_cells(next_num)
    finally:
        self.inner_board = saved_inner
        self.last_position = saved_last
        self.level = saved_level

    # heuristic: fewer onward moves first
    def onward(rc):
        r, c = rc
        saved_inner2 = self.inner_board
        saved_last2 = self.last_position
        saved_level2 = self.level
        try:
            self.level = 3
            self.inner_board = board
            self.last_position = ('inner', r, c)
            return len(self.get_level3_valid_cells(next_num + 1))
        finally:
            self.inner_board = saved_inner2
            self.last_position = saved_last2
            self.level = saved_level2

    candidates.sort(key=onward)

    for r, c in candidates:
        board[r][c] = next_num
        if self._backtrack_level_3(board, r, c, next_num + 1):
            return True
        board[r][c] = None
    return False


# =============================================================================
# Section 4: UI Components
# =============================================================================

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


# =============================================================================
# Section 5: Audio
# =============================================================================

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


# =============================================================================
# Section 6: Pre-game Screens
# =============================================================================

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


class TimeLimitScreen:
    """Screen for setting the time limit for a level."""

    def __init__(self, screen, clock, level=1):
        self.screen = screen
        self.clock = clock
        self.level = level
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 28)

        cx = WINDOW_WIDTH // 2
        self.input_rect = pygame.Rect(cx - 80, 315, 160, 44)
        self.start_btn = Button(cx - 165, 390, 150, 40, "Start Game", GREEN)
        self.no_limit_btn = Button(cx + 15, 390, 150, 40, "No Limit", BLUE)

        self.input_text = "60"
        self.message = f"Enter time limit in seconds for Level {level}."
        self.message_color = DARK_GRAY

    def draw(self):
        self.screen.fill(WHITE)

        title = self.font_large.render("5x5 Matrix Game", True, BLACK)
        self.screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 100)))

        sub = self.font_medium.render(f"Set Time Limit - Level {self.level}", True, DARK_GRAY)
        self.screen.blit(sub, sub.get_rect(center=(WINDOW_WIDTH // 2, 160)))

        note = self.font_small.render("Finish early = +1 pt/sec bonus. Go over = -1 pt/sec penalty.", True, DARK_GRAY)
        self.screen.blit(note, note.get_rect(center=(WINDOW_WIDTH // 2, 210)))

        label = self.font_small.render("Seconds (e.g. 30, 60, 80):", True, BLACK)
        self.screen.blit(label, label.get_rect(center=(WINDOW_WIDTH // 2, 285)))

        pygame.draw.rect(self.screen, WHITE, self.input_rect)
        pygame.draw.rect(self.screen, BLUE, self.input_rect, 2)
        inp = self.font_medium.render(self.input_text, True, BLACK)
        self.screen.blit(inp, inp.get_rect(center=self.input_rect.center))

        self.start_btn.draw(self.screen, self.font_small)
        self.no_limit_btn.draw(self.screen, self.font_small)

        msg = self.font_small.render(self.message, True, self.message_color)
        self.screen.blit(msg, msg.get_rect(center=(WINDOW_WIDTH // 2, 460)))

        pygame.display.flip()

    def run(self) -> int:
        """Returns the time limit in seconds, or 0 for no limit."""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEMOTION:
                    self.start_btn.handle_event(event)
                    self.no_limit_btn.handle_event(event)

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.no_limit_btn.rect.collidepoint(event.pos):
                        return 0
                    elif self.start_btn.rect.collidepoint(event.pos):
                        result = self._try_submit()
                        if result is not None:
                            return result

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        result = self._try_submit()
                        if result is not None:
                            return result
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                    elif event.unicode.isdigit():
                        self.input_text += event.unicode

            self.draw()
            self.clock.tick(60)

    def _try_submit(self):
        try:
            limit = int(self.input_text) if self.input_text else 0
            if limit < 0:
                raise ValueError
            return limit
        except ValueError:
            self.message = "Invalid input. Enter a whole number (0 = no limit)."
            self.message_color = RED
        return None


# =============================================================================
# Section 7: Main Game GUI
# =============================================================================

class GameGUI:
    """Main game GUI using Pygame."""
    
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("5x5 Matrix Game - Sprint 2")
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

        # Leaderboard state
        self.show_leaderboard = False
        self.leaderboard_entries = []

        # Hint state (for highlighting valid cells in Level 1)
        self.show_hints = False

        # Timer state
        self.time_limit = 0          # 0 = no limit
        self.level_start_ticks = pygame.time.get_ticks()
        self.level_complete = False

        # Initialize game
        self.game_board.initialize_level_1()
        
    def create_buttons(self):
        """Create UI buttons."""
        button_y = WINDOW_HEIGHT - 80
        spacing = BUTTON_WIDTH + 10

        # 8 buttons total
        start_x = (WINDOW_WIDTH - (spacing * 8 - 10)) // 2

        self.new_game_btn = Button(start_x, button_y, BUTTON_WIDTH, BUTTON_HEIGHT, "New Game", GREEN)
        self.clear_btn = Button(start_x + spacing, button_y, BUTTON_WIDTH, BUTTON_HEIGHT, "Clear", YELLOW)
        self.undo_btn = Button(start_x + spacing * 2, button_y, BUTTON_WIDTH, BUTTON_HEIGHT, "Undo", BLUE)
        self.level2_btn = Button(start_x + spacing * 3, button_y, BUTTON_WIDTH, BUTTON_HEIGHT, "Level 2", RED)
        self.level3_btn = Button(start_x + spacing * 4, button_y, BUTTON_WIDTH, BUTTON_HEIGHT, "Level 3", RED)
        self.hint_btn = Button(start_x + spacing * 5, button_y, BUTTON_WIDTH, BUTTON_HEIGHT, "Hint", BLUE)
        self.solution_btn = Button(start_x + spacing * 6, button_y, BUTTON_WIDTH, BUTTON_HEIGHT, "Solution", ORANGE)
        self.leaderboard_btn = Button(start_x + spacing * 7, button_y, BUTTON_WIDTH, BUTTON_HEIGHT, "Top 10", BLUE)
        
    def draw_board(self):
        """Draw the game board (inner 5x5 and outer ring for Level 2)."""
        # Highlight last placed position in Level 1
        last_inner_pos = None
        if self.game_board.level in (1, 3) and self.game_board.last_position is not None:
            last_inner_pos = (self.game_board.last_position[1], self.game_board.last_position[2])

        # Compute valid adjacent empty cells for Level 1 highlighting (used when hints are on)
        valid_cells = set()
        if self.show_hints:
            if self.game_board.level == 1:
                valid_cells = set(self.game_board.get_valid_adjacent_empty_cells())
            elif self.game_board.level == 3:
                valid_cells = set(self.game_board.get_level3_valid_cells(self.game_board.next_number))

        
        # Draw inner 5x5 grid
        for row in range(5):
            for col in range(5):
                x = GRID_OFFSET_X + col * CELL_SIZE
                y = GRID_OFFSET_Y + row * CELL_SIZE
                
                # Highlight: solution cells in orange, last placed in yellow, hints in green
                if (row, col) in self.game_board.solution_cells:
                    pygame.draw.rect(self.screen, ORANGE, (x, y, CELL_SIZE, CELL_SIZE))
                elif last_inner_pos and (row, col) == last_inner_pos:
                    pygame.draw.rect(self.screen, YELLOW, (x, y, CELL_SIZE, CELL_SIZE))
                elif (row, col) in valid_cells:
                    pygame.draw.rect(self.screen, GREEN, (x, y, CELL_SIZE, CELL_SIZE))
                else:
                    pygame.draw.rect(self.screen, WHITE, (x, y, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(self.screen, BLACK, (x, y, CELL_SIZE, CELL_SIZE), 2)

                # Draw number if present
                number = self.game_board.inner_board[row][col]
                if number is not None:
                    # Solution numbers in different color (User Story 13)
                    num_color = ORANGE if (row, col) in self.game_board.solution_cells else BLACK
                    text = self.font_medium.render(str(number), True, num_color)
                    text_rect = text.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                    self.screen.blit(text, text_rect)
        
        # Draw outer ring for Level 2
        if self.game_board.level >= 2:
            self.draw_outer_ring()
    
    def draw_outer_ring(self):
        """Draw the outer ring of 24 cells for Level 2."""
        ring_positions = self._get_ring_positions()
        
        # Corner indices: top-left=0, top-right=6, bottom-right=12, bottom-left=18
        corner_indices = {0, 6, 12, 18}

        hint_indices = set()
        if self.show_hints and self.game_board.level == 2:
            hint_indices = set(self.game_board.get_level2_valid_ring_indices(self.game_board.next_number))
        
        # Draw each ring cell
        for idx, (x, y) in enumerate(ring_positions):
            # Solution ring cells in orange, corners green, others light gray
            if idx in self.game_board.solution_ring_indices:
                cell_color = ORANGE
            elif idx in hint_indices:
                cell_color = YELLOW
            elif idx in corner_indices:
                cell_color = GREEN
            else:
                cell_color = LIGHT_GRAY

            pygame.draw.rect(self.screen, cell_color, (x, y, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(self.screen, DARK_GRAY, (x, y, CELL_SIZE, CELL_SIZE), 2)

            # Draw number if present
            number = self.game_board.outer_ring[idx]
            if number is not None:
                # Solution numbers in different color (User Story 13)
                num_color = ORANGE if idx in self.game_board.solution_ring_indices else BLACK
                text = self.font_medium.render(str(number), True, num_color)
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

        # Timer display (left side)
        if self.time_limit > 0:
            if self.level_complete:
                timer_str = "Time: Done"
                timer_color = DARK_GRAY
            else:
                remaining = self.time_limit - self._get_elapsed_secs()
                if remaining >= 0:
                    timer_str = f"Time: {int(remaining)}s"
                    timer_color = GREEN if remaining > 10 else RED
                else:
                    timer_str = f"Overtime: +{int(-remaining)}s"
                    timer_color = RED
            timer_text = self.font_medium.render(timer_str, True, timer_color)
            self.screen.blit(timer_text, (30, 300))

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
        self.level3_btn.draw(self.screen, self.font_small)
        self.hint_btn.draw(self.screen, self.font_small)
        self.solution_btn.draw(self.screen, self.font_small)
        self.leaderboard_btn.draw(self.screen, self.font_small)

        # Draw leaderboard overlay if toggled on
        if self.show_leaderboard:
            self.draw_leaderboard_overlay()
    
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
                            # Hint is one-time: turn off after a successful move
                            self.show_hints = False
                            self.sound_manager.play_valid_sound()
                            self.message = msg
                            self.message_color = GREEN
                            
                            # Check if level is complete
                            if self.game_board.is_level_complete():
                                self.level_complete = True
                                time_msg = self._apply_time_score()
                                self.sound_manager.play_success_sound()
                                self.message = f"Level 1 Complete! Score: {self.game_board.score}{time_msg}"
                                self.message_color = BLUE
                                self.game_board.save_game_log()
                                self._add_leaderboard_entry()
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

        elif self.game_board.level == 3:
            # Level 3: inner board active again
            for row in range(5):
                for col in range(5):
                    x = GRID_OFFSET_X + col * CELL_SIZE
                    y = GRID_OFFSET_Y + row * CELL_SIZE
                    cell_rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                    if cell_rect.collidepoint(pos):
                        success, msg = self.game_board.place_number(row, col, 'inner')
                        if success:
                            self.show_hints = False
                            self.sound_manager.play_valid_sound()
                            self.message = msg
                            self.message_color = GREEN
        
                            if self.game_board.is_level_complete():
                                self.level_complete = True
                                time_msg = self._apply_time_score()
                                self.sound_manager.play_success_sound()
                                self.message = f"Level 3 Complete! Final Score: {self.game_board.score}{time_msg}"
                                self.message_color = BLUE
                                self.game_board.save_game_log()
                                self._add_leaderboard_entry()
                            elif not self.game_board.has_valid_moves():
                                self.message = "Dead end! Use Undo to rollback."
                                self.message_color = RED
                        else:
                            self.sound_manager.play_invalid_sound()
                            self.message = msg
                            self.message_color = RED
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
                        # Turn off hints after any successful placement
                        self.show_hints = False
                        self.sound_manager.play_valid_sound()
                        self.message = msg
                        self.message_color = GREEN
                        
                        # Check if level is complete
                        if self.game_board.is_level_complete():
                            self.level_complete = True
                            time_msg = self._apply_time_score()
                            self.sound_manager.play_success_sound()
                            self.message = f"Level 2 Complete! Click Level 3 to continue. Final Score: {self.game_board.score}{time_msg}"
                            self.message_color = BLUE
                            self.game_board.save_game_log()
                            self._add_leaderboard_entry()
                        # Check for dead end
                        elif not self.game_board.has_valid_moves():
                            self.message = "Dead end! Use Undo to rollback."
                            self.message_color = RED
                    else:
                        self.sound_manager.play_invalid_sound()
                        self.message = msg
                        self.message_color = RED
                    return
    
    def _get_elapsed_secs(self) -> float:
        """Return seconds elapsed since the current level started."""
        return (pygame.time.get_ticks() - self.level_start_ticks) / 1000.0

    def _apply_time_score(self) -> str:
        """Compute time bonus/penalty, apply to score, return display string."""
        if self.time_limit <= 0:
            return ""
        remaining = self.time_limit - self._get_elapsed_secs()
        if remaining >= 0:
            bonus = int(remaining)
            self.game_board.score += bonus
            return f"  +{bonus}s bonus!"
        else:
            penalty = int(-remaining)
            self.game_board.score = max(0, self.game_board.score - penalty)
            return f"  -{penalty}s penalty."

    def _reset_timer(self):
        """Reset the level timer."""
        self.level_start_ticks = pygame.time.get_ticks()
        self.level_complete = False

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

    def _load_leaderboard(self):
        """Load leaderboard entries from file."""
        leaderboard_file = Path("leaderboard.json")
        if leaderboard_file.exists():
            try:
                with open(leaderboard_file, "r") as f:
                    entries = json.load(f)
                    if isinstance(entries, list):
                        return entries
            except json.JSONDecodeError:
                return []
        return []

    def _save_leaderboard(self, entries):
        """Persist leaderboard entries to file."""
        leaderboard_file = Path("leaderboard.json")
        with open(leaderboard_file, "w") as f:
            json.dump(entries, f, indent=2)

    def _add_leaderboard_entry(self):
        """Add current game result to leaderboard and keep top 10 by score."""
        entry = {
            "player_name": self.game_board.player_name,
            "score": self.game_board.score,
            "level": self.game_board.level,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        entries = self._load_leaderboard()
        entries.append(entry)
        # Sort by score descending, then by most recent timestamp
        entries.sort(key=lambda e: (e.get("score", 0), e.get("timestamp", "")), reverse=True)
        entries = entries[:10]
        self._save_leaderboard(entries)
        self.leaderboard_entries = entries

    def _toggle_leaderboard(self):
        """Toggle leaderboard overlay visibility."""
        if not self.show_leaderboard:
            # Refresh from disk when opening
            self.leaderboard_entries = self._load_leaderboard()
        self.show_leaderboard = not self.show_leaderboard

    def draw_leaderboard_overlay(self):
        """Draw a small panel overlay showing the top 10 scores."""
        width = 360
        height = 320
        x = WINDOW_WIDTH - width - 30
        y = 40

        # Panel background
        panel_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, LIGHT_GRAY, panel_rect, border_radius=8)
        pygame.draw.rect(self.screen, DARK_GRAY, panel_rect, 2, border_radius=8)

        title_text = self.font_medium.render("Top 10 Scores", True, BLACK)
        self.screen.blit(title_text, (x + 20, y + 15))

        if not self.leaderboard_entries:
            empty_text = self.font_small.render("No scores yet.", True, DARK_GRAY)
            self.screen.blit(empty_text, (x + 20, y + 70))
            return

        header_y = y + 60
        name_header = self.font_small.render("Player", True, BLACK)
        score_header = self.font_small.render("Score", True, BLACK)
        level_header = self.font_small.render("Lvl", True, BLACK)
        self.screen.blit(name_header, (x + 20, header_y))
        self.screen.blit(score_header, (x + 190, header_y))
        self.screen.blit(level_header, (x + 275, header_y))

        row_y = header_y + 30
        for idx, entry in enumerate(self.leaderboard_entries[:10]):
            name = str(entry.get("player_name", ""))[:12]
            score = str(entry.get("score", ""))
            level = str(entry.get("level", ""))

            rank_text = self.font_small.render(f"{idx + 1}.", True, DARK_GRAY)
            name_text = self.font_small.render(name, True, BLACK)
            score_text = self.font_small.render(score, True, BLACK)
            level_text = self.font_small.render(level, True, BLACK)

            self.screen.blit(rank_text, (x + 20, row_y))
            self.screen.blit(name_text, (x + 45, row_y))
            self.screen.blit(score_text, (x + 190, row_y))
            self.screen.blit(level_text, (x + 275, row_y))

            row_y += 26
    
    def handle_new_game(self):
        """Start a new game at Level 1."""
        self.game_board.initialize_level_1(random_start=True)
        self._reset_timer()
        self.message = "New game started! Place numbers sequentially."
        self.message_color = BLACK
    
def handle_clear(self):
    """Clear the board based on current level."""
    self.game_board.clear_board(random_restart=True)
    self._reset_timer()
    if self.game_board.level == 1:
        self.message = "Board cleared! Number 1 placed randomly."
    elif self.game_board.level == 2:
        self.message = "Outer ring cleared! Inner board remains."
    elif self.game_board.level == 3:
        self.message = "Inner grid cleared! Outer ring remains."
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
        if self.game_board.level == 1:
            if self.game_board.is_level_complete():
                # Ask for Level 2 time limit before starting
                tls = TimeLimitScreen(self.screen, self.clock, level=2)
                self.time_limit = tls.run()
                self.game_board.initialize_level_2()
                self._reset_timer()
                self.message = "Level 2! Place numbers 2-25 on the outer ring (green = valid)."
                self.message_color = GREEN
            else:
                self.message = "Complete Level 1 first (fill all 25 cells)!"
                self.message_color = RED
        else:
            self.message = "Already in Level 2!"
            self.message_color = RED
    def handle_solution(self):
        """Show a full solution for the current level (User Story 13)."""
        if self.game_board.showing_solution:
            self.message = "Solution already displayed!"
            self.message_color = RED
            return
        success, msg = self.game_board.solve_and_display()
        self.message = msg
        self.message_color = GREEN if success else RED

def handle_level_3(self):
    """Activate Level 3."""
    if self.game_board.level == 2 and self.game_board.is_level_complete():
        tls = TimeLimitScreen(self.screen, self.clock, level=3)
        self.time_limit = tls.run()

        self.game_board.initialize_level_3()
        # Set last_position to current 1 position so adjacency works
        for r in range(5):
            for c in range(5):
                if self.game_board.inner_board[r][c] == 1:
                    self.game_board.last_position = ('inner', r, c)
                    break

        self._reset_timer()
        self.message = "Level 3 started! Place numbers 2-25 in the inner grid."
        self.message_color = GREEN
    else:
        self.message = "Complete Level 2 first!"
        self.message_color = RED

    def _toggle_hints(self):
        """Toggle display of valid Level 1 moves."""
        # Only meaningful in Level 1, but safe to toggle anytime
        self.show_hints = not self.show_hints
    
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
            if self.level3_btn.handle_event(event):
                self.handle_level_3()
            if self.leaderboard_btn.handle_event(event):
                self._toggle_leaderboard()
            if self.hint_btn.handle_event(event):
                self._toggle_hints()
            if self.solution_btn.handle_event(event):
                self.handle_solution()
            
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


# =============================================================================
# Section 8: Entry Point
# =============================================================================

def main():
    """Entry point for the game."""
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("5x5 Matrix Game - Sprint 2")
    clock = pygame.time.Clock()

    login = LoginScreen(screen, clock)
    player_name = login.run()

    time_limit_screen = TimeLimitScreen(screen, clock, level=1)
    time_limit = time_limit_screen.run()

    game = GameGUI()
    game.game_board.player_name = player_name
    game.time_limit = time_limit
    game._reset_timer()
    game.message = f"Welcome, {player_name}! Click on a cell to place numbers."
    game.run()


if __name__ == "__main__":
    main()
