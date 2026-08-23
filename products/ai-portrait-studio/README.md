# AI Portrait Studio
Private ComfyUI execution. Buyer submits reference + notes → runs on your V100 → delivers results.

- Price: $19
- Delivery: <24h via email/download
- Privacy: no data leaves your Ontario server
- Queue: n8n + ComfyUI API

## Buyer provides
- 1 reference photo
- prompt notes / style preference
- output count / size

## Operator workflow
1. n8n receives webhook/email from Gumroad/Formspree
2. saves input to `the delivered buyer archive`
3. posts workflow to `the configured service endpoint`
4. polls `/history` until complete
5. emails results from `the delivered buyer archive`

## Sellable micro-offers
- Starter Pack — 5 images — $19
- Pro Pack — 12 images + 2 style variants — $49
- Headshot Pack — 8 images, fixed style — $29

## Files
- `templates/job.json` — canonical job shape
- `workflows/portrait-base.json` — ComfyUI workflow skeleton
- `assets/sample-prompt-1.txt` — starter prompt

**Price:** $19–$49
