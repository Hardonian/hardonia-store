# Reference catalog.py — Copy to /mnt/ai-storage/ai-workspace/repos/ai-lab-audit-api/app/catalog.py
# All price_ids and payment_links must be LIVE Stripe values

from dataclasses import dataclass


@dataclass(frozen=True)
class Offer:
    sku: str
    name: str
    price_usd: int
    payment_link: str
    price_id: str = ""  # real Stripe price_ id; enables Checkout Session creation


OFFERS: dict[str, Offer] = {
    # Core audit services
    "automated-report": Offer(
        sku="automated-report",
        name="Automated AI Lab Report",
        price_usd=49,
        payment_link="https://buy.stripe.com/00w28qdDW7lW34CgP7b3q0D",
    ),
    "hands-on-audit": Offer(
        sku="hands-on-audit",
        name="Hands-on AI Lab Audit",
        price_usd=297,
        payment_link="https://buy.stripe.com/7sYaEW9nG6hSdJggP7b3q0i",
    ),
    "done-with-you": Offer(
        sku="done-with-you",
        name="Done-with-you Command Center Setup",
        price_usd=997,
        payment_link="https://buy.stripe.com/9B68wO57qbCc7kSeGZb3q0j",
    ),

    # Agent Skin Packs (one-time)
    "skin-neon-sovereign": Offer(
        sku="skin-neon-sovereign",
        name="Neon Sovereign — Agent Skin Pack",
        price_usd=19,
        payment_link="https://buy.stripe.com/3cI9ASfM4dKk7kS7exb3q2c",
        price_id="price_1U1cCLC651G6xmqGTZZCMFbV",
    ),
    "skin-heritage-quiet": Offer(
        sku="skin-heritage-quiet",
        name="Heritage Quiet — Agent Skin Pack",
        price_usd=19,
        payment_link="https://buy.stripe.com/00w28q1VecGgcFc9mFb3q2d",
        price_id="price_1U1cCLC651G6xmqG4ulsQBFs",
    ),

    # LoRA Packs (one-time)
    "lora-neon-line-art": Offer(
        sku="lora-neon-line-art",
        name="Neon Line Art — ComfyUI LoRA Pack",
        price_usd=19,
        payment_link="https://buy.stripe.com/fZu14meI0bCc6gOcyRb3q2g",
        price_id="price_1U1cCNC651G6xmqG14Lgl6ol",
    ),

    # Digital assets (one-time)
    "prompt-pack-agent-ops": Offer(
        sku="prompt-pack-agent-ops",
        name="Agent Ops Prompt Pack",
        price_usd=9,
        payment_link="https://buy.stripe.com/cNiaEW0Ra9u434C42lb3q2h",
        price_id="price_1U1cmhC651G6xmqGkJGSUPZk",
    ),
    "sop-incident-response": Offer(
        sku="sop-incident-response",
        name="AI Incident Response SOP",
        price_usd=19,
        payment_link="https://buy.stripe.com/fZucN4czS6hSbB8gP7b3q2i",
        price_id="price_1U1cmiC651G6xmqGrOwatXJV",
    ),
    "checklist-model-launch": Offer(
        sku="checklist-model-launch",
        name="Model Launch Checklist",
        price_usd=9,
        payment_link="https://buy.stripe.com/fZu6oG7fyay88oWcyRb3q2j",
        price_id="price_1U1cmjC651G6xmqGaMEdj47d",
    ),
    "template-rfp-response": Offer(
        sku="template-rfp-response",
        name="Sovereign RFP Response Template",
        price_usd=19,
        payment_link="https://buy.stripe.com/7sY7sK8jC35G34CdCVb3q2k",
        price_id="price_1U1cmkC651G6xmqG950LBvmR",
    ),
    "prompt-pack-comfyui": Offer(
        sku="prompt-pack-comfyui",
        name="ComfyUI Workflow Prompt Pack",
        price_usd=9,
        payment_link="https://buy.stripe.com/4gM7sKeI00XyeNk42lb3q2l",
        price_id="price_1U1cmlC651G6xmqG55UnTq0h",
    ),
    "checklist-stripe-setup": Offer(
        sku="checklist-stripe-setup",
        name="Stripe sovereign setup checklist",
        price_usd=9,
        payment_link="https://buy.stripe.com/dRm3cu8jC21Cax442lb3q2m",
        price_id="price_1U1cmlC651G6xmqG8cCINKe5",
    ),

    # NEW: Recurring subscriptions (factory-backed)
    "skin-subscription-monthly": Offer(
        sku="skin-subscription-monthly",
        name="Agent Skin Subscription — Monthly",
        price_usd=12,
        payment_link="https://buy.stripe.com/8x2fZggQ849KbB86atb3q2o",
        price_id="price_1U1qBzC651G6xmqG0lD35TCR",
    ),
    "lora-subscription-monthly": Offer(
        sku="lora-subscription-monthly",
        name="LoRA Style Drop — Monthly",
        price_usd=15,
        payment_link="https://buy.stripe.com/eVqcN4gQ8gWwfRo9mFb3q2p",
        price_id="price_1U1qC0C651G6xmqGOeTIdvl5",
    ),
    "comfyui-workflow-subscription": Offer(
        sku="comfyui-workflow-subscription",
        name="ComfyUI Workflow of the Month",
        price_usd=9,
        payment_link="https://buy.stripe.com/cNi5kC57q8q09t0aqJb3q2q",
        price_id="price_1U1qC0C651G6xmqG4f13WaHW",
    ),
    "gpu-spend-guard": Offer(
        sku="gpu-spend-guard",
        name="GPU Spend Guard",
        price_usd=19,
        payment_link="https://buy.stripe.com/28E3cu43m49K20ydCVb3q2r",
        price_id="price_1U1qC0C651G6xmqGxV9Lugic",
    ),
    "sovereign-ops-score": Offer(
        sku="sovereign-ops-score",
        name="Sovereign Ops Score API",
        price_usd=29,
        payment_link="https://buy.stripe.com/eVq4gyfM4dKk48G2Yhb3q2s",
        price_id="price_1U1qC0C651G6xmqGkAa5F2OV",
    ),
    "agent-ops-concierge": Offer(
        sku="agent-ops-concierge",
        name="Agent Ops Concierge",
        price_usd=99,
        payment_link="https://buy.stripe.com/7sYdR88jC6hS34CbuNb3q2t",
        price_id="price_1U1qC0C651G6xmqGH1LDXXfO",
    ),

    # NEW: One-time digital products & services
    "private-ai-readiness": Offer(
        sku="private-ai-readiness",
        name="Private AI Readiness Audit",
        price_usd=149,
        payment_link="https://buy.stripe.com/cNi5kC57q0Xy5cKgP7b3q2u",
        price_id="price_1U1qC1C651G6xmqGYI1JdwCf",
    ),
    "checklist-stripe-setup-video": Offer(
        sku="checklist-stripe-setup-video",
        name="Stripe Sovereign Setup Checklist + Video Walkthrough",
        price_usd=29,
        payment_link="https://buy.stripe.com/3cI7sK43m21CcFceGZb3q2v",
        price_id="price_1U1qC1C651G6xmqGHdytYV6N",
    ),
    "sovereign-starter-bundle-v2": Offer(
        sku="sovereign-starter-bundle-v2",
        name="Sovereign Starter Bundle (Refreshed)",
        price_usd=39,
        payment_link="https://buy.stripe.com/fZu7sKgQ88q08oWcyRb3q2w",
        price_id="price_1U1qC1C651G6xmqG6FEWXsI8",
    ),
    "comfyui-node-of-month": Offer(
        sku="comfyui-node-of-month",
        name="ComfyUI Node of the Month",
        price_usd=19,
        payment_link="https://buy.stripe.com/cNi5kC1Ve49KfRoaqJb3q2x",
        price_id="price_1U1qC1C651G6xmqGJje9qrCi",
    ),
}


def public_catalog() -> dict[str, dict[str, str | int]]:
    return {
        sku: {"name": offer.name, "price_usd": offer.price_usd}
        for sku, offer in OFFERS.items()
    }


# === CHECKOUT ENDPOINT USAGE ===
# POST /api/checkout with form data: sku=your-sku&email=user@example.com
# Returns 303 redirect to Stripe Payment Link
# Webhook at /webhook/stripe handles fulfillment


# === WEBHOOK SIGNATURE VERIFICATION ===
# import stripe, os
# event = stripe.Webhook.construct_event(
#     payload=request.body,
#     sig_header=request.headers.get("stripe-signature"),
#     secret=os.getenv("STRIPE_WEBHOOK_SECRET")
# )
# if event.type == "checkout.session.completed":
#     session = event.data.object
#     sku = session.metadata.get("sku")
#     # Fulfill based on sku