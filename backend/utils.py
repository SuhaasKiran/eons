import pygame
from entities import *

def check_user(username):
    return False, {"username": username, "place": "Amherst"}

def add_new_user(username):
    return {"username": username, "place": "Amherst"}

def route_to_instructions(background, screen):
    # """
    # Opens the instructions screen modally and returns its result ("back"/"next"/"quit"/None).
    # Works with either the BaseDisplay InstructionDisplay or legacy instructionScreen.
    # """
        # Prefer BaseDisplay version if present
    from frontend.instructionScreen import InstructionDisplay
    bg_path = background if isinstance(background, str) else None
    disp = InstructionDisplay(screen, background_path=bg_path)
    if bg_path is None and background is not None:
        # reuse the already-loaded Surface if you have one
        try:
            if isinstance(background, pygame.Surface):
                disp.background = background
        except Exception:
            pass
    result = disp.run()
    return result

def route_to_entry(background, screen):
    # """
    # Opens the instructions screen modally and returns its result ("back"/"next"/"quit"/None).
    # Works with either the BaseDisplay InstructionDisplay or legacy instructionScreen.
    # """
        # Prefer BaseDisplay version if present
    from frontend.entryScreen import EntryDisplay
    bg_path = background if isinstance(background, str) else None
    disp = EntryDisplay(screen, background_path=bg_path)
    if bg_path is None and background is not None:
        # reuse the already-loaded Surface if you have one
        try:
            if isinstance(background, pygame.Surface):
                disp.background = background
        except Exception:
            pass
    result = disp.run()
    return result

def route_to_mode(background, screen):
    # """
    # Opens the instructions screen modally and returns its result ("back"/"next"/"quit"/None).
    # Works with either the BaseDisplay InstructionDisplay or legacy instructionScreen.
    # """
        # Prefer BaseDisplay version if present
    from frontend.modeSelect import ModeSelectDisplay
    bg_path = background if isinstance(background, str) else None
    disp = ModeSelectDisplay(screen, background_path=bg_path)
    if bg_path is None and background is not None:
        # reuse the already-loaded Surface if you have one
        try:
            if isinstance(background, pygame.Surface):
                disp.background = background
        except Exception:
            pass
    result = disp.run()
    return result

def route_to_playerInfo(background, screen):
    # """
    # Opens the instructions screen modally and returns its result ("back"/"next"/"quit"/None).
    # Works with either the BaseDisplay InstructionDisplay or legacy instructionScreen.
    # """
        # Prefer BaseDisplay version if present
    from frontend.userProfile import UserProfileDisplay
    bg_path = background if isinstance(background, str) else None
    disp = UserProfileDisplay(screen, background_path=bg_path)
    if bg_path is None and background is not None:
        # reuse the already-loaded Surface if you have one
        try:
            if isinstance(background, pygame.Surface):
                disp.background = background
        except Exception:
            pass
    result = disp.run()
    return result

def route_to_placeTimeInfo(background, screen, time_place_info, time_place_animals, time_background):
    # """
    # Opens the instructions screen modally and returns its result ("back"/"next"/"quit"/None).
    # Works with either the BaseDisplay InstructionDisplay or legacy instructionScreen.
    # """
        # Prefer BaseDisplay version if present
    from frontend.infoScreen import InfoDisplay
    bg_path = background if isinstance(background, str) else None
    disp = InfoDisplay(screen, background_path=bg_path, time_place_info=time_place_info, time_place_animals=time_place_animals, time_background=time_background)
    if bg_path is None and background is not None:
        # reuse the already-loaded Surface if you have one
        try:
            if isinstance(background, pygame.Surface):
                disp.background = background
        except Exception:
            pass
    result = disp.run()
    return result

def route_to_exploreGame(background, screen, animal_info, background_path):
    # """
    # Opens the instructions screen modally and returns its result ("back"/"next"/"quit"/None).
    # Works with either the BaseDisplay InstructionDisplay or legacy instructionScreen.
    # """
        # Prefer BaseDisplay version if present
    from frontend.exploreGame import PokemonDisplay
    bg_path = background if isinstance(background, str) else None
    disp = PokemonDisplay(screen, background_path=background_path, animals=animal_info)
    if bg_path is None and background is not None:
        # reuse the already-loaded Surface if you have one
        try:
            if isinstance(background, pygame.Surface):
                disp.background = background
        except Exception:
            pass
    result = disp.run()
    return result

def route_to_catchGame(background, screen, animal_info):
    # """
    # Opens the instructions screen modally and returns its result ("back"/"next"/"quit"/None).
    # Works with either the BaseDisplay InstructionDisplay or legacy instructionScreen.
    # """
        # Prefer BaseDisplay version if present
    from frontend.catchGameScreen import CaptureGameDisplay
    species_name = animal_info.species_name
    description = animal_info.description
    image_path = animal_info.image_name
    size = animal_info.relative_size
    

    # setting the powers based on size
    size_power: float = max(0.5, 0.75 * size)   # Clamp size between 0.5 and 2.0
    speed_power: float = 2.5  # Keeping speed fixed for now,
    shots_power: float = max(1.0, 2.0 * size_power)# Direct relation to size
    print("\npowers - ", size_power, speed_power, shots_power)  # DEBUG

    bg_path = background if isinstance(background, str) else None
    disp = CaptureGameDisplay(screen, 
                              background_path=bg_path, 
                              animal_image_path=image_path,
                              animal_name=species_name,
                              animal_desc = description,
                              size_power=size_power,
                              speed_power=speed_power,
                              shots_power=shots_power
                              )
    if bg_path is None and background is not None:
        # reuse the already-loaded Surface if you have one
        try:
            if isinstance(background, pygame.Surface):
                disp.background = background
        except Exception:
            pass
    result = disp.run()
    return result

