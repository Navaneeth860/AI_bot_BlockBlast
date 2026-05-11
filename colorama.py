#!/usr/bin/env python3
"""
Block Blast Bot - Terminal Version
A comprehensive bot-only implementation with step-by-step visualization
Author: AI Assistant
"""

import random
import time
import copy
from typing import List, Tuple, Optional, Dict, Set
from colorama import init, Fore, Back, Style

# Initialize colorama for Windows compatibility
init(autoreset=True)

# ==================== CONFIGURATION CONSTANTS ====================
# Board dimensions (configurable)
BOARD_SIZE = 9

# Animation and timing
ANIMATION_ENABLED = True  # Set to False to disable animations
MOVE_DELAY = 0.3  # Seconds between bot moves (0.2-0.5 as requested)
CLEAR_FLASH_DELAY = 0.15  # Flash duration for cleared lines

# Debug mode
DEBUG = False  # Set to True for detailed logging

# Random seed for reproducible games (None for random)
RANDOM_SEED = None  # Example: 42 for reproducible bot games

# Color scheme - Each piece type gets unique colors
PIECE_COLORS = {
    0: (Fore.BLACK, Back.BLACK),      # Empty
    1: (Fore.RED, Back.RED),          # Single block
    2: (Fore.GREEN, Back.GREEN),      # Horizontal line
    3: (Fore.YELLOW, Back.YELLOW),    # Vertical line
    4: (Fore.BLUE, Back.BLUE),        # Square
    5: (Fore.MAGENTA, Back.MAGENTA),  # L-shape
    6: (Fore.CYAN, Back.CYAN),        # T-shape
    7: (Fore.WHITE, Back.WHITE),      # Cross
}

# Special colors for effects
CLEAR_COLOR = (Fore.BLACK, Back.LIGHTYELLOW)  # Highlight for cleared lines
BORDER_COLOR = Fore.LIGHTBLUE
TEXT_COLOR = Fore.LIGHTWHITE
HIGHLIGHT_COLOR = Fore.LIGHTGREEN

# ==================== PIECE DEFINITIONS ====================
# Define all possible piece shapes (like Tetris pieces but simplified)
PIECE_SHAPES = {
    1: [(0, 0)],  # Single block
    2: [(0, 0), (1, 0)],  # Horizontal line (2 blocks)
    3: [(0, 0), (0, 1)],  # Vertical line (2 blocks)
    4: [(0, 0), (1, 0), (0, 1), (1, 1)],  # Square (2x2)
    5: [(0, 0), (1, 0), (0, 1)],  # L-shape
    6: [(0, 0), (1, 0), (2, 0)],  # Horizontal line (3 blocks)
    7: [(0, 0), (0, 1), (0, 2)],  # Vertical line (3 blocks)
    8: [(0, 0), (1, 0), (2, 0), (3, 0)],  # Horizontal line (4 blocks)
    9: [(0, 0), (0, 1), (0, 2), (0, 3)],  # Vertical line (4 blocks)
    10: [(0, 0), (1, 0), (2, 0), (1, 1)],  # T-shape
    11: [(1, 0), (0, 1), (1, 1), (2, 1)],  # Cross
    12: [(0, 0), (1, 0), (1, 1), (2, 1)],  # Zigzag
}

# ==================== BOARD CLASS ====================
class Board:
    """Represents the game board and handles placement logic."""
    
    def __init__(self, size: int = BOARD_SIZE):
        self.size = size
        self.grid = [[0 for _ in range(size)] for _ in range(size)]
        self.score = 0
    
    def copy(self):
        """Create a deep copy of the board."""
        new_board = Board(self.size)
        new_board.grid = [row[:] for row in self.grid]
        new_board.score = self.score
        return new_board
    
    def is_valid_placement(self, piece_shape: List[Tuple[int, int]], row: int, col: int, piece_type: int) -> bool:
        """Check if a piece can be placed at the given position."""
        for dr, dc in piece_shape:
            new_row, new_col = row + dr, col + dc
            # Check bounds
            if (new_row < 0 or new_row >= self.size or 
                new_col < 0 or new_col >= self.size):
                return False
            # Check if position is occupied
            if self.grid[new_row][new_col] != 0:
                return False
        return True
    
    def place_piece(self, piece_shape: List[Tuple[int, int]], row: int, col: int, piece_type: int) -> int:
        """Place a piece on the board and return the score gained."""
        # Place the piece
        for dr, dc in piece_shape:
            new_row, new_col = row + dr, col + dc
            self.grid[new_row][new_col] = piece_type
        
        # Clear lines and calculate score
        lines_cleared, lines_info, original_colors = self.clear_lines()
        score_gained = self.calculate_score(lines_cleared)
        self.score += score_gained
        
        return score_gained, lines_cleared, lines_info, original_colors, lines_cleared, lines_info, original_colors
    
    def clear_lines(self) -> Tuple[int, set, dict]:
        """Clear full rows and columns, return number of lines cleared."""
        lines_to_clear = set()
        
        # Check rows
        for row in range(self.size):
            if all(self.grid[row][col] != 0 for col in range(self.size)):
                lines_to_clear.add(('row', row))
        
        # Check columns
        for col in range(self.size):
            if all(self.grid[row][col] != 0 for row in range(self.size)):
                lines_to_clear.add(('col', col))
        
        # Store original colors for animation
        original_colors = {}
        for line_type, index in lines_to_clear:
            if line_type == 'row':
                original_colors[('row', index)] = [self.grid[index][col] for col in range(self.size)]
            else:  # column
                original_colors[('col', index)] = [self.grid[row][index] for row in range(self.size)]
        
        # Clear the lines
        for line_type, index in lines_to_clear:
            if line_type == 'row':
                for col in range(self.size):
                    self.grid[index][col] = 0
            else:  # column
                for row in range(self.size):
                    self.grid[row][index] = 0
        
        return len(lines_to_clear), lines_to_clear, original_colors
    
    def calculate_score(self, lines_cleared: int) -> int:
        """Calculate score based on lines cleared."""
        if lines_cleared == 0:
            return 0
        elif lines_cleared == 1:
            return 100
        elif lines_cleared == 2:
            return 300  # Bonus for multiple clears
        elif lines_cleared == 3:
            return 600
        else:
            return 1000 + (lines_cleared - 4) * 500  # Exponential bonus
    
    def get_valid_moves(self, piece_shape: List[Tuple[int, int]], piece_type: int) -> List[Tuple[int, int]]:
        """Get all valid placement positions for a piece."""
        valid_moves = []
        for row in range(self.size):
            for col in range(self.size):
                if self.is_valid_placement(piece_shape, row, col, piece_type):
                    valid_moves.append((row, col))
        return valid_moves
    
    def count_filled_cells(self) -> int:
        """Count the number of filled cells on the board."""
        return sum(1 for row in self.grid for cell in row if cell != 0)

# ==================== PIECE GENERATOR ====================
class PieceGenerator:
    """Generates random pieces for the game."""
    
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self.piece_types = list(PIECE_SHAPES.keys())
    
    def get_random_piece(self) -> Tuple[int, List[Tuple[int, int]]]:
        """Get a random piece type and its shape."""
        piece_type = random.choice(self.piece_types)
        return piece_type, PIECE_SHAPES[piece_type]

# ==================== GREEDY BOT AI ====================
class GreedyBot:
    """Advanced greedy bot that considers multiple factors for move evaluation."""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
    
    def evaluate_move(self, board: Board, piece_shape: List[Tuple[int, int]], 
                     row: int, col: int, piece_type: int) -> Dict[str, float]:
        """Evaluate a move and return detailed scoring information."""
        
        # Create a copy of the board to simulate the move
        test_board = board.copy()
        
        # Place the piece and get immediate score
        immediate_score = test_board.place_piece(piece_shape, row, col, piece_type)
        lines_cleared = test_board.clear_lines()
        
        # Calculate future opportunities (how many valid moves for next pieces)
        future_opportunities = 0
        test_pieces = 10  # Test with 10 random pieces
        
        for _ in range(test_pieces):
            test_piece_type, test_piece_shape = PieceGenerator().get_random_piece()
            future_moves = test_board.get_valid_moves(test_piece_shape, test_piece_type)
            future_opportunities += len(future_moves)
        
        avg_future_moves = future_opportunities / test_pieces
        
        # Calculate dead-end risk (how blocked is the board)
        filled_cells = test_board.count_filled_cells()
        dead_end_risk = filled_cells / (test_board.size * test_board.size)
        
        # Calculate center preference (center positions are generally better)
        center_row, center_col = test_board.size // 2, test_board.size // 2
        distance_from_center = abs(row - center_row) + abs(col - center_col)
        center_bonus = max(0, (test_board.size - distance_from_center) / test_board.size)
        
        # Combine all factors
        total_score = (
            immediate_score * 1.0 +  # Immediate points are important
            lines_cleared * 50 +   # Bonus for clearing lines
            avg_future_moves * 2.0 + # Future opportunities are crucial
            center_bonus * 10 -     # Slight bonus for center positions
            dead_end_risk * 100     # Heavy penalty for dead-end positions
        )
        
        return {
            'total_score': total_score,
            'immediate_score': immediate_score,
            'lines_cleared': lines_cleared,
            'future_moves': avg_future_moves,
            'dead_end_risk': dead_end_risk,
            'center_bonus': center_bonus
        }
    
    def find_best_move(self, board: Board, piece_shape: List[Tuple[int, int]], 
                      piece_type: int) -> Tuple[Optional[Tuple[int, int]], str]:
        """Find the best move and return it with explanation."""
        
        valid_moves = board.get_valid_moves(piece_shape, piece_type)
        
        if not valid_moves:
            return None, "No valid moves available"
        
        if len(valid_moves) == 1:
            return valid_moves[0], "Only one valid move available"
        
        # Evaluate all moves
        best_move = None
        best_score = float('-inf')
        best_details = None
        
        for move in valid_moves:
            row, col = move
            details = self.evaluate_move(board, piece_shape, row, col, piece_type)
            
            if details['total_score'] > best_score:
                best_score = details['total_score']
                best_move = move
                best_details = details
        
        # Generate explanation
        if best_details['lines_cleared'] > 0:
            reason = f"Clears {best_details['lines_cleared']} line(s) for {best_details['immediate_score']} points"
        elif best_details['future_moves'] > 5:
            reason = f"Maximizes future opportunities ({best_details['future_moves']:.1f} avg moves)"
        elif best_details['dead_end_risk'] < 0.3:
            reason = f"Avoids dead-end positions (risk: {best_details['dead_end_risk']:.2f})"
        else:
            reason = f"Best overall score: {best_score:.1f}"
        
        if self.debug:
            print(f"  Evaluated {len(valid_moves)} moves")
            print(f"  Best move score: {best_score:.1f}")
            print(f"  Lines cleared: {best_details['lines_cleared']}")
            print(f"  Future moves: {best_details['future_moves']:.1f}")
            print(f"  Dead-end risk: {best_details['dead_end_risk']:.2f}")
        
        return best_move, reason

# ==================== GAME ENGINE ====================
class GameEngine:
    """Main game engine that coordinates all components."""
    
    def __init__(self, board_size: int = BOARD_SIZE, animation_enabled: bool = True, 
                 debug: bool = False, seed: Optional[int] = None):
        self.board = Board(board_size)
        self.piece_generator = PieceGenerator(seed)
        self.bot = GreedyBot(debug)
        self.animation_enabled = animation_enabled
        self.debug = debug
        self.game_over = False
        self.moves_count = 0
        
        if seed is not None:
            random.seed(seed)
    
    def animate_line_clear(self, lines_info: set, original_colors: dict, animation_type: str = "flash"):
        """Animate line clearing with special effects."""
        if not self.animation_enabled or not lines_info:
            return
        
        if animation_type == "flash":
            # Simple flash effect - show cleared lines in special color
            print(f"{HIGHLIGHT_COLOR}🎯 Lines cleared: {len(lines_info)} 🎯")
            
            # Flash the cleared lines
            for frame in range(3):
                # Show with effect
                self.render_board(lines_info, use_clear_color=True)
                time.sleep(CLEAR_FLASH_DELAY)
                
                # Show normal
                self.render_board()
                time.sleep(CLEAR_FLASH_DELAY / 2)
    
    def render_board(self, highlight_lines: set = None, use_clear_color: bool = False, 
                    original_colors: dict = None, particle_effect: bool = False, 
                    frame: int = 0):
        """Render the board with colors, borders, and special effects."""
        
        def get_cell_display(row: int, col: int) -> Tuple[str, str]:
            """Get the display characters and colors for a cell."""
            cell_value = self.board.grid[row][col]
            
            # Check if this cell should be highlighted
            is_highlighted = False
            if highlight_lines:
                for line_type, index in highlight_lines:
                    if (line_type == 'row' and row == index) or (line_type == 'col' and col == index):
                        is_highlighted = True
                        break
            
            # Determine colors
            if is_highlighted:
                if use_clear_color:
                    fg_color, bg_color = CLEAR_COLOR
                elif particle_effect:
                    # Particle effect - cycling colors
                    particle_colors = [Fore.YELLOW, Fore.RED, Fore.GREEN, Fore.BLUE, Fore.MAGENTA]
                    fg_color = particle_colors[frame % len(particle_colors)]
                    bg_color = Back.BLACK
                elif original_colors and (row, col) in [(r, c) for line_type, idx in original_colors.keys() 
                                                         for r in range(self.board.size) for c in range(self.board.size)
                                                         if (line_type == 'row' and r == idx) or (line_type == 'col' and c == idx)]:
                    # Use original color from the saved state
                    for line_type, index in original_colors.keys():
                        if (line_type == 'row' and row == index) or (line_type == 'col' and col == index):
                            # Find the original color in this line
                            if line_type == 'row':
                                original_color = original_colors[(line_type, index)][col]
                            else:  # column
                                original_color = original_colors[(line_type, index)][row]
                            fg_color, bg_color = PIECE_COLORS.get(original_color, (Fore.WHITE, Back.BLACK))
                            break
                    else:
                        fg_color, bg_color = PIECE_COLORS.get(cell_value, (Fore.WHITE, Back.BLACK))
                else:
                    fg_color, bg_color = PIECE_COLORS.get(cell_value, (Fore.WHITE, Back.BLACK))
            else:
                fg_color, bg_color = PIECE_COLORS.get(cell_value, (Fore.WHITE, Back.BLACK))
            
            # Choose display character
            if cell_value == 0:
                char = " · "
            elif is_highlighted and use_clear_color:
                char = " ★ "
            elif particle_effect and is_highlighted:
                char = " ✦ "
            else:
                char = " ■ "
            
            return fg_color, bg_color, char
        
        print(f"\n{BORDER_COLOR}┌{'─' * (self.board.size * 3)}┐")
        
        for row in range(self.board.size):
            print(f"{BORDER_COLOR}│", end="")
            for col in range(self.board.size):
                fg_color, bg_color, char = get_cell_display(row, col)
                print(f"{bg_color}{fg_color}{char}", end="")
            print(f"{BORDER_COLOR}│")
        
        print(f"{BORDER_COLOR}└{'─' * (self.board.size * 3)}┘")
        
        # Add particle effect text
        if particle_effect and highlight_lines:
            print(f"{HIGHLIGHT_COLOR}✨ Lines cleared! ✨")
        elif use_clear_color and highlight_lines:
            print(f"{HIGHLIGHT_COLOR}💥 BOOM! Lines clearing! 💥")
        
        print()
    
    def play_bot_game(self):
        """Play a complete bot game with visualization."""
        print(f"{BORDER_COLOR}{'='*60}")
        print(f"{TEXT_COLOR}BLOCK BLAST BOT - TERMINAL VERSION")
        print(f"{BORDER_COLOR}{'='*60}")
        print()
        
        while not self.game_over:
            self.play_single_move()
            if self.animation_enabled:
                time.sleep(MOVE_DELAY)
        
        # Game over
        print(f"\n{BORDER_COLOR}{'='*60}")
        print(f"{TEXT_COLOR}BOT LOST! Final Score: {self.board.score}")
        print(f"{BORDER_COLOR}{'='*60}")
    
    def play_single_move(self):
        """Play a single bot move."""
        self.moves_count += 1
        
        # Generate new piece
        piece_type, piece_shape = self.piece_generator.get_random_piece()
        
        print(f"\n{BORDER_COLOR}--- Move #{self.moves_count} ---")
        print(f"{TEXT_COLOR}Current Piece: Type {piece_type}")
        self.print_piece_info(piece_type, piece_shape)
        
        # Find best move
        best_move, reason = self.bot.find_best_move(self.board, piece_shape, piece_type)
        
        if best_move is None:
            self.game_over = True
            return
        
        row, col = best_move
        print(f"{HIGHLIGHT_COLOR}Bot chooses: Row {row}, Col {col}")
        print(f"{TEXT_COLOR}Reason: {reason}")
        
        if self.debug:
            print(f"\n{TEXT_COLOR}Board before move:")
        self.render_board()
        
        # Execute the move
        result = self.board.place_piece(piece_shape, row, col, piece_type)
        score_gained, lines_cleared, lines_info, original_colors = result
        
        # Show the result
        if self.debug:
            print(f"\n{TEXT_COLOR}Board after placement (Score: +{score_gained}, Total: {self.board.score}):")
            self.render_board()
        
        # Animate line clearing if any lines were cleared
        if lines_cleared > 0:
            print(f"{HIGHLIGHT_COLOR}🎯 Lines cleared: {lines_cleared} 🎯")
            self.animate_line_clear(lines_info, original_colors, "flash")
            print(f"{HIGHLIGHT_COLOR}✨ Score gained: +{score_gained} ✨")
        
        if not self.debug:
            print(f"\n{TEXT_COLOR}Board after move (Score: {self.board.score}):")
            self.render_board()
        
        # Check if game should continue
        self.check_game_over()

    def render_board_simple(self):
        """Simple board rendering without animations."""
        print(f"\n{BORDER_COLOR}┌{'─' * (self.board.size * 3)}┐")
        
        for row in range(self.board.size):
            print(f"{BORDER_COLOR}│", end="")
            for col in range(self.board.size):
                cell_value = self.board.grid[row][col]
                fg_color, bg_color = PIECE_COLORS.get(cell_value, (Fore.WHITE, Back.BLACK))
                
                if cell_value == 0:
                    print(f"{bg_color}{fg_color} · ", end="")
                else:
                    print(f"{bg_color}{fg_color} ■ ", end="")
            print(f"{BORDER_COLOR}│")
        
        print(f"{BORDER_COLOR}└{'─' * (self.board.size * 3)}┘")
        print()
    
    def check_game_over(self):
        """Check if the game should end."""
        # Generate a test piece to see if any moves are possible
        test_piece_type, test_piece_shape = self.piece_generator.get_random_piece()
        valid_moves = self.board.get_valid_moves(test_piece_shape, test_piece_type)
        
        if not valid_moves:
            self.game_over = True
    
    def print_piece_info(self, piece_type: int, piece_shape: List[Tuple[int, int]]):
        """Print information about the current piece."""
        print(f"{TEXT_COLOR}Shape: {piece_shape}")
        print(f"{TEXT_COLOR}Size: {len(piece_shape)} blocks")
    
    def render_board(self):
        """Render the board with colors and borders."""
        print(f"\n{BORDER_COLOR}┌{'─' * (self.board.size * 3)}┐")
        
        for row in range(self.board.size):
            print(f"{BORDER_COLOR}│", end="")
            for col in range(self.board.size):
                cell_value = self.board.grid[row][col]
                fg_color, bg_color = PIECE_COLORS.get(cell_value, (Fore.WHITE, Back.BLACK))
                
                if cell_value == 0:
                    print(f"{bg_color}{fg_color} · ", end="")
                else:
                    print(f"{bg_color}{fg_color} ■ ", end="")
            print(f"{BORDER_COLOR}│")
        
        print(f"{BORDER_COLOR}└{'─' * (self.board.size * 3)}┘")
        print()

# ==================== MAIN EXECUTION ====================
def main():
    """Main function to run the bot game."""
    print(f"{TEXT_COLOR}Initializing Block Blast Bot...")
    print(f"{TEXT_COLOR}Configuration:")
    print(f"  Board Size: {BOARD_SIZE}x{BOARD_SIZE}")
    print(f"  Animation: {'Enabled' if ANIMATION_ENABLED else 'Disabled'}")
    print(f"  Move Delay: {MOVE_DELAY}s")
    print(f"  Debug Mode: {'On' if DEBUG else 'Off'}")
    print(f"  Random Seed: {RANDOM_SEED if RANDOM_SEED else 'Random'}")
    print()
    
    # Create and run the game
    game = GameEngine(
        board_size=BOARD_SIZE,
        animation_enabled=ANIMATION_ENABLED,
        debug=DEBUG,
        seed=RANDOM_SEED
    )
    
    game.play_bot_game()

if __name__ == "__main__":
    main()