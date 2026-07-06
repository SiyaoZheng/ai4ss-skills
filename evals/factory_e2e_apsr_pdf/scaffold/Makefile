SHELL := /bin/bash
.DELETE_ON_ERROR:

PYTHON ?= python3
RSCRIPT ?= Rscript
LATEXMK ?= latexmk

PAPER_TEX ?= paper/full_draft.tex
PAPER_PDF ?= paper/full_draft.pdf

DIRS := \
	.ai4ss \
	.ai4ss/checks \
	.ai4ss/handoffs \
	.ai4ss/scratch \
	data/raw \
	data/intermediate \
	data/processed \
	output/tables \
	output/figures \
	output/models \
	output/logs \
	paper \
	scripts

.PHONY: all dirs data analysis tables figures paper pdf check clean clean-paper

all: dirs data analysis tables figures paper

dirs:
	@mkdir -p $(DIRS)

data: dirs
	@if [ -x scripts/build_data.sh ]; then \
		scripts/build_data.sh; \
	elif [ -f scripts/build_data.R ]; then \
		$(RSCRIPT) scripts/build_data.R; \
	elif [ -f scripts/build_data.py ]; then \
		$(PYTHON) scripts/build_data.py; \
	else \
		echo "No data builder found: add scripts/build_data.{R,py,sh}"; \
	fi

analysis: data
	@if [ -x scripts/run_analysis.sh ]; then \
		scripts/run_analysis.sh; \
	elif [ -f scripts/run_analysis.R ]; then \
		$(RSCRIPT) scripts/run_analysis.R; \
	elif [ -f scripts/run_analysis.py ]; then \
		$(PYTHON) scripts/run_analysis.py; \
	else \
		echo "No analysis runner found: add scripts/run_analysis.{R,py,sh}"; \
	fi

tables: analysis
	@if [ -x scripts/build_tables.sh ]; then \
		scripts/build_tables.sh; \
	elif [ -f scripts/build_tables.R ]; then \
		$(RSCRIPT) scripts/build_tables.R; \
	elif [ -f scripts/build_tables.py ]; then \
		$(PYTHON) scripts/build_tables.py; \
	else \
		echo "No table builder found: add scripts/build_tables.{R,py,sh}"; \
	fi

figures: analysis
	@if [ -x scripts/build_figures.sh ]; then \
		scripts/build_figures.sh; \
	elif [ -f scripts/build_figures.R ]; then \
		$(RSCRIPT) scripts/build_figures.R; \
	elif [ -f scripts/build_figures.py ]; then \
		$(PYTHON) scripts/build_figures.py; \
	else \
		echo "No figure builder found: add scripts/build_figures.{R,py,sh}"; \
	fi

paper: $(PAPER_PDF)

pdf: paper

$(PAPER_PDF): $(PAPER_TEX) dirs
	@mkdir -p paper output/logs
	cd paper && $(LATEXMK) -pdf -interaction=nonstopmode -halt-on-error -file-line-error $(notdir $(PAPER_TEX))

check: $(PAPER_PDF)
	@test -r $(PAPER_PDF)
	@pdfinfo $(PAPER_PDF) >/dev/null
	@pdftotext $(PAPER_PDF) - >/dev/null
	@$(PYTHON) scripts/check_real_data_contract.py $(PAPER_PDF)
	@echo "PDF check passed: $(PAPER_PDF)"

clean-paper:
	@$(LATEXMK) -C -outdir=paper $(PAPER_TEX) >/dev/null 2>&1 || true
	@rm -f paper/*.aux paper/*.bbl paper/*.blg paper/*.fdb_latexmk paper/*.fls paper/*.log paper/*.out paper/*.synctex.gz

clean: clean-paper
	@rm -rf data/intermediate/* data/processed/* output/tables/* output/figures/* output/models/* output/logs/*
