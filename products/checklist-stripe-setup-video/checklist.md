# Stripe Sovereign Setup Checklist
## 40-Step Production Checklist for Self-Hosted Stripe Integration

### Phase 1: Stripe Dashboard Configuration (Steps 1-10)
1. [ ] Create Stripe account → complete business verification
2. [ ] Enable **Test mode** → verify test keys work
3. [ ] Create **Products** in Dashboard (one per SKU)
4. [ ] Create **Prices** for each product:
   - One-time: `recurring=null`
   - Subscriptions: `recurring.interval=month`
   - Set `metadata.sku` = your internal SKU
5. [ ] Create **Payment Links** for each Price:
   - `after_completion.redirect.url` = `https://yourdomain.com/order/success`
   - `metadata.sku` = your internal SKU
6. [ ] Copy **Price IDs** (`price_...`) → paste into `catalog.py`
7. [ ] Copy **Payment Link URLs** (`buy.stripe.com/...`) → paste into `catalog.py`
8. [ ] Set **Webhook endpoint** in Dashboard:
   - URL: `https://yourdomain.com/webhook/stripe`
   - Events: `checkout.session.completed`, `checkout.session.async_payment_succeeded`, `checkout.session.async_payment_failed`, `charge.refunded`, `customer.subscription.*`, `invoice.paid`
9. [ ] Copy **Webhook Signing Secret** (`whsec_...`) → `.env` as `STRIPE_WEBHOOK_SECRET`
10. [ ] Verify webhook receives test events (use Stripe CLI)

### Phase 2: Local Environment (Steps 11-20)
11. [ ] `.env` contains:
    ```
    STRIPE_SECRET_KEY=sk_live_... (or sk_test_...)
    STRIPE_PUBLISHABLE_KEY=pk_live_... (or pk_test_...)
    STRIPE_WEBHOOK_SECRET=whsec_...
    ```
12. [ ] `catalog.py` has all OFFERS with correct `price_id` and `payment_link`
13. [ ] Run `systemctl --user restart ai-lab-audit-api`
14. [ ] Test checkout: `curl -X POST http://127.0.0.1:8011/api/checkout -d 'sku=YOUR_SKU'`
15. [ ] Verify 303 redirect to `buy.stripe.com/...`
16. [ ] Test webhook locally: `stripe listen --forward-to localhost:8011/webhook/stripe`
17. [ ] Complete test payment in Test mode
18. [ ] Verify webhook receives `checkout.session.completed`
19. [ ] Check `commerce_events` table for `status=fulfilled`
20. [ ] Verify deliverable accessible (download/access granted)

### Phase 3: Hardonia Checkout API (Steps 21-30)
21. [ ] `hardonia-checkout-api` `.env` has `STRIPE_SECRET_KEY`
22. [ ] `commerce_catalog` synced: `python scripts/sync_commerce_catalog.py --apply`
23. [ ] Verify `commerce_catalog` rows match Stripe Prices
24. [ ] Webhook endpoint: `https://yourdomain.com/api/v1/webhook/stripe`
25. [ ] Test webhook signature verification
26. [ ] Test `checkout.session.completed` → fulfillment flow
27. [ ] Test `charge.refunded` → revocation flow
28. [ ] Test subscription lifecycle events
29. [ ] Verify `purchases` table populated
30. [ ] Test `/api/v1/fulfillment/claim` with customer email

### Phase 4: Storefront Integration (Steps 31-40)
31. [ ] Storefront `products` table has all SKUs with `checkout_url`
32. [ ] Product pages render: `/p/{slug}`
33. [ ] Checkout forms POST to `/api/checkout` (audit-api) or Stripe directly
34. [ ] Success page: `/order/success` shows fulfillment info
35. [ ] Cancel page: `/order/cancel` handles gracefully
36. [ ] Analytics events firing: `view`, `checkout_start`, `purchase`
37. [ ] Sitemap includes all product pages
38. [ ] SEO metadata: title, description, OG image, JSON-LD Product schema
39. [ ] Mobile responsive: test all product pages
40. [ ] **Go Live**: Switch Test → Live keys, update webhook URLs, test one real $1 payment

---

## Quick Reference: catalog.py Entry Template

```python
"your-sku": Offer(
    sku="your-sku",
    name="Human Readable Name",
    price_usd=29,  # USD cents in Stripe
    payment_link="https://buy.stripe.com/...",
    price_id="price_...",  # from Stripe Dashboard
),
```

## Webhook Signature Verification (Python)

```python
import stripe
event = stripe.Webhook.construct_event(
    payload=request.body,
    sig_header=request.headers.get("stripe-signature"),
    secret=os.getenv("STRIPE_WEBHOOK_SECRET")
)
```

## Test Mode → Live Mode Checklist

- [ ] All test payments refunded/voided
- [ ] `STRIPE_SECRET_KEY=sk_live_...`
- [ ] `STRIPE_PUBLISHABLE_KEY=pk_live_...`
- [ ] `STRIPE_WEBHOOK_SECRET=whsec_live_...`
- [ ] Dashboard webhook URL updated to production domain
- [ ] `catalog.py` price_ids and payment_links are LIVE versions
- [ ] `commerce_catalog` re-synced with live Prices
- [ ] One real $1 test payment end-to-end
- [ ] Fulfillment delivered successfully
- [ ] Webhook logs clean (no signature errors)