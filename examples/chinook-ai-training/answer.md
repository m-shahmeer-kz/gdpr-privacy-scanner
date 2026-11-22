# Real run: a fresh AI agent used the skill on the Chinook database

The user (role-played): *"We're a small online music shop based in Italy. We want to fine-tune an AI model on our customer and sales
database (data/chinook.db) to predict what customers will buy next. Is there personal data in it, what's risky under GDPR, and can you
make a safe copy for training? We still need to link customers to their invoices."*

The agent had only the skill (v1.0.2) and the database, and nobody to answer questions. This is its answer (content unchanged; bullet layout condensed):

---

**Not legal advice** — an automated scan plus my review; please have your DPO or a privacy professional confirm.

**Assumptions (you weren't available):** purpose = AI training; the only link needed is customer → invoice → invoice lines; the model doesn't need customer contact details, location, or staff data. No source code was checked (the project contains only the database).

## What I found
- 1 file / 11 tables / 64 columns scanned (15,607 rows; every row read — the 20,000-row sample limit was never reached).
- Personal data in **34 columns** (the scanner flagged 25; I added 9 it missed on review): 13 direct identifiers (customer and staff first/last names, home and billing addresses, phones, faxes, e-mails), 16 quasi-identifiers (City, PostalCode, staff BirthDate from the scan; I added customer Company — 10 values, each unique to one customer — State/Country, BillingState/BillingCountry, staff Title and HireDate), and 5 linking IDs (CustomerId in Customer and Invoice, SupportRepId, EmployeeId, ReportsTo).
- **Special categories (Art. 9)**: none found. **Children's data**: none found (no age field to check).
- Re-identification: Customer — 100% of the 59 customers unique on City + PostalCode; Country alone singles out 25% (15 countries have just one customer). Employee — all 8 staff unique. Invoice — the scanner reports 0% unique, but that's misleading: each customer has 6–7 invoices, every billing-location group belongs to exactly one customer, and the billing address matched the home address on all 412 invoices.
- Artist / track / composer names are catalogue data about musicians, not about your customers — left as is.

## Biggest risks
1. Names, e-mails, phones and addresses would go into a model that doesn't need them — breaks data minimisation (Art. 5(1)(c)) and data protection by design (Art. 25).
2. Location fields single out customers even without names (Recital 26) — removing names alone isn't enough.
3. Purchase histories are still personal data once linked to a customer ID; a model trained on them isn't automatically anonymous and could memorise individual histories (EDPB Opinion 28/2024).
4. Staff data (names, birth dates, addresses) is irrelevant to predicting purchases and shouldn't be in the training set.

## What I did
- Plan: **dropped** all names, addresses, phones, faxes, e-mails, Company, City, State, Country, PostalCode, all Billing* fields, SupportRepId, and the whole staff (Employee) table; **pseudonymised** CustomerId in Customer and Invoice (keyed HMAC-SHA256, same key, so the link is kept — verified: all 412 invoices and 2,240 invoice lines still join to their 59 customers, invoice counts per customer unchanged); kept invoice dates, totals, tracks, genres and prices for the model.
- Result (re-scan of the output): direct identifiers 13 → 0 columns; quasi-identifiers 16 → 0; records unique on quasi-identifiers 100% → 0%. Two pseudonymised ID columns remain.
- Your original database was not changed.
- Secret key: `.privacy/secret.key` — move it somewhere separate (e.g. a password manager with restricted access). The output is **pseudonymised, not anonymous** — it is still personal data under the GDPR.

## What only you can decide
- Your lawful basis (Art. 6) for training a model on purchase history — if legitimate interest, run the three-step test and tell customers in your privacy notice. No Art. 9(2) exception is needed (no special categories).
- Whether the model needs Country (if so, I'd add it back as a broad region, not the exact country).
- How long to keep the training copy and the key, and who can see them; add this processing to your record (Art. 30) and consider a short DPIA (Art. 35), since this is customer profiling.
- If you fine-tune through an external AI provider: a processor contract (Art. 28) and, if outside the EEA, transfer safeguards.

_Not legal advice._
