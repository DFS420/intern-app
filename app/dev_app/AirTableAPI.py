from pyairtable import Api
from flask import Blueprint, Flask, jsonify, request
from requests.exceptions import HTTPError
from urllib.request import urlretrieve
from app.utils.File import render_document
from pathlib import Path


with open(r'app/dev_app/api_key', 'r') as f:
    api_key = f.readline()

airtable_api = Blueprint('airtable_api', __name__)

api = Api(api_key)
BASE_ID = api.bases()[0].id

cv_table = api.table(BASE_ID, "CV")
person_table = api.table(BASE_ID, "Personnes")
projet_table = api.table(BASE_ID, "Projets")


@airtable_api.route("/air/person/GET/<person_id>", methods=['GET', 'POST'])
def get_person(person_id):
    try:
        person = person_table.get(record_id=person_id)['fields']
        return person
    except HTTPError as e:
        raise ValueError("L'entrée personne : {0} n'existe pas".format(person_id))


@airtable_api.route("/air/person/GET/<project_id>", methods=['GET', 'POST'])
def get_project(project_id):
    try:
        project = projet_table.get(record_id=project_id)['fields']
        return project
    except HTTPError as e:
        raise ValueError("L'entrée projet : {0} n'existe pas".format(project_id))


@airtable_api.route("/air/cv/GET/<cv_id>", methods=['GET', 'POST'])
def get_cv(cv_id):
    try:
        cv = cv_table.get(record_id=cv_id)['fields']
        return cv
    except HTTPError as e:
        raise ValueError("L'entrée CV : {0} n'existe pas".format(cv_id))


def upload_cv(cv_id):


@airtable_api.route("/air/cv/assemble/<cv_id>", methods=['GET', 'POST'])
def assemble_cv(cv_id):
    projects = []
    persons = []
    try:
        cv = get_cv(cv_id)

    except HTTPError as e:
        raise ValueError("L'entrée CV : {0} n'existe pas".format(cv_id))

    for project_id in cv['Projets']:
        projects.append(get_project(project_id))

    for person_id in cv['Personnes']:
        persons.append(get_person(person_id))

    template_file = urlretrieve(cv['Templates']['url'])

    filename = cv['Nom'] + '.docx'
    rendered_doc = Path('generated'/'developpement'/filename)
    cv = render_document(template_file, rendered_doc, projects, persons[0])


