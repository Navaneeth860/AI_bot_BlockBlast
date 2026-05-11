<div align='center'>
  
# Block Blast 

A Python/Tkinter implementation of the Block Blast puzzle game — playable by
a human or watched as an intelligent bot solves the board autonomously.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Tkinter](https://img.shields.io/badge/UI-Tkinter-informational)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Stable-brightgreen)

</div>

---

## Table of Contents

1. [Description](#description)
2. [Features](#features)
3. [Tech Stack](#tech-stack)
4. [Architecture Overview](#architecture-overview)
5. [Installation](#installation)
6. [Running the Project](#running-the-project)
7. [Gameplay Guide](#gameplay-guide)
8. [Core AI Logic](#core-ai-logic)
9. [Folder Structure](#folder-structure)
10. [Screenshots](#screenshots)
11. [Known Limitations](#known-limitations)
12. [Future Improvements](#future-improvements)
13. [Contributing](#contributing)
14. [License](#license)
15. [Credits](#credits)

---

## Description

Block Blast is a grid puzzle game where the player places tetromino-style blocks
onto a 10 × 10 board.  Full rows or columns are cleared for points.  The game
ends when no remaining block can be legally placed.

This implementation ships with **two modes**:

| Mode | Description |
|------|-------------|
| **Human Play** | Click to select a block, hover for a ghost preview, click the board to place it. |
| **Bot Player** | An autonomous greedy look-ahead agent plays continuously in a separate window, with pause/speed controls. |

---

## Features

- 12 distinct block shapes (1 × 1 through 4-cell polyominoes, S/Z/L/J)
- Ghost-preview system showing exactly where a block will land
- Visual selection highlight on the active block slot
- Row **and** column clearing with combo scoring
- Autonomous bot with a configurable play speed (0.1 s → 2.0 s per move)
- Non-blocking UI — all bot animations use Tkinter's `after()` scheduler; no `time.sleep()`, no extra threads
- Clean restart in both modes with persistent per-session statistics
- Console logging of every bot decision for post-game analysis

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| GUI | Tkinter (stdlib — zero external dependencies) |
| AI Engine | Custom greedy heuristic (pure Python) |
| Packaging | Single-file (`block_blast.py`) |

No pip install required.  Ships with every standard Python installation.

---

## Architecture Overview

The project follows a strict **three-layer separation**:

```
┌─────────────────────────────────────────────────────┐
│  BlockBlastEngine  (Layer 1 – Pure Game Logic)       │
│  • Board state, placement rules, line clearing       │
│  • Single source of truth for score                  │
│  • No GUI references whatsoever                      │
└───────────────────┬─────────────────────────────────┘
                    │ reads / writes board
┌───────────────────▼─────────────────────────────────┐
│  BlockBlastBot  (Layer 2 – AI Decision Engine)       │
│  • Greedy look-ahead heuristic                       │
│  • Simulates moves on in-memory board copies         │
│  • No GUI references whatsoever                      │
└───────────────────┬─────────────────────────────────┘
                    │ calls engine API
┌───────────────────▼─────────────────────────────────┐
│  BlockBlastGUI / BlockBlastBotGUI  (Layer 3 – UI)    │
│  • Tkinter canvases, event bindings, colour palette  │
│  • Reads engine state; never mutates score directly  │
│  • All animation via root.after(), never time.sleep()│
└─────────────────────────────────────────────────────┘
```

This separation means the engine and bot can be unit-tested in complete
isolation from any display system.

---

## Installation

### Prerequisites

- Python **3.10 or later** (for `list[...]` type-hint syntax)
- Tkinter — bundled with the CPython installer on Windows and macOS.
  On Debian/Ubuntu Linux you may need:

```bash
sudo apt-get install python3-tk
```

### Clone

```bash
git clone https://github.com/your-username/block-blast.git
cd block-blast
```

No virtual environment or package installation is required.

---

## Running the Project

```bash
python block_blast.py
```

The **human-play window** opens immediately.  Click **🤖 Launch Bot** to open the
autonomous bot window alongside it (both windows run independently).

### Running with verbose bot output

Bot decisions are always printed to stdout.  Redirect to a file for analysis:

```bash
python block_blast.py 2>&1 | tee bot_session.log
```

---

## Gameplay Guide

### Human Mode

1. **Select a block** — click any block in the right panel.  The selected block
   gets an orange highlight ring.
2. **Preview placement** — move the cursor over the board.  A blue ghost shows
   where the block will land.
3. **Place the block** — click on the board at the desired position.
4. **Score** — each cleared row or column scores **100 points**.  Multiple clears
   from a single placement all score independently.
5. **New round** — once all three block slots are placed, three new blocks are
   dealt automatically.
6. **Game over** — when no remaining block fits anywhere on the board, the game
   ends and you are offered a restart.

### Bot Mode

| Control | Action |
|---------|--------|
| ⏸ Pause / ▶ Resume | Freeze or continue autonomous play |
| ⚡ Speed | Cycle through 0.1 s / 0.3 s / 0.5 s / 1.0 s / 2.0 s per move |

The bot restarts automatically after each game over, accumulating a running
games-played counter.

---

## Core AI Logic

### Algorithm: Greedy Single-Ply Look-Ahead

The bot does **not** use minimax, MCTS, or any learned model.  It evaluates
every legal `(block, row, col)` triple using a four-term heuristic and picks
the highest-scoring placement.

#### Evaluation Function

```
H(placement) =
    lines_cleared × 100          # immediate reward
  + lines_cleared × 50           # combo-potential bonus
  + avg_future_moves × 1.5       # opportunity preservation
  - fill_ratio × 200             # board-congestion penalty
```

| Term | Rationale |
|------|-----------|
| `lines_cleared × 100` | Reward the move that directly scores the most points. |
| `lines_cleared × 50` | Extra weight to strongly prefer line-clearing moves over neutral ones. |
| `avg_future_moves × 1.5` | Sample 5 random shapes; count how many positions each can still be placed.  Rewards moves that keep the board open. |
| `fill_ratio × 200` | Heavily penalise board states approaching saturation; the denominator is `GRID_SIZE²`. |

#### Simulation Method

For each candidate placement the bot:
1. Copies the live board into a plain Python list (no full `Engine` object).
2. Stamps the block, counts full rows/columns, clears them.
3. Samples 5 random shapes and counts legal positions in the resulting board.
4. Computes `fill_ratio = filled_cells / 100`.

The winner is the placement with the highest `H` value across all three block
slots.

#### Why Greedy Works Here

Block Blast has no adversary and no hidden information.  A greedy single-ply
search with a well-tuned heuristic achieves respectable scores (typically
500–2 000 points) without the complexity of deeper tree search.

#### Known Weakness

The bot does not look ahead multiple placements within a single three-block
deal.  It may sacrifice a good second/third placement to optimise the first.
A full three-ply search over all permutations would require `O(100³)` board
simulations per turn — tractable but slower.

---

## Folder Structure

```
block-blast/
├── block_blast.py      # Entire project — engine + bot + GUI
└── README.md           # This file
```

The single-file layout is intentional for simplicity.  If the project grows,
the natural split is:

```
block-blast/
├── engine.py           # BlockBlastEngine
├── bot.py              # BlockBlastBot
├── gui_human.py        # BlockBlastGUI
├── gui_bot.py          # BlockBlastBotGUI
├── constants.py        # GRID_SIZE, CELL_SIZE, SHAPES, PALETTE …
└── main.py             # Entry point
```

---

## Screenshots

> _Add screenshots here once the application is running._

| Human Mode | Bot Mode |
|:----------:|:--------:|
| _(screenshot)_ | _(screenshot)_ |

---

## Known Limitations

| # | Limitation |
|---|------------|
| 1 | **Single-ply AI** — the bot does not plan across an entire three-block deal. |
| 2 | **No persistence** — scores reset when the window closes; there is no high-score file. |
| 3 | **Fixed 10 × 10 grid** — `GRID_SIZE` is a module constant, not a runtime setting. |
| 4 | **No sound** — Tkinter has no audio subsystem; adding sound requires `pygame` or `playsound`. |
| 5 | **Tkinter DPI** — on HiDPI / Retina displays the canvas may appear slightly blurry; Tkinter does not expose per-canvas DPI scaling. |
| 6 | **Single-file** — not structured for unit testing without import surgery. |

---

## Future Improvements

These are **optional** enhancements — they are not needed for the current
feature set but would raise the project to a publishable game.

### Short-term (low effort)

- [ ] **High-score persistence** — write `scores.json` on game over; display top 5.
- [ ] **Keyboard shortcuts** — `1` / `2` / `3` to select a block; `R` to restart.
- [ ] **Configurable grid size** — pass `--size 8` via `argparse`.
- [ ] **Block rotation** — add rotated variants to `SHAPES` or generate them programmatically.

### Medium-term

- [ ] **Three-ply bot search** — evaluate all permutations of the three available
  blocks for a measurably stronger agent.
- [ ] **Unit test suite** — split into modules; add `pytest` tests for
  `BlockBlastEngine` (placement, clearing, game-over detection).
- [ ] **Pygame port** — pixel-perfect rendering, DPI support, sound effects,
  particle systems for line clears.

### Long-term

- [ ] **Reinforcement learning agent** — replace the heuristic with a trained
  DQN or PPO policy using a gym-style environment wrapper around
  `BlockBlastEngine`.
- [ ] **Web version** — compile via Pyodide + a canvas renderer, or rewrite
  the frontend in JavaScript with the same engine logic ported to TypeScript.
- [ ] **Multiplayer** — WebSocket-based competitive mode where two players race
  on mirrored boards.

### Deployment Note

This is a desktop GUI application.  "Deployment" means packaging as a
standalone binary:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed block_blast.py
```

The output binary in `dist/` runs on any machine without a Python installation.

---

## Contributing

Contributions are welcome.  Please follow these steps:

1. Fork the repository and create a feature branch:
   ```bash
   git checkout -b feat/my-improvement
   ```
2. Keep changes incremental — one concern per pull request.
3. If you change game logic, include a written description of the expected
   behaviour change and why the heuristic values were chosen.
4. Run a quick manual smoke-test:
   - Human mode: place blocks, clear a line, trigger game over.
   - Bot mode: watch at least 30 seconds of autonomous play without a crash.
5. Open a pull request with a clear title and description.

### Code Style

- Follow PEP 8 with a 100-character line limit.
- Use type hints on all public method signatures.
- Prefer `after()` over `time.sleep()` for any UI timing.
- Never call Tkinter APIs from a non-main thread.

---

## Security Notes

- This application makes **no network requests** and reads/writes **no files**
  (until high-score persistence is added).
- There are no external dependencies that could introduce supply-chain risk.

---


## Credits

| Contribution | Detail |
|---|---|
| Original game concept | Inspired by the mobile game *Block Blast!* by Hungry Studio |
| Implementation | Written from scratch in Python/Tkinter |
| AI heuristic design | Custom; informed by classic Tetris heuristic literature (Dellacherie features) |

---

_Built with Python and curiosity._
