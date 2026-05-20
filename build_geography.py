#!/usr/bin/env python3
"""
Build geography data for NAWS dashboard.

Inputs:
  - Client Report with Address.csv (~/Downloads)
  - NAWS Surgeries 2025 - invoice_line_items_report-01_01_2025-12_31_2025 (1).csv
  - invoice line items report 01-01-26 04-30-26.csv

Output:
  - geography_data.json (embedded into naws-dashboard-2025.html)
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional

ROOT = Path("/Users/bryanengel/NAWS Data")
CLIENT_FILE = Path("/Users/bryanengel/Downloads/Client Report with Address.csv")
INV_2025 = ROOT / "NAWS Surgeries 2025 - invoice_line_items_report-01_01_2025-12_31_2025 (1).csv"
INV_2026 = ROOT / "invoice line items report 01-01-26 04-30-26.csv"
OUT = ROOT / "geography_data.json"

STATE_NORMALIZE = {
    "missouri": "MO", "mo": "MO", "mo.": "MO",
    "kansas": "KS", "ks": "KS", "ks.": "KS",
    "iowa": "IA", "ia": "IA",
    "nebraska": "NE", "ne": "NE",
    "arkansas": "AR", "ar": "AR",
    "oklahoma": "OK", "ok": "OK",
    "illinois": "IL", "il": "IL",
    "texas": "TX", "tx": "TX",
    "colorado": "CO", "co": "CO",
    "california": "CA", "ca": "CA",
    "florida": "FL", "fl": "FL",
    "tennessee": "TN", "tn": "TN",
    "kentucky": "KY", "ky": "KY",
    "minnesota": "MN", "mn": "MN",
    "wisconsin": "WI", "wi": "WI",
    "indiana": "IN", "in": "IN",
    "ohio": "OH", "oh": "OH",
    "michigan": "MI", "mi": "MI",
    "new york": "NY", "ny": "NY",
    "georgia": "GA", "ga": "GA",
    "north carolina": "NC", "nc": "NC",
    "south carolina": "SC", "sc": "SC",
    "arizona": "AZ", "az": "AZ",
    "washington": "WA", "wa": "WA",
    "oregon": "OR", "or": "OR",
    "virginia": "VA", "va": "VA",
}

CITY_ALIASES = {
    "kc": "Kansas City",
    "k.c.": "Kansas City",
    "kc.": "Kansas City",
}

def parse_money(s: str) -> float:
    if not s:
        return 0.0
    s = s.replace("$", "").replace(",", "").strip()
    if not s or s == "-":
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0

VALID_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA",
    "ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK",
    "OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC",
}

def normalize_state(raw: str) -> str:
    s = re.sub(r"[^A-Za-z\s]", "", raw).strip().lower().rstrip(".")
    if s in STATE_NORMALIZE:
        return STATE_NORMALIZE[s]
    up = s.upper()
    if up in VALID_STATES:
        return up
    return ""  # unknown / unparseable

def normalize_city(raw: str) -> str:
    s = raw.strip()
    if not s:
        return ""
    return CITY_ALIASES.get(s.lower().rstrip("."), s.title())

def extract_zip(token: str) -> Optional[str]:
    """Return 5-digit zip from a token, else None."""
    m = re.search(r"\b(\d{5})(?:-\d{4})?\b", token)
    return m.group(1) if m else None

def parse_address(addr: str):
    """Returns (zip5, city, state, raw_state) or (None,...) when unparseable."""
    if not addr or not addr.strip():
        return None, "", "", ""
    parts = [p.strip() for p in addr.split(",")]
    # Zip is usually the last meaningful field.
    zip5 = None
    state_raw = ""
    city = ""
    # Walk from the right looking for a zip
    for i in range(len(parts) - 1, -1, -1):
        z = extract_zip(parts[i])
        if z:
            zip5 = z
            # State is normally the token before the zip
            if i - 1 >= 0:
                state_raw = parts[i - 1]
            # City is the token before state
            if i - 2 >= 0:
                city = parts[i - 2]
            break
    state = normalize_state(state_raw) if state_raw else ""
    city = normalize_city(city)
    return zip5, city, state, state_raw

# ----------------------------------------------------------------------
# 1. Parse client address file
# ----------------------------------------------------------------------
clients = {}  # client_id -> {name, zip, city, state, raw_address}
name_to_ids = defaultdict(list)

with CLIENT_FILE.open(newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        cid = row["Client ID"].strip()
        name = row["Client Full Name"].strip()
        addr = row["Full Address"].strip()
        if not cid:
            continue
        zip5, city, state, _ = parse_address(addr)
        clients[cid] = {
            "name": name,
            "zip": zip5 or "",
            "city": city,
            "state": state,
            "address": addr,
        }
        # Track for duplicate detection (case- and whitespace-insensitive)
        name_key = re.sub(r"\s+", " ", name.lower()).strip()
        if name_key:
            name_to_ids[name_key].append(cid)

print(f"Clients loaded: {len(clients):,}")
unparsed = sum(1 for c in clients.values() if not c["zip"])
print(f"  Address parse failures (no zip): {unparsed:,}")

# ----------------------------------------------------------------------
# 2. Parse invoice line items
# ----------------------------------------------------------------------
def iter_line_items(path: Path):
    """Yield dicts of line items. Handles 2025 file (summary on top, header at line 39)
    and 2026 file (header at line 5)."""
    with path.open(newline="", encoding="utf-8") as f:
        # Find header row
        header = None
        header_idx = 0
        for i, line in enumerate(f):
            if line.startswith("Date of Invoice"):
                header = next(csv.reader([line]))
                header_idx = i
                break
        if header is None:
            return
        # Re-open and skip past header line
        f.seek(0)
        for _ in range(header_idx + 1):
            f.readline()
        reader = csv.DictReader(f, fieldnames=header)
        for row in reader:
            cid = (row.get("Client ID") or "").strip()
            if not cid or cid == "-":
                continue
            yield row

active_clients = set()  # client_ids with any 2025 or 2026 activity
# zip -> {revenue, count, services: {desc: {count, revenue}}}
zip_agg = defaultdict(lambda: {"revenue": 0.0, "count": 0, "services": defaultdict(lambda: {"count": 0, "revenue": 0.0})})
# city, state aggregations
city_agg = defaultdict(lambda: {"revenue": 0.0, "count": 0, "state": ""})
state_agg = defaultdict(lambda: {"revenue": 0.0, "count": 0})
unknown_client_items = 0      # Client ID in invoice but not in address file
unknown_client_revenue = 0.0
no_zip_items = 0              # Client in address file but address didn't parse to a zip
no_zip_revenue = 0.0
total_line_items = 0
total_revenue = 0.0
# Track year split
year_agg = defaultdict(lambda: {"revenue": 0.0, "count": 0})

# Procedure-level breakdown for top zip lookups: zip -> sorted list (computed at end)

for source_label, path in [("2025", INV_2025), ("2026", INV_2026)]:
    src_count = 0
    for li in iter_line_items(path):
        cid = li["Client ID"].strip()
        desc = (li.get("Description") or "").strip()
        category = (li.get("Product Category") or "").strip()
        price = parse_money(li.get("Selling Price") or li.get("Total") or "0")
        qty_str = (li.get("Quantity") or "1").strip()
        try:
            qty = int(float(qty_str))
        except ValueError:
            qty = 1
        # Use Total field for revenue when present (covers discounts)
        revenue = parse_money(li.get("Total") or li.get("Selling Price") or "0")

        # Skip non-service rows? Keep everything but tag category.
        active_clients.add(cid)
        total_line_items += 1
        total_revenue += revenue
        year_agg[source_label]["count"] += qty
        year_agg[source_label]["revenue"] += revenue
        src_count += 1

        client = clients.get(cid)
        if not client:
            unknown_client_items += 1
            unknown_client_revenue += revenue
            continue
        if not client["zip"]:
            no_zip_items += 1
            no_zip_revenue += revenue
            continue
        z = client["zip"]
        zip_agg[z]["revenue"] += revenue
        zip_agg[z]["count"] += qty
        if desc:
            zip_agg[z]["services"][desc]["count"] += qty
            zip_agg[z]["services"][desc]["revenue"] += revenue
        city_key = (client["city"], client["state"])
        city_agg[city_key]["revenue"] += revenue
        city_agg[city_key]["count"] += qty
        city_agg[city_key]["state"] = client["state"]
        state_agg[client["state"]]["revenue"] += revenue
        state_agg[client["state"]]["count"] += qty
    print(f"{source_label}: {src_count:,} line items")

print(f"Total line items: {total_line_items:,}")
print(f"Total revenue: ${total_revenue:,.0f}")
print(f"  Unknown client (Client ID not in address file): {unknown_client_items:,}  (${unknown_client_revenue:,.0f})")
print(f"  Client found but address has no zip: {no_zip_items:,}  (${no_zip_revenue:,.0f})")
print(f"Distinct active clients (any 2025/26 activity): {len(active_clients):,}")

# ----------------------------------------------------------------------
# 3. Dormant + duplicate flagging
# ----------------------------------------------------------------------
dormant = [cid for cid in clients.keys() if cid not in active_clients]
duplicates = {n: ids for n, ids in name_to_ids.items() if len(ids) > 1 and n not in ("", "123 http://saint.example.com")}

print(f"Dormant clients (no 2025/26 activity): {len(dormant):,}")
print(f"Duplicate name groups: {len(duplicates):,}  ({sum(len(v) for v in duplicates.values()):,} client records)")

# ----------------------------------------------------------------------
# 4. Build JSON payload for dashboard
# ----------------------------------------------------------------------
# Top zips by revenue
zip_rows = []
for z, agg in zip_agg.items():
    # Find dominant city for label
    cities_here = defaultdict(int)
    state_here = ""
    # peek at clients in this zip
    for c in clients.values():
        if c["zip"] == z:
            if c["city"]:
                cities_here[c["city"]] += 1
            if c["state"]:
                state_here = c["state"]
    label_city = max(cities_here.items(), key=lambda kv: kv[1])[0] if cities_here else ""
    # Top 5 services in this zip
    top_services = sorted(agg["services"].items(), key=lambda kv: kv[1]["revenue"], reverse=True)[:5]
    zip_rows.append({
        "zip": z,
        "city": label_city,
        "state": state_here,
        "revenue": round(agg["revenue"], 2),
        "count": agg["count"],
        "topServices": [
            {"name": name, "count": v["count"], "revenue": round(v["revenue"], 2)}
            for name, v in top_services
        ],
    })

zip_rows.sort(key=lambda r: r["revenue"], reverse=True)

# City rollup
city_rows = sorted(
    [
        {
            "city": city,
            "state": state,
            "revenue": round(agg["revenue"], 2),
            "count": agg["count"],
        }
        for (city, state), agg in city_agg.items()
        if city
    ],
    key=lambda r: r["revenue"],
    reverse=True,
)

# State rollup
state_rows = sorted(
    [
        {"state": st, "revenue": round(agg["revenue"], 2), "count": agg["count"]}
        for st, agg in state_agg.items()
        if st
    ],
    key=lambda r: r["revenue"],
    reverse=True,
)

# Duplicate sample (up to 30 groups, by group size desc)
dup_sample = sorted(duplicates.items(), key=lambda kv: -len(kv[1]))[:30]
dup_out = []
for name_key, ids in dup_sample:
    records = []
    for cid in ids:
        c = clients.get(cid, {})
        records.append({
            "clientId": cid,
            "name": c.get("name", ""),
            "zip": c.get("zip", ""),
            "city": c.get("city", ""),
            "state": c.get("state", ""),
            "active": cid in active_clients,
        })
    dup_out.append({"nameKey": name_key, "records": records})

payload = {
    "summary": {
        "totalClients": len(clients),
        "unparsedAddresses": unparsed,
        "activeClients": len(active_clients),
        "dormantClients": len(dormant),
        "duplicateGroups": len(duplicates),
        "duplicateRecords": sum(len(v) for v in duplicates.values()),
        "totalLineItems": total_line_items,
        "totalRevenue": round(total_revenue, 2),
        "unknownClientItems": unknown_client_items,
        "unknownClientRevenue": round(unknown_client_revenue, 2),
        "noZipItems": no_zip_items,
        "noZipRevenue": round(no_zip_revenue, 2),
        "byYear": {y: {"count": v["count"], "revenue": round(v["revenue"], 2)} for y, v in year_agg.items()},
        "distinctZipsServed": sum(1 for z, a in zip_agg.items() if a["count"] > 0),
    },
    "zips": zip_rows,
    "cities": city_rows,
    "states": state_rows,
    "duplicates": dup_out,
}

with OUT.open("w") as f:
    json.dump(payload, f, indent=2)

print(f"\nWrote {OUT}  ({OUT.stat().st_size:,} bytes)")
print(f"  zip rows: {len(zip_rows):,}")
print(f"  city rows: {len(city_rows):,}")
print(f"  state rows: {len(state_rows):,}")
