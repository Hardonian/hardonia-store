# RFP Response Template — enterprise AI

Structured, section-by-section. Fill the brackets.

## 1. Executive summary
"We propose a sovereign <capability> that runs on your infrastructure, with no
data leaving your network. Fixed scope: <scope>. Outcome: <outcome> in <weeks>."

## 2. Understanding the requirement
- Restate the buyer's problem in their words.
- List the 3 constraints that matter most (compliance, latency, cost).

## 3. Solution architecture
- Local-first deployment (no third-party data egress)
- <component> -> <component> -> <delivery>
- Security: <RLS / secret handling / audit log>

## 4. Implementation plan
| Phase | Weeks | Deliverable |
|-------|-------|-------------|
| 1     | 1-2   | <discovery + scaffold> |
| 2     | 3-5   | <core build> |
| 3     | 6-7   | <hardening + handoff> |

## 5. Compliance & security
- Data residency: on-prem / your VPC
- Access: least-privilege, audited
- Certs relevant: <SOC2 / ISO / HIPAA as applicable>

## 6. Commercials
- Fixed price: <amount>
- Includes: <what is in scope>
- Out of scope: <what is not>

## 7. References
- Similar work: <anonymized example>
- Proof: <live demo / metric>
