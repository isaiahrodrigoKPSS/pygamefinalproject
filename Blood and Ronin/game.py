import pygame
from pygame import mixer

mixer.init()
pygame.init()

# tutorial by "Coding With Russ" on YT - https://youtu.be/s5bd9KMSSW4?si=gdchO-R7S70nHOEz

# create game window
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Blood and Ronin")

# set framerate
clock = pygame.time.Clock()
FPS = 60

# define colours
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)

# define game variables
intro_count = 3
last_count_update = pygame.time.get_ticks()
score = [0, 0]
round_over = False
ROUND_OVER_COOLDOWN = 2000

# define fighter variables
RONIN1_SIZE = 200 #hitbox
RONIN1_SCALE = 2.5 #visual size
RONIN1_OFFSET = [96, 36] #position
RONIN1_DATA = [RONIN1_SIZE, RONIN1_SCALE, RONIN1_OFFSET]
 
RONIN2_SIZE = 200
RONIN2_SCALE = 2.5
RONIN2_OFFSET = [72, 42]
RONIN2_DATA = [RONIN2_SIZE, RONIN2_SCALE, RONIN2_OFFSET]

# load music and sounds
pygame.mixer.music.load("assets/audio/music.mp3")
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1, 0.0, 5000)
sword_fx = pygame.mixer.Sound("assets/audio/sword.wav")
sword_fx.set_volume(0.2)

# load background
gif_bg = pygame.image.load("assets/images/background/background.png").convert_alpha()

# function that draws text
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

# function that draws the background
def draw_bg():
    scaled_bg = pygame.transform.scale(gif_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.blit(scaled_bg, (0, 0))

# function that draws the hp bar
def draw_health_bar(health, x, y):
    ratio = health / 100
    pygame.draw.rect(screen, WHITE, (x - 2, y - 2, 404, 34))
    pygame.draw.rect(screen, RED, (x, y, 400, 30))
    pygame.draw.rect(screen, YELLOW, (x, y, 400 * ratio, 30))

# animation steps (idle, run, jump, attack1, attack2, hit, death; in that order)
RONIN1_ANIMATION_STEPS = [8, 8, 1, 6, 6, 4, 6]
RONIN2_ANIMATION_STEPS = [4, 8, 1, 4, 4, 3, 7]

# load sprites
ronin1_sheet = pygame.image.load("assets/images/ronin/player1.png").convert_alpha()
ronin2_sheet = pygame.image.load("assets/images/ronin/player2.png").convert_alpha()

# victory icon
victory_img = pygame.image.load("assets/images/icons/victory.png").convert_alpha()

# fonts
count_font = pygame.font.Font("assets/fonts/turok.ttf", 80)
score_font = pygame.font.Font("assets/fonts/turok.ttf", 30)


class Fighter():
    def __init__(self, player, x, y, flip, data, sprite_sheet, animation_steps, sound):
        #plyaer details
        self.player = player
        self.size = data[0]
        self.image_scale = data[1]
        self.offset = data[2]
        self.flip = flip
        # animation
        self.animation_list = self.load_images(sprite_sheet, animation_steps)
        self.action = 0
        self.frame_index = 0
        self.image = self.animation_list[self.action][self.frame_index]
        self.update_time = pygame.time.get_ticks()
        # position and movement
        self.rect = pygame.Rect((x, y, 80, 180))
        self.vel_y = 0
        self.running = False
        self.jump = False
        # combat
        self.attacking = False
        self.attack_type = 0
        self.attack_cooldown = 0
        self.attack_sound = sound
        self.hit = False
        self.health = 100
        self.alive = True
        # dodge (unique feature)
        self.dodge_active = False
        self.dodge_cooldown = 0
        self.dodge_timer = 0

    # loads and divides the spritesheet into individual frames
    def load_images(self, sprite_sheet, animation_steps):
        animation_list = []
        for y, frames in enumerate(animation_steps):
            temp_img_list = []
            for x in range(frames):
                temp_img = sprite_sheet.subsurface(x * self.size, y * self.size, self.size, self.size)
                temp_img = pygame.transform.scale(temp_img, (self.size * self.image_scale, self.size * self.image_scale))
                temp_img_list.append(temp_img)
            animation_list.append(temp_img_list)
        return animation_list

    # handles movement, jumping, dodging, and attacking
    def move(self, screen_width, screen_height, surface, target, round_over):
        SPEED = 12
        GRAVITY = 2
        dx = 0
        dy = 0
        self.running = False
        self.attack_type = 0
        key = pygame.key.get_pressed()

        if not self.attacking and self.alive and not round_over:
            # p1 controsl
            if self.player == 1:
                if key[pygame.K_a]:
                    dx = -SPEED
                    self.running = True
                if key[pygame.K_d]:
                    dx = SPEED
                    self.running = True
                if key[pygame.K_w] and not self.jump:
                    self.vel_y = -30
                    self.jump = True
                if key[pygame.K_q]:
                    self.attack(target)
                    self.attack_type = 1
                if key[pygame.K_e]:
                    self.attack(target)
                    self.attack_type = 2
                if key[pygame.K_s] and self.dodge_cooldown == 0:
                    self.dodge_active = True
                    self.dodge_timer = 15
                    self.dodge_cooldown = 45
            # p2 controls
            if self.player == 2:
                if key[pygame.K_j]:
                    dx = -SPEED
                    self.running = True
                if key[pygame.K_l]:
                    dx = SPEED
                    self.running = True
                if key[pygame.K_i] and not self.jump:
                    self.vel_y = -30
                    self.jump = True
                if key[pygame.K_u]:
                    self.attack(target)
                    self.attack_type = 1
                if key[pygame.K_o]:
                    self.attack(target)
                    self.attack_type = 2
                if key[pygame.K_k] and self.dodge_cooldown == 0:
                    self.dodge_active = True
                    self.dodge_timer = 15
                    self.dodge_cooldown = 45

        #applies gravity
        self.vel_y += GRAVITY
        dy += self.vel_y

        # game boundaries
        if self.rect.left + dx < 0:
            dx = -self.rect.left
        if self.rect.right + dx > screen_width:
            dx = screen_width - self.rect.right
        if self.rect.bottom + dy > screen_height - 110:
            self.vel_y = 0
            self.jump = False
            dy = screen_height - 110 - self.rect.bottom
        # flip ronin based on target position
        if target.rect.centerx > self.rect.centerx:
            self.flip = False
        else:
            self.flip = True

        # cooldowns for dodge and attacks
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if self.dodge_cooldown > 0:
            self.dodge_cooldown -= 1
        if self.dodge_active:
            self.dodge_timer -= 1
            if self.dodge_timer <= 0:
                self.dodge_active = False
        # position updates
        self.rect.x += dx
        self.rect.y += dy
    # animation updates
    def update(self):
        if self.health <= 0:
            self.alive = False
            self.update_action(6)
        elif self.hit:
            self.update_action(5)
            if self.frame_index == len(self.animation_list[5]) - 1:
                self.hit = False
        elif self.attacking:
            if self.attack_type == 1:
                self.update_action(3)
            elif self.attack_type == 2:
                self.update_action(4)
        elif self.jump:
            self.update_action(2)
        elif self.running:
            self.update_action(1)
        else:
            self.update_action(0)

        # frame change timing
        animation_cooldown = 50
        self.image = self.animation_list[self.action][self.frame_index]
        if pygame.time.get_ticks() - self.update_time > animation_cooldown:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()
        if self.frame_index >= len(self.animation_list[self.action]):
            if not self.alive:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0
                if self.action in [3, 4, 5]:
                    self.attacking = False
                    self.attack_cooldown = 20

    # attack method
    def attack(self, target):
        if self.attack_cooldown == 0 and not self.hit:
            self.attacking = True
            self.attack_sound.play()
            # attack range
            attacking_rect = pygame.Rect(self.rect.centerx - (2 * self.rect.width * self.flip), self.rect.y, 2 * self.rect.width, self.rect.height)
            if attacking_rect.colliderect(target.rect):
                if not target.dodge_active and not target.hit:
                    # p1 gets slightly more damage to compensate for slightly longer anims
                    damage = 12 if self.player == 1 else 10
                    target.health -= damage
                    target.hit = True

    # change animation state
    def update_action(self, new_action):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    # draw fighters on screen
    def draw(self, surface):
        img = pygame.transform.flip(self.image, self.flip, False)
        if self.dodge_active:
            white_img = img.copy()
            white_img.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_ADD)
            surface.blit(white_img, (self.rect.x - (self.offset[0] * self.image_scale), self.rect.y - (self.offset[1] * self.image_scale)))
        else:
            surface.blit(img, (self.rect.x - (self.offset[0] * self.image_scale), self.rect.y - (self.offset[1] * self.image_scale)))

# create fighters
fighter_1 = Fighter(1, 200, 310, False, RONIN1_DATA, ronin1_sheet, RONIN1_ANIMATION_STEPS, sword_fx)
fighter_2 = Fighter(2, 700, 310, True, RONIN2_DATA, ronin2_sheet, RONIN2_ANIMATION_STEPS, sword_fx)

# main loop
run = True
while run:
    clock.tick(FPS)
    draw_bg()
    draw_health_bar(fighter_1.health, 20, 20) # draws p1 hp
    draw_health_bar(fighter_2.health, 580, 20) # draws p2 hp
    draw_text("P1: " + str(score[0]), score_font, WHITE, 20, 60) # draws p1 scroe
    draw_text("P2: " + str(score[1]), score_font, WHITE, 925, 60) # draws p2 score

    if intro_count <= 0:
        # lets them move if countdown is over
        fighter_1.move(SCREEN_WIDTH, SCREEN_HEIGHT, screen, fighter_2, round_over)
        fighter_2.move(SCREEN_WIDTH, SCREEN_HEIGHT, screen, fighter_1, round_over)
    else:
        # shows countdown text before round starts
        draw_text(str(intro_count), count_font, RED, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3)
        # reduce countdown every second
        if (pygame.time.get_ticks() - last_count_update) >= 1000:
            intro_count -= 1
            last_count_update = pygame.time.get_ticks()

    # update fighters (animations, state changes)
    fighter_1.update()
    fighter_2.update()
     # draw fighters on screen
    fighter_1.draw(screen)
    fighter_2.draw(screen)

    # check for KO and end round
    if not round_over:
        if not fighter_1.alive:
            score[1] += 1 # p2 gets point
            round_over = True
            round_over_time = pygame.time.get_ticks()
        elif not fighter_2.alive:
            score[0] += 1 # p1 gets point
            round_over = True
            round_over_time = pygame.time.get_ticks()
    else:
        # shows victory image
        screen.blit(victory_img, (360, 150))
        # reset after cooldown ends
        if pygame.time.get_ticks() - round_over_time > ROUND_OVER_COOLDOWN:
            round_over = False
            intro_count = 3 # restarts countdown
            # reset fighters
            fighter_1 = Fighter(1, 200, 310, False, RONIN1_DATA, ronin1_sheet, RONIN1_ANIMATION_STEPS, sword_fx)
            fighter_2 = Fighter(2, 700, 310, True, RONIN2_DATA, ronin2_sheet, RONIN2_ANIMATION_STEPS, sword_fx)

    # check for quit event
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update() # updates display

pygame.quit()
