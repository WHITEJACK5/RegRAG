# SahiCredit Finance Pvt Ltd — Retail Credit & Customer Protection Policy

> **SYNTHETIC DOCUMENT — evaluation-corpus only.**
> SahiCredit Finance Pvt Ltd is not a real company. This policy was written for
> the RegRAG corpus (educational project, not legal or financial advice).
> Rules marked `[trace: ...]` must be consistent with the cited RBI document in
> `data/MANIFEST.json`. Rules marked `[internal]` are this (fictional) lender's
> own choices. Rules marked `VERIFY-D3` must be confirmed against the parsed RBI
> PDF before any golden-set question cites them.

| Field | Value |
| --- | --- |
| doc_id | `synthetic_internal_policy` |
| Version | 1.0 |
| Effective date | 2026-11-10 |
| Policy owner | Head — Credit Policy (fictional) |
| Review cycle | Annual, or immediately upon an RBI reissue (see MANIFEST `status`) |
| Contact | compliance@SahiCredit.example (reserved `.example` domain — fictional) |

## 1. Purpose and scope

This policy governs retail lending at SahiCredit Finance Pvt Ltd ("the Company"),
a fictional small non-banking finance company lending to salaried and
self-employed individuals. It covers origination, pricing, servicing,
grievance handling, recovery and asset-classification practice for three
retail products (Section 2). Where this policy is stricter than applicable RBI
directions, the Company adopts the stricter rule by choice. Where this
document is silent, the applicable RBI direction governs. Nothing here
overrides regulation; the register in Section 10 records every place where
internal rules are deliberately tighter than regulatory baselines.

## 2. Products covered

| Code | Product | Purpose | Max ticket size | Tenor | Security |
| --- | --- | --- | --- | --- | --- |
| SC-PL | Personal loan | Consumption, medical, education support | ₹5,00,000 | 12–60 months | Unsecured |
| SC-VL | Vehicle loan | Two- and four-wheeler purchase | ₹10,00,000 | 12–84 months | Hypothecation of vehicle |
| SC-CD | Consumer-durables loan | Appliance/phone/ laptop purchase | ₹2,00,000 | 6–24 months | Hypothecation of goods |

The aggregate borrowing cap across all three products is ₹10,00,000
outstanding per customer. `[internal]`

## 3. Eligibility

1. Age 21 at application and not past 58 at final tenor. `[internal]`
2. Minimum verified net monthly income: ₹25,000 for salaried applicants and
   ₹35,000 for self-employed applicants. `[internal]`
3. **Loan-to-income (LTI):** the sum of EMIs of all active loans of the
   applicant (including loans from other lenders) must not exceed **40%** of
   verified net monthly income. `[internal — deliberately tighter than common
   market practice]`
4. Credit-bureau score floors: **700** for SC-PL and SC-CD; **650** for SC-VL.
   `[internal]`
5. Maximum **two** active loans with the Company at any time. `[internal]`
6. **KYC:** onboarding follows the applicable RBI Know Your Customer
   directions; the Company does not maintain its own document list and relies
   on the direction's official-valid-document framework.
   `[trace: rbi_kyc_2016]`
7. INCOME AND REPAYMENT DATA: all income figures used for LTI must come from
   verified documents (salary slips or audited field checks), never from
   self-declaration alone. `[internal]`
8. Employment stability: salaried applicants need at least 12 months of
   verified employment of which the last 3 months are with the current
   employer; self-employed applicants need 24 months of continuous operation.
   `[internal]`
9. Geography: the Company lends only in districts on its filed service-city
   list (v1: 42 cities across 9 states). Applications from non-listed
   districts are declined, not referred. `[internal]`
10. Negative conduct screen: auto-decline for an active write-off with any
    lender in the last 36 months, more than two cheque/ECS bounces in the
    last 12 months, or a confirmed bureau fraud record. Marginal files
    (score within 20 points of the floor) go to manual underwriting, not
    auto-decline. `[internal — our tighter choice, not a regulatory minimum]`

## 4. Pricing, disclosure and fees

1. Maximum APR: **24%** for SC-PL, **18%** for SC-VL, **26%** for SC-CD.
   The card-rate sheet is filed with this policy and reviewed quarterly.
   `[internal]`
2. **Full disclosure:** every sanction letter states the APR, all recurring
   charges, and the total cost of credit, consistent with the RBI Fair
   Practices Code framework. `[trace: rbi_fair_practices_code]`
3. **No foreclosure or prepayment charges** on any retail product of the
   Company, in whole or in part, however funded. The Company waives charges
   even where the regulatory framework would permit them.
   `[internal — deliberately stricter; VERIFY-D3 the exact exemption conditions]`
4. No charge may be levied that is not in the filed card-rate sheet.
   `[trace: rbi_fair_practices_code]`
5. **Named fee schedule:** every fee the Company may charge is on this list;
   anything not on it is not chargeable. `[trace: rbi_fair_practices_code]`

   | Fee | Amount | When charged |
   | --- | --- | --- |
   | Processing fee | 1.0% of sanctioned amount (min ₹1,000, max ₹5,000) | Once, at sanction; included in APR disclosure |
   | Bounce / ECS return fee | ₹500 per event | Each failed repayment instrument |
   | Late payment penalty | No separate penalty; stated overdue interest applies per the sanction letter | After due date |
   | Statement, foreclosure-request, or document-retrieval fee | Zero | Always |

   As a rule, no fee is charged for complaint filing or for setting up digital
   repayment. Charging a customer to file a complaint is prohibited.

## 5. Digital personal loans (SC-PL digital channel)

1. All digitally sourced SC-PL lending complies with the RBI (Digital Lending)
   Directions, 2025, which consolidate the 2022 digital-lending guidelines.
   `[trace: rbi_digital_lending_2025]`
2. Disbursal and repayment flow directly between the borrower's bank account
   and the Company; neither lending service partners nor recovery agents may
   hold borrower funds. `[trace: rbi_digital_lending_2025]`
3. Consent for data use is explicit, purpose-bound, and data is deleted on
   request after repayment as required by the Directions.
   `[trace: rbi_digital_lending_2025]`
4. **Cooling-off period:** five calendar days from disbursal on loans of seven
   days' tenor or longer, during which the borrower may exit by paying
   principal and proportionate APR without penalty. `[internal — must never be
   shorter than the RBI-mandated minimum; VERIFY-D3 the exact para]`
5. Lending-service partners may join the origination journey but may not
   influence credit decisions; underwriting authority stays with the Company.
   `[trace: rbi_digital_lending_2025]`
6. Every LSP agreement names a responsible officer, audit rights, and a 30-day
   cure period. The Company may terminate an LSP whose originated loans
   breach the internal 60-DPD roll-rate watch-list threshold.
   `[internal]`

## 6. Grievance redressal

1. **Resolution timeline:** every complaint receives either a resolution or a
   reasoned written response within **7 working days** of receipt — irrespective
   of channel (branch, app, phone, letter). `[internal — deliberately stricter]`
2. A Nodal Grievance Officer is listed on the website and in every sanction
   letter; complaints may be sent to compliance@SahiCredit.example or via the
   app's in-message complaint tool. `[internal]`
3. If the internal timeline lapses or the customer is dissatisfied, the
   customer may escalate under the RBI Integrated Ombudsman framework.
   `[trace: rbi_fair_practices_code; VERIFY-D3 exact routing conditions]`
4. Every complaint and its TAT is logged monthly to the board.
   `[internal]`
5. **Acknowledgement within 1 working day:** every complaint gets a tracking
   reference and a named owner within one working day of receipt.
   `[internal — deliberately tighter than any framework baseline]`
6. **Category discipline:** complaints are logged by category (disclosure,
   pricing, collection conduct, digital channel, data, other). A conduct
   complaint is never re-logged as a service complaint; monthly board
   reporting is by category. `[internal]`

## 7. Collections and recovery conduct

1. Borrower contact is permitted only between 08:00 and 19:00 local time,
   except with the borrower's explicit consent. `[trace: rbi_fair_practices_code;
   VERIFY-D3 exact window]`
2. Recovery staff identify themselves, their employer, and the purpose of
   every contact, and may contact family or employer only with the borrower's
   documented consent. `[trace: rbi_fair_practices_code]`
3. Harassment, intimidation, public shaming, or threats of criminal action are
   prohibited and are a dismissal-level offence. `[trace: rbi_fair_practices_code]`
4. **Repossession (SC-VL and SC-CD only):** repossession is a last resort
   attempted only after at least 21 days' written notice; personal belongings
   found in a repossessed vehicle are inventoried and returned; repossession
   visits follow the same 08:00–19:00 conduct window as collections.
   `[internal — the 21-day notice is deliberately longer than the regulatory
   minimum; VERIFY-D3 the governing instrument and its minimum]`

## 8. Asset classification and early warning

1. Regulatory asset classification follows the RBI prudential norms for
   advances; a retail account is a non-performing asset at **90 days past
   due**. `[trace: rbi_iracp_2025]`
2. **Internal watch-list:** any account at **60 days past due** is flagged
   Code-W before it is an NPA: restricted from further credit, re-underwritten,
   and assigned a recovery plan. `[internal — deliberately stricter]`
3. Provisioning follows RBI norms; the Company additionally holds a 0.5%
   management buffer on all watch-listed balances. `[internal]`

## 9. Records and privacy

1. KYC records are retained per the RBI KYC direction's retention rules;
   applicant data is minimised to what underwriting needs.
   `[trace: rbi_kyc_2016]`
2. Repayment history is reported accurately and disputes are corrected within
   the timelines that apply to credit institutions. `[VERIFY-D3 which instrument
   governs credit-information reporting before this line is cited]`

## 10. Deliberately-stricter register

| # | Rule | Internal | Regulatory baseline | RBI doc | Relation |
| --- | --- | --- | --- | --- | --- |
| 1 | Grievance resolution TAT | 7 working days | Framework-mandated timeline (VERIFY-D3 exact TAT) | rbi_fair_practices_code | stricter |
| 2 | LTI cap | 40% of verified income | No universal RBI LTI number for unsecured retail (VERIFY-D3 situational limits) | — | internal-only |
| 3 | NPA watch-list | flag at 60 DPD | NPA at 90 DPD | rbi_iracp_2025 | stricter |
| 4 | Foreclosure charges | always zero | Charges permitted in defined conditions (VERIFY-D3) | rbi_fair_practices_code | stricter |
| 5 | Digital cooling-off | 5 calendar days | RBI minimum (VERIFY-D3 exact days) | rbi_digital_lending_2025 | stricter |
| 6 | Ticket caps | ₹10L aggregate | No general cap for retail NBFC lending (VERIFY-D3 any category limits) | — | internal-only |

**Version note:** this is v1.0 for the RegRAG corpus. The numerical values
in Sections 2–8 were reviewed and accepted by the policy owner on
2026-11-10 (recorded in `docs/DECISIONS.md`). The regulation changes;
before citing any rule in an answer, check `data/MANIFEST.json` `status` and
`effective_date`. A superseded rule quoted confidently is a real failure mode.