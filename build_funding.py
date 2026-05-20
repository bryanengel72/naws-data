#!/usr/bin/env python3
"""Build funding/payment data for the NAWS dashboard.

Reads the Q1 Transaction Report, aggregates by payment type (net + gross),
identifies cancel/re-entry pairs, and emits funding_data.json for the
"Funding / Grants" tab.
"""
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path("/Users/bryanengel/NAWS Data")
SRC = ROOT / "Transaction Report 1st Quarter.csv"
OUT = ROOT / "funding_data.json"


def parse_money(s: str) -> float:
    s = (s or "").replace("$", "").replace(",", "").strip()
    if not s or s == "-":
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_date(s: str):
    """Returns (year, month) ints from m/d/yy."""
    s = (s or "").strip()
    if not s or s == "-":
        return None, None
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", s)
    if not m:
        return None, None
    return int(m.group(3)) if int(m.group(3)) > 99 else 2000 + int(m.group(3)), int(m.group(1))


rows = []
with SRC.open(newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        r["_amount"] = parse_money(r.get("Amount Paid"))
        r["_year"], r["_month"] = parse_date(r.get("Date of Payment"))
        rows.append(r)

# ----------------------------------------------------------------------
# Aggregate by Payment Type
# ----------------------------------------------------------------------
ptype = defaultdict(lambda: {"gross_count": 0, "gross_amount": 0.0,
                              "net_count": 0, "net_amount": 0.0,
                              "canceled_count": 0, "canceled_amount": 0.0,
                              "refund_count": 0, "refund_amount": 0.0})

for r in rows:
    pt = (r.get("Payment Type") or "").strip() or "Unknown"
    tt = (r.get("Transaction Type") or "").strip()
    amt = r["_amount"]
    ptype[pt]["gross_count"] += 1
    ptype[pt]["gross_amount"] += amt
    if tt == "Payment":
        ptype[pt]["net_count"] += 1
        ptype[pt]["net_amount"] += amt
    elif tt == "Canceled":
        ptype[pt]["canceled_count"] += 1
        ptype[pt]["canceled_amount"] += amt
    elif tt == "Refund":
        ptype[pt]["refund_count"] += 1
        ptype[pt]["refund_amount"] += amt
        # Refunds reduce net
        ptype[pt]["net_amount"] -= amt

# Roll up card brands into "Credit Card" for simpler view
CREDIT_BRANDS = {"Visa", "MasterCard", "American Express", "Discover"}
credit_summary = {"gross_count": 0, "gross_amount": 0.0, "net_count": 0, "net_amount": 0.0,
                  "canceled_count": 0, "canceled_amount": 0.0, "refund_count": 0, "refund_amount": 0.0}
for brand in CREDIT_BRANDS:
    if brand in ptype:
        for k in credit_summary:
            credit_summary[k] += ptype[brand][k]

# ----------------------------------------------------------------------
# Cancel/re-entry pair detection: same Payment Type + same Invoice ID,
# where one is Canceled and another is Payment.
# ----------------------------------------------------------------------
by_inv = defaultdict(list)
for r in rows:
    pt = (r.get("Payment Type") or "").strip()
    inv = (r.get("Invoice IDs") or "").strip()
    if not inv or inv == "-":
        continue
    by_inv[(pt, inv)].append(r)

pairs = []
for (pt, inv), grp in by_inv.items():
    cancels = [r for r in grp if r.get("Transaction Type", "").strip() == "Canceled"]
    payments = [r for r in grp if r.get("Transaction Type", "").strip() == "Payment"]
    if cancels and payments:
        pairs.append({
            "paymentType": pt,
            "invoiceId": inv,
            "client": payments[0].get("Client Full Name", ""),
            "canceled": [{"date": r["Date of Payment"], "amount": r["_amount"]} for r in cancels],
            "kept": [{"date": r["Date of Payment"], "amount": r["_amount"]} for r in payments],
        })

# ----------------------------------------------------------------------
# Detail listings for the two funding sources
# ----------------------------------------------------------------------
def detail_for(target_type):
    out = []
    for r in rows:
        pt = (r.get("Payment Type") or "").strip()
        if pt != target_type:
            continue
        out.append({
            "date": r["Date of Payment"],
            "clientId": r["Client ID"],
            "client": r["Client Full Name"],
            "patients": r["Patient Names"],
            "invoice": r["Invoice IDs"],
            "amount": r["_amount"],
            "type": r["Transaction Type"],
            "note": (r["Payment Note"] or "").strip() if r["Payment Note"] not in (None, "-", "") else "",
            "user": r["User"],
        })
    return out

mr_donation = detail_for("Mr. Donation")
mo_grant = detail_for("MO.DEPT AG GRANT 2026")

# ----------------------------------------------------------------------
# Monthly trend (Jan/Feb/Mar) for grant + donation
# ----------------------------------------------------------------------
def monthly_net(target_type):
    by_m = defaultdict(float)
    for r in rows:
        pt = (r.get("Payment Type") or "").strip()
        if pt != target_type:
            continue
        if r.get("Transaction Type", "").strip() != "Payment":
            continue
        m = r["_month"]
        if m:
            by_m[m] += r["_amount"]
    return [round(by_m.get(m, 0), 2) for m in (1, 2, 3)]

monthly = {
    "Mr. Donation": monthly_net("Mr. Donation"),
    "MO.DEPT AG GRANT 2026": monthly_net("MO.DEPT AG GRANT 2026"),
}

# ----------------------------------------------------------------------
# Build payload
# ----------------------------------------------------------------------
total_net = sum(v["net_amount"] for v in ptype.values())
grant_net = ptype.get("MO.DEPT AG GRANT 2026", {}).get("net_amount", 0)
donation_net = ptype.get("Mr. Donation", {}).get("net_amount", 0)
subsidized_net = grant_net + donation_net

payment_types = []
for pt, v in sorted(ptype.items(), key=lambda kv: -kv[1]["net_amount"]):
    payment_types.append({
        "name": pt,
        "grossCount": v["gross_count"],
        "grossAmount": round(v["gross_amount"], 2),
        "netCount": v["net_count"],
        "netAmount": round(v["net_amount"], 2),
        "canceledCount": v["canceled_count"],
        "canceledAmount": round(v["canceled_amount"], 2),
        "refundCount": v["refund_count"],
        "refundAmount": round(v["refund_amount"], 2),
        "category": (
            "Grant" if "GRANT" in pt.upper() else
            "Donation" if "DONATION" in pt.upper() else
            "Credit Card" if pt in CREDIT_BRANDS else
            "Cash" if pt == "Cash" else
            "Check" if pt == "Check" else
            "Other"
        ),
    })

payload = {
    "period": "Q1 2026 (Jan 1 – Mar 31)",
    "summary": {
        "totalRows": len(rows),
        "totalNet": round(total_net, 2),
        "grantNet": round(grant_net, 2),
        "donationNet": round(donation_net, 2),
        "subsidizedNet": round(subsidized_net, 2),
        "subsidizedPct": round(subsidized_net / total_net * 100, 2) if total_net else 0,
        "creditCard": {k: round(v, 2) if isinstance(v, float) else v for k, v in credit_summary.items()},
    },
    "paymentTypes": payment_types,
    "monthly": monthly,
    "cancelPairs": pairs,
    "mrDonation": mr_donation,
    "moGrant2026": mo_grant,
}

OUT.write_text(json.dumps(payload, indent=2))
print(f"Wrote {OUT}  ({OUT.stat().st_size:,} bytes)")
print(f"Total rows: {len(rows):,}  Total net: ${total_net:,.2f}")
print(f"Grant net: ${grant_net:,.2f}  Donation net: ${donation_net:,.2f}")
print(f"Subsidized %: {payload['summary']['subsidizedPct']}%")
print(f"Cancel/re-entry pairs detected: {len(pairs)}")
for p in pairs:
    cancel_amts = " + ".join(f"${c['amount']:.0f}" for c in p["canceled"])
    kept_amts = " + ".join(f"${c['amount']:.0f}" for c in p["kept"])
    print(f"  [{p['paymentType']}] inv {p['invoiceId']} {p['client']}: canceled {cancel_amts} -> kept {kept_amts}")
