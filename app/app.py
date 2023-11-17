# -*- coding: utf-8 -*-
import os, secrets, re, requests

from requests import ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError

from flask import Flask, render_template, request, redirect, url_for, Response, flash, send_from_directory
from werkzeug.utils import secure_filename
from .utils import eep_traitement as eep
from .utils import eepower_utils as eeu
from .utils.File import validate_file_epow as validate, get_uploads_files, purge_file, full_paths, \
    create_dir_if_dont_exist as create_dir, zip_files, decode_str_filename, add_to_list_file, get_items_from_file, \
    save_items_as_json, render_document
from .utils.dev_db_utils import prefill_prep, prep_data_for_db, get_max_len
from .linepole.KMLHandler import KMLHandler
from .linepole import settings as kml_settings

from .utils.db_dev_api import get_metadata

app = Flask(__name__)
app.secret_key = secrets.token_bytes()
app.config['MAX_CONTENT_LENGTH'] = 3072 * 3072
app.config['UPLOAD_EXTENSIONS'] = ['.csv', '.xlsx', '.xls']
app.config['UPLOAD_PATH'] = create_dir('uploads')
app.config['UPLOAD_PATH_EPOW'] = create_dir(r'uploads/eepower')

app.config['UPLOAD_PATH_LP'] = create_dir(r'uploads/linepole_generator')
app.config['GENERATED_PATH'] = create_dir(r'generated')
app.config['CURRENT_OUTPUT_FILE'] = ''

app.config['MAX_XP'] = 3
app.config['MAX_SLAN'] = 2
app.config['MAX_DEGREES'] = 2

app.config['UPLOAD_PATH_DEV'] = create_dir(r'uploads/developpement')
app.config['DEV_TEMPLATE_DOC'] = os.path.join(app.config['UPLOAD_PATH_DEV'], 'templates')
app.config['GENERATED_DEV_DOC_PATH'] = os.path.join(app.config['GENERATED_PATH'], 'developpement')

BUSES_FILE = os.path.join(app.config['UPLOAD_PATH_EPOW'], r'bus_exclus')
EEP_DATA = {"BUS_EXCLUS": get_items_from_file(BUSES_FILE),
            "FILE_PATHS": [],
            "FILE_NAMES": [],
            "SCENARIOS": [],
            "NB_SCEN": 0,
            "REPORT_TYPE": []}


@app.route('/')
def index():
    return render_template('accueil.html')


@app.route('/eepower', methods=['GET', 'POST'])
def eepower():
    uploaded_files = get_uploads_files(app.config['UPLOAD_PATH_EPOW'])
    if request.method == 'POST':
        # ajout de fichier pour analyse
        if request.form['btn_id'] == 'soumettre_fichier':
            error_messages = []
            submittted_files = request.files.getlist('file')
            for uploaded_file in submittted_files:
                filename = secure_filename(uploaded_file.filename)
                if filename != '':
                    file_ext = os.path.splitext(filename)[1]
                    # valide si l'extension des fichiers est bonne
                    if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                        flash("Les fichiers reçus ne sont des fichiers .csv ou .xlsx", 'error')
                    uploaded_file.save(os.path.join(app.config['UPLOAD_PATH_EPOW'], filename))
                    # valide en ouvrant les fichiers si le contenu est bon
                    try:
                        EEP_DATA["REPORT_TYPE"].append(validate(os.path.join(app.config['UPLOAD_PATH_EPOW'], filename)))
                    except ValueError as e:
                        os.remove(os.path.join(app.config['UPLOAD_PATH_EPOW'], filename))
                        error_messages.append("Fichier {0} : {1}".format(filename, e))

            flash("\n".join(error_messages), 'warning')
            return redirect(url_for('eepower'))

        elif request.form['btn_id'] == 'purger':
            return redirect(url_for('purge', app_name='eepower'))

        elif request.form['btn_id'] == 'suivant':
            return redirect(url_for('eepower_traitement'))

    return render_template('easy_power.html', uploaded_files=uploaded_files)


@app.route('/eepower-2', methods=['GET', 'POST'])
def eepower_traitement():
    app_name = 'eepower'
    try:
        EEP_DATA["FILE_NAMES"] = get_uploads_files(app.config['UPLOAD_PATH_EPOW'])
        EEP_DATA["FILE_PATHS"] = full_paths(app.config['UPLOAD_PATH_EPOW'])
        EEP_DATA["SCENARIOS"] = eeu.scenario_finder(EEP_DATA["FILE_NAMES"])
        EEP_DATA["NB_SCEN"] = len(EEP_DATA["SCENARIOS"])
    except(AttributeError):
        flash("Problème avec les regex", 'error')
        EEP_DATA["FILE_NAMES"] = []
        return redirect(url_for('eepower_traitement'))
    file_ready = 0

    if request.method == 'POST':
        if request.form['btn_id'] == 'ajouter_bus':
            if request.form['bus'] != '':
                add_to_list_file(BUSES_FILE, str.upper(request.form['bus']))
                EEP_DATA["BUS_EXCLUS"] = get_items_from_file(BUSES_FILE)
                render_template('easy_power_traitement.html', nb_scen=EEP_DATA["NB_SCEN"],
                                bus_exclus=EEP_DATA["BUS_EXCLUS"],
                                file_ready=1)

        elif request.form['btn_id'] == 'suivant':
            try:
                dirpath = create_dir(os.path.join(app.config['GENERATED_PATH'], 'eepower'))
            except FileNotFoundError:
                flash("Problème lors de la création du répertoire", 'error')
                return render_template('easy_power_traitement.html', nb_scen=EEP_DATA["NB_SCEN"],
                                       bus_exclus=EEP_DATA["BUS_EXCLUS"],
                                       file_ready=file_ready)
            try:
                file_list = []
                if "CC" in EEP_DATA["REPORT_TYPE"]:
                    file_list += eep.report_cc(EEP_DATA, dirpath)
                if "AF" in EEP_DATA["REPORT_TYPE"]:
                    file_list += eep.report_af(EEP_DATA, dirpath)
                if "ED" in EEP_DATA["REPORT_TYPE"]:
                    file_list += eep.report_ed(EEP_DATA, dirpath)
                if "TCC" in EEP_DATA["REPORT_TYPE"]:
                    file_list += eep.report_tcc(EEP_DATA, dirpath)
                if file_list == []:
                    flash("Pas de fichiers fournis", 'error')
                    return render_template('easy_power_traitement.html', nb_scen=EEP_DATA["NB_SCEN"],
                                           bus_exclus=EEP_DATA["BUS_EXCLUS"],
                                           file_ready=file_ready)
                app.config['CURRENT_OUTPUT_FILE'] = zip_files(file_list, zip_file_name=app_name + '_result')

            except FileNotFoundError as e:
                flash(e, 'error')
                return render_template('easy_power_traitement.html', nb_scen=EEP_DATA["NB_SCEN"],
                                       bus_exclus=EEP_DATA["BUS_EXCLUS"],
                                       file_ready=file_ready)

            return render_template('easy_power_traitement.html', nb_scen=EEP_DATA["NB_SCEN"],
                                   bus_exclus=EEP_DATA["BUS_EXCLUS"],
                                   file_ready=1)

        elif request.form['btn_id'] == 'retour':
            return redirect(url_for('eepower'))

        elif request.form['btn_id'] == 'telecharger':
            return redirect(url_for('download', app_name='eepower', filename=app.config['CURRENT_OUTPUT_FILE']))

        elif request.form['btn_id'] == 'terminer':
            return redirect(url_for('purge', app_name='eepower'))

    return render_template('easy_power_traitement.html', nb_scen=EEP_DATA["NB_SCEN"], bus_exclus=EEP_DATA["BUS_EXCLUS"],
                           file_ready=file_ready)


@app.route('/linepole_generator', methods=['GET', 'POST'])
def linepole_generator():
    app_name = 'linepole_generator'
    uploaded_files = get_uploads_files(app.config['UPLOAD_PATH_LP'])
    output_path = create_dir(os.path.join(app.config['GENERATED_PATH'], app_name))

    if request.method == 'POST':
        # ajout de fichier pour analyse
        if request.form['btn_id'] == 'soumettre_fichier':
            file = request.files['file']
            filename = secure_filename(file.filename)

            if filename != '':
                file_ext = os.path.splitext(filename)[1]
                # valide si l'extension des fichier est bonne
                if file_ext != '.kml':
                    flash("Le fichier reçu n'est pas un fichier .kml", 'error')

                file.save(os.path.join(app.config['UPLOAD_PATH_LP'], filename))
                return redirect(url_for('linepole_generator', uploaded_files=uploaded_files, file_ready=0))

            return redirect(url_for('linepole_generator', uploaded_files=uploaded_files, file_ready=0, file_submit=1))

        elif request.form['btn_id'] == 'analyze':
            global handle
            kml_settings.init()
            handle = KMLHandler(os.path.join(app.config["UPLOAD_PATH_LP"], uploaded_files[0]))
            return render_template('linepole.html', uploaded_files=uploaded_files, file_ready=0, file_submit=1,
                                   loader=0, pole=0, parallele=0)

        elif request.form['btn_id'] == 'pole':
            kml_settings.space_by_type['custom'] = request.form.get('dist_pole', type=int)
            handle.generatePoles()
            handle.generateOutput()

            # create the kml with poles
            kml_file_name = os.path.join(output_path, "augmented_kml.kml")
            kml_file = open(kml_file_name, "w+")
            kml_file.write(repr(handle))
            kml_file.close()

            # create a csv in the camelia format
            camelia = handle.camelia
            cam_file_name = os.path.join(output_path, "camelia_output.csv")
            camelia.to_csv(cam_file_name)

            # generate a csv containing all generated data
            csv_name = os.path.join(output_path, "all_data.csv")
            handle.outputdf.to_csv(csv_name)

            outputs = [kml_file_name, cam_file_name, csv_name]

            app.config['CURRENT_OUTPUT_FILE'] = os.path.basename(zip_files(outputs, zip_file_name=app_name + '_result'))
            return render_template('linepole.html', uploaded_files=uploaded_files, file_ready=1, file_submit=1,
                                   pole=1, parallele=0)

        elif request.form['btn_id'] == 'parallele':
            offset = request.form.get('dist_line', type=int)
            max_dist = request.form.get('dist_max_line', type=int)

            handle.generateOffset(offset, max_dist)
            handle.generateOutput()

            # create the kml with poles
            kml_file_name = os.path.join(output_path, "augmented_kml.kml")
            kml_file = open(kml_file_name, "w+")
            kml_file.write(repr(handle))
            kml_file.close()

            # generate a csv containing all generated data
            csv_name = os.path.join(output_path, "all_data.csv")
            handle.outputdf.to_csv(csv_name)

            outputs = [kml_file_name, csv_name]

            app.config['CURRENT_OUTPUT_FILE'] = os.path.basename(zip_files(outputs, zip_file_name=app_name + '_result'))
            return render_template('linepole.html', uploaded_files=uploaded_files, file_ready=1, file_submit=1,
                                   pole=0, parallele=1)

        elif request.form['btn_id'] == 'purger':
            return redirect(url_for('purge', app_name=app_name, file_submit=0))

        elif request.form['btn_id'] == 'telecharger':
            return redirect(url_for('download', app_name=app_name, filename=app.config['CURRENT_OUTPUT_FILE']))

        elif request.form['btn_id'] == 'terminer':
            return redirect(url_for('purge', app_name=app_name))

    return render_template('linepole.html', uploaded_files=uploaded_files, file_ready=0, file_submit=0, loader=0)


@app.route('/developpement/')
def developpement():
    return render_template('dev_menu.html')


@app.route("/new_entry/", methods=['GET', 'POST'])
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
                app.config['MAX_XP'] = prefill['xp_len']
                app.config['MAX_DEGREES'] = prefill['degrees_len']
                app.config['MAX_SLAN'] = prefill['slan_len']
                flash("Problème lors de la création de l'entrée : {0}".format(e), category='error')
                return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                                       projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'],
                                       prefill=prefill, _type=_type, max_xp=app.config['MAX_XP'],
                                       max_slan=app.config['MAX_SLAN'],
                                       max_degrees=app.config['MAX_DEGREES'])

            return redirect(url_for("developpement_add") + '?type=' + _type)

        elif request.form.get('load', False):
            data = {'name': request.form['name'], 'type': _type, 'language': request.form['language']}
            try:
                response = requests.get("{0}dev/GET".format(request.host_url), json=data).json()

                if not response:
                    raise FileNotFoundError
                prefill = prefill_prep(response[0], _type)

                app.config['MAX_XP'] = prefill['xp_len']
                app.config['MAX_DEGREES'] = prefill['degrees_len']
                app.config['MAX_SLAN'] = prefill['slan_len']

                return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                                       projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'],
                                       prefill=prefill, _type=_type, max_xp=prefill['xp_len'],
                                       max_slan=prefill['slan_len'],
                                       max_degrees=prefill['degrees_len'])

            except AttributeError as e:
                flash("Problème de requests : {0}".format(e), 'error')
                return redirect(url_for("developpement_add") + '?type=' + _type)
            except FileNotFoundError:
                flash("Aucun résultat trouvé", 'error')
                return redirect(url_for("developpement_add") + '?type=' + _type)
            except Exception as e:
                flash("Erreur : {0}".format(e), 'error')
                return redirect(url_for("developpement_add") + '?type=' + _type)

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
                        dirpath = create_dir(os.path.join(app.config['GENERATED_PATH'], 'developpement'))
                        filename, _ = save_items_as_json(results, dirpath)
                        return redirect(url_for('download', app_name=app_name, filename=filename))
                    else:
                        return render_template('json_output.html', results=results)
                except AttributeError as e:
                    flash("Problème de requests : {0}".format(e.message), 'error')
                    return redirect(url_for("developpement_add") + '?type=' + _type)
                except FileNotFoundError:
                    flash("Aucun résultat trouvé", 'error')
                    return redirect(url_for("developpement_add") + '?type=' + _type)
                except Exception as e:
                    flash("Erreur : {0}".format(e.message), 'error')
                    return redirect(url_for("developpement_add") + '?type=' + _type)

            else:
                flash("Aucun tags soumis", 'error')
                return redirect(url_for("developpement_add") + '?type=' + _type)

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
                return redirect(url_for("developpement_add") + '?type=' + _type)

        elif request.form.get("add_xp", False):
            current_xp_len = get_max_len(request.form, 'xp')
            app.config['MAX_XP'] = current_xp_len + 1
            prefill = prefill_prep(prep_data_for_db(request.form, _type), _type)
            return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                                   projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'],
                                   prefill=prefill, _type=_type, max_xp=app.config['MAX_XP'],
                                   max_slan=app.config['MAX_SLAN'],
                                   max_degrees=app.config['MAX_DEGREES'])

        elif request.form.get("del_xp", False):
            current_xp_len = get_max_len(request.form, 'xp')
            app.config['MAX_XP'] = current_xp_len - 1
            prefill = prefill_prep(prep_data_for_db(request.form, _type), _type)
            return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                                   projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'],
                                   prefill=prefill, _type=_type, max_xp=app.config['MAX_XP'],
                                   max_slan=app.config['MAX_SLAN'],
                                   max_degrees=app.config['MAX_DEGREES'])

        elif request.form.get("add_degree", False):
            current_deg_len = get_max_len(request.form, 'degree')
            app.config['MAX_DEGREES'] = current_deg_len + 1
            prefill = prefill_prep(prep_data_for_db(request.form, _type), _type)
            return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                                   projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'],
                                   prefill=prefill, _type=_type, max_xp=app.config['MAX_XP'],
                                   max_slan=app.config['MAX_SLAN'],
                                   max_degrees=app.config['MAX_DEGREES'])

        elif request.form.get("del_degree", False):
            current_deg_len = get_max_len(request.form, 'degree')
            app.config['MAX_DEGREES'] = current_deg_len - 1
            prefill = prefill_prep(prep_data_for_db(request.form, _type), _type)
            return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                                   projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'],
                                   prefill=prefill, _type=_type, max_xp=app.config['MAX_XP'],
                                   max_slan=app.config['MAX_SLAN'],
                                   max_degrees=app.config['MAX_DEGREES'])

        elif request.form.get("add_lan", False):
            current_slan_len = get_max_len(request.form, 'slan')
            app.config['MAX_SLAN'] = current_slan_len + 1
            prefill = prefill_prep(prep_data_for_db(request.form, _type), _type)
            return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                                   projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'],
                                   prefill=prefill, _type=_type, max_xp=app.config['MAX_XP'],
                                   max_slan=app.config['MAX_SLAN'],
                                   max_degrees=app.config['MAX_DEGREES'])

        elif request.form.get("del_lan", False):
            current_slan_len = get_max_len(request.form, 'slan')
            app.config['MAX_SLAN'] = current_slan_len - 1
            prefill = prefill_prep(prep_data_for_db(request.form, _type), _type)
            return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                                   projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'],
                                   prefill=prefill, _type=_type, max_xp=app.config['MAX_XP'],
                                   max_slan=app.config['MAX_SLAN'],
                                   max_degrees=app.config['MAX_DEGREES'])

        else:
            flash("Bouton inconnu")

    return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                           projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'],
                           prefill=prefill, _type=_type, max_xp=app.config['MAX_XP'],
                           max_slan=app.config['MAX_SLAN'],
                           max_degrees=app.config['MAX_DEGREES'])


@app.route("/doc_assembler", methods=['GET', 'POST'])
def doc_assembler():
    """
    Search entry and generate documents
    """
    app_name = 'developpement'
    metadata = get_metadata()
    templates = get_uploads_files(dir_name='./uploads/developpement/templates')
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
                results = (requests.get("{0}dev/GET".format(request.host_url), json=proj_data).json(),
                           requests.get("{0}dev/GET".format(request.host_url), json=per_data).json())

                if not results[0] and not results[1]:
                    raise FileNotFoundError

                return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                                       projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'],
                                       templates=templates, selected_projects=results[0],
                                       selected_persons=results[1], selected=True)

            except AttributeError as e:
                flash("Problème de requests : {0}".format(e.message), 'error')
                return redirect(url_for('doc_assembler'))
            except FileNotFoundError:
                flash("Aucun résultat trouvé", 'error')
                return redirect(url_for('doc_assembler'))
            except Exception as e:
                flash("Erreur : {0}".format(e.message), 'error')
                return redirect(url_for('doc_assembler'))

        if request.form.get('generate', False):
            template_path = os.path.join(app.config['DEV_TEMPLATE_DOC'], request.form['template'])
            docpath = os.path.join(app.config['GENERATED_DEV_DOC_PATH'], 'generated_doc.docx')
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
                filename = secure_filename(uploaded_file.filename)
                if filename != '':
                    file_ext = os.path.splitext(filename)[1]
                    # valide si l'extension des fichier est bonne
                    if file_ext not in ['.docx']:
                        flash("Les fichiers reçus ne sont des pas des fichiers .docx", 'error')
                        return redirect(url_for('doc_assembler'))
                    uploaded_file.save(os.path.join(app.config['DEV_TEMPLATE_DOC'], filename))
                    flash("Template(s) téléversé(s)", 'message')

    return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                           projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'])


@app.route('/download_dev_db', methods=['GET', 'POST'])
def download_dev_db():
    _type = request.args['type']
    response = requests.get("{0}dev/download_db?_type={1}".format(request.host_url, _type))
    content = response.content
    return Response(content,
                    mimetype='application/{0}'.format(_type),
                    headers={'Content-Disposition': 'attachment;filename=dev_db.{0}'.format(_type)})


@app.route('/<app_name>/<filename>/', methods=['GET', 'POST'])
def download(app_name, filename):
    filename, _type = decode_str_filename(filename)
    if _type == 'list':
        filename = os.path.basename(zip_files(filename, zip_file_name=app_name + '_result'))
    directory = os.path.abspath(os.path.join(app.config['GENERATED_PATH'], app_name))
    return send_from_directory(directory=directory, path=filename,
                               as_attachment=True)


@app.route('/purge/<app_name>', methods=['GET', 'POST'])
def purge(app_name):
    purge_file(os.path.join(app.config['UPLOAD_PATH'], app_name))
    purge_file(os.path.join(app.config['GENERATED_PATH'], app_name))
    EEP_DATA = {"BUS_EXCLUS": [],
                "FILE_PATHS": [],
                "FILE_NAMES": [],
                "SCENARIOS": [],
                "NB_SCEN": 0}
    return redirect(url_for(app_name))


@app.errorhandler(Exception)
def basic_error(e):
    return "an error occured: " + str(e)

