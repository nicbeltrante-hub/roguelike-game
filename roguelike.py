# Author: Nicoletta Beltrante
# A simple terminal-based roguelike game where the player navigates a grid, collects items, and avoids an enemy. 
# The game features colored output for better visual distinction of game elements!

import os
import sys
import termios
import tty
import random
from colorama import Fore, Style, init

# Initialize colorama for colored terminal output
init(autoreset=True)

# Define the Entity class to represent both the player and enemy
class Entity:
    def __init__(self, x: int, y: int, token: str, color_style: str):
        self.x: int = x
        self.y: int = y
        self.token: str = token
        self.color_style: str = color_style  

# Define the Player class, inheriting from Entity
class Player(Entity):
    def __init__(self, x: int, y: int):
        super().__init__(x, y, "@", Fore.GREEN + Style.BRIGHT)

# Define the Enemy class, inheriting from Entity
class Enemy(Entity):
    def __init__(self, x: int, y: int):
        super().__init__(x, y, "X", Fore.RED + Style.BRIGHT)
    
    # Calculate the next move for the enemy towards the player, avoiding walls
    def calculate_next_move(self, target_x: int, target_y: int, grid: list[list[str]]) -> tuple[int, int]:
        dx, dy = 0, 0
        if self.x < target_x: dx = 1
        elif self.x > target_x: dx = -1
        if self.y < target_y: dy = 1
        elif self.y > target_y: dy = -1
        
        # Prioritize horizontal movement if possible, otherwise move vertically if there is a wall in the way
        if grid[self.y][self.x + dx] != "#":
            return dx, 0
        elif grid[self.y + dy][self.x] != "#":
            return 0, dy
        return 0, 0

# Class to manage the game engine, including the game loop, rendering, and input handling
class RoguelikeEngine:
    def __init__(self, width: int = 30, height: int = 12):
        self.width: int = width
        self.height: int = height
        self.player: Player = Player(2, 2)
        self.enemy: Enemy = Enemy(width - 3, height - 3)
        self.score: int = 0
        self.total_items: int = 0
        self.turn_count: int = 0
        self.game_state: str = "RUNNING"
        
        self.grid: list[list[str]] = []
        self.generate_map()
    
    # Generate the game map with walls, items, and an exit
    def generate_map(self) -> None:
        self.grid = [["." for _ in range(self.width)] for _ in range(self.height)]
        for y in range(self.height):
            for x in range(self.width):
                # Create walls around the edges of the map
                if x == 0 or y == 0 or x == self.width - 1 or y == self.height - 1:
                    self.grid[y][x] = "#"
                # Randomly place walls and items within the map, keeping some distance from the edges
                elif random.random() < 0.10 and (x > 3 or y > 3) and (x < self.width - 4):
                    self.grid[y][x] = "#"
                elif random.random() < 0.04 and (x > 3 or y > 3):
                    self.grid[y][x] = "*"
                    self.total_items += 1
        # Ensures there is at least one item in the game for the player to collect
        if self.total_items == 0:
            self.grid[5][5] = "*"
            self.total_items = 1

    def get_keypress(self) -> str:
        # Grab terminal input stream id and save in fd
        fd = sys.stdin.fileno()
        # Save the current terminal settings
        old_settings = termios.tcgetattr(fd)
        try:
            # Set the terminal to raw mode to capture keypresses without waiting for Enter
            tty.setraw(sys.stdin.fileno())
            # Read a single character from stdin
            ch = sys.stdin.read(1)
        finally:
            # Restore the terminal settings to their original state
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        # Return the captured character
        return ch

    def update_game_tick(self, dx: int, dy: int) -> None:
        # Calculate the new position of the player based on the input direction
        new_px = self.player.x + dx
        new_py = self.player.y + dy
        
        # Check if the new position is not a wall
        if self.grid[new_py][new_px] != "#":
            # Update the player's position and increment the turn count
            self.player.x = new_px
            self.player.y = new_py
            self.turn_count += 1
            
            # Check if the player has collected an item
            if self.grid[self.player.y][self.player.x] == "*":
                self.score += 10
                self.total_items -= 1
                self.grid[self.player.y][self.player.x] = "."
                if self.total_items == 0:
                    self.grid[self.height // 2][self.width // 2] = "E"
            
            # Check if the player has reached the exit
            elif self.grid[self.player.y][self.player.x] == "E":
                self.game_state = "WON"
                return

        # Check if the player has collided with the enemy
        if self.player.x == self.enemy.x and self.player.y == self.enemy.y:
            self.game_state = "LOST"
            return

        # Move the enemy every 3 turns
        if self.turn_count > 0 and self.turn_count % 3 == 0:
            edx, edy = self.enemy.calculate_next_move(self.player.x, self.player.y, self.grid)
            self.enemy.x += edx
            self.enemy.y += edy

        # Check if the enemy has collided with the player
        if self.enemy.x == self.player.x and self.enemy.y == self.player.y:
            self.game_state = "LOST"

    def render_frame(self) -> None:
        # Clear the terminal screen before rendering the new frame
        os.system('clear')
        
        # Status message with score, items remaining, and controls
        cyan_score = Fore.CYAN + Style.BRIGHT + "Score:" + Style.RESET_ALL
        yellow_items = Fore.YELLOW + Style.BRIGHT + "Items Remaining:" + Style.RESET_ALL
        
        status_msg = f"{cyan_score} {self.score} | {yellow_items} {self.total_items} | Controls: WASD, Q=Quit\r\n"
        # If all items are collected, display a message indicating that the portal is active
        if self.total_items == 0:
            magenta_portal = Fore.MAGENTA + Style.BRIGHT + "[!] PORTAL ACTIVE: Reach 'E' to escape! [!]" + Style.RESET_ALL
            status_msg = f"{cyan_score} {self.score} | {magenta_portal}\r\n"
    
        output = status_msg
        output += "─" * self.width + "\r\n"
        
        # Render game grid, displaying player, enemy, walls, items, and exit
        for y in range(self.height):
            row_str = ""
            for x in range(self.width):
                # Render the player character if the current cell matches the player's position
                if x == self.player.x and y == self.player.y:
                    row_str += f"{self.player.color_style}{self.player.token}{Style.RESET_ALL}"
                # Render the enemy character if the current cell matches the enemy's position
                elif x == self.enemy.x and y == self.enemy.y:
                    row_str += f"{self.enemy.color_style}{self.enemy.token}{Style.RESET_ALL}"
                else:
                    cell = self.grid[y][x]
                    # Render walls
                    if cell == "#":
                        row_str += "|"
                    # Render items
                    elif cell == "*":
                        row_str += f"{Fore.YELLOW}{Style.BRIGHT}*{Style.RESET_ALL}"
                    # Render exit
                    elif cell == "E":
                        row_str += f"{Fore.MAGENTA}{Style.BRIGHT}E{Style.RESET_ALL}"
                    # Render empty spaces
                    else:
                        row_str += f"{Fore.WHITE}{Style.DIM}.{Style.RESET_ALL}"
            output += row_str + "\r\n"
        
        # Flush the output to the terminal to ensure it displays immediately
        sys.stdout.write(output)
        sys.stdout.flush()

    def run(self) -> None:
        # Main game loop that continues until the game state changes from "RUNNING"
        while self.game_state == "RUNNING":
            self.render_frame()
            key = self.get_keypress().lower()
            
            # Handle player input for movement and quitting the game
            if key == 'q':
                self.game_state = "QUIT"
            elif key == 'w': self.update_game_tick(0, -1)
            elif key == 's': self.update_game_tick(0, 1)
            elif key == 'a': self.update_game_tick(-1, 0)
            elif key == 'd': self.update_game_tick(1, 0)

        # Clear the terminal and display the final game state message
        os.system('clear')
        if self.game_state == "WON":
            print(Fore.GREEN + Style.BRIGHT + f"CONGRATULATIONS! You escaped! Final Score: {self.score}\n")
        elif self.game_state == "LOST":
            print(Fore.RED + Style.BRIGHT + f"GAME OVER :( The enemy caught you. Final Score: {self.score}\n")
        else:
            print("Game session terminated.\n")

if __name__ == "__main__":
    engine = RoguelikeEngine()
    engine.run()