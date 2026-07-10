# Public Data Sources for Empirical Social Science

This list is a starting point for source discovery. Before collection, consult current official
documentation and inspect a small sample of the actual data.

## Access conditions

| Access condition | Meaning | Implication for the study |
|---|---|---|
| Open public access | Data or metadata can be consulted without an individual account | Establish temporal and geographic coverage, the unit of observation, and the terms of use. |
| Free registration | Access requires a free account, key, token, or application | Confirm that the proposed use and any redistribution are permitted. |
| Public or registered download | Data are released as files, sometimes after registration | Retain the original release, codebook, version, and date of access. |

Free access does not imply anonymous, unlimited, or redistributable access. Record the actual terms.

## Candidate sources

| Source | Substantive use | Access condition | Where to begin |
|---|---|---|---|
| World Bank Indicators | Cross-country development, governance proxies, education, poverty, population, macro panel data | Open public access | `https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?format=json&per_page=20000` |
| Penn World Table 11.0 | Country-year income, output, input, productivity, PPP, labor, capital, and TFP measures | Public or registered download | Official GGDC Excel/Stata downloads; inspect the version notes and variable definitions before selecting a measure. |
| Maddison Project Database 2023 | Long-run country-year GDP per capita, population, and comparative income levels | Public or registered download | Official GGDC Excel/Stata downloads; use the documented full-data sheet and record the database version. |
| UNDP HDR composite-index time series | HDI, IHDI, GDI, GII, PHDI, life expectancy, schooling, and GNI components by country-year | Public download for CSV; free registration for HDR API 2.0 | The official composite-indices time-series CSV is usually sufficient; record the release year and definitions. |
| Correlates of War National Material Capabilities | State-year CINC, military, industrial, energy, urban population, and total population capabilities | Public or registered download | Official COW ZIP; inspect both abridged and supplementary files and document state-system coding choices. |
| OECD Data Explorer API | OECD and partner-country macro, education, labor, fiscal, regional statistics | Open public access | `https://sdmx.oecd.org/public/rest/dataflow/all`, then filtered SDMX data queries |
| Eurostat | EU and European regional/NUTS statistics | Open public access | Begin with the dissemination database and the definitions of the relevant table or series. |
| ECB Data Portal API | Euro-area monetary, financial, balance sheet, exchange-rate, bank, and macro-financial time series | Open public access | `https://data-api.ecb.europa.eu/service/dataflow/ECB/all/latest?detail=allstubs` |
| IMF Data API | IMF macro, financial, balance of payments, government finance, and country data | Open public access for SDMX data; portal exploration may require sign-in | Consult the current IMF documentation and confirm series coverage, definitions, and revisions. |
| UN SDG API / UNData | UN indicator and SDG data | Open public access for many endpoints | Prefer SDG API for SDG indicators; UNData API coverage varies by datamart |
| WHO GHO / Athena | Health indicators, mortality, disease burden, health systems, tobacco, nutrition | Open public access | `https://ghoapi.azureedge.net/api/Indicator`, then indicator-specific OData calls |
| ILOSTAT | Labor force, employment, unemployment, informality, wages, working conditions | Open public access for SDMX/bulk metadata and many downloads | `https://sdmx.ilo.org/rest/v1/dataflow/all/all/latest?detail=allstubs` |
| UNHCR Refugee Statistics API | Refugees, asylum applications, IDPs, statelessness, origin/asylum country panels | Open public access | Begin with the Refugee Data Finder and distinguish origin, asylum, stock, and flow measures. |
| OWID Grapher | Clean chart-level panels for health, demography, inequality, climate, conflict, technology | Open public access for redistributable Grapher charts | Append `.csv`, `.metadata.json`, or `.zip` to a Grapher chart URL; check metadata license. |
| NASA POWER | Gridded climate/weather covariates for social-science panels and historical context | Open public access | `https://power.larc.nasa.gov/api/temporal/monthly/point?...` |
| Federal Register API | U.S. federal rules, notices, policy text, agency activity, regulatory agenda evidence | Open public access | `https://www.federalregister.gov/api/v1/documents.json?...` |
| Harvard Dataverse | Replication packages, social-science datasets, DOI-backed research data discovery | Open public access for public search and metadata | Search the official Dataverse catalogue and inspect the full dataset record. |
| Research-data repositories | Finding public datasets, replication packages, DOI-backed records, and possible sources before a named dataset is chosen | Open metadata search; files are public only when the individual record permits download | See `references/discovery-platforms.md` for Zenodo, DataCite, Dataverse, Figshare, Dryad, OpenAIRE, re3data, and OSF. |
| Crossref | DOI metadata, publication metadata, funder metadata | Open public access | REST API with a polite `mailto` parameter when possible |
| DataCite | DOI metadata for datasets and research objects | Open public access for metadata retrieval | REST API metadata retrieval without auth; auth is for DOI create/update |
| Voteview | U.S. Congress roll-call votes, member ideology, NOMINATE scores | Open public access for static CSV downloads | `https://voteview.com/static/data/out/members/HSall_members.csv` and related CSVs |
| ParlGov | European parties, elections, cabinets, party families, government composition | Open public access static CSV/SQLite downloads | `https://parlgov.org/data/parlgov-development_csv-utf-8.zip` |
| FAOSTAT | Agriculture, food, land, prices, emissions, production, trade | Open public access or bulk download depending on the series | Use the official portal and establish the domain, item, element, unit, and geographic coverage. |
| yescallop/areacodes | China administrative-code history and city/county crosswalk spine | Open public access static CSV | `https://raw.githubusercontent.com/yescallop/areacodes/master/result.csv`; verify against MCA/NBS definitions before publication |
| CEADs city catalogs | China city carbon, industrial process emissions, water, mercury, and city MRIO discovery | Open public access for catalog pages; downloads may require an account | Begin with the city-data catalogue, then inspect the documentation and access conditions for the selected series. |
| CHAP / ChinaHighPM2.5 | China gridded annual/monthly/daily PM2.5 and other air-pollution covariates | Open public metadata and downloads | Inspect the repository record and files; city-year values require explicit boundary and spatial-aggregation choices. |
| EOG VIIRS Nighttime Lights | Annual global night-light covariates for China city-year panels | Public or registered download | Download annual GeoTIFFs from EOG VNL; aggregate to city-year with a fixed boundary vintage |
| GDELT | Global news, events, media agenda, geolocation, text search | Open public access | Evaluate event ontology, source coverage, duplication, geocoding, and historical versioning before treating counts as political events. |
| U.S. Census Data API | ACS, decennial, geography, economic and community variables in the United States | Free registration for sustained access | Begin with the relevant survey documentation, geography, universe, and table definitions. |
| FRED | Macro, financial, regional, historical U.S. and international time series | Free registration | Trace each series to its producing institution and preserve revision notes. |
| BEA | U.S. national accounts, regional GDP/income, international transactions, industry accounts | Free registration | Consult BEA methods and metadata for the selected table and vintage. |
| BLS | U.S. labor, CPI/PPI, wages, employment, productivity time series | Limited open access; free registration for fuller access | Check seasonal adjustment, series breaks, and population or establishment coverage. |
| EIA | Energy production, prices, consumption, electricity, emissions-related energy measures | Free registration | Use the relevant survey and series documentation; bulk releases may differ from the API. |
| NOAA CDO | Station weather and climate normals for the U.S. and some global holdings | Free registration | Inspect station coverage, missing observations, and changes in the observing network. |
| IPUMS API | Census, CPS, NHGIS, ATUS, international and harmonized microdata extracts | Free registration; collection-specific permission may apply | Read the harmonization and sample documentation for the relevant collection. |
| UN Comtrade | International trade, product flows, political economy of trade | Free registration for ordinary access | Record the reporter, partner, product classification, flow, valuation, and revision vintage. |
| OpenAlex | Bibliometrics, scholarly works, authors, institutions, sources, topics, citations | Open search; free registration improves access | Use persistent identifiers and verify bibliographic records against the publication itself. |
| Semantic Scholar | Scholarly paper search and citation-graph discovery | Open search; free registration improves access | Treat records as discovery aids and verify claims in the underlying publication. |
| ORCID | Public researcher identifiers and profile metadata | Free registration for programmatic access | Treat self-reported profiles as identifiers, not independent evidence of affiliation or output. |
| UCDP API | Conflict events, dyads, one-sided/non-state violence, battle deaths | Free registration | Use the current release, definitions, inclusion thresholds, and versioned codebook. |
| Manifesto Project | Party manifestos, party positions, coded policy emphasis | Free registration | Consult corpus coverage, coding categories, uncertainty, and version notes. |
| OpenAQ | Air-quality monitors and pollutant observations | Free registration | Examine monitor siting, reporting frequency, missingness, and API version. |
| IATI Datastore | Aid, development finance, activities, budgets, transactions | Free registration | Distinguish commitments, disbursements, transactions, activities, and reporting organizations. |
| ACLED | Conflict and protest event data | Free registration | myACLED account plus OAuth or cookie auth; check current access policy |
| DHS Program API | DHS indicators, countries, surveys, datasets metadata | Open public access for metadata; microdata requires account approval | Use the public catalogue for metadata and obtain microdata through DHS or IPUMS DHS under the applicable terms. |
| Media Cloud | News sources and article search | Free registration or project access | Confirm current account, collection coverage, and conditions of use. |
| V-Dem | Democracy indicators and country-year panels | Public or registered download | Download versioned CSV/R/Stata/SPSS files; record version and release date |
| QoG | Curated comparative politics country-year/cross-section datasets | Public or registered download | Download standard/basic datasets or use R tooling; record version/date |
| WVS / EVS | Values survey microdata and aggregate survey analysis | Public or registered download | Register/download official files; respect non-commercial and citation terms |
| Afrobarometer | Public-opinion surveys in African countries | Public or registered download | Download merged round files and read weights/sample documentation |
| CSES | Comparative electoral survey modules | Public or registered download | Download IMD/modules with codebooks and weights |
| ANES | U.S. election studies, time-series and cumulative survey files | Public or registered download | Download official CSV/Stata/SPSS release files |
| ESS | European public-opinion survey rounds | Public or registered download | Use the ESS Data Portal; preserve weights, fieldwork information, and edition. |
| GSS | U.S. general social attitudes survey | Public or registered download | Use an official extract or data release and retain its codebook. |
| DPI | Political institutions, elections, government systems, veto players | Public or registered download | Download the current IDB DPI release and metadata |
| Correlates of War | Interstate war, disputes, alliances, capabilities, contiguity, IGO membership | Public or registered download | Download versioned datasets and codebooks |
| Comparative Agendas Project | Policy agendas, hearings, bills, speeches, laws, media/policy attention | Public or registered download | Download project-specific CSV and codebook |
| MIT Election Data and Science Lab | U.S. election returns and election administration data | Public or registered download | Download dataset-specific files and documentation |
| International IDEA | Voter turnout, direct democracy, electoral systems, political finance | Public or registered download | Use official tools/downloads; verify terms and coverage |
| WID.world | Income/wealth inequality and distributional national accounts | Public or registered download | Use the official bulk release and record its definitions, population groups, and version. |
| WIID | Cross-national income inequality series | Public or registered download | Download UNU-WIDER versioned files |
| SWIID | Harmonized Gini/redistribution estimates | Public or registered download | Download versioned SWIID files and cite version |
| China City Statistical Yearbook / XMU panel | China prefecture-city year socioeconomic panel, core city controls and outcomes | Public or registered download | Prefer official NBS yearbook definitions; XMU open panel is a large RAR archive covering 2004-2020 |
| Peking University Digital Financial Inclusion Index | Province/city/county digital finance measures for China | Public or registered download | Request or download the data from the project, cite the PKU DFIIC report, and follow its terms. |
| MOHURD construction yearbooks | China urban construction, municipal infrastructure, water/gas/roads/green space | Public or registered download | Use the official yearbook index or publication and record the edition. |
| China Land Market Network | Land conveyance, land finance, parcel announcements and supply results | Public or registered download | Use the official portal under its terms and assess the completeness and stability of the records. |
| China NBS national data | Chinese macro and statistical indicators | Public or registered download or fragile website backend | Prefer official downloads/pages; treat unofficial `easyquery`-style endpoints as unstable |

## Assessing access and suitability

Open access does not settle whether a source is appropriate for a study. Begin
with the codebook, the population represented, the unit of observation, the
period and places covered, and the history of revisions. Retrieve a small
sample before committing to the source. This often reveals discrepancies in
identifiers, missing-value conventions, temporal coverage, or the meaning of a
seemingly familiar measure.

Public interfaces such as those maintained by the World Bank, OECD, Eurostat,
WHO, UNHCR, and Dataverse are useful for examining metadata and obtaining
well-defined subsets. Their convenience should not substitute for reading the
source documentation. Repository and bibliographic records are especially
valuable for discovery, but the underlying dataset, codebook, and associated
publication remain the objects that require scholarly assessment.

Registered sources may impose conditions on particular collections, users, or
forms of redistribution. Confirm those conditions before beginning the study.
For IPUMS, DHS microdata, ACLED, WVS, EVS, UCDP, the Manifesto Project, and
similar sources, access to a catalogue or metadata page does not itself confer
permission to use every collection.

For downloaded data, retain the original release and record its version, date,
codebook, and source. Survey data require particular attention to weights,
strata, primary sampling units, question wording, harmonization, and special
missing-value codes. Institutional and event data require an explicit account
of the unit of observation and of the rules that create country-years,
elections, parties, cabinets, dyads, or events.

## Source Notes

### Global Country-Year Panels

- Country-year datasets embody different decisions about states, borders,
  measurement, and missingness; they should not be treated as interchangeable.
  World Bank, PWT, Maddison, UNDP HDR, QoG, and V-Dem can usually be harmonized
  through ISO3 codes, whereas COW state membership and country codes require a
  separate and documented crosswalk.
- Penn World Table 11.0 is the first-stop annual macro/productivity panel when
  the design needs PPP-adjusted output, expenditure, capital, labor, hours, or
  TFP concepts for modern countries. Verify the exact real/nominal concept and
  base-year treatment before merging with World Bank or IMF indicators.
- Maddison Project Database 2023 is the first-stop long-run economic history
  panel. It is strong for historical GDP/population coverage, but country
  boundaries, predecessor states, and historical aggregates require explicit
  sample decisions.
- UNDP HDR time-series CSV is convenient for human-development indices and
  components. Record the release year and consult the definitions before
  comparing it with measures from other organizations.
- Correlates of War National Material Capabilities is the first-stop IR
  state-year capabilities panel. Use COW state system membership, COW `ccode`,
  and release version in provenance; do not name-merge it into ISO panels
  without a checked crosswalk.
- Keep source-specific codebooks and citations with the analytical data.
  Concepts such as GDP per capita, real GDP, population, state-system
  membership, democracy, and human development can differ across sources even
  when variable names look similar.

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
- The XMU open archive for `2004-2020《中国城市统计年鉴》面板数据` can be a useful
  starting point. Check its variables against the relevant NBS yearbooks,
  document any cleaning or recoding, and do not assume that a harmonized label
  has an invariant definition across years.
- For digital-finance mechanisms, the PKU DFIIC report says the index covers
  provinces, 337 prefecture-level cities, and about 2,800 counties; current
  report access says the full data can be requested from the project team for
  free. Classify it as free download/request, not no-auth API.
- For environmental covariates, CEADs city catalogs, CHAP/ChinaHighPM2.5, and
  EOG VIIRS are strong candidates. CHAP and VIIRS are gridded products, so
  city-year panels require explicit boundary vintage, projection, raster
  aggregation rule, and area/urban-mask decision.
- MOHURD construction yearbooks are useful for infrastructure covariates. For
  land-finance variables, the China Land Market Network is an official web
  source; consult its terms of access and assess the completeness of the
  resulting records.
- Do not merge China city panels by city name alone. Use administrative code,
  year, boundary-vintage decision, municipality/direct-admin exceptions, and
  split/merge notes.

### Conflict, Parties, Elections, And Policy

- UCDP access is free after registration. Record the release version and read
  the event, dyad, inclusion, and battle-death definitions before analysis.
- Correlates of War: public versioned downloads for wars, MIDs, alliances,
  capabilities, contiguity, and related IR datasets.
- Manifesto Project datasets require a free account. Record the corpus version
  and consider the implications of coding uncertainty and manifesto coverage.
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
- BEA, BLS, EIA, and NOAA provide free registered access. Their methods,
  revisions, seasonal adjustment, and geographic coverage matter more to the
  study than the particular means of retrieval.

## What to record

For every source used in an analysis, record the producing institution, dataset
and release, date of access, population and unit of observation, temporal and
geographic coverage, key variable definitions, missingness, known revisions,
and any restrictions on use or redistribution. Also record the transformations
that connect the released data to the analytical measure. This is part of the
substantive account of the evidence, not merely a matter of data management.
