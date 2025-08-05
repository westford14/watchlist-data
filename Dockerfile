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
    bzip2 \
    libxtst6 \
    libgtk-3-0 \
    libx11-xcb-dev \
    libdbus-glib-1-2 \
    libxt6 \
    libpci-dev \
    libasound-dev \
    build-essential && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

ARG FIREFOX_VERSION=128.0.3
RUN curl -fL -o /tmp/firefox.tar.bz2 "https://download.mozilla.org/?product=firefox-latest-ssl&os=linux64&lang=en-US" && \
    tar -xf /tmp/firefox.tar.bz2 -C /opt/ && \
    ln -s /opt/firefox/firefox /usr/bin/firefox

ARG GECKODRIVER_VERSION=0.34.0
RUN curl -fL -o /tmp/geckodriver.tar.gz "https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/geckodriver-v${GECKODRIVER_VERSION}-linux64.tar.gz" && \
    tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin/ && \
    chmod +x /usr/local/bin/geckodriver

COPY . /root/pipelines
WORKDIR /root/pipelines

RUN jq -r '.default | to_entries[] | .key + .value.version' \
    Pipfile.lock > requirements.txt

RUN pip install .