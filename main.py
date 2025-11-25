import asyncio
import pygame
import random

# --- CONFIGURATION ---
WIDTH, HEIGHT = 800, 600
TILE_SIZE = 40 
FPS = 60

# COLORS - MATCHING THE 3D TOY MAZE IMAGE
FLOOR_COLOR = (230, 140, 60)   # Orange/Peach floor
WALL_TOP = (30, 60, 200)       # Bright Blue (Top of wall)
WALL_SIDE = (20, 40, 140)      # Darker Blue (Side of wall - creates 3D effect)
WHITE = (255, 255, 255)
GREEN = (50, 205, 50)          # Notes
RED = (220, 20, 60)            # HOD
GOLD = (255, 215, 0)           # Gate

# --- ASSET LOADER ---
def load_image(filename, fallback_color, size):
    try:
        path = f"assets/{filename}"
        img = pygame.image.load(path)
        return pygame.transform.scale(img, size)
    except:
        surf = pygame.Surface(size)
        surf.fill(fallback_color)
        return surf

# --- MAZE GENERATOR (RECURSIVE BACKTRACKER) ---
# This creates the "Bunny Maze" / "Long Corridor" style
def generate_maze_grid(cols, rows):
    # 1. Start with a grid full of walls (1)
    grid = [[1 for _ in range(cols)] for _ in range(rows)]
    
    def carve(cx, cy):
        # Directions: Up, Down, Left, Right (Jump 2 steps to leave walls)
        directions = [(0, -2), (0, 2), (-2, 0), (2, 0)]
        random.shuffle(directions) 
        
        for dx, dy in directions:
            nx, ny = cx + dx, cy + dy
            
            # Check if neighbor is within bounds and is a Wall
            if 1 <= nx < cols-1 and 1 <= ny < rows-1 and grid[ny][nx] == 1:
                # Knock down the wall between current and neighbor
                grid[cy + dy // 2][cx + dx // 2] = 0
                grid[ny][nx] = 0 # Mark neighbor as path
                carve(nx, ny) # Recursive call

    # Start carving from (1, 1)
    grid[1][1] = 0
    carve(1, 1)
    
    # Ensure Gate area is open
    grid[rows-2][cols-2] = 0
    grid[rows-2][cols-3] = 0
    
    return grid

# --- TOUCH CONTROLS ---
class TouchButton:
    def __init__(self, x, y, w, h, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = WHITE
        
    def draw(self, screen):
        # Draw transparent button
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        s.fill((255, 255, 255, 50)) 
        screen.blit(s, self.rect.topleft)
        pygame.draw.rect(screen, self.color, self.rect, 2)
        
        font = pygame.font.SysFont("Arial", 30)
        txt = font.render(self.text, True, self.color)
        screen.blit(txt, (self.rect.centerx - txt.get_width()//2, self.rect.centery - txt.get_height()//2))

    def is_pressed(self):
        if pygame.mouse.get_pressed()[0]:
            mx, my = pygame.mouse.get_pos()
            if self.rect.collidepoint(mx, my): return True
        return False

# --- CLASSES ---
class Player(pygame.sprite.Sprite):
    def __init__(self, gender, x, y):
        super().__init__()
        self.base_speed = 4
        self.speed = self.base_speed
        
        # Load small sprites to fit in maze
        if gender == 'Male': self.image = load_image("boy.png", (0,0,255), (28, 28))
        else: self.image = load_image("girl.png", (255,100,100), (28, 28))
            
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.lives = 3
        self.boost_timer = 0
        self.gender = gender # Store for restart
        
    def update(self, keys, walls, touch_inputs):
        # MOVE X
        dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a] or touch_inputs['left']: dx = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d] or touch_inputs['right']: dx = self.speed
        
        self.rect.x += dx
        # Slide against wall X
        hit_list = pygame.sprite.spritecollide(self, walls, False)
        for wall in hit_list:
            if dx > 0: self.rect.right = wall.rect.left
            elif dx < 0: self.rect.left = wall.rect.right

        # MOVE Y
        dy = 0
        if keys[pygame.K_UP] or keys[pygame.K_w] or touch_inputs['up']: dy = -self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s] or touch_inputs['down']: dy = self.speed
        
        self.rect.y += dy
        # Slide against wall Y
        hit_list = pygame.sprite.spritecollide(self, walls, False)
        for wall in hit_list:
            if dy > 0: self.rect.bottom = wall.rect.top
            elif dy < 0: self.rect.top = wall.rect.bottom

        # Speed Boost Timer
        if self.boost_timer > 0: self.boost_timer -= 1
        else: self.speed = self.base_speed

    def boost(self):
        self.speed = 6
        self.boost_timer = 180 

class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = load_image("hod.png", RED, (30, 30))
        self.rect = self.image.get_rect()
        self.rect.topleft = (0, 0)
        self.speed = 3 # CONSTANT SPEED
        
    def update(self, player_rect, walls):
        # Smart Chase with Sliding
        dx = 0
        if self.rect.x < player_rect.x: dx = self.speed
        if self.rect.x > player_rect.x: dx = -self.speed
        
        self.rect.x += dx
        if pygame.sprite.spritecollide(self, walls, False): self.rect.x -= dx

        dy = 0
        if self.rect.y < player_rect.y: dy = self.speed
        if self.rect.y > player_rect.y: dy = -self.speed
        
        self.rect.y += dy
        if pygame.sprite.spritecollide(self, walls, False): self.rect.y -= dy

class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Create a 3D looking wall using CODE (Drawing rectangles)
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        
        # 1. Draw the darker "Side" face
        self.image.fill(WALL_SIDE)
        
        # 2. Draw the lighter "Top" face (shifted up slightly)
        top_rect = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE - 8)
        pygame.draw.rect(self.image, WALL_TOP, top_rect)
        
        # 3. Add a highlight for extra 3D pop
        pygame.draw.line(self.image, (60, 90, 255), (0,0), (TILE_SIZE, 0), 2)
        
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

class Note(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = load_image("note.png", GREEN, (20, 20))
        self.rect = self.image.get_rect()
        self.rect.center = (x + TILE_SIZE//2, y + TILE_SIZE//2)

class Gate(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(GOLD)
        # Add "EXIT" text to gate
        pygame.draw.rect(self.image, (200, 180, 0), (2,2,36,36), 2)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

# --- MAIN GAME ---
async def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Campus Run 3D Maze")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 24)
    big_font = pygame.font.SysFont("Arial", 48)

    # Touch Buttons
    btn_size = 60; gap = 10
    sx, sy = WIDTH - 220, HEIGHT - 150
    btn_up = TouchButton(sx + btn_size + gap, sy, btn_size, btn_size, "^")
    btn_down = TouchButton(sx + btn_size + gap, sy + btn_size + gap, btn_size, btn_size, "v")
    btn_left = TouchButton(sx, sy + btn_size + gap, btn_size, btn_size, "<")
    btn_right = TouchButton(sx + (btn_size + gap)*2, sy + btn_size + gap, btn_size, btn_size, ">")
    buttons = [btn_up, btn_down, btn_left, btn_right]

    state = "LOGIN"
    level = 1
    score = 0
    gender = "Male"
    
    # Groups
    sprites = pygame.sprite.Group()
    walls = pygame.sprite.Group()
    notes = pygame.sprite.Group()
    enemy_grp = pygame.sprite.Group()
    
    player = None
    hod = None
    gate = None

    def build_level(lvl):
        sprites.empty()
        walls.empty()
        notes.empty()
        enemy_grp.empty()
        
        # 1. Generate the Maze Grid (The "Brain" of the maze)
        cols = WIDTH // TILE_SIZE
        rows = HEIGHT // TILE_SIZE
        maze_data = generate_maze_grid(cols, rows)
        
        spawn_points = []
        
        # 2. Build 3D Walls based on Grid
        for r in range(rows):
            for c in range(cols):
                x = c * TILE_SIZE
                y = r * TILE_SIZE
                
                if maze_data[r][c] == 1:
                    w = Wall(x, y)
                    walls.add(w)
                    sprites.add(w)
                else:
                    spawn_points.append((x, y))
        
        nonlocal player, hod, gate
        
        # Spawn Player at Start (Top Left)
        start_pos = spawn_points[0]
        player = Player(gender, start_pos[0] + 6, start_pos[1] + 6)
        sprites.add(player)
        
        # Spawn Gate at End (Bottom Right)
        end_pos = spawn_points[-1]
        gate = Gate(end_pos[0], end_pos[1])
        sprites.add(gate)
        
        # Spawn HOD in the Middle
        mid_index = len(spawn_points) // 2
        hod_pos = spawn_points[mid_index]
        hod = Enemy()
        hod.rect.topleft = hod_pos
        enemy_grp.add(hod)
        sprites.add(hod)
        
        # Spawn Notes Randomly
        for _ in range(5 + lvl):
            pos = random.choice(spawn_points)
            n = Note(pos[0], pos[1])
            notes.add(n)
            sprites.add(n)

    running = True
    while running:
        screen.fill(FLOOR_COLOR) # The Orange Floor
        
        # Touch Inputs
        t_in = {'up': btn_up.is_pressed(), 'down': btn_down.is_pressed(), 
                'left': btn_left.is_pressed(), 'right': btn_right.is_pressed()}

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            
            if state == "LOGIN":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN: build_level(level); state = "PLAY"
                    elif event.key == pygame.K_m: gender = "Male"
                    elif event.key == pygame.K_f: gender = "Female"
                # Touch Login
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if pygame.mouse.get_pos()[1] > 350: build_level(level); state = "PLAY"
                    else: gender = "Female" if gender == "Male" else "Male"

            elif state == "GAMEOVER":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    level = 1; score = 0; state = "LOGIN"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    level = 1; score = 0; state = "LOGIN"

        # --- DRAWING ---
        if state == "LOGIN":
            # Title Screen
            title = big_font.render("CAMPUS MAZE RUN", True, WHITE)
            sub = font.render(f"Tap to Switch: {gender}", True, WALL_TOP)
            start = font.render("Tap HERE to Start", True, WHITE)
            
            # Draw a box behind text
            pygame.draw.rect(screen, WALL_SIDE, (WIDTH//2 - 200, 150, 400, 300))
            pygame.draw.rect(screen, WALL_TOP, (WIDTH//2 - 200, 150, 400, 300), 5)
            
            screen.blit(title, (WIDTH//2 - 180, 200))
            screen.blit(sub, (WIDTH//2 - 100, 300))
            screen.blit(start, (WIDTH//2 - 100, 380))
            
        elif state == "PLAY":
            player.update(pygame.key.get_pressed(), walls, t_in)
            hod.update(player.rect, walls)
            
            # Collisions
            if pygame.sprite.spritecollide(player, notes, True):
                score += 100
                player.boost()
                
            if pygame.sprite.spritecollide(player, enemy_grp, False):
                player.lives -= 1
                player.rect.topleft = (45, 45) # Reset Player
                hod.rect.topleft = (WIDTH//2, HEIGHT//2) # Reset Enemy
                if player.lives <= 0: state = "GAMEOVER"
                
            if pygame.sprite.collide_rect(player, gate):
                level += 1
                score += 500
                build_level(level)

            sprites.draw(screen) # Draws walls, player, hod
            
            # Draw Buttons
            for btn in buttons: btn.draw(screen)
            
            # HUD
            hud_bg = pygame.Surface((WIDTH, 40))
            hud_bg.fill((0,0,0))
            hud_bg.set_alpha(150)
            screen.blit(hud_bg, (0,0))
            hud = font.render(f"Score: {score} | Lvl: {level} | Lives: {player.lives}", True, WHITE)
            screen.blit(hud, (20, 5))

        elif state == "GAMEOVER":
            pygame.draw.rect(screen, (0,0,0), (WIDTH//2 - 150, 200, 300, 200))
            t1 = big_font.render("GAME OVER", True, RED)
            t2 = font.render("Tap to Restart", True, WHITE)
            screen.blit(t1, (WIDTH//2 - 120, 250))
            screen.blit(t2, (WIDTH//2 - 80, 320))

        pygame.display.flip()
        await asyncio.sleep(0)

if __name__ == "__main__":
    asyncio.run(main())
