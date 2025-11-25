import asyncio
import pygame
import random
import math

# --- CONFIGURATION ---
WIDTH, HEIGHT = 800, 600
FPS = 60

# --- GIANT MAZE SETTINGS (100x100) ---
TILE_SIZE = 40          
COLS = 100              
ROWS = 100              

# --- COLORS ---
FLOOR_COLOR = (230, 140, 60)   
WALL_TOP = (30, 80, 220)       
WALL_SIDE = (20, 50, 150)      
WHITE = (255, 255, 255)
GREEN = (50, 205, 50)          
RED = (220, 20, 60)            
GOLD = (255, 215, 0)           

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

# --- MAZE GENERATOR (Recursive Backtracker) ---
def generate_maze_grid(cols, rows):
    grid = [[1 for _ in range(cols)] for _ in range(rows)]
    start_x, start_y = 1, 1
    grid[start_y][start_x] = 0
    stack = [(start_x, start_y)]
    
    while stack:
        cx, cy = stack[-1]
        directions = [(0, -2), (0, 2), (-2, 0), (2, 0)]
        random.shuffle(directions)
        
        carved = False
        for dx, dy in directions:
            nx, ny = cx + dx, cy + dy
            if 1 <= nx < cols-1 and 1 <= ny < rows-1 and grid[ny][nx] == 1:
                grid[cy + dy // 2][cx + dx // 2] = 0 
                grid[ny][nx] = 0 
                stack.append((nx, ny)) 
                carved = True
                break
        if not carved: stack.pop() 

    grid[rows-2][cols-2] = 0
    grid[rows-2][cols-3] = 0
    return grid

# --- CAMERA SYSTEM ---
class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        x = -target.rect.centerx + int(WIDTH / 2)
        y = -target.rect.centery + int(HEIGHT / 2)
        x = min(0, x) 
        y = min(0, y) 
        x = max(-(self.width - WIDTH), x) 
        y = max(-(self.height - HEIGHT), y) 
        self.camera = pygame.Rect(x, y, self.width, self.height)

# --- TOUCH BUTTONS ---
class TouchButton:
    def __init__(self, x, y, w, h, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = WHITE
        
    def draw(self, screen):
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
    def __init__(self, name, gender, x, y, current_level):
        super().__init__()
        # INTEGRATED LOGIC: Speed increases with Level
        self.base_speed = 5 + (current_level * 0.1) 
        self.speed = self.base_speed
        self.name = name
        
        if gender == 'Male': self.image_original = load_image("boy.png", (0,0,255), (30, 30))
        else: self.image_original = load_image("girl.png", (255,100,100), (30, 30))
        self.image = self.image_original.copy()
        
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.lives = 3
        self.boost_timer = 0
        self.visible = True

        # Name Tag
        font = pygame.font.SysFont("Arial", 14, bold=True)
        text_surf = font.render(name, True, WHITE)
        self.name_tag = pygame.Surface((text_surf.get_width() + 6, text_surf.get_height() + 4))
        self.name_tag.fill((0, 0, 0))
        self.name_tag.set_alpha(150)
        self.name_tag.blit(text_surf, (3, 2))
        
    def update(self, keys, walls, touch_inputs):
        dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a] or touch_inputs['left']: dx = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d] or touch_inputs['right']: dx = self.speed
        
        self.rect.x += dx
        hit_list = pygame.sprite.spritecollide(self, walls, False)
        for wall in hit_list:
            if dx > 0: self.rect.right = wall.rect.left
            elif dx < 0: self.rect.left = wall.rect.right

        dy = 0
        if keys[pygame.K_UP] or keys[pygame.K_w] or touch_inputs['up']: dy = -self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s] or touch_inputs['down']: dy = self.speed
        
        self.rect.y += dy
        hit_list = pygame.sprite.spritecollide(self, walls, False)
        for wall in hit_list:
            if dy > 0: self.rect.bottom = wall.rect.top
            elif dy < 0: self.rect.top = wall.rect.bottom

        if self.boost_timer > 0: self.boost_timer -= 1
        else: self.speed = self.base_speed

    def boost(self):
        self.speed = 9
        self.boost_timer = 180 
        
    def toggle_visibility(self):
        if self.visible: self.image.set_alpha(0); self.visible = False
        else: self.image.set_alpha(255); self.visible = True
    def make_visible(self):
        self.image.set_alpha(255); self.visible = True

class Enemy(pygame.sprite.Sprite):
    def __init__(self, current_level):
        super().__init__()
        self.image = load_image("hod.png", RED, (32, 32))
        self.rect = self.image.get_rect()
        
        # INTEGRATED LOGIC: Enemy Speed Scaling
        self.speed = 3.0 + (current_level * 0.08)
        # Ensure enemy is never faster than player base speed
        if self.speed >= 4.8: self.speed = 4.8
        
    def update(self, player_rect, walls):
        dx, dy = 0, 0
        if self.rect.x < player_rect.x: dx = self.speed
        if self.rect.x > player_rect.x: dx = -self.speed
        self.rect.x += dx
        if pygame.sprite.spritecollide(self, walls, False): self.rect.x -= dx

        if self.rect.y < player_rect.y: dy = self.speed
        if self.rect.y > player_rect.y: dy = -self.speed
        self.rect.y += dy
        if pygame.sprite.spritecollide(self, walls, False): self.rect.y -= dy

class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # 3D Wall Effect
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(WALL_SIDE)
        top_rect = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE - 10)
        pygame.draw.rect(self.image, WALL_TOP, top_rect)
        pygame.draw.line(self.image, (100, 150, 255), (0,0), (TILE_SIZE, 0), 2)
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
        pygame.draw.rect(self.image, (200, 180, 0), (2,2,36,36), 2)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

# --- MAIN GAME ---
async def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Campus Maze: Web Edition")
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
    player_name = "" 
    hit_timer = 0 
    
    camera = Camera(COLS * TILE_SIZE, ROWS * TILE_SIZE)
    
    sprites = pygame.sprite.Group()
    walls = pygame.sprite.Group()
    notes = pygame.sprite.Group()
    enemy_grp = pygame.sprite.Group()
    
    player = None
    hod = None
    gate = None
    start_pos = (0,0)
    hod_start_pos = (0,0)

    def build_level(lvl):
        sprites.empty(); walls.empty(); notes.empty(); enemy_grp.empty()
        
        # GENERATE MAZE (Recursive Backtracker)
        maze_data = generate_maze_grid(COLS, ROWS)
        spawn_points = []
        
        for r in range(ROWS):
            for c in range(COLS):
                x = c * TILE_SIZE
                y = r * TILE_SIZE
                if maze_data[r][c] == 1:
                    w = Wall(x, y)
                    walls.add(w)
                    sprites.add(w)
                else:
                    spawn_points.append((x, y))
        
        nonlocal player, hod, gate, start_pos, hod_start_pos
        
        start_pos = spawn_points[0]
        # PASS LEVEL to Player for Speed Scaling
        player = Player(player_name if player_name else "Player", gender, start_pos[0] + 6, start_pos[1] + 6, lvl)
        sprites.add(player)
        
        end_pos = spawn_points[-1]
        gate = Gate(end_pos[0], end_pos[1])
        sprites.add(gate)
        
        hod_start_pos = spawn_points[len(spawn_points)//2]
        # PASS LEVEL to Enemy for Speed Scaling
        hod = Enemy(lvl)
        hod.rect.topleft = hod_start_pos
        enemy_grp.add(hod)
        sprites.add(hod)
        
        for _ in range(20 + lvl):
            pos = random.choice(spawn_points)
            n = Note(pos[0], pos[1])
            notes.add(n)
            sprites.add(n)

    running = True
    while running:
        screen.fill(FLOOR_COLOR)
        
        t_in = {'up': btn_up.is_pressed(), 'down': btn_down.is_pressed(), 
                'left': btn_left.is_pressed(), 'right': btn_right.is_pressed()}

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            
            if state == "LOGIN":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN: 
                        build_level(level); state = "PLAY"
                    elif event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]
                    elif event.key == pygame.K_m: gender = "Male" 
                    elif event.key == pygame.K_f: gender = "Female" 
                    else:
                        if len(player_name) < 10 and event.unicode.isalnum():
                            player_name += event.unicode

                if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pos()[1] < 350:
                     gender = "Female" if gender == "Male" else "Male"
                if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pos()[1] > 350:
                     build_level(level); state = "PLAY"

            elif state == "GAMEOVER":
                if (event.type == pygame.KEYDOWN and event.key == pygame.K_r) or event.type == pygame.MOUSEBUTTONDOWN:
                    level = 1; score = 0; state = "LOGIN"

        if state == "LOGIN":
            title = big_font.render("CAMPUS MAZE", True, WHITE)
            name_box = font.render(f"Name: {player_name}_", True, GOLD)
            gender_txt = font.render(f"Char: {gender} (Tap Switch)", True, WALL_TOP)
            start = font.render("Tap HERE to Start", True, WHITE)
            
            pygame.draw.rect(screen, WALL_SIDE, (WIDTH//2 - 220, 150, 440, 320))
            pygame.draw.rect(screen, WALL_TOP, (WIDTH//2 - 220, 150, 440, 320), 5)
            
            screen.blit(title, (WIDTH//2 - 160, 180))
            screen.blit(name_box, (WIDTH//2 - 100, 260))
            screen.blit(gender_txt, (WIDTH//2 - 140, 320))
            screen.blit(start, (WIDTH//2 - 180, 400))
            
        elif state == "PLAY":
            player.update(pygame.key.get_pressed(), walls, t_in)
            hod.update(player.rect, walls)
            camera.update(player)
            
            if pygame.sprite.spritecollide(player, notes, True):
                score += 100
                player.boost()
            if pygame.sprite.spritecollide(player, enemy_grp, False):
                player.lives -= 1
                state = "HIT"; hit_timer = 60
            if pygame.sprite.collide_rect(player, gate):
                # INTEGRATED LOGIC: Score +1000
                level += 1; score += 1000; build_level(level)

            for sprite in sprites:
                offset_rect = camera.apply(sprite)
                if screen.get_rect().colliderect(offset_rect):
                    screen.blit(sprite.image, offset_rect)
                    if sprite == player and player.visible:
                        tag_x = offset_rect.centerx - player.name_tag.get_width() // 2
                        tag_y = offset_rect.top - 20
                        screen.blit(player.name_tag, (tag_x, tag_y))
            
            for btn in buttons: btn.draw(screen)
            hud = font.render(f"Score: {score} | Lvl: {level} | Lives: {player.lives}", True, WHITE)
            screen.blit(hud, (20, 5))

        elif state == "HIT":
            hit_timer -= 1
            if hit_timer % 10 == 0: player.toggle_visibility()
            for sprite in sprites:
                offset_rect = camera.apply(sprite)
                if screen.get_rect().colliderect(offset_rect):
                    screen.blit(sprite.image, offset_rect)
                    if sprite == player and player.visible:
                        tag_x = offset_rect.centerx - player.name_tag.get_width() // 2
                        tag_y = offset_rect.top - 20
                        screen.blit(player.name_tag, (tag_x, tag_y))
            
            if hit_timer <= 0:
                player.make_visible()
                if player.lives <= 0: state = "GAMEOVER"
                else:
                    player.rect.topleft = (start_pos[0]+6, start_pos[1]+6)
                    hod.rect.topleft = hod_start_pos
                    state = "PLAY"
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
