#!/usr/bin/env bash
# linear-mirror.sh — GitHub issue mirror for Linear (SSOT)
#
# Three operations:
#   mirror       Create GitHub issue + attach to Linear issue
#   close        Close the GitHub mirror of a Linear issue
#   link         Link an existing URL to a Linear issue (github-issue | github-pr | url | slack)
#
# Auth: reads LINEAR_API_TOKEN or ~/.linearis/token, plus GH_TOKEN or gh CLI auth

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# --- Resolve tokens ---
get_linear_token() {
  if [[ -n "${LINEAR_API_TOKEN:-}" ]]; then echo "$LINEAR_API_TOKEN"
  elif [[ -f "$HOME/.linearis/token" ]]; then cat "$HOME/.linearis/token"
  else echo "ERROR: No Linear token. Set LINEAR_API_TOKEN or run 'linearis auth login'." >&2; exit 1
  fi
}

# --- Resolve Linear issue ID (supports both TA-123 and UUID) ---
resolve_issue_id() {
  local input="$1"
  if [[ "$input" =~ ^[0-9a-f]{8}-[0-9a-f]{4}- ]]; then echo "$input"  # already UUID
  else
    # Convert TA-123 to UUID via linearis
    local result
    result=$(linearis issues read "$input" 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])" 2>/dev/null)
    if [[ -z "$result" || "$result" == "null" ]]; then
      echo "ERROR: Could not resolve issue: $input" >&2; exit 1
    fi
    echo "$result"
  fi
}

# --- GraphQL call ---
graphql() {
  local token query
  token="$(get_linear_token)"
  query="$1"
  curl -s -X POST https://api.linear.app/graphql \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d "$(python3 -c "import json; print(json.dumps({'query': '''$query'''}))")"
}

# ================================================================
# OPERATION: mirror — Create GitHub issue + attach to Linear
# ================================================================
cmd_mirror() {
  local linear_issue repo title body labels
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --issue)  linear_issue="$2"; shift 2 ;;
      --repo)   repo="$2"; shift 2 ;;
      --title)  title="$2"; shift 2 ;;
      --body)   body="$2"; shift 2 ;;
      --labels) labels="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "${linear_issue:-}" || -z "${repo:-}" || -z "${title:-}" ]]; then
    cat <<'HELP'
Usage: linear-mirror.sh mirror --issue <TA-xxx> --repo <owner/repo> --title <title> [--body <markdown>] [--labels <label1,label2>]

Creates a GitHub issue in the given repo, then attaches it to the Linear issue.
HELP
    exit 1
  fi

  echo "Creating GitHub issue in $repo..."

  # Build gh issue create command
  local gh_args=("issue" "create" "--repo" "$repo" "--title" "$title")
  [[ -n "${body:-}" ]] && gh_args+=("--body" "$body")
  [[ -n "${labels:-}" ]] && gh_args+=("--label" "$labels")

  local gh_url
  gh_url=$(gh "${gh_args[@]}" 2>&1)
  echo "  GitHub: $gh_url"

  # Attach to Linear
  echo "Attaching to Linear issue $linear_issue..."
  local linear_uuid
  linear_uuid=$(resolve_issue_id "$linear_issue")

  local gql
  gql="mutation { attachmentLinkGitHubIssue(issueId: \"$linear_uuid\", url: \"$gh_url\") { success attachment { id url } } }"
  local result
  result=$(graphql "$gql")

  if echo "$result" | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if d['data']['attachmentLinkGitHubIssue']['success'] else 1)" 2>/dev/null; then
    echo "  Linked: $gh_url -> $linear_issue"
  else
    echo "  WARNING: GitHub issue created but link to Linear failed" >&2
    echo "  $gh_url" >&2
  fi
}

# ================================================================
# OPERATION: close — Close the GitHub mirror of a Linear issue
# ================================================================
cmd_close() {
  local linear_issue
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --issue) linear_issue="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "${linear_issue:-}" ]]; then
    echo "Usage: linear-mirror.sh close --issue <TA-xxx>"
    exit 1
  fi

  local linear_uuid
  linear_uuid=$(resolve_issue_id "$linear_issue")

  # Find GitHub attachments on this Linear issue
  local gh_url
  gh_url=$(graphql "{ issue(id: \"$linear_uuid\") { attachments { nodes { url sourceType } } } }" | \
    python3 -c "
import json, sys
d = json.load(sys.stdin)
for att in d.get('data',{}).get('issue',{}).get('attachments',{}).get('nodes',[]):
    if att.get('sourceType') == 'github' and 'github.com' in att.get('url','') and '/issues/' in att.get('url',''):
        print(att['url'])
        break
" 2>/dev/null)

  if [[ -z "$gh_url" ]]; then
    echo "No GitHub issue mirror found for $linear_issue"
    exit 0
  fi

  # Extract owner/repo/issue_number from URL
  # e.g. https://github.com/SiyaoZheng/scientificity/issues/15
  local repo issue_num
  repo=$(echo "$gh_url" | sed -n 's|https://github.com/\([^/]*/[^/]*\)/issues/.*|\1|p')
  issue_num=$(echo "$gh_url" | sed -n 's|.*/issues/\([0-9]*\).*|\1|p')

  if [[ -z "$repo" || -z "$issue_num" ]]; then
    echo "Could not parse GitHub URL: $gh_url"
    exit 1
  fi

  echo "Closing GitHub issue $repo#$issue_num..."
  gh issue close "$issue_num" --repo "$repo" -c "Closed: Linear issue $linear_issue was completed."
  echo "  Closed: $gh_url"
}

# ================================================================
# OPERATION: link — Attach an existing URL to a Linear issue
# ================================================================
cmd_link() {
  local link_type issue_id url title
  link_type="${1:-}"; shift 2>/dev/null || true

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --issue) issue_id="$2"; shift 2 ;;
      --url)   url="$2"; shift 2 ;;
      --title) title="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$link_type" || -z "${issue_id:-}" || -z "${url:-}" ]]; then
    cat <<'HELP'
Usage: linear-mirror.sh link <type> --issue <TA-xxx> --url <url> [--title <title>]

Types: github-issue | github-pr | url | slack
HELP
    exit 1
  fi

  local mutation
  case "$link_type" in
    github-issue) mutation="attachmentLinkGitHubIssue" ;;
    github-pr)    mutation="attachmentLinkGitHubPR" ;;
    url)          mutation="attachmentLinkURL" ;;
    slack)        mutation="attachmentLinkSlack" ;;
    *) echo "Unknown: $link_type"; exit 1 ;;
  esac

  local title_json="null"
  [[ -n "${title:-}" ]] && title_json="\"$(echo "$title" | sed 's/\\/\\\\/g; s/"/\\"/g')\""

  local linear_uuid gql result
  linear_uuid=$(resolve_issue_id "$issue_id")
  gql="mutation { ${mutation}(issueId: \"$linear_uuid\", url: \"$url\", title: $title_json) { success attachment { id url sourceType } } }"
  result=$(graphql "$gql")

  if echo "$result" | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if d['data']['${mutation}']['success'] else 1)" 2>/dev/null; then
    local att_info
    att_info=$(echo "$result" | python3 -c "import json,sys; a=json.load(sys.stdin)['data']['${mutation}']['attachment']; print(f\"{a['url']} ({a['sourceType']})\")")
    echo "  Linked: $att_info -> $issue_id"
  else
    echo "  Failed to link" >&2
    echo "$result" | python3 -m json.tool >&2
    exit 1
  fi
}

# ================================================================
# Main
# ================================================================
OPERATION="${1:-}"; shift 2>/dev/null || true

case "$OPERATION" in
  mirror) cmd_mirror "$@" ;;
  close)  cmd_close "$@" ;;
  link)   cmd_link "$@" ;;
  *)
    cat <<'HELP'
Usage: linear-mirror.sh <operation> [options]

Operations:
  mirror    Create GitHub issue + attach to Linear issue
  close     Close the GitHub mirror of a Linear issue
  link      Link an existing URL to a Linear issue

Examples:
  # Create a GitHub mirror for a new Linear issue
  linear-mirror.sh mirror --issue TA-83 --repo SiyaoZheng/scientificity \
    --title "Fix filter_non_papers" --labels "bug"

  # Close the GitHub mirror when Linear issue is done
  linear-mirror.sh close --issue TA-83

  # Link an existing URL
  linear-mirror.sh link github-pr --issue TA-83 --url https://github.com/SiyaoZheng/scientificity/pull/42
HELP
    exit 1
    ;;
esac
