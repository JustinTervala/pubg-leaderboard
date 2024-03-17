ARG PYTHON_VERSION=3.9

FROM python:${PYTHON_VERSION}-bookworm as builder

ARG UNAME=user_pubg_leaderboard_scraper

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

RUN apt-get update && apt-get clean

RUN pip install poetry

ENV PYTHONUNBUFFERED=1\
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    \
    # poetryzzz
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /home/$UNAME/pubg_leaderboard_scraper

COPY pyproject.toml poetry.lock ./
RUN touch README.md

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --without dev --no-root

FROM python:${PYTHON_VERSION}-slim-bookworm as runtime

ARG UNAME=user_pubg_leaderboard_scraper
ARG GNAME=group_pubg_leaderboard_scraper
ARG UID=1000
ARG GID=1000

ENV VIRTUAL_ENV=/home/$UNAME/pubg_leaderboard_scraper/.venv
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

RUN apt-get update && \
    apt-get install -y --no-install-recommends dumb-init && \
    apt-get clean

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

RUN groupadd -g $GID -o $GNAME && \
    useradd -m -u $UID -g $GID -o -s /bin/bash $UNAME && \
    chown -R $UNAME:$GNAME /home/$UNAME/pubg_leaderboard_scraper && \
    chmod 755 /home/$UNAME/pubg_leaderboard_scraper

COPY . ./

ENTRYPOINT ["dumb-init", "--"]
