# Runbook — Domain Down / TLS Recovery (Cloudflare Tunnel)

REAL recipe from 2026-07-11 aiautomatedsystems.ca incident. Verified, not theoretical.

## Symptoms
- Site unreachable over HTTPS. `curl -svI https://<domain>/` → TLS handshake failure.
- Origin check `curl -skv https://127.0.0.1:443/` → "TLS alert, internal error (592)".
- NOTE: 592 from curl to 127.0.0.1 is a FALSE SIGNAL if you didn't set SNI. Test with real SNI:
  `curl -sk --resolve <domain>:443:127.0.0.1 https://<domain>/` → expect HTTP 200.

## Root cause (two compounding)
1. Caddy had no cert (ACME http-01 failed: inbound :80 blocked) → aborts origin TLS (592).
2. DNS was a GREY A to ISP IP, bypassing the live cloudflared tunnel → hit broken :443 directly.

## Fix (verified order)
STEP 1 — Origin cert. Add `tls internal` to the Caddy site block in /etc/caddy/Caddyfile
(root-owned; stage at /tmp, run sudo block — interactive pw on this box):
  sudo bash -c 'BAK=/etc/caddy/Caddyfile.bak.$(date +%Y%m%d-%H%M%S); cp /etc/caddy/Caddyfile "$BAK"; cp /tmp/Caddyfile.new /etc/caddy/Caddyfile; caddy validate --config /etc/caddy/Caddyfile; systemctl restart caddy; sleep 3; curl -sk -o /dev/null -w "localhost:443 -> %{http_code}\n" --resolve aiautomatedsystems.ca:443:127.0.0.1 https://aiautomatedsystems.ca/'
STEP 2 — DNS. Delete the GREY A (raw ISP IP) in Cloudflare DNS. Zero Trust → Tunnels → epyc →
Public Hostnames confirms `<domain>` → https://127.0.0.1:443 (noTLSVerify:true). This auto-creates
the ORANGE CNAME. Wait ~5 min.

## Key facts (EPYC box)
- Caddy /usr/bin/caddy v2.11.4 — NO cloudflare DNS module → DNS-01 impossible without xcaddy.
- cloudflared tunnel `epyc` Connected (yyz). Token in `~/.cloudflared/72acc3fd-...json`.
- Caddy cert store: `/var/lib/caddy/.local/share/caddy/certificates/local/` (NOT /root).
- Order: T(tunnel, no token) > B(internal cert) > A(origin cert w/ valid token) > C(router).

## Verify
  curl -svI https://<domain>/   # expect issuer "Cloudflare Inc" + HTTP 200/308
  /home/scott/ai-lab/scripts/tls-status.sh   # 4-line health snapshot
  /home/scott/ai-lab/scripts/tls-watch.sh    # background watcher, notifies on flip

## Guardrails
- Fix cert BEFORE flipping DNS (else tunnel proxies broken backend).
- sudo needs INTERACTIVE pw (no NOPASSWD). Stage at /tmp.
- 9109 token error = missing ACCOUNT "Cloudflare Tunnel:Edit"; tunnel path needs no token anyway.
- After recovery, re-run SEO/RSS/backlink jobs (sitemap ping endpoints deprecated — use Search Console).

## 2026-07-12 addendum — PUBLIC 503 root cause (token-run tunnel)
After NS flipped to Cloudflare and the tunnel CNAME went orange, the site returned 503 even though
the origin (Caddy :443 -> 8020) returned HTTP 200 with real app HTML. Root cause:
- The running tunnel is started with `cloudflared tunnel run --token` (token-run). Token-run tunnels
  IGNORE the local `~/.cloudflared/config-epyc.yml` ingress and use the config pushed from the
  Cloudflare Zero Trust dashboard.
- The dashboard tunnel ingress had been reset to a catch-all `http_status:503` (seen in cloudflared
  log: `Updated to new configuration ... "service":"http_status:503"`).
- Fix is DASHBOARD-SIDE, not on the box: Zero Trust -> Networks -> Tunnels -> epyc -> Public Hostnames
  -> set `aiautomatedsystems.ca` (and www, api) origin to `https://127.0.0.1:443` with
  `noTLSVerify: true`. Save. The 503 clears within ~30s.
- Do NOT try to fix a token-run tunnel's routing by editing config-epyc.yml — it has no effect.

## Note: tls internal cert lifetime
The `tls internal` (Caddy Local Authority) cert is valid 12h and auto-renews. Tunnel uses
noTLSVerify:true, so renewal is seamless — no action. If you ever see a TLS error after 12h,
just `systemctl restart caddy`; it re-issues.
