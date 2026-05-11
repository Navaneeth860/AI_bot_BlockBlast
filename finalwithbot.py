# -----------------------------------------------------------------------------
# BLOCK BLAST – INTEGRATED VERSION with BOT
# Original Animated Game + Bot Player
# -----------------------------------------------------------------------------

import tkinter as tk
from tkinter import messagebox
import random
import time
import math
import threading

# Game Configuration
CELL_SIZE = 40
GRID_SIZE = 10
BOARD_WIDTH = GRID_SIZE * CELL_SIZE
BLOCK_AREA_WIDTH = CELL_SIZE * 6
ANIMATION_SPEED = 15  # Milliseconds between animation frames
FALL_SPEED = 0.8  # Speed of falling animation

# Color palette
BOARD_COLORS = {
    'empty': 'white',
    'filled': '#444444',
    'grid_line': '#aaaaaa',
    'block_area_bg': '#dddddd',
    'block_outline': '#555555',
    'preview_fill': '#cccccc',
    'preview_outline': '#999999',
    'arrow': '#ff6b35'
}

BLOCK_COLORS = [
    "#4cc9f0",  # Light blue
    "#f72585",  # Pink
    "#7209b7",  # Purple
    "#3a0ca3",  # Dark blue
    "#4361ee",  # Blue
    "#ff6b35",  # Orange
    "#06d6a0",  # Green
    "#ffd23f",  # Yellow
]

# -----------------------------
# BACKEND: GAME ENGINE (LOGIC)
# -----------------------------
class BlockBlastEngine:
    """Game engine that handles all game logic."""
    
    def __init__(self):
        self.board = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.score = 0
        self.game_over = False
        
        # Define all possible block shapes
        self.shapes = [
            [[1]],                    # Single block
            [[1, 1]],                 # Horizontal line (2)
            [[1], [1]],               # Vertical line (2)
            [[1, 1], [1, 1]],         # 2x2 square
            [[1, 1, 1]],              # Horizontal line (3)
            [[1], [1], [1]],          # Vertical line (3)
            [[1, 0], [1, 1]],         # L-shape
            [[0, 1], [1, 1]],         # Reverse L-shape
            [[1, 1, 1, 1]],           # Horizontal line (4)
            [[1], [1], [1], [1]],    # Vertical line (4)
        ]

    def generate_blocks(self):
        """Generate 3 random blocks for the player to use."""
        return [random.choice(self.shapes) for _ in range(3)]

    def get_board(self):
        """Return the current state of the board."""
        return self.board

    def can_place(self, block, start_row, start_col):
        """Check if a block can be placed at the given position."""
        block_height = len(block)
        block_width = len(block[0])
        
        if start_row < 0 or start_col < 0:
            return False
        if start_row + block_height > GRID_SIZE or start_col + block_width > GRID_SIZE:
            return False
            
        for r in range(block_height):
            for c in range(block_width):
                if block[r][c] == 1:
                    if self.board[start_row + r][start_col + c] == 1:
                        return False
        
        return True

    def place_block(self, block, start_row, start_col):
        """Place a block on the board if valid."""
        block_height = len(block)
        block_width = len(block[0])
        
        for r in range(block_height):
            for c in range(block_width):
                if block[r][c] == 1:
                    self.board[start_row + r][start_col + c] = 1

    def clear_lines(self):
        """Clear full rows and columns from the board."""
        lines_cleared = 0
        
        # Clear full rows
        for r in range(GRID_SIZE):
            if all(self.board[r][c] == 1 for c in range(GRID_SIZE)):
                for c in range(GRID_SIZE):
                    self.board[r][c] = 0
                lines_cleared += 1

        # Clear full columns
        for c in range(GRID_SIZE):
            if all(self.board[r][c] == 1 for r in range(GRID_SIZE)):
                for r in range(GRID_SIZE):
                    self.board[r][c] = 0
                lines_cleared += 1
        
        return lines_cleared

    def check_game_over(self, available_blocks):
        """Check if the game is over (no valid moves available)."""
        for block in available_blocks:
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    if self.can_place(block, r, c):
                        return False
        return True

    def reset_board(self):
        """Reset the board to start a new game."""
        self.board = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.score = 0
        self.game_over = False

    def find_drop_position(self, block, target_col):
        """Find the lowest valid row for dropping a block in a specific column."""
        for row in range(GRID_SIZE - len(block) + 1):
            if self.can_place(block, row, target_col):
                # Check if we can go lower
                if row + 1 < GRID_SIZE and self.can_place(block, row + 1, target_col):
                    continue
                return row
        return -1  # No valid position


# -----------------------------
# INTELLIGENT BOT ENGINE
# -----------------------------
class BlockBlastBot:
    """Intelligent bot that plays Block Blast automatically."""
    
    def __init__(self, engine):
        self.engine = engine
        self.debug = True  # Set to True to see bot's reasoning
    
    def evaluate_position(self, block, row, col):
        """Evaluate how good a position is for placing a block."""
        # Create a copy of the board to simulate the move
        test_engine = BlockBlastEngine()
        test_engine.board = [row[:] for row in self.engine.board]  # Deep copy
        test_engine.score = self.engine.score
        
        # Place the block
        if test_engine.can_place(block, row, col):
            test_engine.place_block(block, row, col)
            lines_cleared = test_engine.clear_lines()
            
            # Calculate score based on multiple factors
            immediate_score = lines_cleared * 100
            
            # Count future opportunities (how many valid moves for next pieces)
            future_opportunities = 0
            test_pieces = 5  # Test with 5 random pieces
            
            for _ in range(test_pieces):
                test_block = random.choice(self.engine.shapes)
                for r in range(GRID_SIZE):
                    for c in range(GRID_SIZE):
                        if test_engine.can_place(test_block, r, c):
                            future_opportunities += 1
            
            avg_future_moves = future_opportunities / test_pieces
            
            # Calculate dead-end risk (how blocked is the board)
            filled_cells = sum(sum(row) for row in test_engine.board)
            dead_end_risk = filled_cells / (GRID_SIZE * GRID_SIZE)
            
            # Combine all factors
            total_score = (
                immediate_score * 1.0 +      # Immediate points
                lines_cleared * 50 +       # Bonus for clearing lines
                avg_future_moves * 1.5 -   # Future opportunities
                dead_end_risk * 200        # Heavy penalty for dead-end positions
            )
            
            return total_score, lines_cleared
        
        return float('-inf'), 0
    
    def find_best_move(self, available_blocks):
        """Find the best move among all available blocks and positions."""
        best_score = float('-inf')
        best_move = None
        best_block_idx = None
        
        # Evaluate all blocks and positions
        for block_idx, block in enumerate(available_blocks):
            # Check if block is already used
            is_used = all(all(cell == 0 for cell in row) for row in block)
            if is_used:
                continue
                
            for row in range(GRID_SIZE):
                for col in range(GRID_SIZE):
                    if self.engine.can_place(block, row, col):
                        score, lines_cleared = self.evaluate_position(block, row, col)
                        
                        if score > best_score:
                            best_score = score
                            best_move = (row, col)
                            best_block_idx = block_idx
        
        return best_move, best_block_idx
    
    def get_move_explanation(self, block, row, col, score, lines_cleared):
        """Generate an explanation for why this move was chosen."""
        if lines_cleared > 0:
            return f"Clears {lines_cleared} line(s) for {lines_cleared * 100} points"
        elif score > 100:
            return "Maximizes future placement opportunities"
        elif row > GRID_SIZE // 2:
            return "Strategic lower position for better block utilization"
        else:
            return "Best available position considering board state"


# -----------------------------
# FRONTEND: MAIN GAME GUI
# -----------------------------
class BlockBlastGUI:
    """Enhanced GUI for Block Blast with animations."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Block Blast – Enhanced Version")
        self.root.resizable(False, False)
        self.root.configure(bg='#f0f0f0')
        
        # Initialize game engine
        self.engine = BlockBlastEngine()
        
        # Game state
        self.current_blocks = self.engine.generate_blocks()
        self.selected_block = None
        self.selected_index = None
        self.preview_position = None
        self.game_over = False
        
        # Animation state
        self.animation_queue = []
        self.is_animating = False
        
        self.setup_ui()
        self.draw_board()
        self.draw_blocks()
        
        # Bind events
        self.root.bind('<Button-1>', self.on_click)
        self.root.bind('<Motion>', self.on_motion)

    def setup_ui(self):
        """Setup the user interface."""
        # Create main container
        self.main_container = tk.Frame(self.root, bg='#f0f0f0')
        self.main_container.pack(padx=20, pady=20)
        
        # Create game board
        self.board_frame = tk.Frame(self.main_container, bg='#ffffff', relief='raised', bd=2)
        self.board_frame.grid(row=0, column=0, padx=(0, 20))
        
        self.board_canvas = tk.Canvas(
            self.board_frame,
            width=BOARD_WIDTH,
            height=BOARD_WIDTH,
            bg="#ffffff",
            highlightthickness=0
        )
        self.board_canvas.pack(padx=10, pady=10)
        
        # Create side panel
        self.side_panel = tk.Frame(self.main_container, bg='#ffffff')
        self.side_panel.grid(row=0, column=1)
        
        # Score display
        self.score_label = tk.Label(
            self.side_panel,
            text="Score: 0",
            font=('Arial', 18, 'bold'),
            fg='#333333',
            bg='#ffffff'
        )
        self.score_label.pack(pady=(0, 20))
        
        # Block area
        self.block_area = tk.Frame(self.side_panel, bg='#ffffff')
        self.block_area.pack()
        
        # Add bot player button
        self.bot_button = tk.Button(
            self.side_panel,
            text="🤖 Start Bot Player",
            command=self.start_bot_player,
            bg='#3498db',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=15,
            pady=8
        )
        self.bot_button.pack(pady=(20, 0))

    def draw_board(self):
        """Draw the game board."""
        self.board_canvas.delete("all")
        board = self.engine.get_board()
        
        # Draw cells
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if board[r][c] == 1:
                    color = BOARD_COLORS['filled']
                    outline = '#333333'
                else:
                    color = BOARD_COLORS['empty']
                    outline = BOARD_COLORS['grid_line']
                
                self.board_canvas.create_rectangle(
                    c * CELL_SIZE, 
                    r * CELL_SIZE, 
                    (c + 1) * CELL_SIZE, 
                    (r + 1) * CELL_SIZE,
                    fill=color, 
                    outline=outline
                )
        
        # Add grid lines
        for i in range(GRID_SIZE + 1):
            self.board_canvas.create_line(
                i * CELL_SIZE, 0, i * CELL_SIZE, BOARD_WIDTH,
                fill=BOARD_COLORS['grid_line'], width=1
            )
            self.board_canvas.create_line(
                0, i * CELL_SIZE, BOARD_WIDTH, i * CELL_SIZE,
                fill=BOARD_COLORS['grid_line'], width=1
            )
        
        # Draw preview if available
        if self.preview_position and self.selected_block:
            self.draw_preview()

    def draw_blocks(self):
        """Draw the available blocks."""
        # Clear existing blocks display
        for widget in self.block_area.winfo_children():
            widget.destroy()
        
        # Create labels for blocks
        for i, block in enumerate(self.current_blocks):
            is_used = all(all(cell == 0 for cell in row) for row in block)
            if is_used:
                continue
                
            block_frame = tk.Frame(self.block_area, bg='#ffffff', relief='raised', bd=2)
            block_frame.pack(pady=5)
            
            canvas = tk.Canvas(block_frame, width=CELL_SIZE * 3, height=CELL_SIZE * 3, bg='#ffffff')
            canvas.pack()
            
            # Draw block
            block_height = len(block)
            block_width = len(block[0])
            
            for r in range(block_height):
                for c in range(block_width):
                    if block[r][c] == 1:
                        color = BLOCK_COLORS[i % len(BLOCK_COLORS)]
                        canvas.create_rectangle(
                            c * CELL_SIZE + 10,
                            r * CELL_SIZE + 10,
                            (c + 1) * CELL_SIZE + 10,
                            (r + 1) * CELL_SIZE + 10,
                            fill=color,
                            outline='#333333',
                            width=2
                        )
            
            # Bind click event
            canvas.bind('<Button-1>', lambda e, idx=i: self.select_block(idx))

    def draw_preview(self):
        """Draw preview of where the block will be placed."""
        if not self.selected_block or not self.preview_position:
            return
        
        row, col = self.preview_position
        block_height = len(self.selected_block)
        block_width = len(self.selected_block[0])
        
        for r in range(block_height):
            for c in range(block_width):
                if self.selected_block[r][c] == 1:
                    x1 = (col + c) * CELL_SIZE
                    y1 = (row + r) * CELL_SIZE
                    x2 = x1 + CELL_SIZE
                    y2 = y1 + CELL_SIZE
                    
                    self.board_canvas.create_rectangle(
                        x1, y1, x2, y2,
                        fill=BOARD_COLORS['preview_fill'],
                        outline=BOARD_COLORS['preview_outline'],
                        width=2,
                        stipple='gray50'
                    )

    def select_block(self, index):
        """Select a block for placement."""
        if index < len(self.current_blocks):
            self.selected_block = self.current_blocks[index]
            self.selected_index = index

    def on_click(self, event):
        """Handle mouse click events."""
        if self.game_over or not self.selected_block:
            return
        
        # Get board position
        x, y = event.x, event.y
        col = x // CELL_SIZE
        row = y // CELL_SIZE
        
        # Try to place the block
        if self.engine.can_place(self.selected_block, row, col):
            self.place_block_with_animation(row, col)

    def on_motion(self, event):
        """Handle mouse motion for preview."""
        if not self.selected_block:
            return
        
        x, y = event.x, event.y
        col = x // CELL_SIZE
        row = y // CELL_SIZE
        
        if self.engine.can_place(self.selected_block, row, col):
            self.preview_position = (row, col)
        else:
            self.preview_position = None
        
        self.draw_board()

    def place_block_with_animation(self, row, col):
        """Place block with animation effect."""
        self.engine.place_block(self.selected_block, row, col)
        
        # Add placement animation
        self.add_placement_animation(row, col, self.selected_block)
        
        # Clear lines
        lines_cleared = self.engine.clear_lines()
        if lines_cleared > 0:
            self.engine.score += lines_cleared * 100
            self.add_clear_animation(lines_cleared)
        
        # Mark block as used
        self.current_blocks[self.selected_index] = [[0]]
        self.selected_block = None
        self.selected_index = None
        self.preview_position = None
        
        # Update display
        self.draw_board()
        self.draw_blocks()
        self.update_score()
        
        # Check for game over
        if self.engine.check_game_over(self.current_blocks):
            self.game_over = True
            self.show_game_over()
        elif all(all(all(cell == 0 for cell in row) for row in block) for block in self.current_blocks):
            # All blocks used, generate new ones
            self.current_blocks = self.engine.generate_blocks()
            self.draw_blocks()

    def add_placement_animation(self, row, col, block):
        """Add animation when placing a block."""
        # Simple highlight effect
        block_height = len(block)
        block_width = len(block[0])
        
        for r in range(block_height):
            for c in range(block_width):
                if block[r][c] == 1:
                    x1 = (col + c) * CELL_SIZE
                    y1 = (row + r) * CELL_SIZE
                    x2 = x1 + CELL_SIZE
                    y2 = y1 + CELL_SIZE
                    
                    # Create highlight rectangle
                    highlight = self.board_canvas.create_rectangle(
                        x1, y1, x2, y2,
                        fill='yellow',
                        outline='orange',
                        width=3
                    )
                    
                    # Fade out
                    self.root.after(200, lambda: self.board_canvas.delete(highlight))

    def add_clear_animation(self, lines_cleared):
        """Add animation when lines are cleared."""
        # Flash effect
        for i in range(3):
            self.board_canvas.config(bg='#ffff00' if i % 2 == 0 else '#ffffff')
            self.root.update()
            time.sleep(0.1)

    def update_score(self):
        """Update score display."""
        self.score_label.config(text=f"Score: {self.engine.score}")

    def show_game_over(self):
        """Show game over message."""
        messagebox.showinfo("Game Over", f"Final Score: {self.engine.score}")

    def start_bot_player(self):
        """Start the bot player in a new window."""
        bot_window = tk.Toplevel(self.root)
        bot_window.title("Block Blast Bot Player")
        bot_window.resizable(False, False)
        bot_window.configure(bg='#2c3e50')
        
        # Create bot GUI
        bot_gui = BlockBlastBotGUI(bot_window)


# -----------------------------
# BOT GUI (SEPARATE WINDOW)
# -----------------------------
class BlockBlastBotGUI:
    """GUI for the bot to play Block Blast automatically."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Block Blast Bot - Automated Player")
        self.root.resizable(False, False)
        self.root.configure(bg='#2c3e50')
        
        # Initialize game engine
        self.engine = BlockBlastEngine()
        self.bot = BlockBlastBot(self.engine)
        
        # Game state
        self.current_blocks = self.engine.generate_blocks()
        self.is_playing = False
        self.game_speed = 0.5  # Seconds between moves
        self.debug = True
        
        # Statistics
        self.moves_count = 0
        self.games_played = 0
        
        self.setup_ui()
        self.draw_board()
        self.draw_blocks()
        
        # Start auto-play after a short delay
        self.root.after(1000, self.start_auto_play)

    def setup_ui(self):
        """Setup the user interface for the bot player."""
        # Create main container
        self.main_container = tk.Frame(self.root, bg='#2c3e50')
        self.main_container.pack(padx=20, pady=20)
        
        # Create header with title and statistics
        self.header_frame = tk.Frame(self.main_container, bg='#2c3e50')
        self.header_frame.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        self.title_label = tk.Label(
            self.header_frame,
            text="🤖 BLOCK BLAST BOT PLAYER 🤖",
            font=('Arial', 24, 'bold'),
            fg='#3498db',
            bg='#2c3e50'
        )
        self.title_label.pack()
        
        self.subtitle_label = tk.Label(
            self.header_frame,
            text="Intelligent AI Playing Automatically",
            font=('Arial', 12, 'italic'),
            fg='#ecf0f1',
            bg='#2c3e50'
        )
        self.subtitle_label.pack()
        
        # Create game board
        self.board_frame = tk.Frame(self.main_container, bg='#34495e', relief='raised', bd=3)
        self.board_frame.grid(row=1, column=0, padx=(0, 20))
        
        self.board_canvas = tk.Canvas(
            self.board_frame,
            width=BOARD_WIDTH,
            height=BOARD_WIDTH,
            bg="#2c3e50",
            highlightthickness=0
        )
        self.board_canvas.pack(padx=8, pady=8)
        
        # Create info panel
        self.info_frame = tk.Frame(self.main_container, bg='#34495e', relief='raised', bd=3)
        self.info_frame.grid(row=1, column=1)
        
        # Score display
        self.score_label = tk.Label(
            self.info_frame,
            text="Score: 0",
            font=('Arial', 18, 'bold'),
            fg='#e74c3c',
            bg='#34495e'
        )
        self.score_label.pack(pady=(15, 10))
        
        # Statistics
        self.stats_frame = tk.Frame(self.info_frame, bg='#34495e')
        self.stats_frame.pack(pady=10)
        
        self.moves_label = tk.Label(
            self.stats_frame,
            text="Moves: 0",
            font=('Arial', 12),
            fg='#ecf0f1',
            bg='#34495e'
        )
        self.moves_label.pack()
        
        self.games_label = tk.Label(
            self.stats_frame,
            text="Games: 0",
            font=('Arial', 12),
            fg='#ecf0f1',
            bg='#34495e'
        )
        self.games_label.pack()
        
        # Current blocks display
        self.blocks_label = tk.Label(
            self.info_frame,
            text="Available Blocks:",
            font=('Arial', 12, 'bold'),
            fg='#3498db',
            bg='#34495e'
        )
        self.blocks_label.pack(pady=(15, 5))
        
        self.blocks_canvas = tk.Canvas(
            self.info_frame,
            width=150,
            height=200,
            bg='#2c3e50',
            highlightthickness=0
        )
        self.blocks_canvas.pack(pady=5)
        
        # Control buttons
        self.control_frame = tk.Frame(self.info_frame, bg='#34495e')
        self.control_frame.pack(pady=15)
        
        self.pause_button = tk.Button(
            self.control_frame,
            text="⏸ Pause",
            command=self.toggle_pause,
            bg='#f39c12',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=10,
            pady=5
        )
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        self.speed_button = tk.Button(
            self.control_frame,
            text="⚡ Speed",
            command=self.change_speed,
            bg='#27ae60',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=10,
            pady=5
        )
        self.speed_button.pack(side=tk.LEFT, padx=5)
        
        # Move explanation
        self.explanation_label = tk.Label(
            self.info_frame,
            text="Bot is thinking...",
            font=('Arial', 10, 'italic'),
            fg='#bdc3c7',
            bg='#34495e',
            wraplength=130,
            justify='center'
        )
        self.explanation_label.pack(pady=(10, 15))

    def draw_board(self):
        """Draw the game board with enhanced colors."""
        self.board_canvas.delete("all")
        board = self.engine.get_board()
        
        # Draw grid with colors
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if board[r][c] == 1:
                    # Filled cell - use vibrant colors
                    color = '#e74c3c'  # Red for filled cells
                    outline = '#c0392b'
                else:
                    # Empty cell - use subtle colors
                    color = '#ecf0f1'  # Light gray
                    outline = '#bdc3c7'
                
                self.board_canvas.create_rectangle(
                    c * CELL_SIZE, 
                    r * CELL_SIZE, 
                    (c + 1) * CELL_SIZE, 
                    (r + 1) * CELL_SIZE,
                    fill=color, 
                    outline=outline,
                    width=2
                )
        
        # Add grid lines for better visibility
        for i in range(GRID_SIZE + 1):
            self.board_canvas.create_line(
                i * CELL_SIZE, 0, i * CELL_SIZE, BOARD_WIDTH,
                fill='#7f8c8d', width=1
            )
            self.board_canvas.create_line(
                0, i * CELL_SIZE, BOARD_WIDTH, i * CELL_SIZE,
                fill='#7f8c8d', width=1
            )

    def draw_blocks(self):
        """Draw the available blocks with colors."""
        self.blocks_canvas.delete("all")
        
        y_position = 10
        block_spacing = 15
        
        for i, block in enumerate(self.current_blocks):
            # Check if block is already used
            is_used = all(all(cell == 0 for cell in row) for row in block)
            if is_used:
                continue
                
            block_height = len(block)
            block_width = len(block[0])
            
            # Calculate position to center the block
            x_offset = (150 - (block_width * 20)) // 2
            color = BLOCK_COLORS[i % len(BLOCK_COLORS)]
            
            # Draw the block with enhanced styling
            for r in range(block_height):
                for c in range(block_width):
                    if block[r][c] == 1:
                        x1 = x_offset + c * 20
                        y1 = y_position + r * 20
                        x2 = x1 + 18
                        y2 = y1 + 18
                        
                        # Draw with 3D effect
                        self.blocks_canvas.create_rectangle(
                            x1, y1, x2, y2,
                            fill=color,
                            outline='#2c3e50',
                            width=2
                        )
                        
                        # Add highlight
                        self.blocks_canvas.create_line(
                            x1 + 2, y1 + 2, x2 - 2, y1 + 2,
                            fill='white',
                            width=1
                        )
            
            y_position += (block_height * 20) + block_spacing

    def make_bot_move(self):
        """Make a single bot move with intelligent decision making."""
        if self.engine.game_over or not self.is_playing:
            return
        
        # Find the best move
        best_position, best_block_idx = self.bot.find_best_move(self.current_blocks)
        
        if best_position is None or best_block_idx is None:
            # No valid moves left - game over
            self.engine.game_over = True
            self.show_game_over()
            return
        
        row, col = best_position
        selected_block = self.current_blocks[best_block_idx]
        
        # Get explanation for the move
        score, lines_cleared = self.bot.evaluate_position(selected_block, row, col)
        explanation = self.bot.get_move_explanation(selected_block, row, col, score, lines_cleared)
        
        # Update UI with move information
        self.explanation_label.config(text=explanation)
        
        if self.debug:
            print(f"Bot Move #{self.moves_count + 1}:")
            print(f"  Selected block: {best_block_idx}")
            print(f"  Position: Row {row}, Col {col}")
            print(f"  Reason: {explanation}")
            print(f"  Expected score: {score:.1f}")
        
        # Place the block
        self.engine.place_block(selected_block, row, col)
        
        # Clear lines and update score
        lines_cleared = self.engine.clear_lines()
        if lines_cleared > 0:
            self.engine.score += lines_cleared * 100
            self.add_clear_effect(lines_cleared)
        
        # Mark this block as used
        self.current_blocks[best_block_idx] = [[0]]
        
        # Update statistics
        self.moves_count += 1
        self.update_display()
        
        # Check if all blocks are used
        if all(all(all(cell == 0 for cell in row) for row in block) for block in self.current_blocks):
            # Generate new blocks
            self.current_blocks = self.engine.generate_blocks()
            
            # Check for game over
            if self.engine.check_game_over(self.current_blocks):
                self.engine.game_over = True
                self.show_game_over()
                return
        
        # Update display
        self.draw_board()
        self.draw_blocks()
        
        # Schedule next move
        if not self.engine.game_over:
            self.root.after(int(self.game_speed * 1000), self.make_bot_move)

    def add_clear_effect(self, lines_cleared):
        """Add visual effect when lines are cleared."""
        # Flash effect
        for i in range(3):
            self.board_canvas.config(bg='#f1c40f' if i % 2 == 0 else '#2c3e50')
            self.root.update()
            time.sleep(0.1)
        
        # Add celebration text
        if lines_cleared > 0:
            celebration_text = f"+{lines_cleared * 100} POINTS!"
            celebration = self.board_canvas.create_text(
                BOARD_WIDTH // 2, BOARD_WIDTH // 2,
                text=celebration_text,
                font=('Arial', 20, 'bold'),
                fill='#f1c40f'
            )
            
            def fade_celebration():
                for _ in range(10):
                    self.board_canvas.move(celebration, 0, -5)
                    self.root.update()
                    time.sleep(0.05)
                self.board_canvas.delete(celebration)
            
            threading.Thread(target=fade_celebration, daemon=True).start()

    def start_auto_play(self):
        """Start the bot playing automatically."""
        self.is_playing = True
        self.make_bot_move()

    def toggle_pause(self):
        """Pause/resume the bot."""
        self.is_playing = not self.is_playing
        self.pause_button.config(text="▶ Resume" if not self.is_playing else "⏸ Pause")
        
        if self.is_playing:
            self.make_bot_move()

    def change_speed(self):
        """Change the game speed."""
        speeds = [0.1, 0.3, 0.5, 1.0, 2.0]
        current_idx = speeds.index(self.game_speed)
        self.game_speed = speeds[(current_idx + 1) % len(speeds)]
        
        speed_text = f"⚡ Speed: {self.game_speed}s"
        self.speed_button.config(text=speed_text)

    def update_display(self):
        """Update all display elements."""
        self.score_label.config(text=f"Score: {self.engine.score}")
        self.moves_label.config(text=f"Moves: {self.moves_count}")
        self.games_label.config(text=f"Games: {self.games_played}")

    def show_game_over(self):
        """Show game over screen and restart."""
        self.games_played += 1
        final_score = self.engine.score
        
        # Show game over message
        game_over_text = f"🤖 BOT GAME OVER 🤖\nFinal Score: {final_score}\nTotal Moves: {self.moves_count}"
        self.explanation_label.config(text=game_over_text)
        
        print(f"\n{'='*50}")
        print(f"🤖 BOT GAME OVER 🤖")
        print(f"Final Score: {final_score}")
        print(f"Total Moves: {self.moves_count}")
        print(f"Games Played: {self.games_played}")
        print(f"{'='*50}\n")
        
        # Wait a bit then start new game
        self.root.after(2000, self.restart_game)

    def restart_game(self):
        """Restart the game with a new board."""
        self.engine.reset_board()
        self.current_blocks = self.engine.generate_blocks()
        self.moves_count = 0
        self.is_playing = True
        
        self.update_display()
        self.draw_board()
        self.draw_blocks()
        
        # Start playing again
        self.root.after(1000, self.make_bot_move)


# -----------------------------
# MAIN EXECUTION
# -----------------------------
def main():
    """Main function to run the integrated game."""
    root = tk.Tk()
    app = BlockBlastGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()