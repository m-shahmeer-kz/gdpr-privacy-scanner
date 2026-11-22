"""Build docs/index.html from results/*.json so every number on the page is a measured one.

Run:  python docs/build.py
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
H1 = json.loads((R / "holdout1_blind.json").read_text())
H2 = json.loads((R / "holdout2_blind.json").read_text())
REAL = json.loads((R / "real_datasets.json").read_text())
PSEUDO = json.loads((R / "pseudonymisation_real.json").read_text())
CODE = json.loads((R / "code_real_repos.json").read_text())
AGENSI_URL = "https://www.agensi.io/skills/gdpr-privacy-scanner-find-personal-data-before-you-build-ai"
PRICE = "$15"
GH = "https://github.com/m-shahmeer-kz/gdpr-privacy-scanner"
e = html.escape
CSS = (ROOT / "docs" / "style.css").read_text()

GROUPS = [
    ("E-mails, phones, IBANs, cards, IPs", {"email", "phone", "iban", "payment_card", "ip_address"}),
    ("National ID numbers", {"national_id"}),
    ("Names", {"person_name"}),
    ("IDs that link a row to a person", {"customer_id", "device_id"}),
    ("Quasi-identifiers (birth date, age, postcode, ...)", {"date_of_birth", "age", "gender", "postal_code", "city",
     "nationality", "occupation", "marital_status", "education", "income", "vehicle_plate", "user_agent",
     "geolocation", "postal_address"}),
    ("Special categories (Art. 9) and criminal data", {"health", "genetic", "biometric", "racial_ethnic_origin",
     "political_opinion", "religion", "trade_union", "sex_life_orientation", "criminal"}),
    ("Free text containing personal data", {"free_text"}),
]


def norm(t):
    nat = {"it_codice_fiscale", "es_dni_nie", "fr_nir", "de_steuer_id", "nl_bsn", "be_national_number", "pl_pesel",
           "pt_nif", "se_personnummer", "fi_hetu", "dk_cpr", "ie_pps", "ro_cnp", "at_svnr", "uk_nino", "uk_nhs"}
    return "national_id" if t in nat else t


def group_rows(res):
    out = ""
    for label, types in GROUPS:
        xs = [r for r in res["rows"] if r["expected"] and norm(r["expected"]) in types]
        if xs:
            out += f"<tr><td>{e(label)}</td><td>{sum(1 for r in xs if r['got'])} / {len(xs)}</td></tr>"
    return out


h2 = H2["result"]
h1a, h1b = H1["frozen_versions"]["1.0.0"], H1["frozen_versions"]["1.0.1"]
r0, r1 = REAL["frozen_1.0.0"], REAL["after_fixes_1.1.x"]
pb, pa = PSEUDO["before"]["by_category"], PSEUDO["after"]["by_category"]
direct_b = pb.get("direct", 0) + pb.get("financial", 0)
direct_a = pa.get("direct", 0) + pa.get("financial", 0)
adult = next(x for x in PSEUDO["reidentification"] if x["table"].endswith("adult.csv"))
leak = PSEUDO["raw_value_leak_check"]
buy = f'<a class="btn solid" href="{AGENSI_URL}" target="_blank" rel="noopener">Get it on Agensi · {PRICE} ↗</a>'
miss2 = "".join(f"<tr><td>{e(r['table'])}</td><td><code>{e(r['column'])}</code></td><td>{e(r['expected'] or 'not personal')}</td>"
                f"<td>{e(r['got'] or 'not found')}</td></tr>" for r in h2["rows"] if r["status"] in ("FN", "FP"))

page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GDPR Privacy Scanner · is there personal data in your dataset?</title>
<meta name="description" content="AI-agent skill that finds personal data in datasets and code (names, e-mails, IBANs, 16 EU and UK national IDs, health and other Article 9 data, re-identification risk), pseudonymises it and writes a GDPR report. Blind-tested. Not legal advice.">
<meta property="og:type" content="website">
<meta property="og:title" content="GDPR Privacy Scanner · is there personal data in your dataset?">
<meta property="og:description" content="Finds personal data in your data and code before you build AI on it, then pseudonymises it and writes a GDPR report. Blind-tested. Not legal advice.">
<meta property="og:url" content="https://m-shahmeer-kz.github.io/gdpr-privacy-scanner/">
<meta property="og:image" content="https://m-shahmeer-kz.github.io/gdpr-privacy-scanner/assets/og.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="627">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="assets/logo.png">
{CSS}</head>
<body><div class="wrap">
<p class="sub" style="letter-spacing:.12em;text-transform:uppercase;font-size:12px">AI-agent skill · Claude Code · Codex · Cursor · Gemini CLI</p>
<h1>Is there personal data in your dataset?</h1>
<p class="sub">GDPR Privacy Scanner lets your AI coding agent check datasets (CSV, Excel, JSON, Parquet, SQLite, logs) and code for personal data
before you build AI or analytics on them. It finds names, e-mails, phones, addresses, IBANs, payment cards and 16 EU and UK national ID numbers
(checking their check digits), special-category data such as health or religion, and how many people could be re-identified from ordinary
columns like birth date and postcode. Then it plans and applies pseudonymisation on a copy, re-checks the result and writes a short GDPR report.</p>
<div class="notice"><b>Not legal advice.</b> The scanner can miss personal data and can flag columns that are not personal. Every report says so
and asks you to have your DPO or a privacy professional confirm it. Pseudonymised output is still personal data under the GDPR.</div>
<div class="btns">{buy}<a class="btn" href="#tested">Blind test results</a><a class="btn" href="#real">Real data</a><a class="btn" href="{GH}">GitHub ↗</a></div>

<h2 id="tested">Blind test: data the scanner had never seen</h2>
<p class="sub">I froze the skill, then asked a fresh AI agent that had never seen its code to build a realistic test set from scratch:
{e(H2['built'])}. Every column has a correct label, and {h2['non_personal_columns']} of the {h2['columns']} are look-alikes that are not personal data
(business contact details, order and booking numbers, product codes, timestamps, aggregates). Version {e(H2['version'])} was scored once, with no changes afterwards.</p>
<div class="grid">
 <div class="card stat"><b>{h2['detected']} / {h2['personal_columns']}</b><span>personal-data columns found ({round(h2['recall']*100)}%)</span></div>
 <div class="card stat"><b>{h2['false_alarms']} / {h2['non_personal_columns']}</b><span>non-personal columns wrongly flagged</span></div>
 <div class="card stat"><b>{leak['raw_values_checked']:,}</b><span>real names, e-mails, phones and addresses checked: none appeared in any report (all masked)</span></div>
 <div class="card stat"><b>{direct_b} → {direct_a}</b><span>columns of direct identifiers before → after pseudonymising 9 real datasets</span></div>
</div>
<details><summary>Results by kind of data</summary><div class="tbl"><table><tr><th>Kind of data</th><th>Found</th></tr>{group_rows(h2)}</table></div></details>
<details><summary>Every miss and false alarm</summary><div class="tbl"><table><tr><th>Table</th><th>Column</th><th>Truth</th><th>Scanner</th></tr>{miss2}</table></div></details>
<p class="sub">History, for honesty: an earlier blind test (18 tables, 256 columns, built the same way) found {h1a['detected']} of {h1a['personal_columns']}
with version 1.0.0 and {h1b['detected']} of {h1b['personal_columns']} with 1.0.1, with {h1b['false_alarms']} false alarms out of {h1b['non_personal_columns']}.
It was weak on ID columns like <code>KundenNr</code> and on languages it did not know (Greek, Czech, Hungarian). I added 22 EU languages and
person-ID rules, then built the new blind test above to measure the new version fairly.</p>

<h2 id="real">Real public datasets</h2>
<p class="sub">{len(REAL['datasets'])} well-known datasets ({e(', '.join(REAL['datasets']))}): {r0['columns']} columns. I wrote the correct answer
for every column before the first run.</p>
<div class="tbl"><table><tr><th>Version</th><th>Personal columns found</th><th>False alarms</th></tr>
<tr><td>1.0.0 (frozen, first run)</td><td>{r0['detected']} / {r0['personal_columns']}</td><td>{r0['false_alarms']} / {r0['non_personal_columns']}</td></tr>
<tr><td>1.1 (after fixes; not blind)</td><td>{r1['detected']} / {r1['personal_columns']}</td><td>{r1['false_alarms']} / {r1['non_personal_columns']}</td></tr></table></div>
<p class="sub">What it still misses here: abbreviated medical columns in the heart-disease data (<code>Fbs</code>, <code>Thal</code>, <code>Oldpeak</code>...)
and US state columns. After pseudonymising with the default plan, records unique on ordinary attributes in the census data fell from
{round(adult['unique_share_before']*100)}% to {round(adult['unique_share_after']*100, 1)}%. Small tables (8 employees) stay unique: the report says so and suggests dropping them.</p>

<h2>Code review on real projects</h2>
<p class="sub">It also reads code for privacy problems: personal data in logs, sent to LLM APIs or trackers, plain hashes of e-mails,
special-category fields in schemas, personal data saved in notebook outputs. On 3 real open-source projects
({', '.join(e(p['repo']) for p in CODE['projects'])}) the first version raised {CODE['frozen_1.0.0']['findings']} findings, of which
{CODE['frozen_1.0.0']['confirmed']} was real: {e(CODE['frozen_1.0.0']['confirmed_detail'])}. After fixing the noise it raises
{CODE['after_fixes_1.0.2']['findings']}, the real one.</p>

<h2>What your agent does with it</h2>
<ol class="steps">
<li>Asks what the data is for (AI training, analytics, sharing) and which columns you need to link records.</li>
<li>Scans data and, if you want, code. Every finding comes with the GDPR article, a confidence level and masked examples only.</li>
<li>Reviews the doubtful findings itself and adds what the scanner cannot see.</li>
<li>Plans actions per column: drop, pseudonymise (keyed HMAC-SHA256), generalise (birth year, age band, postcode prefix), mask or redact free text.
It tightens the plan until at most 5% of records are unique.</li>
<li>Applies the plan on a copy, never on your originals, with the key kept separately. Then it re-scans the output.</li>
<li>Answers in plain language: what was found, the biggest risks, what was done (before → after) and what only you can decide.</li>
</ol>

<h2>Good to know</h2>
<div class="grid">
 <div class="card"><h3>Who it is for</h3><p>EU companies and teams that want to train AI, run analytics or share data built from customer, patient or employee records.</p></div>
 <div class="card"><h3>Runs locally</h3><p>One Python package, standard library only (Python 3.10+; pandas only for Excel/Parquet). Nothing is uploaded.</p></div>
 <div class="card"><h3>Check digits, not guesses</h3><p>IBANs and ID numbers from 14 countries are validated by their check digits, so order numbers and ISBNs are not mistaken for them.</p></div>
 <div class="card"><h3>Honest limits</h3><p>It reads a sample per table, cannot read images or PDFs, and misses coded or abbreviated columns. It does not decide your lawful basis.</p></div>
</div>

<div class="btns" style="margin-top:34px">{buy}<a class="btn" href="{GH}">GitHub ↗</a></div>
<p class="sub">Made by <a href="https://m-shahmeer-kz.github.io/">Muhammad Shahmeer</a> · Data Science MSc, University of Naples Federico II · © 2026, all rights reserved.
Not legal advice. Not affiliated with the EDPB or any data protection authority.</p>
</div></body></html>
"""
(ROOT / "docs" / "index.html").write_text(page)
print("wrote docs/index.html", len(page))
