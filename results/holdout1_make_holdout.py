#!/usr/bin/env python3
"""Generator for the blind GDPR personal-data detection holdout benchmark.

Seeded and reproducible:  python3 make_holdout.py
Writes data/*, labels.json and README.md in the folder of this script.
All synthetic people are fake (Faker); identifiers are format-valid and
checked with python-stdnum where stdnum has a validator.
"""
import base64
import hashlib
import json
import os
import random
import re
import sqlite3
import string
import unicodedata
import uuid
from datetime import date, datetime, timedelta

import pandas as pd
from faker import Faker
from stdnum import ean, iban as stdiban, luhn
from stdnum.cz import rc as cz_rc
from stdnum.de import idnr as de_idnr, vat as de_vat
from stdnum.es import dni as es_dni, nie as es_nie, cif as es_cif
from stdnum.fi import hetu as fi_hetu
from stdnum.fr import nir as fr_nir
from stdnum.ie import pps as ie_pps
from stdnum.it import codicefiscale as it_cf, iva as it_iva
from stdnum.nl import bsn as nl_bsn
from stdnum.pl import pesel as pl_pesel
from stdnum.pt import nif as pt_nif
from stdnum.se import personnummer as se_pnr
from stdnum.util import isdigits
from stdnum.iso7064 import mod_11_10

SEED = 20261121
BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
os.makedirs(DATA, exist_ok=True)

R = random.Random(SEED)
Faker.seed(SEED)
FK = {}


def fk(loc):
    if loc not in FK:
        f = Faker(loc)
        f.seed_instance(SEED + len(FK))
        FK[loc] = f
    return FK[loc]


REF_DAY = date(2026, 10, 1)
VALIDATED = {}  # id type -> list of values (for the final check)


def keep(kind, v):
    VALIDATED.setdefault(kind, []).append(v)
    return v


def maybe(v, p=0.08):
    return None if R.random() < p else v


def rdate(y0, y1):
    d0 = date(y0, 1, 1).toordinal()
    d1 = date(y1, 12, 31).toordinal()
    return date.fromordinal(R.randint(d0, d1))


def rdt(y0=2025, y1=2026):
    d = rdate(y0, y1)
    return datetime(d.year, d.month, d.day, R.randint(0, 23), R.randint(0, 59), R.randint(0, 59))


def age_of(dob):
    return REF_DAY.year - dob.year - ((REF_DAY.month, REF_DAY.day) < (dob.month, dob.day))


def person(loc, y0=1950, y1=2003):
    f = fk(loc)
    g = R.choice("MF")
    first = f.first_name_male() if g == "M" else f.first_name_female()
    last = f.last_name()
    dob = rdate(y0, y1)
    return dict(g=g, first=first, last=last, dob=dob, f=f)


def rand_not(n, validator):
    """Random n-digit number (no leading zero) that is NOT accepted by validator."""
    while True:
        v = str(R.randint(10 ** (n - 1), 10 ** n - 1))
        if not validator(v):
            return v


def digits(n):
    return "".join(R.choice(string.digits) for _ in range(n))


# ---------------------------------------------------------------- national IDs
MONTH_CF = "ABCDEHLMPRST"
BELFIORE = ["F839", "H501", "F205", "L219", "G273", "A662", "D612", "L736", "C351", "A944"]


def _cf_part(s, is_name):
    s = re.sub(r"[^A-Z]", "", s.upper().translate(str.maketrans("ÀÈÉÌÒÙ", "AEEIOU")))
    cons = [c for c in s if c not in "AEIOU"]
    vows = [c for c in s if c in "AEIOU"]
    if is_name and len(cons) >= 4:
        cons = [cons[0], cons[2], cons[3]]
    return ("".join(cons + vows) + "XXX")[:3]


def codice_fiscale(p):
    d = p["dob"]
    day = d.day + (40 if p["g"] == "F" else 0)
    body = _cf_part(p["last"], False) + _cf_part(p["first"], True) + f"{d.year % 100:02d}" + MONTH_CF[d.month - 1] + f"{day:02d}" + R.choice(BELFIORE)
    v = body + it_cf.calc_check_digit(body)
    assert it_cf.is_valid(v), v
    return keep("it_cf", v)


def dni():
    n = f"{R.randint(10000000, 99999999)}"
    v = n + es_dni.calc_check_digit(n)
    assert es_dni.is_valid(v)
    return keep("es_dni", v)


def nie():
    n = R.choice("XYZ") + digits(7)
    v = n + es_nie.calc_check_digit(n)
    assert es_nie.is_valid(v)
    return keep("es_nie", v)


def nir(p):
    d = p["dob"]
    body = ("1" if p["g"] == "M" else "2") + f"{d.year % 100:02d}{d.month:02d}" + R.choice(["75", "13", "69", "33", "59", "31", "44", "67"]) + f"{R.randint(1, 999):03d}{R.randint(1, 999):03d}"
    v = body + fr_nir.calc_check_digits(body)
    assert fr_nir.is_valid(v), v
    return keep("fr_nir", v)


def steuer_id():
    while True:
        ds = R.sample(string.digits, 9)
        if ds[0] == "0":
            continue
        dup = R.choice(ds)
        pos = R.randint(1, 9)
        ds.insert(pos, dup)
        body = "".join(ds)
        v = body + mod_11_10.calc_check_digit(body)
        if de_idnr.is_valid(v):
            return keep("de_idnr", v)


def bsn():
    while True:
        v = str(R.randint(100000000, 699999999))
        if nl_bsn.is_valid(v):
            return keep("nl_bsn", v)


def pesel(p):
    d = p["dob"]
    m = d.month + (20 if d.year >= 2000 else 0)
    serial = digits(3) + str(R.choice([1, 3, 5, 7, 9] if p["g"] == "M" else [0, 2, 4, 6, 8]))
    body = f"{d.year % 100:02d}{m:02d}{d.day:02d}" + serial
    v = body + pl_pesel.calc_check_digit(body)
    assert pl_pesel.is_valid(v)
    return keep("pl_pesel", v)


def nif_pt():
    body = R.choice("12") + digits(7)
    v = body + pt_nif.calc_check_digit(body)
    assert pt_nif.is_valid(v)
    return keep("pt_nif", v)


def personnummer(p):
    d = p["dob"]
    nnn = f"{R.randint(0, 99) :02d}" + str(R.choice([1, 3, 5, 7, 9] if p["g"] == "M" else [0, 2, 4, 6, 8]))
    body = f"{d.year % 100:02d}{d.month:02d}{d.day:02d}" + nnn
    v = f"{body[:6]}-{nnn}{luhn.calc_check_digit(body)}"
    assert se_pnr.is_valid(v), v
    return keep("se_pnr", v)


def hetu(p):
    d = p["dob"]
    sign = "-" if d.year < 2000 else "A"
    n = R.randint(2, 899)
    if (n % 2 == 1) != (p["g"] == "M"):
        n += 1
    body = f"{d.day:02d}{d.month:02d}{d.year % 100:02d}{n:03d}"
    v = f"{body[:6]}{sign}{n:03d}" + "0123456789ABCDEFHJKLMNPRSTUVWXY"[int(body) % 31]
    assert fi_hetu.is_valid(v), v
    return keep("fi_hetu", v)


def pps():
    while True:
        ds = digits(7)
        suffix = R.choice(["", "", "W", "A"])
        s = sum(int(c) * (8 - i) for i, c in enumerate(ds))
        if suffix:
            s += 9 * (ord(suffix) - 64 if suffix != "W" else 0)
        v = ds + "WABCDEFGHIJKLMNOPQRSTUV"[s % 23] + suffix
        if ie_pps.is_valid(v):
            return keep("ie_pps", v)


def rodne_cislo(p):
    d = p["dob"]
    m = d.month + (50 if p["g"] == "F" else 0)
    while True:
        body = f"{d.year % 100:02d}{m:02d}{d.day:02d}" + digits(3)
        c = int(body) % 11
        if c == 10:
            continue
        v = f"{body[:6]}/{body[6:]}{c}"
        if cz_rc.is_valid(v):
            return keep("cz_rc", v)


NINO_BAD1 = set("DFIQUV")
NINO_BAD2 = set("DFIQUVO")
NINO_BADPFX = {"BG", "GB", "NK", "KN", "TN", "NT", "ZZ"}
NINO_RE = re.compile(r"^[A-CEGHJ-PR-TW-Z][A-CEGHJ-NPR-TW-Z]\d{6}[A-D]$")


def nino():
    while True:
        a = R.choice([c for c in string.ascii_uppercase if c not in NINO_BAD1])
        b = R.choice([c for c in string.ascii_uppercase if c not in NINO_BAD2])
        if a + b in NINO_BADPFX:
            continue
        v = a + b + digits(6) + R.choice("ABCD")
        assert NINO_RE.match(v)
        return keep("gb_nino", v)


def hu_szemelyi_szam(p):
    """Hungarian personal identification number (szemelyi azonosito), 11 digits.
    Not in python-stdnum; checksum implemented from the public algorithm."""
    d = p["dob"]
    first = (1 if p["g"] == "M" else 2) + (2 if d.year >= 2000 else 0)
    while True:
        body = f"{first}{d.year % 100:02d}{d.month:02d}{d.day:02d}" + digits(3)
        if d < date(1997, 1, 1):
            c = sum(int(x) * (i + 1) for i, x in enumerate(body)) % 11
        else:
            c = sum(int(x) * (10 - i) for i, x in enumerate(body)) % 11
        if c != 10:
            return keep("hu_szsz", body + str(c))


def iban_for(loc):
    if loc == "hu":
        while True:
            bank = digits(7)
            c1 = (10 - sum(int(x) * w for x, w in zip(bank, [9, 7, 3, 1] * 2)) % 10) % 10
            acct = digits(15)
            c2 = (10 - sum(int(x) * w for x, w in zip(acct, [9, 7, 3, 1] * 4)) % 10) % 10
            bban = bank + str(c1) + acct + str(c2)
            v = "HU" + stdiban.calc_check_digits("HU00" + bban) + bban
            if stdiban.is_valid(v):
                return keep("iban", v)
    while True:
        v = fk(loc).iban()
        if stdiban.is_valid(v) and v[:2] == loc[-2:].upper():
            return keep("iban", v)


def fmt_iban(v):
    return " ".join(v[i:i + 4] for i in range(0, len(v), 4))


def card():
    kind = R.choice(["visa", "visa", "mc", "amex"])
    if kind == "visa":
        body = "4" + digits(14)
    elif kind == "mc":
        body = str(R.randint(51, 55)) + digits(13)
    else:
        body = R.choice(["34", "37"]) + digits(12)
    v = body + luhn.calc_check_digit(body)
    assert luhn.is_valid(v)
    keep("card", v)
    if R.random() < 0.4 and len(v) == 16:
        return " ".join(v[i:i + 4] for i in range(0, 16, 4))
    return v


def ean13(prefix="40"):
    body = prefix + digits(12 - len(prefix))
    v = body + ean.calc_check_digit(body)
    assert ean.is_valid(v)
    return v


def isbn13():
    return ean13("978" + R.choice(["88", "3", "2", "84"]))


def it_piva():
    while True:
        body = digits(7) + f"{R.randint(1, 100):03d}"
        v = body + luhn.calc_check_digit(body)
        if it_iva.is_valid(v):
            return "IT" + v


def de_ustid():
    while True:
        body = str(R.randint(1, 9)) + digits(7)
        v = body + mod_11_10.calc_check_digit(body)
        if de_vat.is_valid(v):
            return "DE" + v


def es_cif_company():
    while True:
        body = R.choice("AB") + digits(7)
        v = body + es_cif.calc_check_digits(body)[0]
        if es_cif.is_valid(v):
            return v


# ---------------------------------------------------------------- helpers
def phone_de():
    n = "1" + R.choice(["51", "52", "60", "62", "70", "71", "76"]) + digits(R.choice([7, 8]))
    return R.choice([f"+49 {n[:3]} {n[3:]}", f"0{n[:3]}/{n[3:]}", f"0{n}", f"0049{n}", f"+49{n}"])


def phone_it():
    n = "3" + R.choice(["33", "35", "38", "40", "47", "20", "92"]) + digits(7)
    return R.choice([f"+39 {n[:3]} {n[3:]}", n, f"{n[:3]} {n[3:6]} {n[6:]}", f"0039{n}"])


def phone_generic(loc, cc):
    raw = fk(loc).phone_number()
    return raw if R.random() < 0.6 else f"+{cc} " + re.sub(r"^\+?\d{0,2}\s?|^0", "", raw)


def email_for(p, domains):
    f, l = p["first"], p["last"]
    def asc(x):
        x = x.lower().replace("ß", "ss").replace("ł", "l").replace("ø", "o").replace("æ", "ae").replace("đ", "d")
        x = unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode()
        return re.sub(r"[^a-z]", "", x) or "user"
    f, l = asc(f), asc(l)
    pat = R.choice(["{f}.{l}", "{f}{l}", "{f0}{l}", "{l}.{f}", "{f}_{l}{n}", "{f}{n}"])
    user = pat.format(f=f, l=l, f0=f[:1], n=R.randint(1, 99))
    return f"{user}@{R.choice(domains)}"


def mixed_date(d, styles):
    s = R.choice(styles)
    return d.strftime(s)


TABLES = []  # (key, df_or_records, labels, meta)


def add(key, columns, labels, rows, fmt, scenario, language, tricky, **kw):
    assert len(columns) == len(labels), key
    TABLES.append(dict(key=key, columns=columns, labels=dict(zip(columns, labels)), rows=rows, fmt=fmt,
                       scenario=scenario, language=language, tricky=tricky, **kw))


def build(specs, n, row_fn):
    """specs: list of (column, label). row_fn(i) -> dict column->value."""
    cols = [c for c, _ in specs]
    labs = [l for _, l in specs]
    rows = []
    for i in range(n):
        r = row_fn(i)
        assert set(cols) <= set(r), set(cols) - set(r)
        rows.append([r[c] for c in cols])
    return cols, labs, rows


# ================================================================ 1 German CRM
def t_crm():
    f = fk("de_DE")
    filialen = [("Filiale München-Pasing", "81241"), ("Filiale Hamburg-Altona", "22765"), ("Filiale Köln Innenstadt", "50667"),
                ("Filiale Leipzig Hbf", "04109"), ("Filiale Stuttgart-Mitte", "70173")]
    seg_age = {"A-Premium": 52.4, "B-Standard": 41.7, "C-Gelegenheit": 33.9, "D-Inaktiv": 47.2}
    notes = ["", "", "kein Kommentar", "Newsletter abbestellt", "Reklamation Lieferung KW12 erledigt", "Zahlung per Lastschrift",
             "Kunde wünscht Rückruf unter {tel}", "Hat Diabetes Typ 1, Lieferung bitte nur vormittags", "Ehefrau {nm} ist Mitinhaberin des Kontos",
             "Gutschein 10% gewährt", "Adressänderung telefonisch, neue Mail {mail}", "VIP – persönlicher Ansprechpartner Hr. Brandt",
             "Mahnstufe 1", "Rollstuhlfahrer, Lieferung ebenerdig"]
    specs = [("KundenNr", "customer_id"), ("Anrede", "gender"), ("Vorname", "person_name"), ("Nachname", "person_name"),
             ("Strasse_HausNr", "postal_address"), ("PLZ", "postal_code"), ("Ort", "city"), ("Tel", "phone"), ("E-Mail", "email"),
             ("Geb_Datum", "date_of_birth"), ("SteuerID", "national_id"), ("IBAN", "iban"),
             ("Kunde_seit", None), ("Umsatz_12M_EUR", None), ("Filiale", None), ("Filiale_PLZ", None), ("Segment", None),
             ("Ø_Alter_Segment", None), ("field_7", None), ("Bemerkung", "free_text")]

    def row(i):
        p = person("de_DE")
        fil = R.choice(filialen)
        seg = R.choice(list(seg_age))
        note = R.choice(notes).format(tel=phone_de(), nm=f.first_name_female() + " " + p["last"], mail=email_for(p, ["web.de", "gmx.de"]))
        return {"KundenNr": f"K{100000 + i * 7 + R.randint(0, 6)}", "Anrede": R.choice(["Herr", "Hr."]) if p["g"] == "M" else R.choice(["Frau", "Fr."]),
                "Vorname": p["first"], "Nachname": p["last"], "Strasse_HausNr": f.street_address(), "PLZ": f.postcode(), "Ort": f.city(),
                "Tel": maybe(phone_de(), 0.1), "E-Mail": maybe(email_for(p, ["gmx.de", "web.de", "t-online.de", "gmail.com", "posteo.de"]), 0.07),
                "Geb_Datum": maybe(mixed_date(p["dob"], ["%d.%m.%Y", "%d.%m.%Y", "%Y-%m-%d"]), 0.05), "SteuerID": maybe(steuer_id(), 0.25),
                "IBAN": maybe(R.choice([lambda v: v, fmt_iban])(iban_for("de_DE")), 0.15), "Beruf": maybe(f.job(), 0.2),
                "Kunde_seit": rdate(2012, 2026).strftime("%d.%m.%Y"), "Umsatz_12M_EUR": f"{R.uniform(0, 4800):.2f}".replace(".", ","),
                "Filiale": fil[0], "Filiale_PLZ": fil[1], "Segment": seg, "Ø_Alter_Segment": str(seg_age[seg]).replace(".", ","),
                "field_7": rand_not(11, de_idnr.is_valid), "Bemerkung": maybe(note, 0.05)}
    cols, labs, rows = build(specs, R.randint(150, 250), row)
    add("crm_kunden_export.csv", cols, labs, rows, ("csv", ";"), "CRM customer export", "German",
        "segment-level average age (Ø_Alter_Segment) = null; branch name/branch PLZ = null; field_7 is a random 11-digit number "
        "(same length as Steuer-IdNr, fails checksum) = null; German decimal commas; notes mix health, phone, spouse name and harmless text")


# ================================================================ 2 Italian e-commerce
def t_ordini():
    f = fk("it_IT")
    prodotti = [("Scarpe da corsa uomo tg. 42", 89.9), ("Zaino trekking 30L", 59.0), ("Caffettiera moka 6 tazze", 24.5), ("Pizza Margherita surgelata x4", 9.99),
                ("Libro: Il nome della rosa", 14.0), ("Cuffie bluetooth ANC", 129.0), ("Borraccia termica 750ml", 19.9), ("Maglia ciclismo donna M", 45.0),
                ("Set pentole antiaderenti", 79.0), ("Lampada da scrivania LED Bella", 34.9)]
    # faker it_IT city() is not hash-seed stable, so use a fixed list
    CITTA_IT = ["Roma", "Milano", "Napoli", "Torino", "Palermo", "Genova", "Bologna", "Firenze", "Bari", "Catania", "Verona", "Padova",
                "Salerno", "Caserta", "Pozzuoli", "Brescia", "Lecce", "Pescara", "Trento", "Cagliari", "Perugia", "Monza"]
    magazzini = ["Magazzino Nola – Interporto Campano, Lotto B", "Magazzino Piacenza – Via Tirotti 2", "Magazzino Passo Corese – Via della Meccanica 1"]
    venditori = [it_piva() for _ in range(6)]
    note = ["", "", "", "Lasciare al portiere", "Citofonare {cog}", "Chiamare prima: {tel}", "Consegna solo mattina", "Regalo, non inserire fattura",
            "Se assente lasciare dalla vicina sig.ra {nome}", "Cancello verde, secondo piano", "Pacco fragile"]
    specs = [("id_ordine", None), ("cod_cliente", "customer_id"), ("data_ordine", None), ("sku", None), ("ean", None),
             ("descrizione_prodotto", None), ("prezzo_unit", None), ("totale_eur", None), ("indirizzo_spedizione", "postal_address"),
             ("cap", "postal_code"), ("citta", "city"), ("cod_fiscale", "national_id"), ("piva_venditore", None), ("magazzino", None),
             ("corriere", None), ("n_tracking", None), ("ip_cliente", "ip_address"), ("note_consegna", "free_text")]

    def row(i):
        p = person("it_IT")
        pr = R.choice(prodotti)
        q = R.randint(1, 4)
        return {"id_ordine": f"ORD-2026-{i + 3000:06d}", "cod_cliente": f"C{R.randint(10000, 99999)}", "data_ordine": rdt().strftime("%d/%m/%Y %H:%M"),
                "sku": f"SKU-{R.choice('ABCDEFG')}{R.randint(1000, 9999)}", "ean": isbn13() if pr[0].startswith("Libro") else ean13("80"),
                "descrizione_prodotto": pr[0], "qta": q, "prezzo_unit": pr[1], "totale_eur": round(pr[1] * q, 2),
                "indirizzo_spedizione": f.street_address(), "cap": f.postcode(), "citta": R.choice(CITTA_IT), "cod_fiscale": maybe(codice_fiscale(p), 0.2),
                "piva_venditore": R.choice(venditori), "magazzino": R.choice(magazzini), "corriere": R.choice(["BRT", "GLS", "SDA", "Poste Italiane", "DHL"]),
                "n_tracking": str(R.randint(10 ** 13, 10 ** 14 - 1)), "ip_cliente": maybe(f.ipv4_public() if R.random() < 0.85 else f.ipv6(), 0.05),
                "stato": R.choice(["consegnato", "spedito", "in lavorazione", "reso", "annullato"]),
                "note_consegna": maybe(R.choice(note).format(cog=p["last"], tel=phone_it(), nome=f.name_female()), 0.1)}
    cols, labs, rows = build(specs, R.randint(150, 250), row)
    add("ordini_ecommerce.csv", cols, labs, rows, ("csv", ","), "E-commerce orders", "Italian",
        "seller VAT numbers (valid P.IVA) = null; warehouse addresses = null; 14-digit tracking numbers, EAN-13 and ISBN-13 = null; "
        "product names that look like first names (Margherita, Bella) = null; IPv4 and IPv6 mixed")


# ================================================================ 3 Spanish payroll (TSV)
def t_nomina():
    f = fk("es_ES")
    cif = es_cif_company()
    puestos = ["Técnico de mantenimiento", "Contable", "Enfermera", "Desarrollador backend", "Mozo de almacén", "Jefa de ventas", "Administrativo", "Conductor"]
    specs = [("id_empleado", "customer_id"), ("nombre_completo", "person_name"), ("dni_nie", "national_id"), ("iban_nomina", "iban"),
             ("email_corporativo", "email"), ("salario_bruto_anual", "income"), ("departamento", None), ("puesto", "occupation"),
             ("fecha_alta", None), ("fecha_nacimiento", "date_of_birth"), ("estado_civil", "marital_status"), ("afiliacion_sindical", "trade_union"),
             ("motivo_baja", "health"), ("centro_trabajo", None), ("cuenta_contable", None), ("cif_empresa", None)]

    def row(i):
        p = person("es_ES", 1960, 2004)
        nm = f"{p['first']} {p['last']} {f.last_name()}"
        return {"id_empleado": f"E-{2000 + i}", "nombre_completo": nm.upper() if R.random() < 0.3 else nm, "dni_nie": dni() if R.random() < 0.8 else nie(),
                "iban_nomina": iban_for("es_ES"), "email_corporativo": email_for(p, ["logisur.es"]),
                "salario_bruto_anual": round(R.uniform(16576, 68000), 2), "departamento": R.choice(["Operaciones", "Finanzas", "IT", "RRHH", "Ventas"]),
                "puesto": R.choice(puestos), "fecha_alta": rdate(2005, 2026).isoformat(), "fecha_nacimiento": p["dob"].strftime("%d/%m/%Y"),
                "estado_civil": maybe(R.choice(["soltero/a", "casado/a", "divorciado/a", "viudo/a", "pareja de hecho"]), 0.1),
                "afiliacion_sindical": R.choice(["", "", "", "CCOO", "UGT", "CGT", "ninguna"]),
                "motivo_baja": R.choice(["", "", "", "", "", "lumbalgia", "depresión", "embarazo de riesgo", "fractura muñeca", "COVID-19", "gripe"]),
                "centro_trabajo": R.choice(["Almacén Getafe", "Oficina Sevilla – Av. de la Buhaira 15", "Plataforma Zaragoza PLAZA"]),
                "cuenta_contable": R.choice(["640000", "642000", "465000"]), "cif_empresa": cif}
    cols, labs, rows = build(specs, R.randint(150, 250), row)
    add("nomina_empleados.tsv", cols, labs, rows, ("csv", "\t"), "HR / payroll", "Spanish",
        "mix of DNI and NIE in one column; company CIF (constant, valid) = null; accounting account codes = null; mostly-empty special-category "
        "columns (union, sick-leave reason); some names in upper case")


# ================================================================ 4 French hospital
def t_hopital():
    f = fk("fr_FR")
    docs = [f"Dr {fk('fr_FR').first_name()} {fk('fr_FR').last_name()}" for _ in range(8)]
    cim = [("E11.9", "metformine 1000 mg"), ("I10", "amlodipine 5 mg"), ("J45.9", "salbutamol inhalé"), ("C50.9", "tamoxifène 20 mg"),
           ("F32.1", "sertraline 50 mg"), ("K35.8", "amoxicilline-ac. clav."), ("O80", ""), ("S72.0", "paracétamol 1 g x3"), ("N18.3", "furosémide 40 mg")]
    comm = ["RAS", "RAS", "", "Patiente anxieuse, fille ({nm}, {tel}) à prévenir", "Allergie pénicilline signalée", "Transfert prévu en cardiologie",
            "Refuse transfusion (Témoin de Jéhovah)", "Sortie J+2 si constantes stables", "Appeler le conjoint au {tel}", "Bilan sanguin à 8h",
            "Suivi par Dr Morel, ancien tabagique"]
    specs = [("IPP", "customer_id"), ("NIR", "national_id"), ("nom", "person_name"), ("prenom", "person_name"), ("date_naissance", "date_of_birth"),
             ("sexe", "gender"), ("groupe_sanguin", "health"), ("code_cim10", "health"), ("test_brca1", "genetic"),
             ("medecin_referent", "person_name"), ("service", None), ("chambre", None), ("date_entree", None), ("mutuelle", None),
             ("finess_etab", None), ("commentaire_infirmier", "free_text")]
    finess = [digits(9) for _ in range(3)]

    def row(i):
        p = person("fr_FR", 1935, 2006)
        c = R.choice(cim)
        return {"IPP": f"{R.randint(10 ** 7, 10 ** 8 - 1)}", "NIR": maybe(R.choice([lambda v: v, lambda v: f"{v[0]} {v[1:3]} {v[3:5]} {v[5:7]} {v[7:10]} {v[10:13]} {v[13:]}"])(nir(p)), 0.05),
                "nom": p["last"].upper(), "prenom": p["first"], "date_naissance": p["dob"].strftime("%d/%m/%Y"), "sexe": p["g"],
                "groupe_sanguin": R.choice(["A+", "O+", "B+", "AB+", "A-", "O-", ""]), "code_cim10": c[0], "traitement": maybe(c[1], 0.1),
                "test_brca1": R.choice(["", "", "", "", "négatif", "variant pathogène c.68_69delAG", "VSI"]), "medecin_referent": R.choice(docs),
                "service": R.choice(["Cardiologie", "Médecine interne", "Oncologie", "Maternité", "Urgences", "Orthopédie"]),
                "chambre": f"{R.choice('ABC')}-{R.randint(100, 450)}", "date_entree": rdt().strftime("%Y-%m-%d %H:%M"),
                "mutuelle": R.choice(["MGEN", "Harmonie Mutuelle", "AXA Santé", "Malakoff Humanis", ""]), "finess_etab": R.choice(finess),
                "commentaire_infirmier": R.choice(comm).format(nm=f.name_female(), tel=f.phone_number())}
    cols, labs, rows = build(specs, R.randint(150, 250), row)
    add("patients_hopital.csv", cols, labs, rows, ("csv", ";"), "Hospital admissions", "French",
        "doctor names (natural persons) = person_name; FINESS facility numbers (9 digits) = null; room codes and admission timestamps = null; "
        "mutuelle (insurer company) = null; genetic test column mostly empty; NIR with and without spaces")


# ================================================================ 5 Dutch insurance claims (nested JSON)
def t_claims():
    f = fk("nl_NL")
    def kenteken():
        L = "BDFGHJKLNPRSTVXZ"
        return R.choice([f"{R.choice(L)}{R.choice(L)}-{digits(3)}-{R.choice(L)}", f"{digits(1)}-{R.choice(L)}{R.choice(L)}{R.choice(L)}-{digits(2)}",
                         f"{R.choice(L)}{R.choice(L)}{R.choice(L)}-{digits(2)}-{R.choice(L)}", f"{digits(2)}-{R.choice(L)}{R.choice(L)}-{R.choice(L)}{R.choice(L)}"])
    oms = ["Ruitbreuk voorruit door steenslag", "Hagelschade aan motorkap en dak", "Aanrijding op de A12 bij Utrecht, tegenpartij {nm} ({tel})",
           "Inbraak in auto, laptop gestolen", "Verzekerde had whiplash na aanrijding, opgenomen in UMC", "Parkeerschade, dader onbekend",
           "Eenzijdig ongeval, gladheid", "Getuige: {nm}, bereikbaar via {mail}"]
    bureaus = [("Schade-Expertise Nederland B.V.", "Utrecht"), ("Crawford & Company", "Rotterdam"), ("Van Ameyde", "Rijswijk"), ("TEN Schade-experts", "Zwolle")]
    kvk = {b[0]: digits(8) for b in bureaus}
    labels = {"claimnummer": None, "schadedatum": None, "schadebedrag": None,
              "verzekerde.naam": "person_name", "verzekerde.bsn": "national_id", "verzekerde.geboortedatum": "date_of_birth",
              "verzekerde.adres.straat": "postal_address", "verzekerde.adres.postcode": "postal_code", "verzekerde.adres.woonplaats": "city",
              "verzekerde.telefoon": "phone", "voertuig.kenteken": "vehicle_plate", "voertuig.merk": None, "voertuig.bouwjaar": None,
              "omschrijving": "free_text", "expert.bureau": None, "expert.vestiging": None, "expert.kvk": None}
    recs = []
    for i in range(R.randint(150, 250)):
        p = person("nl_NL")
        b = R.choice(bureaus)
        tussen = R.choice(["", "", "van ", "de ", "van der "])
        recs.append({"claimnummer": f"CLM{2026}{i + 1:05d}", "schadedatum": rdate(2025, 2026).isoformat(), "schadebedrag": round(R.uniform(150, 18000), 2),
                     "verzekerde": {"naam": f"{p['first']} {tussen}{p['last']}", "bsn": bsn(), "geboortedatum": p["dob"].strftime("%d-%m-%Y"),
                                    "adres": {"straat": f.street_address(), "postcode": f.postcode(), "woonplaats": f.city()},
                                    "telefoon": maybe(f.phone_number(), 0.1)},
                     "voertuig": {"kenteken": kenteken(), "merk": R.choice(["Volkswagen", "Kia", "Toyota", "Tesla", "Peugeot", "Opel"]), "bouwjaar": R.randint(2008, 2026)},
                     "omschrijving": R.choice(oms).format(nm=f.name(), tel=f.phone_number(), mail=f.free_email()),
                     "expert": {"bureau": b[0], "vestiging": b[1], "kvk": kvk[b[0]]}})
    add("schadeclaims.json", list(labels), list(labels.values()), recs, ("json",), "Motor insurance claims (nested JSON array)", "Dutch",
        "nested objects 2 levels deep (dot-path labels); BSN without formatting; expert office city and KvK number = null; vehicle build year = null")


# ================================================================ 6 Portuguese school (minors)
def t_escola():
    f = fk("pt_PT")
    turmas = {f"{a}º{t}": round(R.uniform(11.5, 16.5), 1) for a in (7, 8, 9) for t in "ABC"}
    specs = [("n_processo", "customer_id"), ("nome_aluno", "person_name"), ("data_nascimento", "date_of_birth"), ("idade", "age"),
             ("nif_aluno", "national_id"), ("turma", None), ("ano_letivo", None), ("encarregado_educacao", "person_name"),
             ("telemovel_ee", "phone"), ("email_ee", "email"), ("nee", "health"), ("emrc", "religion"), ("escola", None),
             ("morada_escola", None), ("cod_postal_escola", None), ("media_turma", None)]
    escolas = [("Agrupamento de Escolas de Benfica", "Rua Dr. João Couto, Lisboa", "1500-236"), ("Escola Básica Gaia Nascente", "Rua do Bom Sucesso 103, Vila Nova de Gaia", "4400-034")]

    def row(i):
        p = person("pt_PT", 2011, 2014)
        t = R.choice(list(turmas))
        es = R.choice(escolas)
        ee = person("pt_PT", 1970, 1990)
        ee["last"] = p["last"]
        return {"n_processo": str(R.randint(10000, 39999)), "nome_aluno": f"{p['first']} {f.last_name()} {p['last']}", "data_nascimento": p["dob"].isoformat(),
                "idade": age_of(p["dob"]), "nif_aluno": maybe(nif_pt(), 0.1), "turma": t, "ano_letivo": "2026/2027",
                "encarregado_educacao": f"{ee['first']} {ee['last']}", "telemovel_ee": maybe(R.choice(["9", "+351 9", "00351 9"]) + R.choice("1236") + digits(7), 0.05),
                "email_ee": maybe(email_for(ee, ["gmail.com", "sapo.pt", "hotmail.com"]), 0.15),
                "nee": R.choice(["", "", "", "", "", "dislexia", "PHDA", "perturbação do espetro do autismo", "diabetes tipo 1", "baixa visão"]),
                "emrc": R.choice(["Sim (Católica)", "Não", "Não", "Sim (Evangélica)", "Sim (Islâmica)"]), "escola": es[0], "morada_escola": es[1],
                "cod_postal_escola": es[2], "media_turma": turmas[t]}
    cols, labs, rows = build(specs, R.randint(150, 250), row)
    add("alunos_escola.csv", cols, labs, rows, ("csv", ","), "School pupil register (minors, 11-15 y)", "Portuguese",
        "school address and school postcode = null; class average grade (media_turma, same for whole class) = null; religion-class enrolment = religion; "
        "special educational needs = health")


# ================================================================ 7 Polish gym
def t_silownia():
    f = fk("pl_PL")
    kluby = [("FitZone Kraków Galeria", "ul. Pawia 5, 31-154 Kraków"), ("FitZone Warszawa Mokotów", "ul. Wołoska 12, 02-675 Warszawa"),
             ("FitZone Gdańsk Oliwa", "al. Grunwaldzka 309, 80-309 Gdańsk")]
    specs = [("nr_karty", "customer_id"), ("imie_i_nazwisko", "person_name"), ("pesel", "national_id"), ("plec", "gender"), ("wiek", "age"),
             ("tel", "phone"), ("e_mail", "email"), ("kontuzje_uwagi", "health"), ("szablon_odcisku_palca", "biometric"), ("klub", None),
             ("adres_klubu", None), ("karnet_typ", None), ("cena_pln", None), ("data_zakupu", None), ("kod_promocyjny", None)]

    def row(i):
        p = person("pl_PL", 1960, 2008)
        k = R.choice(kluby)
        return {"nr_karty": f"FZ{R.randint(10 ** 7, 10 ** 8 - 1)}", "imie_i_nazwisko": f"{p['first']} {p['last']}", "pesel": pesel(p),
                "plec": "M" if p["g"] == "M" else "K", "wiek": age_of(p["dob"]),
                "tel": maybe(R.choice(["+48 ", "", "0048"]) + R.choice("5678") + digits(2) + R.choice([" ", ""]) + digits(3) + R.choice([" ", "-", ""]) + digits(3), 0.07),
                "e_mail": maybe(email_for(p, ["wp.pl", "onet.pl", "gmail.com", "interia.pl"]), 0.1),
                "kontuzje_uwagi": R.choice(["", "", "", "brak", "kontuzja kolana (ACL 2024)", "astma", "nadciśnienie", "ciąża 2 trymestr", "przepuklina L5-S1"]),
                "szablon_odcisku_palca": base64.b64encode(bytes(R.getrandbits(8) for _ in range(R.randint(48, 72)))).decode(),
                "klub": k[0], "adres_klubu": k[1], "karnet_typ": R.choice(["OPEN", "PORANNY", "STUDENT", "SENIOR"]), "cena_pln": R.choice([99, 129, 149, 79]),
                "data_zakupu": rdate(2025, 2026).strftime("%d.%m.%Y"), "kod_promocyjny": maybe("".join(R.choice(string.ascii_uppercase + string.digits) for _ in range(8)), 0.6)}
    cols, labs, rows = build(specs, R.randint(150, 250), row)
    add("czlonkowie_silowni.csv", cols, labs, rows, ("csv", ","), "Gym membership with fingerprint entry", "Polish",
        "fingerprint template stored as base64 blob = biometric; club addresses including postcode = null; random promo codes = null; PESEL gender digit consistent")


# ================================================================ 8 Swedish ride-hailing
def t_resor():
    zones = {"Stockholm C": (59.3303, 18.0586), "Södermalm": (59.3149, 18.0710), "Kista": (59.4032, 17.9447), "Solna": (59.3600, 18.0009),
             "Arlanda": (59.6498, 17.9238), "Nacka": (59.3105, 18.1637)}
    drivers = [(f"DRV-{R.randint(1000, 9999)}", person("sv_SE", 1965, 2000)) for _ in range(30)]
    for d in drivers:
        d[1]["pnr"] = personnummer(d[1])
        L = "ABCDEFGHJKLMNOPRSTUWXYZ"
        d[1]["reg"] = "".join(R.choice(L) for _ in range(3)) + R.choice([" ", ""]) + digits(2) + R.choice(list(L) + list(string.digits))
        d[1]["dev"] = str(uuid.UUID(int=R.getrandbits(128)))
    specs = [("resa_id", None), ("forar_id", "customer_id"), ("passagerar_id", "customer_id"), ("forare_personnr", "national_id"),
             ("regnr", "vehicle_plate"), ("start_lat", "geolocation"), ("start_lon", "geolocation"),
             ("starttid", None), ("avstand_km", None), ("pris_sek", None), ("betalmetod", None),
             ("enhets_id", "device_id"), ("zon", None), ("zon_lat", None), ("zon_lon", None)]

    def row(i):
        d = R.choice(drivers)
        z = R.choice(list(zones))
        lat, lon = zones[z]
        km = round(R.uniform(1.2, 42), 1)
        return {"resa_id": str(uuid.UUID(int=R.getrandbits(128))), "forar_id": d[0], "passagerar_id": f"u_{R.randint(10 ** 6, 10 ** 7)}",
                "forare_personnr": d[1]["pnr"] if R.random() < 0.7 else d[1]["pnr"].replace("-", ""), "regnr": d[1]["reg"],
                "start_lat": round(lat + R.uniform(-0.03, 0.03), 6), "start_lon": round(lon + R.uniform(-0.05, 0.05), 6),
                "slut_lat": round(59.33 + R.uniform(-0.12, 0.3), 6), "slut_lon": round(18.05 + R.uniform(-0.2, 0.15), 6),
                "starttid": rdt().strftime("%Y-%m-%dT%H:%M:%S"), "avstand_km": str(km).replace(".", ","), "pris_sek": int(45 + km * 14.5),
                "betalmetod": R.choice(["kort", "Swish", "faktura", "Apple Pay"]), "enhets_id": d[1]["dev"], "zon": z, "zon_lat": lat, "zon_lon": lon}
    cols, labs, rows = build(specs, R.randint(150, 250), row)
    add("resor_gps.csv", cols, labs, rows, ("csv", ";"), "Ride-hailing trips with GPS", "Swedish",
        "zone centroid lat/lon (fixed per zone) = null while trip start/end coordinates = geolocation; trip UUID = null vs driver app device UUID = device_id; "
        "personnummer with and without hyphen")


# ================================================================ 9 UK newsletter (JSONL, nested)
def t_newsletter():
    f = fk("en_GB")
    labels = {"signup_id": None, "email": "email", "first_name": "person_name", "postcode": "postal_code",
              "consent.marketing": None, "consent.ts": None, "consent.policy_version": None,
              "source.campaign": None, "source.ip": "ip_address", "source.ua": "user_agent", "source.landing_page": None,
              "prefs.topics": None, "prefs.frequency": None}
    recs = []
    for i in range(R.randint(150, 250)):
        p = person("en_GB")
        recs.append({"signup_id": f"nl_{i + 1:06d}", "email": email_for(p, ["gmail.com", "outlook.com", "btinternet.com", "yahoo.co.uk"]),
                     "first_name": maybe(p["first"], 0.2), "postcode": maybe(f.postcode(), 0.3),
                     "consent": {"marketing": R.random() < 0.7, "ts": rdt().isoformat() + "Z", "policy_version": R.choice(["2024-03", "2025-11"])},
                     "source": {"campaign": R.choice(["black_friday_26", "spring_sale", "organic", "podcast_ad"]), "ip": f.ipv4_public(), "ua": f.user_agent(),
                                "landing_page": R.choice(["/", "/offers", "/blog/how-to-choose-running-shoes", "/newsletter"])},
                     "prefs": {"topics": ";".join(R.sample(["running", "cycling", "outdoor", "sale"], R.randint(1, 3))), "frequency": R.choice(["weekly", "monthly"])}})
    add("newsletter_signups.jsonl", list(labels), list(labels.values()), recs, ("jsonl",), "Newsletter sign-ups", "English (UK)",
        "JSON Lines with nested consent/source/prefs objects; consent timestamps and policy versions = null")


# ================================================================ 10 Danish web analytics (TSV)
def t_events():
    f = fk("da_DK")
    servers = ["10.20.1.11", "10.20.1.12", "10.20.1.13", "10.20.2.7"]
    sessions = []
    for _ in range(60):
        sessions.append(dict(cookie=f"GA1.2.{R.randint(10 ** 8, 10 ** 9)}.{R.randint(1700000000, 1790000000)}", sess=hashlib.md5(str(R.random()).encode()).hexdigest(),
                             ip=f.ipv4_public(), ua=f.user_agent(), ad=str(uuid.UUID(int=R.getrandbits(128))).upper() if R.random() < 0.5 else "",
                             uid=f"bruger{R.randint(1000, 99999)}" if R.random() < 0.5 else ""))
    specs = [("event_id", None), ("tidsstempel", None), ("cookie_id", "device_id"), ("session_id", "device_id"),
             ("bruger_id", "customer_id"), ("ip_adresse", "ip_address"), ("user_agent", "user_agent"), ("annonce_id", "device_id"),
             ("side_url", None), ("produkt_sku", None), ("kurv_vaerdi_dkk", None), ("indholds_hash", None), ("server_ip", None)]

    def row(i):
        s = R.choice(sessions)
        url = R.choice(["/da/", "/da/kurv", "/da/produkter/cykelhjelm-pro", "/da/kasse", "/da/kampagne/vinter26"])
        return {"event_id": str(uuid.UUID(int=R.getrandbits(128))), "tidsstempel": int(rdt().timestamp() * 1000), "haendelse": R.choice(["page_view", "add_to_cart", "purchase", "scroll"]),
                "cookie_id": s["cookie"], "session_id": s["sess"], "bruger_id": s["uid"], "ip_adresse": s["ip"], "user_agent": s["ua"], "annonce_id": s["ad"],
                "side_url": "https://shop.example.dk" + url, "skaermoplosning": R.choice(["1920x1080", "390x844", "1440x900"]),
                "produkt_sku": R.choice(["", "DK-HJ-220", "DK-LYS-031", "DK-LÅS-007"]), "kurv_vaerdi_dkk": R.choice(["", f"{R.uniform(99, 2500):.2f}"]),
                "indholds_hash": hashlib.sha256(url.encode()).hexdigest(), "server_ip": R.choice(servers)}
    cols, labs, rows = build(specs, R.randint(150, 250), row)
    add("web_haendelser.tsv", cols, labs, rows, ("csv", "\t"), "Web analytics events", "Danish",
        "event UUID = null vs advertising UUID = device_id; internal server IPs (10.x) = null vs visitor IP = ip_address; sha256 of page URL = null; "
        "epoch-millisecond timestamps = null")


# ================================================================ 11 Czech support tickets
def t_podpora():
    f = fk("cs_CZ")
    agents = [f"{fk('cs_CZ').first_name()} {fk('cs_CZ').last_name()}" for _ in range(6)]
    popis = ["Nefunguje přihlášení do aplikace po aktualizaci.", "Reklamace: displej po týdnu prasklý.", "Zákazník {nm} volal z {tel}, nefunguje mu router.",
             "Prosím o vrácení peněz na účet {iban}.", "Faktura obsahuje špatnou cenu za dopravu.", "Pošlete prosím kopii smlouvy na {mail}.",
             "Dotaz na dostupnost zboží.", "Kurýr nedoručil, prý nikdo nebyl doma.", "Zákaznice je po operaci a nemůže převzít zásilku osobně."]
    specs = [("cislo_tiketu", None), ("vytvoreno", None), ("jmeno_zakaznika", "person_name"), ("rodne_cislo", "national_id"), ("telefon", "phone"),
             ("email", "email"), ("predmet", None), ("popis_problemu", "free_text"), ("stav", None), ("resitel", "person_name"),
             ("produkt", None), ("cislo_objednavky", None)]

    def row(i):
        p = person("cs_CZ")
        return {"cislo_tiketu": f"TKT-{48000 + i}", "vytvoreno": rdt().strftime("%d.%m.%Y %H:%M"), "jmeno_zakaznika": f"{p['first']} {p['last']}",
                "rodne_cislo": maybe(rodne_cislo(p), 0.3), "telefon": maybe(R.choice(["+420 ", "", "00420"]) + R.choice(["602", "731", "777", "604"]) + " " + digits(3) + " " + digits(3), 0.05),
                "email": maybe(email_for(p, ["seznam.cz", "email.cz", "centrum.cz", "gmail.com"]), 0.1),
                "predmet": R.choice(["Reklamace", "Fakturace", "Technická podpora", "Doprava", "Vrácení zboží"]),
                "popis_problemu": R.choice(popis).format(nm=f.name(), tel="+420 " + digits(9), iban=iban_for("cs_CZ"), mail=f.free_email()),
                "stav": R.choice(["nový", "řeší se", "vyřešeno", "zamítnuto"]), "priorita": R.choice(["nízká", "střední", "vysoká"]), "resitel": R.choice(agents),
                "produkt": R.choice(["Router AX3000", "Mobilní tarif S", "TV box 4K", "Optika 500 Mb/s"]), "cislo_objednavky": rand_not(10, cz_rc.is_valid)}
    cols, labs, rows = build(specs, R.randint(150, 250), row)
    add("podpora_tikety.csv", cols, labs, rows, ("csv", ";"), "Customer-support tickets", "Czech (outside required list)",
        "support agent names (employees) = person_name; 10-digit order numbers (same length as rodné číslo digits) = null; ticket subject = null "
        "while free-text description sometimes holds names/phones/IBAN/health")


# ================================================================ 12 Hungarian bank transactions
def t_tranzakciok():
    f = fk("hu_HU")
    customers = []
    for _ in range(70):
        p = person("hu_HU")
        customers.append(dict(id=f"UGY-{R.randint(100000, 999999)}", iban=iban_for("hu"), card=card(), szsz=hu_szemelyi_szam(p), nm=f"{p['last']} {p['first']}"))
    merchants = [("TESCO Budaörs", "Budaörs", "5411"), ("MOL Benzinkút M1", "Tatabánya", "5541"), ("Lidl Debrecen", "Debrecen", "5411"),
                 ("Libri Allee", "Budapest", "5942"), ("Wizz Air", "Budapest", "4511"), ("Spar Szeged", "Szeged", "5411")]
    kozl = ["", "", "", "Albérlet - {nm}", "SZLA-2026/{n}", "Ebéd", "Kölcsön visszafizetés {nm2}", "Rezsi", "Fizetés október", "Ajándék anyának"]
    specs = [("tranzakcio_azonosito", None), ("ugyfel_azonosito", "customer_id"), ("szamla_iban", "iban"), ("c3", "payment_card"),
             ("szemelyi_szam", "national_id"), ("osszeg_huf", None), ("konyvelesi_datum", None), ("kereskedo", None),
             ("kereskedo_varos", None), ("mcc", None), ("kozlemeny", "free_text"), ("csatorna", None), ("referencia_hash", None)]

    def row(i):
        c = R.choice(customers)
        m = R.choice(merchants)
        return {"tranzakcio_azonosito": rand_not(16, luhn.is_valid), "ugyfel_azonosito": c["id"], "szamla_iban": c["iban"], "c3": c["card"],
                "szemelyi_szam": maybe(c["szsz"], 0.2), "osszeg_huf": -R.randint(500, 250000), "penznem": "HUF", "konyvelesi_datum": rdate(2026, 2026).strftime("%Y.%m.%d."),
                "kereskedo": m[0], "kereskedo_varos": m[1], "mcc": m[2], "kozlemeny": R.choice(kozl).format(nm=c["nm"], n=R.randint(1, 999), nm2=f.name()),
                "egyenleg_kategoria": R.choice(["A", "B", "C"]), "csatorna": R.choice(["POS", "online", "átutalás", "ATM"]),
                "referencia_hash": hashlib.sha1(str(R.random()).encode()).hexdigest()[:20]}
    cols, labs, rows = build(specs, R.randint(150, 250), row)
    add("tranzakciok.csv", cols, labs, rows, ("csv", ","), "Bank card transactions", "Hungarian (outside required list)",
        "card numbers under the uninformative name c3 (spaced and unspaced, Luhn-valid); 16-digit transaction IDs (card-length, not Luhn-checked) = null; "
        "merchant names/cities and MCC codes = null; Hungarian személyi szám (checksum from public algorithm, not in stdnum)")


# ================================================================ 13 Finnish smart-home IoT
def t_iot():
    f = fk("fi_FI")
    homes = []
    for _ in range(45):
        p = person("fi_FI")
        homes.append(dict(dev=f"HB-{''.join(R.choice('0123456789ABCDEF') for _ in range(12))}", hetu=hetu(p), addr=f.street_address(), pc=f.postcode(), city=f.city(),
                          gps=f"{60.1 + R.uniform(0, 5):.5f},{22 + R.uniform(0, 8):.5f}"))
    specs = [("laite_id", "device_id"), ("mittausaika", None), ("lampotila_c", None), ("kulutus_kwh", None),
             ("firmware", None), ("anturi_malli", None), ("asiakas_hetu", "national_id"), ("asennusosoite", "postal_address"),
             ("postinumero", "postal_code"), ("kunta", "city"), ("koordinaatit", "geolocation"), ("col12", None), ("verkkoalue", None)]

    def row(i):
        h = R.choice(homes)
        return {"laite_id": h["dev"], "mittausaika": rdt(2026, 2026).isoformat(timespec="seconds"), "lampotila_c": round(R.uniform(17, 24), 1),
                "kosteus_pct": R.randint(20, 60), "kulutus_kwh": round(R.uniform(0.1, 3.5), 3), "firmware": R.choice(["v2.4.1", "v2.5.0", "v3.0.0-rc1"]),
                "anturi_malli": R.choice(["TH-200", "TH-210 Pro", "EM-1 Energia"]), "asiakas_hetu": maybe(h["hetu"], 0.1), "asennusosoite": h["addr"],
                "postinumero": h["pc"], "kunta": h["city"], "koordinaatit": h["gps"], "col12": f"{R.randint(100000, 999999)}-{R.choice('ABCDEFHJKLMNPRSTUVWXY')}",
                "verkkoalue": R.choice(["Helen Sähköverkko", "Caruna", "Elenia"])}
    cols, labs, rows = build(specs, R.randint(150, 250), row)
    add("iot_mittaukset.csv", cols, labs, rows, ("csv", ";"), "Smart-home sensor telemetry", "Finnish",
        "col12 is a batch/lot code shaped like a HETU tail (6 digits-dash-letter) = null; household coordinates as one 'lat,lon' string; "
        "grid operator company = null")


# ================================================================ 14 UK/IE applicants (xlsx)
def t_applicants():
    f = fk("en_GB")
    fi = fk("en_IE")
    notes = ["Strong Python skills, good culture fit", "", "Candidate mentioned she is pregnant, available from June", "Call back on {tel}",
             "Referred by {nm} (Data team)", "No-show for first interview", "Requested step-free access to interview room (wheelchair user)",
             "Salary expectations too high", "Previous employer reference received", "Needs visa sponsorship"]
    specs = [("ApplicantRef", "customer_id"), ("Full Name", "person_name"), ("Email", "email"), ("Mobile", "phone"), ("NINO", "national_id"),
             ("PPSN", "national_id"), ("DOB", "date_of_birth"), ("Nationality", "nationality"), ("Highest Qualification", "education"),
             ("Current Job Title", "occupation"), ("Current Employer", None), ("Expected Salary", "income"),
             ("Ethnicity", "racial_ethnic_origin"), ("Disability", "health"), ("Unspent Convictions", "criminal"), ("Sexual Orientation", "sex_life_orientation"),
             ("Vacancy Code", None), ("Applied On", None), ("Recruiter Notes", "free_text")]

    def row(i):
        irish = R.random() < 0.35
        p = person("en_IE" if irish else "en_GB", 1965, 2004)
        return {"ApplicantRef": f"APP-{26000 + i}", "Full Name": f"{p['first']} {p['last']}", "Email": email_for(p, ["gmail.com", "outlook.com", "eircom.net" if irish else "hotmail.co.uk"]),
                "Mobile": ("+353 8" + R.choice("3567") + " " + digits(3) + " " + digits(4)) if irish else R.choice(["07", "+44 7"]) + digits(3) + " " + digits(6),
                "NINO": None if irish else maybe(R.choice([lambda v: v, lambda v: f"{v[:2]} {v[2:4]} {v[4:6]} {v[6:8]} {v[8]}"])(nino()), 0.1),
                "PPSN": pps() if irish else None, "DOB": p["dob"].strftime("%d/%m/%Y"),
                "Nationality": R.choice(["Irish", "Irish", "Polish", "Brazilian"]) if irish else R.choice(["British", "British", "Indian", "Nigerian", "Italian", "Pakistani"]),
                "Highest Qualification": R.choice(["GCSE", "A-Level", "BSc", "BA (Hons)", "MSc", "PhD", "Leaving Certificate", "HND"]),
                "Current Job Title": maybe(f.job(), 0.15), "Current Employer": R.choice(["Tesco PLC", "Accenture", "HSE", "NHS Digital", "Ryanair", "Unemployed", "Self-employed"]),
                "Current Salary": maybe(R.randrange(22000, 95000, 500), 0.2), "Expected Salary": R.randrange(28000, 110000, 1000),
                "Ethnicity": R.choice(["White - British", "White - Irish", "Asian - Indian", "Black - African", "Mixed", "Prefer not to say", "Asian - Pakistani"]),
                "Disability": R.choice(["No", "No", "No", "Yes - dyslexia", "Yes - hearing impairment", "Prefer not to say"]),
                "Unspent Convictions": R.choice(["No", "No", "No", "No", "Yes - driving offence 2023", "Prefer not to say"]),
                "Sexual Orientation": R.choice(["Heterosexual", "Heterosexual", "Gay", "Bisexual", "Lesbian", "Prefer not to say"]),
                "Religion": R.choice(["None", "Christian", "Catholic", "Muslim", "Hindu", "Jewish", "Prefer not to say"]),
                "Vacancy Code": R.choice(["VAC-2026-014", "VAC-2026-021", "VAC-2026-030"]), "Applied On": rdate(2026, 2026).strftime("%Y-%m-%d"),
                "Recruiter Notes": R.choice(notes).format(tel=f.phone_number(), nm=fi.name())}
    cols, labs, rows = build(specs, R.randint(150, 250), row)
    add("applicants.xlsx::Applicants", cols, labs, rows, ("xlsx",), "Job applicants with equal-opportunity monitoring", "English (UK + Ireland)",
        "two national-ID columns each ~2/3 or ~1/3 empty; NINO with and without spaces; employer company = null; vacancy codes and application date = null; "
        "'Unemployed'/'Self-employed' as employer values")


# ================================================================ 15/16 SQLite finance.db
def t_finance():
    vendors = [("Bürobedarf Schmidt GmbH", de_ustid(), "de_DE", "info@buerobedarf-schmidt.de", "+49 89 4521300"),
               ("Amazon Web Services EMEA SARL", "LU26888617", "fr_FR", "aws-billing@amazon.com", "+352 2789 0057"),
               ("Officine Meccaniche Rossi S.p.A.", it_piva(), "it_IT", "amministrazione@omrossi.it", "+39 0522 941100"),
               ("Logística Ibérica S.L.", "ES" + es_cif_company(), "es_ES", "facturas@logiberica.es", "+34 91 555 0123"),
               ("Hotel Bayerischer Hof GmbH", de_ustid(), "de_DE", "reservations@bayerischerhof.de", "+49 89 21200")]
    viban = {v[0]: iban_for(v[2]) for v in vendors}
    lspecs = [("entry_id", None), ("posting_date", None), ("account_code", None), ("cost_center", None), ("description", None),
              ("amount_eur", None), ("currency", None), ("vendor_name", None), ("vendor_vat", None), ("vendor_iban", None),
              ("vendor_email", None), ("vendor_phone", None), ("invoice_no", None), ("fiscal_period", None)]
    descr = ["Office supplies Q1", "AWS invoice – compute", "Spare parts order", "Freight Madrid–Milan", "Conference venue deposit", "Licence renewal",
             "Accrual reversal", "FX revaluation"]

    def lrow(i):
        v = R.choice(vendors)
        d = rdate(2025, 2026)
        return {"entry_id": 900000 + i, "posting_date": d.isoformat(), "account_code": R.choice(["4000", "6100", "6300", "6815", "2100"]),
                "cost_center": R.choice(["CC-OPS", "CC-IT", "CC-SALES", "CC-HQ"]), "description": R.choice(descr), "amount_eur": round(R.uniform(-5000, 25000), 2),
                "currency": "EUR", "vendor_name": v[0], "vendor_vat": v[1], "vendor_iban": viban[v[0]], "vendor_email": v[3], "vendor_phone": v[4],
                "invoice_no": f"INV-{d.year}-{R.randint(1, 99999):05d}", "fiscal_period": f"{d.year}-P{d.month:02d}"}
    lc, ll, lr = build(lspecs, R.randint(150, 250), lrow)
    add("finance.db::ledger", lc, ll, lr, ("sqlite", "finance.db", "ledger"), "General ledger / AP entries", "English",
        "ALL columns null: supplier IBANs (valid), supplier VAT IDs, generic supplier e-mails (info@, billing@) and switchboard phones = null; invoice numbers")

    emps = []
    for k in range(40):
        loc = R.choice(["de_DE", "it_IT", "fr_FR", "nl_NL", "es_ES"])
        p = person(loc, 1965, 2002)
        emps.append(dict(no=f"{R.randint(10000, 99999)}", nm=f"{p['first']} {p['last']}", mail=email_for(p, ["eurotrade-group.eu"]), iban=iban_for(loc)))
    mgrs = [e["nm"] for e in emps[:5]]
    especs = [("claim_id", None), ("emp_no", "customer_id"), ("employee_name", "person_name"), ("work_email", "email"), ("iban", "iban"),
              ("amount", None), ("category", None), ("submitted_at", None), ("approver", "person_name"), ("receipt_ref", None), ("notes", "free_text")]
    enotes = ["", "Taxi to client with {nm}", "Hotel Munich 2 nights", "Train ticket", "Dinner with Dr. {nm}, Siemens", "Lost receipt – see email from {mail}",
              "Medical certificate attached, trip cancelled due to illness", "Parking airport"]

    def erow(i):
        e = R.choice(emps)
        o = R.choice(emps)
        return {"claim_id": 5000 + i, "emp_no": e["no"], "employee_name": e["nm"], "work_email": e["mail"], "iban": e["iban"], "amount": round(R.uniform(8, 1400), 2),
                "category": R.choice(["travel", "meals", "lodging", "training", "other"]), "submitted_at": rdt().strftime("%Y-%m-%d %H:%M:%S"),
                "approver": R.choice(mgrs), "receipt_ref": hashlib.md5(str(R.random()).encode()).hexdigest()[:12].upper(),
                "notes": R.choice(enotes).format(nm=o["nm"], mail=o["mail"])}
    ec, el, er = build(especs, R.randint(150, 250), erow)
    add("finance.db::expense_claims", ec, el, er, ("sqlite", "finance.db", "expense_claims"), "Employee expense claims", "English",
        "employee IBANs (personal) in the same DB as supplier IBANs (null); manager names in approver; receipt hash refs = null")


# ================================================================ 17 Greek survey
def t_survey():
    f = fk("el_GR")
    specs = [("αναγνωριστικό_ερωτώμενου", "customer_id"), ("έκδοση_ερωτηματολογίου", None), ("ημερομηνία_υποβολής", None), ("ηλικία", "age"),
             ("φύλο", "gender"), ("πόλη", "city"), ("οικογενειακή_κατάσταση", "marital_status"),
             ("εισόδημα_κλίμακα", "income"), ("θρήσκευμα", "religion"), ("κόμμα_ψήφου", "political_opinion"), ("μέλος_συνδικάτου", "trade_union"),
             ("χρόνια_πάθηση", "health"), ("q7", None), ("σχόλια", "free_text")]
    comments = ["", "", "", "Καλή έρευνα.", "Πολύ μεγάλο ερωτηματολόγιο.", "Τηλεφωνήστε μου στο 69{d}", "Είμαι η {nm} και θα ήθελα τα αποτελέσματα στο {mail}",
                "Ο γιατρός μου είπε ότι έχω κατάθλιψη από πέρσι.", "Δεν εμπιστεύομαι τα κόμματα."]

    def row(i):
        p = person("el_GR", 1945, 2007)
        return {"αναγνωριστικό_ερωτώμενου": f"R-{i + 1:06d}", "έκδοση_ερωτηματολογίου": "v2.1", "ημερομηνία_υποβολής": rdate(2026, 2026).strftime("%d/%m/%Y"),
                "ηλικία": age_of(p["dob"]), "φύλο": "Άνδρας" if p["g"] == "M" else R.choice(["Γυναίκα", "Γυναίκα", "Άλλο"]),
                "πόλη": R.choice(["Αθήνα", "Θεσσαλονίκη", "Πάτρα", "Ηράκλειο", "Λάρισα", "Βόλος"]),
                "οικογενειακή_κατάσταση": R.choice(["Έγγαμος/η", "Άγαμος/η", "Διαζευγμένος/η", "Χήρος/α"]),
                "εκπαίδευση": R.choice(["Δημοτικό", "Λύκειο", "ΑΕΙ", "Μεταπτυχιακό", "ΙΕΚ"]),
                "εισόδημα_κλίμακα": R.choice(["<10.000€", "10.000-20.000€", "20.000-35.000€", ">35.000€", "Δεν απαντώ"]),
                "θρήσκευμα": R.choice(["Ορθόδοξος/η", "Ορθόδοξος/η", "Καθολικός/ή", "Μουσουλμάνος/α", "Άθεος/η", "Δεν απαντώ"]),
                "κόμμα_ψήφου": R.choice(["ΝΔ", "ΠΑΣΟΚ", "ΣΥΡΙΖΑ", "ΚΚΕ", "Ελληνική Λύση", "Λευκό", "Δεν απαντώ"]),
                "μέλος_συνδικάτου": R.choice(["Όχι", "Όχι", "Ναι - ΓΣΕΕ", "Ναι - ΑΔΕΔΥ"]),
                "χρόνια_πάθηση": R.choice(["Καμία", "Καμία", "Διαβήτης τύπου 2", "Υπέρταση", "Άσθμα", "Κατάθλιψη"]), "q7": R.randint(1, 5),
                "ικανοποίηση_1_10": R.randint(1, 10), "σχόλια": R.choice(comments).format(d=digits(8), nm=f"{p['first']} {p['last']}", mail=f.free_email())}
    cols, labs, rows = build(specs, R.randint(150, 250), row)
    add("ereuna_kinonikon_stasewn.csv", cols, labs, rows, ("csv", ","), "Opinion survey with sensitive answers", "Greek (outside required list; Greek script headers)",
        "all column names in Greek script; Likert answer q7 = null; questionnaire version = null")


# ================================================================ 18 application log
def t_log():
    f = fk("en_GB")
    lines = []
    users = [(email_for(person(l), ["gmail.com", "libero.it", "gmx.de", "orange.fr"]), f.ipv4_public()) for l in ["it_IT", "de_DE", "fr_FR", "en_GB"] for _ in range(6)]
    for i in range(R.randint(180, 230)):
        ts = rdt(2026, 2026).isoformat(timespec="milliseconds") + "Z"
        u, ip = R.choice(users)
        k = R.random()
        if k < 0.35:
            l = f"{ts} INFO  [http] GET /api/v1/products/SKU-{R.randint(1000, 9999)} 200 {R.randint(3, 180)}ms"
        elif k < 0.5:
            l = f"{ts} INFO  [scheduler] job=nightly-export status=OK rows={R.randint(1000, 90000)} duration={R.randint(10, 900)}s"
        elif k < 0.62:
            l = f"{ts} WARN  [auth] failed login for user={u} from {ip} attempt={R.randint(1, 5)}"
        elif k < 0.72:
            l = f"{ts} INFO  [auth] login ok uid={R.randint(10000, 99999)} ip={ip}"
        elif k < 0.8:
            l = f"{ts} ERROR [payments] card declined for order ORD-2026-{R.randint(1, 999999):06d} reason=insufficient_funds"
        elif k < 0.87:
            l = f"{ts} DEBUG [mailer] queued template=order_confirmation to={u}"
        elif k < 0.93:
            l = f"{ts} INFO  [http] POST /api/v1/cart 201 {R.randint(5, 90)}ms ua=\"{f.user_agent()}\""
        else:
            l = f"{ts} ERROR [db] connection pool exhausted host=db-replica-02 port=5432"
        lines.append([l])
    add("app_server.log", ["line"], ["free_text"], lines, ("log",), "Application server log", "English",
        "most lines are technical; a minority contain e-mails, client IPs, user IDs and user agents")


# ================================================================ write everything
def nested(rec_flat_keys, rec):
    return rec


def main():
    for fn in [t_crm, t_ordini, t_nomina, t_hopital, t_claims, t_escola, t_silownia, t_resor, t_newsletter, t_events, t_podpora,
               t_tranzakciok, t_iot, t_applicants, t_finance, t_survey, t_log]:
        fn()
    labels = {}
    sqlite_path = os.path.join(DATA, "finance.db")
    if os.path.exists(sqlite_path):
        os.remove(sqlite_path)
    readme = ["# GDPR personal-data detection holdout (blind)", "",
              "Generated by `make_holdout.py` (seed %d). Labels in `labels.json`. One line per table:" % SEED, ""]
    for t in TABLES:
        key, fmt = t["key"], t["fmt"]
        labels[key] = t["labels"]
        kind = fmt[0]
        if kind == "csv":
            df = pd.DataFrame(t["rows"], columns=t["columns"])
            df.to_csv(os.path.join(DATA, key), sep=fmt[1], index=False, encoding="utf-8")
            n = len(df)
        elif kind == "xlsx":
            fname, sheet = key.split("::")
            df = pd.DataFrame(t["rows"], columns=t["columns"])
            df.to_excel(os.path.join(DATA, fname), sheet_name=sheet, index=False)
            n = len(df)
        elif kind == "sqlite":
            con = sqlite3.connect(sqlite_path)
            pd.DataFrame(t["rows"], columns=t["columns"]).to_sql(fmt[2], con, index=False)
            con.close()
            n = len(t["rows"])
        elif kind == "json":
            with open(os.path.join(DATA, key), "w", encoding="utf-8") as fh:
                json.dump(t["rows"], fh, ensure_ascii=False, indent=1)
            n = len(t["rows"])
        elif kind == "jsonl":
            with open(os.path.join(DATA, key), "w", encoding="utf-8") as fh:
                for r in t["rows"]:
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            n = len(t["rows"])
        elif kind == "log":
            with open(os.path.join(DATA, key), "w", encoding="utf-8") as fh:
                fh.write("\n".join(r[0] for r in t["rows"]) + "\n")
            n = len(t["rows"])
        npers = sum(1 for v in t["labels"].values() if v)
        readme.append(f"- `{key}` | {t['scenario']} | {t['language']} | {n} rows x {len(t['columns'])} cols "
                      f"({npers} personal / {len(t['columns']) - npers} null) | tricky: {t['tricky']}")
    with open(os.path.join(BASE, "labels.json"), "w", encoding="utf-8") as fh:
        json.dump(labels, fh, ensure_ascii=False, indent=1)
    readme += ["", "Notes:", "- Labels follow the benchmark rules: business locations, company identifiers, generic company contacts, order/transaction IDs, "
               "amounts and non-birth dates are null; employees' work e-mails are email; salary is income.",
               "- Identifiers validated with python-stdnum: IT codice fiscale, ES DNI/NIE, FR NIR, DE Steuer-IdNr, NL BSN, PL PESEL, PT NIF, SE personnummer, "
               "FI HETU, IE PPS, CZ rodné číslo, IBANs, payment cards (Luhn), EAN/ISBN. UK NINO checked with the HMRC prefix/format rules and "
               "Hungarian személyi szám with its public checksum (neither is in python-stdnum).",
               "- JSON/JSONL columns are dot paths of leaf keys; xlsx/sqlite keys are `file::table`; the .log file has a single column `line`."]
    with open(os.path.join(BASE, "README.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(readme) + "\n")


if __name__ == "__main__":
    main()
