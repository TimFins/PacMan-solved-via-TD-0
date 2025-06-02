import pygame
import os
from td_agent import TDAgent
agent = TDAgent()

TILE_SIZE = 64
BORDER_THICKNESS = 120
FPS = 5000
PAUSE = 1
LEVEL = [
    ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', ' ', ' ', ' ', ' ', ' ', '.', ' ', '.', ' ', ' ', '.'],
    ['.', ' ', 'G', '.', '.', ' ', '.', ' ', '.', '*', ' ', '.'],
    ['.', ' ', '.', '.', 'P', ' ', '.', ' ', '.', '.', ' ', '.'],
    ['.', ' ', '.', '.', ' ', ' ', 'G', ' ', '.', '.', ' ', '.'],
    ['.', '.', '.', '.', '.', '.', '.', ' ', '.', '.', ' ', 'E'],
]

TILE_COLORS = {
    ' ': (0, 0, 255),
    '.': (200, 200, 200),
    '*': (255, 255, 0),
    'G': (255, 0, 0),
    'E': (0, 200, 0),
    'P': (0, 0, 255),
}

IMAGE_PATHS = {
    'P': 'assets/pacman.png',
    'G': 'assets/ghost.png',
    '.': 'assets/bonus.png',
    '*': 'assets/star.png',
    'E': 'assets/goal.png',
}

class PacManGame:
    def __init__(self, level, start_maximized=False):
        pygame.init()
        self.level = [row[:] for row in level]
        self.height = len(level)
        self.width = len(level[0])
        self.penalty = 0
        self.max_penalty = None
        self.find_player()
        self.last_scores = []
        self.max_scores_to_show = 25

        flags = pygame.RESIZABLE

        if start_maximized:
            info = pygame.display.Info()
            window_width = info.current_w
            window_height = info.current_h

            max_tile_width = (window_width - BORDER_THICKNESS * 2) // self.width
            max_tile_height = (window_height - BORDER_THICKNESS * 2) // self.height
            self.tile_size = min(max_tile_width, max_tile_height)
            if self.tile_size < 10:
                self.tile_size = 10

            self.screen = pygame.display.set_mode((window_width, window_height), flags)
        else:
            self.tile_size = TILE_SIZE
            window_width = self.width * self.tile_size + BORDER_THICKNESS * 2
            window_height = self.height * self.tile_size + BORDER_THICKNESS * 2
            self.screen = pygame.display.set_mode((window_width, window_height), flags)

        pygame.display.set_caption("PacMan with TD(0)")
        self.font = pygame.font.SysFont("Arial", 24)
        self.images = self.load_images()
        self.clock = pygame.time.Clock()
        self.running = True
        self.round_num = 1

    def load_images(self):
        images = {}
        for tile, path in IMAGE_PATHS.items():
            if os.path.exists(path):
                image = pygame.image.load(path).convert_alpha()
                image = pygame.transform.scale(image, (self.tile_size, self.tile_size))
                images[tile] = image
            else:
                images[tile] = None
        return images

    def find_player(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.level[y][x] == 'P':
                    self.player_pos = (x, y)
                    return

    def can_move(self, nx, ny):
        return 0 <= nx < self.width and 0 <= ny < self.height

    def move_pacman(self, dx, dy):
        if not self.running:
            return
        x, y = self.player_pos
        nx, ny = x + dx, y + dy
        if self.can_move(nx, ny):
            tile = self.level[ny][nx]
            if tile == 'G':
                self.penalty += 100
                self.level[y][x] = ' '
                self.level[ny][nx] = 'P'
                self.player_pos = (nx, ny)
                self.draw()
                print("Game over: hit a ghost! Final penalty:", self.penalty)
                self.running = False
                pygame.time.wait(PAUSE)
                return
            elif tile == '*':
                self.penalty -= 10
            elif tile == '.':
                self.penalty -= 1
            elif tile == ' ':
                self.penalty += 1
            elif tile == 'E':
                self.level[y][x] = ' '
                self.level[ny][nx] = 'P'
                self.player_pos = (nx, ny)
                self.draw()
                print("Goal reached! Final penalty:", self.penalty)
                self.running = False
                pygame.time.wait(PAUSE)
                return

            self.level[y][x] = ' '
            self.level[ny][nx] = 'P'
            self.player_pos = (nx, ny)
            self.draw()
            self.clock.tick(FPS)
        else:
            self.penalty += 1
            self.draw()
            self.clock.tick(FPS)

    def move_left(self):
        self.move_pacman(-1, 0)

    def move_right(self):
        self.move_pacman(1, 0)

    def move_up(self):
        self.move_pacman(0, -1)

    def move_down(self):
        self.move_pacman(0, 1)

    def draw(self):
        self.screen.fill((50, 50, 50))

        for y in range(self.height):
            for x in range(self.width):
                tile = self.level[y][x]
                rect = pygame.Rect(
                    BORDER_THICKNESS + x * self.tile_size,
                    BORDER_THICKNESS + y * self.tile_size,
                    self.tile_size, self.tile_size)

                pygame.draw.rect(self.screen, (0, 0, 255), rect)

                image = self.images.get(tile)
                if image:
                    small_image = pygame.transform.smoothscale(image, (self.tile_size - 4, self.tile_size - 4))
                    self.screen.blit(small_image, (rect.x + 2, rect.y + 2))
                else:
                    pygame.draw.rect(self.screen, TILE_COLORS[tile], rect)

        # Penalty top-left
        penalty_text = self.font.render(f"Penalty: {self.penalty}", True, (255, 255, 255))
        self.screen.blit(penalty_text, (5, 5))

        if self.last_scores:
            last_scores_to_consider = 25
            avg_score = sum(self.last_scores[-last_scores_to_consider:]) / last_scores_to_consider
            avg_text = self.font.render(f"Average: {avg_score:.2f}", True, (255, 255, 255))
            self.screen.blit(avg_text, (5, 40))
            y_start = 80
        else:
            y_start = 40

        # Last Scores
        self.screen.blit(self.font.render("Last Scores:", True, (255, 255, 255)), (5, y_start))
        for i, score in enumerate(self.last_scores[-self.max_scores_to_show:][::-1]):
            score_text = self.font.render(f"{len(self.last_scores) - i}: {score}", True, (255, 255, 255))
            self.screen.blit(score_text, (5, y_start + 30 + i * 25))

        # Round top-right
        round_text = self.font.render(f"Round: {self.round_num}", True, (255, 255, 255))
        text_rect = round_text.get_rect()
        self.screen.blit(round_text, (self.screen.get_width() - text_rect.width - 5, 5))

        # Max penalty centered top
        max_text_value = f"{self.max_penalty}" if self.max_penalty is not None else "-"
        max_text = self.font.render(f"Best score: {max_text_value}", True, (255, 255, 255))
        max_rect = max_text.get_rect(center=(self.screen.get_width() // 2, 15))
        self.screen.blit(max_text, max_rect)

        pygame.display.flip()

    def close(self):
        pygame.quit()

    def reset(self):
        self.level = [row[:] for row in LEVEL]
        self.find_player()
        self.penalty = 0
        self.running = True
        self.draw()

    def get_possible_moves(self):
        return [self.move_left, self.move_right, self.move_up, self.move_down]

if __name__ == "__main__":
    start_maximized = True
    game = PacManGame(LEVEL, start_maximized=start_maximized)
    round_num = 0

    move_mapping = {
        'left': game.move_left,
        'right': game.move_right,
        'up': game.move_up,
        'down': game.move_down,
    }

    while True:
        game.round_num = round_num + 1
        game.reset()

        print(f"Round {game.round_num} start!")

        state = agent.get_state(game)

        while game.running:
            old_state = agent.get_state(game)
            action = agent.choose_action(game, move_mapping)
            old_penalty = game.penalty

            action()

            reward = game.penalty - old_penalty
            new_state = agent.get_state(game)
            agent.update(old_state, reward, new_state)

        # Update score tracking
        if game.max_penalty is None or game.penalty < game.max_penalty:
            game.max_penalty = game.penalty
        game.last_scores.append(game.penalty)

        print(f"Round {game.round_num} ended. Penalty: {game.penalty} | Best score: {game.max_penalty}")
        pygame.time.wait(PAUSE)
        round_num += 1
