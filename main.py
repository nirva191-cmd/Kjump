import pygame
import random
import json
import os
import numpy as np

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1)

sound_muted = False

def generate_retro_sound(freq, duration, sound_type="square"):
    sample_rate = 22050
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    if sound_type == "square":
        wave = np.sign(np.sin(2 * np.pi * freq * t))
    elif sound_type == "noise":
        wave = np.random.uniform(-1, 1, len(t))
    else:
        wave = np.sin(2 * np.pi * freq * t)
        
    envelope = np.linspace(1, 0, len(wave))
    audio = (wave * envelope * 32767).astype(np.int16)
    return pygame.mixer.Sound(buffer=audio)

def play_sound(snd):
    if not sound_muted:
        snd.play()

def generate_bg_music(level_num):
    sample_rate = 22050
    
    if level_num <= 5:
        notes = [261.63, 293.66, 329.63, 392.00, 440.00]
        note_duration = 0.45
    elif level_num <= 15:
        notes = [220.00, 246.94, 293.66, 329.63, 370.00]
        note_duration = 0.5
    else:
        notes = [196.00, 220.00, 261.63, 329.63, 392.00]
        note_duration = 0.6
        
    melody = [random.choice(notes) for _ in range(12)]
    
    song_data = []
    for freq in melody:
        t = np.linspace(0, note_duration, int(sample_rate * note_duration), endpoint=False)
        wave = np.sin(2 * np.pi * freq * t) * 0.12
        envelope = np.linspace(1, 0, len(wave))
        note_audio = (wave * envelope * 32767).astype(np.int16)
        song_data.append(note_audio)
        
    full_audio = np.concatenate(song_data)
    return pygame.mixer.Sound(buffer=full_audio)

sound_jump = generate_retro_sound(440, 0.1, "square")
sound_shoot = generate_retro_sound(880, 0.08, "square")
sound_heart = generate_retro_sound(650, 0.15, "square")
sound_hit = generate_retro_sound(150, 0.2, "noise")
sound_pause = generate_retro_sound(520, 0.05, "square")

current_bg_level = 1
background_music = generate_bg_music(current_bg_level)
music_channel = pygame.mixer.Channel(0)

WIDTH = 720
HEIGHT = 1500
GAME_H = 1100

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Platform Jump - 100 Mundos del Espacio")

clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 40)
small_font = pygame.font.SysFont(None, 26)
big_font = pygame.font.SysFont(None, 48)

BROWN = (165, 88, 29)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GREEN = (0, 180, 70)
BLUE = (40, 90, 255)
SKIN = (235, 205, 170)
ORANGE = (255, 140, 0)
YELLOW = (255, 220, 0)
PURPLE = (160, 80, 220)
RED = (220, 40, 40)
CYAN = (0, 220, 220)
GOLD = (255, 215, 0)
MAGENTA = (255, 0, 128)
GRAY = (120, 120, 120)
ICE_BLUE = (150, 220, 255)

COLOR_OPTIONS = [
    ("Verde", GREEN), ("Azul", BLUE), ("Rojo", RED), ("Amarillo", YELLOW), 
    ("Naranja", ORANGE), ("Morado", PURPLE), ("Cian", CYAN), ("Magenta", MAGENTA),
    ("Blanco", WHITE), ("Gris", GRAY), ("Rosa", (255, 105, 180)), 
    ("Lima", (50, 205, 50)), ("Marrón", (139, 69, 19)), ("Turquesa", (64, 224, 208)), 
    ("Oro", GOLD)
]

AVATAR_OPTIONS = ["hombre", "mujer", "dinosaurio", "perro", "gato", "monstruo"]

ACCESSORY_OPTIONS = [
    "ninguno", "lentes", "gorra", "corona", "capa", "antifaz", "casco", 
    "bufanda", "audífonos", "orejas", "moño", "alas", "halo", "collar", "bandana"
]

LEVEL_NAMES = [
    "Pradera Verde", "Lluvia Matutina", "Tormenta Eléctrica", "Bosque Otoñal", "Vientos de Invierno",
    "Deshielo Primaveral", "Atardecer Dorado", "Cielo Crepuscular", "Noche de Luciernagas", "Luna Llena",
    "Bóveda Celeste", "Capa de Ozono", "Estratosfera", "Aurora Boreal", "Viento Solar",
    "Estación Espacial", "Órbita Terrestre", "Mar de Estrellas", "Nebulosa Lejana", "Cúmulo Estelar"
]
while len(LEVEL_NAMES) < 100:
    LEVEL_NAMES.append(f"Sector Alfa-{len(LEVEL_NAMES)+1}")

STATE_MENU = 0
STATE_PLAYING = 1
STATE_PAUSED = 2
STATE_LOWER_WORLD = 3
STATE_GAMEOVER = 4
game_state = STATE_MENU

selected_avatar_idx = 0
selected_color_idx = 0
selected_acc_idx = 0
dropdown_open = None

LEVEL = 1
MAX_LEVELS = 100
PLATFORMS_TO_FINISH = 30
platforms_passed = 0
score = 0
ammo = 3
lives = 20

player = pygame.Rect(340, 800, 40, 55)
speed = 9.5
gravity = 0.55
jump_force = -17.5
vx = 0
vy = 0
on_ground = False
shield_active = False

cpu2 = pygame.Rect(200, 800, 40, 55)
cpu2_vx = 0
cpu2_vy = 0
cpu2_on_ground = False

left_zone = pygame.Rect(0, 1100, 180, 400)
right_zone = pygame.Rect(180, 1100, 180, 400)
jump_zone = pygame.Rect(360, 1100, 180, 400)
fire_zone = pygame.Rect(540, 1100, 180, 400)

pause_btn = pygame.Rect(520, 15, 80, 40)
mute_btn = pygame.Rect(610, 15, 90, 40)

left_pressed = False
right_pressed = False
jump_pressed = False
fire_pressed = False
active_fingers = {}

platforms = []
trampolines = []
items = []
spiders = []
projectiles = []
spaceships = []
save_message_timer = 0

def save_game():
    global save_message_timer
    data = {
        "level": LEVEL,
        "platforms_passed": platforms_passed,
        "score": score,
        "ammo": ammo,
        "lives": lives,
        "avatar": selected_avatar_idx,
        "color": selected_color_idx,
        "accessory": selected_acc_idx
    }
    try:
        with open("partida.json", "w") as f:
            json.dump(data, f)
        save_message_timer = 90
    except Exception as e:
        print("Error al guardar:", e)

def load_game():
    global LEVEL, platforms_passed, score, ammo, lives, selected_avatar_idx, selected_color_idx, selected_acc_idx, background_music, current_bg_level
    if os.path.exists("partida.json"):
        try:
            with open("partida.json", "r") as f:
                data = json.load(f)
                LEVEL = data.get("level", 1)
                platforms_passed = data.get("platforms_passed", 0)
                score = data.get("score", 0)
                ammo = data.get("ammo", 3)
                lives = data.get("lives", 20)
                selected_avatar_idx = data.get("avatar", 0)
                selected_color_idx = data.get("color", 0)
                selected_acc_idx = data.get("accessory", 0)
            current_bg_level = LEVEL
            background_music = generate_bg_music(LEVEL)
            return True
        except Exception as e:
            print("Error al cargar:", e)
    return False

def reset_game():
    global LEVEL, platforms_passed, score, ammo, lives, platforms, trampolines, items, spiders, projectiles, spaceships, player, cpu2, background_music, current_bg_level
    LEVEL = 1
    current_bg_level = 1
    background_music = generate_bg_music(LEVEL)
    platforms_passed = 0
    score = 0
    ammo = 3
    lives = 20
    player.x = 340
    player.y = 800
    cpu2.x = 200
    cpu2.y = 800
    platforms.clear()
    trampolines.clear()
    items.clear()
    spiders.clear()
    projectiles.clear()
    spaceships.clear()

    last_x = 300
    last_y = 900
    for i in range(12):
        p_type = "normal"
        r_val = random.randint(0, 100)
        if LEVEL % 3 == 0 and r_val < 30:
            p_type = "falling"
        elif LEVEL % 4 == 0 and r_val < 35:
            p_type = "slippery"
            
        p = {"rect": pygame.Rect(last_x, last_y, 130, 18), "type": p_type, "fall_timer": 0, "offset": random.uniform(0, 6.28)}
        platforms.append(p)
        
        if random.randint(0, 100) < 20:
            trampolines.append(pygame.Rect(last_x + 40, last_y - 12, 50, 12))
        if random.randint(0, 100) < 40:
            item_t = random.choices(
                ["escudo", "balas", "electricidad", "fuego", "hielo", "corazon"],
                weights=[15, 15, 10, 10, 10, 40],
                k=1
            )[0]
            items.append({"rect": pygame.Rect(last_x + 50, last_y - 32, 28, 28), "type": item_t})
        if random.randint(0, 100) < 18:
            spiders.append(pygame.Rect(last_x + 50, last_y - 25, 25, 25))

        if last_x < 300:
            last_x = random.randint(380, 520)
        else:
            last_x = random.randint(80, 240)
        last_y -= 95

reset_game()

environment_elements = []
for _ in range(25):
    environment_elements.append({
        "x": random.randint(0, WIDTH),
        "y": random.randint(0, GAME_H),
        "speed": random.uniform(1.0, 3.0),
        "type": random.choice(["rain", "star", "astronaut", "leaf"])
    })

level_banner_timer = 0
level_banner_text = ""

def evaluate_touches():
    global left_pressed, right_pressed, jump_pressed, fire_pressed
    prev_jump = jump_pressed
    left_pressed = False
    right_pressed = False
    jump_pressed = False
    fire_pressed = False

    for pos in active_fingers.values():
        tx, ty = pos
        if ty >= 1100:
            if left_zone.collidepoint(tx, ty): left_pressed = True
            if right_zone.collidepoint(tx, ty): right_pressed = True
            if jump_zone.collidepoint(tx, ty): jump_pressed = True
            if fire_zone.collidepoint(tx, ty): fire_pressed = True

    if jump_pressed and not prev_jump and game_state == STATE_PLAYING and on_ground:
        play_sound(sound_jump)

def draw_custom_character(surface, rect, avatar, color_tuple, accessory):
    cx, cy = rect.centerx, rect.y
    pygame.draw.circle(surface, SKIN, (cx, cy + 8), 10)
    pygame.draw.rect(surface, color_tuple, (rect.x + 10, rect.y + 18, 20, 22), border_radius=4)
    pygame.draw.line(surface, color_tuple, (rect.x + 10, cy + 22), (rect.x + 2, cy + 32), 4)
    pygame.draw.line(surface, color_tuple, (rect.x + 30, cy + 22), (rect.x + 38, cy + 32), 4)
    pygame.draw.line(surface, BLACK, (rect.x + 13, rect.y + 40), (rect.x + 13, rect.y + 53), 4)
    pygame.draw.line(surface, BLACK, (rect.x + 27, rect.y + 40), (rect.x + 27, rect.y + 53), 4)

    if avatar == "mujer":
        pygame.draw.polygon(surface, color_tuple, [(rect.x + 6, rect.y + 40), (rect.x + 34, rect.y + 40), (rect.x + 20, rect.y + 18)])
    elif avatar == "dinosaurio":
        pygame.draw.circle(surface, GREEN, (cx + 6, cy + 2), 6)
    elif avatar == "perro":
        pygame.draw.circle(surface, ORANGE, (cx - 8, cy + 2), 5)
        pygame.draw.circle(surface, ORANGE, (cx + 8, cy + 2), 5)
    elif avatar == "gato":
        pygame.draw.polygon(surface, PURPLE, [(cx - 8, cy), (cx - 12, cy - 8), (cx - 4, cy - 2)])
        pygame.draw.polygon(surface, PURPLE, [(cx + 8, cy), (cx + 12, cy - 8), (cx + 4, cy - 2)])
    elif avatar == "monstruo":
        pygame.draw.circle(surface, YELLOW, (cx - 4, cy + 6), 3)
        pygame.draw.circle(surface, YELLOW, (cx + 4, cy + 6), 3)
        pygame.draw.circle(surface, BLACK, (cx - 4, cy + 6), 1)
        pygame.draw.circle(surface, BLACK, (cx + 4, cy + 6), 1)

    if accessory == "lentes":
        pygame.draw.rect(surface, BLACK, (cx - 10, cy + 4, 20, 5), border_radius=2)
    elif accessory == "gorra":
        pygame.draw.rect(surface, RED, (rect.x + 8, cy - 2, 24, 5), border_radius=2)
    elif accessory == "corona":
        pygame.draw.polygon(surface, GOLD, [(cx - 8, cy - 2), (cx - 8, cy - 8), (cx, cy - 12), (cx + 8, cy - 8), (cx + 8, cy - 2)])
    elif accessory == "capa":
        pygame.draw.polygon(surface, RED, [(rect.x + 10, cy + 18), (rect.x - 4, cy + 42), (rect.x + 14, cy + 32)])
    elif accessory == "antifaz":
        pygame.draw.rect(surface, PURPLE, (cx - 12, cy + 4, 24, 7), border_radius=3)
    elif accessory == "casco":
        pygame.draw.arc(surface, CYAN, (cx - 12, cy - 4, 24, 24), 0, 3.14, 3)
    elif accessory == "bufanda":
        pygame.draw.rect(surface, ORANGE, (cx - 10, cy + 14, 20, 5), border_radius=2)
    elif accessory == "audífonos":
        pygame.draw.arc(surface, BLACK, (cx - 14, cy - 2, 28, 18), 0, 3.14, 3)
    elif accessory == "orejas":
        pygame.draw.circle(surface, color_tuple, (cx - 10, cy - 2), 5)
        pygame.draw.circle(surface, color_tuple, (cx + 10, cy - 2), 5)
    elif accessory == "moño":
        pygame.draw.polygon(surface, MAGENTA, [(cx, cy + 2), (cx - 8, cy - 4), (cx - 8, cy + 8)])
        pygame.draw.polygon(surface, MAGENTA, [(cx, cy + 2), (cx + 8, cy - 4), (cx + 8, cy + 8)])
    elif accessory == "alas":
        pygame.draw.ellipse(surface, WHITE, (rect.x - 10, cy + 12, 12, 20))
        pygame.draw.ellipse(surface, WHITE, (rect.x + 38, cy + 12, 12, 20))
    elif accessory == "halo":
        pygame.draw.ellipse(surface, YELLOW, (cx - 8, cy - 10, 16, 6), 2)
    elif accessory == "collar":
        pygame.draw.circle(surface, GOLD, (cx, cy + 18), 7, 2)
    elif accessory == "bandana":
        pygame.draw.rect(surface, BLUE, (cx - 12, cy + 2, 24, 4))

def get_level_spider_color(lvl):
    colors = [(50, 50, 50), (180, 40, 40), (40, 120, 220), (220, 140, 0), (140, 40, 220), (0, 180, 180)]
    return colors[(lvl - 1) % len(colors)]

running = True

while running:
    if LEVEL != current_bg_level:
        current_bg_level = LEVEL
        background_music = generate_bg_music(current_bg_level)
        music_channel.stop()

    if not music_channel.get_busy() and not sound_muted:
        music_channel.play(background_music)
    elif sound_muted and music_channel.get_busy():
        music_channel.stop()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.FINGERDOWN:
            x = int(event.x * WIDTH)
            y = int(event.y * HEIGHT)
            active_fingers[event.finger_id] = (x, y)

            if game_state == STATE_PLAYING and y < 1100:
                if pause_btn.collidepoint(x, y):
                    play_sound(sound_pause)
                    game_state = STATE_PAUSED
                elif mute_btn.collidepoint(x, y):
                    sound_muted = not sound_muted

            evaluate_touches()

            if game_state == STATE_MENU:
                clicked_inside = False
                if dropdown_open == "avatar":
                    for idx, _ in enumerate(AVATAR_OPTIONS):
                        r = pygame.Rect(160, 350 + idx * 45, 400, 40)
                        if r.collidepoint(x, y):
                            selected_avatar_idx = idx
                            clicked_inside = True
                            break
                    dropdown_open = None
                    if clicked_inside: continue
                elif dropdown_open == "color":
                    for idx, _ in enumerate(COLOR_OPTIONS):
                        r = pygame.Rect(160, 480 + idx * 45, 400, 40)
                        if r.collidepoint(x, y):
                            selected_color_idx = idx
                            clicked_inside = True
                            break
                    dropdown_open = None
                    if clicked_inside: continue
                elif dropdown_open == "accessory":
                    for idx, _ in enumerate(ACCESSORY_OPTIONS):
                        r = pygame.Rect(160, 610 + idx * 45, 400, 40)
                        if r.collidepoint(x, y):
                            selected_acc_idx = idx
                            clicked_inside = True
                            break
                    dropdown_open = None
                    if clicked_inside: continue

                if pygame.Rect(160, 300, 400, 45).collidepoint(x, y):
                    dropdown_open = "avatar"
                elif pygame.Rect(160, 430, 400, 45).collidepoint(x, y):
                    dropdown_open = "color"
                elif pygame.Rect(160, 560, 400, 45).collidepoint(x, y):
                    dropdown_open = "accessory"
                elif pygame.Rect(210, 1220, 300, 60).collidepoint(x, y):
                    if load_game():
                        active_fingers.clear()
                        evaluate_touches()
                        game_state = STATE_PLAYING
                elif pygame.Rect(210, 1300, 300, 60).collidepoint(x, y):
                    reset_game()
                    active_fingers.clear()
                    evaluate_touches()
                    game_state = STATE_PLAYING

            elif game_state == STATE_PAUSED:
                if pygame.Rect(210, 520, 300, 60).collidepoint(x, y):
                    game_state = STATE_PLAYING
                elif pygame.Rect(210, 600, 300, 60).collidepoint(x, y):
                    save_game()
                elif pygame.Rect(210, 680, 300, 60).collidepoint(x, y):
                    if load_game():
                        game_state = STATE_PLAYING
                elif pygame.Rect(210, 760, 300, 60).collidepoint(x, y):
                    game_state = STATE_MENU

            elif game_state == STATE_LOWER_WORLD:
                if pygame.Rect(210, 900, 300, 60).collidepoint(x, y):
                    game_state = STATE_PLAYING
                    player.y = 800
                    if platforms:
                        player.x = platforms[0]["rect"].centerx - 20
                        player.bottom = platforms[0]["rect"].top

            elif game_state == STATE_GAMEOVER:
                if pygame.Rect(210, 800, 300, 60).collidepoint(x, y):
                    reset_game()
                    game_state = STATE_PLAYING

            elif game_state == STATE_PLAYING and y >= 1100 and fire_zone.collidepoint(x, y):
                if ammo > 0:
                    ammo -= 1
                    projectiles.append(pygame.Rect(player.centerx - 5, player.y, 10, 16))
                    play_sound(sound_shoot)

        elif event.type == pygame.FINGERMOTION:
            if event.finger_id in active_fingers:
                x = int(event.x * WIDTH)
                y = int(event.y * HEIGHT)
                active_fingers[event.finger_id] = (x, y)
                evaluate_touches()

        elif event.type == pygame.FINGERUP:
            if event.finger_id in active_fingers:
                del active_fingers[event.finger_id]
            evaluate_touches()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            if game_state == STATE_MENU:
                if pygame.Rect(160, 300, 400, 45).collidepoint(x, y): dropdown_open = "avatar"
                elif pygame.Rect(160, 430, 400, 45).collidepoint(x, y): dropdown_open = "color"
                elif pygame.Rect(160, 560, 400, 45).collidepoint(x, y): dropdown_open = "accessory"
                elif pygame.Rect(210, 1220, 300, 60).collidepoint(x, y):
                    if load_game():
                        active_fingers.clear()
                        evaluate_touches()
                        game_state = STATE_PLAYING
                elif pygame.Rect(210, 1300, 300, 60).collidepoint(x, y):
                    reset_game()
                    active_fingers.clear()
                    evaluate_touches()
                    game_state = STATE_PLAYING
            elif game_state == STATE_PAUSED:
                if pygame.Rect(210, 520, 300, 60).collidepoint(x, y): game_state = STATE_PLAYING
                elif pygame.Rect(210, 600, 300, 60).collidepoint(x, y): save_game()
                elif pygame.Rect(210, 680, 300, 60).collidepoint(x, y):
                    if load_game(): game_state = STATE_PLAYING
                elif pygame.Rect(210, 760, 300, 60).collidepoint(x, y): game_state = STATE_MENU
            elif game_state == STATE_LOWER_WORLD:
                if pygame.Rect(210, 900, 300, 60).collidepoint(x, y):
                    game_state = STATE_PLAYING
                    player.y = 800
                    if platforms:
                        player.x = platforms[0]["rect"].centerx - 20
                        player.bottom = platforms[0]["rect"].top
            elif game_state == STATE_GAMEOVER:
                if pygame.Rect(210, 800, 300, 60).collidepoint(x, y):
                    reset_game()
                    game_state = STATE_PLAYING
            elif game_state == STATE_PLAYING:
                if pause_btn.collidepoint(x, y):
                    play_sound(sound_pause)
                    game_state = STATE_PAUSED
                elif mute_btn.collidepoint(x, y):
                    sound_muted = not sound_muted

    if game_state == STATE_MENU:
        screen.fill((20, 30, 50))
        title = big_font.render("PLATFORM JUMP", True, YELLOW)
        subtitle = small_font.render("100 MUNDOS DEL ESPACIO", True, CYAN)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 40))
        screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, 90))

        preview_box = pygame.Rect(WIDTH//2 - 40, 150, 80, 90)
        pygame.draw.rect(screen, (30, 30, 60), preview_box, border_radius=12)
        pygame.draw.rect(screen, CYAN, preview_box, 2, border_radius=12)
        draw_custom_character(screen, pygame.Rect(WIDTH//2 - 20, 165, 40, 55), AVATAR_OPTIONS[selected_avatar_idx], COLOR_OPTIONS[selected_color_idx][1], ACCESSORY_OPTIONS[selected_acc_idx])

        pygame.draw.rect(screen, (50, 50, 90), (160, 300, 400, 45), border_radius=8)
        screen.blit(small_font.render(f"Avatar: {AVATAR_OPTIONS[selected_avatar_idx].upper()}", True, WHITE), (180, 312))

        pygame.draw.rect(screen, (50, 50, 90), (160, 430, 400, 45), border_radius=8)
        screen.blit(small_font.render(f"Color: {COLOR_OPTIONS[selected_color_idx][0]}", True, COLOR_OPTIONS[selected_color_idx][1]), (180, 442))

        pygame.draw.rect(screen, (50, 50, 90), (160, 560, 400, 45), border_radius=8)
        screen.blit(small_font.render(f"Accesorio: {ACCESSORY_OPTIONS[selected_acc_idx].upper()}", True, WHITE), (180, 572))

        if dropdown_open == "avatar":
            for idx, av in enumerate(AVATAR_OPTIONS):
                r = pygame.Rect(160, 350 + idx * 45, 400, 40)
                pygame.draw.rect(screen, (40, 40, 90), r, border_radius=6)
                pygame.draw.rect(screen, YELLOW, r, 1, border_radius=6)
                screen.blit(small_font.render(av.upper(), True, WHITE), (180, 362 + idx * 45))
        elif dropdown_open == "color":
            for idx, col in enumerate(COLOR_OPTIONS):
                r = pygame.Rect(160, 480 + idx * 45, 400, 40)
                pygame.draw.rect(screen, (40, 40, 90), r, border_radius=6)
                pygame.draw.rect(screen, YELLOW, r, 1, border_radius=6)
                screen.blit(small_font.render(col[0], True, col[1]), (180, 492 + idx * 45))
        elif dropdown_open == "accessory":
            for idx, acc in enumerate(ACCESSORY_OPTIONS):
                r = pygame.Rect(160, 610 + idx * 45, 400, 40)
                pygame.draw.rect(screen, (40, 40, 90), r, border_radius=6)
                pygame.draw.rect(screen, YELLOW, r, 1, border_radius=6)
                screen.blit(small_font.render(acc.upper(), True, WHITE), (180, 622 + idx * 45))

        btn_load = pygame.Rect(210, 1220, 300, 60)
        pygame.draw.rect(screen, BLUE, btn_load, border_radius=12)
        screen.blit(font.render("CARGAR PARTIDA", True, WHITE), (btn_load.centerx - 105, btn_load.centery - 15))

        btn_start = pygame.Rect(210, 1300, 300, 60)
        pygame.draw.rect(screen, GREEN, btn_start, border_radius=12)
        screen.blit(font.render("NUEVO JUEGO", True, BLACK), (btn_start.centerx - 90, btn_start.centery - 15))

        pygame.display.flip()
        clock.tick(60)
        continue

    if game_state == STATE_PAUSED:
        screen.fill((10, 10, 20))
        title = big_font.render("JUEGO PAUSADO", True, YELLOW)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 350))

        btn_resume = pygame.Rect(210, 520, 300, 60)
        pygame.draw.rect(screen, GREEN, btn_resume, border_radius=10)
        screen.blit(font.render("REANUDAR", True, BLACK), (btn_resume.centerx - 70, btn_resume.centery - 15))

        btn_save = pygame.Rect(210, 600, 300, 60)
        pygame.draw.rect(screen, BLUE, btn_save, border_radius=10)
        screen.blit(font.render("GUARDAR PARTIDA", True, WHITE), (btn_save.centerx - 105, btn_save.centery - 15))

        btn_load_p = pygame.Rect(210, 680, 300, 60)
        pygame.draw.rect(screen, CYAN, btn_load_p, border_radius=10)
        screen.blit(font.render("CARGAR PARTIDA", True, BLACK), (btn_load_p.centerx - 100, btn_load_p.centery - 15))

        btn_exit = pygame.Rect(210, 760, 300, 60)
        pygame.draw.rect(screen, RED, btn_exit, border_radius=10)
        screen.blit(font.render("MENÚ PRINCIPAL", True, WHITE), (btn_exit.centerx - 100, btn_exit.centery - 15))

        if save_message_timer > 0:
            save_message_timer -= 1
            msg = small_font.render("¡Partida Guardada con Éxito!", True, GREEN)
            screen.blit(msg, (WIDTH//2 - msg.get_width()//2, 450))

        pygame.display.flip()
        clock.tick(60)
        continue

    if game_state == STATE_LOWER_WORLD:
        screen.fill((40, 10, 10))
        title = big_font.render("MUNDO INFERIOR", True, RED)
        subtitle = font.render("¡Has sido transportado por la nave!", True, WHITE)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 400))
        screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, 470))

        btn_back = pygame.Rect(210, 900, 300, 60)
        pygame.draw.rect(screen, GREEN, btn_back, border_radius=10)
        screen.blit(font.render("REGRESAR", True, BLACK), (btn_back.centerx - 65, btn_back.centery - 15))

        pygame.display.flip()
        clock.tick(60)
        continue

    if game_state == STATE_GAMEOVER:
        screen.fill((20, 10, 10))
        title = big_font.render("FIN DEL JUEGO", True, RED)
        sc_text = font.render(f"Puntuación final: {score}", True, WHITE)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 450))
        screen.blit(sc_text, (WIDTH//2 - sc_text.get_width()//2, 530))

        btn_restart = pygame.Rect(210, 800, 300, 60)
        pygame.draw.rect(screen, GREEN, btn_restart, border_radius=10)
        screen.blit(font.render("JUGAR DE NUEVO", True, BLACK), (btn_restart.centerx - 95, btn_restart.centery - 15))

        pygame.display.flip()
        clock.tick(60)
        continue

    target_vx = 0
    if left_pressed: target_vx = -speed
    if right_pressed: target_vx = speed

    is_slippery = (LEVEL % 4 == 0)
    if is_slippery:
        vx += (target_vx - vx) * 0.15
    else:
        vx = target_vx

    player.x += int(vx)
    if player.left < 0: player.left = 0
    if player.right > WIDTH: player.right = WIDTH

    is_inverted_gravity = (LEVEL % 5 == 0)
    current_gravity = -gravity if is_inverted_gravity else gravity
    current_jump = -jump_force if is_inverted_gravity else jump_force

    if jump_pressed and on_ground:
        vy = current_jump

    vy += current_gravity
    player.y += int(vy)
    on_ground = False

    if not is_inverted_gravity:
        if player.bottom > GAME_H:
            player.bottom = GAME_H
            vy = 0
            on_ground = True
    else:
        if player.top < 0:
            player.top = 0
            vy = 0
            on_ground = True

    for p_obj in platforms:
        p = p_obj["rect"]
        
        if p_obj["type"] == "moving":
            p_obj["offset"] += 0.05
            p.x += int(np.sin(p_obj["offset"]) * 3)

        if p_obj["type"] == "falling" and p_obj["fall_timer"] > 0:
            p.y += 6
            continue

        if not is_inverted_gravity:
            if player.colliderect(p) and vy > 0:
                if player.bottom - vy <= p.top + 10:
                    player.bottom = p.top
                    vy = 0
                    on_ground = True
                    if p_obj["type"] == "falling":
                        p_obj["fall_timer"] = 1
        else:
            if player.colliderect(p) and vy < 0:
                if player.top - vy >= p.bottom - 10:
                    player.top = p.bottom
                    vy = 0
                    on_ground = True
                    if p_obj["type"] == "falling":
                        p_obj["fall_timer"] = 1

    for t in trampolines:
        if not is_inverted_gravity:
            if player.colliderect(t) and vy > 0:
                player.bottom = t.top
                vy = jump_force * 1.4
                on_ground = False
        else:
            if player.colliderect(t) and vy < 0:
                player.top = t.bottom
                vy = -jump_force * 1.4
                on_ground = False

    for item in items[:]:
        if player.colliderect(item["rect"]):
            if item["type"] == "escudo":
                shield_active = True
            elif item["type"] == "balas":
                ammo += 5
            elif item["type"] == "electricidad":
                score += 50
            elif item["type"] == "fuego":
                score += 50
            elif item["type"] == "hielo":
                score += 50
            elif item["type"] == "corazon":
                if lives < 20:
                    lives += 1
                play_sound(sound_heart)
            items.remove(item)

    for proj in projectiles[:]:
        proj.y -= 15
        if proj.y < 0:
            projectiles.remove(proj)
            continue
        hit_enemy = False
        for sp in spiders[:]:
            if proj.colliderect(sp):
                spiders.remove(sp)
                score += 150
                hit_enemy = True
                play_sound(sound_hit)
                break
        if hit_enemy and proj in projectiles:
            projectiles.remove(proj)

    for sp in spiders[:]:
        if player.colliderect(sp):
            if shield_active:
                shield_active = False
                spiders.remove(sp)
            else:
                lives -= 1
                spiders.remove(sp)
                play_sound(sound_hit)
                if lives <= 0:
                    game_state = STATE_GAMEOVER

    if random.randint(0, 1000) < 5 and not spaceships:
        spaceships.append(pygame.Rect(-100, random.randint(100, 400), 90, 45))

    for ship in spaceships[:]:
        ship.x += 4
        if ship.colliderect(player):
            if shield_active:
                shield_active = False
                spaceships.remove(ship)
            else:
                if LEVEL > 1:
                    LEVEL -= 1
                game_state = STATE_LOWER_WORLD
                spaceships.remove(ship)
        elif ship.x > WIDTH:
            spaceships.remove(ship)

    target_platform = None
    min_dist = 999999
    for p_obj in platforms:
        p = p_obj["rect"]
        if p.centery < cpu2.centery:
            dist = abs(cpu2.centerx - p.centerx) + (cpu2.centery - p.centery)
            if dist < min_dist:
                min_dist = dist
                target_platform = p

    cpu2_vx = 0
    if target_platform:
        if cpu2.centerx < target_platform.centerx - 5:
            cpu2_vx = 10
        elif cpu2.centerx > target_platform.centerx + 5:
            cpu2_vx = -10

    cpu2.x += int(cpu2_vx)
    if cpu2.left < 0: cpu2.left = 0
    if cpu2.right > WIDTH: cpu2.right = WIDTH

    if cpu2_on_ground:
        should_jump_cpu = False
        if target_platform and (cpu2.centery - target_platform.centery) < 180:
            should_jump_cpu = True
        elif random.randint(0, 100) < 25:
            should_jump_cpu = True

        if should_jump_cpu:
            cpu2_vy = jump_force - 1.5
            cpu2_on_ground = False

    cpu2_vy += gravity
    cpu2.y += int(cpu2_vy)
    cpu2_on_ground = False

    for p_obj in platforms:
        p = p_obj["rect"]
        if cpu2.colliderect(p) and cpu2_vy > 0:
            if cpu2.bottom - cpu2_vy <= p.top + 10:
                cpu2.bottom = p.top
                cpu2_vy = 0
                cpu2_on_ground = True

    if cpu2.bottom > GAME_H:
        cpu2.bottom = GAME_H
        cpu2_vy = 0
        cpu2_on_ground = True

    if player.y < 550:
        shift = 550 - player.y
        player.y += shift
        cpu2.y += shift

        for p_obj in platforms: p_obj["rect"].y += shift
        for t in trampolines: t.y += shift
        for item in items: item["rect"].y += shift
        for sp in spiders: sp.y += shift
        for proj in projectiles: proj.y += shift
        for ship in spaceships: ship.y += shift

        highest_p_y = min(p_obj["rect"].y for p_obj in platforms)
        for p_obj in platforms:
            p = p_obj["rect"]
            if p.y > GAME_H:
                highest_p_y -= 95
                if p.x > 300:
                    p.x = random.randint(80, 240)
                else:
                    p.x = random.randint(380, 520)
                p.y = highest_p_y
                
                p_type = "normal"
                r_val = random.randint(0, 100)
                if LEVEL % 3 == 0 and r_val < 30:
                    p_type = "falling"
                elif LEVEL % 4 == 0 and r_val < 35:
                    p_type = "slippery"
                elif LEVEL >= 7 and r_val < 25:
                    p_type = "moving"
                
                p_obj["type"] = p_type
                p_obj["fall_timer"] = 0
                p_obj["offset"] = random.uniform(0, 6.28)

                if random.randint(0, 100) < 25:
                    trampolines.append(pygame.Rect(p.x + 40, p.y - 12, 50, 12))
                if random.randint(0, 100) < 40:
                    item_t = random.choices(
                        ["escudo", "balas", "electricidad", "fuego", "hielo", "corazon"],
                        weights=[15, 15, 10, 10, 10, 40],
                        k=1
                    )[0]
                    items.append({"rect": pygame.Rect(p.x + 50, p.y - 32, 28, 28), "type": item_t})
                if random.randint(0, 100) < 18:
                    spiders.append(pygame.Rect(p.x + 50, p.y - 25, 25, 25))

                platforms_passed += 1
                score += 1

                if platforms_passed >= PLATFORMS_TO_FINISH:
                    if LEVEL < MAX_LEVELS:
                        LEVEL += 1
                        platforms_passed = 0
                        score += 1000 * LEVEL
                        level_banner_timer = 120
                        level_banner_text = f"¡NIVEL {LEVEL}: {LEVEL_NAMES[LEVEL-1].upper()}!"
                    else:
                        LEVEL = 100

    if level_banner_timer > 0:
        level_banner_timer -= 1

    for obj in environment_elements:
        obj["y"] += obj["speed"]
        if obj["y"] > GAME_H:
            obj["y"] = -20
            obj["x"] = random.randint(0, WIDTH)

    current_name = LEVEL_NAMES[LEVEL-1].lower()
    if "pradera" in current_name:
        bg_color = (135, 206, 235)
    elif "lluvia" in current_name or "matutina" in current_name:
        bg_color = (110, 150, 180)
    elif "tormenta" in current_name or "eléctrica" in current_name:
        bg_color = (50, 60, 80)
    elif "otoñal" in current_name or "bosque" in current_name:
        bg_color = (180, 130, 90)
    elif "invierno" in current_name or "vientos" in current_name:
        bg_color = (140, 170, 200)
    elif "primaveral" in current_name or "deshielo" in current_name:
        bg_color = (120, 200, 150)
    elif "atardecer" in current_name or "dorado" in current_name:
        bg_color = (210, 120, 60)
    elif "crepuscular" in current_name or "cielo" in current_name:
        bg_color = (90, 50, 110)
    elif "luciernagas" in current_name or "noche" in current_name:
        bg_color = (20, 25, 50)
    elif "luna llena" in current_name:
        bg_color = (15, 20, 40)
    elif LEVEL <= 50:
        bg_color = (40, 30, 70)
    else:
        bg_color = (10, 10, 25)

    screen.fill(bg_color)

    if "luna llena" in current_name or LEVEL > 50:
        pygame.draw.circle(screen, (240, 240, 220), (550, 150), 45)

    for obj in environment_elements:
        if "lluvia" in current_name or "tormenta" in current_name or LEVEL <= 3:
            if obj["type"] == "rain":
                pygame.draw.line(screen, (200, 220, 255), (obj["x"], obj["y"]), (obj["x"] - 2, obj["y"] + 10), 2)
        elif "otoñal" in current_name or "bosque" in current_name:
            if obj["type"] == "leaf":
                pygame.draw.circle(screen, (200, 120, 40), (int(obj["x"]), int(obj["y"])), 4)
        elif LEVEL > 10:
            if obj["type"] == "star":
                pygame.draw.circle(screen, WHITE, (int(obj["x"]), int(obj["y"])), 2)
            elif obj["type"] == "astronaut":
                pygame.draw.rect(screen, WHITE, (int(obj["x"]), int(obj["y"]), 14, 20), border_radius=4)
                pygame.draw.circle(screen, CYAN, (int(obj["x"]) + 7, int(obj["y"]) + 5), 4)

    for p_obj in platforms:
        p = p_obj["rect"]
        p_col = ICE_BLUE if p_obj["type"] == "slippery" else BROWN
        pygame.draw.rect(screen, p_col, p)

    for t in trampolines:
        pygame.draw.rect(screen, CYAN, t, border_radius=4)

    for item in items:
        if item["type"] == "escudo":
            col = YELLOW
        elif item["type"] == "balas":
            col = RED
        elif item["type"] == "electricidad":
            col = CYAN
        elif item["type"] == "fuego":
            col = RED
        elif item["type"] == "corazon":
            hx, hy = item["rect"].center
            pygame.draw.circle(screen, RED, (hx - 4, hy), 6)
            pygame.draw.circle(screen, RED, (hx + 4, hy), 6)
            pygame.draw.polygon(screen, RED, [(hx - 11, hy + 2), (hx + 11, hy + 2), (hx, hy + 13)])
            continue
        else:
            col = BLUE
        pygame.draw.circle(screen, col, item["rect"].center, 12)

    spider_col = get_level_spider_color(LEVEL)
    for sp in spiders:
        pygame.draw.circle(screen, spider_col, sp.center, 12)
        pygame.draw.line(screen, spider_col, (sp.centerx - 12, sp.centery), (sp.centerx - 18, sp.centery - 6), 2)
        pygame.draw.line(screen, spider_col, (sp.centerx + 12, sp.centery), (sp.centerx + 18, sp.centery - 6), 2)

    for proj in projectiles:
        pygame.draw.rect(screen, YELLOW, proj)

    for ship in spaceships:
        pygame.draw.ellipse(screen, (100, 100, 100), (ship.x, ship.y + 15, ship.width, 15))
        pygame.draw.ellipse(screen, CYAN, (ship.x + 20, ship.y + 5, 50, 18))
        pygame.draw.circle(screen, YELLOW, (ship.x + 15, ship.y + 22), 3)
        pygame.draw.circle(screen, YELLOW, (ship.x + 45, ship.y + 25), 3)
        pygame.draw.circle(screen, YELLOW, (ship.x + 75, ship.y + 22), 3)

    draw_custom_character(screen, player, AVATAR_OPTIONS[selected_avatar_idx], COLOR_OPTIONS[selected_color_idx][1], ACCESSORY_OPTIONS[selected_acc_idx])

    if shield_active:
        pygame.draw.circle(screen, CYAN, player.center, 32, 2)

    pygame.draw.circle(screen, SKIN, (cpu2.centerx, cpu2.y + 8), 10)
    pygame.draw.rect(screen, ORANGE, (cpu2.x + 10, cpu2.y + 18, 20, 22), border_radius=4)
    pygame.draw.line(screen, BLACK, (cpu2.x + 13, cpu2.y + 40), (cpu2.x + 13, cpu2.y + 53), 4)
    pygame.draw.line(screen, BLACK, (cpu2.x + 27, cpu2.y + 40), (cpu2.x + 27, cpu2.y + 53), 4)

    pygame.draw.rect(screen, (40, 40, 40), (20, 20, 480, 25))
    progress_width = int((platforms_passed / PLATFORMS_TO_FINISH) * 480)
    pygame.draw.rect(screen, (0, 220, 80), (20, 20, progress_width, 25))

    pygame.draw.rect(screen, BLUE, pause_btn, border_radius=6)
    screen.blit(small_font.render("||", True, WHITE), (pause_btn.centerx - 8, pause_btn.centery - 10))

    pygame.draw.rect(screen, RED if sound_muted else GREEN, mute_btn, border_radius=6)
    screen.blit(small_font.render("MUTE" if sound_muted else "AUDIO", True, WHITE), (mute_btn.centerx - 28, mute_btn.centery - 8))

    hud1 = font.render(f"Nivel {LEVEL}: {LEVEL_NAMES[LEVEL-1]}", True, WHITE)
    hud2 = small_font.render(f"Progreso {platforms_passed}/{PLATFORMS_TO_FINISH}", True, WHITE)
    hud3 = small_font.render(f"Puntos: {score}  Balas: {ammo}", True, WHITE)

    screen.blit(hud1, (20, 55))
    screen.blit(hud2, (20, 95))
    screen.blit(hud3, (250, 95))

    pygame.draw.circle(screen, spider_col, (650, 75), 10)
    pygame.draw.line(screen, spider_col, (640, 75), (632, 68), 2)
    pygame.draw.line(screen, spider_col, (660, 75), (668, 68), 2)

    for i in range(lives):
        hx = 20 + (i % 10) * 22
        hy = 135 + (i // 10) * 18
        pygame.draw.circle(screen, RED, (hx - 3, hy), 4)
        pygame.draw.circle(screen, RED, (hx + 3, hy), 4)
        pygame.draw.polygon(screen, RED, [(hx - 7, hy + 1), (hx + 7, hy + 1), (hx, hy + 8)])

    if level_banner_timer > 0:
        banner_surf = big_font.render(level_banner_text, True, YELLOW)
        screen.blit(banner_surf, (WIDTH//2 - banner_surf.get_width()//2, 350))

    pygame.draw.rect(screen, (25, 25, 50), (0, 1100, WIDTH, 400))
    pygame.draw.rect(screen, (20, 20, 80) if left_pressed else (5, 5, 30), left_zone)
    pygame.draw.rect(screen, (20, 20, 80) if right_pressed else (5, 5, 30), right_zone)
    pygame.draw.rect(screen, (0, 180, 0) if jump_pressed else (0, 90, 0), jump_zone)
    pygame.draw.rect(screen, (180, 20, 20) if fire_pressed else (90, 10, 10), fire_zone)

    screen.blit(font.render("<", True, WHITE), (80, 1300))
    screen.blit(font.render(">", True, WHITE), (260, 1300))
    screen.blit(font.render("SALTO", True, WHITE), (390, 1300))
    screen.blit(font.render("FUEGO", True, WHITE), (565, 1300))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
