from flask import Flask, redirect, url_for, session, flash, render_template
from flask_session import Session
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import InputRequired, Regexp
import datetime


app = Flask(__name__)

app.secret_key = 'una stringa qualunque'
app.config["SESSION_PERMANENT"] = True
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=120)
app.config['SESSION_TYPE'] = 'filesystem'

Session(app)


docenti = [ "Cinque", "Cotroneo", "Natella" ]


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

    if "nome" in session:

        return redirect(url_for('hello'))

    else:
        form = FormStudente()

        if form.validate_on_submit():

            session["cognome"] = form.cognome.data
            session["nome"] = form.nome.data
            session["matricola"] = form.matricola.data
            session["docente"] = form.docente.data

            connection.execute("UPDATE students SET firstname=?, surname=?, matricola=?, docente=?, activated=1 WHERE id=(SELECT id FROM students WHERE activated=0 LIMIT 1);", (session["nome"], session["cognome"], session["matricola"], session["docente"]))

            student_row = connection.execute("SELECT id, username, password, repository_rul FROM students WHERE nome=? AND cognome=? AND matricola=? AND docente=?;", (session["nome"], session["cognome"], session["matricola"], session["docente"]))

            student_id, username, password, repository_url = student_row.fetchone()

            session["id"] = student_id
            session["username"] = username
            session["password"] = password
            session["repository_url"] = repository_url

            return redirect(url_for('hello'))

        else:

            return render_template('form.html', form=form)



@app.route('/hello', methods=['GET'])
def hello():

    if "nome" in session:

        #return f'CIAO {session["nome"]}'
        return render_template('git.html', id=id)

    else:

        return redirect(url_for('start'))



if __name__ == '__main__':

    db_file="students.db"
    connection = sqlite3.connect(db_file)


    table_exists = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")

    if table_exists.rowcount() == 0:
        print("Errore: Database non inizializzato")
        sys.exit(1)

    app.run(debug = True)


