# Buyer test: expected answers written BEFORE running the scanner

Written 2026-11-21T23:07 against frozen v1.0.0 (see frozen_hashes_v1.0.0.txt), before any scan of these files.

Real public datasets: Chinook, Northwind, Sakila (SQLite sample databases), Titanic (titanic3.csv), UCI Adult census (adult.csv),
Cleveland heart disease (Heart.csv), US medical insurance (insurance.csv), IBM Telco customer churn, UCI red wine quality (negative control).
46 tables, 325 columns: 111 personal, 214 non-personal. Labels in buyer_labels.json, same rules as the blind holdout:
- Business data is not personal: Northwind customers/suppliers are companies, so their codes, addresses and phones are null; their contact person names are personal.
- IDs that point to a person (customer, employee, staff, actor IDs, usernames) = customer_id. IDs that point to addresses, stores or films = null.
- Medical measurements (BMI, smoking, cholesterol, blood pressure, ECG, heart-disease diagnosis) = health.
- Composer names in Chinook = person_name (real people). Artist names = null (mostly bands).
- Region/state of residence = city (coarse place of residence); country of residence = null.
- Photos/pictures = null in this taxonomy (personal data, but not biometric under Recital 51). Passwords = null (not in taxonomy).
What I expect before running: abbreviated medical columns (Chol, Fbs, RestECG, ...) are likely MISSED (no hints for them, on purpose);
business-contact columns in Northwind may cause false alarms (phone/address/city of companies).
