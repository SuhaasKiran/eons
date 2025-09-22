# userProfileTemplate.py — User Profile screen implemented on BaseDisplay
import os
import pygame
from typing import Optional, List, Dict, Any, Tuple
from frontend.baseDisplay import BaseDisplay
from backend.utils import route_to_instructions

TITLE = "User Profile"

def _font(size=28, bold=False):
    f = pygame.font.SysFont("arial", size, bold=bold)
    return f if f is not None else pygame.font.Font(None, size)

def draw_round_rect(surface, rect, color, radius=18, width=0):
    pygame.draw.rect(surface, color, rect, width=width, border_radius=radius)

def safe_load(path: str) -> Optional[pygame.Surface]:
    try:
        if path and os.path.exists(path):
            img = pygame.image.load(path)
            return img.convert_alpha()
    except Exception:
        pass
    return None

def blit_image_fit(surface: pygame.Surface, img: Optional[pygame.Surface], rect: pygame.Rect):
    """Scale 'img' to fit within 'rect' preserving aspect ratio, centered."""
    if img is None or rect.w <= 0 or rect.h <= 0:
        return
    iw, ih = img.get_size()
    if iw == 0 or ih == 0:
        return
    scale = min(rect.w / iw, rect.h / ih)
    new_size = (max(1, int(iw * scale)), max(1, int(ih * scale)))
    scaled = pygame.transform.smoothscale(img, new_size)
    dst = scaled.get_rect(center=rect.center)
    surface.blit(scaled, dst)

def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> List[str]:
    words = (text or "").split()
    lines: List[str] = []
    line: List[str] = []
    for w in words:
        test = (" ".join(line + [w])).strip()
        if not line or font.size(test)[0] <= max_width:
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


class ProfileCard:
    """Cached card surface with animal data (image left, key-value on right)."""
    def __init__(self, data: Dict[str, Any]):
        """
        data keys expected (flexible):
          species (str), epoch (str), place (str), time/time_mya/mya (str|float), image (path)
        """
        self.data = data
        self.thumb = safe_load(data.get("image", ""))
        self._cached: Optional[Tuple[pygame.Surface, Tuple[int,int]]] = None  # (surface, (w,h))

    def _get_time_value(self) -> str:
        # try common keys
        for key in ("time", "time_mya", "mya", "Time", "TIME"):
            if key in self.data and self.data[key] not in (None, ""):
                v = self.data[key]
                if isinstance(v, (int, float)):
                    return f"{v} MYA"
                s = str(v)
                return s if "mya" in s.lower() or "my" in s.lower() else (s + " MYA")
        return "—"

    def measure_height(self, width: int, fonts: Dict[str, pygame.font.Font]) -> int:
        """Compute needed card height for given width so we don't clip the 'Time' line."""
        FONT_TITLE = fonts["title"]
        FONT_MD    = fonts["md"]
        pad = 16
        img_w = int(width * 0.28)
        content_w = width - (pad + img_w + 14 + pad)
        label_w = 110
        line_gap = 6

        # Title height
        title_h = FONT_TITLE.get_height()

        # Wrap three fields
        epoch_lines = wrap_text(str(self.data.get("epoch", "—")), FONT_MD, max(1, content_w - label_w))
        place_lines = wrap_text(str(self.data.get("place", "—")), FONT_MD, max(1, content_w - label_w))
        time_lines  = wrap_text(self._get_time_value(),           FONT_MD, max(1, content_w - label_w))

        kv_block_h = (
            max(FONT_MD.get_height(), FONT_MD.get_height()) +   # "Epoch:" + first line
            (len(epoch_lines)-1) * (FONT_MD.get_height()+line_gap) + line_gap +
            max(FONT_MD.get_height(), FONT_MD.get_height()) +
            (len(place_lines)-1) * (FONT_MD.get_height()+line_gap) + line_gap +
            max(FONT_MD.get_height(), FONT_MD.get_height()) +
            (len(time_lines)-1) * (FONT_MD.get_height()+line_gap)
        )

        # image column imposes a min height
        img_h_min = 140
        # total: pads + title + spacing + kv + pads
        total = pad + title_h + 8 + kv_block_h + pad
        return max(total, img_h_min)

    def _render_card_surface(self, size: Tuple[int,int], fonts: Dict[str, pygame.font.Font]) -> pygame.Surface:
        w, h = size
        FONT_TITLE = fonts["title"]
        FONT_MD    = fonts["md"]
        FONT_SM    = fonts["sm"]

        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        # background
        draw_round_rect(surf, surf.get_rect(), (32, 38, 56), radius=14)
        pygame.draw.rect(surf, (70, 90, 120), surf.get_rect(), 2, border_radius=14)

        pad = 16
        img_rect = pygame.Rect(pad, pad, int(w * 0.28), h - pad * 2)
        content = pygame.Rect(img_rect.right + 14, pad, w - (img_rect.right + 14) - pad, h - pad * 2)

        # image
        if self.thumb:
            blit_image_fit(surf, self.thumb, img_rect)
        else:
            # placeholder
            pygame.draw.rect(surf, (60, 66, 86), img_rect, border_radius=10)
            ph = FONT_SM.render("No Image", True, (180, 190, 210))
            surf.blit(ph, ph.get_rect(center=img_rect.center))

        # text
        y = content.y
        title = FONT_TITLE.render(str(self.data.get("species", "Unknown")), True, (235, 240, 252))
        surf.blit(title, (content.x, y))
        y += title.get_height() + 8

        label_color = (180, 195, 220)
        value_color = (225, 232, 246)
        label_w = 110
        line_gap = 6
        bottom_limit = content.bottom

        def draw_kv(label: str, value: str, y: int) -> int:
            lab = FONT_MD.render(label, True, label_color)
            first_line_w = max(0, content.w - label_w)
            val_lines = wrap_text(str(value), FONT_MD, first_line_w) or [""]
            if y + lab.get_height() > bottom_limit:
                return bottom_limit
            surf.blit(lab, (content.x, y))
            v0 = FONT_MD.render(val_lines[0], True, value_color)
            surf.blit(v0, (content.x + label_w, y))
            y2 = y + v0.get_height() + line_gap
            for ln in val_lines[1:]:
                if y2 + v0.get_height() > bottom_limit:
                    ell = FONT_MD.render("…", True, value_color)
                    surf.blit(ell, (content.x + label_w, bottom_limit - ell.get_height()))
                    return bottom_limit
                v = FONT_MD.render(ln, True, value_color)
                surf.blit(v, (content.x + label_w, y2))
                y2 += v.get_height() + line_gap
            return y2

        y = draw_kv("Epoch:", str(self.data.get("epoch", "—")), y)
        y = draw_kv("Place:", str(self.data.get("place", "—")), y)
        y = draw_kv("Time:",  self._get_time_value(), y)

        # cache and return
        self._cached = (surf, size)
        return surf

    def get_surface(self, size: Tuple[int,int], fonts: Dict[str, pygame.font.Font]) -> pygame.Surface:
        if self._cached and self._cached[1] == size:
            return self._cached[0]
        return self._render_card_surface(size, fonts)

class UserProfileDisplay(BaseDisplay):
    CAPTION = TITLE

    def __init__(self, screen: pygame.Surface, background_path: Optional[str] = None,
                 user: Optional[Dict[str, Any]] = None, animals: Optional[List[Dict[str, Any]]] = None):
        super().__init__(screen, background_path)
        # Fonts
        self.FONT_HERO  = _font(46, bold=True)
        self.FONT_SUB   = _font(22)
        self.FONT_TITLE = _font(26, bold=True)
        self.FONT_MD    = _font(20)
        self.FONT_SM    = _font(16)
        self._fonts_map = {"title": self.FONT_TITLE, "md": self.FONT_MD, "sm": self.FONT_SM}

        # UI
        W, H = self.screen.get_width(), self.screen.get_height()
        self.x_btn = IconButton(W - 20, 20, size=36)

        # Data
        self.user = user or {"username": "Player", "coins": 0}
        # If no animals provided, show a small stub list
        self.animals: List[Dict[str, Any]] = animals or [
            {"species": "Triceratops", "epoch": "Late Cretaceous", "place": "North America", "time": "68–66 MYA", "image": ""},
            {"species": "Smilodon", "epoch": "Pleistocene", "place": "Americas", "time": "2.5–0.01 MYA", "image": ""},
            {"species": "Megalodon", "epoch": "Neogene", "place": "Global Oceans", "time": "23–3.6 MYA", "image": ""},
        ]
        self.cards: List[ProfileCard] = [ProfileCard(a) for a in self.animals]

        # Scrolling / inertia
        self.scroll_y: float = 0.0
        self.scroll_v: float = 0.0  # px/sec
        self.header_top = int(H * 0.10)
        self.header_gap = 6

        # layout cache
        self.viewport_rect: Optional[pygame.Rect] = None
        self.content_height: int = 0

    # ---------- BaseDisplay hooks ----------
    def on_event(self, event: pygame.event.Event):
        # Close & back
        if self.x_btn.clicked(event):
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        # Scroll input
        if event.type == pygame.MOUSEWHEEL:
            # positive y = up
            self.scroll_v -= event.y * 720  # strong impulse
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.scroll_v -= 520
            elif event.key == pygame.K_DOWN:
                self.scroll_v += 520
            elif event.key == pygame.K_PAGEUP:
                self.scroll_v -= 1500
            elif event.key == pygame.K_PAGEDOWN:
                self.scroll_v += 1500
            elif event.key == pygame.K_HOME:
                self.scroll_y = 0.0; self.scroll_v = 0.0
            elif event.key == pygame.K_END:
                # jump to bottom; compute from current viewport
                if self.viewport_rect:
                    max_scroll = max(0, self.content_height - self.viewport_rect.h)
                    self.scroll_y = float(max_scroll); self.scroll_v = 0.0

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            running = False
        if keys[pygame.K_i]:
            res = route_to_instructions(self.background_path, self.screen)
        

    def update(self, dt_ms: int):
        # Integrate inertia
        self.scroll_y += (self.scroll_v * dt_ms) / 1000.0
        # Damping (exponential wrt frame time)
        damping = 0.86 ** (dt_ms / 16.0)
        self.scroll_v *= damping

        # Clamp
        if self.viewport_rect:
            max_scroll = max(0, self.content_height - self.viewport_rect.h)
            if self.scroll_y < 0.0:
                self.scroll_y = 0.0
                self.scroll_v = 0.0
            elif self.scroll_y > max_scroll:
                self.scroll_y = float(max_scroll)
                self.scroll_v = 0.0

    def draw_content(self, surface: pygame.Surface):
        W, H = surface.get_width(), surface.get_height()

        # Header
        username = str(self.user.get("username", "Player"))
        coins = int(self.user.get("coins", 0))
        title = self.FONT_HERO.render(username, True, (255, 255, 255))
        subtitle = self.FONT_SUB.render(f"Coins Left: {coins}", True, (220, 230, 245))
        surface.blit(title, title.get_rect(midtop=(W // 2, self.header_top)))
        surface.blit(subtitle, subtitle.get_rect(midtop=(W // 2, self.header_top + title.get_height() + self.header_gap)))

        # Layout content viewport
        top_margin = int(H * 0.26)
        bottom_margin = 56
        left = int(W * 0.12)
        right = W - left
        width = right - left
        height = H - top_margin - bottom_margin
        self.viewport_rect = pygame.Rect(left, top_margin, width, height)

        # Build content surface based on cards
        widths = width
        # First pass: measure per-card heights
        heights = []
        for c in self.cards:
            h_needed = c.measure_height(width, self._fonts_map)
            heights.append(h_needed)
        total_h = sum(heights) + (len(self.cards)-1) * 16  # gap
        self.content_height = total_h
        content_surf = pygame.Surface((width, max(1, total_h)), pygame.SRCALPHA)

        # Second pass: render
        y_off = 0
        for c, ch in zip(self.cards, heights):
            surf_card = c.get_surface((width, ch), self._fonts_map)
            content_surf.blit(surf_card, (0, y_off))
            y_off += ch + 16

        # Blit viewport with scroll
        clip = pygame.Surface((width, height), pygame.SRCALPHA)
        clip.blit(content_surf, (0, -int(self.scroll_y)))
        surface.blit(clip, self.viewport_rect.topleft)

        clip = pygame.Surface((width, height), pygame.SRCALPHA)
        clip.blit(content_surf, (0, -int(self.scroll_y)))
        surface.blit(clip, self.viewport_rect.topleft)

        # Simple scrollbar
        max_scroll = max(0, self.content_height - self.viewport_rect.h)
        if max_scroll > 0:
            bar_area = pygame.Rect(self.viewport_rect.right + 6, self.viewport_rect.top, 8, self.viewport_rect.height)
            pygame.draw.rect(surface, (60, 80, 110), bar_area, border_radius=4)
            thumb_h = max(24, int(bar_area.h * (self.viewport_rect.h / (self.content_height + 0.001))))
            thumb_y = int(bar_area.y + (bar_area.h - thumb_h) * (self.scroll_y / max_scroll))
            pygame.draw.rect(surface, (200, 220, 245), (bar_area.x, thumb_y, bar_area.w, thumb_h), border_radius=4)

        # Footer hint & X
        hint = self.FONT_SM.render("Scroll: Mouse Wheel / ↑ ↓ / PgUp PgDn • ESC to go back", True, (210, 220, 235))
        surface.blit(hint, hint.get_rect(midbottom=(W // 2, H - 8)))
        self.x_btn.draw(surface)

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1000, 640))
    pygame.display.set_caption(TITLE)
    # TODO: replace with real user data
    animals = [
        {"species": "Triceratops", "epoch": "Late Cretaceous", "place": "North America", "time": "68–66 MYA", "image": ""},
        {"species": "Smilodon", "epoch": "Pleistocene", "place": "Americas", "time": "2.5–0.01 MYA", "image": ""},
        {"species": "Megalodon", "epoch": "Neogene", "place": "Global Oceans", "time": "23–3.6 MYA", "image": ""},
    ]
    disp = UserProfileDisplay(screen, background_path="frontend/assets/login4.jpg",
                              user={"username": "Ash", "coins": 12},
                              animals=animals)
    disp.run()
    pygame.quit()
