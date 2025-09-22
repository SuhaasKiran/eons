# frontend/pokemon_main.py â€" Animal Explorer (BaseDisplay)
import math
import random
import pygame
from typing import Optional, Tuple, List, Dict
from backend.utils import *

# Robust import for BaseDisplay
try:
    from frontend.baseDisplay import BaseDisplay
except Exception:
    from baseDisplay import BaseDisplay  # fallback if project structure differs

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (76, 175, 80)
BLUE = (33, 150, 243)
LIGHT_BLUE = (100, 181, 246)
YELLOW = (255, 235, 59)
RED = (244, 67, 54)
PURPLE = (156, 39, 176)
ORANGE = (255, 152, 0)
BROWN = (121, 85, 72)

# Game constants
PERSON_SIZE = 40
PERSON_SPEED = 4
ANIMAL_SIZE = 35
WIGGLE_DISTANCE = 100   # Distance at which animals start wiggles
INTERACTION_DISTANCE = 50  # Distance at which name appears and info can be shown

# Fallback animal info for unknown types
DEFAULT_ANIMAL_INFO = "A mysterious creature from an ancient time."

# Default animal colors for rendering unknown species
ANIMAL_COLORS = [GREEN, BLUE, RED, PURPLE, ORANGE, BROWN, YELLOW]

# ----------------- Entities ----------------- #
class Person:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.size = PERSON_SIZE
        self.speed = PERSON_SPEED
        self.rect = pygame.Rect(x - self.size//2, y - self.size//2, self.size, self.size)

        # Animation vars
        self.frames = self._create_frames()
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 150  # ms per frame
        self.is_moving = False
        self.image = self.frames[0]

    def _create_frames(self) -> List[pygame.Surface]:
        frames = []
        for i in range(2):  # idle & step
            surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            # Head
            pygame.draw.circle(surf, (255, 220, 177), (self.size//2, self.size//4), self.size//6)
            # Body
            body_rect = pygame.Rect(self.size//3, self.size//3, self.size//3, self.size//2)
            pygame.draw.rect(surf, (66, 133, 244), body_rect, border_radius=5)
            # Eyes
            pygame.draw.circle(surf, BLACK, (self.size//2 - 4, self.size//4 - 2), 2)
            pygame.draw.circle(surf, BLACK, (self.size//2 + 4, self.size//4 - 2), 2)
            # Arms
            pygame.draw.line(surf, (255, 220, 177), (self.size//3, self.size//2),
                             (self.size//5, self.size*2//3), 4)
            pygame.draw.line(surf, (255, 220, 177), (self.size*2//3, self.size//2),
                             (self.size*4//5, self.size*2//3), 4)
            # Legs (alternate on step)
            if i == 0:
                pygame.draw.line(surf, BROWN, (self.size//2 - 6, self.size*5//6), (self.size//2 - 14, self.size), 4)
                pygame.draw.line(surf, BROWN, (self.size//2 + 6, self.size*5//6), (self.size//2 + 14, self.size), 4)
            else:
                pygame.draw.line(surf, BROWN, (self.size*2//5, self.size*5//6), (self.size//2, self.size), 4)
                pygame.draw.line(surf, BROWN, (self.size*3//5, self.size*5//6), (self.size//4, self.size), 4)
            frames.append(surf)
        return frames

    def update(self, keys, dt_ms: int, bounds: Tuple[int, int]):
        """Move and animate based on input; clamp to bounds (width,height)."""
        w, h = bounds
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:  dx = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx =  self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:    dy = -self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:  dy =  self.speed

        self.is_moving = (dx != 0 or dy != 0)

        # animation
        if self.is_moving:
            self.animation_timer += dt_ms
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                self.image = self.frames[self.current_frame]
        else:
            self.current_frame = 0
            self.image = self.frames[0]

        # move & clamp
        self.x = max(self.size//2, min(w - self.size//2, self.x + dx))
        self.y = max(self.size//2, min(h - self.size//2, self.y + dy))
        self.rect.topleft = (self.x - self.size//2, self.y - self.size//2)

    def draw(self, screen: pygame.Surface):
        screen.blit(self.image, (self.x - self.size//2, self.y - self.size//2))


class Animal:
    def __init__(self, x: int, y: int, species_name: str, description: str, image_name: Optional[str] = None, relative_size: float = 1.0):
        self.x = x
        self.y = y
        self.original_x = x
        self.original_y = y
        self.size = ANIMAL_SIZE
        self.species_name = species_name
        self.description = description
        self.image_name = image_name
        self.relative_size = relative_size  # could be adjusted based on species
        self.rect = pygame.Rect(x - self.size//2, y - self.size//2, self.size, self.size)
        self.info_timer = 0  
        self.info_duration = 5000

        # Animation / proximity
        self.wiggle_time = 0.0
        self.wiggle_intensity = 0.0
        self.target_wiggle_intensity = 0.0
        self.is_wiggling = False

        # UI
        self.show_name = False
        self.name_font = pygame.font.Font(None, 20)
        self.name_surface: Optional[pygame.Surface] = None
        self.name_box_alpha = 0

        # Info box
        self.info_font = pygame.font.Font(None, 22)
        self.show_info = False  # toggled via 'P' nearby

        # Render image & name
        self.image = self._generate_image()
        self.name_surface = self.name_font.render(self.species_name, True, BLACK)

    def _generate_image(self) -> pygame.Surface:
        """Generate animal image. Try to load from file first, fallback to procedural generation."""
        surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        
        # Try to load from image file if image_name is provided
        if self.image_name:
            try:
                # Try to load the actual image file
                loaded_img = pygame.image.load(f"frontend/assets/animals/{self.image_name}")
                scaled_img = pygame.transform.scale(loaded_img, (self.size, self.size))
                return scaled_img
            except Exception:
                # If loading fails, continue to procedural generation
                pass
        
        # Procedural generation based on species name or fallback
        species_lower = self.species_name.lower()
        
        # Use a hash of the species name to get consistent colors/shapes
        species_hash = hash(species_lower) % len(ANIMAL_COLORS)
        primary_color = ANIMAL_COLORS[species_hash]
        secondary_color = ANIMAL_COLORS[(species_hash + 2) % len(ANIMAL_COLORS)]
        
        # Generate based on known patterns or create generic creature
        # TODO: Using static images for now. Implmenet generating image dynamically
        if "cat" in species_lower or "feline" in species_lower:
            self._draw_cat_like(surf, primary_color, secondary_color)
        elif "dog" in species_lower or "canine" in species_lower or "wolf" in species_lower:
            self._draw_dog_like(surf, primary_color, secondary_color)
        elif "bird" in species_lower or "avian" in species_lower or species_lower.endswith("us") and "bird" in self.description.lower():
            self._draw_bird_like(surf, primary_color, secondary_color)
        elif "fish" in species_lower or "aquatic" in self.description.lower():
            self._draw_fish_like(surf, primary_color, secondary_color)
        elif "rabbit" in species_lower or "hare" in species_lower:
            self._draw_rabbit_like(surf, primary_color, secondary_color)
        elif "reptile" in species_lower or "lizard" in species_lower or "dinosaur" in species_lower:
            self._draw_reptile_like(surf, primary_color, secondary_color)
        else:
            # Generic creature
            self._draw_generic_creature(surf, primary_color, secondary_color)
        
        return surf

    def _draw_cat_like(self, surf: pygame.Surface, primary: Tuple[int,int,int], secondary: Tuple[int,int,int]):
        # ears
        pygame.draw.polygon(surf, primary, [(10, 10), (16, 2), (22, 10)])
        pygame.draw.polygon(surf, primary, [(self.size-22, 10), (self.size-16, 2), (self.size-10, 10)])
        # head
        pygame.draw.circle(surf, primary, (self.size//2, self.size//2), self.size//3)
        # eyes & nose
        pygame.draw.circle(surf, WHITE, (self.size//2 - 6, self.size//2 - 4), 3)
        pygame.draw.circle(surf, WHITE, (self.size//2 + 6, self.size//2 - 4), 3)
        pygame.draw.polygon(surf, secondary, [(self.size//2 - 3, self.size//2 + 2),
                                           (self.size//2 + 3, self.size//2 + 2),
                                           (self.size//2, self.size//2 + 6)])

    def _draw_dog_like(self, surf: pygame.Surface, primary: Tuple[int,int,int], secondary: Tuple[int,int,int]):
        pygame.draw.circle(surf, primary, (self.size//2, self.size//2), self.size//3)
        pygame.draw.circle(surf, BLACK, (self.size//2 - 5, self.size//2 - 2), 2)
        pygame.draw.circle(surf, BLACK, (self.size//2 + 5, self.size//2 - 2), 2)
        pygame.draw.circle(surf, secondary, (self.size//2 - 12, self.size//2 - 8), 6)
        pygame.draw.circle(surf, secondary, (self.size//2 + 12, self.size//2 - 8), 6)

    def _draw_bird_like(self, surf: pygame.Surface, primary: Tuple[int,int,int], secondary: Tuple[int,int,int]):
        pygame.draw.ellipse(surf, primary, (10, 8, self.size-20, self.size-14))
        pygame.draw.circle(surf, primary, (self.size//2 + 5, self.size//3), self.size//6)
        pygame.draw.polygon(surf, secondary, [(self.size//2 + 10, self.size//3),
                                           (self.size//2 + 18, self.size//3 - 2),
                                           (self.size//2 + 18, self.size//3 + 2)])
        pygame.draw.circle(surf, BLACK, (self.size//2 + 8, self.size//3 - 2), 2)

    def _draw_fish_like(self, surf: pygame.Surface, primary: Tuple[int,int,int], secondary: Tuple[int,int,int]):
        pygame.draw.ellipse(surf, primary, (8, 12, self.size-16, self.size-20))
        pygame.draw.polygon(surf, primary, [(8, self.size//2), (0, self.size//2 - 6), (0, self.size//2 + 6)])
        pygame.draw.circle(surf, primary, (self.size*3//4, self.size//2), self.size//6)
        pygame.draw.circle(surf, WHITE, (self.size*3//4, self.size//2 - 2), 3)
        pygame.draw.circle(surf, BLACK, (self.size*3//4 + 1, self.size//2 - 2), 2)

    def _draw_rabbit_like(self, surf: pygame.Surface, primary: Tuple[int,int,int], secondary: Tuple[int,int,int]):
        pygame.draw.ellipse(surf, primary, (self.size//4, self.size//3, self.size//2, self.size//2))
        pygame.draw.rect(surf, primary, (self.size//2 - 2, 4, 4, self.size//3))
        pygame.draw.rect(surf, primary, (self.size//2 + 6, 4, 4, self.size//3))
        pygame.draw.circle(surf, BLACK, (self.size//2 - 3, self.size//2), 2)
        pygame.draw.circle(surf, BLACK, (self.size//2 + 3, self.size//2), 2)

    def _draw_reptile_like(self, surf: pygame.Surface, primary: Tuple[int,int,int], secondary: Tuple[int,int,int]):
        # Elongated body
        pygame.draw.ellipse(surf, primary, (6, 10, self.size-12, self.size-18))
        # Head
        pygame.draw.circle(surf, primary, (self.size*3//4, self.size//2), self.size//5)
        # Eyes
        pygame.draw.circle(surf, secondary, (self.size*3//4 - 3, self.size//2 - 2), 2)
        pygame.draw.circle(surf, secondary, (self.size*3//4 + 3, self.size//2 - 2), 2)
        # Spikes or scales
        for i in range(3):
            x = self.size//4 + i * self.size//6
            pygame.draw.polygon(surf, secondary, [(x, self.size//3), (x+3, self.size//4), (x+6, self.size//3)])

    def _draw_generic_creature(self, surf: pygame.Surface, primary: Tuple[int,int,int], secondary: Tuple[int,int,int]):
        # Generic blob creature with eyes
        pygame.draw.circle(surf, primary, (self.size//2, self.size//2), self.size//3)
        pygame.draw.circle(surf, BLACK, (self.size//2 - 5, self.size//2 - 3), 2)
        pygame.draw.circle(surf, BLACK, (self.size//2 + 5, self.size//2 - 3), 2)
        # Add some unique features based on the secondary color
        pygame.draw.circle(surf, secondary, (self.size//2, self.size//2 + 8), 3)

    def update(self, person: Person, dt: float):
        """Update proximity wiggle & name fade based on distance to person."""
        dist = math.hypot(self.x - person.x, self.y - person.y)
        if dist <= WIGGLE_DISTANCE:
            self.is_wiggling = True
            self.target_wiggle_intensity = min(1.0, (WIGGLE_DISTANCE - dist) / WIGGLE_DISTANCE)
        else:
            self.is_wiggling = False
            self.target_wiggle_intensity = 0.0

        # Smooth intensity
        speed = 2.0
        self.wiggle_intensity += (self.target_wiggle_intensity - self.wiggle_intensity) * min(1.0, dt * speed)

        # Wiggle motion
        if self.is_wiggling:
            self.wiggle_time += dt * 10.0
            offset_x = math.sin(self.wiggle_time) * 2 * self.wiggle_intensity
            offset_y = math.cos(self.wiggle_time * 1.2) * 2 * self.wiggle_intensity
            self.x = self.original_x + offset_x
            self.y = self.original_y + offset_y
        else:
            self.wiggle_time = 0.0
            self.x = self.original_x
            self.y = self.original_y

        # Name fade near person
        if dist <= INTERACTION_DISTANCE:
            self.show_name = True
            self.name_box_alpha = min(255, self.name_box_alpha + int(dt * 400))
        else:
            self.show_name = False
            self.name_box_alpha = max(0, self.name_box_alpha - int(dt * 400))

        # Update rect
        self.rect.topleft = (int(self.x - self.size//2), int(self.y - self.size//2))

        if self.show_info and self.info_timer > 0:
            self.info_timer -= dt * 1000  
            if self.info_timer <= 0:
                self.show_info = False
                self.info_timer = 0

    def draw_info_box(self, screen: pygame.Surface):
        if not self.show_info:
            return
        
        # Split description by newlines and wrap long lines
        lines = []
        for line in self.description.split('\n'):
            if len(line) > 60:  # Wrap long lines
                words = line.split()
                current_line = []
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    if len(test_line) <= 60:
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))
                        current_line = [word]
                if current_line:
                    lines.append(' '.join(current_line))
            else:
                lines.append(line)
        
        line_surfs = [self.info_font.render(line, True, BLACK) for line in lines]
        box_w = max(s.get_width() for s in line_surfs) + 20
        box_h = sum(s.get_height() for s in line_surfs) + 15
        box_x = int(self.x - box_w / 2)
        box_y = int(self.y - self.size//2 - box_h - 10)
        
        # Clamp into screen bounds
        sw, sh = screen.get_size()
        box_x = max(10, min(sw - box_w - 10, box_x))
        box_y = max(10, min(sh - box_h - 10, box_y))
        
        # Draw box
        panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        panel.fill((255, 255, 255, 230))
        screen.blit(panel, (box_x, box_y))
        pygame.draw.rect(screen, (0, 0, 0, 160), (box_x, box_y, box_w, box_h), 2, border_radius=6)
        
        # Draw text lines
        y = box_y + 8
        for s in line_surfs:
            screen.blit(s, (box_x + 10, y))
            y += s.get_height() + 2

    def draw(self, screen: pygame.Surface):
        screen.blit(self.image, (int(self.x - self.size//2), int(self.y - self.size//2)))
        # Name box
        if self.name_box_alpha > 10 and self.name_surface:
            bw = self.name_surface.get_width() + 10
            bh = self.name_surface.get_height() + 6
            bx = int(self.x - bw // 2)
            by = int(self.y - self.size//2 - bh - 5)
            box = pygame.Surface((bw, bh), pygame.SRCALPHA)
            box.fill((255, 255, 255, int(self.name_box_alpha * 0.9)))
            text = self.name_surface.copy()
            text.set_alpha(int(self.name_box_alpha))
            screen.blit(box, (bx, by))
            pygame.draw.rect(screen, (0, 0, 0, int(self.name_box_alpha * 0.5)), (bx, by, bw, bh), 2, border_radius=6)
            screen.blit(text, (bx + 5, by + 3))
        # Info panel
        self.draw_info_box(screen)


# --------------- Display (BaseDisplay) --------------- #
class PokemonDisplay(BaseDisplay):
    CAPTION = "Animal Explorer"

    def __init__(self, screen: pygame.Surface, background_path: Optional[str] = "frontend/assets/swamp.png", animals: Optional[Dict[str, Dict[str, str]]] = None):
        super().__init__(screen, background_path)
        w, h = self.screen.get_size()

        # Prepare tiled background (overlays base background)
        # self.bg_tiled = self._create_tiled_background_img(background_path)
        self.bg_tiled = None
        self.background_path = background_path
        # Entities
        self.person = Person(w // 2, h // 2)
        self.animals: List[Animal] = []
        
        # Create animals from provided data or use defaults
        if animals:
            species_list = list(animals.keys())
            # Limit to a reasonable number for display
            max_animals = min(len(species_list), 8)
            selected_species = random.sample(species_list, max_animals) if len(species_list) > max_animals else species_list
            
            for species_name in selected_species:
                animal_data = animals[species_name]
                description = animal_data.get("description", DEFAULT_ANIMAL_INFO)
                image_name = animal_data.get("image_name")
                
                # Find a good position
                for _try in range(100):  # Prevent infinite loop
                    x = random.randint(ANIMAL_SIZE, w - ANIMAL_SIZE)
                    y = random.randint(ANIMAL_SIZE, h - ANIMAL_SIZE)
                    # Don't place too close to person
                    if math.hypot(x - self.person.x, y - self.person.y) < 100:
                        continue
                    # Don't place too close to other animals
                    if any(math.hypot(x - a.x, y - a.y) < 80 for a in self.animals):
                        continue
                    break
                
                self.animals.append(Animal(x, y, species_name, description, image_name))
        else:
            # Fallback to default animals if none provided
            default_animals = {
                "Cat": {"description": "Cats are skilled predators and can hear frequencies too high or low for humans.", "image_name": None},
                "Dog": {"description": "Dogs have a sense of smell that is thousands of times more sensitive than a human's.", "image_name": None},
                "Rabbit": {"description": "A rabbit's teeth never stop growing! Chewing on hay and toys helps keep them trim.", "image_name": None},
                "Bird": {"description": "Some birds, like the Arctic Tern, migrate thousands of miles every year.", "image_name": None},
                "Fish": {"description": "Fish have been on the Earth for more than 500 million years, long before dinosaurs.", "image_name": None},
            }
            
            for species_name, data in default_animals.items():
                # Find a good position
                for _try in range(100):
                    x = random.randint(ANIMAL_SIZE, w - ANIMAL_SIZE)
                    y = random.randint(ANIMAL_SIZE, h - ANIMAL_SIZE)
                    if math.hypot(x - self.person.x, y - self.person.y) < 100:
                        continue
                    if any(math.hypot(x - a.x, y - a.y) < 80 for a in self.animals):
                        continue
                    break
                
                self.animals.append(Animal(x, y, species_name, data["description"], data["image_name"]))

        # UI font for instructions
        self.font_instr = pygame.font.Font(None, 24)

        # Result (if you want to return anything to a router)
        self.result = None

    # ---------- BaseDisplay hooks ----------
    def on_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
        # Toggle info panel for closest animal when pressing 'P'
            if event.key == pygame.K_p:
                closest = None
                min_d = float('inf')
                for a in self.animals:
                    d = math.hypot(self.person.x - a.x, self.person.y - a.y)
                    if d < min_d:
                        min_d = d
                        closest = a
                if closest and min_d <= INTERACTION_DISTANCE:
                    should = not closest.show_info
                    for a in self.animals:
                        a.show_info = False
                        a.info_timer = 0  # Reset timers for all animals
                    if should:
                        closest.show_info = True
                        closest.info_timer = 5000
                

            # Alternate: Toggle info panel for closest animal when pressing 'C'
            if event.key == pygame.K_c:
                closest = None
                min_d = float('inf')
                for a in self.animals:
                    d = math.hypot(self.person.x - a.x, self.person.y - a.y)
                    if d < min_d:
                        min_d = d
                        closest = a
                if closest and min_d <= INTERACTION_DISTANCE:
                    should = not closest.show_info
                    for a in self.animals:
                        a.show_info = False
                    closest.show_info = should
                    print("closest - ", closest.species_name, closest.description, closest.image_name)  # DEBUG 
                    res = route_to_catchGame(self.background_path, self.screen, closest)
            
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            running = False
        if keys[pygame.K_i]:
            route_to_instructions(self.background_path, self.screen)
        if keys[pygame.K_m]: res = route_to_mode(self.background_path, self.screen); return

    def update(self, dt_ms: int):
        dt = dt_ms / 1000.0
        keys = pygame.key.get_pressed()
        self.person.update(keys, dt_ms, self.screen.get_size())
        for a in self.animals:
            a.update(self.person, dt)

    def draw_content(self, surface: pygame.Surface):
        # Background (tiled)
        if self.bg_tiled:
            surface.blit(self.bg_tiled, (0, 0))

        # Animals then person (so person overlaps)
        for a in self.animals:
            a.draw(surface)
        self.person.draw(surface)

        # Instructions
        lines = [
            "Use Arrow Keys to move",
            "Animals wiggle when you get close",
            "Press 'P' near an animal for info!"
            "Press 'C' near an animal to catch it!",
            "Press ESC to exit",
        ]
        for i, line in enumerate(lines):
            text = self.font_instr.render(line, True, WHITE)
            shadow = self.font_instr.render(line, True, BLACK)
            surface.blit(shadow, (11, 11 + i * 25))
            surface.blit(text, (10, 10 + i * 25))

    # ---------- helpers ----------
    def _create_tiled_background_img(self, image_path: Optional[str]) -> Optional[pygame.Surface]:
        """Tile image 3x3 and crop to screen size; returns a Surface or None if load fails."""
        if not image_path:
            return None
        try:
            tile = pygame.image.load(image_path).convert()
        except Exception:
            return None
        tw, th = tile.get_size()
        sw, sh = self.screen.get_size()

        full_w, full_h = tw * 3, th * 3
        full_bg = pygame.Surface((full_w, full_h))
        for r in range(3):
            for c in range(3):
                full_bg.blit(tile, (c * tw, r * th))

        # crop center to screen
        start_x = max(0, (full_w - sw)//2)
        start_y = max(0, (full_h - sh)//2)
        return full_bg.subsurface(pygame.Rect(start_x, start_y, sw, sh)).copy()


# Optional: local run
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((900, 600))
    # Example animals data structure
    sample_animals = {
        "Tyrannosaurus Rex": {
            "description": "A massive predatory dinosaur from the late Cretaceous period. Known for its powerful jaws and tiny arms.",
            "image_name": "t_rex.png",
            "relative_size": 1.5
        },
        "Triceratops": {
            "description": "A large herbivorous dinosaur with three distinctive horns and a bony frill around its neck.",
            "image_name": "triceratops.png",
            "relative_size": 1.2
        },
        "Pteranodon": {
            "description": "A flying reptile with a wingspan that could reach up to 23 feet. Not technically a dinosaur, but lived alongside them.",
            "image_name": "pteranodon.png",
            "relative_size": 1.0
        }
    }
    disp = PokemonDisplay(screen, background_path="frontend/assets/swamp.png", animals=sample_animals)
    disp.run()
    pygame.quit()