# Agent-Fetchable Data Discovery Platforms

This file is intentionally narrower than a general list of useful research
data websites. Include a platform here only when both conditions are true:

- Official documentation describes a programmatic API or machine-readable
  endpoint.
- A no-secret live probe from this workspace returned machine-readable metadata
  on 2026-07-05.

Do not add browser-only catalogs, login-only portals, or "probably CKAN"
instances without a successful live probe.

## Access Levels

| Level | Meaning | Agent rule |
|---|---|---|
| `file_fetchable_when_public` | Search metadata are no-secret and public records can expose direct file URLs | Search freely; download only when the record exposes an unrestricted file URL and license/terms permit use. |
| `metadata_fetchable` | Search metadata are no-secret, but files are not exposed by default or require a second source-specific check | Use for discovery, DOI routing, repository choice, and source queues; do not treat as acquired data. |

## Verified Platforms

| Platform | Access level | Verified agent path | Returns | File acquisition status | Use when |
|---|---|---|---|---|---|
| Zenodo | `file_fetchable_when_public` | `GET https://zenodo.org/api/records?q={query}&size=10` | JSON records, DOI, landing links, metadata, file entries on public records | Public records often expose file links under `files`; verify license and checksum before download | General open research data, code, supplements, replication artifacts |
| DataCite | `metadata_fetchable` | `GET https://api.datacite.org/dois?query={query}&resource-type-id=Dataset&page[size]=10` | JSON DOI metadata for datasets and research objects | Metadata router only; follow DOI or landing page to source-specific API before acquisition | Cross-repository DOI discovery and repository routing |
| Harvard Dataverse / Dataverse instances | `file_fetchable_when_public` | `GET https://dataverse.harvard.edu/api/search?q={query}&type=dataset&per_page=10` | JSON dataset search metadata, persistent IDs, authors, file counts | Public dataset details can expose unrestricted file IDs; download via Dataverse access API only when `restricted=false` | Social-science replication packages and DOI-backed datasets |
| Figshare | `file_fetchable_when_public` | `POST https://api.figshare.com/v2/articles/search` with JSON body `{"search_for":"{query}","item_type":3,"page_size":10}` | JSON article records; details endpoint exposes public files | Public details can expose `download_url`, size, and MD5 | Datasets and supplementary files hosted on Figshare |
| Dryad | `metadata_fetchable` | `GET https://datadryad.org/api/v2/search?q={query}&per_page=10` | JSON dataset metadata, DOI identifier, API links | Search works without a secret; the tested API download relation returned `401 Unauthorized`, so do not auto-download by default | Discover published research datasets and route to DOI/landing page |
| OpenAIRE Graph Search | `metadata_fetchable` | `GET https://api.openaire.eu/search/researchProducts?keywords={query}&format=json&size=10` | JSON metadata for publications, datasets, software, and projects | Metadata discovery only; it is an aggregator, not a default file source | Broad scholarly graph discovery, publication-data links, repository hints |
| re3data | `metadata_fetchable` | `GET https://www.re3data.org/api/beta/repositories?query={query}` | XML repository records with names, IDs, DOIs, and self links | Repository discovery only; not dataset/file acquisition | Find domain repositories before searching source-specific APIs |
| OSF public API | `metadata_fetchable` | `GET https://api.osf.io/v2/nodes/?filter[title]={query}&page[size]=10` and `GET https://api.osf.io/v2/preprints/?filter[title]={query}&page[size]=10` | JSON API records for public projects, components, preprints, and related metadata | Metadata discovery by default; file acquisition requires following public file relationships and checking access | Project/preprint-to-data discovery and OSF-hosted research-object routing |

## Excluded From The Default Agent List

These may still be useful for human research, but they are not default
agent-fetchable sources until a no-secret machine-readable live probe succeeds:

- `catalog.data.gov` CKAN default endpoints. Live probes of
  `/api/action/package_search`, `/api/3/action/package_search`, and
  `/api/3/action/status_show` returned 404 on 2026-07-05.
- Google Dataset Search. It is a search product, not a documented no-secret
  API for agents.
- Kaggle, ICPSR, UK Data Service, GESIS, CESSDA, QDR, and similar high-value
  repositories when the normal path requires human login, account terms, UI
  interaction, or restricted-use approval.
- Any CKAN instance by name alone. Verify the exact instance endpoint before
  using it.

## Discovery Protocol

1. Search two or more verified platforms with bounded limits.
2. Normalize `platform`, `title`, `identifier`, `doi`, `landing_url`,
   `api_url`, `published`, `creators`, `license`, `access_level`, and
   `files`.
3. Cap file metadata in discovery outputs; use source-specific acquisition code
   when a record contains many files.
4. Mark a result as acquired data only after a direct file URL or source API
   returns a successful no-login response and the license/terms allow use.
5. Preserve source payload snippets or request logs under the project workspace
   when handing off to `research-data-builder`.
6. Treat metadata-only records as source leads, not empirical rows.
