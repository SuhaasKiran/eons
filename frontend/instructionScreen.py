# instructionTemplate.py â€" Instructions screen implemented on BaseDisplay
import pygame
from typing import List, Tuple, Optional
from frontend.baseDisplay import BaseDisplay

TITLE = "Instructions"

def _font(size=28, bold=False):
    f = pygame.font.SysFont("arial", size, bold=bold)
    return f if f is not None else pygame.font.Font(None, size)

# ---------------- UI Primitives ---------------- #
def draw_round_rect(surface, rect, color, radius=18, width=0):
    pygame.draw.rect(surface, color, rect, width=width, border_radius=radius)

def draw_shadow(surface, rect, radius=20, spread=12, alpha=90):
    """Soft drop shadow behind a rounded rect card."""
    shadow = pygame.Surface((rect.w + spread*2, rect.h + spread*2), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0,0,0,alpha), shadow.get_rect(), border_radius=radius+6)
    surface.blit(shadow, (rect.x - spread, rect.y - spread))

class Button:
    def __init__(self, x, y, w, h, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label

    def draw(self, surface, font, enabled=True):
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        base = (70, 110, 160) if (not hover or not enabled) else (90, 140, 200)
        pygame.draw.rect(surface, base, self.rect, border_radius=14)
        pygame.draw.rect(surface, (15, 25, 40), self.rect, 2, border_radius=14)
        t = font.render(self.label, True, (255, 255, 255))
        surface.blit(t, t.get_rect(center=self.rect.center))

    def clicked(self, event, enabled=True):
        return enabled and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)

def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> List[str]:
    """Wrap a long string into multiple lines that fit within max_width."""
    words = text.split()
    lines: List[str] = []
    line: List[str] = []
    for w in words:
        test = (" ".join(line+[w])).strip()
        if font.size(test)[0] <= max_width or not line:
            line.append(w)
        else:
            lines.append(" ".join(line))
            line = [w]
    if line:
        lines.append(" ".join(line))
    return lines

class InstructionDisplay(BaseDisplay):
    CAPTION = TITLE

    def __init__(self, screen: pygame.Surface, background_path: Optional[str] = None):
        super().__init__(screen, background_path)
        self.FONT_HERO = _font(42, bold=True)
        self.FONT_MD = _font(22)
        self.FONT_SM = _font(16)

        self.result = None
        self._running = True

        W, H = screen.get_width(), screen.get_height()
        margin = 40
        self.card_rect = pygame.Rect(margin, margin + 10, W - margin*2, H - margin*2 - 20)

        btn_w, btn_h = 120, 46
        self.next_btn = Button(self.card_rect.right - btn_w - 20, self.card_rect.bottom - btn_h - 16, btn_w, btn_h, "Next →")
        self.back_btn = Button(self.card_rect.left + 20,            self.card_rect.bottom - btn_h - 16, btn_w, btn_h, "← Back")

        # Content
        self.raw_lines = [
            "Welcome to the Game!",
            "",
            "You have 2 game modes: Explore and Battle.",
            "",
            "Explore:",
            "• Move Left:  ←",
            "• Move Right: →",
            "• Move Up: ↑",
            "• Move Down: ↓",
            "",
            "To catch the animal:",
            "Press Space to throw BeastBall",
            "Goal: Hit the moving animal the required number of times before you run out of ammo.",
            "Tip: Lead your shots and watch the animal's speed patterns.",
            "",
            "",
            "Notes: This panel is scrollable. Use mouse wheel, ↑/↓, PgUp/PgDn, or click-drag on the scroll bar.",
            "Long lines will be wrapped without overflowing off the screen, even on smaller displays.",
            "You can adjust difficulty using size_power, speed_power, and shots_power in your settings.",
        ]

        # Scroll state
        self.scroll_offset = 0
        self.content_height = 0  # computed
        self.viewport_rect = None  # computed

    # ---------- BaseDisplay hooks ----------
    def on_event(self, event: pygame.event.Event):
        # Buttons
        if self.next_btn.clicked(event):
            self.result = "next"
            self._running = False
            return
        if self.back_btn.clicked(event):
            self.result = "back"
            self._running = False
            return

        # Keys: R to go back (per prior UX), ESC to close
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.result = "back"
                self._running = False
                return
            if event.key == pygame.K_ESCAPE:
                self.result = "back"
                self._running = False
                return
            # scroll with arrows/page keys
            if event.key in (pygame.K_UP, pygame.K_PAGEUP):
                self._scroll_by(-60 if event.key == pygame.K_UP else -240)
            if event.key in (pygame.K_DOWN, pygame.K_PAGEDOWN):
                self._scroll_by(60 if event.key == pygame.K_DOWN else 240)

        # Mouse wheel
        if event.type == pygame.MOUSEWHEEL:
            self._scroll_by(-event.y * 60)

    def run(self):
        """Override BaseDisplay.run() to ensure proper exit handling."""
        clock = pygame.time.Clock()
        self._running = True
        
        while self._running:
            dt_ms = clock.tick(60)
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Don't quit the entire game, just this screen
                    self.result = "quit"
                    self._running = False
                    break
                else:
                    self.on_event(event)
            
            # Update and draw
            self.update(dt_ms)
            self.screen.fill((0, 0, 0))
            
            # Draw background if available
            if hasattr(self, 'background') and self.background:
                self.screen.blit(self.background, (0, 0))
            
            self.draw_content(self.screen)
            pygame.display.flip()
        
        return self

    def update(self, dt_ms: int):
        pass  # no internal timers needed

    def draw_content(self, surface: pygame.Surface):
        # Card background
        draw_shadow(surface, self.card_rect, radius=22, spread=16, alpha=110)
        draw_round_rect(surface, self.card_rect, (230, 236, 248), radius=20)

        # Title
        t_title = self.FONT_HERO.render("How to Play", True, (25, 40, 65))
        surface.blit(t_title, (self.card_rect.left + 24, self.card_rect.top + 20))

        # Layout for body + viewport
        content_top = self.card_rect.top + 90
        body_width = self.card_rect.w - 24*2 - 18  # leave room for scrollbar
        viewport_h = self.card_rect.bottom - 80 - content_top  # leave space for buttons

        self.viewport_rect = pygame.Rect(self.card_rect.left + 24, content_top, body_width, viewport_h)
        viewport_surf = pygame.Surface((self.viewport_rect.w, self.viewport_rect.h), pygame.SRCALPHA)
        viewport_surf.fill((0,0,0,0))

        # Render wrapped lines into the viewport
        body_lines: List[str] = []
        for raw in self.raw_lines:
            if raw.strip() == "":
                body_lines.append("")
                continue
            if raw.startswith("  "):  # pre-indented bullet
                body_lines.extend(["  " + ln for ln in wrap_text(raw.strip(), self.FONT_MD, body_width-18)])
            else:
                body_lines.extend(wrap_text(raw, self.FONT_MD, body_width))

        line_surfs = [(None if ln=="" else self.FONT_MD.render(ln, True, (25, 40, 65))) for ln in body_lines]
        line_heights = [(18 if s is None else s.get_height()+6) for s in line_surfs]
        self.content_height = sum(line_heights)
        max_scroll = max(0, self.content_height - viewport_h)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

        y = -self.scroll_offset
        for s, h, ln in zip(line_surfs, line_heights, body_lines):
            if s is None:
                y += 8
                continue
            if y + h >= 0 and y <= viewport_h:
                draw_x = 18 if ln.startswith("  ") else 0
                viewport_surf.blit(s, (draw_x, y))
            y += h

        surface.blit(viewport_surf, self.viewport_rect.topleft)

        # Scrollbar
        if max_scroll > 0:
            bar_area = pygame.Rect(self.viewport_rect.right + 6, self.viewport_rect.top, 8, self.viewport_rect.height)
            pygame.draw.rect(surface, (60, 80, 110), bar_area, border_radius=4)
            thumb_h = max(24, int(bar_area.h * (viewport_h / (self.content_height + 0.001))))
            thumb_y = int(bar_area.y + (bar_area.h - thumb_h) * (self.scroll_offset / max_scroll))
            pygame.draw.rect(surface, (200, 220, 245), (bar_area.x, thumb_y, bar_area.w, thumb_h), border_radius=4)

        # Buttons
        self.back_btn.draw(surface, self.FONT_MD, enabled=True)
        # self.next_btn.draw(surface, self.FONT_MD, enabled=True)  # Disabled for now, as there's no next screen

    # ---------- helpers ----------
    def _scroll_by(self, dy: int):
        if self.viewport_rect is None:
            return
        max_scroll = max(0, self.content_height - self.viewport_rect.h)
        self.scroll_offset = max(0, min(self.scroll_offset + dy, max_scroll))


# Legacy function-based interface for backward compatibility
def show_instructions(screen: pygame.Surface, background) -> str:
    """
    Legacy function interface that creates and runs an InstructionDisplay.
    Returns the result ("back", "next", or None).
    """
    bg_path = background if isinstance(background, str) else None
    disp = InstructionDisplay(screen, background_path=bg_path)
    
    # If background is already a Surface, use it directly
    if bg_path is None and background is not None:
        try:
            if isinstance(background, pygame.Surface):
                disp.background = background
        except Exception:
            pass
    
    result = disp.run()
    return getattr(disp, "result", None)


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1000, 640))
    disp = InstructionDisplay(screen)
    pygame.display.set_caption(TITLE)
    result = disp.run()
    print("Closed with result:", getattr(disp, "result", None))
    pygame.quit()