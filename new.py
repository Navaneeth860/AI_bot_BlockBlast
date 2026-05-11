# =============================================================================
# BLOCK BLAST – INTEGRATED VERSION WITH BOT
# Original Animated Game + Intelligent Bot Player
#
# Architecture: Single-file, three-layer design
#   - BlockBlastEngine  : Pure game logic (no GUI references)
#   - BlockBlastBot     : AI decision engine (reads engine state, no GUI refs)
#   - BlockBlastGUI     : Human-play interface
#   - BlockBlastBotGUI  : Bot-play interface (separate Toplevel window)
# =============================================================================

import tkinter as tk
from tkinter import messagebox
import random

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

CELL_SIZE      = 40          # Pixel size of each grid cell
GRID_SIZE      = 10          # Board is GRID_SIZE × GRID_SIZE
BOARD_PX       = GRID_SIZE * CELL_SIZE   # Board canvas dimension in pixels
BOT_MOVE_DELAY = 500         # Default ms between bot moves

# Sentinel used to mark a block slot as "already placed".
# Using a named constant prevents the magic-value bug that previously allowed
# the engine to treat [[0]] as a valid 1×1 air block.
USED_SENTINEL = [[0]]

# ---------------------------------------------------------------------------
# COLOUR PALETTE
# ---------------------------------------------------------------------------

PALETTE = {
    # Board
    "cell_empty":   "#FAFAFA",
    "cell_filled":  "#2D3748",
    "grid_line":    "#CBD5E0",
    "cell_outline": "#4A5568",
    # Preview ghost
    "preview_fill":    "#BEE3F8",
    "preview_outline": "#63B3ED",
    # Selection highlight
    "select_ring": "#F6AD55",
    # Bot board colours
    "bot_cell_empty":  "#EDF2F7",
    "bot_cell_filled": "#E53E3E",
    "bot_grid_line":   "#A0AEC0",
}

BLOCK_COLORS = [
    "#4CC9F0",  # cyan
    "#F72585",  # pink
    "#7209B7",  # purple
    "#3A0CA3",  # dark blue
    "#4361EE",  # blue
    "#FF6B35",  # orange
    "#06D6A0",  # teal
    "#FFD23F",  # yellow
]

# ---------------------------------------------------------------------------
# BLOCK SHAPE CATALOGUE
# ---------------------------------------------------------------------------

SHAPES = [
    [[1]],                        # 1 × 1
    [[1, 1]],                     # 1 × 2 horizontal
    [[1], [1]],                   # 2 × 1 vertical
    [[1, 1], [1, 1]],             # 2 × 2 square
    [[1, 1, 1]],                  # 1 × 3 horizontal
    [[1], [1], [1]],              # 3 × 1 vertical
    [[1, 1, 1, 1]],               # 1 × 4 horizontal
    [[1], [1], [1], [1]],         # 4 × 1 vertical
    [[1, 0], [1, 1]],             # L-shape
    [[0, 1], [1, 1]],             # J-shape
    [[1, 1, 0], [0, 1, 1]],       # S-shape
    [[0, 1, 1], [1, 1, 0]],       # Z-shape
]


# =============================================================================
# LAYER 1 – GAME ENGINE  (pure logic, zero GUI imports)
# =============================================================================

class BlockBlastEngine:
    """
    All game state and rules live here.  No Tkinter references.
    Score is the single source of truth inside this class; the GUI
    should read ``engine.score`` rather than maintaining its own copy.
    """

    def __init__(self):
        self.board: list[list[int]] = []
        self.score: int = 0
        self.game_over: bool = False
        self._init_board()

    # ------------------------------------------------------------------
    # Board helpers
    # ------------------------------------------------------------------

    def _init_board(self) -> None:
        self.board = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]

    def reset(self) -> None:
        """Reset the engine to a fresh game state."""
        self._init_board()
        self.score = 0
        self.game_over = False

    # ------------------------------------------------------------------
    # Block generation
    # ------------------------------------------------------------------

    def generate_blocks(self) -> list:
        """Return three randomly chosen block shapes."""
        return [random.choice(SHAPES) for _ in range(3)]

    # ------------------------------------------------------------------
    # Placement logic
    # ------------------------------------------------------------------

    def can_place(self, block: list[list[int]], row: int, col: int) -> bool:
        """Return True iff *block* fits on the board at (row, col)."""
        bh, bw = len(block), len(block[0])

        if row < 0 or col < 0:
            return False
        if row + bh > GRID_SIZE or col + bw > GRID_SIZE:
            return False

        for r in range(bh):
            for c in range(bw):
                if block[r][c] == 1 and self.board[row + r][col + c] == 1:
                    return False
        return True

    def place_block(self, block: list[list[int]], row: int, col: int) -> None:
        """Stamp *block* onto the board (caller must verify with can_place first)."""
        for r, row_cells in enumerate(block):
            for c, cell in enumerate(row_cells):
                if cell == 1:
                    self.board[row + r][col + c] = 1

    # ------------------------------------------------------------------
    # Line clearing
    # ------------------------------------------------------------------

    def clear_lines(self) -> int:
        """
        Clear any full rows and columns.
        Returns the total number of lines cleared (rows + columns).
        Score is updated here — the GUI should not modify engine.score directly.
        """
        cleared = 0

        full_rows = [r for r in range(GRID_SIZE) if all(self.board[r])]
        for r in full_rows:
            self.board[r] = [0] * GRID_SIZE
            cleared += 1

        full_cols = [c for c in range(GRID_SIZE)
                     if all(self.board[r][c] for r in range(GRID_SIZE))]
        for c in full_cols:
            for r in range(GRID_SIZE):
                self.board[r][c] = 0
            cleared += 1

        if cleared:
            self.score += cleared * 100

        return cleared

    # ------------------------------------------------------------------
    # Game-over detection
    # ------------------------------------------------------------------

    def check_game_over(self, available_blocks: list) -> bool:
        """
        Return True if *none* of the real (non-sentinel) blocks in
        ``available_blocks`` can be placed anywhere on the board.
        """
        live_blocks = [b for b in available_blocks if not _is_sentinel(b)]
        if not live_blocks:
            # All three slots used up — caller should regenerate before calling.
            return False

        for block in live_blocks:
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    if self.can_place(block, r, c):
                        return False
        return True


# =============================================================================
# LAYER 2 – BOT ENGINE  (reads engine state, no GUI references)
# =============================================================================

class BlockBlastBot:
    """
    Greedy look-ahead bot.

    Evaluation heuristic per candidate move:
      +  lines_cleared × 100   (immediate reward)
      +  lines_cleared × 50    (bonus for combo potential)
      +  avg_future_moves × 1.5  (opportunity preservation)
      −  fill_ratio × 200      (penalty for board congestion)
    """

    def __init__(self, engine: BlockBlastEngine):
        self.engine = engine

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find_best_move(self, available_blocks: list) -> tuple:
        """
        Evaluate every (block, row, col) triple and return
        ``(best_position, best_block_index)`` or ``(None, None)`` if no
        move is possible.
        """
        best_score = float("-inf")
        best_position = None
        best_block_idx = None

        for idx, block in enumerate(available_blocks):
            if _is_sentinel(block):
                continue

            for row in range(GRID_SIZE):
                for col in range(GRID_SIZE):
                    if self.engine.can_place(block, row, col):
                        score, _ = self._evaluate(block, row, col)
                        if score > best_score:
                            best_score = score
                            best_position = (row, col)
                            best_block_idx = idx

        return best_position, best_block_idx

    def move_explanation(self, lines_cleared: int, score: float) -> str:
        """Human-readable reason for the chosen move."""
        if lines_cleared > 1:
            return f"Combo! Clears {lines_cleared} lines (+{lines_cleared * 100} pts)"
        if lines_cleared == 1:
            return "Clears a line (+100 pts)"
        if score > 50:
            return "Maximises future placement options"
        return "Best available position given board state"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _evaluate(self, block, row, col) -> tuple:
        """Return (heuristic_score, lines_cleared) for a candidate placement."""
        # Shallow-copy the board; avoid constructing a full engine object.
        sim_board = [r[:] for r in self.engine.board]
        sim_score = self.engine.score

        # Stamp block onto simulation board
        for r, row_cells in enumerate(block):
            for c, cell in enumerate(row_cells):
                if cell == 1:
                    sim_board[row + r][col + c] = 1

        # Count cleared lines
        full_rows = sum(1 for r in range(GRID_SIZE) if all(sim_board[r]))
        full_cols = sum(
            1 for c in range(GRID_SIZE)
            if all(sim_board[r][c] for r in range(GRID_SIZE))
        )
        lines_cleared = full_rows + full_cols

        # Clear them from the simulation
        for r in range(GRID_SIZE):
            if all(sim_board[r]):
                sim_board[r] = [0] * GRID_SIZE
        for c in range(GRID_SIZE):
            if all(sim_board[r][c] for r in range(GRID_SIZE)):
                for r in range(GRID_SIZE):
                    sim_board[r][c] = 0

        # Future opportunity: sample 5 random shapes
        future_hits = 0
        for _ in range(5):
            test_block = random.choice(SHAPES)
            for tr in range(GRID_SIZE):
                for tc in range(GRID_SIZE):
                    bh, bw = len(test_block), len(test_block[0])
                    if tr + bh <= GRID_SIZE and tc + bw <= GRID_SIZE:
                        if all(
                            test_block[dr][dc] == 0 or sim_board[tr + dr][tc + dc] == 0
                            for dr in range(bh)
                            for dc in range(bw)
                        ):
                            future_hits += 1
                            break
                else:
                    continue
                break

        fill_ratio = sum(sim_board[r][c] for r in range(GRID_SIZE) for c in range(GRID_SIZE)) / (GRID_SIZE ** 2)

        heuristic = (
            lines_cleared * 100
            + lines_cleared * 50
            + (future_hits / 5) * 1.5
            - fill_ratio * 200
        )
        return heuristic, lines_cleared


# =============================================================================
# UTILITIES
# =============================================================================

def _is_sentinel(block: list) -> bool:
    """Return True if *block* is the USED_SENTINEL (all cells are 0)."""
    return all(cell == 0 for row in block for cell in row)


def _deep_copy_block(block: list) -> list:
    return [row[:] for row in block]


# =============================================================================
# LAYER 3 – HUMAN-PLAY GUI
# =============================================================================

class BlockBlastGUI:
    """
    Human-play window.

    Mouse interaction:
      1. Click a block in the side panel  → selects it (highlights frame)
      2. Move cursor over the board       → draws ghost preview
      3. Click on the board              → places the selected block
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Block Blast")
        self.root.resizable(False, False)
        self.root.configure(bg="#F7FAFC")

        self.engine = BlockBlastEngine()
        self.current_blocks: list = self.engine.generate_blocks()
        self.selected_block: list | None = None
        self.selected_index: int | None = None
        self.preview_pos: tuple | None = None    # (row, col) under cursor
        self._last_preview: tuple | None = None  # throttle redraws

        self._build_ui()
        self._refresh_board()
        self._refresh_blocks()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        outer = tk.Frame(self.root, bg="#F7FAFC")
        outer.pack(padx=24, pady=24)

        # ── Left: game board ──────────────────────────────────────────
        board_wrapper = tk.Frame(outer, bg="#E2E8F0", relief="flat", bd=0)
        board_wrapper.grid(row=0, column=0, padx=(0, 20))

        self.board_canvas = tk.Canvas(
            board_wrapper,
            width=BOARD_PX,
            height=BOARD_PX,
            bg=PALETTE["cell_empty"],
            highlightthickness=0,
        )
        self.board_canvas.pack(padx=2, pady=2)

        # Bind to canvas only — avoids misfire on side panel clicks
        self.board_canvas.bind("<Button-1>", self._on_board_click)
        self.board_canvas.bind("<Motion>",   self._on_board_motion)
        self.board_canvas.bind("<Leave>",    self._on_board_leave)

        # ── Right: side panel ────────────────────────────────────────
        side = tk.Frame(outer, bg="#F7FAFC")
        side.grid(row=0, column=1, sticky="n")

        self.score_var = tk.StringVar(value="Score\n0")
        tk.Label(
            side,
            textvariable=self.score_var,
            font=("Courier", 22, "bold"),
            fg="#2D3748",
            bg="#F7FAFC",
            justify="center",
        ).pack(pady=(0, 20))

        tk.Label(
            side,
            text="AVAILABLE BLOCKS",
            font=("Courier", 9, "bold"),
            fg="#718096",
            bg="#F7FAFC",
        ).pack()

        # Block slots live here; rebuilt on every block-state change
        self.block_panel = tk.Frame(side, bg="#F7FAFC")
        self.block_panel.pack(pady=8)

        tk.Button(
            side,
            text="🤖  Launch Bot",
            command=self._open_bot_window,
            bg="#4361EE",
            fg="white",
            font=("Courier", 11, "bold"),
            relief="flat",
            padx=14,
            pady=8,
            cursor="hand2",
            activebackground="#3A0CA3",
            activeforeground="white",
        ).pack(pady=(20, 0), fill="x")

        tk.Button(
            side,
            text="↺  New Game",
            command=self._restart,
            bg="#718096",
            fg="white",
            font=("Courier", 10),
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            activebackground="#4A5568",
            activeforeground="white",
        ).pack(pady=(8, 0), fill="x")

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _refresh_board(self) -> None:
        """Redraw the full board canvas."""
        c = self.board_canvas
        c.delete("all")
        board = self.engine.board

        for r in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                filled = board[r][col] == 1
                x1, y1 = col * CELL_SIZE, r * CELL_SIZE
                x2, y2 = x1 + CELL_SIZE, y1 + CELL_SIZE
                c.create_rectangle(
                    x1, y1, x2, y2,
                    fill=PALETTE["cell_filled"] if filled else PALETTE["cell_empty"],
                    outline=PALETTE["cell_outline"] if filled else PALETTE["grid_line"],
                    width=1 if filled else 1,
                )

        # Ghost preview
        if self.preview_pos and self.selected_block:
            pr, pc = self.preview_pos
            for r, row_cells in enumerate(self.selected_block):
                for col, cell in enumerate(row_cells):
                    if cell == 1:
                        x1 = (pc + col) * CELL_SIZE
                        y1 = (pr + r)   * CELL_SIZE
                        c.create_rectangle(
                            x1, y1, x1 + CELL_SIZE, y1 + CELL_SIZE,
                            fill=PALETTE["preview_fill"],
                            outline=PALETTE["preview_outline"],
                            width=2,
                        )

    def _refresh_blocks(self) -> None:
        """Rebuild the block-selector panel."""
        for w in self.block_panel.winfo_children():
            w.destroy()

        for idx, block in enumerate(self.current_blocks):
            if _is_sentinel(block):
                continue

            is_selected = (idx == self.selected_index)
            border_color = PALETTE["select_ring"] if is_selected else "#CBD5E0"

            frame = tk.Frame(
                self.block_panel,
                bg="#FFFFFF",
                relief="flat",
                highlightthickness=2,
                highlightbackground=border_color,
            )
            frame.pack(pady=5)

            bh = len(block)
            bw = len(block[0])
            mini_size = 16
            pad = 8
            canvas_w = max(bw * mini_size + pad * 2, 64)
            canvas_h = max(bh * mini_size + pad * 2, 48)

            mini = tk.Canvas(frame, width=canvas_w, height=canvas_h,
                              bg="#FFFFFF", highlightthickness=0)
            mini.pack()

            color = BLOCK_COLORS[idx % len(BLOCK_COLORS)]
            for r, row_cells in enumerate(block):
                for col, cell in enumerate(row_cells):
                    if cell == 1:
                        x1 = pad + col * mini_size
                        y1 = pad + r   * mini_size
                        mini.create_rectangle(
                            x1, y1, x1 + mini_size - 1, y1 + mini_size - 1,
                            fill=color, outline="#2D3748", width=1,
                        )

            # Clicking the canvas or its frame both select this block
            mini.bind("<Button-1>",  lambda e, i=idx: self._select_block(i))
            frame.bind("<Button-1>", lambda e, i=idx: self._select_block(i))

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _select_block(self, index: int) -> None:
        self.selected_index = index
        self.selected_block = self.current_blocks[index]
        self._refresh_blocks()   # re-draw selection highlight

    def _on_board_click(self, event: tk.Event) -> None:
        if self.engine.game_over or self.selected_block is None:
            return
        col = event.x // CELL_SIZE
        row = event.y // CELL_SIZE
        if self.engine.can_place(self.selected_block, row, col):
            self._commit_placement(row, col)

    def _on_board_motion(self, event: tk.Event) -> None:
        if self.selected_block is None:
            return
        col = event.x // CELL_SIZE
        row = event.y // CELL_SIZE
        new_pos = (row, col) if self.engine.can_place(self.selected_block, row, col) else None

        # Only redraw when the preview cell actually changed
        if new_pos != self._last_preview:
            self.preview_pos = new_pos
            self._last_preview = new_pos
            self._refresh_board()

    def _on_board_leave(self, _event: tk.Event) -> None:
        if self.preview_pos is not None:
            self.preview_pos = None
            self._last_preview = None
            self._refresh_board()

    # ------------------------------------------------------------------
    # Placement & game flow
    # ------------------------------------------------------------------

    def _commit_placement(self, row: int, col: int) -> None:
        self.engine.place_block(self.selected_block, row, col)
        self.engine.clear_lines()

        # Mark slot as used
        self.current_blocks[self.selected_index] = USED_SENTINEL
        self.selected_block = None
        self.selected_index = None
        self.preview_pos = None
        self._last_preview = None

        self._refresh_board()
        self._refresh_blocks()
        self.score_var.set(f"Score\n{self.engine.score}")

        # All slots used → generate a new set
        if all(_is_sentinel(b) for b in self.current_blocks):
            self.current_blocks = self.engine.generate_blocks()
            self._refresh_blocks()

        if self.engine.check_game_over(self.current_blocks):
            self.engine.game_over = True
            self._show_game_over()

    def _show_game_over(self) -> None:
        ans = messagebox.askyesno(
            "Game Over",
            f"Final Score: {self.engine.score}\n\nPlay again?",
        )
        if ans:
            self._restart()

    def _restart(self) -> None:
        self.engine.reset()
        self.current_blocks = self.engine.generate_blocks()
        self.selected_block = None
        self.selected_index = None
        self.preview_pos = None
        self._last_preview = None
        self.score_var.set("Score\n0")
        self._refresh_board()
        self._refresh_blocks()

    def _open_bot_window(self) -> None:
        win = tk.Toplevel(self.root)
        BlockBlastBotGUI(win)


# =============================================================================
# LAYER 4 – BOT-PLAY GUI
# =============================================================================

class BlockBlastBotGUI:
    """
    Autonomous bot-play window.

    The bot runs entirely on Tkinter's ``after()`` scheduler — no threads,
    no ``time.sleep()``.  All visual effects are also scheduled via ``after()``.
    """

   
    SPEEDS = [2000, 1000, 500, 333, 250]  # ms between moves
    SPEED_LABELS = ["0.25x", "0.5x", "1x", "1.5x", "2.0x"]

    def __init__(self, root: tk.Toplevel):
        self.root = root
        self.root.title("Block Blast – Bot Player")
        self.root.resizable(False, False)
        self.root.configure(bg="#1A202C")

        self.engine = BlockBlastEngine()
        self.bot     = BlockBlastBot(self.engine)
        self.current_blocks: list = self.engine.generate_blocks()

        self.is_playing    = False
        self.speed_idx     = 2          # default → 500 ms
        self.total_moves   = 0
        self.games_played  = 0
        self._pending_id   = None       # after() job ID for cancellation

        self._build_ui()
        self._refresh_board()
        self._refresh_blocks()

        # Start after the window has fully rendered
        self.root.after(800, self._resume)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        outer = tk.Frame(self.root, bg="#1A202C")
        outer.pack(padx=20, pady=20)

        # Header
        hdr = tk.Frame(outer, bg="#1A202C")
        hdr.grid(row=0, column=0, columnspan=2, pady=(0, 16))

        tk.Label(
            hdr, text="🤖  BLOCK BLAST BOT",
            font=("Courier", 20, "bold"),
            fg="#63B3ED", bg="#1A202C",
        ).pack()
        tk.Label(
            hdr, text="Autonomous AI Player",
            font=("Courier", 10, "italic"),
            fg="#718096", bg="#1A202C",
        ).pack()

        # ── Board ───────────────────────────────────────────────────
        board_wrapper = tk.Frame(outer, bg="#2D3748", relief="flat")
        board_wrapper.grid(row=1, column=0, padx=(0, 20))

        self.board_canvas = tk.Canvas(
            board_wrapper,
            width=BOARD_PX, height=BOARD_PX,
            bg=PALETTE["bot_cell_empty"],
            highlightthickness=0,
        )
        self.board_canvas.pack(padx=4, pady=4)

        # ── Info panel ──────────────────────────────────────────────
        info = tk.Frame(outer, bg="#2D3748", relief="flat")
        info.grid(row=1, column=1, sticky="nsew")

        self.score_var = tk.StringVar(value="0")
        tk.Label(
            info, textvariable=self.score_var,
            font=("Courier", 28, "bold"),
            fg="#FC8181", bg="#2D3748",
        ).pack(pady=(12, 0))
        tk.Label(
            info, text="SCORE",
            font=("Courier", 8, "bold"),
            fg="#718096", bg="#2D3748",
        ).pack()

        # Stats
        stats = tk.Frame(info, bg="#2D3748")
        stats.pack(pady=10)

        self.moves_var = tk.StringVar(value="Moves: 0")
        self.games_var = tk.StringVar(value="Games: 1")

        for var in (self.moves_var, self.games_var):
            tk.Label(
                stats, textvariable=var,
                font=("Courier", 10),
                fg="#A0AEC0", bg="#2D3748",
            ).pack()

        # Blocks display
        tk.Label(
            info, text="NEXT BLOCKS",
            font=("Courier", 8, "bold"),
            fg="#63B3ED", bg="#2D3748",
        ).pack(pady=(10, 4))

        self.blocks_canvas = tk.Canvas(
            info, width=150, height=220,
            bg="#1A202C", highlightthickness=0,
        )
        self.blocks_canvas.pack()

        # Controls
        ctrl = tk.Frame(info, bg="#2D3748")
        ctrl.pack(pady=12)

        self.pause_var = tk.StringVar(value="⏸  Pause")
        tk.Button(
            ctrl, textvariable=self.pause_var,
            command=self._toggle_pause,
            bg="#D69E2E", fg="white",
            font=("Courier", 9, "bold"),
            relief="flat", padx=8, pady=5,
            cursor="hand2",
            activebackground="#B7791F",
        ).pack(side=tk.LEFT, padx=4)

        self.speed_var = tk.StringVar(value=f"⚡ {self.SPEED_LABELS[self.speed_idx]}")
        tk.Button(
            ctrl, textvariable=self.speed_var,
            command=self._cycle_speed,
            bg="#38A169", fg="white",
            font=("Courier", 9, "bold"),
            relief="flat", padx=8, pady=5,
            cursor="hand2",
            activebackground="#276749",
        ).pack(side=tk.LEFT, padx=4)

        # Status line
        self.status_var = tk.StringVar(value="Bot is warming up…")
        tk.Label(
            info, textvariable=self.status_var,
            font=("Courier", 9, "italic"),
            fg="#718096", bg="#2D3748",
            wraplength=150, justify="center",
        ).pack(pady=(4, 12))

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _refresh_board(self) -> None:
        c = self.board_canvas
        c.delete("all")
        board = self.engine.board

        for r in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                filled = board[r][col] == 1
                x1, y1 = col * CELL_SIZE, r * CELL_SIZE
                x2, y2 = x1 + CELL_SIZE, y1 + CELL_SIZE
                c.create_rectangle(
                    x1, y1, x2, y2,
                    fill=PALETTE["bot_cell_filled"] if filled else PALETTE["bot_cell_empty"],
                    outline=PALETTE["bot_grid_line"],
                    width=1,
                )

    def _refresh_blocks(self) -> None:
        c = self.blocks_canvas
        c.delete("all")

        y = 10
        for idx, block in enumerate(self.current_blocks):
            if _is_sentinel(block):
                continue
            bh, bw = len(block), len(block[0])
            cell = 18
            pad  = (150 - bw * cell) // 2
            color = BLOCK_COLORS[idx % len(BLOCK_COLORS)]

            for r, row_cells in enumerate(block):
                for col, val in enumerate(row_cells):
                    if val == 1:
                        x1 = pad + col * cell
                        y1 = y + r * cell
                        c.create_rectangle(
                            x1, y1, x1 + cell - 2, y1 + cell - 2,
                            fill=color, outline="#1A202C", width=1,
                        )
            y += bh * cell + 14

    # ------------------------------------------------------------------
    # Bot loop  (entirely via after(), no threads)
    # ------------------------------------------------------------------

    def _step(self) -> None:
        """Execute one bot move then schedule the next."""
        if not self.is_playing or self.engine.game_over:
            return

        position, block_idx = self.bot.find_best_move(self.current_blocks)

        if position is None or block_idx is None:
            self._handle_game_over()
            return

        row, col  = position
        block     = self.current_blocks[block_idx]

        self.engine.place_block(block, row, col)
        lines = self.engine.clear_lines()

        self.current_blocks[block_idx] = USED_SENTINEL
        self.total_moves += 1

        # Update status
        _, lines_check = self.bot._evaluate(block, row, col)
        self.status_var.set(self.bot.move_explanation(lines, 0))

        self._refresh_board()
        self._refresh_blocks()
        self._update_stats()

        # Flash on line clear — pure after() animation
        if lines:
            self._flash_clear(lines, step=0)

        # Replenish blocks if all used
        if all(_is_sentinel(b) for b in self.current_blocks):
            self.current_blocks = self.engine.generate_blocks()
            self._refresh_blocks()

        if self.engine.check_game_over(self.current_blocks):
            self._handle_game_over()
            return

        # Schedule next move
        delay = self.SPEEDS[self.speed_idx]
        self._pending_id = self.root.after(delay, self._step)

    def _flash_clear(self, lines: int, step: int) -> None:
        """Non-blocking board flash using recursive after() calls."""
        if step >= 4:
            self._refresh_board()
            return
        color = "#F6E05E" if step % 2 == 0 else PALETTE["bot_cell_empty"]
        self.board_canvas.config(bg=color)
        self.root.after(80, lambda: self._flash_clear(lines, step + 1))

    # ------------------------------------------------------------------
    # Controls
    # ------------------------------------------------------------------

    def _resume(self) -> None:
        self.is_playing = True
        self.pause_var.set("⏸  Pause")
        self._step()

    def _toggle_pause(self) -> None:
        if self.is_playing:
            self.is_playing = False
            self.pause_var.set("▶  Resume")
            if self._pending_id:
                self.root.after_cancel(self._pending_id)
                self._pending_id = None
        else:
            self._resume()

    def _cycle_speed(self) -> None:
        self.speed_idx = (self.speed_idx + 1) % len(self.SPEEDS)
        self.speed_var.set(f"⚡ {self.SPEED_LABELS[self.speed_idx]}")

    # ------------------------------------------------------------------
    # Game flow
    # ------------------------------------------------------------------

    def _update_stats(self) -> None:
        self.score_var.set(str(self.engine.score))
        self.moves_var.set(f"Moves: {self.total_moves}")
        self.games_var.set(f"Games: {self.games_played + 1}")

    def _handle_game_over(self) -> None:
        self.engine.game_over = True
        self.is_playing = False
        self.games_played += 1

        print(
            f"[Bot] Game {self.games_played} over | "
            f"Score: {self.engine.score} | Moves: {self.total_moves}"
        )
        self.status_var.set(
            f"Game over!\nScore: {self.engine.score}\nRestarting…"
        )
        self.root.after(2200, self._restart)

    def _restart(self) -> None:
        self.engine.reset()
        self.current_blocks = self.engine.generate_blocks()
        self._refresh_board()
        self._refresh_blocks()
        self._update_stats()
        self.root.after(600, self._resume)


# =============================================================================
# ENTRY POINT
# =============================================================================

def main() -> None:
    root = tk.Tk()
    BlockBlastGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()