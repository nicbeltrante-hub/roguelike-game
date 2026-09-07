# Roguelike Game

A small terminal-based 2D game written in Python. Explore a randomly generated grid, collect every item, and reach the escape portal before the enemy catches you.

## Features

- Randomly generated maps with walls and collectible items
- Colored terminal output for the player, enemy, items, and portal
- Three levels with increasingly fast enemy movement
- Score tracking and win/loss states

## Requirements

- Python 3.9 or newer
- A Unix-like terminal, such as macOS or Linux
- The `colorama` package

## Installation

Clone the repository and install the dependency:

```bash
git clone <repository-url>
cd rougelike-game
python3 -m pip install colorama
```

## Run the game

```bash
python3 roguelike.py
```

The game reads one key at a time, so run it directly in a terminal rather than through an environment that does not provide interactive terminal input.

## Controls

| Key | Action     |
| --- | ---------- |
| `W` | Move up    |
| `A` | Move left  |
| `S` | Move down  |
| `D` | Move right |
| `Q` | Quit       |

## Symbols

| Symbol | Meaning          |
| ------ | ---------------- |
| `@`    | Player           |
| `X`    | Enemy            |
| `*`    | Collectible item |
| `E`    | Escape portal    |
| `\|`   | Wall             |
| `.`    | Open space       |

## How to win

Collect all items to activate the portal, then move onto `E` to escape and advance to the next level. Each collected item is worth 10 points. The enemy moves toward you every three successful moves on level 1, every two moves on level 2, and every move on level 3. Escape all three levels to win!

## Project structure

```text
.
├── README.md
└── roguelike.py
```

## Author

Nicoletta Beltrante
