# FAERS_MPN_three_tier

Analysis code for the manuscript:

> **Background selection determines the conclusion: a three-tier disproportionality analysis of thrombotic signals for myeloproliferative neoplasm therapies in FAERS**

Every count reported in the paper can be reproduced from the cached responses in `cache/` without contacting the openFDA endpoint again.

## What the study does

Six drugs licensed for myeloproliferative neoplasms (ruxolitinib, hydroxyurea, anagrelide, busulfan, luspatercept, ropeginterferon alfa-2b) are crossed with 16 MedDRA preferred terms, giving 96 drug–event pairs. Each pair is analysed against three reference groups:

| Tier | Reference | Question it answers |
|---|---|---|
| 1 | all other reports in FAERS | what a conventional signal query returns |
| 2 | reports recording a myeloproliferative neoplasm | does the signal survive holding the disease constant |
| 3 | a comparator drug used in the same disease | does the signal survive active comparison |

## Repository layout

```
code/      one script per analysis step, run in the order below
tables/    derived results (CSV, UTF-8 with BOM)
cache/     raw count responses from openFDA, keyed by query string
figures/   final figures at 300 dpi
```

## Reproducing

```bash
python -m venv .venv && .venv/Scripts/activate      # Windows
pip install -r requirements.txt

cd code
python faers_main.py               # tier 1: 6 drugs x 16 events vs the whole database
python mpn_stratified.py           # tier 2: within the MPN report pool
python disease_stratified.py       # tier 3: head-to-head within each disease
python sensitivity.py              # S1 exclude combination users, S2 serious only
python l2_sensitivity.py           # S3 pool without ruxolitinib, S4 unexposed reference
python background_enrichment.py    # disease prevalence ratio for the 16 events
python case_series.py              # retrieve 169 individual reports
python case_analysis.py            # structured review of those reports
python readus_supplement.py        # READUS-PV items 7a, 8a, 8b, 13
python figures_final.py            # Figures 1-5 and S1
python build_submission.py         # Word versions of manuscript, tables, supplement
```

Scripts read and write the caches in `cache/` and `../tables/`; adjust the `BASE` constant at the top of each file if you move the directories.

## Data source

US Food and Drug Administration Adverse Event Reporting System, via the openFDA `drug/event` endpoint (`https://api.fda.gov/drug/event.json`), retrieved 1 November 2026. Total 20,692,690 reports. No individual-level data are redistributed here; all inputs are public.

## Three traps worth knowing before reusing this code

1. **Use `patient.drug.openfda.generic_name`, not `medicinalproduct`.** For ruxolitinib the two fields return 71,241 and 10,645 reports respectively — a 6.7-fold difference.
2. **FAERS uses British spelling in indications.** `POLYCYTHAEMIA VERA` returns 16,282 reports; the American spelling returns 2, and `ESSENTIAL THROMBOCYTHAEMIA` returns 5,048 against 2. A query with American spelling returns near-zero counts *without raising an error*, which reads as absence of reports.
3. **Range syntax needs a literal space around `TO`.** `receivedate:[20110101 TO 20111231]` works; `+TO+` is URL-encoded to `%2B` and the endpoint returns HTTP 500.

## Licence

MIT for the code. The derived tables are released under CC BY 4.0.
