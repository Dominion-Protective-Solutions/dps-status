# DPS public status

Canonical GitHub home for **https://status.dominionprotectivesolutions.com**.

This is **Dominion Protective Solutions** only (SES Corp dba DPS, CA PPO #122483). Not Ironclad. Not pitetti.co.

## Source of truth

| Surface | Value |
|---|---|
| Repo | `Dominion-Protective-Solutions/dps-status` (this org repo) |
| Pages | Deploy from branch `main`, folder `/` (legacy) |
| Pages custom domain | `status.dominionprotectivesolutions.com` (this `CNAME` file) |
| DNS | Cloudflare zone `dominionprotectivesolutions.com`, DNS-only CNAME → `dominion-protective-solutions.github.io` |
| Personal leftover | `dominion-ceo/dps-status` is **not** the live Pages source. Do not re-enable Pages or re-bind the custom domain there. |

GitHub Pages on a user repo cannot share this custom domain. Keep Pages **off** on `dominion-ceo/dps-status`.

## Honesty

`index.html` is a **frozen 2026-07-17 snapshot**. Automatic 15-minute publishes are not reaching GitHub. Do **not** restore “All systems operational” or “checks every 15 minutes” until a pipeline actually writes new HTML here.

UptimeRobot (or any other monitor) is a separate probe. Do not paste it into this page as live status.

## Operator clicks (GitHub UI)

API already enabled Pages on this repo and bound the custom domain. Confirm in the org UI:

1. **https://github.com/Dominion-Protective-Solutions/dps-status/settings/pages**
   - Source: Deploy from a branch → `main` / `/` (root)
   - Custom domain: `status.dominionprotectivesolutions.com`
   - Enforce HTTPS: on (wait if the cert is still provisioning)
2. Optional later: **Leave fork network** so this repo is not a fork of `dominion-ceo/dps-status`, then **archive** the personal repo. Do not delete it until the live hostname has been green on this org for a while.
3. Do **not** change Ironclad or pitetti.co Pages/DNS.
