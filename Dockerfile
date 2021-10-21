FROM python:3.9
ENV PIP_DISABLE_PIP_VERSION_CHECK=on

RUN useradd -ms /bin/bash uwsgi
WORKDIR /biodataner

RUN pip install poetry

COPY poetry.lock pyproject.toml /biodataner/

RUN poetry config virtualenvs.create false && \
	poetry install --no-interaction

COPY . /biodataner

CMD poetry run uwsgi  \
	--uid uwsgi \
	--chdir /biodataner \
	--wsgi-file /biodataner/python_scripts/webapp.py \
	--callable app   \
	--master --processes 4 --threads 2 \
	--http :8080 \
	--lazy-apps \
	--strict \
	--disable-logging \
	--log-4xx \
	--log-5xx