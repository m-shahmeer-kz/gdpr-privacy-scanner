# Privacy report (GDPR)

> **Not legal advice.** This report comes from an automated scan. It finds likely personal data and suggests protections; a qualified privacy professional or your DPO should confirm the conclusions.

## Summary

- Scanned 1 file(s), 11 table(s), 64 columns, 15,607 rows (sample of up to 20,000 rows per table). Purpose: training or fine-tuning an AI model.
- Columns with personal data: **25** (Direct identifier: 13, Quasi-identifier: 7, Pseudonymous ID: 5)
- Re-identification check: in `chinook.db::Customer`, 100.0% of records are unique on `City`, `PostalCode` (smallest group: 1).

## Data map

| File / table | Column | Personal data | GDPR | Confidence | Masked example | Suggested action |
|---|---|---|---|---|---|---|
| chinook.db::Customer | `CustomerId` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | * / ** | pseudonymise |
| chinook.db::Customer | `FirstName` | Person name (Direct identifier) | Art. 4(1) identifier | high | L*** / F*** | drop |
| chinook.db::Customer | `LastName` | Person name (Direct identifier) | Art. 4(1) identifier | high | G*** / K*** | drop |
| chinook.db::Customer | `Address` | Postal address (Direct identifier) | Art. 4(1) identifier | high | Av******70 / Th******34 | drop |
| chinook.db::Customer | `City` | City / place (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | medium | Sã******os / St*****rt | drop |
| chinook.db::Customer | `PostalCode` | Postal code (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | high | 12*****00 / 7***4 | drop |
| chinook.db::Customer | `Phone` | Phone number (Direct identifier) | Art. 4(1) identifier | high | +5******55 / +4******22 | drop |
| chinook.db::Customer | `Fax` | Phone number (Direct identifier) | Art. 4(1) identifier | high | +5******66 / +4******55 | drop |
| chinook.db::Customer | `Email` | E-mail address (Direct identifier) | Art. 4(1) identifier | high | l***@e***.br / l***@s***.de | drop |
| chinook.db::Customer | `SupportRepId` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | * | drop |
| chinook.db::Employee | `EmployeeId` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | * | pseudonymise |
| chinook.db::Employee | `LastName` | Person name (Direct identifier) | Art. 4(1) identifier | high | A*** / E*** | drop |
| chinook.db::Employee | `FirstName` | Person name (Direct identifier) | Art. 4(1) identifier | high | A*** / N*** | drop |
| chinook.db::Employee | `ReportsTo` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | * | drop |
| chinook.db::Employee | `BirthDate` | Date of birth (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | high | 19******00 | drop |
| chinook.db::Employee | `Address` | Postal address (Direct identifier) | Art. 4(1) identifier | high | 11******NW / 82******SW | drop |
| chinook.db::Employee | `City` | City / place (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | medium | Ed****on / C*****y | drop |
| chinook.db::Employee | `PostalCode` | Postal code (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | high | T*****1 / T*****3 | drop |
| chinook.db::Employee | `Phone` | Phone number (Direct identifier) | Art. 4(1) identifier | high | +1******82 / +1******43 | drop |
| chinook.db::Employee | `Fax` | Phone number (Direct identifier) | Art. 4(1) identifier | high | +1******57 / +1******22 | drop |
| chinook.db::Employee | `Email` | E-mail address (Direct identifier) | Art. 4(1) identifier | high | a***@c***.com / n***@c***.com | drop |
| chinook.db::Invoice | `CustomerId` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | * / ** | pseudonymise |
| chinook.db::Invoice | `BillingAddress` | Postal address (Direct identifier) | Art. 4(1) identifier | high | Th******34 / Ul******14 | drop |
| chinook.db::Invoice | `BillingCity` | City / place (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | medium | St*****rt / **** | drop |
| chinook.db::Invoice | `BillingPostalCode` | Postal code (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | high | 7***4 / **** | drop |

Why each column was flagged is in `findings.json` (`why`). Confidence: **high** = check digit or strict format verified (or name + values agree); **medium** = column name or value pattern; **low** = column name only.

## Re-identification risk

- `chinook.db::Customer`: quasi-identifiers `City`, `PostalCode` → 59 of 59 records unique (100.0%), 59 in groups smaller than 5.
- `chinook.db::Employee`: quasi-identifiers `BirthDate`, `City`, `PostalCode` → 8 of 8 records unique (100.0%), 8 in groups smaller than 5.
- `chinook.db::Invoice`: quasi-identifiers `BillingCity`, `BillingPostalCode` → 0 of 412 records unique (0.0%), 0 in groups smaller than 5.

Records that are unique on a few ordinary attributes can be singled out and linked to other data (EDPB Guidelines 02/2026 on anonymisation, draft: record isolation and linkage). Removing names alone does not make data anonymous.

## What this means

- The data is **personal data** (Art. 4(1)): the GDPR applies to everything you do with it, including training a model, testing and sharing.
- **AI training**: you need a lawful basis for training; for legitimate interest, the EDPB's three-step test applies (Opinion 28/2024). A model trained on personal data is not automatically anonymous, so drop direct identifiers and special categories the model does not need before training.
- **Pseudonymise or drop** direct identifiers (Art. 25 data protection by design; Art. 32 security). Pseudonymised data is still personal data (Recital 26), but the risk is lower.
- **Record it**: list this dataset, its purpose and retention in your record of processing (Art. 30).

## After pseudonymisation

- Written: `chinook.db`
- Direct identifiers: 13 column(s) before → 0 after (re-scan of the output).
- Special-category columns: 0 before → 0 after.
- `chinook.db::Customer`: records unique on City, PostalCode: 100.0% before → 0.0% after.
- `chinook.db::Employee`: records unique on BirthDate, City, PostalCode: 100.0% before → 0.0% after.
- `chinook.db::Invoice`: records unique on BillingCity, BillingPostalCode: 0.0% before → 0.0% after.
- Pseudonymised columns left in the output: 3 (still personal data).
- Secret key: `.privacy/secret.key`. Keep it away from the data (other folder, restricted access). Anyone with the key and the original data can re-link pseudonyms.
- **This output is pseudonymised, not anonymous**: it is still personal data under the GDPR (Art. 4(5), Recital 26; EDPB Guidelines 01/2025) for anyone who can re-identify people.

## What this tool cannot decide

- Your lawful basis (Art. 6) and, for special categories, the Art. 9(2) exception.
- Whether each field is necessary for the purpose (data minimisation, Art. 5(1)(c)) and how long to keep it.
- Whether the result is anonymous for a specific recipient: that needs a contextual assessment.
- Personal data it cannot see: images, audio, PDFs, scanned documents, and values outside the sample.

_Generated by GDPR Privacy Scanner 1.0.2. Law and guidance checked: 21 Nov 2026. Not legal advice._
