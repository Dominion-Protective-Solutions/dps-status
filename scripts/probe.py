#!/usr/bin/env python3
"""Probe in-service DPS public hosts and render GitHub Pages HTML."""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Callable, Mapping

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CHECKS = ROOT / "checks.json"
USER_AGENT = "DPS-status-probe/1.0 (+https://status.dominionprotectivesolutions.com/)"
TIMEOUT_SEC = 15

FetchFn = Callable[[str], dict[str, Any]]

STATE_STYLE = {
    "operational": ("#4ade80", "● Operational"),
    "down": ("#f87171", "● Down"),
    "error": ("#fbbf24", "● Check failed"),
}


def load_checks(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not data.get("checks"):
        raise ValueError("checks.json has no checks")
    return data


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def fmt_utc(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%d %H:%M UTC")


def fetch_url(url: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC, context=ctx) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            resp.read(2048)
            return {
                "status_code": int(resp.status),
                "headers": headers,
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        headers = {k.lower(): v for k, v in (exc.headers.items() if exc.headers else [])}
        try:
            exc.read(2048)
        except Exception:
            pass
        return {
            "status_code": int(exc.code),
            "headers": headers,
            "error": None,
        }
    except Exception as exc:
        return {
            "status_code": None,
            "headers": {},
            "error": f"{type(exc).__name__}: {exc}",
        }


def classify(check: Mapping[str, Any], fetched: Mapping[str, Any]) -> dict[str, Any]:
    name = str(check["name"])
    url = str(check["url"])
    expect = [int(code) for code in check.get("expect", [])]
    note = str(check.get("note") or "")
    auth_ok = bool(check.get("auth_challenge_is_up"))

    if fetched.get("error"):
        return {
            "id": check.get("id"),
            "name": name,
            "url": url,
            "state": "error",
            "http_status": fetched.get("status_code"),
            "detail": str(fetched["error"]),
            "note": note,
        }

    code = fetched.get("status_code")
    headers = fetched.get("headers") or {}
    has_auth = any(k.lower() == "www-authenticate" for k in headers)

    if code in expect:
        detail = f"HTTP {code}"
        if code == 401 and has_auth:
            detail = "HTTP 401 auth challenge"
        return {
            "id": check.get("id"),
            "name": name,
            "url": url,
            "state": "operational",
            "http_status": code,
            "detail": detail,
            "note": note,
        }

    if auth_ok and code == 401 and has_auth:
        return {
            "id": check.get("id"),
            "name": name,
            "url": url,
            "state": "operational",
            "http_status": code,
            "detail": "HTTP 401 auth challenge",
            "note": note,
        }

    detail = f"HTTP {code}" if code is not None else "No HTTP status"
    return {
        "id": check.get("id"),
        "name": name,
        "url": url,
        "state": "down",
        "http_status": code,
        "detail": detail,
        "note": note,
    }


def headline_for(rows: list[dict[str, Any]]) -> tuple[str, str, str]:
    """Return (css_color, headline, banner or empty)."""
    states = [row["state"] for row in rows]
    down_names = [row["name"] for row in rows if row["state"] != "operational"]

    if not states:
        return (
            "#fbbf24",
            "No checks configured",
            "This page has nothing to probe.",
        )
    if all(state == "operational" for state in states):
        return (
            "#4ade80",
            "Checked systems operational",
            "",
        )
    if all(state != "operational" for state in states):
        return (
            "#f87171",
            "All checked systems down",
            "Every probed surface failed this publish.",
        )
    names = ", ".join(down_names)
    return (
        "#fbbf24",
        "Partial outage",
        f"Down this publish: {names}. Other rows are current probe results, not a frozen snapshot.",
    )


def render_html(config: Mapping[str, Any], rows: list[dict[str, Any]], published: datetime) -> str:
    color, headline, banner = headline_for(rows)
    brand = escape(str(config.get("brand") or "Dominion Protective Solutions"))
    license_line = escape(str(config.get("license") or "CA PPO #122483"))
    published_label = escape(fmt_utc(published))
    banner_html = ""
    if banner:
        banner_html = (
            f'<div class="banner">{escape(banner)}</div>\n'
        )

    row_html = []
    for row in rows:
        style, label = STATE_STYLE[row["state"]]
        note_bits = [row["detail"]]
        if row.get("note"):
            note_bits.append(row["note"])
        note = escape(" · ".join(note_bits))
        name = escape(row["name"])
        url = escape(row["url"])
        row_html.append(
            '<div class="row">'
            f'<div class="svc">{name}<div class="note">{url}<br>{note}</div></div>'
            f'<div class="state" style="color:{style}">{label}</div>'
            "</div>"
        )

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{brand} — Status</title>
<style>
body{{margin:0;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;background:#000000;color:#f5f5f4}}
.wrap{{max-width:640px;margin:0 auto;padding:32px 20px}}
.brand{{font-size:14px;letter-spacing:.08em;text-transform:uppercase;color:#d4a853;font-weight:700}}
h1{{font-size:22px;margin:6px 0 2px;color:#f5f5f4}}
.head{{display:flex;align-items:center;gap:10px;margin:18px 0}}
.dot{{width:14px;height:14px;border-radius:50%;background:{color}}}
.headline{{font-size:17px;font-weight:600;color:{color}}}
.banner{{background:#1c1408;border:1px solid #854d0e;border-radius:8px;padding:12px 14px;font-size:14px;margin:14px 0;color:#fde68a}}
.card{{background:#0d0d0d;border:1px solid #2a2a2a;border-radius:10px;overflow:hidden;margin-top:14px}}
.row{{display:flex;justify-content:space-between;align-items:flex-start;padding:14px 16px;border-bottom:1px solid #2a2a2a;gap:12px}}
.row:last-child{{border-bottom:none}}
.svc{{font-size:15px;font-weight:500;min-width:0;flex:1}}
.note{{font-size:12.5px;color:#a8a29e;font-weight:400;margin-top:2px;line-height:1.4;overflow-wrap:anywhere}}
.state{{font-size:13px;font-weight:600;white-space:nowrap;flex-shrink:0}}
footer{{margin-top:22px;font-size:12.5px;color:#a8a29e;line-height:1.5}}
</style></head><body><div class="wrap">
<div class="brand">{brand}</div>
<h1>Service Status</h1>
<div class="head"><div class="dot"></div><div class="headline">{escape(headline)}</div></div>
{banner_html}<div class="card">
{"".join(row_html)}
</div>
<footer>Last published: {published_label}. This timestamp is the last probe that wrote this file on GitHub <code>main</code>. A 15-minute Actions schedule is configured; it only counts if this time keeps moving.<br>
{brand} · {license_line}. Company license only — not a personal credential.</footer>
</div></body></html>
"""


def probe_all(
    config: Mapping[str, Any],
    fetch: FetchFn = fetch_url,
) -> list[dict[str, Any]]:
    return [classify(check, fetch(str(check["url"]))) for check in config["checks"]]


def snapshot(config: Mapping[str, Any], rows: list[dict[str, Any]], published: datetime) -> dict[str, Any]:
    return {
        "brand": config.get("brand"),
        "license": config.get("license"),
        "published_at": published.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "headline": headline_for(rows)[1],
        "checks": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checks", type=Path, default=DEFAULT_CHECKS)
    parser.add_argument("--write-html", type=Path, default=None)
    parser.add_argument("--write-json", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_checks(args.checks)
    published = utc_now()
    rows = probe_all(config)
    html = render_html(config, rows, published)
    data = snapshot(config, rows, published)

    html_path = args.write_html if args.write_html is not None else ROOT / "index.html"
    json_path = args.write_json if args.write_json is not None else ROOT / "status.json"
    html_path.write_text(html, encoding="utf-8")
    json_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    print(f"published_at={data['published_at']}")
    print(f"headline={data['headline']}")
    for row in rows:
        print(f"{row['state']}\t{row['name']}\t{row['detail']}\t{row['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
