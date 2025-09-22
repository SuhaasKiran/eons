# InfoScreen.py — Streaming paragraph screen (BaseDisplay)
import pygame
from typing import Optional, List
from frontend.baseDisplay import BaseDisplay
from backend.utils import *

TITLE = "Information"

def _font(size=28, bold=False):
    f = pygame.font.SysFont("arial", size, bold=bold)
    return f if f is not None else pygame.font.Font(None, size)

def draw_round_rect(surface, rect, color, radius=18, width=0):
    pygame.draw.rect(surface, color, rect, width=width, border_radius=radius)

def draw_shadow(surface, rect, radius=22, spread=16, alpha=110):
    shadow = pygame.Surface((rect.w + spread, rect.h + spread), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, alpha), shadow.get_rect(), border_radius=radius+4)
    surface.blit(shadow, (rect.x + 6, rect.y + 8))

class Button:
    def __init__(self, x, y, w, h, label):
        self.rect = pygame.Rect(x, y, w, h); self.label = label
    def draw(self, surface, font, enabled=True):
        hover = enabled and self.rect.collidepoint(pygame.mouse.get_pos())
        base = (70, 110, 160) if (not hover or not enabled) else (90, 140, 200)
        pygame.draw.rect(surface, base, self.rect, border_radius=14)
        pygame.draw.rect(surface, (15, 25, 40), self.rect, 2, border_radius=14)
        t = font.render(self.label, True, (255,255,255) if enabled else (230,230,230))
        surface.blit(t, t.get_rect(center=self.rect.center))
    def clicked(self, event, enabled=True):
        return enabled and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)

def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> List[str]:
    words = (text or "").split()
    lines: List[str] = []; line: List[str] = []
    for w in words:
        test = (" ".join(line + [w])).strip()
        if not line or font.size(test)[0] <= max_width:
            line.append(w)
        else:
            lines.append(" ".join(line)); line = [w]
    if line: lines.append(" ".join(line))
    return lines

class InfoDisplay(BaseDisplay):
    CAPTION = TITLE
    def __init__(self, screen: pygame.Surface, background_path: Optional[str] = None,
                 text: Optional[str] = None, title: Optional[str] = None,
                 ms_per_char: int = 22, enable_punct_pause: bool = True,
                 require_full_before_start: bool = True,
                 time_place_info=None, time_place_animals=None, time_background="frontend/assets/swamp.png"):
        super().__init__(screen, background_path)
        self.FONT_HERO = _font(40, bold=True); self.FONT_MD = _font(22); self.FONT_SM = _font(16)
        self.title = title or "Info"
        print("time_place_info =", time_place_info)  # DEBUG
        print("time place_animals =", time_place_animals)  # DEBUGs
        self.full_text = time_place_info['summary'] or "This is a streaming paragraph. Press Space to fast-forward. Press Start to continue."
        W, H = self.screen.get_width(), self.screen.get_height()
        margin = 40
        self.card_rect = pygame.Rect(margin, margin+10, W - margin*2, H - margin*2 - 20)
        self.start_btn = Button(0, 0, 160, 48, "Start")
        self.require_full = require_full_before_start
        self.ms_per_char = max(5, int(ms_per_char)); self.enable_punct_pause = enable_punct_pause
        self._chars = 0; self._done = False; self._accum = 0.0; self._cur_delay = float(self.ms_per_char)
        self.result = None
        self.time_place_info = time_place_info
        self.time_place_animals = time_place_animals
        self.time_background = time_background

    def on_event(self, event: pygame.event.Event):
        if self.start_btn.clicked(event, enabled=(self._done or not self.require_full)):
            self.result = "start"
            animal_info = {}
            for animal in (self.time_place_animals or []):
                print("\nanimal:", getattr(animal, 'species', None), getattr(animal, 'imagePath', None), getattr(animal, 'description', None))  # DEBUG
                animal_info[str(getattr(animal, 'species', None))] = {
                    "image_name": str(getattr(animal, 'imagePath', "")),
                    "description": getattr(animal, 'description', 1.0),
                    "relative_size": float(getattr(animal, 'size', 1.0))  # New field
                }
            print("animal_info:", animal_info)  # DEBUG
            res = route_to_exploreGame(self.background_path, self.screen, animal_info, self.time_background)
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.card_rect.collidepoint(event.pos) and not self._done: self._finish_stream()
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                if not self._done: self._finish_stream()
                else: self.result = "start"; pygame.event.post(pygame.event.Event(pygame.QUIT)); return
            if event.key == pygame.K_ESCAPE: pygame.event.post(pygame.event.Event(pygame.QUIT)); return
    def update(self, dt_ms: int):
        if self._done: return
        self._accum += dt_ms
        while self._accum >= self._cur_delay and not self._done:
            self._accum -= self._cur_delay; self._chars += 1
            if self._chars >= len(self.full_text): self._chars = len(self.full_text); self._done = True; break
            self._cur_delay = self._next_delay(self.full_text[self._chars - 1])
    def draw_content(self, surface: pygame.Surface):
        draw_shadow(surface, self.card_rect, radius=22, spread=16, alpha=110)
        draw_round_rect(surface, self.card_rect, (24, 28, 44), radius=20)
        pygame.draw.rect(surface, (50, 70, 110), self.card_rect, 2, border_radius=20)
        t_title = self.FONT_HERO.render(self.title, True, (255, 255, 255))
        surface.blit(t_title, (self.card_rect.left + 24, self.card_rect.top + 20))
        pad = 24; top_y = self.card_rect.top + 20 + t_title.get_height() + 12
        bottom_y = self.card_rect.bottom - (pad + 56)
        viewport = pygame.Rect(self.card_rect.left + pad, top_y, self.card_rect.w - pad*2, bottom_y - top_y)
        snippet = self.full_text[:self._chars]; lines = wrap_text(snippet, self.FONT_MD, viewport.w)
        y = viewport.y
        for ln in lines:
            s = self.FONT_MD.render(ln, True, (220, 230, 245)); surface.blit(s, (viewport.x, y)); y += s.get_height() + 6
        if not self._done and lines:
            caret_w = max(2, self.FONT_MD.size("|")[0] // 3); caret_h = self.FONT_MD.get_height()
            caret_x = viewport.x + (self.FONT_MD.size(lines[-1])[0]); caret_y = y - (self.FONT_MD.get_height() + 6)
            pygame.draw.rect(surface, (240, 240, 255), (caret_x, caret_y + 3, caret_w, caret_h - 6), border_radius=1)
        self.start_btn.rect.center = (self.card_rect.centerx, self.card_rect.bottom - pad - self.start_btn.rect.h//2)
        enabled = (self._done or not self.require_full); self.start_btn.draw(surface, self.FONT_MD, enabled=enabled)
        
    def _next_delay(self, ch: str) -> float:
        if not self.enable_punct_pause: return float(self.ms_per_char)
        if ch in ".!?": return float(self.ms_per_char * 4)
        if ch in ",;:": return float(self.ms_per_char * 2)
        if ch.isspace(): return max(10.0, float(self.ms_per_char) * 0.8)
        return float(self.ms_per_char)
    def _finish_stream(self): self._chars = len(self.full_text); self._done = True; self._accum = 0.0; self._cur_delay = float(self.ms_per_char)

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1000, 640)); pygame.display.set_caption(TITLE)
    demo_text = ("Welcome to InfoScreen. This paragraph is revealed gradually as if typed in real time. "
                 "Use Space or click to fast-forward. When finished, press Start to continue.")
    disp = InfoDisplay(screen, background_path=None, text=demo_text, title="Info", ms_per_char=18)
    disp.run(); print("Result:", disp.result); pygame.quit()
