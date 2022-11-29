from pydantic import BaseModel, validator
from datetime import datetime

from typing import List, Dict


class Project(BaseModel):
    """
    Define a project inputs
    """
    title: str
    language = 'fr'
    start_date: str
    stop_date: str

    country: str
    location: str = ''
    client: str
    client_address: str = ''
    founder = ''

    contract_value: int = 0
    service_value: int = 0

    leader: List[str] = []
    expert: List[str] = []
    other: List[str] = []
    staff_month: int = 0
    associate: List[str] = []
    associate_staff_month: int = 0

    tags: List[str] = []
    abstract: str
    body: str

    custom_entry: Dict = {}

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
    tel: str = ''
    email: str
    body: str
    tags: List[str] = []
    project: List[str] = []
    type = 'person'


class Getter(BaseModel):
    """
    Define a query dict
    """
    list_search: str = 'any'
    type: str
    body: str = ''
    tags: List[str] = []

    #section for project search
    title: str = ''
    start_date: str = ''
    stop_date: str = ''

    country: str = ''
    location: str = ''
    client: str
    client_address: str = ''
    founder = ''

    contract_value: int = 0
    service_value: int = 0

    participants: List[str] = []
    staff_month: int = 0
    associate: List[str] = []
    associate_staff_month: int = 0

    abstract: str = ''

    #section for person
    name: str = ''
    second_name = ''
    company: str = ''
    tel: str = ''
    email: str = ''
    project: List[str] = []

    @validator('list_search')
    def list_search_all_or_any(v):
        if v not in ['all', 'any', 'one_of']:
            raise ValueError("Must be 'any' 'all' or 'one_of'")
        return v
