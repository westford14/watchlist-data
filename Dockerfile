FROM ubuntu:24.04 AS base

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.13 python3.13-dev python3.13-venv curl && \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.13 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

FROM base AS python-deps

RUN pip install pipenv
RUN apt-get update && apt-get install -y --no-install-recommends \
  gcc \
  pkg-config \
  cmake \
  build-essential \
  libpq-dev

COPY Pipfile .
COPY Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --dev

FROM base AS runtime

COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

RUN apt-get update && apt-get upgrade -y && \
  apt-get install -y --no-install-recommends \
    gnupg2 \
    apt-utils \
    wget \
    ca-certificates \
    software-properties-common \
    cmake \
    jq \
    libnspr4 \
    libnss3 \
    libxcb-xkb-dev \
    build-essential && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \ 
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
RUN apt-get update && apt-get -y install google-chrome-stable

COPY . /root/pipelines
WORKDIR /root/pipelines

RUN jq -r '.default | to_entries[] | .key + .value.version' \
    Pipfile.lock > requirements.txt

RUN pip install .