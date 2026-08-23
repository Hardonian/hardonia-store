# Stripe Sovereign Setup Checklist

Go live on Stripe without leaking keys or breaking fulfillment.

## Account
- [ ] Live mode activated (not test)
- [ ] Webhook endpoint created (https://stripe-webhook.aiautomatedsystems.ca/webhook/stripe)
- [ ] Webhook secret stored in env (STRIPE_WEBHOOK_SECRET), never in code
- [ ] Webhook signs: checkout.session.completed

## Key safety
- [ ] Secret key in .env, chmod 600, gitignored
- [ ] Rotated key re-linked via key-rotation-relink.py
- [ ] No key in chat, logs, or client bundle

## Checkout
- [ ] Products use Checkout Sessions (cs_live_), not raw Payment Links
- [ ] Success URL points to /audit/complete
- [ ] commerce_catalog.stripe_price_id is a real price_1

## Fulfillment
- [ ] Webhook verifies signature with raw body
- [ ] Fulfillment writes a signed download URL (HMAC, 7-day expiry)
- [ ] Download route serves the real bundle
- [ ] Bad signature returns 400 (verified)

## Compliance
- [ ] /terms /refund /privacy pages live
- [ ] Receipt + download shown on success page
- [ ] Refund policy states digital-goods policy
