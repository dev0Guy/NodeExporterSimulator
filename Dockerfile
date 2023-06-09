FROM python:3.10-slim as build
RUN apt-get update
RUN apt-get install -y --no-install-recommends \
	      build-essential gcc 
WORKDIR /usr/app
RUN python -m venv /usr/app/venv
ENV PATH="/usr/app/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

FROM python:3.10-slim@sha256:2bac43769ace90ebd3ad83e5392295e25dfc58e58543d3ab326c3330b505283d
WORKDIR /usr/app
COPY --from=build /usr/app/venv ./venv
RUN mkdir node_exporter
COPY ./node_exporter_simulator/ node_exporter_simulator
COPY script.py .

ENV PATH="/usr/app/venv/bin:$PATH"
ENTRYPOINT ["python3", "script.py"]
