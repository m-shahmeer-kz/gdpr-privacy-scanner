#!/usr/bin/env python3
"""Seeded generator for the holdout2 GDPR personal-data detection benchmark.

Writes data files to ./data, ground-truth labels to ./labels.json.
Run:  python3 make_holdout.py
"""
import base64
import datetime as dt
import hashlib
import json
import random
import sqlite3
import string
import unicodedata
from pathlib import Path

import pandas as pd
from faker import Faker
from stdnum import ean as std_ean
from stdnum import iban as std_iban
from stdnum import isbn as std_isbn
from stdnum import luhn
from stdnum.be import nn as be_nn
from stdnum.cz import rc as cz_rc
from stdnum.ee import ik as ee_ik
from stdnum.es import dni as es_dni
from stdnum.es import nie as es_nie
from stdnum.ie import pps as ie_pps
from stdnum.it import codicefiscale
from stdnum.lt import asmens as lt_asmens
from stdnum.pl import pesel as pl_pesel
from stdnum.pt import nif as pt_nif
from stdnum.ro import cnp as ro_cnp
from stdnum.se import personnummer as se_pnr
from stdnum.sk import dph as sk_dph

SEED = 20261122
random.seed(SEED)
Faker.seed(SEED)
R = random.Random(SEED)

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)

LABELS = {}
README = []
VALIDATIONS = []  # (name, validator, list_of_values)
TODAY = dt.date(2026, 11, 1)

FK = {}


def fk(loc):
    if loc not in FK:
        FK[loc] = Faker(loc)
    return FK[loc]


# ----------------------------------------------------------------- helpers
def d(n):
    return "".join(R.choice(string.digits) for _ in range(n))


def up(n):
    return "".join(R.choice(string.ascii_uppercase) for _ in range(n))


def rdate(a, b):
    return a + dt.timedelta(days=R.randint(0, (b - a).days))


def rdt(a, b):
    base = rdate(a, b)
    return dt.datetime(base.year, base.month, base.day, R.randint(0, 23), R.randint(0, 59), R.randint(0, 59))


def birth(min_age=18, max_age=85):
    return rdate(dt.date(TODAY.year - max_age, 1, 1), dt.date(TODAY.year - min_age, 10, 31))


def age_of(b, ref=TODAY):
    return ref.year - b.year - ((ref.month, ref.day) < (b.month, b.day))


def maybe(v, p):
    return None if R.random() < p else v


def ascii_up(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper()


def person(loc):
    f = fk(loc)
    fem = R.random() < 0.5
    first = f.first_name_female() if fem else f.first_name_male()
    last = f.last_name_female() if (fem and hasattr(f, "last_name_female")) else (
        f.last_name_male() if hasattr(f, "last_name_male") else f.last_name())
    return first, last, fem


def dec(x, comma=True):
    s = f"{x:.2f}"
    return s.replace(".", ",") if comma else s


def register(key, df_or_cols, labels, desc):
    cols = list(df_or_cols)
    assert cols == list(labels.keys()), (key, cols, list(labels.keys()))
    LABELS[key] = labels
    README.append(desc)


# ------------------------------------------------------------------ phones
PH = {
    "IT": ("39", "", lambda: "3" + R.choice("234689") + d(8)),
    "DE": ("49", "0", lambda: R.choice(["151", "152", "160", "170", "176", "177", "30", "89", "221", "40"]) + d(8)),
    "ES": ("34", "", lambda: R.choice("67") + d(8)),
    "FR": ("33", "0", lambda: R.choice("67") + d(8)),
    "PL": ("48", "", lambda: R.choice("5678") + d(8)),
    "PT": ("351", "", lambda: "9" + R.choice("1236") + d(7)),
    "BE": ("32", "0", lambda: "4" + R.choice("6789") + d(7)),
    "CZ": ("420", "", lambda: R.choice("67") + d(8)),
    "IE": ("353", "0", lambda: "8" + R.choice("35679") + d(7)),
    "RO": ("40", "0", lambda: "7" + R.choice("2345") + d(7)),
    "SE": ("46", "0", lambda: "7" + R.choice("0236") + d(7)),
    "GR": ("30", "", lambda: "69" + R.choice("0345789") + d(7)),
    "HU": ("36", "06", lambda: R.choice(["20", "30", "70"]) + d(7)),
    "EE": ("372", "", lambda: "5" + d(7)),
    "LT": ("370", "8", lambda: "6" + d(7)),
    "BG": ("359", "0", lambda: "8" + R.choice("789") + d(7)),
    "SK": ("421", "0", lambda: "9" + R.choice("01458") + d(7)),
}


def phone(cc):
    code, trunk, gen = PH[cc]
    nsn = gen()
    f = R.random()
    sp = lambda s: f"{s[:3]} {s[3:6]} {s[6:]}"
    if f < 0.28:
        return f"+{code} {sp(nsn)}"
    if f < 0.42:
        return f"+{code}{nsn}"
    if f < 0.50:
        return f"00{code} {nsn}"
    if f < 0.75:
        return trunk + nsn
    if f < 0.90:
        return trunk + sp(nsn)
    return f"{trunk}{nsn[:3]}/{nsn[3:]}"


# ------------------------------------------------------------- identifiers
CF_PLACES = ["F839", "H501", "F205", "L219", "A662", "D612", "G273", "C351", "A509", "B963"]


def gen_cf(first, last, b, fem):
    def cons(s):
        return [c for c in s if c.isalpha() and c not in "AEIOU"]

    def vow(s):
        return [c for c in s if c in "AEIOU"]

    L, F = ascii_up(last), ascii_up(first)
    s = (cons(L) + vow(L) + ["X"] * 3)[:3]
    c = cons(F)
    n = [c[0], c[2], c[3]] if len(c) >= 4 else (c + vow(F) + ["X"] * 3)[:3]
    base = "".join(s) + "".join(n) + f"{b.year % 100:02d}" + "ABCDEHLMPRST"[b.month - 1] + \
        f"{b.day + (40 if fem else 0):02d}" + R.choice(CF_PLACES)
    return base + codicefiscale.calc_check_digit(base)


def gen_dni():
    s = d(8)
    return s + es_dni.calc_check_digit(s)


def gen_nie():
    p = R.choice("XYZ") + d(7)
    return p + es_nie.calc_check_digit(p)


def gen_pt_nif():
    b = R.choice("123") + d(7)
    return b + pt_nif.calc_check_digit(b)


def gen_pesel(b, fem):
    m = b.month + (20 if b.year >= 2000 else 0)
    s = f"{b.year % 100:02d}{m:02d}{b.day:02d}" + d(3) + str(R.choice([0, 2, 4, 6, 8] if fem else [1, 3, 5, 7, 9]))
    return s + pl_pesel.calc_check_digit(s)


def gen_cnp(b, fem):
    sx = (2 if fem else 1) if b.year < 2000 else (6 if fem else 5)
    s = f"{sx}{b.year % 100:02d}{b.month:02d}{b.day:02d}{R.randint(1, 46):02d}{R.randint(1, 999):03d}"
    return s + ro_cnp.calc_check_digit(s)


def gen_pnr(b, fem):
    base = f"{b.year % 100:02d}{b.month:02d}{b.day:02d}" + d(2) + str(R.choice([0, 2, 4, 6, 8] if fem else [1, 3, 5, 7, 9]))
    c = luhn.calc_check_digit(base)
    if R.random() < 0.25:
        return f"{b.year}{base[2:6]}-{base[6:]}{c}"
    if R.random() < 0.2:
        return base + c
    return f"{base[:6]}-{base[6:]}{c}"


def gen_rc(b, fem):
    while True:
        m = b.month + (50 if fem else 0)
        base = f"{b.year % 100:02d}{m:02d}{b.day:02d}" + d(3)
        c = int(base) % 11
        if c == 10:
            continue
        s = base + str(c)
        out = s[:6] + "/" + s[6:] if R.random() < 0.8 else s
        if cz_rc.is_valid(out):
            return out


def gen_be_nn(b, fem):
    ser = R.randrange(2 if fem else 1, 998, 2)
    base = f"{b.year % 100:02d}{b.month:02d}{b.day:02d}{ser:03d}"
    chk = 97 - (int(("2" if b.year >= 2000 else "") + base) % 97)
    s = base + f"{chk:02d}"
    return f"{s[:2]}.{s[2:4]}.{s[4:6]}-{s[6:9]}.{s[9:]}" if R.random() < 0.7 else s


def gen_pps():
    while True:
        b = d(7)
        for L in "ABCDEFGHIJKLMNOPQRSTUVW":
            if ie_pps.is_valid(b + L):
                return b + L


def gen_ee(b, fem):
    g = (4 if fem else 3) if b.year < 2000 else (6 if fem else 5)
    s = f"{g}{b.year % 100:02d}{b.month:02d}{b.day:02d}" + d(3)
    return s + ee_ik.calc_check_digit(s + "0")


def gen_lt(b, fem):
    g = (4 if fem else 3) if b.year < 2000 else (6 if fem else 5)
    s = f"{g}{b.year % 100:02d}{b.month:02d}{b.day:02d}" + d(3)
    return s + lt_asmens.calc_check_digit(s + "0")


def gen_sk_dph():
    while True:
        s = "SK" + R.choice("123456789") + d(9)
        if sk_dph.is_valid(s):
            return s


IBAN_BBAN = {
    "DE": lambda: d(18),
    "SE": lambda: d(20),
    "RO": lambda: R.choice(["BTRL", "RNCB", "BRDE", "INGB", "BACX"]) + d(16),
    "SK": lambda: R.choice(["0200", "0900", "1100", "7500", "5600"]) + d(16),
    "LT": lambda: R.choice(["73000", "70440", "72900", "40100"]) + d(11),
    "EE": lambda: R.choice(["22", "10", "77", "42"]) + d(14),
    "IT": lambda: up(1) + R.choice(["03069", "02008", "05034", "01030"]) + d(5) + d(12),
}


def gen_iban(cc, fmt_p=0.5):
    for _ in range(100):
        bban = IBAN_BBAN[cc]()
        num = cc + std_iban.calc_check_digits(cc + "00" + bban) + bban
        if std_iban.is_valid(num):
            return std_iban.format(num) if R.random() < fmt_p else num
    raise RuntimeError("iban " + cc)


def gen_card():
    k = R.random()
    if k < 0.5:
        pre, L = "4" + d(5), 16
    elif k < 0.85:
        pre, L = str(R.randint(51, 55)) + d(4), 16
    else:
        pre, L = R.choice(["34", "37"]) + d(4), 15
    body = pre + d(L - 1 - len(pre))
    n = body + luhn.calc_check_digit(body)
    f = R.random()
    if L == 15:
        return f"{n[:4]} {n[4:10]} {n[10:]}" if f < 0.5 else n
    if f < 0.45:
        return " ".join(n[i:i + 4] for i in range(0, 16, 4))
    if f < 0.6:
        return "-".join(n[i:i + 4] for i in range(0, 16, 4))
    return n


def gen_imei():
    body = R.choice(["35", "86", "01", "99"]) + d(12)
    return body + luhn.calc_check_digit(body)


def gen_ean(prefix):
    b = prefix + d(12 - len(prefix))
    return b + std_ean.calc_check_digit(b)


def gen_isbn13():
    b = "978963" + d(6)
    return b + std_ean.calc_check_digit(b)


def mac():
    return ":".join(f"{R.randint(0, 255):02x}" for _ in range(6))


def latlon(lat, lon, spread=0.08):
    return round(lat + R.uniform(-spread, spread), 6), round(lon + R.uniform(-spread, spread), 6)


def free(p_empty, nopd, pd_, ctx, p_pd=0.5):
    """Free-text value: empty, a note without personal data, or one with personal data."""
    if R.random() < p_empty:
        return None
    if R.random() < p_pd:
        return R.choice(pd_).format(**ctx())
    return R.choice(nopd)


def nrows():
    return R.randint(150, 250)


# ================================================================== TABLES
def t01_telco():
    f = fk("it_IT")
    # it_IT city list order is not stable across interpreter runs -> sort it for reproducibility
    IT_CITIES = sorted({c for pr in f.providers if hasattr(pr, "cities") for c in pr.cities})
    rows = []
    piani = ["Giga 100 5G", "Smart 50", "Unlimited Pro", "Senior Easy", "Young 150 Giga", "Fibra+Mobile Combo"]
    nopd = ["Cliente richiede portabilità da altro operatore", "Reclamo per addebito roaming, inoltrato al backoffice",
            "Sospensione per mancato pagamento fattura", "Upgrade piano proposto, cliente ci pensa",
            "Sostituzione SIM per smarrimento", "Richiesta disattivazione servizi a pagamento",
            "Copertura scarsa in zona, aperto ticket rete"]
    pd_ = ["Richiamare il sig. {sur} al {ph} dopo le 18", "Contatto alternativo: {em}",
           "Delega al coniuge {n2} per la gestione del contratto",
           "Cliente ricoverata in ospedale (intervento al cuore), chiede sospensione temporanea",
           "Il figlio {n2} chiama per conto del padre, numero {ph}",
           "Cliente invalido civile al 100%, applicata agevolazione",
           "Cambio intestatario a favore di {n2}, CF {cf2}"]
    for _ in range(nrows()):
        fn, ln, fem = person("it_IT")
        b = birth(18, 90)

        def ctx():
            a, bb, fe = person("it_IT")
            bd = birth(20, 80)
            return dict(sur=ln, ph=phone("IT"), em=f.free_email(), n2=f"{a} {bb}", cf2=gen_cf(a, bb, bd, fe))
        rows.append({
            "id_abbonato": str(R.randint(10000000, 99999999)),
            "nome": fn,
            "cognome": ln,
            "codice_fiscale": maybe(gen_cf(fn, ln, b, fem), 0.03),
            "data_nascita": b.strftime("%d/%m/%Y"),
            "sesso": "F" if fem else "M",
            "indirizzo": f.street_address(),
            "cap": f.postcode(),
            "comune": R.choice(IT_CITIES),
            "cellulare": phone("IT"),
            "rif_disp": maybe(gen_imei(), 0.1),
            "piano_tariffario": R.choice(piani),
            "canone_mensile": dec(R.choice([7.99, 9.99, 12.99, 14.99, 19.99, 29.99])),
            "data_attivazione": rdate(dt.date(2018, 1, 1), dt.date(2026, 10, 30)).isoformat(),
            "codice_contratto": f"CTR-{R.randint(2018, 2026)}-{d(7)}",
            "stato": R.choice(["ATTIVO"] * 6 + ["SOSPESO", "CESSATO", "IN PORTABILITA"]),
            "note_operatore": free(0.55, nopd, pd_, ctx, 0.5),
        })
    df = pd.DataFrame(rows)
    df.to_csv(DATA / "abbonati_mobile_2026.csv", sep=";", index=False, encoding="utf-8-sig")
    VALIDATIONS.append(("it.codicefiscale", codicefiscale.is_valid, df["codice_fiscale"].dropna().tolist()))
    VALIDATIONS.append(("imei(luhn)", luhn.is_valid, df["rif_disp"].dropna().tolist()))
    L = {"id_abbonato": "customer_id", "nome": "person_name", "cognome": "person_name", "codice_fiscale": "national_id",
         "data_nascita": "date_of_birth", "sesso": "gender", "indirizzo": "postal_address", "cap": "postal_code",
         "comune": "city", "cellulare": "phone", "rif_disp": "device_id", "piano_tariffario": None,
         "canone_mensile": None, "data_attivazione": None, "codice_contratto": None, "stato": None,
         "note_operatore": "free_text"}
    register("abbonati_mobile_2026.csv", df.columns, L,
             f"abbonati_mobile_2026.csv | telecom mobile subscribers (IT) | Italian | {len(df)} rows / {len(df.columns)} cols | ';' delimiter, UTF-8 BOM, decimal comma, device column with uninformative name, operator notes partly personal")


def t02_energy():
    f = fk("de_DE")
    rows = []
    for _ in range(nrows()):
        fn, ln, fem = person("de_DE")
        rows.append({
            "Kundennummer": str(R.randint(400000000, 499999999)),
            "Anrede": ("Frau" if fem else "Herr") if R.random() > 0.03 else "Divers",
            "Vorname": fn,
            "Nachname": ln,
            "Straße_Hausnr": f.street_address(),
            "PLZ": f.postcode(),
            "Ort": f.city(),
            "Telefon": maybe(phone("DE"), 0.2),
            "Zählernummer": "1" + R.choice(["EMH", "ESY", "ITF", "LOG"]) + "00" + d(8),
            "Zählerstand_kWh": dec(R.uniform(1000, 60000), True)[:-1],
            "Ablesedatum": rdate(dt.date(2025, 12, 1), dt.date(2026, 2, 15)).strftime("%d.%m.%Y"),
            "Tarif": R.choice(["Grundversorgung", "ÖkoStrom Plus 24", "Wärmepumpe Komfort", "Strom Fix 12", "Heizstrom NT"]),
            "Abschlag_EUR": dec(R.choice([45, 58, 63, 72, 89, 104, 120, 151])),
            "IBAN": maybe(gen_iban("DE"), 0.15),
            "Netzbetreiber": R.choice(["Stromnetz Berlin GmbH", "Netze BW GmbH", "Bayernwerk Netz GmbH", "Westnetz GmbH",
                                       "Avacon Netz GmbH", "SachsenNetze GmbH"]),
        })
    df = pd.DataFrame(rows)
    df.to_csv(DATA / "stromkunden_export.csv", sep=";", index=False)
    VALIDATIONS.append(("iban DE", std_iban.is_valid, df["IBAN"].dropna().tolist()))
    L = {"Kundennummer": "customer_id", "Anrede": "gender", "Vorname": "person_name", "Nachname": "person_name",
         "Straße_Hausnr": "postal_address", "PLZ": "postal_code", "Ort": "city", "Telefon": "phone",
         "Zählernummer": None, "Zählerstand_kWh": None, "Ablesedatum": None, "Tarif": None, "Abschlag_EUR": None,
         "IBAN": "iban", "Netzbetreiber": None}
    register("stromkunden_export.csv", df.columns, L,
             f"stromkunden_export.csv | energy utility household customers (DE) | German | {len(df)} rows / {len(df.columns)} cols | ';' delimiter, decimal comma, salutation encodes gender, meter numbers are non-personal")


def t03_smartmeter():
    cities = [(52.0907, 5.1214, "Utrecht"), (52.3676, 4.9041, "Amsterdam"), (51.9244, 4.4777, "Rotterdam"),
              (51.4416, 5.4697, "Eindhoven"), (53.2194, 6.5665, "Groningen")]
    n = nrows()
    path = DATA / "slimme_meter_metingen.jsonl"
    accounts = [f"KL{d(8)}" for _ in range(60)]
    homes = {}
    for a in accounts:
        c = R.choice(cities)
        lat, lon = latlon(c[0], c[1])
        homes[a] = dict(mac=mac(), ip=fk("nl_NL").ipv4_public(), lat=lat, lon=lon, city=c[2],
                        serial="E0051" + d(11), type=R.choice(["Kaifa MA105", "Landis+Gyr E350", "Iskra AM550", "Sagemcom T211"]))
    with open(path, "w", encoding="utf-8") as fh:
        for i in range(n):
            a = R.choice(accounts)
            h = homes[a]
            rec = {
                "meting_id": f"M{20260000000 + i * 7 + R.randint(0, 6)}",
                "tijdstip": rdt(dt.date(2026, 10, 1), dt.date(2026, 10, 31)).strftime("%Y-%m-%dT%H:%M:%S+01:00"),
                "meter": {"serienummer": h["serial"], "type": h["type"], "firmware": R.choice(["v4.2.1", "v5.0.3", "v5.0.4"])},
                "waarden": {"kwh": round(R.uniform(0.05, 3.2), 3), "spanning_v": round(R.gauss(230, 2.5), 1)},
                "gateway": {"mac": h["mac"], "ip": h["ip"]},
                "huishouden": {"klantnummer": a, "locatie": {"lat": h["lat"], "lon": h["lon"]}},
                "onderstation": f"OS {h['city']}-{R.choice(['Noord', 'Zuid', 'Oost', 'West'])}",
            }
            if R.random() < 0.08:
                del rec["gateway"]["ip"]
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    L = {"meting_id": None, "tijdstip": None, "meter.serienummer": None, "meter.type": None, "meter.firmware": None,
         "waarden.kwh": None, "waarden.spanning_v": None, "gateway.mac": "device_id", "gateway.ip": "ip_address",
         "huishouden.klantnummer": "customer_id", "huishouden.locatie.lat": "geolocation",
         "huishouden.locatie.lon": "geolocation", "onderstation": None}
    register("slimme_meter_metingen.jsonl", L.keys(), L,
             f"slimme_meter_metingen.jsonl | IoT smart-meter readings (NL) | Dutch | {n} rows / {len(L)} cols | JSONL with 2-level nesting (dot paths), meter serials non-personal, home gateway MAC/IP and home coordinates personal")


def t04_rental():
    f = fk("es_ES")
    rows = []
    oficinas = ["Aeropuerto Madrid-Barajas T4", "Barcelona Sants Estación", "Málaga Aeropuerto", "Valencia Joaquín Sorolla",
                "Sevilla Santa Justa", "Palma de Mallorca Aeropuerto", "Bilbao Centro, C/ Gran Vía 45"]
    grupos = ["A - Fiat 500 o similar", "B - Seat Ibiza o similar", "C - VW Golf o similar", "D - Skoda Octavia Combi",
              "F - SUV Nissan Qashqai", "H - Furgoneta 9 plazas"]
    notas_veh = ["Rayón leve parachoques delantero", "Depósito lleno", "Neumático trasero desgastado",
                 "Limpieza interior pendiente", "Golpe retrovisor izquierdo", "Sin incidencias", "Nivel de AdBlue bajo"]
    nopd = ["Solicita silla infantil grupo 1", "Entrega fuera de horario autorizada", "Pago con tarjeta de débito, depósito ampliado",
            "Cliente rechaza seguro a todo riesgo", "Upgrade gratuito por falta de flota", "Devolución en otra oficina"]
    pd_ = ["Conductor adicional: {n2} (DNI {dni2})", "Llamar al {ph} si hay retraso en la devolución",
           "Cliente con movilidad reducida, necesita coche automático y adaptado",
           "Enviar factura a {em}", "Reserva hecha por su hija {n2}, tel. {ph}",
           "Multa de tráfico recibida, reenviada a {n2}"]
    for i in range(nrows()):
        fn, ln, fem = person("es_ES")
        ln2 = f.last_name()
        b = birth(21, 80)
        spanish = R.random() < 0.75
        doc = gen_dni() if spanish else gen_nie()
        start = rdt(dt.date(2026, 3, 1), dt.date(2026, 10, 20))

        def ctx():
            a, bb, _ = person("es_ES")
            return dict(n2=f"{a} {bb}", dni2=gen_dni(), ph=phone("ES"), em=f.free_email())
        rows.append({
            "num_reserva": f"RES{start:%y%m}{d(5)}",
            "cliente": f"{fn} {ln} {ln2}" if R.random() < 0.6 else f"{ln.upper()} {ln2.upper()}, {fn}",
            "dni_nie": doc,
            "permiso_conducir": doc if (spanish and R.random() < 0.85) else (up(2) + d(6) if R.random() < 0.5 else gen_dni()),
            "edad_conductor": age_of(b, start.date()),
            "email": maybe(f.free_email() if R.random() < 0.8 else f.email(), 0.07),
            "telefono": phone("ES"),
            "oficina_recogida": R.choice(oficinas),
            "fecha_recogida": start.strftime("%Y-%m-%d %H:%M"),
            "fecha_devolucion": (start + dt.timedelta(days=R.randint(1, 14), hours=R.randint(-3, 3))).strftime("%Y-%m-%d %H:%M"),
            "grupo_vehiculo": R.choice(grupos),
            "importe_total": dec(R.uniform(60, 1400), False),
            "tarjeta": gen_card(),
            "notas_vehiculo": maybe(R.choice(notas_veh), 0.35),
            "observaciones": free(0.55, nopd, pd_, ctx, 0.55),
        })
    df = pd.DataFrame(rows)
    df.to_csv(DATA / "reservas_alquiler_coches.csv", sep=",", index=False)
    ids = df["dni_nie"].tolist()
    VALIDATIONS.append(("es.dni/nie", lambda x: es_dni.is_valid(x) or es_nie.is_valid(x), ids))
    VALIDATIONS.append(("payment card luhn", lambda x: luhn.is_valid(x.replace(" ", "").replace("-", "")), df["tarjeta"].tolist()))
    L = {"num_reserva": None, "cliente": "person_name", "dni_nie": "national_id", "permiso_conducir": "national_id",
         "edad_conductor": "age", "email": "email", "telefono": "phone", "oficina_recogida": None, "fecha_recogida": None,
         "fecha_devolucion": None, "grupo_vehiculo": None, "importe_total": None, "tarjeta": "payment_card",
         "notas_vehiculo": None, "observaciones": "free_text"}
    register("reservas_alquiler_coches.csv", df.columns, L,
             f"reservas_alquiler_coches.csv | car rental bookings (ES) | Spanish | {len(df)} rows / {len(df.columns)} cols | DNI and NIE mixed, two free-text columns: vehicle-condition notes (no personal data) vs customer remarks (personal)")


def t05_hotel():
    f = fk("fr_FR")
    hotels = [("Hôtel du Vieux Port", "Marseille", "+33 4 91 55 12 00"), ("Le Grand Hôtel Bellecour", "Lyon", "04 78 37 40 21"),
              ("Hôtel Rivage Atlantique", "La Rochelle", "+33 5 46 41 77 90"), ("Résidence Montmartre", "Paris", "01 42 58 63 10"),
              ("Hôtel des Alpes", "Annecy", "+33 4 50 45 03 32"), ("Ibis Styles Gare", "Lille", "03 20 06 15 88")]
    nats = [("française", "FR"), ("belge", "BE"), ("italienne", "IT"), ("allemande", "DE"), ("espagnole", "ES"),
            ("britannique", "GB"), ("suisse", "CH"), ("néerlandaise", "NL"), ("marocaine", "MA")]
    nopd = ["Lit bébé", "Chambre calme, étage élevé", "Arrivée tardive vers 23h", "Parking souterrain réservé",
            "Petit-déjeuner en chambre", "Vue mer si possible", "Facture au nom de la société"]
    pd_ = ["Allergie sévère aux arachides — prévenir le restaurant", "Accompagné de {n2}, anniversaire de mariage",
           "Contacter sa fille {n2} au {ph} en cas d'urgence", "Fauteuil roulant, chambre PMR obligatoire",
           "Client diabétique, prévoir réfrigérateur pour insuline", "Envoyer la confirmation à {em}"]
    recs = []
    n = nrows()
    for i in range(n):
        fn, ln, fem = person("fr_FR")
        nat = R.choice(nats) if R.random() < 0.45 else nats[0]
        h = R.choice(hotels)
        arr = rdate(dt.date(2026, 4, 1), dt.date(2026, 12, 20))

        def ctx():
            a, bb, _ = person("fr_FR")
            return dict(n2=f"{a} {bb}", ph=phone("FR"), em=f.free_email())
        recs.append({
            "reservation": f"HB-{arr:%Y}-{100000 + i * 3}",
            "hotel": {"nom": h[0], "ville": h[1], "telephone": h[2]},
            "client": {
                "nom": ln.upper() if R.random() < 0.5 else ln,
                "prenom": fn,
                "email": f.free_email() if R.random() > 0.1 else None,
                "telephone": phone("FR"),
                "nationalite": nat[0],
                "passeport": (f"{R.randint(10, 26)}{up(2)}{d(5)}" if nat[1] == "FR" else nat[1][0] + d(7) + up(1)) if R.random() > 0.3 else None,
                "date_naissance": birth(18, 85).isoformat(),
            },
            "sejour": {"arrivee": arr.isoformat(), "depart": (arr + dt.timedelta(days=R.randint(1, 9))).isoformat(),
                       "chambre": str(R.choice([1, 2, 3, 4, 5])) + f"{R.randint(1, 28):02d}",
                       "tarif_nuit": round(R.uniform(69, 340), 2)},
            "demandes_speciales": free(0.5, nopd, pd_, ctx, 0.5),
        })
    with open(DATA / "reservations_hotels.json", "w", encoding="utf-8") as fh:
        json.dump(recs, fh, ensure_ascii=False, indent=1)
    L = {"reservation": None, "hotel.nom": None, "hotel.ville": None, "hotel.telephone": None,
         "client.nom": "person_name", "client.prenom": "person_name", "client.email": "email",
         "client.telephone": "phone", "client.nationalite": "nationality", "client.passeport": "national_id",
         "client.date_naissance": "date_of_birth", "sejour.arrivee": None, "sejour.depart": None,
         "sejour.chambre": None, "sejour.tarif_nuit": None, "demandes_speciales": "free_text"}
    register("reservations_hotels.json", L.keys(), L,
             f"reservations_hotels.json | hotel bookings (FR) | French | {n} rows / {len(L)} cols | JSON array with nested objects; hotel city/phone are business data, guest phone/passport personal; special requests contain health info")


def t06_dental():
    f = fk("pl_PL")
    rows = []
    lekarze = []
    for _ in range(6):
        a, bb, _ = person("pl_PL")
        lekarze.append(f"lek. dent. {a} {bb}")
    procs = [("Wypełnienie kompozytowe ząb 36", "K02.1"), ("Ekstrakcja zęba 48", "K01.1"), ("Leczenie kanałowe ząb 21", "K04.0"),
             ("Skaling i piaskowanie", "K03.6"), ("Korona porcelanowa ząb 14", "K08.1"), ("Przegląd kontrolny", "Z01.2"),
             ("Leczenie zapalenia dziąseł", "K05.1")]
    nopd = ["Kontrola za 6 miesięcy", "Płatność przelewem", "Wizyta przełożona przez gabinet", "Zalecono nitkowanie"]
    pd_ = ["Przypomnienie SMS na {ph}", "Skierowanie od dr {n2}", "Ciąża - II trymestr, bez RTG",
           "Opiekun prawny: {n2}, tel. {ph}", "Pacjent po zawale, konsultacja z kardiologiem", "Wynik RTG wysłany na {em}"]
    for i in range(nrows()):
        fn, ln, fem = person("pl_PL")
        b = birth(3, 90)
        p = R.choice(procs)
        vis = rdate(dt.date(2026, 1, 5), dt.date(2026, 11, 15))

        def ctx():
            a, bb, _ = person("pl_PL")
            return dict(ph=phone("PL"), n2=f"{a} {bb}", em=f.free_email())
        rows.append({
            "nr_pacjenta": f"P{R.randint(1000, 9999)}",
            "imie_nazwisko": f"{fn} {ln}",
            "PESEL": gen_pesel(b, fem),
            "data_ur": dt.datetime(b.year, b.month, b.day),
            "plec": "K" if fem else "M",
            "tel": maybe(phone("PL"), 0.08),
            "adres": f"{f.street_address()}, {f.postcode()} {f.city()}",
            "nr_wizyty": f"W/{vis:%Y}/{i + 1:05d}",
            "data_wizyty": dt.datetime(vis.year, vis.month, vis.day, R.choice([8, 9, 10, 11, 13, 14, 15, 16]), R.choice([0, 30])),
            "procedura": p[0],
            "kod_ICD10": p[1],
            "lekarz": R.choice(lekarze),
            "gabinet": f"Gabinet {R.randint(1, 4)}",
            "kwota_PLN": round(R.choice([0, 150, 220, 350, 480, 900, 1800]) * 1.0, 2),
            "forma_platnosci": R.choice(["gotówka", "karta", "przelew", "NFZ"]),
            "nr_faktury": f"FV/{vis:%m}/{vis:%Y}/{R.randint(1, 999):03d}",
            "field_7": R.choice(["penicylina", "lateks", "lidokaina", "brak", "brak", "brak", None, "ibuprofen", "jod"]),
            "uwagi": free(0.5, nopd, pd_, ctx, 0.55),
        })
    df = pd.DataFrame(rows)
    with pd.ExcelWriter(DATA / "gabinet_stomatologiczny.xlsx", engine="openpyxl") as xw:
        df.to_excel(xw, sheet_name="Pacjenci", index=False)
    VALIDATIONS.append(("pl.pesel", pl_pesel.is_valid, df["PESEL"].tolist()))
    L = {"nr_pacjenta": "customer_id", "imie_nazwisko": "person_name", "PESEL": "national_id", "data_ur": "date_of_birth",
         "plec": "gender", "tel": "phone", "adres": "postal_address", "nr_wizyty": None, "data_wizyty": None,
         "procedura": "health", "kod_ICD10": "health", "lekarz": "person_name", "gabinet": None, "kwota_PLN": None,
         "forma_platnosci": None, "nr_faktury": None, "field_7": "health", "uwagi": "free_text"}
    register("gabinet_stomatologiczny.xlsx::Pacjenci", df.columns, L,
             f"gabinet_stomatologiczny.xlsx::Pacjenci | dental clinic patients & visits (PL) | Polish | {len(df)} rows / {len(df.columns)} cols | Excel sheet, real date cells; treating dentist name is personal; allergy column has uninformative name")


def t07_pharmacy():
    f = fk("pt_PT")
    lojas = [("Farmácia Central do Porto", "Rua de Santa Catarina 112, 4000-442 Porto"),
             ("Farmácia Avenida", "Av. da Liberdade 210, 1250-147 Lisboa"),
             ("Farmácia São João", "Praça 8 de Maio 15, 3000-300 Coimbra"),
             ("Farmácia Marítima", "Rua Direita 44, 8000-123 Faro")]
    cats = ["Cosmética", "Higiene oral", "Suplementos", "Puericultura", "Medicamento sujeito a receita", "Ortopedia"]
    meds = ["Metformina 850 mg", "Atorvastatina 20 mg", "Levotiroxina 50 µg", "Sertralina 50 mg", "Salbutamol inalador",
            "Insulina glargina", "Amoxicilina 1 g", "Contracetivo oral (levonorgestrel)", "Omeprazol 20 mg"]
    members = []
    for _ in range(90):
        fn, ln, fem = person("pt_PT")
        cp = f.postcode()
        members.append(dict(card=f"FC{d(9)}", name=f"{fn} {ln} {f.last_name()}", nif=gen_pt_nif(),
                            ph=phone("PT"), em=maybe(f.free_email(), 0.15), cp=cp, loc=f.city()))
    rows = []
    for _ in range(nrows()):
        m = R.choice(members)
        lj = R.choice(lojas)
        cat = R.choice(cats)
        rows.append({
            "n_cartao": m["card"],
            "nome_completo": m["name"],
            "nif": maybe(m["nif"], 0.1),
            "telemovel": m["ph"],
            "email": m["em"],
            "codigo_postal": m["cp"],
            "localidade": m["loc"],
            "data_compra": rdt(dt.date(2026, 1, 1), dt.date(2026, 11, 10)).strftime("%d-%m-%Y %H:%M"),
            "loja": lj[0],
            "morada_loja": lj[1],
            "ean": gen_ean("560"),
            "categoria": cat,
            "medicamento_receitado": R.choice(meds) if cat == "Medicamento sujeito a receita" else None,
            "preco_unit": dec(R.uniform(1.5, 65)),
            "pontos": R.randint(0, 120),
        })
    df = pd.DataFrame(rows)
    df.to_csv(DATA / "farmacia_cartao_cliente.csv", sep=";", index=False)
    VALIDATIONS.append(("pt.nif", pt_nif.is_valid, df["nif"].dropna().tolist()))
    VALIDATIONS.append(("ean13", std_ean.is_valid, df["ean"].tolist()))
    L = {"n_cartao": "customer_id", "nome_completo": "person_name", "nif": "national_id", "telemovel": "phone",
         "email": "email", "codigo_postal": "postal_code", "localidade": "city", "data_compra": None, "loja": None,
         "morada_loja": None, "ean": None, "categoria": None, "medicamento_receitado": "health", "preco_unit": None,
         "pontos": None}
    register("farmacia_cartao_cliente.csv", df.columns, L,
             f"farmacia_cartao_cliente.csv | pharmacy loyalty-card purchases (PT) | Portuguese | {len(df)} rows / {len(df.columns)} cols | ';' delimiter; store address non-personal; prescribed medicine sparse (health); EAN codes")


def t08_municipality():
    f = fk("nl_BE")
    soorten = ["Identiteitskaart", "Reispas", "Rijbewijs", "Bewonerskaart parkeren", "Uittreksel bevolkingsregister",
               "Adreswijziging", "Huwelijksaangifte"]
    staten = ["ongehuwd", "gehuwd", "wettelijk samenwonend", "gescheiden", "weduwe/weduwnaar"]
    nats = ["Belg", "Belg", "Belg", "Belg", "Nederlander", "Marokkaan", "Turk", "Pool", "Roemeen", "Fransman"]
    staff = [f"BEH-{R.randint(10, 99):03d}" for _ in range(8)]
    rows = []
    for i in range(nrows()):
        fn, ln, fem = person("nl_BE")
        b = birth(16, 92)
        s = R.choice(soorten)
        rows.append({
            "dossiernummer": f"2026/{R.randint(10000, 99999)}",
            "rijksregisternummer": gen_be_nn(b, fem),
            "naam": f"{ln}, {fn}",
            "geboortedatum": b.strftime("%d/%m/%Y"),
            "adres": f.street_address(),
            "postcode": f.postcode(),
            "gemeente": f.city(),
            "burgerlijke_staat": maybe(R.choice(staten), 0.1),
            "nationaliteit": R.choice(nats),
            "soort_aanvraag": s,
            "nummerplaat": f"{R.randint(1, 2)}-{up(3)}-{d(3)}" if s == "Bewonerskaart parkeren" else None,
            "behandelaar": R.choice(staff),
            "status": R.choice(["ontvangen", "in behandeling", "afgerond", "afgerond", "geweigerd"]),
            "retributie_eur": dec(R.choice([0, 5, 15, 25, 30.4, 71, 88]), False),
            "aanvraagdatum": rdate(dt.date(2026, 1, 1), dt.date(2026, 11, 14)).isoformat(),
        })
    df = pd.DataFrame(rows)
    df.to_csv(DATA / "loket_aanvragen.tsv", sep="\t", index=False)
    VALIDATIONS.append(("be.nn", be_nn.is_valid, df["rijksregisternummer"].tolist()))
    L = {"dossiernummer": None, "rijksregisternummer": "national_id", "naam": "person_name", "geboortedatum": "date_of_birth",
         "adres": "postal_address", "postcode": "postal_code", "gemeente": "city", "burgerlijke_staat": "marital_status",
         "nationaliteit": "nationality", "soort_aanvraag": None, "nummerplaat": "vehicle_plate", "behandelaar": "customer_id",
         "status": None, "retributie_eur": None, "aanvraagdatum": None}
    register("loket_aanvragen.tsv", df.columns, L,
             f"loket_aanvragen.tsv | municipal service-desk requests (BE/Flanders) | Dutch (Flemish) | {len(df)} rows / {len(df.columns)} cols | tab-separated; number plate sparse (only parking permits); case handler column holds staff codes")


def t09_admissions():
    f = fk("cs_CZ")
    fak = [("Přírodovědecká fakulta", "Biologie"), ("Filozofická fakulta", "Psychologie"), ("Fakulta informatiky", "Umělá inteligence"),
           ("Ekonomicko-správní fakulta", "Finance"), ("Lékařská fakulta", "Všeobecné lékařství"), ("Právnická fakulta", "Právo")]
    nats = ["česká"] * 6 + ["slovenská", "slovenská", "ukrajinská", "vietnamská", "polská"]
    rows = []
    for i in range(nrows()):
        fn, ln, fem = person("cs_CZ")
        b = birth(18, 30)
        fk_ = R.choice(fak)
        rows.append({
            "cislo_prihlasky": f"{R.randint(100000, 999999)}",
            "id_uchazece": f"U26{d(6)}",
            "jmeno": fn,
            "prijmeni": ln,
            "rodne_cislo": gen_rc(b, fem),
            "datum_narozeni": f"{b.day}. {b.month}. {b.year}",
            "pohlavi": "žena" if fem else "muž",
            "statni_obcanstvi": R.choice(nats),
            "email": f.free_email(),
            "nejvyssi_vzdelani": R.choice(["SŠ s maturitou"] * 5 + ["VOŠ", "Bc.", "Mgr."]),
            "specialni_potreby": maybe(R.choice(["dyslexie", "zrakové postižení", "sluchové postižení", "ADHD", "pohybové omezení – vozík"]), 0.85),
            "fakulta": fk_[0],
            "studijni_program": fk_[1],
            "pole_12": R.choice([0, 690, 690, 690, 850]),
            "stav_prihlasky": R.choice(["podána", "zaplacena", "přijat", "nepřijat", "přijat"]),
        })
    df = pd.DataFrame(rows)
    df.to_csv(DATA / "prijimaci_rizeni_2026.csv", sep=",", index=False)
    VALIDATIONS.append(("cz.rc", cz_rc.is_valid, df["rodne_cislo"].tolist()))
    L = {"cislo_prihlasky": None, "id_uchazece": "customer_id", "jmeno": "person_name", "prijmeni": "person_name",
         "rodne_cislo": "national_id", "datum_narozeni": "date_of_birth", "pohlavi": "gender",
         "statni_obcanstvi": "nationality", "email": "email", "nejvyssi_vzdelani": "education",
         "specialni_potreby": "health", "fakulta": None, "studijni_program": None, "pole_12": None,
         "stav_prihlasky": None}
    register("prijimaci_rizeni_2026.csv", df.columns, L,
             f"prijimaci_rizeni_2026.csv | university admissions applicants (CZ) | Czech | {len(df)} rows / {len(df.columns)} cols | birth numbers with/without slash; disability column very sparse; fee column has uninformative name")


def t10_recruitment():
    f = fk("en_IE")
    clients = [("Glenbrook Pharma Ltd", "careers@glenbrookpharma.ie"), ("Liffey Analytics", "jobs@liffeyanalytics.com"),
               ("Shannon Aerospace Services", "hr@shannonaero.ie"), ("Corrib Fintech DAC", "talent@corribfintech.ie"),
               ("Atlantic Data Centres", "recruitment@atlanticdc.eu")]
    titles = ["Data Analyst", "Software Engineer", "Registered Nurse", "Accountant", "Warehouse Supervisor", "Marketing Executive",
              "Lab Technician", "Customer Success Manager", "Electrician", "Unemployed"]
    quals = ["Leaving Certificate", "QQI Level 6", "BSc Computer Science", "BA Business", "MSc Data Science", "PhD Chemistry", "ACCA"]
    nats = ["Irish"] * 5 + ["Polish", "Brazilian", "Indian", "Lithuanian", "British", "Romanian", "Pakistani"]
    nopd = ["Salary negotiable", "No-show on first interview", "Strong SQL, weak on cloud", "Withdrawn - accepted other offer",
            "Good culture fit", "Needs visa sponsorship info from client"]
    pd_ = ["Call back on {ph} after 5pm", "Referred by {n2} ({em})", "Disclosed ADHD diagnosis, requests extra time at assessment",
           "Partner {n2} relocating to Cork, wants hybrid", "On maternity leave until March", "Personal email {em}, do not use work address"]
    rows = []
    for i in range(nrows()):
        fn, ln, fem = person("en_IE")
        b = birth(19, 64)
        c = R.choice(clients)

        def ctx():
            a, bb, _ = person("en_IE")
            return dict(ph=phone("IE"), n2=f"{a} {bb}", em=f.free_email())
        rows.append({
            "candidate_id": f"CAND-{10000 + i * 13}",
            "full_name": f"{fn} {ln}",
            "email": f.free_email(),
            "mobile": phone("IE"),
            "pps_number": maybe(gen_pps(), 0.3),
            "dob": b.strftime("%d/%m/%Y"),
            "current_title": R.choice(titles),
            "highest_qualification": R.choice(quals),
            "expected_salary_eur": R.choice([32000, 38000, 45000, 52000, 60000, 72000, 85000, 95000]),
            "nationality": R.choice(nats),
            "vacancy_ref": f"VAC-{R.randint(2025, 2026)}-{R.randint(1, 180):04d}",
            "client_company": c[0],
            "client_contact": c[1],
            "interview_slot": rdt(dt.date(2026, 11, 20), dt.date(2026, 12, 19)).strftime("%Y-%m-%d %H:%M"),
            "stage": R.choice(["Sourced", "Screened", "Interview 1", "Interview 2", "Offer", "Rejected"]),
            "garda_vetting": R.choice(["Clear"] * 6 + ["Pending", "Not started", "Disclosure: drink-driving conviction 2018",
                                                       "Disclosure: theft (spent conviction) 2014"]),
            "recruiter_notes": free(0.45, nopd, pd_, ctx, 0.5),
        })
    df = pd.DataFrame(rows)
    df.to_csv(DATA / "candidates_pipeline.csv", sep=",", index=False)
    VALIDATIONS.append(("ie.pps", ie_pps.is_valid, df["pps_number"].dropna().tolist()))
    L = {"candidate_id": "customer_id", "full_name": "person_name", "email": "email", "mobile": "phone",
         "pps_number": "national_id", "dob": "date_of_birth", "current_title": "occupation",
         "highest_qualification": "education", "expected_salary_eur": "income", "nationality": "nationality",
         "vacancy_ref": None, "client_company": None, "client_contact": None, "interview_slot": None, "stage": None,
         "garda_vetting": "criminal", "recruiter_notes": "free_text"}
    register("candidates_pipeline.csv", df.columns, L,
             f"candidates_pipeline.csv | recruitment agency candidates (IE) | English | {len(df)} rows / {len(df.columns)} cols | client contact = generic company mailboxes (non-personal); vetting column holds criminal-record outcomes")


def t11_insurance():
    f = fk("ro_RO")
    places = [(44.4268, 26.1025), (46.7712, 23.6236), (45.7489, 21.2087), (47.1585, 27.6014), (45.6427, 25.5887), (44.1598, 28.6348)]
    counties = ["B", "CJ", "TM", "IS", "BV", "CT", "PH", "AG"]
    nopd = ["Grindină, mașină parcată în parcare deschisă", "Daună parcare, autor necunoscut", "Geam spart, furt radio",
            "Coliziune cu animal sălbatic pe DN1", "Copac căzut pe autoturism în timpul furtunii"]
    pd_ = ["Coliziune spate la semafor, celălalt șofer {n2}, tel {ph}", "Martor: {n2}, telefon {ph}",
           "Asiguratul a fost transportat la UPU cu fractură de claviculă", "Pasagera {n2} rănită ușor, internată 2 zile",
           "Constatare amiabilă semnată cu {n2}, CNP {cnp2}"]
    services = ["AutoService Carpați SRL", "Dacia Service Ploiești", "Euro Car Repair SRL", "Service Auto Dan & Fiii"]
    rows = []
    for i in range(nrows()):
        fn, ln, fem = person("ro_RO")
        b = birth(18, 85)
        pl = R.choice(places)
        la, lo = latlon(*pl, spread=0.1)
        cty = R.choice(counties)

        def ctx():
            a, bb, fe = person("ro_RO")
            return dict(n2=f"{a} {bb}", ph=phone("RO"), cnp2=gen_cnp(birth(20, 70), fe))
        rows.append({
            "nr_dosar": f"DA-{R.randint(2025, 2026)}-{d(6)}",
            "asigurat": f"{ln} {fn}" if R.random() < 0.6 else f"{fn} {ln}",
            "cnp": gen_cnp(b, fem),
            "telefon": maybe(phone("RO"), 0.1),
            "nr_inmatriculare": f"{cty} {R.randint(1, 99) if cty != 'B' else R.randint(1, 999):02d} {up(3)}" if R.random() < 0.8 else f"{cty}{R.randint(10, 99)}{up(3)}",
            "marca_model": R.choice(["Dacia Logan", "Dacia Duster", "VW Golf", "Renault Clio", "Skoda Octavia", "Ford Focus", "BMW 320d"]),
            "data_eveniment": rdate(dt.date(2025, 9, 1), dt.date(2026, 11, 1)).strftime("%d.%m.%Y"),
            "coordonate_gps": f"{la}, {lo}" if R.random() > 0.12 else None,
            "descriere": free(0.1, nopd, pd_, ctx, 0.45),
            "leziuni": R.choice(["fără"] * 5 + ["contuzii", "fractură antebraț stâng", "entorsă cervicală", "traumatism cranian ușor"]),
            "suma_estimata_ron": dec(R.uniform(800, 45000)),
            "service_partener": R.choice(services),
            "iban_despagubire": maybe(gen_iban("RO"), 0.2),
            "stare": R.choice(["deschis", "în evaluare", "aprobat", "plătit", "respins"]),
        })
    df = pd.DataFrame(rows)
    df.to_csv(DATA / "dosare_daune_auto.csv", sep=";", index=False)
    VALIDATIONS.append(("ro.cnp", ro_cnp.is_valid, df["cnp"].tolist()))
    VALIDATIONS.append(("iban RO", std_iban.is_valid, df["iban_despagubire"].dropna().tolist()))
    L = {"nr_dosar": None, "asigurat": "person_name", "cnp": "national_id", "telefon": "phone",
         "nr_inmatriculare": "vehicle_plate", "marca_model": None, "data_eveniment": None, "coordonate_gps": "geolocation",
         "descriere": "free_text", "leziuni": "health", "suma_estimata_ron": None, "service_partener": None,
         "iban_despagubire": "iban", "stare": None}
    register("dosare_daune_auto.csv", df.columns, L,
             f"dosare_daune_auto.csv | motor insurance claims (RO) | Romanian | {len(df)} rows / {len(df.columns)} cols | ';' delimiter; incident GPS as 'lat, lon' string; injuries column (health) mostly 'none'")


def t12_kyc():
    f = fk("sv_SE")
    yrken = ["sjuksköterska", "lärare", "mjukvaruutvecklare", "snickare", "ekonom", "pensionär", "student", "busschaufför", "läkare", "egenföretagare"]
    civil = ["ogift", "gift", "skild", "änka/änkling", "registrerad partner"]
    nats = ["svensk"] * 6 + ["finsk", "norsk", "polsk", "syrisk", "tysk", "dansk"]
    kontor = ["Stockholm City", "Göteborg Avenyn", "Malmö Triangeln", "Uppsala Centrum", "Digital"]
    rows = []
    for i in range(nrows()):
        fn, ln, fem = person("sv_SE")
        b = birth(18, 90)
        rows.append({
            "kundnr": f"{R.randint(1000000, 9999999)}",
            "namn": f"{fn} {ln}",
            "personnummer": gen_pnr(b, fem),
            "adress": f.street_address(),
            "postnr": f"{R.randint(100, 984)} {R.randint(0, 99):02d}",
            "ort": f.city(),
            "yrke": maybe(R.choice(yrken), 0.05),
            "arsinkomst_sek": R.choice([0, 180000, 240000, 310000, 385000, 450000, 520000, 690000, 1100000]),
            "civilstand": R.choice(civil),
            "medborgarskap": R.choice(nats),
            "kontonummer_iban": gen_iban("SE"),
            "riskklass": R.choice(["Låg", "Låg", "Medel", "Hög"]),
            "kontor": R.choice(kontor),
            "c3": R.choice(["SWEDSESS", "ESSESESS", "HANDSESS", "NDEASESS"]),
        })
    df = pd.DataFrame(rows)
    df.to_csv(DATA / "kyc_privatkunder.csv", sep=",", index=False)
    VALIDATIONS.append(("se.personnummer", se_pnr.is_valid, df["personnummer"].tolist()))
    VALIDATIONS.append(("iban SE", std_iban.is_valid, df["kontonummer_iban"].tolist()))
    L = {"kundnr": "customer_id", "namn": "person_name", "personnummer": "national_id", "adress": "postal_address",
         "postnr": "postal_code", "ort": "city", "yrke": "occupation", "arsinkomst_sek": "income",
         "civilstand": "marital_status", "medborgarskap": "nationality", "kontonummer_iban": "iban", "riskklass": None,
         "kontor": None, "c3": None}
    register("kyc_privatkunder.csv", df.columns, L,
             f"kyc_privatkunder.csv | bank KYC retail customers (SE) | Swedish | {len(df)} rows / {len(df.columns)} cols | personnummer in 10/12-digit and with/without hyphen; branch and BIC (uninformative name) are non-personal")


def t13_delivery():
    f = fk("el_GR")
    stores = [("Σουβλάκι Ο Θανάσης", "Μητροπόλεως 69, Αθήνα 10556", "210 3244705"),
              ("Pizza Fan Κηφισιά", "Λεωφ. Κηφισίας 238, Κηφισιά 14562", "+30 210 8011223"),
              ("Sushi Bar Θεσσαλονίκη", "Τσιμισκή 45, Θεσσαλονίκη 54623", "2310 222345"),
              ("Μπουγάτσα Μπαντής", "Παναγίας Φανερωμένης 33, Θεσσαλονίκη 54631", "2310 510355")]
    items = ["2x Πίτα γύρο χοιρινό, 1x Coca-Cola 330ml", "1x Pizza Margherita, 1x Σαλάτα Χωριάτικη", "12x Sushi mix, 1x Miso",
             "1x Μπουγάτσα κρέμα, 2x Φρέντο εσπρέσο", "3x Καλαμάκι κοτόπουλο, 1x Τζατζίκι", "1x Burger, 1x Πατάτες"]
    nopd = ["Χωρίς κρεμμύδι", "Αφήστε στην πόρτα", "Χωρίς μαχαιροπίρουνα", "Ρέστα από 50€", "Επιπλέον σάλτσα"]
    pd_ = ["Κουδούνι: {sur}, 3ος όροφος", "Καλέστε στο {ph} όταν φτάσετε", "Αλλεργία σε ξηρούς καρπούς - προσοχή!",
           "Παραλαβή από τον/την {n2}", "Είμαι κωφός, στείλτε SMS στο {ph}"]
    couriers = [f"DRV-{R.randint(1000, 9999)}" for _ in range(25)]
    rows = []
    for i in range(nrows()):
        fn, ln, fem = person("el_GR")
        s = R.choice(stores)
        base = (37.9838, 23.7275) if "Θεσσαλονίκη" not in s[1] else (40.6401, 22.9444)
        la, lo = latlon(*base, spread=0.05)

        def ctx():
            a, bb, _ = person("el_GR")
            return dict(sur=ln, ph=phone("GR"), n2=f"{a} {bb}")
        rows.append({
            "κωδικός_παραγγελίας": f"GR{R.randint(10**9, 10**10 - 1)}",
            "πελάτης": f"{fn} {ln}",
            "τηλέφωνο": phone("GR"),
            "διεύθυνση_παράδοσης": f.street_address(),
            "ΤΚ": f.postcode(),
            "gps_παράδοσης": f"{la},{lo}",
            "κατάστημα": s[0],
            "διεύθυνση_καταστήματος": s[1],
            "τηλ_καταστήματος": s[2],
            "είδη": R.choice(items),
            "σύνολο_€": dec(R.uniform(6, 48)),
            "ώρα_παραγγελίας": rdt(dt.date(2026, 10, 1), dt.date(2026, 11, 15)).strftime("%d/%m/%Y %H:%M"),
            "διανομέας_id": R.choice(couriers),
            "σχόλια": free(0.5, nopd, pd_, ctx, 0.5),
        })
    df = pd.DataFrame(rows)
    df.to_csv(DATA / "paraggelies_delivery.csv", sep=",", index=False)
    L = {"κωδικός_παραγγελίας": None, "πελάτης": "person_name", "τηλέφωνο": "phone", "διεύθυνση_παράδοσης": "postal_address",
         "ΤΚ": "postal_code", "gps_παράδοσης": "geolocation", "κατάστημα": None, "διεύθυνση_καταστήματος": None,
         "τηλ_καταστήματος": None, "είδη": None, "σύνολο_€": None, "ώρα_παραγγελίας": None,
         "διανομέας_id": "customer_id", "σχόλια": "free_text"}
    register("paraggelies_delivery.csv", df.columns, L,
             f"paraggelies_delivery.csv | food delivery orders (GR) | Greek (Greek-script headers/values) | {len(df)} rows / {len(df.columns)} cols | restaurant address/phone non-personal; courier IDs identify gig workers; order items free text without personal data")


def t14_elearning():
    f = fk("hu_HU")
    courses = [("PY-101", "Python alapok"), ("XL-220", "Excel haladó"), ("PM-310", "Projektmenedzsment a gyakorlatban"),
               ("GD-150", "Adatvédelem (GDPR) munkavállalóknak"), ("ML-400", "Gépi tanulás bevezető"), ("EN-B2", "Üzleti angol B2")]
    isbns = {c[0]: gen_isbn13() for c in courses}
    rows = []
    for i in range(nrows()):
        fn, ln, fem = person("hu_HU")
        c = R.choice(courses)
        user = (ascii_up(ln)[:5] + ascii_up(fn)[:2]).lower() + str(R.randint(1, 99)) if R.random() < 0.7 else f"user{R.randint(10000, 99999)}"
        rows.append({
            "felhasznalonev": user,
            "email": f.free_email(),
            "teljes_nev": f"{ln} {fn}",
            "kor": maybe(age_of(birth(17, 66)), 0.1),
            "nem": ("nő" if fem else "férfi") if R.random() > 0.05 else "nem adja meg",
            "utolso_ip": f.ipv4_public() if R.random() < 0.85 else f.ipv6(),
            "bongeszo": f.user_agent(),
            "munkamenet_id": hashlib.md5(f"{i}{R.random()}".encode()).hexdigest(),
            "kurzus_kod": c[0],
            "kurzus_nev": c[1],
            "isbn_jegyzet": isbns[c[0]],
            "beiratkozas_datuma": rdate(dt.date(2025, 9, 1), dt.date(2026, 11, 10)).strftime("%Y.%m.%d."),
            "ar_huf": R.choice([0, 19900, 29900, 49900, 89000]),
            "modul_hash": hashlib.sha1(f"{c[0]}-mod{R.randint(1, 8)}".encode()).hexdigest(),
            "tamogatas_email": "tamogatas@tudaskapu.hu",
        })
    df = pd.DataFrame(rows)
    df["kor"] = df["kor"].astype("Int64")
    df.to_csv(DATA / "elearning_beiratkozasok.csv", sep=";", index=False)
    VALIDATIONS.append(("isbn13", std_isbn.is_valid, df["isbn_jegyzet"].tolist()))
    L = {"felhasznalonev": "customer_id", "email": "email", "teljes_nev": "person_name", "kor": "age", "nem": "gender",
         "utolso_ip": "ip_address", "bongeszo": "user_agent", "munkamenet_id": "device_id", "kurzus_kod": None,
         "kurzus_nev": None, "isbn_jegyzet": None, "beiratkozas_datuma": None, "ar_huf": None, "modul_hash": None,
         "tamogatas_email": None}
    register("elearning_beiratkozasok.csv", df.columns, L,
             f"elearning_beiratkozasok.csv | e-learning platform enrolments (HU) | Hungarian | {len(df)} rows / {len(df.columns)} cols | ';' delimiter; two hex columns: session id (personal) vs content hash (not); support mailbox constant; IPv4+IPv6")


def t15_biobank():
    rows = []
    fem_first = ["Mari", "Kadri", "Liis", "Triin", "Anu", "Katrin", "Piret", "Eha", "Maarja", "Kristiina"]
    male_first = ["Jaan", "Andres", "Tõnu", "Mart", "Rein", "Priit", "Indrek", "Kalev", "Siim", "Toomas"]
    last = ["Tamm", "Saar", "Sepp", "Mägi", "Kask", "Kukk", "Rebane", "Ilves", "Pärn", "Koppel", "Lepik", "Kuusk"]
    for i in range(nrows()):
        fem = R.random() < 0.5
        b = birth(18, 90)
        rows.append({
            "proovi_partii": f"LOT-{R.randint(2024, 2026)}-{R.randint(1, 60):03d}",
            "isikukood": gen_ee(b, fem),
            "nimi": f"{R.choice(fem_first if fem else male_first)} {R.choice(last)}",
            "sünniaeg": b.strftime("%d.%m.%Y"),
            "sugu": "N" if fem else "M",
            "BRCA1": R.choice(["metsiktüüp"] * 8 + ["c.5266dupC heterosügootne", "c.4035delA heterosügootne", "VUS c.1067A>G"]),
            "APOE_genotüüp": R.choice(["ε3/ε3", "ε3/ε3", "ε3/ε4", "ε2/ε3", "ε4/ε4", "ε2/ε4"]),
            "veregrupp": R.choice(["0 Rh+", "A Rh+", "B Rh+", "AB Rh+", "0 Rh-", "A Rh-"]),
            "diagnoos": maybe(R.choice(["E11.9", "I10", "C50.9", "J45.9", "E78.0", "F32.1"]), 0.4),
            "analüüsi_kuupäev": rdate(dt.date(2025, 6, 1), dt.date(2026, 11, 1)).isoformat(),
            "labor": R.choice(["TÜ Kliinikumi Ühendlabor", "SYNLAB Eesti OÜ", "Geenivaramu kesklabor"]),
            "sekvenaator": R.choice(["Illumina NovaSeq 6000", "Illumina NextSeq 2000", "MGI DNBSEQ-G400"]),
            "kvaliteet_Q30": round(R.uniform(85, 97), 1),
        })
    df = pd.DataFrame(rows)
    df.to_csv(DATA / "biopank_proovid.tsv", sep="\t", index=False)
    VALIDATIONS.append(("ee.ik", ee_ik.is_valid, df["isikukood"].tolist()))
    L = {"proovi_partii": None, "isikukood": "national_id", "nimi": "person_name", "sünniaeg": "date_of_birth",
         "sugu": "gender", "BRCA1": "genetic", "APOE_genotüüp": "genetic", "veregrupp": "health", "diagnoos": "health",
         "analüüsi_kuupäev": None, "labor": None, "sekvenaator": None, "kvaliteet_Q30": None}
    register("biopank_proovid.tsv", df.columns, L,
             f"biopank_proovid.tsv | biobank / genetic lab samples (EE) | Estonian | {len(df)} rows / {len(df.columns)} cols | tab-separated; genetic variant columns; blood group & ICD-10 health; lab/QC metadata non-personal")


def t16_hr_db():
    cities_ee = ["Tallinn", "Tartu", "Pärnu", "Narva"]
    cities_lt = ["Vilnius", "Kaunas", "Klaipėda", "Šiauliai"]
    titles = ["Warehouse Operative", "Forklift Driver", "Logistics Coordinator", "HR Specialist", "Data Engineer",
              "Accountant", "Shift Supervisor", "Truck Driver", "Customer Service Agent", "Country Manager"]
    eth = ["Estonian", "Lithuanian", "Russian", "Polish", "Ukrainian", "Latvian", "Prefer not to say"]
    ee_f = ["Mari", "Kadri", "Liis", "Triin"]; ee_m = ["Jaan", "Andres", "Mart", "Priit"]
    lt_f = ["Rūta", "Eglė", "Agnė", "Ieva"]; lt_m = ["Mantas", "Tomas", "Jonas", "Lukas"]
    ee_l = ["Tamm", "Saar", "Sepp", "Mägi", "Kask", "Kukk"]
    lt_l_m = ["Kazlauskas", "Petrauskas", "Jankauskas", "Butkus", "Paulauskas"]
    lt_l_f = ["Kazlauskienė", "Petrauskaitė", "Jankauskienė", "Butkutė", "Paulauskienė"]
    emps = []
    n = nrows()
    for i in range(n):
        fem = R.random() < 0.45
        b = birth(19, 66)
        if R.random() < 0.5:
            fn = R.choice(ee_f if fem else ee_m); ln = R.choice(ee_l); pid = gen_ee(b, fem); city = R.choice(cities_ee)
        else:
            fn = R.choice(lt_f if fem else lt_m); ln = R.choice(lt_l_f if fem else lt_l_m); pid = gen_lt(b, fem); city = R.choice(cities_lt)
        em = ascii_up(fn).lower() + "." + ascii_up(ln).lower() + "@balticfreight.eu"
        emps.append({
            "emp_id": f"E{5000 + i}",
            "first_name": fn,
            "last_name": ln,
            "work_email": em,
            "personal_id": pid,
            "birth_date": b.isoformat(),
            "gender": "F" if fem else "M",
            "job_title": R.choice(titles),
            "dept_id": R.choice(["D10", "D20", "D30", "D40", "D50"]),
            "hire_date": rdate(dt.date(2012, 1, 1), dt.date(2026, 10, 1)).isoformat(),
            "home_city": city,
            "union_member": R.choice(["Y", "N", "N", "N"]),
            "ethnicity_self_declared": maybe(R.choice(eth), 0.2),
            "sick_days_ytd": R.choice([0, 0, 0, 1, 2, 3, 5, 8, 12, 21]),
            "fingerprint_template": base64.b64encode(bytes(R.randint(0, 255) for _ in range(48))).decode() if R.random() < 0.7 else None,
        })
    edf = pd.DataFrame(emps)
    slips = []
    m = nrows()
    chosen = R.sample(emps, min(m, len(emps)))
    while len(chosen) < m:
        chosen.append(R.choice(emps))
    for j, e in enumerate(chosen):
        gross = R.choice([1350, 1600, 1850, 2100, 2400, 2900, 3500, 4800])
        slips.append({
            "payslip_id": f"PS-202610-{j + 1:05d}",
            "emp_id": e["emp_id"],
            "period": "2026-10",
            "gross_salary": gross,
            "net_salary": round(gross * R.uniform(0.72, 0.8), 2),
            "bank_iban": gen_iban("EE" if e["personal_id"] and ee_ik.is_valid(e["personal_id"]) and e["home_city"] in cities_ee else "LT", 0.3),
            "cost_center": R.choice(["CC-TLL-OPS", "CC-VNO-OPS", "CC-HQ-ADM", "CC-KUN-WH"]),
            "currency": "EUR",
            "pay_date": "2026-11-05",
        })
    sdf = pd.DataFrame(slips)
    con = sqlite3.connect(DATA / "hr_baltic.db")
    edf.to_sql("employees", con, index=False, if_exists="replace")
    sdf.to_sql("payslips", con, index=False, if_exists="replace")
    con.close()
    VALIDATIONS.append(("ee.ik/lt.asmens", lambda x: ee_ik.is_valid(x) or lt_asmens.is_valid(x), edf["personal_id"].tolist()))
    VALIDATIONS.append(("iban EE/LT", std_iban.is_valid, sdf["bank_iban"].tolist()))
    L1 = {"emp_id": "customer_id", "first_name": "person_name", "last_name": "person_name", "work_email": "email",
          "personal_id": "national_id", "birth_date": "date_of_birth", "gender": "gender", "job_title": "occupation",
          "dept_id": None, "hire_date": None, "home_city": "city", "union_member": "trade_union",
          "ethnicity_self_declared": "racial_ethnic_origin", "sick_days_ytd": "health",
          "fingerprint_template": "biometric"}
    L2 = {"payslip_id": None, "emp_id": "customer_id", "period": None, "gross_salary": "income", "net_salary": "income",
          "bank_iban": "iban", "cost_center": None, "currency": None, "pay_date": None}
    register("hr_baltic.db::employees", edf.columns, L1,
             f"hr_baltic.db::employees | HR master data, logistics company (EE/LT) | English headers, Estonian/Lithuanian names | {len(edf)} rows / {len(edf.columns)} cols | SQLite; work e-mails are personal; union flag, ethnicity, sick days, base64 fingerprint templates")
    register("hr_baltic.db::payslips", sdf.columns, L2,
             f"hr_baltic.db::payslips | payroll October 2026 (EE/LT) | English | {len(sdf)} rows / {len(sdf.columns)} cols | SQLite; payslip IDs/cost centres non-personal; salary = income")


def t17_log():
    f = fk("it_IT")
    lines = []
    t = dt.datetime(2026, 11, 14, 7, 58, 0)
    n = nrows()
    for i in range(n):
        t += dt.timedelta(seconds=R.randint(3, 240))
        ts = t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{R.randint(0, 999):03d}Z"
        call = f"CC-{R.randint(5000000, 5999999)}"
        ag = f"AG-{R.randint(100, 160):04d}"
        a, bb, _ = person("it_IT")
        k = R.random()
        if k < 0.25:
            ln = f"{ts} INFO  [ivr] call_id={call} queue={R.choice(['FATTURAZIONE', 'TECNICO', 'COMMERCIALE', 'DISDETTE'])} wait={R.randint(5, 600)}s"
        elif k < 0.38:
            ln = f"{ts} DEBUG [asr] call_id={call} confidence={R.uniform(0.6, 0.99):.2f} lang=it-IT model=asr-v7"
        elif k < 0.48:
            ln = f"{ts} ERROR [crm] timeout after 3000ms on get_invoice(inv=INV-2026-{d(6)})"
        elif k < 0.58:
            ln = f"{ts} INFO  [agent:{ag}] call_id={call} transcript=\"Buongiorno, sono {a} {bb}, chiamo per la bolletta di ottobre\""
        elif k < 0.66:
            ln = f"{ts} WARN  [crm] lookup failed for msisdn={phone('IT').replace(' ', '')} call_id={call}"
        elif k < 0.73:
            ln = f"{ts} INFO  [agent:{ag}] call_id={call} contact email updated to {f.free_email()}"
        elif k < 0.79:
            ln = f"{ts} INFO  [agent:{ag}] call_id={call} transcript=\"mia madre è in dialisi, non possiamo restare senza linea\""
        elif k < 0.85:
            ln = f"{ts} INFO  [web] callback requested from ip={f.ipv4_public()} session={d(12)}"
        elif k < 0.92:
            ln = f"{ts} INFO  [wrapup] call_id={call} outcome={R.choice(['RISOLTO', 'ESCALATION', 'RICHIAMARE'])} aht={R.randint(60, 900)}s"
        else:
            ln = f"{ts} INFO  [scheduler] queue stats served={R.randint(50, 400)} abandoned={R.randint(0, 30)} sla={R.uniform(70, 99):.1f}%"
        lines.append(ln)
    (DATA / "callcenter_2026-11-14.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
    L = {"line": "free_text"}
    register("callcenter_2026-11-14.log", L.keys(), L,
             f"callcenter_2026-11-14.log | call-centre application log (IT) | English log format with Italian transcripts | {n} lines / 1 col | plain-text log, column 'line'; mix of technical lines and lines with names, phone numbers, e-mails, IPs, health")


def t18_survey():
    cities = ["София", "Пловдив", "Варна", "Бургас", "Русе", "Стара Загора", "Плевен", "Кърджали"]
    rows = []
    for i in range(nrows()):
        b = birth(18, 88)
        rows.append({
            "id_респондент": f"R{26000 + i}",
            "възраст": age_of(b),
            "пол": R.choice(["мъж", "жена"]),
            "населено_място": R.choice(cities),
            "образование": R.choice(["основно", "средно", "средно", "висше - бакалавър", "висше - магистър", "доктор"]),
            "партия": R.choice(["ГЕРБ-СДС", "ПП-ДБ", "Възраждане", "ДПС", "БСП", "Има такъв народ", "не гласувах", "отказ"]),
            "вероизповедание": R.choice(["православно християнство"] * 4 + ["ислям", "католицизъм", "протестантство", "атеист", "без отговор"]),
            "етническа_група": R.choice(["българска"] * 6 + ["турска", "ромска", "арменска", "друга", "без отговор"]),
            "сексуална_ориентация": R.choice(["хетеросексуална"] * 6 + ["хомосексуална", "бисексуална", "без отговор", "без отговор"]),
            "дата_интервю": rdate(dt.date(2026, 10, 1), dt.date(2026, 10, 28)).strftime("%d.%m.%Y"),
            "тегло": round(R.uniform(0.45, 2.2), 3),
            "вълна": R.choice(["2026-10 W1", "2026-10 W2", "2026-10 W3"]),
        })
    df = pd.DataFrame(rows)
    df.to_csv(DATA / "anketa_naselenie_2026.csv", sep=",", index=False)
    L = {"id_респондент": "customer_id", "възраст": "age", "пол": "gender", "населено_място": "city",
         "образование": "education", "партия": "political_opinion", "вероизповедание": "religion",
         "етническа_група": "racial_ethnic_origin", "сексуална_ориентация": "sex_life_orientation",
         "дата_интервю": None, "тегло": None, "вълна": None}
    register("anketa_naselenie_2026.csv", df.columns, L,
             f"anketa_naselenie_2026.csv | opinion poll / social survey microdata (BG) | Bulgarian (Cyrillic) | {len(df)} rows / {len(df.columns)} cols | pseudonymous respondent IDs; special categories; 'тегло' is a survey weighting factor, not body weight")


def t19_invoices():
    f = fk("sk_SK")
    suppliers = []
    for _ in range(25):
        a, bb, _ = person("sk_SK")
        nm = R.choice(["Tatra", "Danubia", "Považie", "Kriváň", "Orava", "Zemplín", "Nitrastav", "Biela"]) + \
            R.choice([" Trade", " Logistik", " Office", " Pack", " Tech", " Servis"]) + R.choice([" s.r.o.", " a.s.", " s.r.o."])
        dom = ascii_up(nm.split()[0]).lower()
        suppliers.append(dict(name=nm, ico=d(8), dph=gen_sk_dph(), iban=gen_iban("SK"), street=f.street_address(),
                              city=f.city(), psc=f.postcode(), mail=R.choice(["fakturacia", "info", "uctovnictvo"]) + f"@{dom}.sk",
                              contact=f"{a} {bb}" if R.random() < 0.8 else None))
    items = [("Kancelársky papier A4 80g, 5 bal.", "858"), ("Toner HP 26A čierny", "858"), ("Stretch fólia 23µm 500mm", "858"),
             ("Paleta EUR EPAL 1200x800", "858"), ("Kartónová krabica 3VVL 600x400x400", "858"), ("Servis vysokozdvižného vozíka", None),
             ("Preprava Bratislava - Košice, 2 palety", None), ("Licencia ERP modul Sklad, 12 mes.", None)]
    rows = []
    for i in range(nrows()):
        s = R.choice(suppliers)
        it = R.choice(items)
        iss = rdate(dt.date(2026, 1, 2), dt.date(2026, 11, 10))
        base = round(R.uniform(40, 12000), 2)
        rows.append({
            "cislo_faktury": f"{iss:%Y}{R.randint(1, 9999):04d}",
            "variabilny_symbol": f"{iss:%Y}{d(6)}",
            "dodavatel": s["name"],
            "ico": s["ico"],
            "ic_dph": s["dph"],
            "iban_dodavatela": s["iban"],
            "sidlo_ulica": s["street"],
            "mesto": s["city"],
            "psc": s["psc"],
            "kontakt_email": s["mail"],
            "kontaktna_osoba": s["contact"],
            "datum_vystavenia": iss.strftime("%d.%m.%Y"),
            "splatnost": (iss + dt.timedelta(days=R.choice([14, 30, 60]))).strftime("%d.%m.%Y"),
            "suma_bez_dph": dec(base),
            "sadzba_dph": R.choice(["23%", "19%", "5%"]),
            "ean_polozky": gen_ean(it[1]) if it[1] else None,
            "popis_polozky": it[0],
        })
    df = pd.DataFrame(rows)
    df.to_csv(DATA / "faktury_dodavatelov.csv", sep=";", index=False)
    VALIDATIONS.append(("sk.dph", sk_dph.is_valid, df["ic_dph"].tolist()))
    VALIDATIONS.append(("iban SK", std_iban.is_valid, df["iban_dodavatela"].tolist()))
    VALIDATIONS.append(("ean13", std_ean.is_valid, df["ean_polozky"].dropna().tolist()))
    L = {"cislo_faktury": None, "variabilny_symbol": None, "dodavatel": None, "ico": None, "ic_dph": None,
         "iban_dodavatela": None, "sidlo_ulica": None, "mesto": None, "psc": None, "kontakt_email": None,
         "kontaktna_osoba": "person_name", "datum_vystavenia": None, "splatnost": None, "suma_bez_dph": None,
         "sadzba_dph": None, "ean_polozky": None, "popis_polozky": None}
    register("faktury_dodavatelov.csv", df.columns, L,
             f"faktury_dodavatelov.csv | accounts-payable supplier invoices (SK) | Slovak | {len(df)} rows / {len(df.columns)} cols | ';' delimiter; almost all business data (company IDs, VAT, IBAN, seat address, generic mailbox, EAN); only supplier contact person is personal")


def main():
    t01_telco()
    t02_energy()
    t03_smartmeter()
    t04_rental()
    t05_hotel()
    t06_dental()
    t07_pharmacy()
    t08_municipality()
    t09_admissions()
    t10_recruitment()
    t11_insurance()
    t12_kyc()
    t13_delivery()
    t14_elearning()
    t15_biobank()
    t16_hr_db()
    t17_log()
    t18_survey()
    t19_invoices()

    bad = 0
    for name, fn, vals in VALIDATIONS:
        nb = [v for v in vals if not fn(str(v))]
        print(f"validate {name}: {len(vals) - len(nb)}/{len(vals)} valid")
        bad += len(nb)
    assert bad == 0, "invalid identifiers generated"

    with open(ROOT / "labels.json", "w", encoding="utf-8") as fh:
        json.dump(LABELS, fh, ensure_ascii=False, indent=1)
    with open(ROOT / "README.md", "w", encoding="utf-8") as fh:
        fh.write("# holdout2 - blind GDPR personal-data detection benchmark\n\n")
        fh.write("Generated by `make_holdout.py` (seed 20261122). Labels in `labels.json` (one type or null per column; "
                 "nested JSON keys as dot paths, `file::table` for SQLite, `file::Sheet` for Excel). All data is synthetic.\n\n")
        fh.write("Format of each line: file | scenario | language | rows / columns | notes\n\n")
        for line in README:
            fh.write(f"- {line}\n")


if __name__ == "__main__":
    main()
