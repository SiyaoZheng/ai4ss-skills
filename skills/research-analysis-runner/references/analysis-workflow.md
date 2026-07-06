# Analysis Workflow

The analysis runner owns execution, not interpretation. It turns a design source and analysis-ready material into inspectable outputs.

## Readiness Gate

Do not run analysis until `.aiss readiness checks` validates the cleaned
data or source output against the declared plan. The gate must know:

- design source path;
- data or source output path;
- unit of analysis;
- required variables or coding fields;
- `.aiss` row-loss checks, merge checks, and variable-provenance observations when data were transformed;
- `.aiss` model and bridge alignment when a model is present;
- requested first output;
- output directory;
- interpretation boundary.

If any item is missing, repair the missing data/design linkage or route to the
skill that can repair it, then return to the first analysis loop.

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

## Continuation Rules

Continue while avoiding:

- selecting a preferred specification from many runs;
- interpreting significance as substantive importance;
- making causal claims;
- writing result paragraphs;
- hiding failed runs or warnings.
