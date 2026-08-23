# Example finding format

## Finding: Checkout completion path lacks a buyer-visible delivery confirmation

- Severity: High
- Evidence: Checkout session completes, but the completion URL returns a non-success response or no fulfillment action.
- Customer impact: A paid buyer may not receive their product or know how to recover it.
- Recommended fix: Restore the canonical completion route, verify webhook signature handling, and add an idempotent signed-download or claim-path test.
- Verification: Run an isolated signed webhook self-test and browser-check the buyer completion route.
- Rollback: Revert the scoped route/configuration change and retain the prior release artifact.

This is an illustrative format, not a claim about your system.
