# Analysis Workflow

The analysis runner owns execution, not interpretation. It turns a design source and analysis-ready material into inspectable outputs.

## Readiness Gate

Do not run analysis until `analysis_readiness_check.csv` validates the cleaned
data or source output against the declared plan. The gate must know:

- design source path;
- data or source output path;
- unit of analysis;
- required variables or coding fields;
- sample flow, merge audit, and variable provenance paths when data were transformed;
- `.aiss` model and bridge alignment when a model is present;
- requested first output;
- output directory;
- interpretation boundary.

If any item is missing, route back instead of guessing. If the gate is `blocked`,
do not run the first analysis loop.

## One-Loop Execution

One loop means one of:

- descriptive table;
- missingness or coverage table;
- balance or comparability table;
- baseline model from an approved formula;
- event-study or trend figure from an approved design;
- text coding summary;
- case grid.

Each loop should produce:

- readiness check path and status;
- script path;
- output path;
- log path;
- sample note;
- warnings or failure signal;
- next skill route.

## Stop Rules

Stop before:

- selecting a preferred specification from many runs;
- interpreting significance as substantive importance;
- making causal claims;
- writing result paragraphs;
- hiding failed runs or warnings.
