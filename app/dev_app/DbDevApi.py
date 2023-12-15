import requests
import simplejson.errors
from flask import Blueprint, current_app, request, render_template, flash, redirect, url_for
from requests import ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError
from werkzeug.utils import secure_filename
from pathlib import Path
import re
from app.utils.File import create_dir_if_dont_exist as create_dir,\
    save_items_as_json, render_document, get_uploads_files
from app.dev_app.dev_db_utils import prep_data_for_db, prefill_prep, get_max_len
from app.dev_app.model import Person, Project, Getter
from tinydb import TinyDB, Query
import pandas as pd
import json
from flask_pydantic import validate

db_dev_api = Blueprint('db_dev_api', __name__)


current_app.config['DB_PATH'] = current_app.config['UPLOAD_PATH_DEV'] / "dev_db.json"
DB = TinyDB(current_app.config['DB_PATH'], ensure_ascii=False)


def is_duplicate(data):
    if DB.search(Query().body == data['body']):
        return True
    elif DB.search((Query().name == data['name']) & (Query().language == data['language'])):
        return True
    else:
        return False


def get_number(search_type='project'):
    query = Query().type == search_type
    return DB.count(query)


@db_dev_api.route('/dev', methods=['GET', 'POST'])
def root():
    return {"message": "API fonctionnelle"}


@db_dev_api.route("/dev/project/ADD", methods=['GET', 'POST'])
@validate()
def add_project(request: Project):
    project = {}
    for k, v in request:
        project[k] = v

    if not is_duplicate(project):
        entry_num = DB.insert(project)
        return entry_num, 'New project added'

    else:
        raise ValueError("L'entrée {0} existe déjà".format(project['name']))


@db_dev_api.route("/dev/person/ADD", methods=['GET', 'POST'])
@validate()
def add_person(request: Person):
    person = {}
    for k, v in request:
        person[k] = v

    if not is_duplicate(person):
        entry_num = DB.insert(person)
        return entry_num, 'New person added'

    else:
        raise ValueError("L'entrée {0} existe déjà".format(person['name']))


@db_dev_api.route("/dev/GET", methods=['GET'])
@validate()
def get(request: Getter):
    _type = ''
    entry = {}
    list_entry = {}
    ls = {}
    for k, v in request:
        if v != '' and 'ls' not in k and isinstance(v, str) and 'type' not in k:
            entry[k] = v
        elif v != [] and v != [''] and 'ls' not in k and isinstance(v, list):
            list_entry[k] = v
        elif v != '' and 'ls' in k:
            ls[k] = v
        elif v != '' and 'type' in k:
            _type = v

    if not entry and not list_entry:
        return []

    queries = ["(Query().type == _type)"]
    if entry:
        queries.append("(Query().fragment(entry))")

    if list_entry:
        for k in list_entry.keys():
            if 'names' not in k:
                queries.append("(Query().{0}.{1}(list_entry['{0}']))".format(k, ls['{0}_ls'.format(k)]))

        if 'names' in list_entry:
            q_tmp = ["""(Query().name == "{0}")""".format(name) for name in list_entry['names']]
            queries.append((' | '.join(q_tmp)))

    return eval("DB.search({0})".format(' & '.join(queries)))


@db_dev_api.route("/dev/edit/project", methods=['GET', 'POST'])
@validate()
def edit_project(request: Project):
    entry = {}
    for k, v in request:
        if v != '' and v != []:
            entry[k] = v
    return DB.upsert(entry, (Query().name == entry['name']) & (Query().language == entry['language']))


@db_dev_api.route("/dev/edit/person", methods=['GET', 'POST'])
@validate()
def edit_person(request: Person):
    entry = {}
    for k, v in request:
        if v != '' and v != []:
            entry[k] = v

    return DB.upsert(entry, (Query().name == entry['name']) & (Query().language == entry['language']))


@db_dev_api.route("/dev/download_db/<_type>", methods=['GET', 'POST'])
def download_db(_type: str):
    if _type == 'csv':
        with open(current_app.config['DB_PATH']) as f:
            data = json.loads(f.read())['_default']
            df = pd.DataFrame(data).T
            csv_path = current_app.config['UPLOAD_PATH_DEV']/'dev_db.csv'
            df.to_csv(csv_path, encoding='UTF-8-sig', sep=';')
            return redirect(url_for('download', app_name='developpement', filename=csv_path))
    else:
        return redirect(url_for('download', app_name='developpement', filename=current_app.config['DB_PATH']))


def get_data(**kwargs):
    return DB.search(Query().fragment(kwargs))


def get_metadata():
    DB = TinyDB('dev_db.json')
    return {
        "PROJECT": get_data(type='project'),
        "PERSON": get_data(type='person'),
        "NB_PROJECT": len(get_data(type='project')),
        "NB_PERSON": len(get_data(type='person'))
    }


@db_dev_api.route('/developpement')
def developpement():
    return render_template('dev_menu.html')


@db_dev_api.route("/new_entry/", methods=['GET', 'POST'])
def developpement_add():
    """
    Add entry to the dev database
    """
    app_name = 'developpement'
    metadata = get_metadata()
    prefill = {'fr': 'checked', 'currency': 'CAD'}
    _type = request.args['type']
    page = 'add_entry.html'

    if request.method == 'POST':
        if request.form.get('save', False):
            data = prep_data_for_db(request.form, _type)

            try:
                results = requests.get("{0}dev/{1}/ADD".format(request.host_url, _type), json=data)
                if results.status_code == 200:
                    flash("Entrée enregistrée : entrée n°{0}".format(results.text[1:].split(',')[0]), category='info')
                else:
                    raise ValueError
            except (ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError, ValueError) as e:
                prefill = prefill_prep(prep_data_for_db(request.form, _type), _type)
                current_app.config['MAX_XP'] = prefill['xp_len']
                current_app.config['MAX_DEGREES'] = prefill['degrees_len']
                current_app.config['MAX_SLAN'] = prefill['slan_len']
                flash("Problème lors de la création de l'entrée : {0}".format(e), category='error')
                return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                                       projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'],
                                       prefill=prefill, _type=_type, max_xp=current_app.config['MAX_XP'],
                                       max_slan=current_app.config['MAX_SLAN'],
                                       max_degrees=current_app.config['MAX_DEGREES'])

            return redirect(url_for("db_dev_api.developpement_add") + '?type=' + _type)

        elif request.form.get('load', False):
            data = {'name': request.form['name'], 'type': _type, 'language': request.form['language']}
            try:
                response = requests.get("{0}dev/GET".format(request.host_url), json=data).json()

                if not response:
                    raise FileNotFoundError
                prefill = prefill_prep(response[0], _type)

                current_app.config['MAX_XP'] = prefill['xp_len']
                current_app.config['MAX_DEGREES'] = prefill['degrees_len']
                current_app.config['MAX_SLAN'] = prefill['slan_len']

                return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                                       projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'],
                                       prefill=prefill, _type=_type, max_xp=prefill['xp_len'],
                                       max_slan=prefill['slan_len'],
                                       max_degrees=prefill['degrees_len'])

            except AttributeError as e:
                flash("Problème de requests : {0}".format(e), 'error')
                return redirect(url_for("db_dev_api.developpement_add") + '?type=' + _type)
            except FileNotFoundError:
                flash("Aucun résultat trouvé", 'error')
                return redirect(url_for("db_dev_api.developpement_add") + '?type=' + _type)
            except Exception as e:
                flash("Erreur : {0}".format(e), 'error')
                return redirect(url_for("db_dev_api.developpement_add") + '?type=' + _type)

        if request.form.get('tag_search', False) or request.form.get('save_json', False):
            tags_raw = 'tags_searched'
            if request.form[tags_raw] != '':
                tags = list(map(str.lower, re.split(r";\s*", request.form[tags_raw])))
                data = {'tags': tags, "tags_ls": request.form['list_search'], "type": _type}
                try:
                    results = requests.get("{0}dev/GET".format(request.host_url), json=data).json()
                    if not results:
                        raise FileNotFoundError
                    if request.form.get('save_json', False):
                        dirpath = create_dir(current_app.config['GENERATED_PATH']/'developpement')
                        file = save_items_as_json(results, dirpath)
                        return redirect(url_for('download', app_name=app_name, filename=file.name))
                    else:
                        return render_template('json_output.html', results=results)
                except AttributeError as e:
                    flash("Problème de requests : {0}".format(e.message), 'error')
                    return redirect(url_for("db_dev_api.developpement_add") + '?type=' + _type)
                except FileNotFoundError:
                    flash("Aucun résultat trouvé", 'error')
                    return redirect(url_for("db_dev_api.developpement_add") + '?type=' + _type)
                except Exception as e:
                    flash("Erreur : {0}".format(e.message), 'error')
                    return redirect(url_for("db_dev_api.developpement_add") + '?type=' + _type)

            else:
                flash("Aucun tags soumis", 'error')
                return redirect(url_for("db_dev_api.developpement_add") + '?type=' + _type)

        elif request.form.get('edit', False):
            data = prep_data_for_db(request.form, _type)

            try:
                results = requests.get("{0}dev/edit/{1}".format(request.host_url, _type), json=data)
                if results.status_code == 200:
                    flash("{0} modifié(e) : entrée n°{1}".format(_type, results.text[1:].split(',')[0]),
                          category='info')
                else:
                    raise HTTPError

            except (ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError) as e:
                flash("Problème lors de la création de l'entrée : {0}".format(e), category='error')
                return redirect(url_for("db_dev_api.developpement_add") + '?type=' + _type)

        elif request.form.get("add_xp", False):
            current_xp_len = get_max_len(request.form, 'xp')
            current_app.config['MAX_XP'] = current_xp_len + 1
            prefill = prefill_prep(prep_data_for_db(request.form, _type), _type)
            return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                                   projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'],
                                   prefill=prefill, _type=_type, max_xp=current_app.config['MAX_XP'],
                                   max_slan=current_app.config['MAX_SLAN'],
                                   max_degrees=current_app.config['MAX_DEGREES'])

        elif request.form.get("del_xp", False):
            current_xp_len = get_max_len(request.form, 'xp')
            current_app.config['MAX_XP'] = current_xp_len - 1
            prefill = prefill_prep(prep_data_for_db(request.form, _type), _type)
            return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                                   projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'],
                                   prefill=prefill, _type=_type, max_xp=current_app.config['MAX_XP'],
                                   max_slan=current_app.config['MAX_SLAN'],
                                   max_degrees=current_app.config['MAX_DEGREES'])

        elif request.form.get("add_degree", False):
            current_deg_len = get_max_len(request.form, 'degree')
            current_app.config['MAX_DEGREES'] = current_deg_len + 1
            prefill = prefill_prep(prep_data_for_db(request.form, _type), _type)
            return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                                   projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'],
                                   prefill=prefill, _type=_type, max_xp=current_app.config['MAX_XP'],
                                   max_slan=current_app.config['MAX_SLAN'],
                                   max_degrees=current_app.config['MAX_DEGREES'])

        elif request.form.get("del_degree", False):
            current_deg_len = get_max_len(request.form, 'degree')
            current_app.config['MAX_DEGREES'] = current_deg_len - 1
            prefill = prefill_prep(prep_data_for_db(request.form, _type), _type)
            return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                                   projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'],
                                   prefill=prefill, _type=_type, max_xp=current_app.config['MAX_XP'],
                                   max_slan=current_app.config['MAX_SLAN'],
                                   max_degrees=current_app.config['MAX_DEGREES'])

        elif request.form.get("add_lan", False):
            current_slan_len = get_max_len(request.form, 'slan')
            current_app.config['MAX_SLAN'] = current_slan_len + 1
            prefill = prefill_prep(prep_data_for_db(request.form, _type), _type)
            return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                                   projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'],
                                   prefill=prefill, _type=_type, max_xp=current_app.config['MAX_XP'],
                                   max_slan=current_app.config['MAX_SLAN'],
                                   max_degrees=current_app.config['MAX_DEGREES'])

        elif request.form.get("del_lan", False):
            current_slan_len = get_max_len(request.form, 'slan')
            current_app.config['MAX_SLAN'] = current_slan_len - 1
            prefill = prefill_prep(prep_data_for_db(request.form, _type), _type)
            return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                                   projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'],
                                   prefill=prefill, _type=_type, max_xp=current_app.config['MAX_XP'],
                                   max_slan=current_app.config['MAX_SLAN'],
                                   max_degrees=current_app.config['MAX_DEGREES'])

        else:
            flash("Bouton inconnu")

    return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                           projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'],
                           prefill=prefill, _type=_type, max_xp=current_app.config['MAX_XP'],
                           max_slan=current_app.config['MAX_SLAN'],
                           max_degrees=current_app.config['MAX_DEGREES'])

@db_dev_api.route("/doc_assembler", methods=['GET', 'POST'])
def doc_assembler():
    """
    Search entry and generate documents
    """
    app_name = 'developpement'
    metadata = get_metadata()
    templates = get_uploads_files(upload_dir='uploads/developpement/templates')
    page = 'doc_assembler.html'

    if request.method == 'POST':
        if request.form.get('search', False):
            language = request.form['language']
            tags = list(map(str.lower, re.split(r";\s*", request.form['tags_searched'])))
            countries = list(map(str.capitalize, re.split(r";", request.form['countries'])))
            # todo to implement year = request.form['year']
            persons = request.form.getlist('persons')

            proj_data = {'tags': tags, "tags_ls": request.form['tags_ls'],
                         'countries': countries, "countries_ls": request.form['countries_ls'],
                         'persons': persons, "persons_ls": request.form['persons_ls'],
                         'language': language, "type": 'project'}
            per_data = {'names': persons, 'language': language, "type": 'person', 'tags': tags,
                        'countries': countries, "countries_ls": request.form['countries_ls'],}

            try:
                results = (requests.get("{0}dev/GET".format(request.host_url), params=proj_data).json(),
                           requests.get("{0}dev/GET".format(request.host_url), params=per_data).json())

                if not results[0] and not results[1]:
                    raise FileNotFoundError

                return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                                       projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'],
                                       templates=templates, selected_projects=results[0],
                                       selected_persons=results[1], selected=True)

            except AttributeError as e:
                flash("Problème de requests : {0}".format(e.message), 'error')
                return redirect(url_for('db_dev_api.doc_assembler'))
            except FileNotFoundError:
                flash("Aucun résultat trouvé", 'error')
                return redirect(url_for('db_dev_api.doc_assembler'))
            except simplejson.errors.JSONDecodeError as e:
                flash("Erreur lors de la lecture de la base de donneés : {0}".format(e.doc), 'error')
                return redirect(url_for('db_dev_api.doc_assembler'))
            except Exception as e:
                flash("Erreur : {0}".format(e.args[0]), 'error')
                return redirect(url_for('db_dev_api.doc_assembler'))

        if request.form.get('generate', False):
            template_path = current_app.config['DEV_TEMPLATE_DOC']/request.form['template']
            docpath = current_app.config['GENERATED_DEV_DOC_PATH']/'generated_doc.docx'
            proj_data = {'names': request.form.getlist('selected_projects'), "type": 'project'}
            per_data = {'names': request.form.getlist('selected_persons'), "type": 'person'}

            try:
                projects, persons = (requests.get("{0}dev/GET".format(request.host_url), json=proj_data).json(),
                                     requests.get("{0}dev/GET".format(request.host_url), json=per_data).json())

                if not projects and not persons:
                    raise FileNotFoundError

                doc_file = render_document(template_path, docpath, projects, persons)

                return redirect(url_for('download', app_name=app_name, filename=doc_file))

            except AttributeError as e:
                flash("Problème de requests : {0}".format(e.message), 'error')
            except FileNotFoundError:
                flash("Aucun résultat trouvé", 'error')
            except Exception as e:
                flash("Erreur : {0}".format(e.message), 'error')

        if request.form['btn_id'] == 'soumettre_fichier':
            for uploaded_file in request.files.getlist('upload_template'):
                file = Path(secure_filename(uploaded_file.filename))
                if file != '':
                    file_ext = file.suffix()
                    # valide si l'extension des fichiers est bonne
                    if file_ext not in ['.docx']:
                        flash("Les fichiers reçus ne sont des fichiers .docx", 'error')
                        return redirect(url_for('db_dev_api.doc_assembler'))
                    uploaded_file.save(current_app.config['DEV_TEMPLATE_DOC']/file)
                    flash("Template(s) téléversé(s)", 'message')

    return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                           projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'])

