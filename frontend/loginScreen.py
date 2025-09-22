# loginScreen.py
import os
import sys
import pygame
import time
# ---- External modules you provide ----
# backend.py should define:
#   check_user(username) -> (exists: bool, info: dict|None)
#   add_new_user(username) -> dict  (optional but used here)
from backend.utils import *
# instructionScreen.py should define:
#   show_instructions(screen, background) -> None
import frontend.instructionScreen as instructionScreen
from backend.entities import *

# ---------------- Config ---------------- #
SCREEN_W, SCREEN_H = 900, 600
BACKGROUND_PATH = "frontend/assets/login3.png"   # put your image in the same folder or change this path
TITLE = "EONS"

# -------------- Pygame Setup ------------- #
pygame.init()
pygame.display.set_caption(TITLE)
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
clock = pygame.time.Clock()

# -------------- Assets / Fonts ----------- #
# def load_background():
#     if os.path.exists(BACKGROUND_PATH):
#         img = pygame.image.load(BACKGROUND_PATH).convert()
#         return pygame.transform.smoothscale(img, (SCREEN_W, SCREEN_H))
    
#     # fallback color
#     surf = pygame.Surface((SCREEN_W, SCREEN_H))
#     surf.fill((28, 32, 48))
#     return surf

def load_background():
    if os.path.exists(BACKGROUND_PATH):
        img = pygame.image.load(BACKGROUND_PATH).convert()
        img = pygame.transform.smoothscale(img, (SCREEN_W, SCREEN_H))
        return lighten_alpha(img, alpha=90)  # 0..255 (higher = lighter)
    # fallback
    surf = pygame.Surface((SCREEN_W, SCREEN_H))
    surf.fill((28, 32, 48))
    return surf

def lighten_alpha(surface, alpha=80):
    """Lighten by alpha-blending towards white."""
    out = surface.copy()
    overlay = pygame.Surface(out.get_size(), pygame.SRCALPHA)
    overlay.fill((255, 255, 255, alpha))
    out.blit(overlay, (0, 0))
    return out

BACKGROUND = load_background()

def font(name="Georgia", size=28, bold=False):
    f = pygame.font.SysFont(name, size, bold=bold)
    return f if f is not None else pygame.font.Font(None, size)

def draw_round_rect(surface, rect, color, radius=18, width=0):
    pygame.draw.rect(surface, color, rect, width=width, border_radius=radius)

FONT_XL = font(name="Georgia", size=100, bold=True)
FONT_LG = font(size=32, bold=True)
FONT_MD = font(name="Comic Sans MS", size=24, bold=True)
FONT_SM = font(name="Comic Sans MS", size=21, bold=True)

W, H = screen.get_width(), screen.get_height()

# -------------- UI Widgets ---------------- #
# Top-right X
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

x_btn = IconButton(W - 20, 20, size=36)

class InputBox:
    def __init__(self, x, y, w, h, max_len=20):
        self.rect = pygame.Rect(x, y, w, h)
        self.active = False
        self.text = ""
        self.max_len = max_len

    def handle_event(self, event):
        submitted = None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                submitted = self.text.strip()
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if event.unicode and len(self.text) < self.max_len and not event.key in (pygame.K_TAB,):
                    self.text += event.unicode
        return submitted

    def draw(self, surface):
        # Box
        border = 3 if self.active else 2
        pygame.draw.rect(surface, (240, 240, 240), self.rect, border, border_radius=10)
        # Text
        txt = FONT_MD.render(self.text or "", True, (0, 0, 0))
        surface.blit(txt, (self.rect.x + 10, self.rect.y + self.rect.height//2 - txt.get_height()//2))

class Button:
    def __init__(self, x, y, w, h, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label

    def draw(self, surface):
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        base = (70, 110, 160) if not hover else (90, 140, 200)
        pygame.draw.rect(surface, base, self.rect, border_radius=12)
        pygame.draw.rect(surface, (15, 25, 40), self.rect, 2, border_radius=12)
        t = FONT_MD.render(self.label, True, (255, 255, 255))
        surface.blit(t, t.get_rect(center=self.rect.center))

    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)

# -------------- Helpers ------------------- #
def draw_center_text(surface, text, font, color, y):
    t = font.render(text, True, color)
    surface.blit(t, t.get_rect(center=(SCREEN_W // 2, y)))

def show_user_info(username: str, player: Player, new_user=False):
    """
    Display a modal-like overlay with user info for existing players.
    Returns when user presses any key or after short timeout.
    """
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))

    # Render once
    if new_user:
        msg_title = f"New Player '{username}'"
    else:
        msg_title = f"Welcome Back '{username}'"
    print("info - ", player)
    timeout_ms = 1000
    start = pygame.time.get_ticks()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                waiting = False

        if pygame.time.get_ticks() - start > timeout_ms:
            waiting = False

        screen.blit(BACKGROUND, (0, 0))
        screen.blit(overlay, (0, 0))
        draw_center_text(screen, msg_title, FONT_LG, (0, 0, 0), SCREEN_H//2 - 40)

        y = SCREEN_H // 2 + 10
        # if lines:
        #     for ln in lines[:6]:  # keep tidy
        #         draw_center_text(screen, ln, FONT_MD, (230, 240, 255), y)
        #         y += 28
        # else:
        #     draw_center_text(screen, "Loading user info...", FONT_MD, (230, 240, 255), y)

        pygame.display.flip()
        clock.tick(60)



# def route_to_instructions():
#     """
#     Hand off to the instructions screen. Prefers the BaseDisplay version
#     (InstructionDisplay) and falls back to legacy instructionScreen.
#     Expects module-level `screen` and `BACKGROUND`.
#     """
#     try:
#         # Prefer the BaseDisplay-based screen if available
#         from frontend.instructionScreen import InstructionDisplay  # adjust import path if needed

#         # If BACKGROUND is a path string, pass it as background_path
#         bg_path = BACKGROUND if isinstance(BACKGROUND, str) else None
#         disp = InstructionDisplay(screen, background_path=bg_path)

#         # If BACKGROUND is already a Surface, reuse it on the display instance
#         if bg_path is None:
#             try:
#                 if isinstance(BACKGROUND, pygame.Surface):
#                     setattr(disp, "background", BACKGROUND)
#             except Exception:
#                 pass

#         result = disp.run()
#         return result

#     except Exception:
#         # Fallback to legacy function-based implementation
#         try:
#             import frontend.instructionScreen as instructionScreen  # adjust if your project uses a different path
#         except Exception:
#             import instructionScreen  # final fallback if it's in the same package
#         instructionScreen.show_instructions(screen, BACKGROUND)


# def route_to_instructions(background, screen):
#     # """
#     # Opens the instructions screen modally and returns its result ("back"/"next"/"quit"/None).
#     # Works with either the BaseDisplay InstructionDisplay or legacy instructionScreen.
#     # """
#         # Prefer BaseDisplay version if present
#     from frontend.instructionScreen import InstructionDisplay
#     bg_path = background if isinstance(background, str) else None
#     disp = InstructionDisplay(screen, background_path=bg_path)
#     if bg_path is None and background is not None:
#         # reuse the already-loaded Surface if you have one
#         try:
#             if isinstance(background, pygame.Surface):
#                 disp.background = background
#         except Exception:
#             pass
#     result = disp.run()
    # print("result - ", result)
    

    # Clear any stray clicks/keys so they don't leak into the caller
    # try:
    #     import pygame
    #     pygame.event.clear()
    # except Exception:
    #     pass

    # return result


# -------------- Main Loop ---------------- #
def main():
    input_box = InputBox(SCREEN_W//2 - 170, SCREEN_H//2 - 10, 340, 48)
    enter_btn = Button(SCREEN_W//2 + 190, SCREEN_H//2 - 10, 120, 48, "Enter")

    message = ""     # transient feedback line
    msg_timer = 0    # ms remaining to show the message

    playerManager = PlayerManager("data/playerData.json")

    running = True
    while running:
        dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if x_btn.clicked(event):
                pygame.quit(); sys.exit()

            # Submit via Enter key while input active
            submitted = input_box.handle_event(event)

            # Submit via mouse click on Enter button
            if enter_btn.clicked(event):
                submitted = input_box.text.strip()

            if submitted is not None:
                username = submitted
                if not username:
                    message = "Please enter a username."
                    msg_timer = 1200
                else:
                    # exists, info = check_user(username)
                    player = playerManager.get_player(username.lower())
                    if player is not None:
                        # Existing user: show welcome + info
                        message = f"Welcome {username}"
                        msg_timer = 900
                        # (you can also pass this info to the next screen if needed)
                        show_user_info(username, player)
                        # After showing info, you might continue to a main menu or game.
                        # Here we simply clear the field so another login can be tested.
                        # input_box.text = ""
                    else:
                        # New user: add to backend and route to instructions
                        msg_timer = 900
                        player = Player(username=username.lower())
                        playerManager.save_player(player)
                        show_user_info(username, player, new_user=True)
                    res = route_to_mode(BACKGROUND, screen)

        # Decrement message timer
        if msg_timer > 0:
            msg_timer -= dt
            if msg_timer <= 0:
                message = ""

        # ---------- DRAW ---------- #
        screen.blit(BACKGROUND, (0, 0))

        draw_center_text(screen, "EONS", FONT_XL, (20, 69, 22), 120)
        draw_center_text(screen, "Gotta Unearth 'Em All!", FONT_SM, (20, 69, 22), 180)

        # Label
        label = FONT_MD.render("Username:", True, (0, 0, 0))
        screen.blit(label, (SCREEN_W//2 - 170, SCREEN_H//2 - 40))

        # Input and button
        input_box.draw(screen)
        enter_btn.draw(screen)
        x_btn.draw(screen)

        # Feedback line
        if message:
            draw_center_text(screen, message, FONT_MD, (0, 0, 0), SCREEN_H//2 + 60)

        # Footer hint
        draw_center_text(screen, "Press I for Instructions", FONT_SM, (0, 0, 0), SCREEN_H - 20)

        # ESC to quit (continuous keys)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            running = False
        if keys[pygame.K_i] and input_box.text.strip() == "":
            route_to_instructions(BACKGROUND, screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
