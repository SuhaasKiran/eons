from typing import List, Dict, Optional
import json
import os
import yaml

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

class AnimalGameFeats:
    def __init__(self, size: float):
        self.speed = self.set_speed(size)
        self.shotsRequired = self.set_shots_required(size)
    
    def set_speed(self, size: float) -> float:
        return 1.0 / size  

    def set_shots_required(self, size: float) -> int:
        return int(size * 2)  

    def to_dict(self) -> Dict:
        """Convert AnimalGameFeats to a JSON-serializable dictionary."""
        return {
            "speed": self.speed,
            "shotsRequired": self.shotsRequired
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'AnimalGameFeats':
        """Create an AnimalGameFeats instance from a dictionary."""
        instance = cls(size=1.0)  # Temporary size; will be overridden
        instance.speed = data["speed"]
        instance.shotsRequired = data["shotsRequired"]
        return instance

class Animal:
    def __init__(self, species: str, epoch: str, size: float, imagePath: str, description: str = ""):
        self.species = species
        self.epoch = epoch
        self.size = size
        self.imagePath = imagePath
        self.description = description
        self.gameFeats = AnimalGameFeats(self.size)
    
    def to_dict(self) -> Dict:
        """Convert Animal to a JSON-serializable dictionary."""
        return {
            "species": self.species,
            "epoch": self.epoch,
            "size": self.size,
            "imagePath": self.imagePath,
            "gameFeats": self.gameFeats.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Animal':
        """Create an Animal instance from a dictionary."""
        instance = cls(
            species=data["species"],
            epoch=data["epoch"],
            size=data["size"],
            imagePath=data["imagePath"]
        )
        instance.gameFeats = AnimalGameFeats.from_dict(data["gameFeats"])
        return instance

class BeastBall:
    def __init__(self):
        self.imagePath = config['BEASTBALL_IMAGE_PATH']

class GameRecord:
    def __init__(self, date: str, place: str, timeMYA: int, beastballsUsed: int, animalCaught: Animal):
        self.date = date
        self.place = place
        self.timeMYA = timeMYA
        self.beastballsUsed = beastballsUsed
        self.animalCaught = animalCaught

    def to_dict(self) -> Dict:
        """Convert GameRecord to a JSON-serializable dictionary."""
        return {
            "date": self.date,
            "place": self.place,
            "timeMYA": self.timeMYA,
            "beastballsUsed": self.beastballsUsed,
            "animalCaught": self.animalCaught.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'GameRecord':
        """Create a GameRecord instance from a dictionary."""
        return cls(
            date=data["date"],
            place=data["place"],
            timeMYA=data["timeMYA"],
            beastballsUsed=data["beastballsUsed"],
            animalCaught=Animal.from_dict(data["animalCaught"])
        )

class BattleRecord:
    def __init__(self, date: str, animal: Animal, beastballChange: int):
        self.date = date
        self.animal = animal
        self.beastballChange = beastballChange

    def to_dict(self) -> Dict:
        """Convert BattleRecord to a JSON-serializable dictionary."""
        return {
            "date": self.date,
            "animal": self.animal.to_dict(),
            "beastballChange": self.beastballChange
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'BattleRecord':
        """Create a BattleRecord instance from a dictionary."""
        return cls(
            date=data["date"],
            animal=Animal.from_dict(data["animal"]),
            beastballChange=data["beastballChange"]
        )

class Player:
    def __init__(self, username: str):
        self.username = username
        self.beastball_left = config['STARTING_BEASTBALLS']
        self.battle_history: List[BattleRecord] = []
        self.game_history: List[GameRecord] = []
        self.caught_animals: List[Animal] = []

    def to_dict(self) -> Dict:
        """Convert Player to a JSON-serializable dictionary."""
        return {
            "beastballs": self.beastball_left,
            "battle_history": [record.to_dict() for record in self.battle_history],
            "game_history": [record.to_dict() for record in self.game_history],
            "caught_animals": [animal.to_dict() for animal in self.caught_animals]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Player':
        """Create a Player instance from a dictionary."""
        player = cls(username=data["username"])
        player.beastball_left = data["beastballs"]
        player.battle_history = [BattleRecord.from_dict(record) for record in data["battle_history"]]
        player.game_history = [GameRecord.from_dict(record) for record in data["game_history"]]
        player.caught_animals = [Animal.from_dict(animal) for animal in data["caught_animals"]]
        return player

    def add_caught_animal(self, animal: Animal):
        self.caught_animals.append(animal)
    
    def add_game_history(self, record: GameRecord):
        self.game_history.append(record)
    
    def add_battle_history(self, record: BattleRecord):
        self.battle_history.append(record)

    def get_game_history(self) -> List[GameRecord]:
        return self.game_history


class PlayerManager:
    def __init__(self, file_path: str = "data/playerData.json"):
        self.file_path = file_path
        # Ensure the JSON file exists; create an empty one if it doesn't
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump({}, f)

    def _load_players(self) -> Dict:
        """Load the player data from the JSON file."""
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # If the file is empty or corrupted, return an empty dict
            return {}

    def _save_players(self, players: Dict) -> None:
        """Save the player data to the JSON file."""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(players, f, indent=4)
        except PermissionError:
            print(f"Error: No permission to write to {self.file_path}")
            raise

    def save_player(self, player: Player) -> bool:
        """Save a Player object to the JSON file.
        
        Args:
            player: The Player object to save.
        
        Returns:
            bool: True if the player was saved, False if the username already exists.
        """
        if not player.username.strip():
            print("Username cannot be empty.")
            return False
        players = self._load_players()
        if player.username in players:
            print(f"Username '{player.username}' already exists. Use update_player to modify.")
            return False
        players[player.username] = player.to_dict()
        self._save_players(players)
        print(f"Player '{player.username}' saved successfully.")
        return True

    def update_player(self, player: Player) -> bool:
        """Update an existing player's data in the JSON file.
        
        Args:
            player: The Player object with updated data.
        
        Returns:
            bool: True if the player was updated, False if the username doesn't exist.
        """
        if not player.username.strip():
            print("Username cannot be empty.")
            return False
        players = self._load_players()
        if player.username not in players:
            print(f"Username '{player.username}' not found.")
            return False
        players[player.username] = player.to_dict()
        self._save_players(players)
        print(f"Player '{player.username}' updated successfully.")
        return True

    def get_player(self, username: str) -> Optional[Player]:
        """Retrieve a Player object by username from the JSON file.
        
        Args:
            username: The username to look up.
        
        Returns:
            Player: The Player object if found, None otherwise.
        """
        if not username.strip():
            print("Username cannots be empty.")
            return None
        players = self._load_players()
        player_data = players.get(username)
        if player_data:
            # Add username to player_data for from_dict
            player_data["username"] = username
            return Player.from_dict(player_data)
        print(f"Player '{username}' not found.")
        return None

# # Example usage
# if __name__ == "__main__":
#     # Initialize the PlayerManager
#     manager = PlayerManager("players.json")

#     # Create a new player
#     player = Player("dgsk")
#     lion = Animal(species="Lion", epoch="Modern", size=1.5, imagePath="lion.png")
#     t_rex = Animal(species="T-Rex", epoch="Cretaceous", size=12.0, imagePath="trex.png")
#     player.add_caught_animal(lion)
#     player.add_caught_animal(t_rex)
#     player.add_battle_history(BattleRecord(date="2025-09-21", animal=lion, beastballChange=-1))
#     player.add_game_history(GameRecord(date="2025-09-21", place="Jungle", timeMYA=0, beastballsUsed=2, animalCaught=t_rex))

#     # Save the player
#     manager.save_player(player)

#     # Retrieve and print player information
#     retrieved_player = manager.get_player("dgsk")
#     if retrieved_player:
#         print(f"Player: {retrieved_player.username}")
#         print(f"Beastballs: {retrieved_player.beastball_left}")
#         print("Caught animals:")
#         for animal in retrieved_player.caught_animals:
#             print(f"- {animal.species} ({animal.epoch}, size: {animal.size})")
#         print("Battle history:")
#         for record in retrieved_player.battle_history:
#             print(f"- {record.date}: Fought {record.animal.species}, Beastball Change: {record.beastballChange}")
#         print("Game history:")
#         for record in retrieved_player.game_history:
#             print(f"- {record.date}: {record.place}, TimeMYA: {record.timeMYA}, Beastballs Used: {record.beastballsUsed}, Caught: {record.animalCaught.species}")