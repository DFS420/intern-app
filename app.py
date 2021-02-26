# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template, request, redirect, url_for, abort, Response, flash, send_from_directory
from werkzeug.utils import secure_filename
from utils.File import validate_file_epow as validate, get_uploads_files, purger_upload, full_paths

import utils.eep_traitement as eep

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['MAX_CONTENT_LENGTH'] = 3072 * 3072
app.config['UPLOAD_EXTENSIONS'] = ['.csv', '.xlsx', '.xls']
app.config['UPLOAD_PATH'] = 'uploads'
app.config['UPLOAD_PATH_EPOW'] = r'uploads/eepower'
app.config['GENERATED_PATH'] = r'generated'
app.config['CURRENT_OUTPUT_FILE'] = ''

eep_data = {}
eep_data["BUS_EXCLUS"] = []
eep_data["FILE_PATHS"] = []
eep_data["FILE_NAME"] = []
eep_data["NB_SCEN"] = 0




@app.route('/')
def index():
    return render_template('accueil.html')

@app.route('/eepower', methods=['GET','POST'])
def eepower():
    uploaded_files = get_uploads_files(app.config['UPLOAD_PATH_EPOW'])
    if request.method == 'POST':
        #ajout de fichier pour analyse
        if request.form['btn_id'] == 'soumettre_fichier':
            for uploaded_file in request.files.getlist('file'):
                filename = uploaded_file.filename
                if filename != '':
                    file_ext = os.path.splitext(filename)[1]
                    #valide si l'extension des fichier est bonne
                    if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                        flash("Les fichiers reçus ne sont des fichiers .csv ou .xlsx",'error')
                    uploaded_file.save(os.path.join(app.config['UPLOAD_PATH_EPOW'], filename))
                    #valide en ouvrant les fichier si le contenue est bon
                    if validate(os.path.join(app.config['UPLOAD_PATH_EPOW'], filename)) != 0:
                        os.remove(os.path.join(app.config['UPLOAD_PATH_EPOW'], filename))
                        flash("Les fichiers reçus ne contiennent pas les informations nécessaires ou n'ont "
                                       "pas le bon format", 'error')
            return  redirect(url_for('eepower'))

        elif request.form['btn_id'] == 'purger':
            purger_upload(app.config['UPLOAD_PATH_EPOW'])
            return redirect(url_for('eepower'))

        elif request.form['btn_id'] == 'suivant':
            return redirect(url_for('eepower_traitement'))

    return render_template('easy_power.html', uploaded_files=uploaded_files)

@app.route('/eepower-2', methods=['GET','POST'])
def eepower_traitement():
    uploaded_files = get_uploads_files(app.config['UPLOAD_PATH_EPOW'])
    eep_data["FILE_NAME"] = [name.split('/')[-1].split('.')[0] for name in uploaded_files]
    scenarios = set([int(name[(-1)]) for name in eep_data["FILE_NAME"] if 'scen' in name])
    eep_data["FILE_PATHS"] = full_paths(app.config['UPLOAD_PATH_EPOW'])
    eep_data["NB_SCEN"]= len(scenarios)
    file_ready = 0

    if request.method == 'POST':
        if request.form['btn_id'] == 'ajouter_bus':
            if request.form['bus'] != '':
                eep_data["BUS_EXCLUS"].append(str.upper(request.form['bus']))

        elif request.form['btn_id'] == 'suivant':
            output_path, app.config['CURRENT_OUTPUT_FILE'] = eep.report(eep_data, app.config['GENERATED_PATH'])
            return render_template('easy_power_traitement.html', nb_scen=eep_data["NB_SCEN"],
                                   bus_exclus=eep_data["BUS_EXCLUS"],
                                   file_ready=1)

        elif request.form['btn_id'] == 'telecharger':
            return redirect(url_for('download',app_name='eepower',filename=app.config['CURRENT_OUTPUT_FILE']))

    return render_template('easy_power_traitement.html', nb_scen=eep_data["NB_SCEN"], bus_exclus=eep_data["BUS_EXCLUS"],
                           file_ready=file_ready)

@app.route('/<app_name>/<filename>', methods=['GET', 'POST'])
def download(app_name,filename):
    return send_from_directory(directory=app.config['GENERATED_PATH'], filename=filename)

if __name__ == "__main__":
    app.run(debug=True)