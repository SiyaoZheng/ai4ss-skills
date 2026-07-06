FROM aisiuk/inspect-tool-support

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        r-base \
        r-cran-digest \
        r-cran-dplyr \
        r-cran-readr \
        r-cran-yaml \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
