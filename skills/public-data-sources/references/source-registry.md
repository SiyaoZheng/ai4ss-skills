# Free Public Data Source Registry

Use this registry as a routing aid, not as a substitute for live documentation.
For research outputs, re-check official docs or make a small live request on the
day of collection.

## Access Classes

| Access class | Meaning | Agent rule |
|---|---|---|
| `public_no_secret` | Basic API calls work without a user-specific secret | Still throttle, cache, and handle 429/5xx. |
| `free_key_required` | Free account, API key, token, or registration is required for normal use | Read the key from an environment variable; never ask the user to paste it into code or commit it. |
| `download_ingest_only` | Public or free data exist, but the normal workflow is file download, not a stable open REST API | Download or ingest with provenance and version/date stamps; do not pretend it is a live API. |

Free is not the same as no-auth, unlimited, or redistributable. If a source asks
for a free token, classify it as `free_key_required`, even when the data are
academically open.

## Fast Routing Table

| Source | Best for | Access class | Use first |
|---|---|---|---|
| World Bank Indicators | Cross-country development, governance proxies, education, poverty, population, macro panel data | `public_no_secret` | `https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?format=json&per_page=20000` |
| Penn World Table 11.0 | Country-year income, output, input, productivity, PPP, labor, capital, and TFP measures | `download_ingest_only` | Official GGDC Excel/Stata downloads; seed-store imports the Dataverse Excel file into `pwt_11_0`. |
| Maddison Project Database 2023 | Long-run country-year GDP per capita, population, and comparative income levels | `download_ingest_only` | Official GGDC Excel/Stata downloads; seed-store imports the `Full data` sheet into `maddison_project_2023_full_data`. |
| UNDP HDR composite-index time series | HDI, IHDI, GDI, GII, PHDI, life expectancy, schooling, and GNI components by country-year | `download_ingest_only` for CSV; `free_key_required` for HDR API 2.0 | Use the official composite-indices time-series CSV when no API key is configured; queue API calls behind `UNDP_HDR_API_KEY`. |
| Correlates of War National Material Capabilities | State-year CINC, military, industrial, energy, urban population, and total population capabilities | `download_ingest_only` | Official COW ZIP; seed-store imports abridged and supplementary CSV members. |
| OECD Data Explorer API | OECD and partner-country macro, education, labor, fiscal, regional statistics | `public_no_secret` | `https://sdmx.oecd.org/public/rest/dataflow/all`, then filtered SDMX data queries |
| Eurostat | EU and European regional/NUTS statistics | `public_no_secret` | Eurostat dissemination APIs; use Statistics API for JSON-stat or SDMX APIs for SDMX workflows |
| ECB Data Portal API | Euro-area monetary, financial, balance sheet, exchange-rate, bank, and macro-financial time series | `public_no_secret` | `https://data-api.ecb.europa.eu/service/dataflow/ECB/all/latest?detail=allstubs` |
| IMF Data API | IMF macro, financial, balance of payments, government finance, and country data | `public_no_secret` for SDMX data access; portal exploration may require sign-in | Use IMF SDMX 2.1/3.0 docs and verify the exact endpoint before automation |
| UN SDG API / UNData | UN indicator and SDG data | `public_no_secret` for many endpoints | Prefer SDG API for SDG indicators; UNData API coverage varies by datamart |
| WHO GHO / Athena | Health indicators, mortality, disease burden, health systems, tobacco, nutrition | `public_no_secret` | `https://ghoapi.azureedge.net/api/Indicator`, then indicator-specific OData calls |
| ILOSTAT | Labor force, employment, unemployment, informality, wages, working conditions | `public_no_secret` for SDMX/bulk metadata and many downloads | `https://sdmx.ilo.org/rest/v1/dataflow/all/all/latest?detail=allstubs` |
| UNHCR Refugee Statistics API | Refugees, asylum applications, IDPs, statelessness, origin/asylum country panels | `public_no_secret` | `https://api.unhcr.org/population/v1/` endpoints with bounded `limit`/page queries |
| OWID Grapher | Clean chart-level panels for health, demography, inequality, climate, conflict, technology | `public_no_secret` for redistributable Grapher charts | Append `.csv`, `.metadata.json`, or `.zip` to a Grapher chart URL; check metadata license. |
| NASA POWER | Gridded climate/weather covariates for social-science panels and historical context | `public_no_secret` | `https://power.larc.nasa.gov/api/temporal/monthly/point?...` |
| Federal Register API | U.S. federal rules, notices, policy text, agency activity, regulatory agenda evidence | `public_no_secret` | `https://www.federalregister.gov/api/v1/documents.json?...` |
| Harvard Dataverse API | Replication packages, social-science datasets, DOI-backed research data discovery | `public_no_secret` for public search/metadata | `https://dataverse.harvard.edu/api/search?q=...&type=dataset` |
| Agent-fetchable discovery platforms | Finding public datasets, replication packages, DOI-backed data records, and repository candidates before a named source is chosen | `public_no_secret` for verified metadata search; public-file download only when exposed by the record | See `references/discovery-platforms.md`; verified entries are Zenodo, DataCite, Dataverse, Figshare, Dryad, OpenAIRE, re3data, and OSF public API. |
| Crossref | DOI metadata, publication metadata, funder metadata | `public_no_secret` | REST API with a polite `mailto` parameter when possible |
| DataCite | DOI metadata for datasets and research objects | `public_no_secret` for metadata retrieval | REST API metadata retrieval without auth; auth is for DOI create/update |
| Voteview | U.S. Congress roll-call votes, member ideology, NOMINATE scores | `public_no_secret` for static CSV downloads | `https://voteview.com/static/data/out/members/HSall_members.csv` and related CSVs |
| ParlGov | European parties, elections, cabinets, party families, government composition | `public_no_secret` static CSV/SQLite downloads | `https://parlgov.org/data/parlgov-development_csv-utf-8.zip` |
| FAOSTAT | Agriculture, food, land, prices, emissions, production, trade | `public_no_secret` or bulk/download depending endpoint | Prefer official API/bulk portal and bounded domain/item/element queries. |
| yescallop/areacodes | China administrative-code history and city/county crosswalk spine | `public_no_secret` static CSV | `https://raw.githubusercontent.com/yescallop/areacodes/master/result.csv`; verify against MCA/NBS definitions before publication |
| CEADs city catalogs | China city carbon, industrial process emissions, water, mercury, and city MRIO discovery | `public_no_secret` for catalog pages; downloads may require account/session | Parse CEADs city catalog pages first; treat actual files as download/registration workflows |
| CHAP / ChinaHighPM2.5 | China gridded annual/monthly/daily PM2.5 and other air-pollution covariates | `public_no_secret` metadata and public downloads | Use Zenodo file manifests; city-year values require boundary zonal statistics |
| EOG VIIRS Nighttime Lights | Annual global night-light covariates for China city-year panels | `download_ingest_only` | Download annual GeoTIFFs from EOG VNL; aggregate to city-year with a fixed boundary vintage |
| GDELT | Global news, events, media agenda, geolocation, text search | `public_no_secret` | Useful, but default seed-store skips it when the user excludes GDELT. |
| U.S. Census Data API | ACS, decennial, geography, economic and community variables in the United States | `free_key_required` for normal agent use | `CENSUS_API_KEY`; include `key=` in requests |
| FRED | Macro, financial, regional, historical U.S. and international time series | `free_key_required` | `FRED_API_KEY`; append `api_key=` |
| BEA | U.S. national accounts, regional GDP/income, international transactions, industry accounts | `free_key_required` | `BEA_API_KEY`; use BEA methods and metadata endpoints |
| BLS | U.S. labor, CPI/PPI, wages, employment, productivity time series | `free_key_required` for v2; v1 has tight no-key limits | `BLS_API_KEY`; v2 has higher limits and metadata features |
| EIA | Energy production, prices, consumption, electricity, emissions-related energy measures | `free_key_required` | `EIA_API_KEY`; bulk files may be separate |
| NOAA CDO | Station weather and climate normals for the U.S. and some global holdings | `free_key_required` | `NOAA_CDO_TOKEN` header |
| IPUMS API | Census, CPS, NHGIS, ATUS, international and harmonized microdata extracts | `free_key_required` | `IPUMS_API_KEY` as `Authorization` header; user must be registered for each collection |
| UN Comtrade | International trade, product flows, political economy of trade | `free_key_required` for normal data API | `COMTRADE_API_KEY`; free basic individual tier has quotas and record caps |
| OpenAlex | Bibliometrics, scholarly works, authors, institutions, sources, topics, citations | `free_key_required` for practical use | `OPENALEX_API_KEY`; singleton lookups are free, list/search draw from daily budget |
| Semantic Scholar | Scholarly paper search and citation graph lookups | `free_key_required` for reliable use | `SEMANTIC_SCHOLAR_API_KEY`; some public endpoints work without auth but shared limits are fragile |
| ORCID | Public researcher identifiers and profile metadata | `free_key_required` | Register public API credentials and use OAuth token flow |
| UCDP API | Conflict events, dyads, one-sided/non-state violence, battle deaths | `free_key_required` | `UCDP_API_TOKEN`; send `x-ucdp-access-token` header |
| Manifesto Project | Party manifestos, party positions, coded policy emphasis | `free_key_required` | `MANIFESTO_API_KEY`; account is free |
| OpenAQ | Air quality monitors and pollutant observations | `free_key_required` | `OPENAQ_API_KEY`; verify current API version |
| IATI Datastore | Aid, development finance, activities, budgets, transactions | `free_key_required` in current Datastore v3 docs | `IATI_API_KEY`; use activity/transaction/budget endpoints |
| ACLED | Conflict and protest event data | `free_key_required` | myACLED account plus OAuth or cookie auth; check current access policy |
| DHS Program API | DHS indicators, countries, surveys, datasets metadata | `public_no_secret` for metadata API; microdata requires account approval | Use API for metadata; use approved download/IPUMS DHS workflow for microdata |
| Media Cloud | News source and article-search workflows | `free_key_required` or project access | Confirm current account, quota, and collection access before automation |
| V-Dem | Democracy indicators and country-year panels | `download_ingest_only` | Download versioned CSV/R/Stata/SPSS files; record version and release date |
| QoG | Curated comparative politics country-year/cross-section datasets | `download_ingest_only` | Download standard/basic datasets or use R tooling; record version/date |
| WVS / EVS | Values survey microdata and aggregate survey analysis | `download_ingest_only` | Register/download official files; respect non-commercial and citation terms |
| Afrobarometer | Public-opinion surveys in African countries | `download_ingest_only` | Download merged round files and read weights/sample documentation |
| CSES | Comparative electoral survey modules | `download_ingest_only` | Download IMD/modules with codebooks and weights |
| ANES | U.S. election studies, time-series and cumulative survey files | `download_ingest_only` | Download official CSV/Stata/SPSS release files |
| ESS | European public-opinion survey rounds | `download_ingest_only` | Use ESS Data Portal or official packages; preserve weights and edition |
| GSS | U.S. general social attitudes survey | `download_ingest_only` | Use official extract/download workflow |
| DPI | Political institutions, elections, government systems, veto players | `download_ingest_only` | Download the current IDB DPI release and metadata |
| Correlates of War | Interstate war, disputes, alliances, capabilities, contiguity, IGO membership | `download_ingest_only` | Download versioned datasets and codebooks |
| Comparative Agendas Project | Policy agendas, hearings, bills, speeches, laws, media/policy attention | `download_ingest_only` | Download project-specific CSV and codebook |
| MIT Election Data and Science Lab | U.S. election returns and election administration data | `download_ingest_only` | Download dataset-specific files and documentation |
| International IDEA | Voter turnout, direct democracy, electoral systems, political finance | `download_ingest_only` | Use official tools/downloads; verify terms and coverage |
| WID.world | Income/wealth inequality and distributional national accounts | `download_ingest_only` or package-assisted | Use WID bulk download or R/Python tooling; record metadata |
| WIID | Cross-national income inequality series | `download_ingest_only` | Download UNU-WIDER versioned files |
| SWIID | Harmonized Gini/redistribution estimates | `download_ingest_only` | Download versioned SWIID files and cite version |
| China City Statistical Yearbook / XMU panel | China prefecture-city year socioeconomic panel, core city controls and outcomes | `download_ingest_only` | Prefer official NBS yearbook definitions; XMU open panel is a large RAR archive covering 2004-2020 |
| Peking University Digital Financial Inclusion Index | Province/city/county digital finance measures for China | `download_ingest_only` | Free request/download workflow; cite PKU DFIIC report and use the project team's terms |
| MOHURD construction yearbooks | China urban construction, municipal infrastructure, water/gas/roads/green space | `download_ingest_only` | Use MOHURD yearbook index/publication workflow; no stable open REST API |
| China Land Market Network | Land conveyance, land finance, parcel announcements and supply results | `download_ingest_only` | Official web portal; use bounded, logged acquisition and do not treat as stable API |
| China NBS national data | Chinese macro and statistical indicators | `download_ingest_only` or fragile website backend | Prefer official downloads/pages; treat unofficial `easyquery`-style endpoints as unstable |

## Request Patterns

### Public No-Secret APIs

- World Bank: call V2 endpoints only. Add `format=json`, `per_page`, and
  explicit country/indicator filters. Use `date=YYYY:YYYY` for bounded panels.
- OECD/Eurostat/ECB/ILOSTAT: discover datasets with `dataflow`, then use
  source-generated SDMX URLs or filtered `data` queries. Prefer CSV outputs
  when available for pandas/R ingestion.
- WHO GHO: start with OData indicator discovery, then call indicator-specific
  endpoints. Keep query filters explicit because some indicators are large.
- UNHCR: use `/population/v1/` endpoints with `limit`, `page`, year bounds,
  and country filters. Record origin/asylum fields carefully.
- OWID Grapher: use chart URLs ending in `.csv`, `.metadata.json`, or `.zip`.
  Check chart metadata because some underlying data are non-redistributable.
- NASA POWER: use monthly/daily point or regional endpoints. Do not request
  spatial precision finer than the source resolution.
- Federal Register: use `documents.json` with date/agency/type/term filters.
  Keep pagination bounded; the API exposes many document URLs and abstracts.
- Dataverse/Crossref/DataCite: use metadata APIs for discovery. Include contact
  email where supported, respect cursor pagination, and deduplicate by DOI.
- Static CSV/zip sources such as Voteview and ParlGov should be downloaded
  with SHA256 hashes and release/access dates.
- GDELT: make small DOC/GEO/TV API calls during exploration. For event-scale or
  historical work, use raw files or BigQuery instead of paginating live APIs.

### Free Key or Account APIs

- Store keys in environment variables:
  `CENSUS_API_KEY`, `FRED_API_KEY`, `BEA_API_KEY`, `BLS_API_KEY`,
  `EIA_API_KEY`, `NOAA_CDO_TOKEN`, `IPUMS_API_KEY`, `COMTRADE_API_KEY`,
  `OPENALEX_API_KEY`, `SEMANTIC_SCHOLAR_API_KEY`, `ORCID_ACCESS_TOKEN`,
  `UCDP_API_TOKEN`, `MANIFESTO_API_KEY`, `OPENAQ_API_KEY`, `IATI_API_KEY`,
  `ACLED_API_KEY`, `MEDIA_CLOUD_API_KEY`.
- Do not include secrets in `.aiss`, notebooks, logs, Markdown, shell history,
  issue comments, or examples.
- Prefer official client packages only when they reduce errors:
  Python: `requests`, `pandas`, `wbgapi` or `wbdata`, `fredapi`, `census`,
  `ipumspy`, `pyalex`, `pandasdmx`, `comtradeapicall`, `dataverse`, `pyreadstat`.
  R: `WDI`, `OECD`, `eurostat`, `fredr`, `censusapi`, `ipumsr`, `openalexR`,
  `comtradr`, `manifestoR`, `Rilostat`, `essurvey`, `anesrake`.
- For IPUMS, DHS microdata, ACLED, WVS, EVS, UCDP, Manifesto, and similar
  human-registration sources, verify that the user has the right collection
  access before building automation.

### Download-Ingest Sources

- Treat downloaded files as source artifacts: keep original filename, access
  date, release/version, URL, SHA256, row count, and codebook path.
- Never overwrite raw restricted microdata or survey files with cleaned files.
- For survey sources, always preserve weight variables, sample design notes,
  country/round identifiers, and missing-value codebooks.
- For political-institutions sources, record whether country-year, election,
  party, cabinet, dyad, or event is the unit of analysis before merging.
- For large archives, keep the immutable raw archive plus an extraction
  manifest. Cleaned CSV/Stata/Excel derivatives should live in a separate
  staging directory and include source-file checksums.

## Source Notes

### Global Country-Year Panels

- Treat country-year panels as joinable source artifacts, not as a single
  canonical truth table. Start from a stable ISO3 spine for World Bank, PWT,
  Maddison, UNDP HDR, QoG, and V-Dem, and separately document any COW state-code
  joins because COW state membership and country-code definitions differ from
  ISO3.
- Penn World Table 11.0 is the first-stop annual macro/productivity panel when
  the design needs PPP-adjusted output, expenditure, capital, labor, hours, or
  TFP concepts for modern countries. Verify the exact real/nominal concept and
  base-year treatment before merging with World Bank or IMF indicators.
- Maddison Project Database 2023 is the first-stop long-run economic history
  panel. It is strong for historical GDP/population coverage, but country
  boundaries, predecessor states, and historical aggregates require explicit
  sample decisions.
- UNDP HDR time-series CSV is convenient for human-development indices and
  components. HDR API 2.0 requires an API key/subscription, so no-key automation
  should use the official CSV download and record the release year.
- Correlates of War National Material Capabilities is the first-stop IR
  state-year capabilities panel. Use COW state system membership, COW `ccode`,
  and release version in provenance; do not name-merge it into ISO panels
  without a checked crosswalk.
- For publication work, keep source-specific codebooks and citations attached
  to the row provenance. Concepts such as GDP per capita, real GDP, population,
  state system membership, democracy scores, and human development can differ
  across sources even when column names look similar.

### China Prefecture City-Year Panels

- Start with a stable city-code spine. `yescallop/areacodes` is convenient for
  historical county-and-above administrative codes and old/new-code mapping,
  but publication work should still document the MCA/NBS administrative
  definition used by the analysis.
- For core socioeconomic controls, use official China City Statistical Yearbook
  definitions. NBS describes the city yearbook as covering prefecture-level and
  county-level city statistics, including population, resources and environment,
  economic development, technology innovation, living conditions, public
  services, and infrastructure. Treat it as a publication/download source, not
  as a stable public API.
- The XMU open archive for `2004-2020《中国城市统计年鉴》面板数据` is suitable as a
  reusable seed artifact when disk and bandwidth allow. Preserve the RAR,
  extraction manifest, cleaned tabular exports, and SHA256 hashes; check
  variable definitions against the NBS yearbook before manuscript claims.
- For digital-finance mechanisms, the PKU DFIIC report says the index covers
  provinces, 337 prefecture-level cities, and about 2,800 counties; current
  report access says the full data can be requested from the project team for
  free. Classify it as free download/request, not no-auth API.
- For environmental covariates, CEADs city catalogs, CHAP/ChinaHighPM2.5, and
  EOG VIIRS are strong candidates. CHAP and VIIRS are gridded products, so
  city-year panels require explicit boundary vintage, projection, raster
  aggregation rule, and area/urban-mask decision.
- For infrastructure covariates, MOHURD construction yearbooks are useful but
  remain yearbook/publication workflows. For land-finance variables, China Land
  Market Network is an official web portal; use logged, bounded scraping or
  downloads only after checking terms and robots.
- Do not merge China city panels by city name alone. Use administrative code,
  year, boundary-vintage decision, municipality/direct-admin exceptions, and
  split/merge notes.

### Conflict, Parties, Elections, And Policy

- UCDP API: free of charge but token-authenticated. Use
  `x-ucdp-access-token` and versioned URLs such as
  `https://ucdpapi.pcr.uu.se/api/gedevents/26.1?pagesize=100&page=1`.
- Correlates of War: public versioned downloads for wars, MIDs, alliances,
  capabilities, contiguity, and related IR datasets.
- Manifesto Project: current dataset downloads and API/corpus access require a
  free account/API key. Use `manifestoR` when working in R.
- ParlGov: static CSV/SQLite downloads are convenient for parties, elections,
  cabinets, and party-family covariates in Europe.
- Voteview: static CSVs are direct and useful for U.S. roll-call/member panels.
- Comparative Agendas Project: use dataset-specific CSVs plus codebooks for
  policy attention, legislative, speech, law, and media agenda work.
- DPI and MIT Election Lab: both are file-download sources; cite release and
  variable documentation.

### Surveys And Microdata

- IPUMS, Census, DHS metadata, ANES, CSES, ESS, GSS, Afrobarometer, WVS, and
  EVS are often stronger than aggregate APIs when the paper needs individual
  heterogeneity, subgroup mechanisms, or harmonized sampling weights.
- API convenience should not override survey design. For publication work,
  inspect weights, strata/PSU fields, question wording, missing-value codes, and
  harmonization notes.

### Health, Labor, Climate, And Development Covariates

- WHO GHO/Athena, ILOSTAT, NASA POWER, FAOSTAT, UNHCR, OWID, and World Bank
  are good candidates for mechanism/control variables when the main data are
  political or survey data.
- NASA POWER is gridded and model/reanalysis based. Treat it as a contextual
  climate covariate, not as a replacement for station-level measurement when
  local weather precision is central.
- OWID is excellent for quick chart-level panels, but its metadata can identify
  non-redistributable upstream sources. Check each chart before publishing a
  derived dataset.

### Inequality And Fiscal/Macro Data

- WID, WIID, SWIID, BEA, BLS, EIA, ECB, OECD, Eurostat, IMF, FRED, and World
  Bank cover different units and concepts. Do not merge by indicator name alone;
  compare definitions, units, nominal/real treatment, base year, and coverage.
- BEA/BLS/EIA/NOAA are free but key/token-based for normal API use. Queue them
  until the relevant environment variable is present.

## Examples

```bash
curl 'https://api.worldbank.org/v2/country/CHN/indicator/SP.POP.TOTL?format=json&date=2000:2024&per_page=20000'
curl 'https://ghoapi.azureedge.net/api/Indicator?$top=10'
curl 'https://api.unhcr.org/population/v1/countries/?limit=10'
curl 'https://ourworldindata.org/grapher/life-expectancy.csv'
curl 'https://www.federalregister.gov/api/v1/documents.json?per_page=5&conditions%5Bterm%5D=climate'
curl -H "x-ucdp-access-token: ${UCDP_API_TOKEN}" 'https://ucdpapi.pcr.uu.se/api/gedevents/26.1?pagesize=100&page=1'
```

## Safety Checklist

- Record access date, endpoint, query parameters, package version, and API
  response status.
- Use bounded queries before bulk pulls.
- Respect robots, terms, redistribution limits, survey registration agreements,
  and microdata access approvals.
- Cache immutable metadata and cite official source documentation in research
  artifacts.
- If a source is rate-limited, blocked, or returns authentication errors, report
  that as a source-access finding rather than silently switching to scraped data.
