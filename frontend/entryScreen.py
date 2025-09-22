# entryTemplate.py â€" Entry screen implemented on BaseDisplay (corrected)
import pygame
import threading
from typing import Optional
from frontend.baseDisplay import BaseDisplay
from backend.utils import *
from backend.catchGameUtils import *

TITLE = "EONS Entry"

def font(name="arial", size=28, bold=False):
    f = pygame.font.SysFont(name, size, bold=bold)
    return f if f is not None else pygame.font.Font(None, size)

# -------------- UI Helpers & Widgets -------------- #
def draw_round_rect(surface, rect, color, radius=14, width=0):
    pygame.draw.rect(surface, color, rect, width=width, border_radius=radius)

def draw_shadow(surface, rect, radius=18, spread=10, alpha=90):
    shadow_rect = pygame.Rect(rect.x + 6, rect.y + 8, rect.w + spread, rect.h + spread)
    shadow = pygame.Surface((shadow_rect.w, shadow_rect.h), pygame.SRCALPHA)
    draw_round_rect(shadow, shadow.get_rect(), (0, 0, 0, alpha), radius)
    surface.blit(shadow, (shadow_rect.x, shadow_rect.y))

class IconButton:
    def __init__(self, right, top, size=36):
        self.size = size
        self.rect = pygame.Rect(right - size, top, size, size)

    def draw(self, surface):
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        base = (210, 70, 70) if hover else (160, 60, 60)
        draw_round_rect(surface, self.rect, base, radius=10)
        pygame.draw.rect(surface, (25, 20, 20), self.rect, 2, border_radius=10)
        cx, cy = self.rect.center
        pad = 9
        pygame.draw.line(surface, (255, 230, 230), (cx - pad, cy - pad), (cx + pad, cy + pad), 3)
        pygame.draw.line(surface, (255, 230, 230), (cx + pad, cy - pad), (cx - pad, cy + pad), 3)

    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)

class Button:
    def __init__(self, x, y, w, h, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label

    def draw(self, surface, font_obj=None):
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        base = (70, 110, 160) if not hover else (90, 140, 200)
        pygame.draw.rect(surface, base, self.rect, border_radius=12)
        pygame.draw.rect(surface, (15, 25, 40), self.rect, 2, border_radius=12)
        if font_obj is None:
            font_obj = font(size=24)
        t = font_obj.render(self.label, True, (255, 255, 255))
        surface.blit(t, t.get_rect(center=self.rect.center))

    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)

class InputBox:
    def __init__(self, x, y, w, h, placeholder="", max_len=64):
        self.rect = pygame.Rect(x, y, w, h)
        self.active = False
        self.text = ""
        self.placeholder = placeholder
        self.max_len = max_len

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return "SUBMIT"
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if event.unicode and len(self.text) < self.max_len and event.key not in (pygame.K_TAB,):
                    self.text += event.unicode
        return None

    def draw(self, surface, font_obj=None, color=(0,0,0)):
        if font_obj is None:
            font_obj = font(size=24)
        # Box
        border = 3 if self.active else 2
        pygame.draw.rect(surface, (242, 244, 250), self.rect, border, border_radius=10)
        # Text / placeholder
        shown = self.text if self.text else (self.placeholder or "")
        hint_color = (150, 155, 165) if not self.text else color
        t = font_obj.render(shown, True, hint_color)
        surface.blit(t, (self.rect.x + 10, self.rect.y + self.rect.height//2 - t.get_height()//2))

# -------------- Validation -------------- #
def validate_time(text: str) -> bool:
    try:
        v = float(text.strip())
        return v >= 0
    except Exception:
        return False

# -------------- Display -------------- #
class EntryDisplay(BaseDisplay):
    CAPTION = "Entry"

    def __init__(self, screen: pygame.Surface, background_path: Optional[str] = None):
        super().__init__(screen, background_path)
        self.FONT_HERO = font(size=44, bold=True)
        self.FONT_SUB  = font(size=22)
        self.FONT_MD   = font(size=24)
        self.FONT_SM   = font(size=18)
        self.FONT_LBL  = font(size=20, bold=True)

        W, H = self.screen.get_width(), self.screen.get_height()

        # Card layout
        card_w = 640
        card_h = 500
        self.card_rect = pygame.Rect((W - card_w)//2, (H - card_h)//2, card_w, card_h)

        # Widgets
        self.go_btn = Button(0, 0, 160, 54, "Start")
        self.x_btn = IconButton(W - 18, 18, size=36)

        # Input boxes (positions calculated in draw)
        self.place_box = InputBox(0, 0, int(self.card_rect.w * 0.75), 50, placeholder="Place (e.g., Sahara Desert)")
        self.time_box  = InputBox(0, 0, int(self.card_rect.w * 0.75), 50, placeholder="Time in million years ago (e.g., 66)", max_len=16)

        # Feedback
        self.message = ""
        self.msg_timer = 0  # ms

        # Loading animation and backend processing
        self.loading = False
        self.loading_dots = 0
        self.loading_timer = 0  # ms
        self.loading_stage = ""  # Current loading stage message
        self._finish_event = pygame.USEREVENT + 42
        
        # Backend results
        self.backend_thread = None
        self.backend_complete = False
        self.backend_error = None
        self.time_place_info = None
        self.time_place_animals = None
        self.time_background = None

        # Return payload
        self.result = None  # dict like {"place":"...", "time_mya": 66.0}

    # ---------- BaseDisplay hooks ----------
    def on_event(self, event: pygame.event.Event):
        # finish loading when backend completes
        if event.type == self._finish_event and self.loading:
            if self.backend_complete:
                pygame.time.set_timer(self._finish_event, 0)  # stop timer
                if self.backend_error:
                    # Show error and return to form
                    self.loading = False
                    self.message = f"Error: {self.backend_error}"
                    self.msg_timer = 3000
                else:
                    # Success - route to next screen
                    res = route_to_placeTimeInfo(self.background_path, self.screen, 
                                               self.time_place_info, self.time_place_animals, self.time_background)
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                return

        # Close via top-right X
        if self.x_btn.clicked(event) and not self.loading:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        # I -> instructions
        # if event.type == pygame.KEYDOWN and event.key == pygame.K_i and not self.loading and self.place_box.text.strip() == "" and  self.place_box.text.strip() == "":
        #     res = route_to_instructions(self.background_path, self.screen)
        #     return

        # ESC to go back
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and not self.loading:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        if self.loading:
            # ignore inputs while loading
            return

        # Start button
        start_enabled = bool(self.place_box.text.strip() and self.time_box.text.strip() and validate_time(self.time_box.text))
        if self.go_btn.clicked(event) and start_enabled:
            self._submit()
            return

        # Input handling
        submit = self.place_box.handle_event(event)
        if submit == "SUBMIT":
            self.time_box.active = True  # move focus
        sub2 = self.time_box.handle_event(event)
        if sub2 == "SUBMIT":
            if start_enabled:
                self._submit()
            else:
                self.message = "Fill both fields correctly before starting."
                self.msg_timer = 1500
        
    

    def update(self, dt_ms: int):
        # Feedback timer
        if self.msg_timer > 0:
            self.msg_timer -= dt_ms
            if self.msg_timer <= 0:
                self.message = ""

        # Loading animation dots
        if self.loading:
            self.loading_timer += dt_ms
            if self.loading_timer >= 400:
                self.loading_timer = 0
                self.loading_dots = (self.loading_dots + 1) % 4  # 0-3 dots

        # Check if backend processing is complete
        if self.loading and self.backend_complete:
            pygame.event.post(pygame.event.Event(self._finish_event))

    def draw_content(self, surface: pygame.Surface):
        # Loading overlay (draw first if active)
        if self.loading:
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((0,0,0,140))
            surface.blit(overlay, (0,0))
            
            # Loading text with animated dots
            dots = "." * self.loading_dots
            stage_text = self.loading_stage if self.loading_stage else "Loading Game"
            txt = stage_text + dots
            t_surf = self.FONT_HERO.render(txt, True, (245, 248, 255))
            
            # Progress indicator
            # progress_text = "Fetching data from backend..."
            # p_surf = self.FONT_MD.render(progress_text, True, (200, 210, 225))
            
            # Center both texts
            screen_center = self.screen.get_rect().center
            surface.blit(t_surf, t_surf.get_rect(center=(screen_center[0], screen_center[1] - 20)))
            # surface.blit(p_surf, p_surf.get_rect(center=(screen_center[0], screen_center[1] + 30)))
            return

        # Normal UI (only draw if not loading)
        # Center card UI
        draw_shadow(surface, self.card_rect, radius=20, spread=16, alpha=100)
        draw_round_rect(surface, self.card_rect, (238, 242, 250), radius=18)

        # Top-right close
        self.x_btn.draw(surface)

        # Heading and subheading
        heading = "Enter Details"
        sub = "Provide a Place and a Time to start the game."
        h_surf = self.FONT_HERO.render(heading, True, (30, 36, 48))
        s_surf = self.FONT_SUB.render(sub, True, (70, 85, 110))
        surface.blit(h_surf, (self.card_rect.left + 24, self.card_rect.top + 20))
        surface.blit(s_surf, (self.card_rect.left + 24, self.card_rect.top + 20 + h_surf.get_height() + 6))

        # Form layout
        left = self.card_rect.left + 24
        y = self.card_rect.top + 120
        field_w = int(self.card_rect.w * 0.75)

        # Place field
        lbl1 = self.FONT_LBL.render("Place", True, (60, 70, 90))
        surface.blit(lbl1, (left, y)); y += lbl1.get_height() + 8
        self.place_box.rect.topleft = (left, y)
        self.place_box.rect.size = (field_w, 50)
        self.place_box.draw(surface, self.FONT_MD); y += 50 + 14

        # Time field
        lbl2 = self.FONT_LBL.render("Time (million years ago)", True, (60, 70, 90))
        surface.blit(lbl2, (left, y)); y += lbl2.get_height() + 8
        self.time_box.rect.topleft = (left, y)
        self.time_box.rect.size = (field_w, 50)
        self.time_box.draw(surface, self.FONT_MD); y += 50 + 12

        # Validation message
        if self.message:
            warn = self.FONT_SM.render(self.message, True, (200, 60, 60))
            surface.blit(warn, warn.get_rect(midtop=(self.card_rect.centerx, y)))
            y += warn.get_height() + 10

        # Start button
        self.go_btn.rect.center = (self.card_rect.centerx, min(self.card_rect.bottom - 40, y + 28))
        start_enabled = bool(self.place_box.text.strip() and self.time_box.text.strip() and validate_time(self.time_box.text))
        if start_enabled:
            self.go_btn.draw(surface, self.FONT_MD)
        else:
            # Disabled look
            base = (150, 160, 175)
            pygame.draw.rect(surface, base, self.go_btn.rect, border_radius=12)
            pygame.draw.rect(surface, (120, 130, 145), self.go_btn.rect, 2, border_radius=12)
            t = self.FONT_MD.render(self.go_btn.label, True, (240, 240, 240))
            surface.blit(t, t.get_rect(center=self.go_btn.rect.center))

        # Footer hint
        footer = self.FONT_SM.render("Press ESC to go back", True, (80, 95, 120))
        surface.blit(footer, footer.get_rect(midbottom=(self.card_rect.centerx, self.card_rect.bottom - 8)))

    # ---------- Backend Processing ----------
    def _backend_worker(self, place: str, time_mya: float):
        """Run backend operations in a separate thread"""
        try:
            # Update loading stage
            self.loading_stage = "Initializing"
            
            # Create capture game info
            capture_game_info = CaptureGameInfo(place, time_mya)
            
            # Get time place info
            self.loading_stage = "Travelling to Past"
            self.time_place_info = capture_game_info.get_timeplace_info()
            
            # Generate game animals
            self.loading_stage = "Loading Game"
            self.time_place_animals = capture_game_info.generate_game_animals()
            self.time_background = capture_game_info.generate_background()
            
            # Mark as complete
            self.backend_complete = True
            self.loading_stage = "Complete"
            
        except Exception as e:
            # Handle any errors
            self.backend_error = str(e)
            self.backend_complete = True

    def _submit(self):
        # validate again
        if not self.place_box.text.strip():
            self.message = "Please enter a Place."
            self.msg_timer = 1500
            return
        if not self.time_box.text.strip():
            self.message = "Please enter Time (million years ago)."
            self.msg_timer = 1500
            return
        if not validate_time(self.time_box.text):
            self.message = "Time must be a non-negative number (e.g., 66)."
            self.msg_timer = 1800
            return

        # Start loading and backend processing
        self.loading = True
        self.loading_dots = 0
        self.loading_timer = 0
        self.loading_stage = "Starting"
        self.backend_complete = False
        self.backend_error = None
        
        # Set result
        place = self.place_box.text.strip()
        time_mya = float(self.time_box.text.strip())
        self.result = {"place": place, "time_mya": time_mya}
        
        # Start backend processing in a separate thread
        self.backend_thread = threading.Thread(
            target=self._backend_worker, 
            args=(place, time_mya)
        )
        self.backend_thread.daemon = True
        self.backend_thread.start()
        
        # Set up periodic check for completion
        pygame.time.set_timer(self._finish_event, 100, loops=0)  # Check every 100ms


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1000, 640))
    pygame.display.set_caption(TITLE)
    disp = EntryDisplay(screen, background_path="frontend/assets/login3.png")
    result = disp.run()
    print("Entry result:", getattr(disp, "result", None))
    pygame.quit()