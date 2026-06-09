# HONEIA Website Operations Playbook v1

## Scope
- Production site: `https://honeia-lab.uk/`
- Supporting pages:
  - `/multi-agent-ops-map.html`
  - `/agent-ops-console.html`
  - `/hermes-window.html`

## Delivery model
- Repository: `honeia85/chatmyPT`
- Host: Cloudflare Pages
- Production branch: `main`
- Custom domain: `honeia-lab.uk`

## Recommended workflow
1. Create a work branch: `feature/*`, `fix/*`, or `ops/*`
2. Make the change
3. Verify on preview or `*.pages.dev`
4. Merge/push to `main`
5. Verify on `honeia-lab.uk`

## Roles
- `default`: decides scope/priorities and reports back to the user
- `ops`: checks deploy, domain, Cloudflare, and runtime health
- `dev`: changes repo files, tests, branches, and pushes

## Release checklist
- `https://honeia-lab.uk/` opens
- `Ops Map` opens
- `Ops Console` opens
- main navigation still shows expected links
- runtime-backed surfaces show generated snapshot/provenance metadata rather than generic `fixture` wording when `/data/runtime-state-v0.json` and `/data/agent-ops-console-runtime.json` are present
- runtime-backed surfaces distinguish bridge payload generation time from upstream runtime snapshot time when `/data/agent-ops-console-runtime.json` is present
- when `/data/runtime-state-v0.json` is newer than the bridge payload's embedded runtime timestamp, top-level runtime pills prefer the fresher standalone snapshot and explicitly show that the bridge view may lag until the next bridge export
- `Ops Map` shows bridge reconciliation counts plus any `shell-only` / `bridge-only` gaps when the runtime bridge payload is present
- `Ops Console` summary distinguishes runtime-backed, runtime-only, overlay, and conceptual-shell counts so transitional fixture dependence remains visible
- `Ops Console` detail/runtime panes surface bridge-shell vs standalone runtime-profile classification plus any shell-classification drift when `/data/runtime-state-v0.json` is present
- custom domain remains active in Cloudflare Pages

## Incident shortcuts
### Pages works, custom domain fails
Check:
- DNS records
- Pages custom domain status
- SSL/TLS issuance state

### Neither Pages nor custom domain works
Check:
- recent repo changes
- Pages deploy/build status
- missing files or broken paths

### One subpage fails
Check:
- file exists in repo
- link path is correct
- extensionless rewrite behavior

## GitHub operating notes
- Git remote push is configured and working
- branch pushes are possible
- `gh` CLI is installed on this machine (`gh version 2.93.0` verified 2026-06-06)
- `gh auth status` is currently healthy for account `honeia85`
- therefore code fix + branch push + draft PR creation/update are all available from this host when needed
- still treat production as unchanged until custom-domain verification passes after merge/deploy
