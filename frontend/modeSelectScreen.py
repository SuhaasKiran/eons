# modeSelectTemplate.py — Mode Select screen implemented on BaseDisplay
import pygame
from typing import Optional, List, Tuple
from frontend.baseDisplay import BaseDisplay
from backend.utils import *
TITLE = "Select Mode"

def _font(size=28, bold=False):
    f = pygame.font.SysFont("arial", size, bold=bold)
    return f if f is not None else pygame.font.Font(None, size)

def draw_round_rect(surface, rect, color, radius=18, width=0):
    pygame.draw.rect(surface, color, rect, width=width, border_radius=radius)

def draw_shadow(surface, rect, radius=22, spread=16, alpha=110):
    shadow = pygame.Surface((rect.w + spread, rect.h + spread), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, alpha), shadow.get_rect(), border_radius=radius+4)
    surface.blit(shadow, (rect.x + 6, rect.y + 8))

def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> List[str]:
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

class IconButton:
    """Top-right X (close) button."""
    def __init__(self, right, top, size=36):
        self.size = size
        self.rect = pygame.Rect(right - size, top, size, size)

    def draw(self, surface):
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        base = (210, 70, 70) if hover else (160, 60, 60)
        draw_round_rect(surface, self.rect, base, radius=12)
        pygame.draw.rect(surface, (25, 20, 20), self.rect, 2, border_radius=12)
        cx, cy = self.rect.center
        pad = 9
        pygame.draw.line(surface, (255, 230, 230), (cx - pad, cy - pad), (cx + pad, cy + pad), 3)
        pygame.draw.line(surface, (255, 230, 230), (cx + pad, cy - pad), (cx - pad, cy + pad), 3)

    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)

class ModeCard:
    def __init__(self, rect: pygame.Rect, title: str, desc: str):
        self.rect = rect
        self.title = title
        self.desc = desc

    def draw(self, surface, hover: bool, fonts: Tuple[pygame.font.Font, pygame.font.Font]):
        FONT_TITLE, FONT_DESC = fonts
        base = (24, 28, 44)
        border = (50, 70, 110)
        glow = (86, 154, 255) if hover else border
        shadow_alpha = 140 if hover else 100
        y_offset = -2 if hover else 0

        lifted = self.rect.move(0, y_offset)
        draw_shadow(surface, lifted, radius=18, spread=18, alpha=shadow_alpha)
        draw_round_rect(surface, lifted, base, radius=18)
        pygame.draw.rect(surface, glow, lifted, 2, border_radius=18)

        pad = 18
        title_surf = FONT_TITLE.render(self.title, True, (255, 255, 255))
        surface.blit(title_surf, (lifted.x + pad, lifted.y + pad))

        # description block
        desc_top = lifted.y + pad + title_surf.get_height() + 10
        max_w = lifted.w - pad*2
        lines = wrap_text(self.desc, FONT_DESC, max_w)
        y = desc_top
        for ln in lines[:6]:  # clamp a bit to keep tidy
            s = FONT_DESC.render(ln, True, (210, 220, 235))
            surface.blit(s, (lifted.x + pad, y))
            y += s.get_height() + 6

    def hit(self, pos) -> bool:
        return self.rect.collidepoint(pos)

class ModeSelectDisplay(BaseDisplay):
    CAPTION = TITLE

    def __init__(self, screen: pygame.Surface, background_path: Optional[str] = None):
        super().__init__(screen, background_path)
        self.FONT_HERO  = _font(48, bold=True)
        self.FONT_SUB   = _font(22, bold=True)
        self.FONT_TITLE = _font(24, bold=True)  # Slightly smaller for 3 cards
        self.FONT_DESC  = _font(16)             # Slightly smaller for 3 cards
        self.FONT_MESSAGE = _font(28, bold=True)  # For coming soon message

        W, H = self.screen.get_width(), self.screen.get_height()
        self.x_btn = IconButton(W - 20, 20, size=36)

        self.choice: Optional[str] = None  # "explore", "battle", or "player_info"

        # Coming soon message state
        self.show_coming_soon = False
        self.coming_soon_timer = 0
        self.coming_soon_message = ""

        # Cached layout (recomputed each draw to be robust on resize)
        self._cards: Tuple[ModeCard, ModeCard, ModeCard] = self._compute_layout()

    # ---------- BaseDisplay hooks ----------
    def on_event(self, event: pygame.event.Event):
        # Close (X)
        if self.x_btn.clicked(event):
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        # ESC to go back (no selection)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        # Click on a card
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            explore, battle, player_info = self._cards
            pos = event.pos
            if explore.hit(pos):
                self.choice = "explore"
                res = route_to_entry(self.background_path, self.screen)
                return
            if battle.hit(pos):
                self.choice = "battle"
                self._show_coming_soon_message("Battle Mode - Coming Soon!")
                return
            if player_info.hit(pos):
                self.choice = "player_info"
                self._show_coming_soon_message("Player Info - Coming Soon!")
                return
            
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            running = False
        if keys[pygame.K_i]:
            res = route_to_instructions(self.background_path, self.screen)

    def update(self, dt_ms: int):
        # Handle coming soon message timer
        if self.show_coming_soon:
            self.coming_soon_timer -= dt_ms
            if self.coming_soon_timer <= 0:
                self.show_coming_soon = False
                self.coming_soon_message = ""

    def _show_coming_soon_message(self, message: str):
        """Show a temporary 'Coming Soon' message"""
        self.coming_soon_message = message
        self.show_coming_soon = True
        self.coming_soon_timer = 1000  # Show for 2 seconds

    def draw_content(self, surface: pygame.Surface):
        W, H = surface.get_width(), surface.get_height()
        
        # Coming soon overlay (draw first if active)
        if self.show_coming_soon:
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            surface.blit(overlay, (0, 0))
            
            # Message box
            box_w, box_h = 400, 120
            box_x = (W - box_w) // 2
            box_y = (H - box_h) // 2
            
            # Draw message box
            draw_shadow(surface, pygame.Rect(box_x, box_y, box_w, box_h), radius=20, spread=12, alpha=150)
            draw_round_rect(surface, pygame.Rect(box_x, box_y, box_w, box_h), (45, 52, 70), radius=16)
            pygame.draw.rect(surface, (86, 154, 255), pygame.Rect(box_x, box_y, box_w, box_h), 3, border_radius=16)
            
            # Message text
            msg_surf = self.FONT_MESSAGE.render(self.coming_soon_message, True, (255, 255, 255))
            msg_rect = msg_surf.get_rect(center=(W // 2, H // 2 - 10))
            surface.blit(msg_surf, msg_rect)
            
            # Subtitle
            sub_surf = self.FONT_DESC.render("This feature will be available in a future update", True, (200, 210, 230))
            sub_rect = sub_surf.get_rect(center=(W // 2, H // 2 + 20))
            surface.blit(sub_surf, sub_rect)
            
            return  # Don't draw the rest of the UI when overlay is active

        # Normal UI (only draw if not showing coming soon message)
        # Header
        heading = "Choose Your Mode"
        sub     = "Hover and click to pick how you want to play."
        t1 = self.FONT_HERO.render(heading, True, (20, 69, 22))
        t2 = self.FONT_SUB.render(sub, True, (20, 69, 22))
        surface.blit(t1, t1.get_rect(midtop=(W // 2, int(H * 0.15))))  # Moved up slightly
        surface.blit(t2, t2.get_rect(midtop=(W // 2, int(H * 0.15) + 56)))

        # Layout and hover detection
        explore, battle, player_info = self._compute_layout()
        self._cards = (explore, battle, player_info)
        mouse = pygame.mouse.get_pos()
        hover_explore = explore.hit(mouse)
        hover_battle = battle.hit(mouse)
        hover_player_info = player_info.hit(mouse)

        # Draw cards
        explore.draw(surface, hover_explore, (self.FONT_TITLE, self.FONT_DESC))
        battle.draw(surface, hover_battle, (self.FONT_TITLE, self.FONT_DESC))
        player_info.draw(surface, hover_player_info, (self.FONT_TITLE, self.FONT_DESC))

        # Footer + X
        hint = self.FONT_DESC.render("Press I for Instructions", True, (0, 0, 0))
        surface.blit(hint, hint.get_rect(midbottom=(W // 2, H - 10)))
        self.x_btn.draw(surface)

    # ---------- helpers ----------
    def _compute_layout(self) -> Tuple[ModeCard, ModeCard, ModeCard]:
        W, H = self.screen.get_width(), self.screen.get_height()
        
        # Adaptive layout based on screen size
        if W >= 1200:
            # Wide screens: 3 cards in a row
            card_w = min(320, int(W * 0.26))
            card_h = min(220, int(H * 0.35))
            gap = 24
            total_w = card_w * 3 + gap * 2
            left_x = (W - total_w) // 2
            top_y = int(H * 0.38)
            
            rect1 = pygame.Rect(left_x, top_y, card_w, card_h)
            rect2 = pygame.Rect(left_x + card_w + gap, top_y, card_w, card_h)
            rect3 = pygame.Rect(left_x + (card_w + gap) * 2, top_y, card_w, card_h)
            
        elif W >= 800:
            # Medium screens: 2 cards on top, 1 centered below
            card_w = min(340, int(W * 0.38))
            card_h = min(180, int(H * 0.28))
            gap_x = 20
            gap_y = 20
            
            # Top row (2 cards)
            total_w_top = card_w * 2 + gap_x
            left_x_top = (W - total_w_top) // 2
            top_y_first = int(H * 0.32)
            
            rect1 = pygame.Rect(left_x_top, top_y_first, card_w, card_h)
            rect2 = pygame.Rect(left_x_top + card_w + gap_x, top_y_first, card_w, card_h)
            
            # Bottom row (1 card centered)
            left_x_bottom = (W - card_w) // 2
            top_y_second = top_y_first + card_h + gap_y
            rect3 = pygame.Rect(left_x_bottom, top_y_second, card_w, card_h)
            
        else:
            # Small screens: 3 cards vertically stacked
            card_w = min(480, int(W * 0.85))
            card_h = min(140, int(H * 0.22))
            gap = 16
            
            left_x = (W - card_w) // 2
            start_y = int(H * 0.30)
            
            rect1 = pygame.Rect(left_x, start_y, card_w, card_h)
            rect2 = pygame.Rect(left_x, start_y + card_h + gap, card_w, card_h)
            rect3 = pygame.Rect(left_x, start_y + (card_h + gap) * 2, card_w, card_h)

        explore = ModeCard(rect1, "Explore Animals",
                          "Travel to a distant past and face the mysterious beasts.")
        battle = ModeCard(rect2, "Battle Mode",
                         "Fight against Computer with your beast collection.")
        player_info = ModeCard(rect3, "Player Info",
                              "View your collection.")
        
        return explore, battle, player_info


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1000, 640))
    pygame.display.set_caption(TITLE)
    disp = ModeSelectDisplay(screen, background_path="frontend/assets/login2.png")
    disp.run()
    print("Choice:", disp.choice)
    pygame.quit()