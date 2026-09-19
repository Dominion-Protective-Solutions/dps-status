# DPS public status

Canonical GitHub home for **https://status.dominionprotectivesolutions.com**.

This is **Dominion Protective Solutions** only (SES Corp dba DPS, **CA PPO #122483** — company license, not a personal credential). Not Ironclad. Not pitetti.co. Not product docs.

## Source of truth

| Surface | Value |
|---|---|
| Repo | `Dominion-Protective-Solutions/dps-status` (this org repo) |
| Pages | Deploy from branch `main`, folder `/` (legacy). Do **not** switch to `/docs`. |
| Pages custom domain | `status.dominionprotectivesolutions.com` (this `CNAME` file) |
| DNS | Cloudflare zone `dominionprotectivesolutions.com`, DNS-only CNAME → `dominion-protective-solutions.github.io` |
| Personal leftover | `dominion-ceo/dps-status` is **not** SoT. Do not re-enable Pages or re-bind the custom domain there. |

GitHub Pages on a user repo cannot share this custom domain. Keep Pages **off** on `dominion-ceo/dps-status`.

## Why publishes stopped (2026-07-17 → 2026-09-19)

There was **no** probe workflow on this repo. The only Actions job was GitHub’s built-in Pages build. Last real content commit was a hand-pushed `index.html` on **2026-07-17 12:41 UTC** that claimed “checks every 15 minutes.” Nothing on GitHub was scheduled, so nothing republished. Default `GITHUB_TOKEN` workflow permission is **read**; the publisher now requests `contents: write` on `main` so it can commit the snapshot.

GitHub scheduled workflows only fire on the **default branch**. This repo is still a fork of `dominion-ceo/dps-status`; if the 15-minute cron stays silent, enable the “Publish status” workflow in the Actions tab and/or leave the fork network. Do not claim a 15-minute feed unless `Last published` keeps moving.

## What is checked

Only in-service DPS public hosts (`checks.json`):

| Row | URL | Up means |
|---|---|---|
| Website | https://dominionprotectivesolutions.com/ | HTTP 200 |
| Nexus CRM | https://crm.dominionprotectivesolutions.com/ | HTTP 200/3xx, or 401 with an auth challenge |
| OpenSign | https://sign.dominionprotectivesolutions.com/ | HTTP 200/3xx |

Wildcard phantoms (`docs.`, `portal.`, `ops.`, `maps.`, `dl.`, …) are **not** products and are not probed. Down is down — the page must not paint OpenSign green while HTTPS returns 404.

UptimeRobot (or any other monitor) is a separate probe. Do not paste it into this page as live status.

## Publish path

1. `.github/workflows/publish.yml` runs on `main` (schedule `*/15 * * * *`, `workflow_dispatch`, or a push that changes the probe).
2. `scripts/probe.py` writes `index.html` + `status.json`.
3. The job commits those files to `main`. Pages builds from `main` `/`.

```bash
python3 -m unittest discover -s scripts -p 'test_*.py' -v
python3 scripts/probe.py
```

## Operator clicks (GitHub UI)

API already enabled Pages on this repo and bound the custom domain. Confirm in the org UI:

1. **https://github.com/Dominion-Protective-Solutions/dps-status/settings/pages**
   - Source: Deploy from a branch → `main` / `/` (root)
   - Custom domain: `status.dominionprotectivesolutions.com`
   - Enforce HTTPS: on (wait if the cert is still provisioning)
2. Optional later: **Leave fork network** so this repo is not a fork of `dominion-ceo/dps-status`, then **archive** the personal repo. Do not delete it until the live hostname has been green on this org for a while.
3. Do **not** change Ironclad or pitetti.co Pages/DNS.
