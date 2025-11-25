import pygame
import sys

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Maze Runner - HOD Chase")
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255)
RED = (200, 30, 30)
GREEN = (0, 200, 0)

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = 4

    def update(self, keys, walls):
        dx = dy = 0
        if keys[pygame.K_UP]: dy = -self.speed
        if keys[pygame.K_DOWN]: dy = self.speed
        if keys[pygame.K_LEFT]: dx = -self.speed
        if keys[pygame.K_RIGHT]: dx = self.speed

        self.rect.x += dx
        for w in walls:
            if self.rect.colliderect(w.rect):
                self.rect.x -= dx

        self.rect.y += dy
        for w in walls:
            if self.rect.colliderect(w.rect):
                self.rect.y -= dy

# HOD Enemy class
class HOD(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(RED)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = 2  # Slower than player

    def update(self, target_rect, walls):
        if self.rect.x < target_rect.x: self.rect.x += self.speed
        elif self.rect.x > target_rect.x: self.rect.x -= self.speed

        for w in walls:
            if self.rect.colliderect(w.rect):
                if self.rect.x < target_rect.x: self.rect.x -= self.speed
                else: self.rect.x += self.speed

        if self.rect.y < target_rect.y: self.rect.y += self.speed
        elif self.rect.y > target_rect.y: self.rect.y -= self.speed

        for w in walls:
            if self.rect.colliderect(w.rect):
                if self.rect.y < target_rect.y: self.rect.y -= self.speed
                else: self.rect.y += self.speed

# Wall class
class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(BLACK)
        self.rect = self.image.get_rect(topleft=(x, y))

# Maze layout (placeholder; add more walls as needed)
walls = pygame.sprite.Group()
walls.add(Wall(0, 0, WIDTH, 20))
walls.add(Wall(0, HEIGHT-20, WIDTH, 20))
walls.add(Wall(0, 0, 20, HEIGHT))
walls.add(Wall(WIDTH-20, 0, 20, HEIGHT))

# Player, HOD, Gate\player = Player(50, 50)
hod = HOD(700, 500)
gate = pygame.Rect(WIDTH-80, HEIGHT//2 - 25, 60, 50)

# Main loop (NO asyncio here)
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()
    player.update(keys, walls)
    hod.update(player.rect, walls)

    if player.rect.colliderect(hod.rect):
        print("Caught by HOD!")
        pygame.quit()
        sys.exit()

    if player.rect.colliderect(gate):
        print("Reached the Gate!")
        pygame.quit()
        sys.exit()

    screen.fill(WHITE)

    for w in walls:
        screen.blit(w.image, w.rect)

    screen.blit(player.image, player.rect)
    screen.blit(hod.image, hod.rect)
    pygame.draw.rect(screen, GREEN, gate)

    pygame.display.update()
    clock.tick(60)
