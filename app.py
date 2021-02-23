# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template, request, redirect, url_for, abort, Response
from werkzeug.utils import secure_filename
from utils.File import validate_file_epow as validate, uploads_files, purger_upload

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 3072 * 3072
app.config['UPLOAD_EXTENSIONS'] = ['.csv', '.xlsx', '.xls']
app.config['UPLOAD_PATH'] = 'uploads'

@app.route('/')
def index():
    return render_template('accueil.html')

@app.route('/eepower', methods=['GET','POST'])
def eepower():
    uploaded_files = uploads_files(app.config['UPLOAD_PATH'])
    if request.method == 'POST':
        #ajout de fichier pour analyse
        if request.form['btn_id'] == 'soumettre_fichier':
            for uploaded_file in request.files.getlist('file'):
                filename = uploaded_file.filename
                if filename != '':
                    file_ext = os.path.splitext(filename)[1]
                    #valide si l'extension des fichier est bonne
                    if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                        abort(Response("Les fichiers reçus ne sont des fichiers .csv ou .xlsx"))
                    uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
                    #valide en ouvrant les fichier si le contenue est bon
                    if validate(os.path.join(app.config['UPLOAD_PATH'], 'eepower', filename)) != 0:
                        abort(Response("Les fichiers reçus ne contiennent pas les informations nécessaires ou n'ont "
                                       "pas le bon format"))
            return  redirect(url_for('eepower'))

        elif request.form['btn_id'] == 'purger':
            purger_upload(os.path.join(app.config['UPLOAD_PATH'], 'eepower'))
            return redirect(url_for('eepower'))

    return render_template('easy_power.html', uploaded_files=uploaded_files)

if __name__ == "__main__":
    app.run(debug=True)