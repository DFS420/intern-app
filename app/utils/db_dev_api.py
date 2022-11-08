from fastapi import FastAPI, HTTPException
from app.utils.model import Person, Project, Getter
from tinydb import TinyDB, Query

app = FastAPI()

db = TinyDB('developpement_db.json')


def is_duplicate(data):
    if db.search(Query().body == data['body']):
        return True
    else:
        return False


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/project/ADD")
def add_project(request: Project):
    project = {}
    for k, v in request:
        project[k] = v

    if not is_duplicate(project):
        entry_num = db.insert(project)
        return entry_num, 'New project added'

    else:
        raise HTTPException(status_code=450, detail="Entry already exists",
                            headers={"duplicate title": project['title']}
                            )


@app.get("/person/ADD")
def add_person(request: Person):
    person = {}
    for k, v in request:
        person[k] = v

    if not is_duplicate(person):
        entry_num = db.insert(person)
        return entry_num, 'New person added'

    else:
        raise HTTPException(status_code=450, detail="Entry already exists",
                            headers={"name": person['name']}
                            )


@app.get("/GET")
def get(request: Getter):
    ls = request.list_search
    entry = {}
    for k, v in request:
        if v != '' and v != [] and k != 'list_search':
            entry[k] = v

    type_query = Query().type == entry['type']


    print(entry)
    if 'tags' in entry.keys():
        if ls == 'all':
            return db.search((Query().tags.all(entry['tags'])) & type_query)
        elif ls == 'any':
            return db.search(Query().tags.any(entry['tags']) & type_query)
        elif ls == 'one_of':
            return db.search(Query().tags.one_of(entry['tags']) & type_query)
    else:
        return db.search(Query().fragment(entry))

