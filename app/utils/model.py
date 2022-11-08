from pydantic import BaseModel, validator
from datetime import datetime

from typing import List


class Project(BaseModel):
    """
    Define a project inputs
    """
    title: str
    language = 'fr'
    client: str
    founder = ''
    start_date: str
    stop_date: str
    tags: List[str] = []
    body: str
    participants: List[str] = []
    type = 'project'


    @validator('start_date', 'stop_date')
    def is_date_iso(cls, v):
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("Date must be in ISO format")
        return v



class Person(BaseModel):
    """
    Define a person input
    """
    name: str
    second_name = ''
    company: str
    language = 'fr'
    body: str
    tags: List[str] = []
    project: List[str] = []
    type = 'person'


class Getter(BaseModel):
    """
    Define a query dict
    """
    list_search: str = 'any'
    type: str = 'project'
    body: str = ''
    type = 'project'

    #section for project search
    title: str = ''
    language = ''
    client: str = ''
    founder = ''
    start_date: str = ''
    stop_date: str = ''
    tags: List[str] = []
    participants: List[str] = []

    #section for person
    name: str = ''
    second_name = ''
    company: str = ''
    project: List[str] = []

    @validator('list_search')
    def list_search_all_or_any(v):
        if v not in ['all', 'any', 'one_of']:
            raise ValueError("Must be 'any' or 'all'")
        return v
