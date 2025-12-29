import re
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator

request_config = ConfigDict(str_strip_whitespace=True)
response_config = ConfigDict(from_attributes=True)


class ActorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    surname: str = Field(..., min_length=1, max_length=100)

    @field_validator('name', 'surname')
    @classmethod
    def validate_characters(cls, value: str) -> str:
        forbidden_chars = r'[<>/{}\[\]\\|;#$%^*=+]'

        if re.search(forbidden_chars, value):
            raise ValueError("Field contains special characters (e.g. < > { } [ ] ;)")

        if any(char.isdigit() for char in value):
            raise ValueError("Name and surname cannot contain digits")

        return value


class ActorCreateRequest(ActorBase):
    model_config = request_config


class ActorUpdateRequest(ActorBase):
    model_config = request_config


class MovieBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    director: str = Field(..., min_length=1, max_length=100)
    year: int = Field(..., ge=1888, le=2100)
    description: Optional[str] = Field(None, max_length=2000)

    @field_validator('title', 'director')
    @classmethod
    def validate_characters(cls, value: str) -> str:
        forbidden_chars = r'[<>/{}\[\]\\|;#$%^*=+]'
        if re.search(forbidden_chars, value):
            raise ValueError("Field contains special characters")
        return value


class MovieCreateRequest(MovieBase):
    actors: list[int] = Field(default_factory=list, max_length=100)
    model_config = request_config


class MovieUpdateRequest(MovieBase):
    actors: list[int] = Field(default_factory=list, max_length=100)
    model_config = request_config


class ActorResponse(ActorBase):
    id: int
    model_config = response_config


class ActorMovieResponse(MovieBase):
    id: int
    model_config = response_config


class MovieResponse(MovieBase):
    id: int
    actors: list[ActorResponse] = []
    model_config = response_config
