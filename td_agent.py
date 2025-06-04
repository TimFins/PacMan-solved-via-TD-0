import random
from collections import defaultdict

class TDAgent:
    def __init__(self, learning_rate=0.05, discount_factor=1, exploration_rate=0.05):
        self.V = defaultdict(float)  # State-value function: maps state → estimated value
        self.learning_rate = learning_rate  # α in TD update
        self.discount_factor = discount_factor  # γ: future reward discounting
        self.exploration_rate = exploration_rate  # ε: chance to explore randomly

    def get_state(self, game):
        # Extracts a hashable representation of the game state
        pos = game.player_pos
        level = game.level
        tiles = tuple(tuple(row) for row in level)
        return (pos, tiles)

    def get_state_from_level(self, pos, level):
        # Used to create a new state tuple after simulating a move
        tiles = tuple(tuple(row) for row in level)
        return (pos, tiles)

    def simulate_adjacent_states(self, game):
        x, y = game.player_pos
        directions = {
            'left': (-1, 0),
            'right': (1, 0),
            'up': (0, -1),
            'down': (0, 1)
        }
        results = {}
        for dir, (dx, dy) in directions.items():
            nx, ny = x + dx, y + dy
            
            if not game.can_move(nx, ny):
                results[dir] = (self.get_state_from_level((x, y), game.level), 1, False)
                continue
            
            # Create a deep copy of the level to simulate the move
            new_level = [row[:] for row in game.level]
            tile = new_level[ny][nx]

            # Assign immediate reward based on the tile type
            reward = {
                'G': 100,   # Ghost: high penalty
                'E': 0,     # Exit/goal: neutral
                '*': -10,   # Collectible/star: good
                '.': -1,    # Minor reward
                ' ': 1      # Empty space: small cost
            }.get(tile, 0)

            # Update player position in the simulated level
            new_level[y][x] = ' '
            new_level[ny][nx] = 'P'
            new_state = self.get_state_from_level((nx, ny), new_level)
            terminal = tile in {'G', 'E'}

            results[dir] = (new_state, reward, terminal)

        return results

    def choose_action(self, game, actions_by_name):
        if random.random() < self.exploration_rate:
            # Explore: choose a random legal action
            return random.choice(list(actions_by_name.values()))

        # Exploit: evaluate all adjacent states
        state_sim = self.simulate_adjacent_states(game)
        best_value = float('inf') 
        best_dirs = []

        for direction, (next_state, reward, terminal) in state_sim.items():
            v = reward
            if not terminal:
                v += self.discount_factor * self.V[next_state]

            if v < best_value:
                best_value = v
                best_dirs = [direction]
            elif v == best_value:
                best_dirs.append(direction)

        if best_dirs:
            # Break ties randomly
            chosen = random.choice(best_dirs)
            return actions_by_name[chosen]
        else:
            return random.choice(list(actions_by_name.values()))

    def update(self, old_state, reward, new_state):
        # TD(0) update rule
        old_v = self.V[old_state]
        self.V[old_state] += self.learning_rate * (
            reward + self.discount_factor * self.V[new_state] - old_v
        )
