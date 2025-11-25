import pygame
import asyncio
import random

# --- CONFIGURATION ---
WIDTH, HEIGHT = 800, 600
FPS = 60

# COLORS
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (50, 205, 50)  # Notes
RED = (200, 0, 0)      # HOD / Enemy
BLUE = (0, 0, 200)     # Boy
PINK = (255, 105, 180) # Girl
BROWN = (139, 69, 19)  # Obstacles
GOLD = (255, 215, 0)   # Gate
FLOOR = (30, 30, 30)   # Dark Grey Floor

# --- ASSET LOADER ---
def load_asset(filename, color, size):
    """Loads image if exists, else returns colored square."""
    try:
        path = f"assets/{filename}"
        img = pygame.image.load(path)
        return pygame.transform.scale(img, size)
    except:
        surf = pygame.Surface(size)
        surf.fill(color)
        return surf

# --- CLASSES ---
class Player(pygame.sprite.Sprite):
    def __init__(self, gender, x, y):
        super().__init__()
        self.gender = gender
        self.base_speed = 5
        self.speed = self.base_speed
        
        # Gender Selection
        if gender == 'Male':
            self.image = load_asset("boy.png", BLUE, (30, 30))
        else:
            self.image = load_asset("girl.png", PINK, (30, 30))
            
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.lives = 3
        self.boost_timer = 0

    def update(self, keys, walls):
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy = -self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy = self.speed

        # Move X
        self.rect.x += dx
        if pygame.sprite.spritecollide(self, walls, False):
            self.rect.x -= dx # Undo move if hit wall
        
        # Move Y
        self.rect.y += dy
        if pygame.sprite.spritecollide(self, walls, False):
            self.rect.y -= dy # Undo move if hit wall

        # Keep on screen
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

        # Boost Decay
        if self.boost_timer > 0:
            self.boost_timer -= 1
        else:
            self.speed = self.base_speed

    def boost(self):
        self.speed = self.base_speed * 1.8
        self.boost_timer = 180 # 3 seconds

class Enemy(pygame.sprite.Sprite):
    def __init__(self, level):
        super().__init__()
        self.image = load_asset("hod.png", RED, (35, 35))
        self.rect = self.image.get_rect()
        self.rect.topleft = (WIDTH - 50, HEIGHT - 50)
        self.speed = 2.0 + (level * 0.3)
        
    def update(self, target_rect):
        # Chase Logic
        dx, dy = 0, 0
        if self.rect.x < target_rect.x: dx = self.speed
        if self.rect.x > target_rect.x: dx = -self.speed
        if self.rect.y < target_rect.y: dy = self.speed
        if self.rect.y > target_rect.y: dy = -self.speed
        
        self.rect.x += dx
        self.rect.y += dy

class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(BROWN)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

class Note(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = load_asset("note.png", GREEN, (15, 15))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

class Gate(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((80, 10))
        self.image.fill(GOLD)
        self.rect = self.image.get_rect()
        self.rect.midtop = (WIDTH // 2, 0) # Top center

# --- MAIN GAME ---
async def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Campus Run")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 24)
    big_font = pygame.font.SysFont("Arial", 48)

    # States
    LOGIN, PLAY, GAME_OVER, WIN = 0, 1, 2, 3
    state = LOGIN
    
    # Game Data
    player_name = ""
    gender = "Male"
    level = 1
    score = 0
    lives_lost_level = 0
    
    # Groups
    sprites = pygame.sprite.Group()
    walls = pygame.sprite.Group()
    notes = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    
    player = None
    hod = None
    gate = Gate()

    def start_level(lvl):
        sprites.empty()
        walls.empty()
        notes.empty()
        enemies.empty()
        nonlocal player, hod, lives_lost_level
        lives_lost_level = 0
        
        # Player
        player = Player(gender, 50, HEIGHT - 100)
        sprites.add(player)
        
        # Enemy
        hod = Enemy(lvl)
        sprites.add(hod)
        enemies.add(hod)
        
        # Gate
        sprites.add(gate)
        
        # Random Walls (Classroom furniture)
        for _ in range(10 + lvl):
            w = random.randint(50, 150)
            h = random.randint(20, 50)
            x = random.randint(100, WIDTH - 150)
            y = random.randint(50, HEIGHT - 100)
            wall = Wall(x, y, w, h)
            walls.add(wall)
            sprites.add(wall)
            
        # Notes (Powerups)
        for _ in range(5):
            nx = random.randint(50, WIDTH - 50)
            ny = random.randint(50, HEIGHT - 50)
            note = Note(nx, ny)
            notes.add(note)
            sprites.add(note)

    running = True
    while running:
        screen.fill(FLOOR)
        keys = pygame.key.get_pressed()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            
            if state == LOGIN:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and len(player_name) > 0:
                        start_level(level)
                        state = PLAY
                    elif event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]
                    elif event.key == pygame.K_m: gender = "Male"
                    elif event.key == pygame.K_f: gender = "Female"
                    elif event.unicode.isalnum(): player_name += event.unicode
            
            elif state == GAME_OVER or state == WIN:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    # Restart Game
                    level = 1
                    score = 0
                    player.lives = 3
                    state = LOGIN
                
                if state == WIN and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    # Next Level
                    level += 1
                    start_level(level)
                    state = PLAY

        # --- LOGIC ---
        if state == LOGIN:
            t1 = big_font.render("CAMPUS RUN", True, WHITE)
            t2 = font.render(f"Name: {player_name}_", True, WHITE)
            t3 = font.render(f"Gender (M/F): {gender}", True, GREEN)
            t4 = font.render("Press ENTER to Start", True, GOLD)
            screen.blit(t1, (WIDTH//2 - 100, 100))
            screen.blit(t2, (WIDTH//2 - 100, 250))
            screen.blit(t3, (WIDTH//2 - 100, 300))
            screen.blit(t4, (WIDTH//2 - 100, 400))
            
        elif state == PLAY:
            player.update(keys, walls)
            hod.update(player.rect)
            
            # Interactions
            if pygame.sprite.spritecollide(player, notes, True):
                player.boost()
            
            if pygame.sprite.spritecollide(player, enemies, False):
                player.lives -= 1
                lives_lost_level += 1
                player.rect.topleft = (50, HEIGHT - 100) # Reset Pos
                hod.rect.topleft = (WIDTH - 50, HEIGHT - 50) # Reset HOD
                screen.fill(RED) # Hit flash
                if player.lives <= 0:
                    state = GAME_OVER
            
            if pygame.sprite.collide_rect(player, gate):
                pts = 1000 - (lives_lost_level * 500)
                if pts < 0: pts = 0
                score += pts
                state = WIN

            sprites.draw(screen)
            
            # HUD
            hud = font.render(f"Score: {score} | Lvl: {level} | Lives: {player.lives}", True, WHITE)
            screen.blit(hud, (10, 10))

        elif state == GAME_OVER:
            t1 = big_font.render("GAME OVER", True, RED)
            t2 = font.render(f"Final Score: {score}", True, WHITE)
            t3 = font.render("Press R to Restart", True, WHITE)
            screen.blit(t1, (WIDTH//2 - 120, 200))
            screen.blit(t2, (WIDTH//2 - 80, 300))
            screen.blit(t3, (WIDTH//2 - 80, 350))

        elif state == WIN:
            t1 = big_font.render("LEVEL COMPLETE", True, GOLD)
            t2 = font.render("Press SPACE for Next Level", True, WHITE)
            screen.blit(t1, (WIDTH//2 - 150, 200))
            screen.blit(t2, (WIDTH//2 - 120, 300))

        pygame.display.flip()
        await asyncio.sleep(0) # Required for Web

if __name__ == "__main__":
    asyncio.run(main())
