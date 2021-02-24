# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template, request, redirect, url_for, abort, Response, flash
from werkzeug.utils import secure_filename
from utils.File import validate_file_epow as validate, get_uploads_files, purger_upload

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['MAX_CONTENT_LENGTH'] = 3072 * 3072
app.config['UPLOAD_EXTENSIONS'] = ['.csv', '.xlsx', '.xls']
app.config['UPLOAD_PATH'] = 'uploads'
app.config['UPLOAD_PATH_EPOW'] = r'uploads/eepower'

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

    return render_template('easy_power.html', uploaded_files=uploaded_files)

if __name__ == "__main__":
    app.run(debug=True)