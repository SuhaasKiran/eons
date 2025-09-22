# base_display.py
import os, sys, pygame
from typing import Optional, Tuple
import yaml

# Load config
with open("config.yaml", 'r') as f:
    config = yaml.safe_load(f)
ASSETS_PATH = config.get("ASSETS_PATH", "frontend/assets/")

# ---------------- Config ---------------- #
SCREEN_W, SCREEN_H = 900, 600
DEFAULT_BG = ASSETS_PATH + "login3.png"   # put your image in the same folder or change this path
TITLE = "EONS"
# ----------------------------------------- #

# ---------------- Utility ---------------- #
def lighten_alpha(surface, alpha=80):
    """Lighten by alpha-blending towards white."""
    out = surface.copy()
    overlay = pygame.Surface(out.get_size(), pygame.SRCALPHA)
    overlay.fill((255, 255, 255, alpha))
    out.blit(overlay, (0, 0))
    return out

def load_background(size: Tuple[int,int], path: str = DEFAULT_BG) -> pygame.Surface:
    w, h = size
    if os.path.exists(path):
        img = pygame.image.load(path).convert()
        img = pygame.transform.smoothscale(img, (w, h))
        return lighten_alpha(img, alpha=90)  # 0..255 (higher = lighter)
    # fallback
    surf = pygame.Surface((w, h))
    surf.fill((28, 32, 48))
    return surf
# ----------------------------------------- #


class CloseButton:
    """Top-right X (close) button."""
    def __init__(self, right: int, top: int, size: int = 36):
        self.rect = pygame.Rect(right - size, top, size, size)
    def draw(self, surface: pygame.Surface):
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        color = (210, 70, 70) if hover else (160, 60, 60)
        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        pygame.draw.rect(surface, (25, 20, 20), self.rect, 2, border_radius=12)
        cx, cy = self.rect.center; pad = 9
        pygame.draw.line(surface, (255,230,230), (cx-pad,cy-pad), (cx+pad,cy+pad), 3)
        pygame.draw.line(surface, (255,230,230), (cx+pad,cy-pad), (cx-pad,cy+pad), 3)

class BaseDisplay:
    CAPTION = "Screen"

    def __init__(self, screen: pygame.Surface, background_path: Optional[str] = DEFAULT_BG):
        self.screen = screen
        self.w, self.h = screen.get_size()
        self.background_path = background_path
        if background_path is None:
            self.background_path = DEFAULT_BG            
        self.x_btn = CloseButton(self.w - 20, 20, size=36)
        self.clock = pygame.time.Clock()
        self.running = True
        self.result = None

    # --------- Hooks to override --------- #
    def on_event(self, event: pygame.event.Event):  # input
        pass
    def update(self, dt_ms: int):                   # game logic
        pass
    def draw_content(self, surface: pygame.Surface):# UI on top of base
        pass

    # --------- Main loop --------- #
    def run(self):
        background = load_background((self.w, self.h), self.background_path)
        pygame.display.set_caption(self.CAPTION)
        while self.running:
            dt = self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    # Default ESC behavior: return None to caller
                    self.running = False
                    break
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.x_btn.rect.collidepoint(event.pos):
                    pygame.quit(); sys.exit()
                # pass event to subclass
                self.on_event(event)

            self.update(dt)

            # base draw
            self.screen.blit(background, (0, 0))
            self.draw_content(self.screen)  # your UI
            self.x_btn.draw(self.screen)
            pygame.display.flip()

        return self.result
