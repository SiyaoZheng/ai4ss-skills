FROM aisiuk/inspect-tool-support

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        latexmk \
        make \
        poppler-utils \
        r-base \
        r-cran-broom \
        r-cran-curl \
        r-cran-data.table \
        r-cran-dplyr \
        r-cran-ggplot2 \
        r-cran-httr \
        r-cran-jsonlite \
        r-cran-lmtest \
        r-cran-readr \
        r-cran-rvest \
        r-cran-sandwich \
        r-cran-tidyr \
        r-cran-xml2 \
        python3 \
        python3-pip \
        texlive-fonts-recommended \
        texlive-latex-base \
        texlive-latex-extra \
        texlive-latex-recommended \
        texlive-xetex \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir \
        beautifulsoup4 \
        "browser-use[cli]" \
        lxml \
        mcp \
        matplotlib \
        numpy \
        pandas \
        requests \
        scipy \
        statsmodels \
        uv

RUN python3 -m pip install --no-cache-dir playwright
RUN python3 -m playwright install --with-deps chromium

COPY scaffold/ /workspace/
RUN make -C /workspace dirs

WORKDIR /workspace
