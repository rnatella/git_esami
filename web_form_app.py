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
import urllib.parse
import socket
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

def connect_db():

    db_file = os.environ.get("STUDENT_DB")

    if db_file is None:
        db_file = "./db/students.db"

    if not os.path.exists(db_file):
        raise EnvironmentError(f'STUDENT_DB file at {db_file} has not been found')

    connection = sqlite3.connect(db_file)
    return connection



app.git_server_ip = os.environ.get("GIT_SERVER_IP")

def replace_url():

    if not app.git_server_ip is None:

        parsed_url = urllib.parse.urlparse(session["repository_url"])

        session["repository_url"] = parsed_url._replace(netloc="{}:{}@{}:{}".format(
                                                                parsed_url.username, 
                                                                parsed_url.password, 
                                                                app.git_server_ip, 
                                                                parsed_url.port)
                                               ).geturl()


default_subgroup = ""

subgroups = []

with closing(connect_db()) as connection:
    with closing(connection.cursor()) as cursor:

        subgroups_count = cursor.execute("SELECT DISTINCT user_subgroup FROM students ORDER BY user_subgroup ASC")

        if subgroups_count == 0:
            print("Errore: Database non inizializzato")
            sys.exit(1)

        for i,row in enumerate(cursor.fetchall()):
            subgroups.append(row[0])




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

    gruppo = SelectField(label='Gruppo',
                       choices=list(zip(subgroups,subgroups)),
                       validators=[
                           InputRequired()
                       ])

    submit = SubmitField(label="Invia")


@app.route('/', methods=['GET','POST'])
def start():

    if "nome" in session and "id" in session:

        return redirect(url_for('hello'))

    else:

        form = FormStudente(gruppo=default_subgroup)

        if form.validate_on_submit():

            session["cognome"] = form.cognome.data
            session["nome"] = form.nome.data
            session["matricola"] = form.matricola.data
            session["gruppo"] = form.gruppo.data

            connection = connect_db()
            cursor = connection.cursor()

            timestamp = datetime.datetime.now()

            updated = cursor.execute("UPDATE students SET firstname=?, surname=?, matricola=?, activated=? WHERE id=(SELECT id FROM students WHERE activated IS NULL AND INSTR(LOWER(user_subgroup),LOWER(?)) AND enabled=1 LIMIT 1) RETURNING id, username, password, repository_url;", (session["nome"], session["cognome"], session["matricola"], timestamp, session["gruppo"]))

            student_row = updated.fetchone()

            connection.commit()

            if student_row == None:
                return "ERRORE: Impossibile accedere al sistema, contattare il docente."

            cursor.close()
            connection.close()


            session["id"] = student_row[0]
            session["username"] = student_row[1]
            session["password"] = student_row[2]
            session["repository_url"] = student_row[3]

            replace_url()

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

            session["last_commit_msg"] = "Nessuno"
            session["last_commit_time"] = ""

            with closing(connection.cursor()) as commit_cursor:

                last_commit = commit_cursor.execute("SELECT message,timestamp FROM commits WHERE project=? ORDER BY timestamp DESC LIMIT 1", (session["username"],)).fetchone()

                if last_commit != None:
                    session["last_commit_msg"] = last_commit[0]
                    session["last_commit_time"] = f" ({last_commit[1]})"

            replace_url()

            return render_template('git.html', id=id)





connection = connect_db()

table_exists = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='students'")

if not table_exists:
    print("Errore: Database non inizializzato")
    sys.exit(1)


default_subgroup = connection.execute("SELECT DISTINCT user_subgroup FROM students LIMIT 1").fetchall()[0][0]

connection.close()



if not app.git_server_ip is None:

   try:
       socket.inet_aton(app.git_server_ip)
   except:
       print("Invalid address in GIT_SERVER_IP environment variable.")
       sys.exit(1)



if __name__ == '__main__':
    #app.run(debug = True, host="0.0.0.0")
    app.run(host="0.0.0.0")


