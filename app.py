from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('accueil.html')

@app.route('/eepower', methods=['GET','POST'])
def eepower():
    if request.method == 'POST':
        for uploaded_file in request.files.getlist('file'):
            if uploaded_file.filename != '':
                uploaded_file.save(uploaded_file.filename)
        return redirect(url_for('eepower'))

    return render_template('easy_power.html')

if __name__ == "__main__":
    app.run(debug=True)