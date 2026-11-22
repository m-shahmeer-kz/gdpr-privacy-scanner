# Privacy report (GDPR)

> **Not legal advice.** This report comes from an automated scan. It finds likely personal data and suggests protections; a qualified privacy professional or your DPO should confirm the conclusions.

## Summary

- Scanned 9 file(s), 46 table(s), 325 columns, 748,204 rows (sample of up to 20,000 rows per table). Purpose: training or fine-tuning an AI model.
- Columns with personal data: **98** (Quasi-identifier: 36, Direct identifier: 32, Pseudonymous ID: 22, Special category (Art. 9): 7, Free text with personal data: 1)
- **Special-category or criminal data found in 7 column(s)**: `ChestPain` (Health data), `RestBP` (Health data), `Chol` (Health data), `RestECG` (Health data), `race` (Racial or ethnic origin), `bmi` (Health data), `smoker` (Health data)
- **Children's data likely** (ages under 16): extra care (Art. 8, Recital 38).
- Re-identification check: in `chinook.db::Customer`, 100.0% of records are unique on `City`, `PostalCode` (smallest group: 1).

## Data map

| File / table | Column | Personal data | GDPR | Confidence | Masked example | Suggested action |
|---|---|---|---|---|---|---|
| Heart.csv | `Age` | Age (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | high | ** | generalise |
| Heart.csv | `Sex` | Gender / sex (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | high | * | keep |
| Heart.csv | `ChestPain` | Health data (Special category (Art. 9)) | Art. 9(1): needs an Art. 9(2) exception; DPIA likely (Art. 35(3)(b)) | medium | t*****l / as******ic | drop |
| Heart.csv | `RestBP` | Health data (Special category (Art. 9)) | Art. 9(1): needs an Art. 9(2) exception; DPIA likely (Art. 35(3)(b)) | medium | *** / ** | drop |
| Heart.csv | `Chol` | Health data (Special category (Art. 9)) | Art. 9(1): needs an Art. 9(2) exception; DPIA likely (Art. 35(3)(b)) | medium | *** | drop |
| Heart.csv | `RestECG` | Health data (Special category (Art. 9)) | Art. 9(1): needs an Art. 9(2) exception; DPIA likely (Art. 35(3)(b)) | medium | * | drop |
| Telco-Customer-Churn.csv | `customerID` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | 75******EG / 55******DE | pseudonymise |
| Telco-Customer-Churn.csv | `gender` | Gender / sex (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | high | F****e / **** | keep |
| Telco-Customer-Churn.csv | `SeniorCitizen` | Age (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | high | * | generalise |
| Telco-Customer-Churn.csv | `Partner` | Marital status (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | medium | *** / ** | keep |
| adult.csv | `age` | Age (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | high | ** | generalise |
| adult.csv | `education` | Education (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | low | **** / H*****d | keep |
| adult.csv | `educational-num` | Education (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | low | * / ** | keep |
| adult.csv | `marital-status` | Marital status (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | medium | Ne******ed / Ma******se | keep |
| adult.csv | `occupation` | Occupation / employer (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | low | Ma******ct / Fa******ng | drop |
| adult.csv | `relationship` | Marital status (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | medium | Ow*****ld / H*****d | keep |
| adult.csv | `race` | Racial or ethnic origin (Special category (Art. 9)) | Art. 9(1): needs an Art. 9(2) exception; DPIA likely (Art. 35(3)(b)) | high | B***k / W***e | drop |
| adult.csv | `gender` | Gender / sex (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | high | **** / F****e | keep |
| adult.csv | `capital-gain` | Income / salary (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | low | * / **** | generalise |
| adult.csv | `capital-loss` | Income / salary (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | low | * / **** | generalise |
| adult.csv | `native-country` | Nationality (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | medium | Un******es / **** | drop |
| adult.csv | `income` | Income / salary (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | low | <***K / **** | generalise |
| chinook.db::Customer | `CustomerId` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | * / ** | pseudonymise |
| chinook.db::Customer | `FirstName` | Person name (Direct identifier) | Art. 4(1) identifier | high | L*** / F*** | drop |
| chinook.db::Customer | `LastName` | Person name (Direct identifier) | Art. 4(1) identifier | high | G*** / K*** | drop |
| chinook.db::Customer | `Address` | Postal address (Direct identifier) | Art. 4(1) identifier | high | Av******70 / Th******34 | drop |
| chinook.db::Customer | `City` | City / place (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | medium | Sã******os / St*****rt | drop |
| chinook.db::Customer | `PostalCode` | Postal code (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | high | 12*****00 / 7***4 | drop |
| chinook.db::Customer | `Phone` | Phone number (Direct identifier) | Art. 4(1) identifier | high | +5******55 / +4******22 | drop |
| chinook.db::Customer | `Fax` | Phone number (Direct identifier) | Art. 4(1) identifier | high | +5******66 / +4******55 | drop |
| chinook.db::Customer | `Email` | E-mail address (Direct identifier) | Art. 4(1) identifier | high | l***@e***.br / l***@s***.de | pseudonymise |
| chinook.db::Customer | `SupportRepId` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | * | pseudonymise |
| chinook.db::Employee | `EmployeeId` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | * | pseudonymise |
| chinook.db::Employee | `LastName` | Person name (Direct identifier) | Art. 4(1) identifier | high | A*** / E*** | drop |
| chinook.db::Employee | `FirstName` | Person name (Direct identifier) | Art. 4(1) identifier | high | A*** / N*** | drop |
| chinook.db::Employee | `ReportsTo` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | * | pseudonymise |
| chinook.db::Employee | `BirthDate` | Date of birth (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | high | 19******00 | generalise |
| chinook.db::Employee | `Address` | Postal address (Direct identifier) | Art. 4(1) identifier | high | 11******NW / 82******SW | drop |
| chinook.db::Employee | `City` | City / place (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | medium | Ed****on / C*****y | drop |
| chinook.db::Employee | `PostalCode` | Postal code (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | high | T*****1 / T*****3 | drop |
| chinook.db::Employee | `Phone` | Phone number (Direct identifier) | Art. 4(1) identifier | high | +1******82 / +1******43 | drop |
| chinook.db::Employee | `Fax` | Phone number (Direct identifier) | Art. 4(1) identifier | high | +1******57 / +1******22 | drop |
| chinook.db::Employee | `Email` | E-mail address (Direct identifier) | Art. 4(1) identifier | high | a***@c***.com / n***@c***.com | pseudonymise |
| chinook.db::Invoice | `CustomerId` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | * / ** | pseudonymise |
| chinook.db::Invoice | `BillingAddress` | Postal address (Direct identifier) | Art. 4(1) identifier | high | Th******34 / Ul******14 | drop |
| chinook.db::Invoice | `BillingCity` | City / place (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | medium | St*****rt / **** | keep |
| chinook.db::Invoice | `BillingPostalCode` | Postal code (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | high | 7***4 / **** | generalise |
| insurance.csv | `age` | Age (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | high | ** | generalise |
| insurance.csv | `sex` | Gender / sex (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | high | f****e / **** | keep |
| insurance.csv | `bmi` | Health data (Special category (Art. 9)) | Art. 9(1): needs an Art. 9(2) exception; DPIA likely (Art. 35(3)(b)) | medium | **** / 3***7 | drop |
| insurance.csv | `smoker` | Health data (Special category (Art. 9)) | Art. 9(1): needs an Art. 9(2) exception; DPIA likely (Art. 35(3)(b)) | medium | *** / ** | drop |
| northwind.db::CustomerCustomerDemo | `CustomerID` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | low | - | pseudonymise |
| northwind.db::Customers | `ContactName` | Person name (Direct identifier) | Art. 4(1) identifier | high | M*** A*** / A*** T*** | drop |
| northwind.db::Customers | `ContactTitle` | Occupation / employer (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | low | Sa******ve / O***r | keep |
| northwind.db::EmployeeTerritories | `EmployeeID` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | * | pseudonymise |
| northwind.db::Employees | `EmployeeID` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | * | pseudonymise |
| northwind.db::Employees | `LastName` | Person name (Direct identifier) | Art. 4(1) identifier | high | D*** / F*** | drop |
| northwind.db::Employees | `FirstName` | Person name (Direct identifier) | Art. 4(1) identifier | high | N*** / A*** | drop |
| northwind.db::Employees | `TitleOfCourtesy` | Gender / sex (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | medium | *** / **** | keep |
| northwind.db::Employees | `BirthDate` | Date of birth (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | high | 19******08 / 19******19 | generalise |
| northwind.db::Employees | `Address` | Postal address (Direct identifier) | Art. 4(1) identifier | high | 50******2A / 90******ay | drop |
| northwind.db::Employees | `City` | City / place (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | medium | S*****e / T****a | drop |
| northwind.db::Employees | `PostalCode` | Postal code (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | high | 9***2 / 9***1 | drop |
| northwind.db::Employees | `HomePhone` | Phone number (Direct identifier) | Art. 4(1) identifier | high | (2******57 / (2******82 | drop |
| northwind.db::Employees | `Notes` | Free text (Free text with personal data) | Art. 4(1); check each value | high | - | redact |
| northwind.db::Employees | `ReportsTo` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | * | pseudonymise |
| northwind.db::Orders | `CustomerID` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | V***T / T***P | pseudonymise |
| northwind.db::Orders | `EmployeeID` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | * | pseudonymise |
| northwind.db::Orders | `ShipAddress` | Postal address (Direct identifier) | Art. 4(1) identifier | high | 59******ye / Lu******48 | drop |
| northwind.db::Orders | `ShipCity` | City / place (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | medium | R***s / M*****r | keep |
| northwind.db::Orders | `ShipPostalCode` | Postal code (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | high | 5***0 / 4***7 | generalise |
| northwind.db::Suppliers | `ContactName` | Person name (Direct identifier) | Art. 4(1) identifier | high | C*** C*** / S*** B*** | drop |
| northwind.db::Suppliers | `ContactTitle` | Occupation / employer (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | low | Pu******er / Or******or | drop |
| sakila.db::actor | `actor_id` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | * / ** | pseudonymise |
| sakila.db::actor | `first_name` | Person name (Direct identifier) | Art. 4(1) identifier | high | P*** / N*** | drop |
| sakila.db::actor | `last_name` | Person name (Direct identifier) | Art. 4(1) identifier | high | G*** / W*** | drop |
| sakila.db::address | `address` | Postal address (Direct identifier) | Art. 4(1) identifier | high | 47******ve / 28******rd | drop |
| sakila.db::address | `address2` | Postal address (Direct identifier) | Art. 4(1) identifier | low | - | drop |
| sakila.db::address | `postal_code` | Postal code (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | high | 3***0 / 1***6 | generalise |
| sakila.db::address | `phone` | Phone number (Direct identifier) | Art. 4(1) identifier | low | - | drop |
| sakila.db::customer | `customer_id` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | * / ** | pseudonymise |
| sakila.db::customer | `first_name` | Person name (Direct identifier) | Art. 4(1) identifier | high | M*** / P*** | drop |
| sakila.db::customer | `last_name` | Person name (Direct identifier) | Art. 4(1) identifier | high | S*** / J*** | drop |
| sakila.db::customer | `email` | E-mail address (Direct identifier) | Art. 4(1) identifier | high | M***@s***.org / P***@s***.org | pseudonymise |
| sakila.db::film_actor | `actor_id` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | * / ** | pseudonymise |
| sakila.db::payment | `customer_id` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | * / ** | pseudonymise |
| sakila.db::payment | `staff_id` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | * | pseudonymise |
| sakila.db::rental | `customer_id` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | *** / ** | pseudonymise |
| sakila.db::rental | `staff_id` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | * | pseudonymise |
| sakila.db::staff | `staff_id` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | * | pseudonymise |
| sakila.db::staff | `first_name` | Person name (Direct identifier) | Art. 4(1) identifier | high | M*** / J*** | drop |
| sakila.db::staff | `last_name` | Person name (Direct identifier) | Art. 4(1) identifier | high | H*** / S*** | drop |
| sakila.db::staff | `email` | E-mail address (Direct identifier) | Art. 4(1) identifier | high | M***@s***.com / J***@s***.com | pseudonymise |
| sakila.db::staff | `username` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | **** / *** | pseudonymise |
| sakila.db::store | `manager_staff_id` | Customer / user / employee ID (Pseudonymous ID) | Art. 4(1), 4(5); Recital 26 (still personal data) | medium | * | pseudonymise |
| titanic3.csv | `name` | Person name (Direct identifier) | Art. 4(1) identifier | high | A*** M*** E*** / A*** M*** H*** | drop |
| titanic3.csv | `sex` | Gender / sex (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | high | f****e / **** | keep |
| titanic3.csv | `age` | Age (Quasi-identifier) | Art. 4(1) + Recital 26 (indirect identification) | high | ** / 0****7 | generalise |

Why each column was flagged is in `findings.json` (`why`). Confidence: **high** = check digit or strict format verified (or name + values agree); **medium** = column name or value pattern; **low** = column name only.

## Re-identification risk

- `Heart.csv`: quasi-identifiers `Age`, `Sex` → 14 of 303 records unique (4.6%), 123 in groups smaller than 5.
- `Telco-Customer-Churn.csv`: quasi-identifiers `gender`, `SeniorCitizen`, `Partner` → 0 of 7,043 records unique (0.0%), 0 in groups smaller than 5.
- `adult.csv`: quasi-identifiers `age`, `education`, `educational-num`, `marital-status`, `occupation`, `relationship`, `gender`, `capital-gain`, `capital-loss`, `native-country`, `income` → 11,457 of 20,000 records unique (57.3%), 16,954 in groups smaller than 5.
- `chinook.db::Customer`: quasi-identifiers `City`, `PostalCode` → 59 of 59 records unique (100.0%), 59 in groups smaller than 5.
- `chinook.db::Employee`: quasi-identifiers `BirthDate`, `City`, `PostalCode` → 8 of 8 records unique (100.0%), 8 in groups smaller than 5.
- `chinook.db::Invoice`: quasi-identifiers `BillingCity`, `BillingPostalCode` → 0 of 412 records unique (0.0%), 0 in groups smaller than 5.
- `insurance.csv`: quasi-identifiers `age`, `sex` → 0 of 1,338 records unique (0.0%), 0 in groups smaller than 5.
- `northwind.db::Customers`: quasi-identifiers `ContactTitle` → 2 of 93 records unique (2.1%), 8 in groups smaller than 5.
- `northwind.db::Employees`: quasi-identifiers `TitleOfCourtesy`, `BirthDate`, `City`, `PostalCode` → 9 of 9 records unique (100.0%), 9 in groups smaller than 5.
- `northwind.db::Orders`: quasi-identifiers `ShipCity`, `ShipPostalCode` → 0 of 16,282 records unique (0.0%), 0 in groups smaller than 5.
- `northwind.db::Suppliers`: quasi-identifiers `ContactTitle` → 10 of 29 records unique (34.5%), 18 in groups smaller than 5.
- `sakila.db::address`: quasi-identifiers `postal_code` → 593 of 603 records unique (98.3%), 603 in groups smaller than 5.
- `titanic3.csv`: quasi-identifiers `sex`, `age` → 38 of 1,309 records unique (2.9%), 202 in groups smaller than 5.

Records that are unique on a few ordinary attributes can be singled out and linked to other data (EDPB Guidelines 02/2026 on anonymisation, draft: record isolation and linkage). Removing names alone does not make data anonymous.

## What this means

- The data is **personal data** (Art. 4(1)): the GDPR applies to everything you do with it, including training a model, testing and sharing.
- **Special categories (Art. 9)**: processing is prohibited unless an Art. 9(2) exception applies (e.g. explicit consent, healthcare, research with safeguards). Large-scale processing of this data requires a DPIA (Art. 35(3)(b)). Remove these columns unless the purpose truly needs them.
- **Children**: information society services need parental consent under 16 (or the national age, Art. 8); children merit specific protection (Recital 38).
- **AI training**: you need a lawful basis for training; for legitimate interest, the EDPB's three-step test applies (Opinion 28/2024). A model trained on personal data is not automatically anonymous, so drop direct identifiers and special categories the model does not need before training.
- **Pseudonymise or drop** direct identifiers (Art. 25 data protection by design; Art. 32 security). Pseudonymised data is still personal data (Recital 26), but the risk is lower.
- **Record it**: list this dataset, its purpose and retention in your record of processing (Art. 30).

## After pseudonymisation

- Written: `Heart.csv`, `Telco-Customer-Churn.csv`, `adult.csv`, `chinook.db`, `insurance.csv`, `northwind.db`, `sakila.db`, `titanic3.csv`
- Direct identifiers: 32 column(s) before → 0 after (re-scan of the output).
- Special-category columns: 7 before → 0 after.
- `Heart.csv`: records unique on Age, Sex: 4.6% before → 0.3% after (smallest group 1).
- `Telco-Customer-Churn.csv`: records unique on gender, SeniorCitizen, Partner: 0.0% before → 0.0% after (smallest group 1688).
- `adult.csv`: records unique on age, education, educational-num, marital-status, occupation, relationship, gender, capital-gain, capital-loss, native-country, income: 57.3% before → 1.3% after (smallest group 1).
- `chinook.db::Customer`: records unique on City, PostalCode: 100.0% before → 0.0% after.
- `chinook.db::Employee`: records unique on BirthDate, City, PostalCode: 100.0% before → 25.0% after (smallest group 1) — still high: generalise more or drop a quasi-identifier.
- `chinook.db::Invoice`: records unique on BillingCity, BillingPostalCode: 0.0% before → 0.0% after (smallest group 6).
- `insurance.csv`: records unique on age, sex: 0.0% before → 0.0% after (smallest group 56).
- `northwind.db::Customers`: records unique on ContactTitle: 2.1% before → 2.1% after (smallest group 1).
- `northwind.db::Employees`: records unique on TitleOfCourtesy, BirthDate, City, PostalCode: 100.0% before → 55.6% after (smallest group 1) — still high: generalise more or drop a quasi-identifier.
- `northwind.db::Orders`: records unique on ShipCity, ShipPostalCode: 0.0% before → 0.0% after (smallest group 142).
- `northwind.db::Suppliers`: records unique on ContactTitle: 34.5% before → 0.0% after.
- `sakila.db::address`: records unique on postal_code: 98.3% before → 0.7% after (smallest group 1).
- `titanic3.csv`: records unique on sex, age: 2.9% before → 0.1% after (smallest group 1).
- Pseudonymised columns left in the output: 26 (still personal data).
- Database views that used a dropped column no longer work: `northwind.db::Customer and Suppliers by City`, `northwind.db::Invoices`, `northwind.db::Orders Qry`, `sakila.db::customer_list`, `sakila.db::film_list`, `sakila.db::staff_list`, `sakila.db::sales_by_store` (recreate them without that column).
- Secret key: `.privacy/../keys/secret.key`. Keep it away from the data (other folder, restricted access). Anyone with the key and the original data can re-link pseudonyms.
- **This output is pseudonymised, not anonymous**: it is still personal data under the GDPR (Art. 4(5), Recital 26; EDPB Guidelines 01/2025) for anyone who can re-identify people.

## What this tool cannot decide

- Your lawful basis (Art. 6) and, for special categories, the Art. 9(2) exception.
- Whether each field is necessary for the purpose (data minimisation, Art. 5(1)(c)) and how long to keep it.
- Whether the result is anonymous for a specific recipient: that needs a contextual assessment.
- Personal data it cannot see: images, audio, PDFs, scanned documents, and values outside the sample.

_Generated by GDPR Privacy Scanner 1.1.1. Law and guidance checked: 21 Nov 2026. Not legal advice._
