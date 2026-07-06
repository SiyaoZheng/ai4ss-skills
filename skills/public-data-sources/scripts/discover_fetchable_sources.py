#!/usr/bin/env python3
"""Search verified no-secret research-data discovery platforms."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


USER_AGENT = "ai4ss-public-data-sources/0.1 (+agent-fetchable-verification)"
VERIFY_DATE = "2026-07-05"
DEFAULT_FILE_LIMIT = 50

DEFAULT_PLATFORMS = [
    "zenodo",
    "datacite",
    "dataverse",
    "figshare",
    "dryad",
    "openaire",
    "re3data",
    "osf",
]

FETCH_LEVELS = {
    "zenodo": "file_fetchable_when_public",
    "datacite": "metadata_fetchable",
    "dataverse": "file_fetchable_when_public",
    "figshare": "file_fetchable_when_public",
    "dryad": "metadata_fetchable",
    "openaire": "metadata_fetchable",
    "re3data": "metadata_fetchable",
    "osf": "metadata_fetchable",
}


class FetchError(RuntimeError):
    pass


def request_bytes(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: int = 45,
) -> tuple[bytes, str]:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json, text/xml;q=0.9, */*;q=0.5"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read(), resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        body = exc.read(500).decode("utf-8", errors="replace")
        raise FetchError(f"{url} returned HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise FetchError(f"{url} failed: {exc}") from exc


def request_json(url: str, *, method: str = "GET", payload: dict[str, Any] | None = None) -> Any:
    raw, _ = request_bytes(url, method=method, payload=payload)
    return json.loads(raw.decode("utf-8"))


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def compact(values: list[Any]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = clean_text(value)
        if text and text not in seen:
            out.append(text)
            seen.add(text)
    return out


def safe_get(mapping: Any, path: list[str], default: Any = None) -> Any:
    cur: Any = mapping
    for key in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
    return cur if cur is not None else default


def normalize_doi_value(doi: str | None) -> str | None:
    if not doi:
        return None
    doi = doi.strip()
    doi = re.sub(r"^doi:", "", doi, flags=re.IGNORECASE)
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    return doi or None


def doi_landing(doi: str | None) -> str | None:
    doi = normalize_doi_value(doi)
    return "https://doi.org/" + doi if doi else None


def cap_files(files: list[dict[str, Any]], limit: int = DEFAULT_FILE_LIMIT) -> list[dict[str, Any]]:
    return files[:limit]


def normalize_file(
    *,
    name: str | None,
    download_url: str | None,
    size: int | None = None,
    checksum: str | None = None,
    restricted: bool | None = None,
    content_type: str | None = None,
) -> dict[str, Any]:
    return {
        "name": clean_text(name),
        "download_url": download_url,
        "size": size,
        "checksum": checksum,
        "restricted": restricted,
        "content_type": content_type,
    }


def result(
    *,
    platform: str,
    title: str | None,
    identifier: str | None,
    doi: str | None,
    landing_url: str | None,
    api_url: str | None,
    creators: list[Any] | None = None,
    published: str | None = None,
    license_name: str | None = None,
    files: list[dict[str, Any]] | None = None,
    access_note: str,
) -> dict[str, Any]:
    clean_doi = normalize_doi_value(doi)
    return {
        "platform": platform,
        "fetch_level": FETCH_LEVELS[platform],
        "title": clean_text(title),
        "identifier": identifier,
        "doi": clean_doi,
        "landing_url": landing_url or doi_landing(clean_doi),
        "api_url": api_url,
        "creators": compact(creators or []),
        "published": published,
        "license": clean_text(license_name),
        "files": files or [],
        "access_note": access_note,
    }


def search_zenodo(query: str, limit: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"q": query, "size": limit})
    url = f"https://zenodo.org/api/records?{params}"
    obj = request_json(url)
    rows = []
    for item in safe_get(obj, ["hits", "hits"], []):
        metadata = item.get("metadata", {})
        files = []
        raw_files = item.get("files", [])
        if isinstance(raw_files, dict):
            raw_files = raw_files.get("entries", {}).values()
        for file_info in raw_files or []:
            links = file_info.get("links", {})
            checksum = file_info.get("checksum")
            files.append(
                normalize_file(
                    name=file_info.get("key") or file_info.get("filename"),
                    download_url=links.get("self") or links.get("download") or links.get("content"),
                    size=file_info.get("size"),
                    checksum=checksum,
                )
            )
        rows.append(
            result(
                platform="zenodo",
                title=metadata.get("title"),
                identifier=str(item.get("id")) if item.get("id") is not None else None,
                doi=metadata.get("doi") or item.get("doi"),
                landing_url=safe_get(item, ["links", "html"]) or item.get("doi_url"),
                api_url=safe_get(item, ["links", "self"]) or url,
                creators=[creator.get("name") for creator in metadata.get("creators", []) if isinstance(creator, dict)],
                published=metadata.get("publication_date") or item.get("created"),
                license_name=safe_get(metadata, ["license", "id"]) or metadata.get("license"),
                files=cap_files([f for f in files if f["download_url"]]),
                access_note="Search is no-secret; download only files exposed by public record metadata.",
            )
        )
    return rows


def search_datacite(query: str, limit: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"query": query, "resource-type-id": "Dataset", "page[size]": limit})
    url = f"https://api.datacite.org/dois?{params}"
    obj = request_json(url)
    rows = []
    for item in obj.get("data", []):
        attrs = item.get("attributes", {})
        titles = attrs.get("titles") or []
        title = titles[0].get("title") if titles and isinstance(titles[0], dict) else None
        creators = []
        for creator in attrs.get("creators", []) or []:
            if isinstance(creator, dict):
                creators.append(creator.get("name") or creator.get("familyName"))
        doi = attrs.get("doi") or item.get("id")
        rows.append(
            result(
                platform="datacite",
                title=title,
                identifier=item.get("id"),
                doi=doi,
                landing_url=attrs.get("url") or doi_landing(doi),
                api_url=safe_get(item, ["links", "self"]) or url,
                creators=creators,
                published=attrs.get("published") or attrs.get("publicationYear"),
                license_name=None,
                access_note="Metadata router only; follow DOI or landing URL to a source-specific API before acquisition.",
            )
        )
    return rows


def dataverse_files(global_id: str | None) -> list[dict[str, Any]]:
    if not global_id:
        return []
    params = urllib.parse.urlencode({"persistentId": global_id})
    url = f"https://dataverse.harvard.edu/api/datasets/:persistentId/?{params}"
    try:
        obj = request_json(url)
    except FetchError:
        return []
    files = []
    for wrapper in safe_get(obj, ["data", "latestVersion", "files"], []):
        data_file = wrapper.get("dataFile", {})
        file_id = data_file.get("id")
        restricted = bool(wrapper.get("restricted"))
        download_url = None if restricted or file_id is None else f"https://dataverse.harvard.edu/api/access/datafile/{file_id}"
        checksum = safe_get(data_file, ["checksum", "value"]) or data_file.get("md5")
        files.append(
            normalize_file(
                name=wrapper.get("label") or data_file.get("filename"),
                download_url=download_url,
                size=data_file.get("filesize"),
                checksum=checksum,
                restricted=restricted,
                content_type=data_file.get("contentType"),
            )
        )
    return cap_files(files)


def search_dataverse(query: str, limit: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"q": query, "type": "dataset", "per_page": limit})
    url = f"https://dataverse.harvard.edu/api/search?{params}"
    obj = request_json(url)
    rows = []
    for item in safe_get(obj, ["data", "items"], []):
        global_id = item.get("global_id")
        rows.append(
            result(
                platform="dataverse",
                title=item.get("name"),
                identifier=global_id,
                doi=global_id,
                landing_url=item.get("url"),
                api_url=url,
                creators=item.get("authors") or [],
                published=item.get("published_at"),
                license_name=None,
                files=dataverse_files(global_id),
                access_note="Search is no-secret with a User-Agent; download only unrestricted files.",
            )
        )
    return rows


def search_figshare(query: str, limit: int) -> list[dict[str, Any]]:
    url = "https://api.figshare.com/v2/articles/search"
    items = request_json(url, method="POST", payload={"search_for": query, "item_type": 3, "page_size": limit})
    rows = []
    for item in items[:limit]:
        detail_url = item.get("url_public_api") or item.get("url") or f"https://api.figshare.com/v2/articles/{item.get('id')}"
        try:
            detail = request_json(detail_url)
        except FetchError:
            detail = item
        files = []
        for file_info in detail.get("files", []) or []:
            files.append(
                normalize_file(
                    name=file_info.get("name"),
                    download_url=file_info.get("download_url"),
                    size=file_info.get("size"),
                    checksum=file_info.get("computed_md5") or file_info.get("supplied_md5"),
                    restricted=False,
                    content_type=file_info.get("mimetype"),
                )
            )
        rows.append(
            result(
                platform="figshare",
                title=detail.get("title") or item.get("title"),
                identifier=str(detail.get("id") or item.get("id")),
                doi=detail.get("doi") or item.get("doi"),
                landing_url=detail.get("url_public_html") or item.get("url_public_html"),
                api_url=detail_url,
                creators=[author.get("full_name") for author in detail.get("authors", []) if isinstance(author, dict)],
                published=detail.get("published_date") or item.get("published_date"),
                license_name=safe_get(detail, ["license", "name"]),
                files=cap_files([f for f in files if f["download_url"]]),
                access_note="Search and public details are no-secret; details may expose direct file download URLs.",
            )
        )
    return rows


def search_dryad(query: str, limit: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"q": query, "per_page": limit})
    url = f"https://datadryad.org/api/v2/search?{params}"
    obj = request_json(url)
    rows = []
    for item in safe_get(obj, ["_embedded", "stash:datasets"], []):
        identifier = item.get("identifier")
        creators = []
        for author in item.get("authors", []) or []:
            if isinstance(author, dict):
                creators.append(" ".join(part for part in [author.get("firstName"), author.get("lastName")] if part))
        self_href = safe_get(item, ["_links", "self", "href"])
        rows.append(
            result(
                platform="dryad",
                title=item.get("title"),
                identifier=identifier,
                doi=identifier,
                landing_url=doi_landing(identifier),
                api_url=urllib.parse.urljoin("https://datadryad.org", self_href or ""),
                creators=creators,
                published=item.get("publicationDate"),
                license_name=item.get("license"),
                access_note="Search is no-secret; tested API download relation returned 401, so this is metadata-only by default.",
            )
        )
    return rows


def scalar_text(value: Any) -> str | None:
    if isinstance(value, dict):
        if "$" in value:
            return clean_text(value.get("$"))
        for key in ("@name", "@classname", "name", "title"):
            if key in value:
                return clean_text(value.get(key))
    if isinstance(value, str):
        return clean_text(value)
    return None


def listify(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def search_openaire(query: str, limit: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"keywords": query, "format": "json", "size": limit})
    url = f"https://api.openaire.eu/search/researchProducts?{params}"
    obj = request_json(url)
    raw_results = safe_get(obj, ["response", "results", "result"], [])
    rows = []
    for item in listify(raw_results)[:limit]:
        result_body = safe_get(item, ["metadata", "oaf:entity", "oaf:result"], {})
        pid = scalar_text(result_body.get("pid"))
        title = scalar_text(result_body.get("title"))
        creators = [scalar_text(creator) for creator in listify(result_body.get("creator"))]
        access = safe_get(result_body, ["bestaccessright", "@classname"])
        rows.append(
            result(
                platform="openaire",
                title=title,
                identifier=safe_get(item, ["header", "dri:objIdentifier", "$"]),
                doi=pid if safe_get(result_body.get("pid", {}), ["@classid"]) == "doi" else None,
                landing_url=doi_landing(pid) if safe_get(result_body.get("pid", {}), ["@classid"]) == "doi" else None,
                api_url=url,
                creators=[creator for creator in creators if creator],
                published=scalar_text(result_body.get("dateofacceptance")),
                license_name=access,
                access_note="OpenAIRE is a metadata aggregator; use it for discovery and then route to source-specific APIs.",
            )
        )
    return rows


def child_text(elem: ET.Element, tag: str) -> str | None:
    found = elem.find(tag)
    return clean_text(found.text) if found is not None else None


def search_re3data(query: str, limit: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"query": query})
    url = f"https://www.re3data.org/api/beta/repositories?{params}"
    raw, _ = request_bytes(url)
    root = ET.fromstring(raw)
    rows = []
    for repo in root.findall("repository")[:limit]:
        link = None
        link_elem = repo.find("link")
        if link_elem is not None:
            link = link_elem.attrib.get("href")
        repo_id = child_text(repo, "id")
        rows.append(
            result(
                platform="re3data",
                title=child_text(repo, "name"),
                identifier=repo_id,
                doi=child_text(repo, "doi"),
                landing_url=link,
                api_url=link or url,
                access_note="Repository registry only; search the repository's own API before treating data as acquired.",
            )
        )
    return rows


def search_osf(query: str, limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    per_endpoint = max(1, min(limit, 25))
    for endpoint in ("nodes", "preprints"):
        params = urllib.parse.urlencode({"filter[title]": query, "page[size]": per_endpoint})
        url = f"https://api.osf.io/v2/{endpoint}/?{params}"
        obj = request_json(url)
        for item in obj.get("data", []):
            result_id = f"{endpoint}:{item.get('id')}"
            if result_id in seen:
                continue
            seen.add(result_id)
            attrs = item.get("attributes", {})
            rows.append(
                result(
                    platform="osf",
                    title=attrs.get("title"),
                    identifier=result_id,
                    doi=attrs.get("doi"),
                    landing_url=safe_get(item, ["links", "html"]),
                    api_url=safe_get(item, ["links", "self"]) or url,
                    creators=[],
                    published=attrs.get("date_published") or attrs.get("date_created"),
                    license_name=safe_get(attrs, ["license_record", "name"]),
                    access_note="Public API metadata only by default; follow public file relationships before any acquisition.",
                )
            )
            if len(rows) >= limit:
                return rows
    return rows


SEARCHERS = {
    "zenodo": search_zenodo,
    "datacite": search_datacite,
    "dataverse": search_dataverse,
    "figshare": search_figshare,
    "dryad": search_dryad,
    "openaire": search_openaire,
    "re3data": search_re3data,
    "osf": search_osf,
}


def slugify(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return text[:80] or "query"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Search query.")
    parser.add_argument("--limit", type=int, default=5, help="Maximum results per platform, between 1 and 50.")
    parser.add_argument(
        "--platform",
        action="append",
        choices=sorted(DEFAULT_PLATFORMS),
        help="Platform to query. Repeat to query several. Defaults to all verified platforms.",
    )
    parser.add_argument(
        "--out-dir",
        default="tmp/public-data-sources/discovery",
        help="Directory for the normalized JSON report.",
    )
    parser.add_argument("--no-write", action="store_true", help="Print JSON to stdout instead of writing a file.")
    args = parser.parse_args(argv)
    if args.limit < 1 or args.limit > 50:
        parser.error("--limit must be between 1 and 50")
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    platforms = args.platform or DEFAULT_PLATFORMS
    started = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for platform in platforms:
        try:
            results.extend(SEARCHERS[platform](args.query, args.limit))
        except Exception as exc:  # Keep the discovery pass resilient.
            errors.append({"platform": platform, "error": str(exc)})
        time.sleep(0.2)
    payload = {
        "created_at": started,
        "verified_endpoint_date": VERIFY_DATE,
        "query": args.query,
        "limit_per_platform": args.limit,
        "platforms": platforms,
        "result_count": len(results),
        "error_count": len(errors),
        "results": results,
        "errors": errors,
    }
    if args.no_write:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if not errors else 2
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"discovery-{slugify(args.query)}-{started[:10]}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out_path": str(out_path), "result_count": len(results), "error_count": len(errors)}, ensure_ascii=False))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
