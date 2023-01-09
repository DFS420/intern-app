# -*- coding: utf-8 -*-
import os, secrets, re, requests

from requests import ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError

from flask import Flask, render_template, request, redirect, url_for, abort, Response, flash, send_from_directory
from werkzeug.utils import secure_filename
from .utils import eep_traitement as eep
from .utils import eepower_utils as eeu
from .utils.File import validate_file_epow as validate, get_uploads_files, purge_file, full_paths, \
    create_dir_if_dont_exist as create_dir, zip_files, decode_str_filename, add_to_list_file, get_items_from_file
from .utils.dev_db_utils import prefill_prep, prep_data_for_db
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

app.config['UPLOAD_PATH_DEV'] = create_dir(r'uploads/developpement')

BUSES_FILE = os.path.join(app.config['UPLOAD_PATH_EPOW'], r'bus_exclus')
eep_data = {"BUS_EXCLUS": get_items_from_file(BUSES_FILE),
            "FILE_PATHS": [],
            "FILE_NAMES": [],
            "SCENARIOS": [],
            "NB_SCEN": 0}


@app.route('/')
def index():
    return render_template('accueil.html')


@app.route('/eepower', methods=['GET', 'POST'])
def eepower():
    uploaded_files = get_uploads_files(app.config['UPLOAD_PATH_EPOW'])
    if request.method == 'POST':
        # ajout de fichier pour analyse
        if request.form['btn_id'] == 'soumettre_fichier':
            for uploaded_file in request.files.getlist('file'):
                filename = secure_filename(uploaded_file.filename)
                if filename != '':
                    file_ext = os.path.splitext(filename)[1]
                    # valide si l'extension des fichier est bonne
                    if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                        flash("Les fichiers reçus ne sont des fichiers .csv ou .xlsx", 'error')
                    uploaded_file.save(os.path.join(app.config['UPLOAD_PATH_EPOW'], filename))
                    # valide en ouvrant les fichier si le contenue est bon
                    if validate(os.path.join(app.config['UPLOAD_PATH_EPOW'], filename)) != 0:
                        os.remove(os.path.join(app.config['UPLOAD_PATH_EPOW'], filename))
                        flash("Les fichiers reçus ne contiennent pas les informations nécessaires ou n'ont "
                              "pas le bon format", 'error')
            return redirect(url_for('eepower'))

        elif request.form['btn_id'] == 'purger':
            return redirect(url_for('purge', app_name='eepower'))

        elif request.form['btn_id'] == 'suivant':
            return redirect(url_for('eepower_traitement'))

    return render_template('easy_power.html', uploaded_files=uploaded_files)


@app.route('/eepower-2', methods=['GET', 'POST'])
def eepower_traitement():
    if not eep_data["FILE_NAMES"]:
        try:
            eep_data["FILE_NAMES"] = get_uploads_files(app.config['UPLOAD_PATH_EPOW'])
            eep_data["FILE_PATHS"] = full_paths(app.config['UPLOAD_PATH_EPOW'])
            eep_data["SCENARIOS"] = eeu.scenario_finder(eep_data["FILE_NAMES"])
            eep_data["NB_SCEN"] = len(eep_data["SCENARIOS"])
        except(AttributeError):
            flash("Problème avec les regex", 'error')
            eep_data["FILE_NAMES"] = []
            return redirect(url_for('eepower_traitement'))
    file_ready = 0

    if request.method == 'POST':
        if request.form['btn_id'] == 'ajouter_bus':
            if request.form['bus'] != '':
                add_to_list_file(BUSES_FILE, str.upper(request.form['bus']))
                eep_data["BUS_EXCLUS"] = get_items_from_file(BUSES_FILE)
                render_template('easy_power_traitement.html', nb_scen=eep_data["NB_SCEN"],
                                bus_exclus=eep_data["BUS_EXCLUS"],
                                file_ready=1)

        elif request.form['btn_id'] == 'suivant':
            try:
                dirpath = create_dir(os.path.join(app.config['GENERATED_PATH'], 'eepower'))
            except FileNotFoundError:
                flash("Problème lors de la création du répertoire", 'error')
                return render_template('easy_power_traitement.html', nb_scen=eep_data["NB_SCEN"],
                                       bus_exclus=eep_data["BUS_EXCLUS"],
                                       file_ready=file_ready)
            try:
                output_path, app.config['CURRENT_OUTPUT_FILE'] = eep.report(eep_data, dirpath)
            except FileNotFoundError as e:
                flash(e, 'error')
                return render_template('easy_power_traitement.html', nb_scen=eep_data["NB_SCEN"],
                                       bus_exclus=eep_data["BUS_EXCLUS"],
                                       file_ready=file_ready)

            return render_template('easy_power_traitement.html', nb_scen=eep_data["NB_SCEN"],
                                   bus_exclus=eep_data["BUS_EXCLUS"],
                                   file_ready=1)

        elif request.form['btn_id'] == 'retour':
            return redirect(url_for('eepower'))

        elif request.form['btn_id'] == 'telecharger':
            return redirect(url_for('download', app_name='eepower', filename=app.config['CURRENT_OUTPUT_FILE']))

        elif request.form['btn_id'] == 'terminer':
            return redirect(url_for('purge', app_name='eepower'))

    return render_template('easy_power_traitement.html', nb_scen=eep_data["NB_SCEN"], bus_exclus=eep_data["BUS_EXCLUS"],
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
    metadata = get_metadata()
    prefill = {'fr':  'checked', 'currency': 'CAD'}
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
                    flash("Problème lors de la création de l'entrée : {0}".format(str(results.content)), category='error')
            except (ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError) as e:
                # todo: comprendre pourquoi Connection error a lieu de http error
                flash("Problème lors de la création de l'entrée : {0}".format(e), category='error')
                return redirect(url_for("developpement_add") + '?type=' + _type)

            return redirect(url_for("developpement_add") + '?type=' + _type)

        elif request.form.get('load', False):
            data = {'name': request.form['name'], 'type': _type}
            try:
                response = requests.get("{0}dev/GET".format(request.host_url), json=data).json()
                if not response:
                    raise FileNotFoundError
                prefill = prefill_prep(response[0], _type)
                return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                                       projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'],
                                       prefill=prefill, _type=_type, max_xp=prefill['xp_len'])
            except AttributeError as e:
                flash("Problème de requests : {0}".format(e), 'error')
            except FileNotFoundError:
                flash("Aucun résultat trouvé", 'error')
            except Exception as e:
                flash("Erreur : {0}".format(e), 'error')

            return redirect(url_for("developpement_add"))

        if request.form.get('tag_search', False):
            tags_raw = 'tags_searched'
            if request.form[tags_raw] != '':
                tags = re.split(r"\W+\s*|\s+", request.form[tags_raw])
                data = {'tags': tags, "list_search": request.form['list_search'], "type": _type}
                try:
                    results = requests.get("{0}dev/GET".format(request.host_url), json=data).json()
                    if not results:
                        raise FileNotFoundError
                    return render_template('json_output.html', results=results)
                except AttributeError as e:
                    flash("Problème de requests : {0}".format(e.message), 'error')
                except FileNotFoundError:
                    flash("Aucun résultat trouvé", 'error')
                except Exception as e:
                    flash("Erreur : {0}".format(e.message), 'error')

            else:
                flash("Aucun tags soumis", 'error')

        elif request.form.get('edit', False):
            data = prep_data_for_db(request.form, _type)

            try:
                results = requests.get("{0}dev/edit/{1}".format(request.host_url, _type), json=data)
                flash("{0} modifié(e) : entrée n°{1}".format(_type, results.text[1:].split(',')[0]), category='info')

            except (ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError) as e:
                flash("Problème lors de la création de l'entrée : {0}".format(e), category='error')

        elif request.form.get("add_xp", False):
            app.config['MAX_XP'] += 1
            prefill = prefill_prep(prep_data_for_db(request.form, _type), _type)
            return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                                   projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'], prefill=prefill,
                                   max_xp=app.config['MAX_XP'], _type=_type)

        elif request.form.get("del_xp", False):
            app.config['MAX_XP'] -= 1
            prefill = prefill_prep(prep_data_for_db(request.form, _type), _type)
            return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                                   projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'], prefill=prefill,
                                   max_xp=app.config['MAX_XP'], _type=_type)

        else:
            flash("Bouton inconnu")

    return render_template(page, persons=metadata['PERSON'], nb_person=metadata['NB_PERSON'],
                           projects=metadata['PROJECT'], nb_project=metadata['NB_PROJECT'], prefill=prefill,
                           max_xp=app.config['MAX_XP'], _type=_type)


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
    return send_from_directory(directory=directory, path=app.config['CURRENT_OUTPUT_FILE'],
                               as_attachment=True)


@app.route('/purge/<app_name>', methods=['GET', 'POST'])
def purge(app_name):
    purge_file(os.path.join(app.config['UPLOAD_PATH'], app_name))
    purge_file(os.path.join(app.config['GENERATED_PATH'], app_name))
    return redirect(url_for(app_name))


@app.errorhandler(Exception)
def basic_error(e):
    return "an error occured: " + str(e)

