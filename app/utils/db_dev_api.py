from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer
from app.utils.model import Person, Project, Getter
from tinydb import TinyDB, Query
import pandas as pd
import json

db_path = 'developpement_db.json'
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

DB = TinyDB(db_path)


def is_duplicate(data):
    if DB.search(Query().body == data['body']):
        return True
    elif DB.search(Query().name == data['name']):
            return True
    else:
        return False


def get_number(search_type='project'):
    query = Query().type == search_type
    return DB.count(query)


async def read_items(token: str = Depends(oauth2_scheme)):
    return {"token": token}


@app.get("/dev")
async def root():
    return {"message": "API fonctionnelle"}


@app.get("/dev/project/ADD")
def add_project(request: Project):
    project = {}
    for k, v in request:
        project[k] = v

    if not is_duplicate(project):
        entry_num = DB.insert(project)
        return entry_num, 'New project added'

    else:
        raise HTTPException(status_code=450, detail="Entry already exists",
                            headers={"duplicate name": project['name']}
                            )


@app.get("/dev/person/ADD")
def add_person(request: Person):
    person = {}
    for k, v in request:
        person[k] = v

    if not is_duplicate(person):
        entry_num = DB.insert(person)
        return entry_num, 'New person added'

    else:
        raise HTTPException(status_code=450, detail="Entry already exists",
                            headers={"name": person['name']}
                            )


@app.get("/dev/GET")
def get(request: Getter):
    ls = request.list_search
    entry = {}
    for k, v in request:
        if v != '' and v != [] and k != 'list_search':
            entry[k] = v

    type_query = Query().type == entry['type']

    if 'tags' in entry.keys():
        if ls == 'all':
            return DB.search((Query().tags.all(entry['tags'])) & type_query)
        elif ls == 'any':
            return DB.search(Query().tags.any(entry['tags']) & type_query)
        elif ls == 'one_of':
            return DB.search(Query().tags.one_of(entry['tags']) & type_query)
    else:
        return DB.search(Query().fragment(entry))


@app.get('/dev/edit/project')
def edit(request: Project):
    entry = {}
    for k, v in request:
        if v != '' and v != []:
            entry[k] = v
    return DB.upsert(entry, Query().name == entry['name'])


@app.get('/dev/edit/person')
def edit(request: Person):
    entry = {}
    for k, v in request:
        if v != '' and v != []:
            entry[k] = v

    return DB.upsert(entry, Query().name == entry['name'])


@app.get('/dev/download_db')
def download_db(_type: str):
    if _type == 'csv':
        with open(db_path) as f:
            data = json.loads(f.read())['_default']
            df = pd.DataFrame(data).T
            df.to_csv('dev_db.csv', encoding='UTF-8', sep=';')
            return FileResponse(path='dev_db.csv', filename='dev_db.csv', media_type='csv')
    else:
        return FileResponse(path=db_path, filename=db_path, media_type='json')


def get_data(**kwargs):
    return DB.search(Query().fragment(kwargs))


def get_metadata():
    DB = TinyDB('developpement_db.json')
    return {
        "PROJECT": get_data(type='project'),
        "PERSON": get_data(type='person'),
        "NB_PROJECT": len(get_data(type='project')),
        "NB_PERSON": len(get_data(type='person'))
    }

