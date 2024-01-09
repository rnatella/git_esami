from flask import Flask, redirect, url_for, session, flash, render_template
from flask_session import Session
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import InputRequired, Regexp
import datetime
import sqlite3
import sys
import os
import csv
from dotenv import load_dotenv
from contextlib import closing



app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.flaskenv'))

app.secret_key = os.environ.get("SECRET_KEY")

if app.secret_key is None:
    raise EnvironmentError(f'Environment variable SECRET_KEY has not been set (.flaskenv)')


app.config["SESSION_PERMANENT"] = True
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=120)
app.config['SESSION_TYPE'] = 'filesystem'

Session(app)


docenti = []

try:
    with open('.docenti.txt', 'r', newline='') as csv_file:
        docenti = list(csv.reader(csv_file))[0]
except FileNotFoundError as e:
    docenti = input("Inserisci lista docenti (comma-separated): ").split(",")


exam = ""

try:
    with open('.current_exam.txt', 'r', newline='') as csv_file:
        exam = list(csv.reader(csv_file))[0][0]
except FileNotFoundError as e:
    pass



class FormStudente(FlaskForm):
    cognome = StringField(label='Cognome',
                       validators=[
                           InputRequired(),
                           Regexp('^[a-zA-Zàèéìòù\s\']{2,50}$', message="Inserire il cognome")
                       ])

    nome = StringField(label='Nome',
                       validators=[
                           InputRequired(),
                           Regexp('^[a-zA-Zàèéìòù\s\']{2,50}$', message="Inserire il nome")
                       ])

    matricola = StringField(label='Matricola',
                       validators=[
                           InputRequired(),
                           Regexp('^N46\d{6}$', message="Inserire la matricola, in formato N46xxxxxx (6 cifre)")
                       ])

    docente = SelectField(label='Docente',
                       choices=list(zip(docenti,docenti)),
                       validators=[
                           InputRequired()
                       ])

    submit = SubmitField(label="Invia")


@app.route('/', methods=['GET','POST'])
def start():

    if "nome" in session and "id" in session:

        return redirect(url_for('hello'))

    else:

        form = FormStudente()

        if form.validate_on_submit():

            session["cognome"] = form.cognome.data
            session["nome"] = form.nome.data
            session["matricola"] = form.matricola.data
            session["docente"] = form.docente.data

            connection = connect_db()
            cursor = connection.cursor()

            timestamp = datetime.datetime.now()

            updated = cursor.execute("UPDATE students SET firstname=?, surname=?, matricola=?, docente=?, activated=? WHERE id=(SELECT id FROM students WHERE activated IS NULL AND INSTR(LOWER(user_subgroup),LOWER(?)) AND INSTR(LOWER(user_subgroup),LOWER(?)) AND enabled=1 LIMIT 1) RETURNING id, username, password, repository_url;", (session["nome"], session["cognome"], session["matricola"], session["docente"], timestamp, session["docente"], exam))

            student_row = updated.fetchone()

            connection.commit()

            if student_row == None:
                return "ERRORE: Impossibile accedere al sistema, contattare l'amministratore."

            cursor.close()
            connection.close()


            session["id"] = student_row[0]
            session["username"] = student_row[1]
            session["password"] = student_row[2]
            session["repository_url"] = student_row[3]

            return redirect(url_for('hello'))

        else:

            return render_template('form.html', form=form)



@app.route('/hello', methods=['GET'])
def hello():

    if not "id" in session:
        return redirect(url_for('start'))


    #connection = connect_db()
    #cursor = connection.cursor()

    with closing(connect_db()) as connection:
        with closing(connection.cursor()) as cursor:

            user = cursor.execute("SELECT count(*) FROM students WHERE id=? AND not activated is NULL AND enabled=1", (session["id"],)).fetchone()[0]

    #connection.close()

            if user == 0:
                session.clear()
                session["__invalidate__"] = True
                return redirect(url_for('start'))

            session["last_commit_msg"] = "N/A"
            session["last_commit_time"] = ""

            with closing(connection.cursor()) as commit_cursor:

                last_commit = commit_cursor.execute("SELECT message,timestamp FROM commits WHERE project=? ORDER BY timestamp DESC LIMIT 1", (session["username"],)).fetchone()

                if last_commit != None:
                    session["last_commit_msg"] = last_commit[0]
                    session["last_commit_time"] = f" ({last_commit[1]})"

            return render_template('git.html', id=id)



def connect_db():
    db_file="students.db"
    connection = sqlite3.connect(db_file)
    return connection


if __name__ == '__main__':

    connection = connect_db()

    table_exists = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='students'")

    if table_exists.rowcount() == 0:
        print("Errore: Database non inizializzato")
        sys.exit(1)

    connection.close()

    #app.run(debug = True, host="0.0.0.0")
    app.run(host="0.0.0.0")


