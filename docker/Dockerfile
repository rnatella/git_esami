FROM python:3.10-slim

ENV VIRTUAL_ENV "/venv"
RUN python -m venv $VIRTUAL_ENV
ENV PATH "$VIRTUAL_ENV/bin:$PATH"

RUN apt update && \
    apt install -y sqlite3 \
                   build-essential \
		   git

RUN mkdir /app

WORKDIR /app

ENV STUDENT_DB "/app/db/students.db"
ENV PATH "/app:$PATH"

COPY requirements.txt /app
RUN pip install -r /app/requirements.txt

COPY exams_create.sh exams_disable.sh exams_list.sh exams_pull_repos.sh exams_delete.sh exams_enable.sh exams_monitor.sh exams_web_form.sh /app

COPY check_repo.py enable_users.py monitor_repo.py remove_users.py students_db.py web_form_app.py create_repo.py pull_repo.py server_interaction.py students.py /app

COPY templates /app/templates

COPY gitea.toml /app
