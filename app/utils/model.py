from pydantic import BaseModel, validator
from datetime import datetime

from typing import List, Dict


class Project(BaseModel):
    """
    Define a project inputs
    """
    name: str
    language = 'fr'
    start_date: str
    stop_date: str
    duration: str

    countries: List[str]
    locations: List[str] = []
    client: str
    client_address: str = ''
    founder = ''
    reference: List[str] = []

    contract_value: int = 0
    service_value: int = 0
    currency: str

    leader: str = ' '
    expert: List[str] = []
    other: List[str] = []
    staff_month: int = 0
    associate: List[str] = []
    associate_staff_month: int = 0
    persons: List[str] = []

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
    company: str
    language = 'fr'
    birthday: str
    job: str
    tel: str = ''
    email: str
    residency: str
    body: str
    tags: List[str] = []
    associate_project: List[str] = []
    experiences: Dict = {}
    custom_entry: Dict = {}
    type = 'person'


class Getter(BaseModel):
    """
    Define a query dict
    """
    type: str
    tags: List[str] = []
    tags_ls: str = 'any'
    name: str = ''
    name_ls: str = 'any'
    names: List[str] = []
    countries: List[str] = []
    countries_ls: str = 'any'
    persons: List[str] = []
    persons_ls: str = 'any'
    year: str = ''
    language: str = ''

    @validator('tags_ls', 'name_ls', 'countries_ls', 'persons_ls')
    def list_search_all_or_any(v):
        if v not in ['all', 'any', 'one_of']:
            raise ValueError("Must be 'any' 'all' or 'one_of'")
        return v
