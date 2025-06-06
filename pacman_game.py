import pygame
import os
import sys
from td_agent import TDAgent

agent = TDAgent()

TILE_SIZE = 64
BORDER_THICKNESS = 120
FPS = 60
DEFAULT_MOVES_PER_SECOND = 1
DEFAULT_GAMMA = 0.9
PAUSE = 1
LEVEL = [
    ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', 'X', 'X', 'X', 'X', 'X', '.', 'X', '.', 'X', 'X', '.'],
    ['.', 'X', 'G', '.', '.', 'X', '.', 'X', '.', '*', 'X', '.'],
    ['.', 'X', '.', '.', 'P', 'X', '.', 'X', '.', '.', 'X', '.'],
    ['.', 'X', '.', '.', 'X', 'X', 'G', 'X', '.', '.', 'X', '.'],
    ['.', '.', '.', '.', '.', '.', '.', 'X', '.', '.', 'X', 'E'],
]

TILE_COLORS = {
    ' ': (0, 0, 0),
    '.': (200, 200, 200),
    '*': (255, 255, 0),
    'G': (255, 0, 0),
    'E': (0, 200, 0),
    'P': (0, 0, 255),
    'X': (0, 0, 255),
}

DEFAULT_TEXT_FIELD_COLOR = (70, 130, 180)

HIGHLIGHTED_TEXT_FIELD_COLOR = (100, 160, 210)

IMAGE_PATHS = {
    ' ': 'assets/empty.PNG',
    'P': 'assets/pacman.PNG',
    'G': 'assets/ghost.PNG',
    '.': 'assets/bonus.PNG',
    '*': 'assets/star.PNG',
    'E': 'assets/goal.PNG',
    'X': 'assets/wall.PNG'
}

class PacManGame:
    def __init__(self, level, start_maximized=False):
        pygame.init()
        self.level = [row[:] for row in level]
        self.height = len(level)
        self.width = len(level[0])
        self.gamma = str(DEFAULT_GAMMA)
        self.penalty = 0
        self.max_penalty = None
        self.find_player()
        self.last_scores = []
        self.max_scores_to_show = 55

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
        self.other_pacman_orientations = self.generate_other_pacman_orientations(self.images.get("P"))
        self.is_clockwise_orientation = True
        self.clock = pygame.time.Clock()
        self.running = True
        self.is_paused = True
        self.resume_stop_button_text = "Start"
        self.perform_step_forward = False
        self.moves_per_second = str(DEFAULT_MOVES_PER_SECOND)
        self.is_adjust_play_rate_text_field_active = False
        self.is_adjust_gamma_text_field_active = False
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

    def generate_other_pacman_orientations(self, original_pacman):
        pacman_orientations = {
            "facing_right": original_pacman
        }
        pacman_orientations["facing_left"] = pygame.transform.flip(original_pacman, flip_x=True, flip_y=False)
        pacman_orientations["facing_up_clockwise"] = pygame.transform.rotate(original_pacman, 90)
        pacman_orientations["facing_up_counterclockwise"] = pygame.transform.rotate(pygame.transform.flip(original_pacman, flip_x=True, flip_y=False), -90)
        pacman_orientations["facing_down_clockwise"] = pygame.transform.rotate(original_pacman, -90)
        pacman_orientations["facing_down_counterclockwise"] = pygame.transform.rotate(pygame.transform.flip(original_pacman, flip_x=True, flip_y=False), 90)
        
        return pacman_orientations

    def find_player(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.level[y][x] == 'P':
                    self.player_pos = (x, y)
                    return

    def can_move(self, nx, ny):
        if not (0 <= nx < self.width and 0 <= ny < self.height):
            return False
        if self.level[ny][nx] == 'X':
            return False
        
        return True

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
        self.is_clockwise_orientation = False
        self.change_pacman_orientation("facing_left")
        self.move_pacman(-1, 0)

    def move_right(self):
        self.is_clockwise_orientation = True
        self.change_pacman_orientation("facing_right")
        self.move_pacman(1, 0)

    def move_up(self):
        if self.is_clockwise_orientation:
            self.change_pacman_orientation("facing_up_clockwise")
        else:
            self.change_pacman_orientation("facing_up_counterclockwise")
        self.move_pacman(0, -1)

    def move_down(self):
        if self.is_clockwise_orientation:
            self.change_pacman_orientation("facing_down_clockwise")
        else:
            self.change_pacman_orientation("facing_down_counterclockwise")
        self.move_pacman(0, 1)
        
    def change_pacman_orientation(self, orientation):
        self.images["P"] = self.other_pacman_orientations.get(orientation)

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
            avg_text = self.font.render(f"Average for last {last_scores_to_consider} rounds: {avg_score:.2f}", True, (255, 255, 255))
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

        # Draw resume/pause button
        resume_stop_button_rect = pygame.Rect(20, self.screen.get_height() - 80, 160, 60)
        pygame.draw.rect(self.screen, (70, 130, 180), resume_stop_button_rect)
        resume_stop_button_text_surf = self.font.render(self.resume_stop_button_text, True, (255, 255, 255))
        resume_stop_button_text_rect = resume_stop_button_text_surf.get_rect(center=resume_stop_button_rect.center)
        self.screen.blit(resume_stop_button_text_surf, resume_stop_button_text_rect)
        self.resume_stop_button = resume_stop_button_rect
        
        # Step forwards button
        step_forwards_button_rect = pygame.Rect(200, self.screen.get_height() - 80, 160, 60)
        pygame.draw.rect(self.screen, (70, 130, 180), step_forwards_button_rect)
        step_forwards_button_text_surf = self.font.render("Step forward", True, (255, 255, 255))
        step_forwards_button_text_rect = step_forwards_button_text_surf.get_rect(center=step_forwards_button_rect.center)
        self.screen.blit(step_forwards_button_text_surf, step_forwards_button_text_rect)
        self.step_forwards_button = step_forwards_button_rect
        
        # Input field for adjusting play rate
        adjust_play_rate_text_field_rect = pygame.Rect(380, self.screen.get_height() - 80, 160, 60)
        pygame.draw.rect(self.screen, DEFAULT_TEXT_FIELD_COLOR if not game.is_adjust_play_rate_text_field_active else HIGHLIGHTED_TEXT_FIELD_COLOR, adjust_play_rate_text_field_rect)
        adjust_play_rate_text_field_text_surf = self.font.render(str(game.moves_per_second), True, (255, 255, 255))
        adjust_play_rate_text_field_text_rect = adjust_play_rate_text_field_text_surf.get_rect(center=adjust_play_rate_text_field_rect.center)
        self.screen.blit(adjust_play_rate_text_field_text_surf, adjust_play_rate_text_field_text_rect)
        self.adjust_play_rate_text_field = adjust_play_rate_text_field_rect

        # Text for play rate input field
        play_rate_surf = self.font.render("moves/sec", True, (255, 255, 255))
        play_rate_rect = play_rate_surf.get_rect(center=(adjust_play_rate_text_field_rect.center[0], adjust_play_rate_text_field_rect.center[1]-50))
        self.screen.blit(play_rate_surf, play_rate_rect)

        # Quit program button
        quit_program_button_rect = pygame.Rect(self.screen.get_width() - 180, self.screen.get_height() - 80, 160, 60)
        pygame.draw.rect(self.screen, (70, 130, 180), quit_program_button_rect)
        quit_program_button_text_surf = self.font.render("Quit", True, (255, 255, 255))
        quit_program_button_text_rect = quit_program_button_text_surf.get_rect(center=quit_program_button_rect.center)
        self.screen.blit(quit_program_button_text_surf, quit_program_button_text_rect)
        self.quit_program_button = quit_program_button_rect
        
        # Input field for adjusting gamma
        adjust_gamma_text_field_rect = pygame.Rect(560, self.screen.get_height() - 80, 160, 60)
        pygame.draw.rect(self.screen, DEFAULT_TEXT_FIELD_COLOR if not game.is_adjust_gamma_text_field_active else HIGHLIGHTED_TEXT_FIELD_COLOR, adjust_gamma_text_field_rect)
        adjust_gamma_text_field_text_surf = self.font.render(str(game.gamma), True, (255, 255, 255))
        adjust_gamma_text_field_text_rect = adjust_gamma_text_field_text_surf.get_rect(center=adjust_gamma_text_field_rect.center)
        self.screen.blit(adjust_gamma_text_field_text_surf, adjust_gamma_text_field_text_rect)
        self.adjust_gamma_text_field = adjust_gamma_text_field_rect
        
        # Text for gamma input field
        gamma_text_surf = self.font.render("Gamma", True, (255, 255, 255))
        gamma_text_rect = gamma_text_surf.get_rect(center=(adjust_gamma_text_field_rect.center[0], adjust_gamma_text_field_rect.center[1]-50))
        self.screen.blit(gamma_text_surf, gamma_text_rect)

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
        
        last_step_time = pygame.time.get_ticks()
        # milliseconds between moves. 
        # E.g. MOVES_PER_SECOND = 2 --> 2 moves per second --> 500ms delay between each move

        while game.running:
            try:
                STEP_DELAY = 1000 / float(game.moves_per_second)
            except:
                STEP_DELAY = 1000
            current_time = pygame.time.get_ticks()
            if (not game.is_paused and current_time - last_step_time >= STEP_DELAY) or game.perform_step_forward:
                game.perform_step_forward = False
                last_step_time = current_time
                old_state = agent.get_state(game)
                action = agent.choose_action(game, move_mapping)
                old_penalty = game.penalty

                action()

                reward = game.penalty - old_penalty
                new_state = agent.get_state(game)
                agent.update(old_state, reward, new_state)
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if hasattr(game, 'resume_stop_button') and game.resume_stop_button.collidepoint(event.pos):
                        if game.is_paused:
                            game.resume_stop_button_text = "Stop"
                            game.is_paused = False
                        else:
                            game.resume_stop_button_text = "Start"
                            game.is_paused = True
                        game.draw()
                    if hasattr(game, 'step_forwards_button') and game.step_forwards_button.collidepoint(event.pos):
                        if game.is_paused:
                            game.perform_step_forward = True
                    if hasattr(game, 'adjust_play_rate_text_field') and game.adjust_play_rate_text_field.collidepoint(event.pos):
                        game.is_adjust_play_rate_text_field_active = True
                    else:
                        game.is_adjust_play_rate_text_field_active = False
                    if hasattr(game, 'adjust_gamma_text_field') and game.adjust_gamma_text_field.collidepoint(event.pos):
                        game.is_adjust_gamma_text_field_active = True
                    else:
                        game.is_adjust_gamma_text_field_active = False
                    game.draw()
                    if hasattr(game, 'quit_program_button') and game.quit_program_button.collidepoint(event.pos):
                        running = False
                        sys.exit(0)
                elif event.type == pygame.KEYDOWN:
                    if hasattr(game, 'adjust_play_rate_text_field') and game.is_adjust_play_rate_text_field_active:
                        if event.key == pygame.K_BACKSPACE:
                            game.moves_per_second = game.moves_per_second[:-1]
                        else:
                            game.moves_per_second += event.unicode
                    if hasattr(game, 'adjust_gamma_text_field') and game.is_adjust_gamma_text_field_active:
                        if event.key == pygame.K_BACKSPACE:
                            game.gamma = game.gamma[:-1]
                        else:
                            game.gamma += event.unicode
                        game.draw()
            pygame.time.wait(PAUSE)


        # Update score tracking
        if game.max_penalty is None or game.penalty < game.max_penalty:
            game.max_penalty = game.penalty
        game.last_scores.append(game.penalty)

        print(f"Round {game.round_num} ended. Penalty: {game.penalty} | Best score: {game.max_penalty}")
        pygame.time.wait(PAUSE)
        round_num += 1
