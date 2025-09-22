# gpt_timeplace.py (or inline in your class file)
from __future__ import annotations
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field, conint
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import os
import requests
import base64
import uuid
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from entities import *
from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DEEPAI_API_KEY = os.getenv('DEEPAI_API_KEY')

class SpeciesInfoLC(BaseModel):
    name: str = Field(description="Species common or scientific name")
    relative_size_human: conint(ge=1) = Field(
        description="Average size relative to an adult human; natural number where 1 ≈ human-sized"
    )
    description: str = Field(description="Brief 1–2 sentence description of the species")


class TimePlaceInfoLC(BaseModel):
    place: str = Field(description="Location name (as provided or normalized)")
    time_mya: float = Field(description="Time in millions of years ago")
    epoch: str = Field(description="Geological epoch or period, e.g., Late Cretaceous")
    climate: str = Field(description="Concise one-line climate description")
    environment: str = Field(description="Concise one-line environment description")
    species: List[SpeciesInfoLC] = Field(
        description="3 random representative animal species of that epoch (at/around the given place and time). No flora or plants."
    )
    summary: str = Field(description="Detiled paragraph about the place and time with some interesting facts in 100 words.")

@dataclass
class TimePlaceInfo:
    place: str
    time_mya: float
    epoch: str
    climate: str
    environment: str
    species: List[SpeciesInfoLC]
    summary: List[str]


@dataclass
class AnimalImage:
    species: str
    image_path: Optional[str]           # resolved local file path (may be None)
    processed_path: Optional[str] = None  

class CaptureGameInfo:
    def __init__(self, place: str, time_mya: float):
        self.place = place
        self.time_mya = time_mya
        self.game_animals = List[Animal]

    def _build_prompt(self) -> ChatPromptTemplate:
        system = (
            "You are a paleontology specialist.\n"
            "Given a location and a time in millions of years ago, return a concise, factual profile.\n"
            "Prefer established facts."
        )
        human = (
            "Location: {place}\n"
            "Time (Mya): {time_mya}\n\n"
        )
        return ChatPromptTemplate.from_messages([("system", system), ("human", human)])

    def get_timeplace_info(self, model_name: str = "gpt-4o-mini-2024-07-18") -> TimePlaceInfo:
        """
        Calls GPT via LangChain, enforces a typed schema, and caches the result to JSON.
        Requires OPENAI_API_KEY in environment.
        """
        prompt = self._build_prompt()
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        llm = ChatOpenAI(model=model_name, temperature=0.7)
        structured_llm = llm.with_structured_output(TimePlaceInfoLC)
        chain = prompt | structured_llm

        result: TimePlaceInfoLC = chain.invoke({"place": self.place, "time_mya": self.time_mya})

        info = TimePlaceInfo(
            place=result.place or self.place,
            time_mya=result.time_mya if result.time_mya is not None else self.time_mya,
            epoch=result.epoch,
            environment=result.environment,
            climate=result.climate,
            summary=result.summary,
            species=list(result.species or []),
            
        )

        self.timeplace_info = info
        print("timeplace_info:", asdict(info))
        return asdict(info)

    def get_image(self, save_path, img_description:str):

        print("img_description - ", img_description)
        deepai_api_key = DEEPAI_API_KEY
        deepai_url = "https://api.deepai.org/api/text2img"

        if(img_description is not None and img_description != ""):
            deepai_prompt = img_description

            response = requests.post(
                deepai_url,
                data={"text": deepai_prompt},
                headers={"api-key": deepai_api_key}
            )

            if response.status_code == 200:
                image_url = response.json()["output_url"]
                img_data = requests.get(image_url).content
                img_name = save_path + str(uuid.uuid4()) + '.png'
                with open(img_name, "wb") as f:
                    f.write(img_data)
                print("Saved image for {img_name} from DeepAI.")
                return img_data, img_name
            else:
                print("Error from DeepAI:", response.text)
                     
        return None, None
    
    def generate_game_animals(self) -> List[Animal]:
        if not hasattr(self, 'timeplace_info'):
            raise ValueError("TimePlaceInfo must be fetched before generating game animals.")

        animals = []
        print("all species - ", self.timeplace_info.species)
        for species in self.timeplace_info.species:
            print("species name - ", species.name)
            img_data, img_name = self.get_image("data/images/animals/", f"Pixel Art, Solid Background.\nAnimal Species: {species.name}\nDescription: {species.description}")
            print("img_name - ", img_name)
            animal = Animal(species=species.name, epoch=self.timeplace_info.epoch, size=species.relative_size_human, imagePath=img_name, description=species.description)
            print("\n\n later - ", animal.species, animal.imagePath, animal.description)
            animals.append(animal)

        self.game_animals = animals
        return animals
    
    def generate_background(self) -> str:
        if not hasattr(self, 'timeplace_info'):
            raise ValueError("TimePlaceInfo must be fetched before generating game animals.")

        bg_img_data, bg_img_name = self.get_image("data/images/backgrounds/", f"Pixel art texture, top-down view, suitable for 2D game background.\nClimate: {self.timeplace_info.climate}\nEnvironment: {self.timeplace_info.environment}")
        print("img_name - ", bg_img_name)
        return bg_img_name