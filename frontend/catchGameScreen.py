import os
import random
import pygame
from collections import Counter
from typing import Optional, Tuple
from frontend.baseDisplay import BaseDisplay
from backend.utils import *
# ---------------------- Config ---------------------- #
FPS = 120

# Base stats
BASE_SIZE   = 60
BASE_SPEED  = 2.5
BASE_SHOTS  = 2
BASE_AMMO   = 12

# catcher/beastBalls
catcher_SPEED = 6
beastBalls_SPEED  = 9
beastBalls_COOLDOWN_MS = 180

# ---------------------- Utility ---------------------- #
def load_font(size, bold=False):
    f = pygame.font.SysFont("arial", size, bold=bold)
    return f if f is not None else pygame.font.Font(None, size)

# Fonts will be initialized when needed
_fonts_cache = {}

def get_font(size, bold=False):
    key = (size, bold)
    if key not in _fonts_cache:
        _fonts_cache[key] = load_font(size, bold)
    return _fonts_cache[key]

def get_most_common_color(image):
    width, height = image.get_size()
    
    # Count frequency of each color
    color_counter = Counter()
    for x in range(width):
        for y in range(height):
            color = image.get_at((x, y))[:3]  # Get RGB, ignore alpha if present
            color_counter[color] += 1
    
    # Return the most common color
    most_common = color_counter.most_common(1)
    if most_common:
        return most_common[0][0]  # Return the RGB tuple
    else:
        return (0, 0, 0)
    
# Generic safe image loader (returns None if missing)
def safe_load_image(path):
    try:
        if os.path.exists(path):
            image = pygame.image.load(path)
            # bg_color = get_most_common_color(image)
            # image.set_colorkey(bg_color)
            image.set_alpha(None)
            return image.convert_alpha()
    except Exception:
        pass
    return None

def safe_load_image_no_bg(path):
    try:
        if os.path.exists(path):
            image = pygame.image.load(path)
            bg_color = get_most_common_color(image)
            image.set_colorkey(bg_color)
            image.set_alpha(None)
            return image.convert_alpha()
    except Exception:
        pass
    return None

# -------------------- Entities ---------------------- #
class Animal:
    def __init__(self, cx, cy, size_px, speed_px, hits_required, img_raw):
        self.size = int(size_px)
        self.rect = pygame.Rect(0, 0, self.size, self.size)
        self.rect.center = (cx, cy)
        self.vx = speed_px if random.choice([True, False]) else -speed_px
        self.hits_left = max(1, int(round(hits_required)))
        self.color = (180, 100, 50)  # Default brown color

        self.img_raw = img_raw
        self.img = None
        self._rescale_image()

    def _rescale_image(self):
        if self.img_raw:
            # Keep aspect ratio; fit into square self.size x self.size
            w, h = self.img_raw.get_size()
            if w == 0 or h == 0:
                self.img = None
                return
            scale = min(self.size / w, self.size / h)
            new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
            self.img = pygame.transform.smoothscale(self.img_raw, (new_w, new_h))
        else:
            self.img = None

    def set_size(self, new_size):
        center = self.rect.center
        self.size = int(new_size)
        self.rect.size = (self.size, self.size)
        self.rect.center = center
        self._rescale_image()

    def update(self, screen_width):
        self.rect.x += int(self.vx)
        if self.rect.left <= 0:
            self.rect.left = 0
            self.vx = abs(self.vx)
        elif self.rect.right >= screen_width:
            self.rect.right = screen_width
            self.vx = -abs(self.vx)

    def draw(self, surface):
        if self.img:
            # Center the scaled image inside rect
            img_rect = self.img.get_rect(center=self.rect.center)
            surface.blit(self.img, img_rect)
        else:
            pygame.draw.ellipse(surface, self.color, self.rect)
            pygame.draw.ellipse(surface, (0, 0, 0), self.rect, 2)

class catcher:
    def __init__(self, screen_width, screen_height, img_raw=None):
        self.w = 90
        self.h = 64
        self.rect = pygame.Rect(0, 0, self.w, self.h)
        self.rect.midbottom = (screen_width // 2, screen_height - 24)
        self.color = (255, 240, 180)
        self.cooldown_ms = beastBalls_COOLDOWN_MS
        self.last_shot_time = 0
        self.screen_width = screen_width

        # Prepare catcher image
        if img_raw:
            self.img = pygame.transform.smoothscale(img_raw, (self.w, self.h))
        else:
            self.img = None

    def move(self, dx):
        self.rect.x += dx
        self.rect.x = max(0, min(self.screen_width - self.w, self.rect.x))

    def draw(self, surface):
        if self.img:
            surface.blit(self.img, self.rect)
        else:
            pygame.draw.rect(surface, self.color, self.rect, border_radius=0)
            barrel = pygame.Rect(0, 0, 8, 16)
            barrel.midtop = (self.rect.centerx, self.rect.top - 2)
            pygame.draw.rect(surface, (255, 220, 140), barrel, border_radius=0)

    def can_shoot(self):
        return pygame.time.get_ticks() - self.last_shot_time >= self.cooldown_ms

    def record_shot(self):
        self.last_shot_time = pygame.time.get_ticks()

class beastBalls:
    def __init__(self, x, y, img_raw=None):
        self.w, self.h = 10, 24
        self.rect = pygame.Rect(x - self.w // 2, y - self.h, self.w, self.h)
        self.color = (255, 255, 255)
        if img_raw:
            self.img = pygame.transform.smoothscale(img_raw, (self.w, self.h))
        else:
            self.img = None

    def update(self):
        self.rect.y -= beastBalls_SPEED

    def draw(self, surface):
        if self.img:
            surface.blit(self.img, self.rect)
        else:
            pygame.draw.rect(surface, self.color, self.rect, border_radius=3)

    def offscreen(self):
        return self.rect.bottom < 0

# ------------------- Game State --------------------- #
STATE_INTRO   = "intro"
STATE_PLAYING = "playing"
STATE_WIN     = "win"
STATE_LOSE    = "lose"
STATE_STOP    = "stop"   # stopped/paused via E key

# ------------------- Main Display ------------------- #
class CaptureGameDisplay(BaseDisplay):
    CAPTION = "Animal Capture Game"

    def __init__(self, screen: pygame.Surface, 
                 background_path: Optional[str] = "frontend/assets/swamp.png",
                 animal_image_path: Optional[str] = None,
                 animal_name: str = "Mysterious Creature",
                 animal_desc: str = "A fascinating creature that requires skill to capture safely.",
                 size_power: float = 1.0,
                 speed_power: float = 1.0,
                 shots_power: float = 1.0,
                 catcher_image_path: Optional[str] = "frontend/assets/human.jpeg",
                 beastBalls_image_path: Optional[str] = "frontend/assets/beastBalls.jpg"):
        
        super().__init__(screen, background_path)
        
        # Game parameters
        self.animal_name = animal_name
        self.animal_desc = animal_desc
        self.size_power = size_power
        self.speed_power = speed_power
        self.shots_power = shots_power
        
        # Load images
        self.animal_img_raw = safe_load_image(animal_image_path) if animal_image_path else None
        self.catcher_img_raw = safe_load_image_no_bg(catcher_image_path) if catcher_image_path else None
        self.beastBalls_img_raw = safe_load_image(beastBalls_image_path) if beastBalls_image_path else None
        
        # Game state
        self.clock = pygame.time.Clock()
        self.reset_game()

    def apply_powers(self):
        size_px  = BASE_SIZE  * self.size_power
        speed_px = BASE_SPEED * self.speed_power
        hits_req = BASE_SHOTS * self.shots_power
        ammo     = int(BASE_AMMO + hits_req * 4)
        return int(size_px), speed_px, hits_req, ammo

    def reset_game(self):
        size_px, speed_px, hits_req, ammo = self.apply_powers()

        # Intro animal: big & centered (no motion)
        self.intro_animal = Animal(
            self.w // 2, self.h // 2 - 20,
            max(180, size_px * 2), 0,
            max(1, int(round(hits_req))), self.animal_img_raw
        )

        # Playing animal
        self.animal = Animal(
            self.w // 2, self.h // 3,
            size_px, speed_px,
            max(1, int(round(hits_req))), self.animal_img_raw
        )

        self.catcher = catcher(self.w, self.h, self.catcher_img_raw)
        self.beastBallss = []
        self.ammo = int(ammo)
        self.shots_taken = 0
        self.state = STATE_INTRO

    def draw_text_center(self, surface, text, font, color, y):
        t = font.render(text, True, color)
        r = t.get_rect(center=(self.w // 2, y))
        surface.blit(t, r)

    def button(self, surface, rect, label, enabled=True):
        color = (70, 110, 160) if enabled else (80, 80, 80)
        hover = rect.collidepoint(pygame.mouse.get_pos())
        if enabled and hover:
            color = (90, 140, 200)
        pygame.draw.rect(surface, color, rect, border_radius=10)
        pygame.draw.rect(surface, (20, 30, 50), rect, width=2, border_radius=10)
        txt = get_font(24).render(label, True, (255, 255, 255))
        surface.blit(txt, txt.get_rect(center=rect.center))
        return enabled and hover

    def on_event(self, event: pygame.event.Event):
        # Global hotkeys: E = stop/pause
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:
                if self.state not in (STATE_STOP, STATE_WIN, STATE_LOSE):
                    self.state = STATE_STOP
            elif event.key == pygame.K_r:
                if self.state in (STATE_WIN, STATE_LOSE, STATE_STOP):
                    self.reset_game()

        if self.state == STATE_INTRO:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Click handled during draw with hover detection
                pass
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            running = False
        if keys[pygame.K_i]:
            route_to_instructions(self.background_path, self.screen)

    def update(self, dt_ms: int):
        keys = pygame.key.get_pressed()

        if self.state == STATE_PLAYING:
            # catcher movement
            dx = 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx -= catcher_SPEED
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx += catcher_SPEED
            self.catcher.move(dx)

            # Shooting
            if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and self.ammo > 0 and self.catcher.can_shoot():
                bx = self.catcher.rect.centerx
                by = self.catcher.rect.top - 4
                self.beastBallss.append(beastBalls(bx, by, self.beastBalls_img_raw))
                self.catcher.record_shot()
                self.ammo -= 1
                self.shots_taken += 1

            # Update entities
            self.animal.update(self.w)

            for b in self.beastBallss:
                b.update()
            self.beastBallss = [b for b in self.beastBallss if not b.offscreen()]

            # beastBalls vs animal collision
            hit_idx = None
            for i, b in enumerate(self.beastBallss):
                if b.rect.colliderect(self.animal.rect):
                    hit_idx = i
                    break
            if hit_idx is not None:
                del self.beastBallss[hit_idx]
                self.animal.hits_left -= 1

            # Win/Lose logic
            if self.animal.hits_left <= 0:
                self.state = STATE_WIN
            elif self.ammo <= 0 and not self.beastBallss:
                self.state = STATE_LOSE

    def draw_content(self, surface: pygame.Surface):
        if self.state == STATE_INTRO:
            overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            surface.blit(overlay, (0, 0))

            dy = 50

            if hasattr(self.intro_animal, "y"):
                old_y = self.intro_animal.y
                self.intro_animal.y = old_y - dy
                if hasattr(self.intro_animal, "rect"):
                    self.intro_animal.rect.y -= dy

                self.intro_animal.draw(surface)

                # restore
                if hasattr(self.intro_animal, "rect"):
                    self.intro_animal.rect.y += dy
                self.intro_animal.y = old_y
            else:
                # fallback: draw to a temp surface, then blit shifted up
                temp = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
                self.intro_animal.draw(temp)
                surface.blit(temp, (0, -dy))

            self.draw_text_center(surface, self.animal_name, get_font(36, bold=True), (255, 255, 255), self.h // 2 + 50)

            # Wrap description
            words = self.animal_desc.split()
            lines, line = [], []
            font_md = get_font(24)
            for w in words:
                test = " ".join(line + [w])
                if font_md.size(test)[0] > self.w * 0.8:
                    lines.append(" ".join(line))
                    line = [w]
                else:
                    line.append(w)
            if line:
                lines.append(" ".join(line))
            y_start = self.h // 2 + 110
            for i, ln in enumerate(lines[:3]):
                self.draw_text_center(surface, ln, font_md, (230, 240, 255), y_start + i * 28)

            size_px, speed_px, hits_req, ammo_preview = self.apply_powers()
            # info = f"Size: {size_px}px   Speed: {speed_px:.1f}   Shots to Capture: {int(round(hits_req))}   Ammo: {ammo_preview}"
            # self.draw_text_center(surface, info, get_font(18), (210, 220, 240), self.h - 80)

            btn_rect = pygame.Rect(0, 0, 220, 56)
            btn_rect.center = (self.w // 2, self.h - 40)
            hovering = self.button(surface, btn_rect, "Capture")
            if pygame.mouse.get_pressed()[0] and hovering:
                self.state = STATE_PLAYING

            # Hint bar
            self.draw_text_center(surface, "Press E to Stop • ESC to Exit", get_font(18), (220, 230, 245), 24)

        elif self.state == STATE_PLAYING:
            # Draw entities
            self.animal.draw(surface)
            for b in self.beastBallss:
                b.draw(surface)
            self.catcher.draw(surface)

            # HUD
            ui_pad = 10
            hud_bg = pygame.Rect(8, 8, self.w - 16, 40)
            s = pygame.Surface(hud_bg.size, pygame.SRCALPHA)
            s.fill((0, 0, 0, 90))
            surface.blit(s, hud_bg.topleft)
            font_md = get_font(24)
            info_left = f"Animal: {self.animal_name} | Hits Left: {self.animal.hits_left} | Ammo: {self.ammo}"
            info_right = ""
            surface.blit(font_md.render(info_left, True, (255, 255, 255)), (hud_bg.x + ui_pad, hud_bg.y + 10))
            rtxt = font_md.render(info_right, True, (255, 255, 255))
            surface.blit(rtxt, (hud_bg.right - rtxt.get_width() - ui_pad, hud_bg.y + 10))

            # Footer hint
            self.draw_text_center(surface, "←/A and →/D to move • SPACE to shoot • E to Stop • ESC to Exit", get_font(18), (220, 230, 245), self.h - 14)

        elif self.state in (STATE_WIN, STATE_LOSE, STATE_STOP):
            overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            surface.blit(overlay, (0, 0))

            if self.state == STATE_STOP:
                title = "Game Stopped"
                detail = "Press R to Restart, or ESC to Exit."
            elif self.state == STATE_WIN:
                title = "Captured!"
                detail = f"You captured the {self.animal_name} with {self.shots_taken} shots. Press R to Restart or ESC to Exit."
                # TODO: add the code to update user info and add caught animals

            else:
                title = "Out of Ammo!"
                need = self.animal.hits_left
                detail = f"The {self.animal_name} escaped. Needed {need} more hit(s). Press R to Restart or ESC to Exit."

            self.draw_text_center(surface, title, get_font(36, bold=True), (255, 255, 255), self.h // 2 - 30)
            self.draw_text_center(surface, detail, get_font(24), (230, 240, 255), self.h // 2 + 10)

# Optional: local run for testing
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((960, 540))
    
    game_display = CaptureGameDisplay(
        screen=screen,
        background_path="frontend/assets/login4.jpg",
        animal_image_path="frontend/assets/dino.jpeg",
        animal_name="Dinosaur",
        animal_desc="Elusive, agile, and lightning-fast. Requires multiple tranquilizer shots to safely capture.",
        size_power=1.2,
        speed_power=1.4,
        shots_power=1.5,
        catcher_image_path="frontend/assets/human.jpeg",
        beastBalls_image_path="frontend/assets/bullet.jpg"
    )
    
    result = game_display.run()
    pygame.quit()