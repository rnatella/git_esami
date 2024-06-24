# PMGC (Poor Man's Git Classroom)

Questo tool è una collezione di script e di configurazioni per attivare un server Git per la gestione degli esami.

![Overview](/images/overview.png)


Lo studente accede a un form web, ed inserisce i propri dati (cognome, nome, matricola). Su indicazione del docente, lo studente inserisce anche il gruppo di esame a cui partecipa (ad esempio, per dividere gli studenti per docenti, oppure per dare tracce diverse).

![Demo form](/images/demo-form.png)



Lo studente riceve in risposta un account (es. student-10, con password casuale) per accedere al server git. Ogni account dispone di 1 repository, con lo stesso nome dell'utente (es. student-10).

Lo studente riceve inoltre i comandi dettagliati per
- scaricare in locale il repository, e configurarlo
- salvare le modifiche sul server

![Demo git](/images/demo-git.png)


La sessione sul web form dura 2 ore. Lo studente può riavviare il suo browser o il suo computer. Il token di sessione è salvato sul filesystem del server, nella cartella `flask_session`, con chiave generata casualmente al primo avvio del web form, e salvata nel file `.flaskenv`.

Il docente può monitorare i commit inviati dagli studenti tramite una interfaccia su console a caratteri.

![Overview](/images/demo-console.png)

Prima di iniziare gli esami, il docente deve creare preliminarmente gli account. È sufficiente indicare quali gruppi creare, e quanti account creare per ogni gruppo. Non è richiesto (anche se è possibile) inserire preliminarmente i dati degli studenti, perché saranno loro a inserire i loro dati nel form web. 

Sono forniti i seguenti script per la gestione degli account e dei repository:
- **docker-compose-gitea/gitea_configure.sh**: Crea dei container per il server Gitea e relativo dabatase MySQL.
- **docker-compose-gitea/gitea_token.sh**: Ottiene un token per l'accesso alle API Gitea (salvato in **gitea.toml**).
- **docker-compose-gitea/gitea_https.sh**: Abilita il supporto a HTTPS in Gitea (con certificato self-signed).
- **exams_create.sh**: Crea gli utenti sia per il form web (database SQLite in **students.db**), sia per il server Gitea (database MySQL).
- **exams_web_form.sh**: Lancia una app Flask che fornisce l'accesso iniziale agli studenti.
- **exams_disable.sh**: Disabilita il push di commit per tutti i gruppi, o per uno specifico gruppo.
- **exams_enable.sh**: Abilita il push di commit.
- **exams_list.sh**: Elenca i gruppi.
- **exams_monitor.sh**: Mostra in tempo reale i commit degli studenti.
- **exams_pull_repos.sh**: Scarica (o aggiorna) in locale i repository degli studenti.
- **exams_delete.sh**: Rimuove tutto (container, DB, repositories, etc.)


# Quick tutorial

Configure Python environment

```
$ python3 -m venv env
$ source env/bin/activate
$ pip install -r requirements.txt
```


Deploy local Gitea+DB server

```
cd docker-compose-gitea/

./gitea_configure.sh
...enter admin password...
...you can leave "0.0.0.0" (default) as server address...
...you can leave 3000 (default) as port...

./gitea_token.sh

./gitea_https.sh

cd ..
```



Initialize accounts for users (e.g., 2 groups, different code per group, 10 students per group, 20 students in total)
```
./exams_create.sh  so-sangiovanni  10  ./1st-folder-with-code
./exams_create.sh  so-fuorigrotta  20  ./2nd-folder-with-code
```

In a new shell, launch the web form. You can configure here the IP address of the server (environment variable `SERVER_IP`), students will get it through the web form.
```
source env/bin/activate
export SERVER_IP="1.2.3.4"
./exams_web_form.sh
```

In a new shell, get updates in real-time about commits from students
```
source env/bin/activate
./exams_monitor.sh
```

To turn off submissions
```
./exams_disable.sh
```

To download all repositories
```
./exams_pull_repos.sh
```


To delete everything (DB, flask sessions, code repos)
```
./exams_delete.sh
```


# Tutorial for dockerized scripts

Deploy Gitea as before (use `gitea_configure.sh`, `gitea_token.sh`, `gitea_https.sh`).

Build the container image for the scripts:
```
docker build -t git_esami -f docker/Dockerfile .
```

Create and manage exams with the following commands:
```
# To initialize users (can be ran multiple times)
./docker/exams_create.sh so-test 10 ./path-to-source

# From a dedicated shell
export SERVER_IP="1.2.3.4"
./docker/exams_web_form.sh

# From a dedicated shell
./docker/exams_monitor.sh

# From a dedicated shell
./docker/exams_disable.sh
./docker/exams_enable.sh
./docker/exams_pull_repos.sh

```
