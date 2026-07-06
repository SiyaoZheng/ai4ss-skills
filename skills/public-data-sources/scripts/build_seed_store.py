#!/usr/bin/env python3
"""Build a small local seed store for free public social-science sources.

The output is intentionally generated under tmp/ by default. It is a cache and
provenance aid for agents, not a committed data package.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html
import http.client
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any


USER_AGENT = "ai4ss-public-data-sources/0.1"
DEFAULT_OUT_DIR = Path("tmp/public-data-sources")
FETCHED_AT = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()

WORLD_BANK_INDICATORS = [
    "SP.POP.TOTL",
    "NY.GDP.MKTP.CD",
    "NY.GDP.PCAP.CD",
    "SE.SEC.ENRR",
    "SP.DYN.LE00.IN",
    "SP.DYN.TFRT.IN",
    "SI.POV.GINI",
    "SL.UEM.TOTL.ZS",
]

VDEM_CORE_COLUMNS = [
    "country_name",
    "country_text_id",
    "country_id",
    "year",
    "historical_date",
    "project",
    "historical",
    "e_regiongeo",
    "e_regionpol",
    "e_regionpol_6C",
    "e_regionpol_6C_name",
    "v2x_polyarchy",
    "v2x_libdem",
    "v2x_partipdem",
    "v2x_delibdem",
    "v2x_egaldem",
    "v2x_api",
    "v2x_mpi",
    "v2x_freexp_altinf",
    "v2x_frassoc_thick",
    "v2x_suffr",
    "v2x_elecoff",
    "v2x_liberal",
    "v2xcl_rol",
    "v2x_jucon",
    "v2xlg_legcon",
    "v2x_corr",
    "v2x_cspart",
    "v2x_accountability",
    "v2x_gender",
    "v2x_rule",
]

QOG_DOWNLOADS = [
    {
        "source_id": "qog_basic_ts",
        "table": "qog_basic_ts",
        "access_class": "download_ingest_only",
        "url": "https://www.qogdata.pol.gu.se/data/qog_bas_ts_jan26.csv",
    },
    {
        "source_id": "qog_basic_cs",
        "table": "qog_basic_cs",
        "access_class": "download_ingest_only",
        "url": "https://www.qogdata.pol.gu.se/data/qog_bas_cs_jan26.csv",
    },
]

QOG_STANDARD_DOWNLOADS = [
    {
        "source_id": "qog_standard_ts",
        "table": "qog_standard_ts",
        "access_class": "download_ingest_only",
        "url": "https://www.qogdata.pol.gu.se/data/qog_std_ts_jan26.csv",
    },
    {
        "source_id": "qog_standard_cs",
        "table": "qog_standard_cs",
        "access_class": "download_ingest_only",
        "url": "https://www.qogdata.pol.gu.se/data/qog_std_cs_jan26.csv",
    },
]

PWT_11_0_EXCEL_URL = "https://dataverse.nl/api/access/datafile/554105"
MADDISON_2023_EXCEL_URL = "https://dataverse.nl/api/access/datafile/421302"
UNDP_HDR_COMPOSITE_TIME_SERIES_CSV_URL = (
    "https://hdr.undp.org/sites/default/files/2025_HDR/"
    "HDR25_Composite_indices_complete_time_series.csv"
)
COW_NMC_6_ZIP_URL = "http://correlatesofwar.org/wp-content/uploads/NMC_Documentation-6.0.zip"

CHINA_AREACODES_URL = "https://raw.githubusercontent.com/yescallop/areacodes/master/result.csv"
CHINA_XMU_CITY_STATS_PANEL_URL = (
    "https://econpub.xmu.edu.cn/elib/media/datasets/"
    "2004-2020%E3%80%8A%E4%B8%AD%E5%9B%BD%E5%9F%8E%E5%B8%82%E7%BB%9F%E8%AE%A1"
    "%E5%B9%B4%E9%89%B4%E3%80%8B%E9%9D%A2%E6%9D%BF%E6%95%B0%E6%8D%AE.rar"
)
CHINA_CHAP_PM25_ZENODO_API = "https://zenodo.org/api/records/6398971"
CHINA_CEADS_CITY_CATALOG_PAGES = [
    (
        "ceads_city_carbon_inventory",
        "carbon_inventory",
        "https://www.ceads.net/data/carbon-inventory/city-level/",
    ),
    (
        "ceads_city_input_output",
        "input_output",
        "https://www.ceads.net/data/input-output-tables/city/",
    ),
]
CHINA_NBS_CITY_BACKEND_PROBES = [
    (
        "easyquery_city_indicator_tree",
        "https://data.stats.gov.cn/easyquery.htm?m=getTree&dbcode=csnd&wdcode=zb",
    ),
    (
        "easyquery_city_region_tree",
        "https://data.stats.gov.cn/easyquery.htm?m=getTree&dbcode=csnd&wdcode=reg",
    ),
    (
        "new_site_city_tree",
        "https://data.stats.gov.cn/dg/api/new/queryIndexTreeAsync?dbcode=csnd&wdcode=zb",
    ),
]

BLOCKED_OR_CONFIGURED_SOURCES = [
    {
        "source_id": "us_census",
        "source_name": "U.S. Census Data API",
        "access_class": "free_key_required",
        "auth_env_var": "CENSUS_API_KEY",
        "official_url": "https://www.census.gov/data/developers/guidance/api-user-guide.html",
        "reason": "Free key recommended for normal automated use.",
    },
    {
        "source_id": "fred",
        "source_name": "FRED API",
        "access_class": "free_key_required",
        "auth_env_var": "FRED_API_KEY",
        "official_url": "https://fred.stlouisfed.org/docs/api/api_key.html",
        "reason": "FRED web service requires a free API key.",
    },
    {
        "source_id": "ipums",
        "source_name": "IPUMS API",
        "access_class": "free_key_required",
        "auth_env_var": "IPUMS_API_KEY",
        "official_url": "https://developer.ipums.org/docs/v2/get-started/",
        "reason": "Requires account, API key, and collection access.",
    },
    {
        "source_id": "un_comtrade",
        "source_name": "UN Comtrade API",
        "access_class": "free_key_required",
        "auth_env_var": "COMTRADE_API_KEY",
        "official_url": "https://uncomtrade.org/docs/api-subscription-keys/",
        "reason": "Normal API use requires a subscription key and has quotas.",
    },
    {
        "source_id": "undp_hdr_api",
        "source_name": "UNDP HDR API 2.0",
        "access_class": "free_key_required",
        "auth_env_var": "UNDP_HDR_API_KEY",
        "official_url": "https://hdrdata.org/api-details",
        "reason": "HDR API 2.0 requires an API key/subscription; use the official no-key CSV download when adequate.",
    },
    {
        "source_id": "openalex",
        "source_name": "OpenAlex API",
        "access_class": "free_key_required",
        "auth_env_var": "OPENALEX_API_KEY",
        "official_url": "https://docs.openalex.org/how-to-use-the-api/api-overview",
        "reason": "No-key requests exist, but reliable agent use should identify and key itself.",
    },
    {
        "source_id": "semantic_scholar",
        "source_name": "Semantic Scholar API",
        "access_class": "free_key_required",
        "auth_env_var": "SEMANTIC_SCHOLAR_API_KEY",
        "official_url": "https://api.semanticscholar.org/api-docs/",
        "reason": "Shared unauthenticated quota is fragile for automation.",
    },
    {
        "source_id": "orcid",
        "source_name": "ORCID Public API",
        "access_class": "free_key_required",
        "auth_env_var": "ORCID_ACCESS_TOKEN",
        "official_url": "https://info.orcid.org/documentation/api-tutorials/api-tutorial-read-data-on-a-record/",
        "reason": "Public API uses OAuth access tokens.",
    },
    {
        "source_id": "acled",
        "source_name": "ACLED",
        "access_class": "free_key_required",
        "auth_env_var": "ACLED_API_KEY",
        "official_url": "https://acleddata.com/data-export-tool/",
        "reason": "Requires account/API access; access policy can change.",
    },
    {
        "source_id": "media_cloud",
        "source_name": "Media Cloud",
        "access_class": "free_key_required",
        "auth_env_var": "MEDIA_CLOUD_API_KEY",
        "official_url": "https://mediacloud.org/",
        "reason": "Requires project/account access for current APIs.",
    },
    {
        "source_id": "ucdp",
        "source_name": "UCDP API",
        "access_class": "free_key_required",
        "auth_env_var": "UCDP_API_TOKEN",
        "official_url": "https://ucdp.uu.se/apidocs/",
        "reason": "API is free of charge, but current access requires a token in x-ucdp-access-token.",
    },
    {
        "source_id": "manifesto_project",
        "source_name": "Manifesto Project API",
        "access_class": "free_key_required",
        "auth_env_var": "MANIFESTO_API_KEY",
        "official_url": "https://manifesto-project.wzb.eu/information/documents/api",
        "reason": "Requires a free Manifesto Project account and API key.",
    },
    {
        "source_id": "bea",
        "source_name": "U.S. BEA API",
        "access_class": "free_key_required",
        "auth_env_var": "BEA_API_KEY",
        "official_url": "https://apps.bea.gov/api/signup/",
        "reason": "Requires a free BEA API key for normal data retrieval.",
    },
    {
        "source_id": "bls",
        "source_name": "U.S. BLS Public Data API",
        "access_class": "free_key_required",
        "auth_env_var": "BLS_API_KEY",
        "official_url": "https://www.bls.gov/developers/api_faqs.htm",
        "reason": "Unauthenticated v1 exists with tight limits; v2 registration is required for normal agent use.",
    },
    {
        "source_id": "eia",
        "source_name": "U.S. EIA API",
        "access_class": "free_key_required",
        "auth_env_var": "EIA_API_KEY",
        "official_url": "https://www.eia.gov/opendata/",
        "reason": "API access requires a free API key; bulk downloads can be handled separately.",
    },
    {
        "source_id": "noaa_cdo",
        "source_name": "NOAA Climate Data Online API",
        "access_class": "free_key_required",
        "auth_env_var": "NOAA_CDO_TOKEN",
        "official_url": "https://www.ncdc.noaa.gov/cdo-web/webservices/getstarted",
        "reason": "Requires a free token; official limits are per-token.",
    },
    {
        "source_id": "openaq",
        "source_name": "OpenAQ API",
        "access_class": "free_key_required",
        "auth_env_var": "OPENAQ_API_KEY",
        "official_url": "https://docs.openaq.org/",
        "reason": "Current API requires an API key for reliable access.",
    },
    {
        "source_id": "iati",
        "source_name": "IATI Datastore API",
        "access_class": "free_key_required",
        "auth_env_var": "IATI_API_KEY",
        "official_url": "https://iatistandard.org/en/iati-tools-and-resources/iati-datastore/how-to-use-the-datastore-api/",
        "reason": "Current Datastore v3 documentation uses a free account subscription key.",
    },
    {
        "source_id": "wvs_evs",
        "source_name": "WVS / EVS",
        "access_class": "download_ingest_only",
        "auth_env_var": "",
        "official_url": "https://www.worldvaluessurvey.org/WVSContents.jsp",
        "reason": "Official workflow is registration and file download, not open bulk REST.",
    },
    {
        "source_id": "afrobarometer",
        "source_name": "Afrobarometer merged data",
        "access_class": "download_ingest_only",
        "auth_env_var": "",
        "official_url": "https://www.afrobarometer.org/data/merged-data/",
        "reason": "Free public survey files are downloaded by round, not exposed as a stable open REST API.",
    },
    {
        "source_id": "cses",
        "source_name": "Comparative Study of Electoral Systems",
        "access_class": "download_ingest_only",
        "auth_env_var": "",
        "official_url": "https://cses.org/data-download/download-data-documentation/",
        "reason": "Official workflow is module file download with documentation and weights.",
    },
    {
        "source_id": "anes",
        "source_name": "ANES time-series and cumulative files",
        "access_class": "download_ingest_only",
        "auth_env_var": "",
        "official_url": "https://electionstudies.org/data-center/anes-time-series-cumulative-data-file/",
        "reason": "Official workflow is versioned file download in CSV/Stata/SPSS formats.",
    },
    {
        "source_id": "ess",
        "source_name": "European Social Survey",
        "access_class": "download_ingest_only",
        "auth_env_var": "",
        "official_url": "https://www.europeansocialsurvey.org/data/",
        "reason": "Use official data portal or packages; do not treat it as a simple no-key REST source.",
    },
    {
        "source_id": "gss",
        "source_name": "General Social Survey",
        "access_class": "download_ingest_only",
        "auth_env_var": "",
        "official_url": "https://gss.norc.org/get-the-data",
        "reason": "Use official extract/download workflow with weights and release notes.",
    },
    {
        "source_id": "dpi",
        "source_name": "Database of Political Institutions",
        "access_class": "download_ingest_only",
        "auth_env_var": "",
        "official_url": "https://data.iadb.org/dataset/the-database-of-political-institutions-dpi-2023",
        "reason": "Versioned public dataset download; record release and metadata date.",
    },
    {
        "source_id": "cow",
        "source_name": "Correlates of War",
        "access_class": "download_ingest_only",
        "auth_env_var": "",
        "official_url": "https://correlatesofwar.org/data-sets/",
        "reason": "Public versioned datasets are downloadable with codebooks, not a single API.",
    },
    {
        "source_id": "cap",
        "source_name": "Comparative Agendas Project",
        "access_class": "download_ingest_only",
        "auth_env_var": "",
        "official_url": "https://www.comparativeagendas.net/datasets_codebooks",
        "reason": "Dataset and codebook downloads are selected by project/type.",
    },
    {
        "source_id": "mit_election_lab",
        "source_name": "MIT Election Data and Science Lab",
        "access_class": "download_ingest_only",
        "auth_env_var": "",
        "official_url": "https://electionlab.mit.edu/data",
        "reason": "Election datasets are public downloads with dataset-specific documentation.",
    },
    {
        "source_id": "wid",
        "source_name": "World Inequality Database",
        "access_class": "download_ingest_only",
        "auth_env_var": "",
        "official_url": "https://wid.world/data/",
        "reason": "Open-access inequality data are normally downloaded in bulk or via WID tooling.",
    },
    {
        "source_id": "wiid",
        "source_name": "UNU-WIDER WIID",
        "access_class": "download_ingest_only",
        "auth_env_var": "",
        "official_url": "https://www.wider.unu.edu/database/world-income-inequality-database-wiid",
        "reason": "Free versioned inequality files should be downloaded and cited by version.",
    },
    {
        "source_id": "swiid",
        "source_name": "SWIID",
        "access_class": "download_ingest_only",
        "auth_env_var": "",
        "official_url": "https://fsolt.org/swiid/",
        "reason": "Versioned inequality files are public downloads, not a live REST API.",
    },
    {
        "source_id": "dhs_microdata",
        "source_name": "DHS microdata",
        "access_class": "download_ingest_only",
        "auth_env_var": "",
        "official_url": "https://dhsprogram.com/data/",
        "reason": "Metadata are public; microdata require account approval.",
    },
    {
        "source_id": "china_nbs",
        "source_name": "China NBS national data",
        "access_class": "download_ingest_only",
        "auth_env_var": "",
        "official_url": "https://data.stats.gov.cn/",
        "reason": "Official site is public, but stable bulk API access is not guaranteed.",
    },
    {
        "source_id": "china_nbs_city_statistical_yearbook",
        "source_name": "China City Statistical Yearbook",
        "access_class": "download_ingest_only",
        "auth_env_var": "",
        "official_url": "https://www.stats.gov.cn/zs/tjwh/tjkw/tjzl/202302/t20230220_1913734.html",
        "reason": "Official source is a yearbook/publication workflow for city data, not a stable open API.",
    },
    {
        "source_id": "china_xmu_city_stats_yearbook_panel_2004_2020",
        "source_name": "XMU 2004-2020 China City Statistical Yearbook panel archive",
        "access_class": "download_ingest_only",
        "auth_env_var": "",
        "official_url": "https://econpub.xmu.edu.cn/elib/ds_detail/22/",
        "reason": "Public RAR archive is large; default seed builds record metadata only.",
    },
    {
        "source_id": "china_pku_dfiic",
        "source_name": "Peking University Digital Financial Inclusion Index of China",
        "access_class": "download_ingest_only",
        "auth_env_var": "",
        "official_url": "https://www.idf.pku.edu.cn/zsbz/index.htm",
        "reason": "Index data are free to request from the project team, but not exposed as a no-secret bulk API.",
    },
    {
        "source_id": "china_mohurd_construction_yearbook",
        "source_name": "China Urban-Rural Construction Statistical Yearbook",
        "access_class": "download_ingest_only",
        "auth_env_var": "",
        "official_url": "https://www.mohurd.gov.cn/gongkai/fdzdgknr/sjfb/tjxx/jstjnj/index.html",
        "reason": "Official publication/index route for municipal construction variables; no stable open REST API.",
    },
    {
        "source_id": "china_mnr_webmap_1m_boundaries",
        "source_name": "China 1:1,000,000 public basic geographic data",
        "access_class": "download_ingest_only",
        "auth_env_var": "",
        "official_url": "https://www.webmap.cn/commres.do?method=result100W",
        "reason": "Useful for boundary/geographic joins; download workflow may require site login or order steps.",
    },
    {
        "source_id": "china_land_market_network",
        "source_name": "China Land Market Network",
        "access_class": "download_ingest_only",
        "auth_env_var": "",
        "official_url": "https://www.landchina.com/",
        "reason": "Official public portal for land conveyance records, but normal access is web/search, not a stable API.",
    },
    {
        "source_id": "eog_viirs_nighttime_lights",
        "source_name": "EOG VIIRS annual nighttime lights",
        "access_class": "download_ingest_only",
        "auth_env_var": "",
        "official_url": "https://eogdata.mines.edu/products/vnl/",
        "reason": "Gridded annual GeoTIFF products can support city-year covariates after boundary zonal statistics.",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Generated output directory. Default: tmp/public-data-sources",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Redownload raw files even if the local copy already exists.",
    )
    parser.add_argument(
        "--include-qog-standard",
        action="store_true",
        help="Also download and import the larger QoG Standard TS/CS CSV files.",
    )
    parser.add_argument(
        "--include-gdelt",
        action="store_true",
        help="Also fetch GDELT DOC/raw event samples. Default is skipped.",
    )
    parser.add_argument(
        "--include-large-china-city-archives",
        action="store_true",
        help="Download and stage large China city-year archives such as the XMU city statistical yearbook panel.",
    )
    parser.add_argument(
        "--parse-vdem",
        action="store_true",
        help="Use Rscript to extract V-Dem .rda data frames to CSV and import them.",
    )
    parser.add_argument(
        "--worldbank-start-year",
        default="1960",
        help="Start year for the small World Bank indicator panel.",
    )
    parser.add_argument(
        "--worldbank-end-year",
        default=str(dt.date.today().year),
        help="End year for the small World Bank indicator panel.",
    )
    return parser.parse_args()


def now_iso() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def ensure_dirs(out_dir: Path) -> tuple[Path, Path]:
    raw_dir = out_dir / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    return out_dir, raw_dir


def connect(db_path: Path) -> sqlite3.Connection:
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute(
        """
        CREATE TABLE ingest_runs (
            source_id TEXT NOT NULL,
            access_class TEXT NOT NULL,
            status TEXT NOT NULL,
            rows INTEGER,
            bytes INTEGER,
            sha256 TEXT,
            fetched_at TEXT NOT NULL,
            source_url TEXT,
            local_path TEXT,
            notes TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE source_queue (
            source_id TEXT PRIMARY KEY,
            source_name TEXT NOT NULL,
            access_class TEXT NOT NULL,
            auth_env_var TEXT,
            official_url TEXT,
            reason TEXT NOT NULL,
            env_present INTEGER NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE seed_store_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    conn.executemany(
        "INSERT INTO seed_store_metadata (key, value) VALUES (?, ?)",
        [
            ("created_at", FETCHED_AT),
            ("builder", "skills/public-data-sources/scripts/build_seed_store.py"),
        ],
    )
    return conn


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def sanitize_identifier(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z_]+", "_", (value or "").strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_").lower()
    if not cleaned:
        cleaned = fallback
    if cleaned[0].isdigit():
        cleaned = f"col_{cleaned}"
    return cleaned


def unique_columns(raw_names: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    columns: list[str] = []
    for index, raw_name in enumerate(raw_names, start=1):
        base = sanitize_identifier(raw_name, f"col_{index}")
        count = seen.get(base, 0)
        seen[base] = count + 1
        columns.append(base if count == 0 else f"{base}_{count + 1}")
    return columns


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_request(url: str, timeout: int = 60) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
        },
    )


def fetch_bytes(url: str, timeout: int = 60, retries: int = 2) -> bytes:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(make_request(url, timeout), timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code in {429, 500, 502, 503, 504} and attempt < retries:
                time.sleep(2 ** attempt)
                continue
            raise
        except urllib.error.URLError as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            raise
        except http.client.RemoteDisconnected as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError(f"failed to fetch {url}: {last_error}")


def fetch_json(url: str, timeout: int = 60) -> Any:
    payload = fetch_bytes(url, timeout=timeout)
    return json.loads(payload.decode("utf-8"))


def fetch_head_metadata(url: str, timeout: int = 60) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        method="HEAD",
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        length = response.headers.get("Content-Length")
        return {
            "status": getattr(response, "status", None),
            "content_length": int(length) if length and length.isdigit() else None,
            "content_type": response.headers.get("Content-Type"),
            "last_modified": response.headers.get("Last-Modified"),
            "etag": response.headers.get("ETag"),
        }


def download_file(
    url: str,
    path: Path,
    refresh: bool,
    timeout: int = 180,
    retries: int = 2,
) -> tuple[str, int, str]:
    if path.exists() and not refresh:
        return "cached", path.stat().st_size, sha256_file(path)

    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(make_request(url, timeout), timeout=timeout) as response:
                with tmp_path.open("wb") as handle:
                    shutil.copyfileobj(response, handle, length=1024 * 1024)
            tmp_path.replace(path)
            return "downloaded", path.stat().st_size, sha256_file(path)
        except (urllib.error.HTTPError, urllib.error.URLError, http.client.RemoteDisconnected) as exc:
            last_error = exc
            if tmp_path.exists():
                tmp_path.unlink()
            if isinstance(exc, urllib.error.HTTPError) and exc.code not in {429, 500, 502, 503, 504}:
                raise
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            raise
        finally:
            if tmp_path.exists() and attempt == retries:
                tmp_path.unlink()
    raise RuntimeError(f"failed to download {url}: {last_error}")


def record_run(
    conn: sqlite3.Connection,
    source_id: str,
    access_class: str,
    status: str,
    rows: int | None = None,
    bytes_count: int | None = None,
    sha256: str | None = None,
    source_url: str | None = None,
    local_path: Path | None = None,
    notes: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO ingest_runs
        (source_id, access_class, status, rows, bytes, sha256, fetched_at, source_url, local_path, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source_id,
            access_class,
            status,
            rows,
            bytes_count,
            sha256,
            now_iso(),
            source_url,
            str(local_path) if local_path else None,
            notes,
        ),
    )
    conn.commit()


def replace_rows(
    conn: sqlite3.Connection,
    table: str,
    columns: list[str],
    rows: list[dict[str, Any]],
) -> int:
    conn.execute(f"DROP TABLE IF EXISTS {quote_ident(table)}")
    column_sql = ", ".join(f"{quote_ident(column)} TEXT" for column in columns)
    conn.execute(f"CREATE TABLE {quote_ident(table)} ({column_sql})")
    if not rows:
        conn.commit()
        return 0
    placeholders = ", ".join("?" for _ in columns)
    column_names = ", ".join(quote_ident(column) for column in columns)
    values = [[stringify(row.get(column)) for column in columns] for row in rows]
    conn.executemany(
        f"INSERT INTO {quote_ident(table)} ({column_names}) VALUES ({placeholders})",
        values,
    )
    conn.commit()
    return len(rows)


def stringify(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def flatten_row(row: dict[str, Any]) -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for key, value in row.items():
        clean_key = sanitize_identifier(str(key), "field")
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                flattened[f"{clean_key}_{sanitize_identifier(str(sub_key), 'field')}"] = sub_value
        else:
            flattened[clean_key] = value
    return flattened


def replace_json_table(conn: sqlite3.Connection, table: str, rows: list[dict[str, Any]]) -> int:
    flattened = [flatten_row(row) for row in rows]
    keys = sorted({key for row in flattened for key in row})
    return replace_rows(conn, table, keys or ["empty"], flattened)


def import_csv(conn: sqlite3.Connection, table: str, path: Path) -> int:
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            return import_csv_with_encoding(conn, table, path, encoding)
        except UnicodeDecodeError:
            conn.rollback()
            if encoding == "latin-1":
                raise
    raise RuntimeError(f"failed to import {path}")


def import_csv_with_encoding(conn: sqlite3.Connection, table: str, path: Path, encoding: str) -> int:
    csv.field_size_limit(sys.maxsize)
    with path.open("r", encoding=encoding, newline="") as handle:
        reader = csv.reader(handle)
        try:
            raw_header = next(reader)
        except StopIteration:
            return replace_rows(conn, table, ["empty"], [])
        columns = unique_columns(raw_header)
        conn.execute(f"DROP TABLE IF EXISTS {quote_ident(table)}")
        column_sql = ", ".join(f"{quote_ident(column)} TEXT" for column in columns)
        conn.execute(f"CREATE TABLE {quote_ident(table)} ({column_sql})")
        placeholders = ", ".join("?" for _ in columns)
        column_names = ", ".join(quote_ident(column) for column in columns)
        insert_sql = f"INSERT INTO {quote_ident(table)} ({column_names}) VALUES ({placeholders})"
        count = 0
        batch: list[list[str | None]] = []
        for row in reader:
            if len(row) < len(columns):
                row.extend([None] * (len(columns) - len(row)))
            elif len(row) > len(columns):
                row = row[: len(columns)]
            batch.append(row)
            count += 1
            if len(batch) >= 1000:
                conn.executemany(insert_sql, batch)
                batch.clear()
        if batch:
            conn.executemany(insert_sql, batch)
        conn.commit()
        return count


def csv_shape(path: Path) -> tuple[int, int, list[str]]:
    csv.field_size_limit(sys.maxsize)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            return 0, 0, []
        rows = sum(1 for _ in reader)
        return rows, len(header), header


def import_csv_selected(
    conn: sqlite3.Connection,
    table: str,
    path: Path,
    preferred_columns: list[str],
) -> tuple[int, list[str]]:
    csv.field_size_limit(sys.maxsize)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            replace_rows(conn, table, ["empty"], [])
            return 0, []
        selected = [column for column in preferred_columns if column in reader.fieldnames]
        if not selected:
            selected = reader.fieldnames[: min(200, len(reader.fieldnames))]
        sanitized = unique_columns(selected)
        conn.execute(f"DROP TABLE IF EXISTS {quote_ident(table)}")
        column_sql = ", ".join(f"{quote_ident(column)} TEXT" for column in sanitized)
        conn.execute(f"CREATE TABLE {quote_ident(table)} ({column_sql})")
        placeholders = ", ".join("?" for _ in sanitized)
        column_names = ", ".join(quote_ident(column) for column in sanitized)
        insert_sql = f"INSERT INTO {quote_ident(table)} ({column_names}) VALUES ({placeholders})"
        count = 0
        batch: list[list[str | None]] = []
        for row in reader:
            batch.append([row.get(column) for column in selected])
            count += 1
            if len(batch) >= 1000:
                conn.executemany(insert_sql, batch)
                batch.clear()
        if batch:
            conn.executemany(insert_sql, batch)
        conn.commit()
        return count, selected


def import_excel_sheet(conn: sqlite3.Connection, table: str, path: Path, sheet_name: str) -> int:
    try:
        import pandas as pd  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("pandas and openpyxl are required to import Excel seed files") from exc

    frame = pd.read_excel(path, sheet_name=sheet_name)
    frame = frame.dropna(how="all")
    raw_columns = [
        "" if pd.isna(column) else str(column).strip()
        for column in frame.columns.tolist()
    ]
    columns = unique_columns(raw_columns)
    rows: list[dict[str, Any]] = []
    for values in frame.itertuples(index=False, name=None):
        output: dict[str, Any] = {}
        for column, value in zip(columns, values, strict=True):
            output[column] = None if pd.isna(value) else value
        rows.append(output)
    return replace_rows(conn, table, columns, rows)


def import_undp_hdr_timeseries_long(conn: sqlite3.Connection, table: str, path: Path) -> int:
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            return import_undp_hdr_timeseries_long_with_encoding(conn, table, path, encoding)
        except UnicodeDecodeError:
            conn.rollback()
            if encoding == "latin-1":
                raise
    raise RuntimeError(f"failed to import {path}")


def import_undp_hdr_timeseries_long_with_encoding(
    conn: sqlite3.Connection,
    table: str,
    path: Path,
    encoding: str,
) -> int:
    csv.field_size_limit(sys.maxsize)
    with path.open("r", encoding=encoding, newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return replace_rows(conn, table, ["empty"], [])
        id_columns = [column for column in ["iso3", "country", "hdicode", "region", "hdi_rank_2023"] if column in reader.fieldnames]
        metric_fields: list[tuple[str, int, str]] = []
        metric_names: set[str] = set()
        for field in reader.fieldnames:
            match = re.match(r"^(.+)_(\d{4})$", field)
            if not match:
                continue
            metric = sanitize_identifier(match.group(1), "metric")
            year = int(match.group(2))
            metric_fields.append((field, year, metric))
            metric_names.add(metric)
        by_year: dict[int, list[tuple[str, str]]] = {}
        for field, year, metric in metric_fields:
            by_year.setdefault(year, []).append((field, metric))
        metric_columns = sorted(metric_names)
        columns = id_columns + ["year"] + metric_columns
        rows: list[dict[str, Any]] = []
        for source_row in reader:
            base = {column: source_row.get(column) for column in id_columns}
            for year in sorted(by_year):
                output: dict[str, Any] = dict(base)
                output["year"] = str(year)
                has_value = False
                for field, metric in by_year[year]:
                    value = (source_row.get(field) or "").strip()
                    output[metric] = value or None
                    has_value = has_value or bool(value)
                if has_value:
                    rows.append(output)
    return replace_rows(conn, table, columns, rows)


def extract_cow_nmc6_csv_members(
    archive_path: Path,
    extract_dir: Path,
    refresh: bool,
) -> tuple[list[dict[str, Any]], list[tuple[str, Path]]]:
    extract_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    csv_members: list[tuple[str, Path]] = []

    with zipfile.ZipFile(archive_path) as outer:
        for outer_info in outer.infolist():
            manifest.append(
                {
                    "archive": archive_path.name,
                    "member_path": outer_info.filename,
                    "member_type": "file",
                    "bytes": outer_info.file_size,
                }
            )
            if outer_info.filename.lower().endswith(".zip"):
                nested_path = extract_dir / Path(outer_info.filename).name
                if refresh or not nested_path.exists():
                    nested_path.write_bytes(outer.read(outer_info.filename))
                with zipfile.ZipFile(nested_path) as nested:
                    for nested_info in nested.infolist():
                        nested_member = f"{outer_info.filename}/{nested_info.filename}"
                        manifest.append(
                            {
                                "archive": nested_path.name,
                                "member_path": nested_member,
                                "member_type": "file",
                                "bytes": nested_info.file_size,
                            }
                        )
                        if nested_info.filename.lower().endswith(".csv"):
                            target = extract_dir / Path(nested_info.filename).name
                            if refresh or not target.exists():
                                target.write_bytes(nested.read(nested_info.filename))
                            csv_members.append((nested_member, target))
            elif outer_info.filename.lower().endswith(".csv"):
                target = extract_dir / Path(outer_info.filename).name
                if refresh or not target.exists():
                    target.write_bytes(outer.read(outer_info.filename))
                csv_members.append((outer_info.filename, target))
    return manifest, csv_members


def cow_nmc_table_name(member_name: str) -> str:
    stem = sanitize_identifier(Path(member_name).stem, "cow_nmc6")
    if "abridged" in stem:
        return "cow_nmc6_abridged"
    if "wsupplementary" in stem or "supplementary" in stem:
        return "cow_nmc6_with_supplementary"
    return f"cow_nmc6_{stem}"


def table_year_stats(
    conn: sqlite3.Connection,
    table: str,
    year_column: str,
    unit_column: str,
) -> dict[str, Any]:
    columns = {
        row[1]
        for row in conn.execute(f"PRAGMA table_info({quote_ident(table)})").fetchall()
    }
    if year_column not in columns or unit_column not in columns:
        return {"rows": None, "min_year": None, "max_year": None, "units": None}
    row = conn.execute(
        f"""
        SELECT
            COUNT(*),
            MIN(CAST({quote_ident(year_column)} AS INTEGER)),
            MAX(CAST({quote_ident(year_column)} AS INTEGER)),
            COUNT(DISTINCT {quote_ident(unit_column)})
        FROM {quote_ident(table)}
        WHERE {quote_ident(year_column)} IS NOT NULL
          AND TRIM({quote_ident(year_column)}) != ''
        """
    ).fetchone()
    return {
        "rows": row[0],
        "min_year": row[1],
        "max_year": row[2],
        "units": row[3],
    }


def write_country_year_panel_catalog(conn: sqlite3.Connection) -> None:
    specs = [
        {
            "source_id": "pwt_11_0",
            "source_name": "Penn World Table 11.0",
            "table_name": "pwt_11_0",
            "unit": "country-year",
            "unit_code_column": "countrycode",
            "year_column": "year",
            "official_coverage_note": "185 countries between 1950 and 2023.",
            "source_url": PWT_11_0_EXCEL_URL,
        },
        {
            "source_id": "maddison_project_2023",
            "source_name": "Maddison Project Database 2023",
            "table_name": "maddison_project_2023_full_data",
            "unit": "country-year",
            "unit_code_column": "countrycode",
            "year_column": "year",
            "official_coverage_note": "169 countries and period up to 2022; includes long-run historical observations.",
            "source_url": MADDISON_2023_EXCEL_URL,
        },
        {
            "source_id": "undp_hdr_composite_indices_timeseries",
            "source_name": "UNDP HDR composite indices time series",
            "table_name": "undp_hdr_composite_indices_timeseries_long",
            "unit": "country-year",
            "unit_code_column": "iso3",
            "year_column": "year",
            "official_coverage_note": "Composite indices and components time series for 1990-2023.",
            "source_url": UNDP_HDR_COMPOSITE_TIME_SERIES_CSV_URL,
        },
        {
            "source_id": "cow_nmc6_abridged",
            "source_name": "Correlates of War National Material Capabilities 6.0 abridged",
            "table_name": "cow_nmc6_abridged",
            "unit": "state-year",
            "unit_code_column": "ccode",
            "year_column": "year",
            "official_coverage_note": "State system annual values, currently 1816-2016 on the official source page.",
            "source_url": COW_NMC_6_ZIP_URL,
        },
        {
            "source_id": "cow_nmc6_with_supplementary",
            "source_name": "Correlates of War National Material Capabilities 6.0 with supplementary states",
            "table_name": "cow_nmc6_with_supplementary",
            "unit": "state-year",
            "unit_code_column": "ccode",
            "year_column": "year",
            "official_coverage_note": "Supplementary COW NMC release member; verify state-system inclusion before merging.",
            "source_url": COW_NMC_6_ZIP_URL,
        },
    ]
    rows = []
    for spec in specs:
        stats = table_year_stats(conn, spec["table_name"], spec["year_column"], spec["unit_code_column"])
        rows.append(spec | stats)
    replace_json_table(conn, "country_year_panel_catalog", rows)


def insert_source_queue(conn: sqlite3.Connection) -> None:
    rows = [
        (
            source["source_id"],
            source["source_name"],
            source["access_class"],
            source["auth_env_var"],
            source["official_url"],
            source["reason"],
            1 if source["auth_env_var"] and os.environ.get(source["auth_env_var"]) else 0,
        )
        for source in BLOCKED_OR_CONFIGURED_SOURCES
    ]
    conn.executemany(
        """
        INSERT INTO source_queue
        (source_id, source_name, access_class, auth_env_var, official_url, reason, env_present)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()


def worldbank_url(path: str, params: dict[str, str]) -> str:
    query = urllib.parse.urlencode(params)
    return f"https://api.worldbank.org/v2/{path}?{query}"


def fetch_worldbank_pages(path: str, params: dict[str, str]) -> tuple[str, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    first_url = worldbank_url(path, params | {"page": "1"})
    first_payload = fetch_json(first_url)
    if not isinstance(first_payload, list) or len(first_payload) < 2:
        return first_url, rows
    metadata = first_payload[0]
    rows.extend(first_payload[1] or [])
    pages = int(metadata.get("pages") or 1)
    for page in range(2, pages + 1):
        time.sleep(0.15)
        url = worldbank_url(path, params | {"page": str(page)})
        payload = fetch_json(url)
        if isinstance(payload, list) and len(payload) >= 2 and payload[1]:
            rows.extend(payload[1])
    return first_url, rows


def ingest_worldbank(conn: sqlite3.Connection, raw_dir: Path, args: argparse.Namespace) -> None:
    try:
        countries_url, countries = fetch_worldbank_pages(
            "country",
            {"format": "json", "per_page": "400"},
        )
        country_rows = [flatten_row(row) for row in countries]
        replace_json_table(conn, "worldbank_countries", country_rows)
        record_run(
            conn,
            "worldbank_countries",
            "public_no_secret",
            "ingested",
            rows=len(country_rows),
            source_url=countries_url,
        )

        indicators_url, indicators = fetch_worldbank_pages(
            "indicator",
            {"format": "json", "per_page": "20000"},
        )
        indicator_rows = [flatten_row(row) for row in indicators]
        replace_json_table(conn, "worldbank_indicators", indicator_rows)
        record_run(
            conn,
            "worldbank_indicators",
            "public_no_secret",
            "ingested",
            rows=len(indicator_rows),
            source_url=indicators_url,
        )

        values: list[dict[str, Any]] = []
        for indicator in WORLD_BANK_INDICATORS:
            url, indicator_values = fetch_worldbank_pages(
                f"country/all/indicator/{indicator}",
                {
                    "format": "json",
                    "per_page": "20000",
                    "date": f"{args.worldbank_start_year}:{args.worldbank_end_year}",
                },
            )
            for row in indicator_values:
                values.append(
                    {
                        "indicator_id": indicator,
                        "country_id": (row.get("country") or {}).get("id"),
                        "country": (row.get("country") or {}).get("value"),
                        "countryiso3code": row.get("countryiso3code"),
                        "date": row.get("date"),
                        "value": row.get("value"),
                        "unit": row.get("unit"),
                        "obs_status": row.get("obs_status"),
                        "decimal": row.get("decimal"),
                    }
                )
            record_run(
                conn,
                f"worldbank_values_{indicator}",
                "public_no_secret",
                "ingested",
                rows=len(indicator_values),
                source_url=url,
            )
            time.sleep(0.15)
        replace_json_table(conn, "worldbank_indicator_values", values)
    except Exception as exc:  # noqa: BLE001
        record_run(
            conn,
            "worldbank",
            "public_no_secret",
            "failed",
            notes=repr(exc),
        )


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def element_name(element: ET.Element) -> str:
    names = [child.text for child in element if local_name(child.tag) == "Name" and child.text]
    return names[0] if names else ""


def parse_dataflows(xml_payload: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(xml_payload)
    rows: list[dict[str, str]] = []
    for element in root.iter():
        if local_name(element.tag) != "Dataflow":
            continue
        rows.append(
            {
                "id": element.attrib.get("id") or element.attrib.get("ID") or "",
                "agency_id": element.attrib.get("agencyID") or element.attrib.get("agencyId") or "",
                "version": element.attrib.get("version") or "",
                "name": element_name(element),
            }
        )
    return rows


def ingest_dataflow_catalog(
    conn: sqlite3.Connection,
    raw_dir: Path,
    source_id: str,
    table: str,
    url: str,
    refresh: bool,
    timeout: int = 240,
) -> None:
    local_path = raw_dir / f"{source_id}_dataflows.xml"
    try:
        status, bytes_count, digest = download_file(url, local_path, refresh=refresh, timeout=timeout)
        rows = parse_dataflows(local_path.read_bytes())
        replace_json_table(conn, table, rows)
        record_run(
            conn,
            source_id,
            "public_no_secret",
            status,
            rows=len(rows),
            bytes_count=bytes_count,
            sha256=digest,
            source_url=url,
            local_path=local_path,
        )
    except Exception as exc:  # noqa: BLE001
        record_run(
            conn,
            source_id,
            "public_no_secret",
            "failed",
            source_url=url,
            local_path=local_path,
            notes=repr(exc),
        )


def ingest_sdg(conn: sqlite3.Connection) -> None:
    endpoints = [
        ("un_sdg_goals", "https://unstats.un.org/SDGAPI/v1/sdg/Goal/List?includechildren=false"),
        ("un_sdg_targets", "https://unstats.un.org/SDGAPI/v1/sdg/Target/List?includechildren=false"),
        ("un_sdg_indicators", "https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List?includechildren=false"),
        ("un_sdg_series", "https://unstats.un.org/SDGAPI/v1/sdg/Series/List"),
    ]
    for table, url in endpoints:
        try:
            payload = fetch_json(url, timeout=120)
            rows = payload if isinstance(payload, list) else payload.get("data", [])
            if not isinstance(rows, list):
                rows = [payload]
            replace_json_table(conn, table, rows)
            record_run(
                conn,
                table,
                "public_no_secret",
                "ingested",
                rows=len(rows),
                source_url=url,
            )
        except Exception as exc:  # noqa: BLE001
            record_run(
                conn,
                table,
                "public_no_secret",
                "failed",
                source_url=url,
                notes=repr(exc),
            )


def ingest_crossref(conn: sqlite3.Connection) -> None:
    url = (
        "https://api.crossref.org/works?"
        + urllib.parse.urlencode(
            {
                "query": "political economy",
                "rows": "20",
                "mailto": "ai4ss@example.edu",
            }
        )
    )
    try:
        payload = fetch_json(url)
        items = payload.get("message", {}).get("items", [])
        rows = []
        for item in items:
            rows.append(
                {
                    "doi": item.get("DOI"),
                    "type": item.get("type"),
                    "title": first(item.get("title")),
                    "container_title": first(item.get("container-title")),
                    "publisher": item.get("publisher"),
                    "published": json.dumps(item.get("published-print") or item.get("published-online") or item.get("issued")),
                    "is_referenced_by_count": item.get("is-referenced-by-count"),
                    "url": item.get("URL"),
                }
            )
        replace_json_table(conn, "crossref_political_economy_sample", rows)
        record_run(conn, "crossref_sample", "public_no_secret", "ingested", rows=len(rows), source_url=url)
    except Exception as exc:  # noqa: BLE001
        record_run(conn, "crossref_sample", "public_no_secret", "failed", source_url=url, notes=repr(exc))


def ingest_datacite(conn: sqlite3.Connection) -> None:
    url = "https://api.datacite.org/dois?" + urllib.parse.urlencode(
        {"query": "social science", "page[size]": "20"}
    )
    try:
        payload = fetch_json(url)
        items = payload.get("data", [])
        rows = []
        for item in items:
            attributes = item.get("attributes", {})
            rows.append(
                {
                    "doi": attributes.get("doi"),
                    "type": attributes.get("types", {}).get("resourceTypeGeneral"),
                    "title": first((attributes.get("titles") or [{}])[0].get("title")),
                    "publisher": attributes.get("publisher"),
                    "publication_year": attributes.get("publicationYear"),
                    "url": attributes.get("url"),
                    "provider_id": item.get("id"),
                }
            )
        replace_json_table(conn, "datacite_social_science_sample", rows)
        record_run(conn, "datacite_sample", "public_no_secret", "ingested", rows=len(rows), source_url=url)
    except Exception as exc:  # noqa: BLE001
        record_run(conn, "datacite_sample", "public_no_secret", "failed", source_url=url, notes=repr(exc))


def fetch_unhcr_pages(url: str, page_limit: int = 25, sleep_seconds: float = 0.05) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    page = 1
    max_pages = 1
    while page <= max_pages and page <= page_limit:
        separator = "&" if "?" in url else "?"
        payload = fetch_json(f"{url}{separator}page={page}", timeout=60)
        if not isinstance(payload, dict):
            break
        items = payload.get("items", [])
        if isinstance(items, list):
            rows.extend(item for item in items if isinstance(item, dict))
        max_pages = int(payload.get("maxPages") or page)
        page += 1
        if page <= max_pages:
            time.sleep(sleep_seconds)
    return rows


def ingest_who_gho(conn: sqlite3.Connection) -> None:
    url = "https://ghoapi.azureedge.net/api/Indicator?$top=1000"
    try:
        payload = fetch_json(url, timeout=120)
        rows = payload.get("value", []) if isinstance(payload, dict) else []
        replace_json_table(conn, "who_gho_indicators", rows)
        record_run(conn, "who_gho_indicators", "public_no_secret", "ingested", rows=len(rows), source_url=url)
    except Exception as exc:  # noqa: BLE001
        record_run(conn, "who_gho_indicators", "public_no_secret", "failed", source_url=url, notes=repr(exc))


def ingest_unhcr_metadata(conn: sqlite3.Connection) -> None:
    endpoints = [
        (
            "unhcr_countries",
            "https://api.unhcr.org/population/v1/countries/?limit=500",
            5,
        ),
        (
            "unhcr_years",
            "https://api.unhcr.org/population/v1/years/?limit=500",
            2,
        ),
        (
            "unhcr_population_2023_sample",
            "https://api.unhcr.org/population/v1/population/?limit=100&yearFrom=2023&yearTo=2023",
            2,
        ),
        (
            "unhcr_asylum_2023_sample",
            "https://api.unhcr.org/population/v1/asylum-applications/?limit=100&yearFrom=2023&yearTo=2023",
            2,
        ),
    ]
    for table, url, page_limit in endpoints:
        try:
            rows = fetch_unhcr_pages(url, page_limit=page_limit)
            replace_json_table(conn, table, rows)
            record_run(conn, table, "public_no_secret", "ingested", rows=len(rows), source_url=url)
        except Exception as exc:  # noqa: BLE001
            record_run(conn, table, "public_no_secret", "failed", source_url=url, notes=repr(exc))


def ingest_owid_grapher(conn: sqlite3.Connection, raw_dir: Path, refresh: bool) -> None:
    csv_url = "https://ourworldindata.org/grapher/life-expectancy.csv"
    metadata_url = "https://ourworldindata.org/grapher/life-expectancy.metadata.json"
    csv_path = raw_dir / "owid_life_expectancy.csv"
    try:
        status, bytes_count, digest = download_file(csv_url, csv_path, refresh=refresh, timeout=120)
        rows = import_csv(conn, "owid_life_expectancy", csv_path)
        record_run(
            conn,
            "owid_life_expectancy",
            "public_no_secret",
            status,
            rows=rows,
            bytes_count=bytes_count,
            sha256=digest,
            source_url=csv_url,
            local_path=csv_path,
            notes="Small Grapher chart CSV imported as a routing and schema example.",
        )
    except Exception as exc:  # noqa: BLE001
        record_run(conn, "owid_life_expectancy", "public_no_secret", "failed", source_url=csv_url, local_path=csv_path, notes=repr(exc))
    try:
        payload = fetch_json(metadata_url, timeout=60)
        rows = [payload] if isinstance(payload, dict) else []
        replace_json_table(conn, "owid_life_expectancy_metadata", rows)
        record_run(conn, "owid_life_expectancy_metadata", "public_no_secret", "ingested", rows=len(rows), source_url=metadata_url)
    except Exception as exc:  # noqa: BLE001
        record_run(conn, "owid_life_expectancy_metadata", "public_no_secret", "failed", source_url=metadata_url, notes=repr(exc))


def ingest_nasa_power_sample(conn: sqlite3.Connection) -> None:
    url = (
        "https://power.larc.nasa.gov/api/temporal/monthly/point?"
        + urllib.parse.urlencode(
            {
                "parameters": "T2M,PRECTOTCORR",
                "community": "AG",
                "longitude": "121.4737",
                "latitude": "31.2304",
                "start": "2020",
                "end": "2021",
                "format": "JSON",
            }
        )
    )
    try:
        payload = fetch_json(url, timeout=60)
        parameters = payload.get("properties", {}).get("parameter", {}) if isinstance(payload, dict) else {}
        periods = sorted({period for series in parameters.values() for period in series})
        rows = []
        for period in periods:
            row: dict[str, Any] = {"period": period}
            for parameter, series in parameters.items():
                row[sanitize_identifier(parameter, "parameter")] = series.get(period)
            rows.append(row)
        replace_json_table(conn, "nasa_power_shanghai_monthly_sample", rows)
        record_run(conn, "nasa_power_shanghai_monthly_sample", "public_no_secret", "ingested", rows=len(rows), source_url=url)
    except Exception as exc:  # noqa: BLE001
        record_run(conn, "nasa_power_shanghai_monthly_sample", "public_no_secret", "failed", source_url=url, notes=repr(exc))


def ingest_federal_register_sample(conn: sqlite3.Connection) -> None:
    url = "https://www.federalregister.gov/api/v1/documents.json?" + urllib.parse.urlencode(
        {"per_page": "20", "conditions[term]": "climate"}
    )
    try:
        payload = fetch_json(url, timeout=60)
        rows = []
        for item in payload.get("results", []) if isinstance(payload, dict) else []:
            rows.append(
                {
                    "title": item.get("title"),
                    "type": item.get("type"),
                    "document_number": item.get("document_number"),
                    "publication_date": item.get("publication_date"),
                    "agency_names": json.dumps([agency.get("name") for agency in item.get("agencies", [])], ensure_ascii=False),
                    "html_url": item.get("html_url"),
                    "pdf_url": item.get("pdf_url"),
                }
            )
        replace_json_table(conn, "federal_register_climate_sample", rows)
        record_run(conn, "federal_register_climate_sample", "public_no_secret", "ingested", rows=len(rows), source_url=url)
    except Exception as exc:  # noqa: BLE001
        record_run(conn, "federal_register_climate_sample", "public_no_secret", "failed", source_url=url, notes=repr(exc))


def ingest_harvard_dataverse_sample(conn: sqlite3.Connection) -> None:
    url = "https://dataverse.harvard.edu/api/search?" + urllib.parse.urlencode(
        {"q": "political economy", "type": "dataset", "per_page": "50"}
    )
    try:
        payload = fetch_json(url, timeout=60)
        rows = []
        for item in payload.get("data", {}).get("items", []) if isinstance(payload, dict) else []:
            rows.append(
                {
                    "name": item.get("name"),
                    "global_id": item.get("global_id"),
                    "published_at": item.get("published_at"),
                    "publisher": item.get("publisher"),
                    "citation_html": item.get("citationHtml"),
                    "url": item.get("url"),
                }
            )
        replace_json_table(conn, "harvard_dataverse_political_economy_sample", rows)
        record_run(conn, "harvard_dataverse_sample", "public_no_secret", "ingested", rows=len(rows), source_url=url)
    except Exception as exc:  # noqa: BLE001
        record_run(conn, "harvard_dataverse_sample", "public_no_secret", "failed", source_url=url, notes=repr(exc))


def ingest_voteview_members(conn: sqlite3.Connection, raw_dir: Path, refresh: bool) -> None:
    url = "https://voteview.com/static/data/out/members/HSall_members.csv"
    local_path = raw_dir / "voteview_HSall_members.csv"
    try:
        status, bytes_count, digest = download_file(url, local_path, refresh=refresh, timeout=180)
        rows = import_csv(conn, "voteview_hsall_members", local_path)
        record_run(
            conn,
            "voteview_hsall_members",
            "public_no_secret",
            status,
            rows=rows,
            bytes_count=bytes_count,
            sha256=digest,
            source_url=url,
            local_path=local_path,
        )
    except Exception as exc:  # noqa: BLE001
        record_run(conn, "voteview_hsall_members", "public_no_secret", "failed", source_url=url, local_path=local_path, notes=repr(exc))


def ingest_parlgov_core(conn: sqlite3.Connection, raw_dir: Path, refresh: bool) -> None:
    url = "https://parlgov.org/data/parlgov-development_csv-utf-8.zip"
    zip_path = raw_dir / "parlgov-development_csv-utf-8.zip"
    desired = {
        "view_party.csv": "parlgov_party",
        "view_election.csv": "parlgov_election",
        "view_election_result.csv": "parlgov_election_result",
        "view_cabinet.csv": "parlgov_cabinet",
        "info_data_source.csv": "parlgov_info_data_source",
    }
    try:
        status, bytes_count, digest = download_file(url, zip_path, refresh=refresh, timeout=180)
        imported = 0
        with zipfile.ZipFile(zip_path) as archive:
            for member in archive.namelist():
                filename = Path(member).name
                table = desired.get(filename)
                if not table:
                    continue
                csv_path = raw_dir / "parlgov" / filename
                csv_path.parent.mkdir(parents=True, exist_ok=True)
                if refresh or not csv_path.exists():
                    with archive.open(member) as source, csv_path.open("wb") as target:
                        shutil.copyfileobj(source, target)
                rows = import_csv(conn, table, csv_path)
                imported += 1
                record_run(
                    conn,
                    table,
                    "public_no_secret",
                    status,
                    rows=rows,
                    bytes_count=csv_path.stat().st_size,
                    sha256=sha256_file(csv_path),
                    source_url=url,
                    local_path=csv_path,
                    notes=f"Imported from {filename} inside ParlGov development CSV zip.",
                )
        record_run(
            conn,
            "parlgov_development_zip",
            "public_no_secret",
            status if imported else "failed",
            rows=imported,
            bytes_count=bytes_count,
            sha256=digest,
            source_url=url,
            local_path=zip_path,
            notes=f"Imported {imported} core CSV member(s).",
        )
    except Exception as exc:  # noqa: BLE001
        record_run(conn, "parlgov_development_zip", "public_no_secret", "failed", source_url=url, local_path=zip_path, notes=repr(exc))


def ingest_pwt_11_0(conn: sqlite3.Connection, raw_dir: Path, refresh: bool) -> None:
    local_path = raw_dir / "pwt_11_0.xlsx"
    try:
        status, bytes_count, digest = download_file(PWT_11_0_EXCEL_URL, local_path, refresh=refresh, timeout=300)
        try:
            rows = import_excel_sheet(conn, "pwt_11_0", local_path, "Data")
        except zipfile.BadZipFile:
            if refresh:
                raise
            local_path.unlink(missing_ok=True)
            status, bytes_count, digest = download_file(PWT_11_0_EXCEL_URL, local_path, refresh=True, timeout=300)
            status = f"{status}_after_invalid_cache"
            rows = import_excel_sheet(conn, "pwt_11_0", local_path, "Data")
        record_run(
            conn,
            "pwt_11_0",
            "download_ingest_only",
            status,
            rows=rows,
            bytes_count=bytes_count,
            sha256=digest,
            source_url=PWT_11_0_EXCEL_URL,
            local_path=local_path,
            notes="Imported official PWT 11.0 Excel Data sheet.",
        )
    except Exception as exc:  # noqa: BLE001
        record_run(
            conn,
            "pwt_11_0",
            "download_ingest_only",
            "failed",
            source_url=PWT_11_0_EXCEL_URL,
            local_path=local_path,
            notes=repr(exc),
        )


def ingest_maddison_project_2023(conn: sqlite3.Connection, raw_dir: Path, refresh: bool) -> None:
    local_path = raw_dir / "maddison_project_database_2023.xlsx"
    try:
        status, bytes_count, digest = download_file(MADDISON_2023_EXCEL_URL, local_path, refresh=refresh, timeout=300)
        try:
            rows = import_excel_sheet(conn, "maddison_project_2023_full_data", local_path, "Full data")
        except zipfile.BadZipFile:
            if refresh:
                raise
            local_path.unlink(missing_ok=True)
            status, bytes_count, digest = download_file(MADDISON_2023_EXCEL_URL, local_path, refresh=True, timeout=300)
            status = f"{status}_after_invalid_cache"
            rows = import_excel_sheet(conn, "maddison_project_2023_full_data", local_path, "Full data")
        record_run(
            conn,
            "maddison_project_2023_full_data",
            "download_ingest_only",
            status,
            rows=rows,
            bytes_count=bytes_count,
            sha256=digest,
            source_url=MADDISON_2023_EXCEL_URL,
            local_path=local_path,
            notes="Imported official Maddison Project Database 2023 Excel Full data sheet.",
        )
    except Exception as exc:  # noqa: BLE001
        record_run(
            conn,
            "maddison_project_2023_full_data",
            "download_ingest_only",
            "failed",
            source_url=MADDISON_2023_EXCEL_URL,
            local_path=local_path,
            notes=repr(exc),
        )


def ingest_undp_hdr_composite_timeseries(conn: sqlite3.Connection, raw_dir: Path, refresh: bool) -> None:
    local_path = raw_dir / "HDR25_Composite_indices_complete_time_series.csv"
    try:
        status, bytes_count, digest = download_file(
            UNDP_HDR_COMPOSITE_TIME_SERIES_CSV_URL,
            local_path,
            refresh=refresh,
            timeout=300,
        )
        wide_rows = import_csv(conn, "undp_hdr_composite_indices_timeseries_wide", local_path)
        record_run(
            conn,
            "undp_hdr_composite_indices_timeseries_wide",
            "download_ingest_only",
            status,
            rows=wide_rows,
            bytes_count=bytes_count,
            sha256=digest,
            source_url=UNDP_HDR_COMPOSITE_TIME_SERIES_CSV_URL,
            local_path=local_path,
            notes="Imported official HDR composite indices time-series CSV in source wide format.",
        )
        long_rows = import_undp_hdr_timeseries_long(conn, "undp_hdr_composite_indices_timeseries_long", local_path)
        record_run(
            conn,
            "undp_hdr_composite_indices_timeseries_long",
            "download_ingest_only",
            "ingested",
            rows=long_rows,
            bytes_count=bytes_count,
            sha256=digest,
            source_url=UNDP_HDR_COMPOSITE_TIME_SERIES_CSV_URL,
            local_path=local_path,
            notes="Normalized official HDR wide time-series columns to one country-year row per ISO3/year.",
        )
    except Exception as exc:  # noqa: BLE001
        record_run(
            conn,
            "undp_hdr_composite_indices_timeseries",
            "download_ingest_only",
            "failed",
            source_url=UNDP_HDR_COMPOSITE_TIME_SERIES_CSV_URL,
            local_path=local_path,
            notes=repr(exc),
        )


def ingest_cow_nmc6(conn: sqlite3.Connection, raw_dir: Path, refresh: bool) -> None:
    archive_path = raw_dir / "NMC_Documentation-6.0.zip"
    extract_dir = raw_dir / "cow_nmc6"
    try:
        status, bytes_count, digest = download_file(COW_NMC_6_ZIP_URL, archive_path, refresh=refresh, timeout=300)
        manifest, csv_members = extract_cow_nmc6_csv_members(archive_path, extract_dir, refresh=refresh)
        replace_json_table(conn, "cow_nmc6_zip_manifest", manifest)
        imported = 0
        for member_name, csv_path in csv_members:
            table = cow_nmc_table_name(member_name)
            rows = import_csv(conn, table, csv_path)
            imported += 1
            record_run(
                conn,
                table,
                "download_ingest_only",
                "ingested",
                rows=rows,
                bytes_count=csv_path.stat().st_size,
                sha256=sha256_file(csv_path),
                source_url=COW_NMC_6_ZIP_URL,
                local_path=csv_path,
                notes=f"Imported CSV member {member_name} from official COW NMC 6.0 ZIP.",
            )
        record_run(
            conn,
            "cow_nmc6_archive",
            "download_ingest_only",
            status if imported else "failed",
            rows=len(manifest),
            bytes_count=bytes_count,
            sha256=digest,
            source_url=COW_NMC_6_ZIP_URL,
            local_path=archive_path,
            notes=f"Extracted {len(csv_members)} CSV member(s) from nested COW NMC 6.0 archive.",
        )
    except Exception as exc:  # noqa: BLE001
        record_run(
            conn,
            "cow_nmc6_archive",
            "download_ingest_only",
            "failed",
            source_url=COW_NMC_6_ZIP_URL,
            local_path=archive_path,
            notes=repr(exc),
        )


def ingest_global_country_year_panels(conn: sqlite3.Connection, raw_dir: Path, refresh: bool) -> None:
    ingest_pwt_11_0(conn, raw_dir, refresh=refresh)
    ingest_maddison_project_2023(conn, raw_dir, refresh=refresh)
    ingest_undp_hdr_composite_timeseries(conn, raw_dir, refresh=refresh)
    ingest_cow_nmc6(conn, raw_dir, refresh=refresh)


def strip_tags(value: str) -> str:
    value = re.sub(r"<\s*sub\s*>", "_", value, flags=re.I)
    value = re.sub(r"<\s*/\s*sub\s*>", "", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def parse_ceads_catalog_rows(page_html: str, catalog_type: str, source_url: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for match in re.finditer(r"<tr[^>]*id=\"(?P<id>\d+)\"[^>]*>(?P<body>.*?)</tr>", page_html, flags=re.S | re.I):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", match.group("body"), flags=re.S | re.I)
        text_cells = [strip_tags(cell) for cell in cells]
        if len(text_cells) < 10:
            continue
        rows.append(
            {
                "catalog_type": catalog_type,
                "record_id": match.group("id"),
                "name": text_cells[1],
                "year": text_cells[2],
                "spatial_resolution": text_cells[3],
                "temporal_resolution": text_cells[4],
                "element": text_cells[5],
                "energy_type": text_cells[6],
                "industry_type": text_cells[7],
                "search_tags": text_cells[8],
                "published": text_cells[9],
                "source_url": source_url,
            }
        )
    return rows


def ingest_china_areacodes(conn: sqlite3.Connection, raw_dir: Path, refresh: bool) -> None:
    local_path = raw_dir / "china_areacodes_result.csv"
    try:
        status, bytes_count, digest = download_file(CHINA_AREACODES_URL, local_path, refresh=refresh, timeout=120)
        rows = import_csv(conn, "china_areacodes_history", local_path)
        record_run(
            conn,
            "china_areacodes_history",
            "public_no_secret",
            status,
            rows=rows,
            bytes_count=bytes_count,
            sha256=digest,
            source_url=CHINA_AREACODES_URL,
            local_path=local_path,
            notes="Historical county-and-above administrative codes, useful as the city-year crosswalk spine.",
        )
    except Exception as exc:  # noqa: BLE001
        record_run(
            conn,
            "china_areacodes_history",
            "public_no_secret",
            "failed",
            source_url=CHINA_AREACODES_URL,
            local_path=local_path,
            notes=repr(exc),
        )


def ingest_china_ceads_catalogs(conn: sqlite3.Connection, raw_dir: Path, refresh: bool) -> None:
    all_rows: list[dict[str, Any]] = []
    for source_id, catalog_type, url in CHINA_CEADS_CITY_CATALOG_PAGES:
        local_path = raw_dir / f"{source_id}.html"
        try:
            status, bytes_count, digest = download_file(url, local_path, refresh=refresh, timeout=120)
            page_html = local_path.read_text(encoding="utf-8", errors="replace")
            rows = parse_ceads_catalog_rows(page_html, catalog_type, url)
            all_rows.extend(rows)
            record_run(
                conn,
                source_id,
                "public_no_secret",
                status,
                rows=len(rows),
                bytes_count=bytes_count,
                sha256=digest,
                source_url=url,
                local_path=local_path,
                notes="Parsed CEADs public city-level catalog rows; actual downloads may require CEADs account/session workflow.",
            )
        except Exception as exc:  # noqa: BLE001
            record_run(conn, source_id, "public_no_secret", "failed", source_url=url, local_path=local_path, notes=repr(exc))
    replace_json_table(conn, "china_ceads_city_catalog", all_rows)


def ingest_china_chap_pm25_manifest(conn: sqlite3.Connection) -> None:
    try:
        payload = fetch_json(CHINA_CHAP_PM25_ZENODO_API, timeout=120)
        files = payload.get("files", []) if isinstance(payload, dict) else []
        metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
        rows = []
        for file_info in files:
            if not isinstance(file_info, dict):
                continue
            links = file_info.get("links", {}) if isinstance(file_info.get("links"), dict) else {}
            rows.append(
                {
                    "record_id": payload.get("id"),
                    "concept_record_id": payload.get("conceptrecid"),
                    "doi": payload.get("doi"),
                    "title": payload.get("title") or metadata.get("title"),
                    "file_key": file_info.get("key"),
                    "size": file_info.get("size"),
                    "checksum": file_info.get("checksum"),
                    "download_url": links.get("self") or links.get("download"),
                    "created": payload.get("created"),
                    "modified": payload.get("modified"),
                }
            )
        replace_json_table(conn, "china_chap_pm25_zenodo_files", rows)
        record_run(
            conn,
            "china_chap_pm25_zenodo_files",
            "public_no_secret",
            "ingested",
            rows=len(rows),
            bytes_count=sum(int(row.get("size") or 0) for row in rows),
            source_url=CHINA_CHAP_PM25_ZENODO_API,
            notes="File manifest only; city-year PM2.5 requires separate gridded download plus boundary zonal statistics.",
        )
    except Exception as exc:  # noqa: BLE001
        record_run(
            conn,
            "china_chap_pm25_zenodo_files",
            "public_no_secret",
            "failed",
            source_url=CHINA_CHAP_PM25_ZENODO_API,
            notes=repr(exc),
        )


def ingest_china_nbs_city_backend_probe(conn: sqlite3.Connection) -> None:
    rows: list[dict[str, Any]] = []
    for probe_name, url in CHINA_NBS_CITY_BACKEND_PROBES:
        try:
            payload = fetch_bytes(url, timeout=30, retries=0)
            status = "reachable"
            note = payload[:200].decode("utf-8", errors="replace")
            http_status = "200"
        except urllib.error.HTTPError as exc:
            status = "blocked_or_not_open"
            note = repr(exc)
            http_status = str(exc.code)
        except Exception as exc:  # noqa: BLE001
            status = "failed"
            note = repr(exc)
            http_status = ""
        rows.append(
            {
                "probe_name": probe_name,
                "url": url,
                "status": status,
                "http_status": http_status,
                "note": note,
            }
        )
    replace_json_table(conn, "china_nbs_city_backend_probe", rows)
    record_run(
        conn,
        "china_nbs_city_backend_probe",
        "download_ingest_only",
        "probed",
        rows=len(rows),
        source_url="https://data.stats.gov.cn/",
        notes="Old/new National Data city backend probes are recorded as access evidence, not treated as stable API routes.",
    )


def extract_archive(archive_path: Path, extract_dir: Path) -> tuple[str, str, int]:
    extract_dir.mkdir(parents=True, exist_ok=True)
    if shutil.which("unar"):
        result = subprocess.run(
            ["unar", "-quiet", "-force-overwrite", "-output-directory", str(extract_dir), str(archive_path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=3600,
        )
        return "unar", (result.stdout + "\n" + result.stderr).strip(), result.returncode
    if shutil.which("7z"):
        result = subprocess.run(
            ["7z", "x", "-y", f"-o{extract_dir}", str(archive_path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=3600,
        )
        return "7z", (result.stdout + "\n" + result.stderr).strip(), result.returncode
    if shutil.which("unrar"):
        result = subprocess.run(
            ["unrar", "x", "-y", str(archive_path), str(extract_dir) + os.sep],
            check=False,
            capture_output=True,
            text=True,
            timeout=3600,
        )
        return "unrar", (result.stdout + "\n" + result.stderr).strip(), result.returncode
    return "none", "No RAR-capable extractor found.", 1


def manifest_files(root: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        relative = path.relative_to(root).as_posix()
        rows.append(
            {
                "relative_path": relative,
                "suffix": path.suffix.lower(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return rows


def dedupe_labels(labels: list[Any]) -> list[str]:
    seen: dict[str, int] = {}
    output: list[str] = []
    for index, label in enumerate(labels, start=1):
        value = "" if label is None else str(label).strip()
        if not value or value.lower() == "nan":
            value = f"unnamed_{index}"
        count = seen.get(value, 0)
        seen[value] = count + 1
        output.append(value if count == 0 else f"{value}_{count + 1}")
    return output


def detect_xmu_header_row(frame: Any) -> int | None:
    for index in range(min(20, len(frame))):
        values = ["" if value is None else str(value).strip() for value in frame.iloc[index, :5].tolist()]
        if values[:4] == ["年份", "行政区划编码", "省份", "城市"]:
            return index
    return None


def xmu_normalized_columns(labels: list[str]) -> list[str]:
    known = {
        "年份": "year",
        "行政区划编码": "admin_code",
        "省份": "province",
        "城市": "city",
        "统计范围": "stat_scope",
    }
    normalized = []
    for index, label in enumerate(labels, start=1):
        normalized.append(known.get(label, f"var_{index:03d}"))
    return unique_columns(normalized)


def write_xmu_variable_dictionary(path: Path, labels: list[str], normalized: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["position", "normalized_column", "original_label"])
        for index, (normalized_name, original_label) in enumerate(zip(normalized, labels, strict=True), start=1):
            writer.writerow([index, normalized_name, original_label])


def clean_extracted_tabular_files(extract_dir: Path, clean_dir: Path, refresh: bool) -> list[dict[str, Any]]:
    clean_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    tabular_suffixes = {".csv", ".txt", ".tsv", ".dta", ".xlsx", ".xls"}
    tabular_files = [path for path in sorted(extract_dir.rglob("*")) if path.is_file() and path.suffix.lower() in tabular_suffixes]
    panel_files = [
        path
        for path in tabular_files
        if path.suffix.lower() in {".xlsx", ".xls"} and ("面版数据" in path.name or "面板数据" in path.name)
    ]
    if panel_files:
        tabular_files = panel_files
    for path in tabular_files:
        relative = path.relative_to(extract_dir)
        source_hash = hashlib.sha1(relative.as_posix().encode("utf-8")).hexdigest()[:10]
        safe_stem = f"{sanitize_identifier('_'.join(relative.with_suffix('').parts), 'table')}_{source_hash}"
        target_dir = clean_dir / safe_stem
        target_dir.mkdir(parents=True, exist_ok=True)
        suffix = path.suffix.lower()
        try:
            if suffix in {".csv", ".txt", ".tsv"}:
                target = target_dir / f"{safe_stem}{suffix}"
                if refresh or not target.exists():
                    shutil.copy2(path, target)
                csv_rows, csv_cols, header = csv_shape(target) if suffix in {".csv", ".tsv"} else (None, None, [])
                rows.append(
                    {
                        "source_relative_path": relative.as_posix(),
                        "clean_relative_path": target.relative_to(clean_dir).as_posix(),
                        "status": "copied",
                        "rows": csv_rows,
                        "columns": csv_cols,
                        "header": json.dumps(header[:50], ensure_ascii=False),
                    }
                )
                continue
            try:
                import pandas as pd  # type: ignore[import-not-found]
            except Exception as exc:  # noqa: BLE001
                rows.append(
                    {
                        "source_relative_path": relative.as_posix(),
                        "clean_relative_path": "",
                        "status": "skipped_missing_pandas",
                        "notes": repr(exc),
                    }
                )
                continue
            if suffix == ".dta":
                target = target_dir / f"{safe_stem}.csv"
                if refresh or not target.exists():
                    frame = pd.read_stata(path)
                    frame.to_csv(target, index=False)
                csv_rows, csv_cols, header = csv_shape(target)
                rows.append(
                    {
                        "source_relative_path": relative.as_posix(),
                        "clean_relative_path": target.relative_to(clean_dir).as_posix(),
                        "status": "converted_dta_to_csv",
                        "rows": csv_rows,
                        "columns": csv_cols,
                        "header": json.dumps(header[:50], ensure_ascii=False),
                    }
                )
                continue
            sheets = pd.read_excel(path, sheet_name=None, header=None)
            for sheet_name, raw_frame in sheets.items():
                sheet_stem = sanitize_identifier(str(sheet_name), "sheet")
                header_row = detect_xmu_header_row(raw_frame)
                if header_row is None:
                    frame = raw_frame
                    labels = [f"col_{index}" for index in range(1, len(frame.columns) + 1)]
                    frame.columns = labels
                    normalized_columns = labels
                    status = "converted_excel_sheet_to_csv_no_detected_header"
                else:
                    labels = dedupe_labels(raw_frame.iloc[header_row].tolist())
                    frame = raw_frame.iloc[header_row + 1 :].copy()
                    frame = frame.dropna(how="all")
                    frame.columns = labels
                    normalized_columns = xmu_normalized_columns(labels)
                    status = "converted_excel_sheet_to_clean_csv"
                raw_target = target_dir / f"{safe_stem}__{sheet_stem}__raw.csv"
                normalized_target = target_dir / f"{safe_stem}__{sheet_stem}__normalized.csv"
                dictionary_target = target_dir / f"{safe_stem}__{sheet_stem}__variables.csv"
                if refresh or not raw_target.exists():
                    frame.to_csv(raw_target, index=False)
                normalized_frame = frame.copy()
                normalized_frame.columns = normalized_columns
                if refresh or not normalized_target.exists():
                    normalized_frame.to_csv(normalized_target, index=False)
                if refresh or not dictionary_target.exists():
                    write_xmu_variable_dictionary(dictionary_target, labels, normalized_columns)
                rows.append(
                    {
                        "source_relative_path": relative.as_posix(),
                        "clean_relative_path": raw_target.relative_to(clean_dir).as_posix(),
                        "normalized_relative_path": normalized_target.relative_to(clean_dir).as_posix(),
                        "dictionary_relative_path": dictionary_target.relative_to(clean_dir).as_posix(),
                        "sheet": str(sheet_name),
                        "status": status,
                        "rows": len(frame),
                        "columns": len(frame.columns),
                        "header_row": header_row,
                        "header": json.dumps([str(column) for column in frame.columns[:50]], ensure_ascii=False),
                    }
                )
        except Exception as exc:  # noqa: BLE001
            rows.append(
                {
                    "source_relative_path": relative.as_posix(),
                    "clean_relative_path": "",
                    "status": "failed",
                    "notes": repr(exc),
                }
            )
    return rows


def import_xmu_clean_outputs(conn: sqlite3.Connection, clean_dir: Path, clean_rows: list[dict[str, Any]]) -> None:
    candidates = [
        row
        for row in clean_rows
        if row.get("normalized_relative_path") and row.get("dictionary_relative_path") and row.get("status") != "failed"
    ]
    if not candidates:
        record_run(
            conn,
            "china_xmu_city_stats_panel_2004_2020_sqlite_import",
            "download_ingest_only",
            "skipped",
            local_path=clean_dir,
            notes="No normalized clean CSV was produced.",
        )
        return
    canonical = next((row for row in candidates if "查看版" in str(row.get("source_relative_path", ""))), candidates[0])
    normalized_path = clean_dir / str(canonical["normalized_relative_path"])
    dictionary_path = clean_dir / str(canonical["dictionary_relative_path"])
    try:
        panel_rows = import_csv(conn, "china_xmu_city_stats_panel_2004_2020", normalized_path)
        dictionary_rows = import_csv(conn, "china_xmu_city_stats_panel_2004_2020_variables", dictionary_path)
        record_run(
            conn,
            "china_xmu_city_stats_panel_2004_2020_sqlite_import",
            "download_ingest_only",
            "ingested",
            rows=panel_rows,
            bytes_count=normalized_path.stat().st_size,
            sha256=sha256_file(normalized_path),
            local_path=normalized_path,
            notes=(
                "Imported canonical normalized panel CSV and variable dictionary into SQLite. "
                f"dictionary_rows={dictionary_rows}; source={canonical.get('source_relative_path')}"
            ),
        )
    except Exception as exc:  # noqa: BLE001
        record_run(
            conn,
            "china_xmu_city_stats_panel_2004_2020_sqlite_import",
            "download_ingest_only",
            "failed",
            local_path=normalized_path,
            notes=repr(exc),
        )


def ingest_china_xmu_city_stats_panel_archive(
    conn: sqlite3.Connection,
    raw_dir: Path,
    refresh: bool,
    include_large_archives: bool,
) -> None:
    archive_path = raw_dir / "xmu_city_stats_panel_2004_2020.rar"
    try:
        head = fetch_head_metadata(CHINA_XMU_CITY_STATS_PANEL_URL, timeout=60)
    except Exception as exc:  # noqa: BLE001
        record_run(
            conn,
            "china_xmu_city_stats_panel_2004_2020_head",
            "download_ingest_only",
            "failed",
            source_url=CHINA_XMU_CITY_STATS_PANEL_URL,
            local_path=archive_path,
            notes=repr(exc),
        )
        head = {}

    if not include_large_archives:
        record_run(
            conn,
            "china_xmu_city_stats_panel_2004_2020_archive",
            "download_ingest_only",
            "skipped_large_file",
            bytes_count=head.get("content_length"),
            source_url=CHINA_XMU_CITY_STATS_PANEL_URL,
            local_path=archive_path,
            notes=(
                "Public XMU RAR archive; pass --include-large-china-city-archives to download, "
                "extract, and stage it."
            ),
        )
        return

    try:
        status, bytes_count, digest = download_file(CHINA_XMU_CITY_STATS_PANEL_URL, archive_path, refresh=refresh, timeout=7200)
        record_run(
            conn,
            "china_xmu_city_stats_panel_2004_2020_archive",
            "download_ingest_only",
            status,
            bytes_count=bytes_count,
            sha256=digest,
            source_url=CHINA_XMU_CITY_STATS_PANEL_URL,
            local_path=archive_path,
            notes="Downloaded public XMU archive for 2004-2020 China City Statistical Yearbook panel data.",
        )
    except Exception as exc:  # noqa: BLE001
        record_run(
            conn,
            "china_xmu_city_stats_panel_2004_2020_archive",
            "download_ingest_only",
            "failed",
            bytes_count=head.get("content_length"),
            source_url=CHINA_XMU_CITY_STATS_PANEL_URL,
            local_path=archive_path,
            notes=repr(exc),
        )
        return

    extract_dir = raw_dir / "xmu_city_stats_panel_2004_2020_extracted"
    if refresh and extract_dir.exists():
        shutil.rmtree(extract_dir)
    if extract_dir.exists() and any(extract_dir.rglob("*")) and not refresh:
        extractor, output, returncode = "cached", "Existing extraction directory reused.", 0
    else:
        extractor, output, returncode = extract_archive(archive_path, extract_dir)
    file_rows = manifest_files(extract_dir) if extract_dir.exists() else []
    replace_json_table(conn, "china_xmu_city_stats_panel_2004_2020_files", file_rows)
    record_run(
        conn,
        "china_xmu_city_stats_panel_2004_2020_extract",
        "download_ingest_only",
        "extracted" if returncode == 0 else "failed",
        rows=len(file_rows),
        bytes_count=sum(int(row.get("bytes") or 0) for row in file_rows),
        local_path=extract_dir,
        notes=f"extractor={extractor}; output_tail={output[-1000:]}",
    )
    if returncode != 0:
        return

    clean_dir = raw_dir / "xmu_city_stats_panel_2004_2020_clean"
    if refresh and clean_dir.exists():
        shutil.rmtree(clean_dir)
    clean_rows = clean_extracted_tabular_files(extract_dir, clean_dir, refresh=refresh)
    replace_json_table(conn, "china_xmu_city_stats_panel_2004_2020_clean_manifest", clean_rows)
    import_xmu_clean_outputs(conn, clean_dir, clean_rows)
    record_run(
        conn,
        "china_xmu_city_stats_panel_2004_2020_clean",
        "download_ingest_only",
        "cleaned" if clean_rows else "no_tabular_files_found",
        rows=len(clean_rows),
        bytes_count=sum(path.stat().st_size for path in clean_dir.rglob("*") if path.is_file()) if clean_dir.exists() else 0,
        local_path=clean_dir,
        notes="Converted discovered Excel/Stata files to CSV where pandas support is available; raw archive and extraction are preserved.",
    )


def first(value: Any) -> Any:
    if isinstance(value, list):
        return value[0] if value else None
    return value


def ingest_gdelt(conn: sqlite3.Connection) -> None:
    url = (
        "https://api.gdeltproject.org/api/v2/doc/doc?"
        + urllib.parse.urlencode(
            {
                "query": "protest",
                "mode": "artlist",
                "format": "json",
                "maxrecords": "10",
            }
        )
    )
    try:
        payload = fetch_json(url)
        rows = payload.get("articles", []) if isinstance(payload, dict) else []
        replace_json_table(conn, "gdelt_doc_protest_sample", rows)
        record_run(conn, "gdelt_doc_sample", "public_no_secret", "ingested", rows=len(rows), source_url=url)
    except urllib.error.HTTPError as exc:
        status = "rate_limited" if exc.code == 429 else "failed"
        record_run(conn, "gdelt_doc_sample", "public_no_secret", status, source_url=url, notes=repr(exc))
    except Exception as exc:  # noqa: BLE001
        record_run(conn, "gdelt_doc_sample", "public_no_secret", "failed", source_url=url, notes=repr(exc))


def ingest_gdelt_latest_events(conn: sqlite3.Connection, raw_dir: Path, refresh: bool) -> None:
    last_update_url = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"
    try:
        last_update = fetch_bytes(last_update_url, timeout=60).decode("utf-8")
        export_url = ""
        for line in last_update.splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[2].endswith(".export.CSV.zip"):
                export_url = parts[2]
                break
        if not export_url:
            raise RuntimeError("No latest export.CSV.zip URL found in lastupdate.txt")
        zip_path = raw_dir / Path(urllib.parse.urlparse(export_url).path).name
        status, bytes_count, digest = download_file(export_url, zip_path, refresh=refresh, timeout=120)
        with zipfile.ZipFile(zip_path) as archive:
            csv_names = [name for name in archive.namelist() if name.endswith(".CSV")]
            if not csv_names:
                raise RuntimeError(f"No CSV member found in {zip_path}")
            csv_name = csv_names[0]
            csv_path = raw_dir / csv_name
            if refresh or not csv_path.exists():
                with archive.open(csv_name) as source, csv_path.open("wb") as target:
                    shutil.copyfileobj(source, target)
        rows = import_headerless_csv(conn, "gdelt_latest_events", csv_path)
        record_run(
            conn,
            "gdelt_latest_events",
            "public_no_secret",
            status,
            rows=rows,
            bytes_count=bytes_count,
            sha256=digest,
            source_url=export_url,
            local_path=zip_path,
            notes="Latest GDELT 2.0 events export discovered from lastupdate.txt.",
        )
    except Exception as exc:  # noqa: BLE001
        record_run(
            conn,
            "gdelt_latest_events",
            "public_no_secret",
            "failed",
            source_url=last_update_url,
            notes=repr(exc),
        )


def import_headerless_csv(conn: sqlite3.Connection, table: str, path: Path) -> int:
    csv.field_size_limit(sys.maxsize)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        rows = list(reader)
    width = max((len(row) for row in rows), default=0)
    columns = [f"col_{index}" for index in range(1, width + 1)] or ["empty"]
    normalized_rows: list[dict[str, Any]] = []
    for row in rows:
        if len(row) < width:
            row.extend([None] * (width - len(row)))
        normalized_rows.append({column: value for column, value in zip(columns, row, strict=True)})
    return replace_rows(conn, table, columns, normalized_rows)


def ingest_dhs_metadata(conn: sqlite3.Connection) -> None:
    url = "https://api.dhsprogram.com/rest/dhs/countries?f=json"
    try:
        payload = fetch_json(url, timeout=60)
        rows = payload.get("Data", []) if isinstance(payload, dict) else []
        replace_json_table(conn, "dhs_countries", rows)
        record_run(conn, "dhs_countries", "public_no_secret", "ingested", rows=len(rows), source_url=url)
    except Exception as exc:  # noqa: BLE001
        record_run(conn, "dhs_countries", "public_no_secret", "failed", source_url=url, notes=repr(exc))


def ingest_qog(
    conn: sqlite3.Connection,
    raw_dir: Path,
    refresh: bool,
    include_standard: bool,
) -> None:
    downloads = list(QOG_DOWNLOADS)
    if include_standard:
        downloads.extend(QOG_STANDARD_DOWNLOADS)
    else:
        for source in QOG_STANDARD_DOWNLOADS:
            record_run(
                conn,
                source["source_id"],
                source["access_class"],
                "skipped",
                source_url=source["url"],
                notes="Pass --include-qog-standard to download the larger Standard dataset.",
            )

    for source in downloads:
        url = source["url"]
        local_path = raw_dir / Path(urllib.parse.urlparse(url).path).name
        try:
            status, bytes_count, digest = download_file(url, local_path, refresh=refresh, timeout=300)
            rows = import_csv(conn, source["table"], local_path)
            record_run(
                conn,
                source["source_id"],
                source["access_class"],
                status,
                rows=rows,
                bytes_count=bytes_count,
                sha256=digest,
                source_url=url,
                local_path=local_path,
            )
        except Exception as exc:  # noqa: BLE001
            record_run(
                conn,
                source["source_id"],
                source["access_class"],
                "failed",
                source_url=url,
                local_path=local_path,
                notes=repr(exc),
            )


def ingest_vdem(conn: sqlite3.Connection, raw_dir: Path, refresh: bool, parse_vdem: bool) -> None:
    url = "https://github.com/vdeminstitute/vdemdata/raw/master/vdemdata_16.0.tar.gz"
    local_path = raw_dir / "vdemdata_16.0.tar.gz"
    try:
        status, bytes_count, digest = download_file(url, local_path, refresh=refresh, timeout=300)
        members = []
        with tarfile.open(local_path, "r:gz") as archive:
            for member in archive.getmembers():
                members.append(
                    {
                        "path": member.name,
                        "size": member.size,
                        "type": "file" if member.isfile() else "directory" if member.isdir() else "other",
                    }
                )
        replace_json_table(conn, "vdem_package_files", members)
        record_run(
            conn,
            "vdemdata_tarball",
            "download_ingest_only",
            status,
            rows=len(members),
            bytes_count=bytes_count,
            sha256=digest,
            source_url=url,
            local_path=local_path,
            notes="Official public vdeminstitute/vdemdata package tarball; website CSV downloads require form fields.",
        )
        if parse_vdem:
            parse_vdem_package(conn, local_path, raw_dir, refresh=refresh)
        else:
            record_run(
                conn,
                "vdemdata_rda_parse",
                "download_ingest_only",
                "skipped",
                source_url=url,
                local_path=local_path,
                notes="Pass --parse-vdem to use Rscript and import package .rda data frames.",
            )
    except Exception as exc:  # noqa: BLE001
        record_run(
            conn,
            "vdemdata_tarball",
            "download_ingest_only",
            "failed",
            source_url=url,
            local_path=local_path,
            notes=repr(exc),
        )


def parse_vdem_package(conn: sqlite3.Connection, archive_path: Path, raw_dir: Path, refresh: bool) -> None:
    if not shutil.which("Rscript"):
        record_run(
            conn,
            "vdemdata_rda_parse",
            "download_ingest_only",
            "failed",
            local_path=archive_path,
            notes="Rscript is not available.",
        )
        return

    extract_dir = raw_dir / "vdemdata_16_0_pkg"
    csv_dir = raw_dir / "vdemdata_16_0_csv"
    if refresh and extract_dir.exists():
        shutil.rmtree(extract_dir)
    if refresh and csv_dir.exists():
        shutil.rmtree(csv_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)
    csv_dir.mkdir(parents=True, exist_ok=True)

    safe_extract_tar(archive_path, extract_dir)
    rda_files = sorted(
        path for path in extract_dir.rglob("*") if path.is_file() and path.suffix.lower() in {".rda", ".rdata"}
    )
    if not rda_files:
        record_run(
            conn,
            "vdemdata_rda_parse",
            "download_ingest_only",
            "failed",
            local_path=archive_path,
            notes="No .rda files found in package.",
        )
        return

    r_script = (
        "args <- commandArgs(TRUE)\n"
        "rda <- args[[1]]\n"
        "out <- args[[2]]\n"
        "stem <- args[[3]]\n"
        "objs <- load(rda)\n"
        "for (name in objs) {\n"
        "  x <- get(name)\n"
        "  if (is.data.frame(x)) {\n"
        "    safe <- gsub('[^A-Za-z0-9_]+', '_', paste(stem, name, sep='__'))\n"
        "    write.csv(x, file=file.path(out, paste0(safe, '.csv')), row.names=FALSE, na='')\n"
        "    cat(safe, '\\n')\n"
        "  }\n"
        "}\n"
    )
    imported = 0
    for rda_file in rda_files:
        stem = sanitize_identifier(rda_file.stem, "rda")
        existing_csvs = sorted(csv_dir.glob(f"{stem}__*.csv")) if not refresh else []
        if existing_csvs:
            csv_names = [path.stem for path in existing_csvs]
        else:
            result = subprocess.run(
                ["Rscript", "-e", r_script, str(rda_file), str(csv_dir), stem],
                check=False,
                capture_output=True,
                text=True,
                timeout=600,
            )
            if result.returncode != 0:
                record_run(
                    conn,
                    f"vdemdata_rda_{stem}",
                    "download_ingest_only",
                    "failed",
                    local_path=rda_file,
                    notes=result.stderr[-1000:],
                )
                continue
            csv_names = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        for csv_name in csv_names:
            if not csv_name:
                continue
            csv_path = csv_dir / f"{csv_name}.csv"
            if not csv_path.exists():
                continue
            table = sanitize_identifier(f"vdem_{csv_name}", "vdem_table")
            rows, column_count, _header = csv_shape(csv_path)
            try:
                if column_count > 1900:
                    selected_table = "vdem_country_year_core" if "vdem__vdem" in csv_name else f"{table}_core"
                    selected_rows, selected_columns = import_csv_selected(
                        conn,
                        selected_table,
                        csv_path,
                        VDEM_CORE_COLUMNS,
                    )
                    imported += 1
                    record_run(
                        conn,
                        selected_table,
                        "download_ingest_only",
                        "ingested",
                        rows=selected_rows,
                        bytes_count=csv_path.stat().st_size,
                        sha256=sha256_file(csv_path),
                        local_path=csv_path,
                        notes=(
                            f"Imported selected columns from {rda_file.name}; "
                            f"full CSV has {column_count} columns and is kept as raw file. "
                            f"selected_columns={','.join(selected_columns)}"
                        ),
                    )
                    record_run(
                        conn,
                        table,
                        "download_ingest_only",
                        "materialized_csv",
                        rows=rows,
                        bytes_count=csv_path.stat().st_size,
                        sha256=sha256_file(csv_path),
                        local_path=csv_path,
                        notes=f"Not imported as a full SQLite table because it has {column_count} columns.",
                    )
                    continue
                imported_rows = import_csv(conn, table, csv_path)
                imported += 1
                record_run(
                    conn,
                    table,
                    "download_ingest_only",
                    "ingested",
                    rows=imported_rows,
                    bytes_count=csv_path.stat().st_size,
                    sha256=sha256_file(csv_path),
                    local_path=csv_path,
                    notes=f"Imported from {rda_file.name}.",
                )
            except Exception as exc:  # noqa: BLE001
                record_run(
                    conn,
                    table,
                    "download_ingest_only",
                    "failed",
                    rows=rows,
                    bytes_count=csv_path.stat().st_size,
                    sha256=sha256_file(csv_path),
                    local_path=csv_path,
                    notes=repr(exc),
                )
    record_run(
        conn,
        "vdemdata_rda_parse",
        "download_ingest_only",
        "ingested" if imported else "failed",
        rows=imported,
        local_path=csv_dir,
        notes=f"Imported {imported} V-Dem data frame(s).",
    )


def safe_extract_tar(archive_path: Path, extract_dir: Path) -> None:
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive.getmembers():
            target = (extract_dir / member.name).resolve()
            if not str(target).startswith(str(extract_dir.resolve())):
                raise RuntimeError(f"unsafe tar member path: {member.name}")
        archive.extractall(extract_dir)


def write_report(conn: sqlite3.Connection, out_dir: Path, db_path: Path) -> None:
    runs = conn.execute(
        """
        SELECT source_id, status, COALESCE(rows, 0), COALESCE(bytes, 0), COALESCE(local_path, '')
        FROM ingest_runs
        ORDER BY rowid
        """
    ).fetchall()
    queue = conn.execute(
        """
        SELECT source_id, access_class, auth_env_var, env_present, reason
        FROM source_queue
        ORDER BY source_id
        """
    ).fetchall()
    report = {
        "created_at": now_iso(),
        "database": str(db_path),
        "runs": [
            {
                "source_id": source_id,
                "status": status,
                "rows": rows,
                "bytes": bytes_count,
                "local_path": local_path,
            }
            for source_id, status, rows, bytes_count, local_path in runs
        ],
        "source_queue": [
            {
                "source_id": source_id,
                "access_class": access_class,
                "auth_env_var": auth_env_var,
                "env_present": bool(env_present),
                "reason": reason,
            }
            for source_id, access_class, auth_env_var, env_present, reason in queue
        ],
    }
    report_path = out_dir / "seed_store_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"database={db_path}")
    print(f"report={report_path}")
    for source_id, status, rows, bytes_count, local_path in runs:
        print(f"{source_id}\t{status}\trows={rows}\tbytes={bytes_count}\t{local_path}")


def main() -> int:
    args = parse_args()
    out_dir, raw_dir = ensure_dirs(args.out_dir)
    db_path = out_dir / "public_sources.sqlite"
    conn = connect(db_path)
    try:
        insert_source_queue(conn)
        ingest_worldbank(conn, raw_dir, args)
        ingest_dataflow_catalog(
            conn,
            raw_dir,
            "oecd",
            "oecd_dataflows",
            "https://sdmx.oecd.org/public/rest/dataflow/all",
            refresh=args.refresh,
        )
        ingest_dataflow_catalog(
            conn,
            raw_dir,
            "eurostat",
            "eurostat_dataflows",
            "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/dataflow/ESTAT/all",
            refresh=args.refresh,
            timeout=420,
        )
        ingest_dataflow_catalog(
            conn,
            raw_dir,
            "ecb",
            "ecb_dataflows",
            "https://data-api.ecb.europa.eu/service/dataflow/ECB/all/latest?detail=allstubs",
            refresh=args.refresh,
            timeout=180,
        )
        ingest_dataflow_catalog(
            conn,
            raw_dir,
            "ilostat",
            "ilostat_dataflows",
            "https://sdmx.ilo.org/rest/v1/dataflow/all/all/latest?detail=allstubs",
            refresh=args.refresh,
            timeout=180,
        )
        ingest_sdg(conn)
        ingest_crossref(conn)
        ingest_datacite(conn)
        ingest_who_gho(conn)
        ingest_unhcr_metadata(conn)
        ingest_owid_grapher(conn, raw_dir, refresh=args.refresh)
        ingest_nasa_power_sample(conn)
        ingest_federal_register_sample(conn)
        ingest_harvard_dataverse_sample(conn)
        ingest_voteview_members(conn, raw_dir, refresh=args.refresh)
        ingest_parlgov_core(conn, raw_dir, refresh=args.refresh)
        ingest_global_country_year_panels(conn, raw_dir, refresh=args.refresh)
        ingest_china_areacodes(conn, raw_dir, refresh=args.refresh)
        ingest_china_ceads_catalogs(conn, raw_dir, refresh=args.refresh)
        ingest_china_chap_pm25_manifest(conn)
        ingest_china_nbs_city_backend_probe(conn)
        ingest_china_xmu_city_stats_panel_archive(
            conn,
            raw_dir,
            refresh=args.refresh,
            include_large_archives=args.include_large_china_city_archives,
        )
        if args.include_gdelt:
            ingest_gdelt(conn)
            ingest_gdelt_latest_events(conn, raw_dir, refresh=args.refresh)
        ingest_dhs_metadata(conn)
        ingest_qog(conn, raw_dir, refresh=args.refresh, include_standard=args.include_qog_standard)
        ingest_vdem(conn, raw_dir, refresh=args.refresh, parse_vdem=args.parse_vdem)
        write_country_year_panel_catalog(conn)
        write_report(conn, out_dir, db_path)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
