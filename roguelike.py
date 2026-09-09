# Author: Nicoletta Beltrante
# A simple terminal-based roguelike game where the player navigates a grid, collects items, and avoids an enemy. 
# The game features colored output for better visual distinction of game elements!

import os
import sys
import termios
import tty
import random
from collections import deque
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
        super().__init__(x, y, "♞", Fore.GREEN + Style.BRIGHT)
        self.has_shield = False

# Define the Enemy class, inheriting from Entity
class Enemy(Entity):
    def __init__(self, x: int, y: int, behavior: str, move_interval: int):
        super().__init__(x, y, "☠", Fore.RED + Style.BRIGHT)
        self.behavior = behavior
        self.move_interval = move_interval
        self.patrol_direction = (1, 0)

    # Calculate the next move for the enemy towards the player, avoiding walls
    def calculate_next_move(self, target_x: int, target_y: int, grid: list[list[str]]) -> tuple[int, int]:

        # Chaser behavior: Use BFS to find the shortest path to the player
        if self.behavior == "chaser":
            height = len(grid)
            width = len(grid[0])
            start = (self.x, self.y)
            target = (target_x, target_y)
            queue = deque([(start, None)])
            # Dictionary to track the first step taken to reach each position
            first_steps: dict[tuple[int, int], tuple[int, int] | None] = {start: None}

            # Perform a breadth-first search
            while queue:
                (x, y), first_step = queue.popleft()
                if (x, y) == target:
                    return first_step or (0, 0)

                # Explore adjacent positions (up, down, left, right) and add them to the queue if they are valid
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_x = x + dx
                    next_y = y + dy
                    next_position = (next_x, next_y)
                    if (
                        0 <= next_x < width
                        and 0 <= next_y < height
                        and grid[next_y][next_x] != "#"
                        and next_position not in first_steps
                    ):
                        queue.append((next_position, first_step or (dx, dy)))
                        first_steps[next_position] = first_step or (dx, dy)

        # Patroller behavior: Move in a fixed direction and reverse when hitting a wall
        if self.behavior == "patroller":
            dx, dy = self.patrol_direction
            next_x = self.x + dx
            next_y = self.y + dy

            # Reverse direction when the next cell is blocked
            if (
                not 0 <= next_x < len(grid[0])
                or not 0 <= next_y < len(grid)
                or grid[next_y][next_x] == "#"
            ):
                self.patrol_direction = (-dx, -dy)
                dx, dy = self.patrol_direction

            return dx, dy

        # Random behavior: Move to a random adjacent cell that is not blocked
        if self.behavior == "random":
            possible_moves = []
            
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                next_x = self.x + dx
                next_y = self.y + dy
            
                if (
                    0 <= next_x < len(grid[0])
                    and 0 <= next_y < len(grid)
                    and grid[next_y][next_x] != "#"
                ):
                    possible_moves.append((dx, dy))
            
            return random.choice(possible_moves) if possible_moves else (0, 0)
            
        return 0, 0

# Class to manage the game engine, including the game loop, rendering, and input handling
class RoguelikeEngine:
    def __init__(self, width: int = 30, height: int = 12):
        self.player = Player(2, 2)
        self.score = 0
        self.width: int = width
        self.height: int = height
        self.level: int = 1
        self.enemies: list[Enemy] = []
        self.total_items: int = 0
        self.turn_count: int = 0
        self.game_state: str = "RUNNING"
        self.grid: list[list[str]] = []
        self.generate_map()
        self.create_enemies()
    
    # Generate the game map with walls, items, and an exit
    def generate_map(self) -> None:
        self.grid = [["." for _ in range(self.width)] for _ in range(self.height)]
        self.total_items = 0
        shield_position = (self.width // 2, self.height // 2 - 2)
        for y in range(self.height):
            for x in range(self.width):
                # Create walls around the edges of the map
                if (x, y) == shield_position:
                    self.grid[y][x] = "◆"
                elif x == 0 or y == 0 or x == self.width - 1 or y == self.height - 1:
                    self.grid[y][x] = "#"
                # Randomly place walls and items within the map, keeping some distance from the edges
                elif random.random() < 0.10 and (x > 3 or y > 3) and (x < self.width - 4):
                    self.grid[y][x] = "#"
                elif random.random() < 0.04 and (x > 3 or y > 3):
                    self.grid[y][x] = "✦"
                    self.total_items += 1
        # Ensures there is at least one item in the game for the player to collect
        if self.total_items == 0:
            self.grid[5][5] = "✦"
            self.total_items = 1

    # Create enemies based on the current level, with different behaviors and move intervals
    def create_enemies(self) -> None:
        # Level 1: 1 chaser
        if self.level == 1:
            enemy_specs = [("chaser", 3)]
        # Level 2: 1 chasers and 1 patroller
        elif self.level == 2:
            enemy_specs = [("chaser", 2), ("patroller", 1)]
        # Level 3: 1 chaser and 1 random
        else:
            enemy_specs = [("chaser", 1), ("random", 1)]

        # Keep track of occupied positions to avoid spawning enemies on top of the player or each other
        shield_position = (self.width // 2, self.height // 2 - 2)
        occupied_positions = {(self.player.x, self.player.y), shield_position}
        self.enemies = []
        for behavior, move_interval in enemy_specs:
            spawn_x, spawn_y = self.find_enemy_spawn(occupied_positions)
            self.enemies.append(
                Enemy(spawn_x, spawn_y, behavior, move_interval)
            )
            occupied_positions.add((spawn_x, spawn_y))

    # Find a safe spawn position for an enemy, avoiding walls, the player, and other enemies
    def find_enemy_spawn(
        self,
        occupied_positions: set[tuple[int, int]]
    ) -> tuple[int, int]:
        # Generate a list of safe positions that are not walls, not occupied, and at least 6 units away from the player
        safe_positions = [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if self.grid[y][x] != "#"
            and (x, y) not in occupied_positions
            and abs(x - self.player.x) + abs(y - self.player.y) >= 6
        ]
        # If no safe positions are found, find any unoccupied position
        if not safe_positions:
            safe_positions = [
                (x, y)
                for y in range(self.height)
                for x in range(self.width)
                if self.grid[y][x] != "#"
                and (x, y) not in occupied_positions
            ]

        return random.choice(safe_positions)

    # Track user keypresses
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

    # Update the game state based on player movement, item collection, and enemy interactions
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
            if self.grid[self.player.y][self.player.x] == "✦":
                self.score += 10
                self.total_items -= 1
                self.grid[self.player.y][self.player.x] = "."
                if self.total_items == 0:
                    self.grid[self.height // 2][self.width // 2] = "◎"

            elif self.grid[self.player.y][self.player.x] == "◆":
                self.player.has_shield = True
                self.grid[self.player.y][self.player.x] = "."

            # Check if the player has reached the exit
            elif self.grid[self.player.y][self.player.x] == "◎":
                if self.level == 3:
                    self.game_state = "WON"
                else:
                    self.level += 1
                    self.turn_count = 0
                    self.player = Player(2, 2)
                    self.generate_map()
                    self.create_enemies()
                return

        # Check if the player has collided with the enemy
        for enemy in self.enemies:
            if self.player.x == enemy.x and self.player.y == enemy.y:
                if self.player.has_shield:
                    self.player.has_shield = False

                    occupied_positions = {
                        (self.player.x, self.player.y)
                    }
                    occupied_positions.update(
                        (other_enemy.x, other_enemy.y)
                        for other_enemy in self.enemies
                        if other_enemy is not enemy
                    )

                    enemy.x, enemy.y = self.find_enemy_spawn(occupied_positions)
                else:
                    self.game_state = "LOST"
                    return

       # Move each enemy based on their behavior and move interval
        for enemy in self.enemies:
            if self.turn_count > 0 and self.turn_count % enemy.move_interval == 0:
                edx, edy = enemy.calculate_next_move(
                    self.player.x,
                    self.player.y,
                    self.grid
                )
                enemy.x += edx
                enemy.y += edy

        # Check if the enemy has collided with the player
        for enemy in self.enemies:
            if self.player.x == enemy.x and self.player.y == enemy.y:
                if self.player.has_shield:
                    self.player.has_shield = False
        
                    occupied_positions = {
                        (self.player.x, self.player.y)
                    }
                    occupied_positions.update(
                        (other_enemy.x, other_enemy.y)
                        for other_enemy in self.enemies
                        if other_enemy is not enemy
                    )
        
                    enemy.x, enemy.y = self.find_enemy_spawn(occupied_positions)
                else:
                    self.game_state = "LOST"
                    return

    # Render the current game frame, including the grid, player, enemies, and status messages
    def render_frame(self) -> None:
        # Clear the terminal screen before rendering the new frame
        os.system('clear')

        # Define colored labels for the status message
        green_level = Fore.GREEN + Style.BRIGHT + f"Level:" + Style.RESET_ALL
        cyan_score = Fore.CYAN + Style.BRIGHT + "Score:" + Style.RESET_ALL
        yellow_items = Fore.YELLOW + Style.BRIGHT + "Items Remaining:" + Style.RESET_ALL
        cyan_enemy_speeds = Fore.CYAN + Style.BRIGHT + "Enemy Speeds:" + Style.RESET_ALL
        blue_shield = Fore.BLUE + Style.BRIGHT + "SHIELD ACTIVATED | " + Style.RESET_ALL
        yellow_controls = Fore.YELLOW + Style.BRIGHT + "Controls:" + Style.RESET_ALL

        # Display enemy behaviors and their move intervals in the status message
        intervals = ", ".join(
            f"{enemy.behavior}: {enemy.move_interval}"
            for enemy in self.enemies
        )
        shield_status = (
            f"{blue_shield}"
            if self.player.has_shield
            else ""
        )

        # Construct the status message with level, score, items remaining, enemy speeds, and controls
        status_msg = (
            f"{green_level} {self.level}/3 | {cyan_score} {self.score} | "
            f"{yellow_items} {self.total_items} | {cyan_enemy_speeds} {intervals} | "
            f"{shield_status}"
            f"{yellow_controls} WASD, Q=Quit\r\n"
        )      

        # If all items are collected, display a message indicating that the portal is active
        if self.total_items == 0:
            magenta_portal = Fore.MAGENTA + Style.BRIGHT + "[!] PORTAL ACTIVE: Reach '◎' to escape! [!]" + Style.RESET_ALL
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
                # Render each enemy character if the current cell matches the enemy's position
                else:
                    enemy_at_position = next(
                        (
                            enemy for enemy in self.enemies
                            if enemy.x == x and enemy.y == y
                        ),
                        None
                    )

                    if enemy_at_position:
                        row_str += (
                            f"{enemy_at_position.color_style}"
                            f"{enemy_at_position.token}"
                            f"{Style.RESET_ALL}"
                    )
                    else:
                        cell = self.grid[y][x]
                        # Render walls
                        if cell == "#":
                            if(self.player.has_shield == True):
                                row_str += f"{Fore.BLUE}{Style.BRIGHT}▓{Style.RESET_ALL}"
                            else:   
                                row_str += f"{Fore.WHITE}{Style.DIM}▓{Style.RESET_ALL}"
                        # Render items
                        elif cell == "✦":
                            row_str += f"{Fore.YELLOW}{Style.BRIGHT}✦{Style.RESET_ALL}"
                        # Render exit
                        elif cell == "◎":
                            row_str += f"{Fore.MAGENTA}{Style.BRIGHT}◎{Style.RESET_ALL}"
                        # Render empty spaces
                        elif cell == "◆":
                            row_str += f"{Fore.BLUE}{Style.BRIGHT}◆{Style.RESET_ALL}"
                        else:
                            if(self.player.has_shield == True):
                                row_str += f"{Fore.BLUE}{Style.BRIGHT}.{Style.RESET_ALL}"
                            else:
                                row_str += f"{Fore.WHITE}{Style.DIM}.{Style.RESET_ALL}"
            output += row_str + "\r\n"
        
        # Flush the output to the terminal to ensure it displays immediately
        sys.stdout.write(output)
        sys.stdout.flush()

    # Run the main game loop, handling rendering and user input until the game ends
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