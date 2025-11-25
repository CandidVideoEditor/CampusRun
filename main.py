import pygame
import asyncio # Crucial for Web support
import random
import math

# --- CONFIGURATION ---
WIDTH, HEIGHT = 800, 600
FPS = 60

# COLORS
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (50, 205, 50) # Notes
RED = (200, 0, 0)     # HOD
BLUE = (0, 0, 200)    # Boy
PINK = (255, 105, 180)# Girl
BROWN = (139, 69, 19) # Obstacles
GOLD = (255, 215, 0)  # Gate

# --- ASSET LOADER ---
# This function loads an image if it exists, otherwise returns a colored surface
def load_asset(filename, color, size):
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
        self.original_speed = 5
        self.speed = self.original_speed
        
        # Load Sprite based on Gender
        if gender == 'Male':
            self.image = load_asset("boy.png", BLUE, (40, 40))
        else:
            self.image = load_asset("girl.png", PINK, (40, 40))
            
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

        # Move and check wall collisions
        self.rect.x += dx
        if pygame.sprite.spritecollide(self, walls, False):
            self.rect.x -= dx # Undo move
        
        self.rect.y += dy
        if pygame.sprite.spritecollide(self, walls, False):
            self.rect.y -= dy # Undo move

        # Screen boundaries
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

        # Handle Speed Boost decay
        if self.boost_timer > 0:
            self.boost_timer -= 1
        else:
            self.speed = self.original_speed

    def boost(self):
        self.speed = self.original_speed * 1.5
        self.boost_timer = 120 # 2 seconds at 60 FPS

class Enemy(pygame.sprite.Sprite):
    def __init__(self, speed_level):
        super().__init__()
        self.image = load_asset("hod.png", RED, (45, 45))
        self.rect = self.image.get_rect()
        # Spawn away from player
        self.rect.topleft = (WIDTH - 60, HEIGHT - 60) 
        self.speed = 2 + (speed_level * 0.2)
        
    def update(self, player_rect):
        # Simple chasing logic
        dx, dy = 0, 0
        if self.rect.x < player_rect.x: dx = self.speed
        if self.rect.x > player_rect.x: dx = -self.speed
        if self.rect.y < player_rect.y: dy = self.speed
        if self.rect.y > player_rect.y: dy = -self.speed
        
        self.rect.x += dx
        self.rect.y += dy

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(BROWN)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

class Collectible(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = load_asset("note.png", GREEN, (20, 20)) # Neon effect simulated by bright green
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

class Gate(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((60, 10))
        self.image.fill(GOLD)
        self.rect = self.image.get_rect()
        self.rect.midtop = (WIDTH // 2, 0)

# --- GAME MANAGER ---

async def main():
    pygame.init()
    pygame.mixer.init() # Initialize sound
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Campus Run")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    title_font = pygame.font.Font(None, 72)

    # Game States
    STATE_LOGIN = 0
    STATE_PLAYING = 1
    STATE_GAMEOVER = 2
    STATE_LEVEL_COMPLETE = 3
    
    current_state = STATE_LOGIN
    
    # Player Data
    player_name = ""
    player_gender = "Male"
    level = 1
    score = 0
    lives_lost_in_level = 0
    
    # Groups
    all_sprites = pygame.sprite.Group()
    walls = pygame.sprite.Group()
    notes = pygame.sprite.Group()
    enemy_group = pygame.sprite.Group()
    
    player = None
    hod = None
    gate = Gate()
    
    # Sound Load (Try/Except to prevent crash if file missing)
    try:
        bell_sound = pygame.mixer.Sound("assets/school_bell.wav")
    except:
        bell_sound = None

    def setup_level(lvl):
        all_sprites.empty()
        walls.empty()
        notes.empty()
        enemy_group.empty()
        
        nonlocal player, hod, lives_lost_in_level
        lives_lost_in_level = 0
        
        # Spawn Player
        player = Player(player_gender, 50, HEIGHT - 100)
        all_sprites.add(player)
        
        # Spawn HOD
        hod = Enemy(lvl)
        enemy_group.add(hod)
        all_sprites.add(hod)
        
        # Spawn Gate
        all_sprites.add(gate)
        
        # Procedural Map Generation (Campus Classrooms)
        # Create random obstacles/desks
        num_obstacles = 10 + (lvl * 2)
        for _ in range(num_obstacles):
            w, h = random.randint(40, 100), random.randint(20, 60)
            x = random.randint(100, WIDTH - 100)
            y = random.randint(50, HEIGHT - 150)
            wall = Obstacle(x, y, w, h)
            walls.add(wall)
            all_sprites.add(wall)
            
        # Spawn Notes
        for _ in range(5):
            nx = random.randint(50, WIDTH - 50)
            ny = random.randint(50, HEIGHT - 50)
            note = Collectible(nx, ny)
            notes.add(note)
            all_sprites.add(note)

    # --- MAIN LOOP ---
    running = True
    while running:
        screen.fill((30, 30, 30)) # Dark floor background
        
        keys = pygame.key.get_pressed()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if current_state == STATE_LOGIN:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and len(player_name) > 0:
                        setup_level(level)
                        current_state = STATE_PLAYING
                    elif event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]
                    elif event.key == pygame.K_m:
                        player_gender = "Male"
                    elif event.key == pygame.K_f:
                        player_gender = "Female"
                    else:
                        if len(player_name) < 10 and event.unicode.isalnum():
                            player_name += event.unicode
                            
            elif current_state == STATE_GAMEOVER:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        player.lives = 3
                        level = 1
                        score = 0
                        current_state = STATE_LOGIN
                        
            elif current_state == STATE_LEVEL_COMPLETE:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                         level += 1
                         setup_level(level)
                         current_state = STATE_PLAYING

        # --- LOGIC UPDATES ---
        
        if current_state == STATE_LOGIN:
            

[Image of retro video game interface]

            title_text = title_font.render("CAMPUS RUN", True, WHITE)
            name_prompt = font.render(f"Name: {player_name}_", True, WHITE)
            gender_prompt = font.render(f"Press M for Male, F for Female: {player_gender}", True, WHITE)
            start_prompt = font.render("Press ENTER to Confirm", True, GREEN)
            
            screen.blit(title_text, (WIDTH//2 - 150, 100))
            screen.blit(name_prompt, (WIDTH//2 - 100, 250))
            screen.blit(gender_prompt, (WIDTH//2 - 200, 300))
            screen.blit(start_prompt, (WIDTH//2 - 130, 400))
            
            # Show selected sprite preview
            if player_gender == "Male":
                pygame.draw.rect(screen, BLUE, (WIDTH//2 - 20, 200, 40, 40))
            else:
                pygame.draw.rect(screen, PINK, (WIDTH//2 - 20, 200, 40, 40))

        elif current_state == STATE_PLAYING:
            

[Image of pixel art school hallway]

            player.update(keys, walls)
            hod.update(player.rect)
            
            # Note Collection (Speed Boost)
            if pygame.sprite.spritecollide(player, notes, True):
                player.boost()
            
            # HOD Collision (Lose Life)
            if pygame.sprite.spritecollide(player, enemy_group, False):
                player.lives -= 1
                lives_lost_in_level += 1
                # Shake effect logic (simplified as a red flash)
                screen.fill(RED) 
                
                if player.lives <= 0:
                    current_state = STATE_GAMEOVER
                else:
                    # Reset positions but keep level progress
                    player.rect.topleft = (50, HEIGHT - 100)
                    hod.rect.topleft = (WIDTH - 60, HEIGHT - 60)
            
            # Gate Collision (Win Level)
            if pygame.sprite.collide_rect(player, gate):
                if bell_sound: bell_sound.play()
                
                # Scoring Logic
                level_score = 1000
                if lives_lost_in_level == 1: level_score -= 500
                elif lives_lost_in_level == 2: level_score -= 700
                
                score += level_score
                current_state = STATE_LEVEL_COMPLETE

            # Draw
            all_sprites.draw(screen)
            
            # UI
            score_text = font.render(f"Score: {score} | Level: {level}", True, WHITE)
            lives_text = font.render(f"Lives: {player.lives}", True, RED)
            screen.blit(score_text, (10, 10))
            screen.blit(lives_text, (WIDTH - 120, 10))

        elif current_state == STATE_LEVEL_COMPLETE:
            win_text = title_font.render("LEVEL COMPLETE!", True, GOLD)
            score_msg = font.render(f"Total Score: {score}", True, WHITE)
            cont_msg = font.render("Press SPACE for Next Level", True, GREEN)
            screen.blit(win_text, (WIDTH//2 - 200, 200))
            screen.blit(score_msg, (WIDTH//2 - 100, 300))
            screen.blit(cont_msg, (WIDTH//2 - 150, 400))

        elif current_state == STATE_GAMEOVER:
            over_text = title_font.render("GAME OVER", True, RED)
            score_msg = font.render(f"Final Score: {score}", True, WHITE)
            retry_msg = font.render("Press R to Restart", True, WHITE)
            screen.blit(over_text, (WIDTH//2 - 150, 200))
            screen.blit(score_msg, (WIDTH//2 - 100, 300))
            screen.blit(retry_msg, (WIDTH//2 - 100, 400))

        pygame.display.flip()
        
        # Crucial for Web Assembly loop
        await asyncio.sleep(0)

if __name__ == "__main__":
    asyncio.run(main())
