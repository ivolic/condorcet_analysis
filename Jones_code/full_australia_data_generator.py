# --- STV parser with Count and Num Seats (skip if >40 candidates) ---
import json
import pandas as pd
import os
import string
from pathlib import Path

def _get(obj, *keys, default=None):
    for k in keys:
        if k in obj:
            return obj[k]
    return default

def _party_column_id_or_letter(parties, idx):
    if idx is None:
        return None
    if idx < 0 or idx >= len(parties):
        return str(idx)
    party = parties[idx]
    col = party.get("column_id") or party.get("id") or party.get("column") or party.get("name")
    if col:
        return str(col)
    if idx < 26:
        return string.ascii_uppercase[idx]
    return str(idx)

def expand_atl_to_candidate_names(party_order, parties, index_to_name, index_to_groupid):
    res = []
    for pidx in party_order:
        if pidx is None or pidx < 0 or pidx >= len(parties):
            continue
        cand_ids = parties[pidx].get("candidates", [])
        for cid in cand_ids:
            name = index_to_name.get(cid, f"cand_{cid}")
            group = index_to_groupid.get(cid) or _party_column_id_or_letter(parties, pidx)
            if group:
                res.append(f"{name} ({group})")
            else:
                res.append(name)
    return res

def stv_parser_with_groups(input_filename, output_folder=None):
    with open(input_filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    metadata = data.get("metadata") or data.get("Metadata") or data
    candidates = _get(metadata, "candidates", "Candidates", default=[])
    parties = _get(metadata, "parties", "Parties", default=[])
    
    # # --- Skip file if more than 40 candidates ---
    # if isinstance(candidates, dict):
    #     num_candidates = len(candidates)
    # else:
    #     num_candidates = len(candidates)
    # if num_candidates > 40:
    #     print(f"Skipping {input_filename} — {num_candidates} candidates")
    #     return None, None

    atl = data.get("atl", data.get("ATL", [])) or []
    btl = data.get("btl", data.get("BTL", [])) or []
    vacancies = _get(metadata, "vacancies", "Vacancies", default=None)
    if vacancies is None:
        vacancies = data.get("vacancies") or data.get("Vacancies") or 1

    index_to_name = {}
    if isinstance(candidates, dict):
        for k, v in candidates.items():
            try:
                idx = int(k)
            except:
                idx = k
            index_to_name[idx] = v.get("name") or v.get("Name") or str(k)
    else:
        for i, c in enumerate(candidates):
            index_to_name[i] = c.get("name") or c.get("Name") or c.get("candidate_name") or f"cand_{i}"

    index_to_groupid = {}
    if isinstance(parties, list):
        for pidx, p in enumerate(parties):
            colid = p.get("column_id") or p.get("id") or p.get("column") or None
            if colid is None:
                colid = _party_column_id_or_letter(parties, pidx)
            for cid in p.get("candidates", []):
                index_to_groupid[cid] = str(colid)
    if isinstance(candidates, list):
        for i, c in enumerate(candidates):
            if i in index_to_groupid:
                continue
            party_field = c.get("party")
            if party_field is not None and isinstance(party_field, int):
                index_to_groupid[i] = _party_column_id_or_letter(parties, party_field)

    parsed_rows = []

    for entry in atl:
        party_order = entry.get("parties") or entry.get("Parties") or []
        count = entry.get("n") or entry.get("N") or entry.get("count") or 0
        if not isinstance(party_order, list):
            continue
        expanded_names = expand_atl_to_candidate_names(party_order, parties, index_to_name, index_to_groupid)
        row = {f"rank{i+1}": expanded_names[i] for i in range(len(expanded_names))}
        row["Count"] = count
        row["Num Seats"] = vacancies
        parsed_rows.append(row)

    for entry in btl:
        cand_ids = entry.get("candidates") or entry.get("Candidates") or []
        count = entry.get("n") or entry.get("N") or entry.get("count") or 0
        names = []
        for cid in cand_ids:
            nm = index_to_name.get(cid, f"cand_{cid}")
            grp = index_to_groupid.get(cid)
            if grp:
                names.append(f"{nm} ({grp})")
            else:
                names.append(nm)
        row = {f"rank{i+1}": names[i] for i in range(len(names))}
        row["Count"] = count
        row["Num Seats"] = vacancies
        parsed_rows.append(row)

    if not parsed_rows:
        df = pd.DataFrame(columns=["Count", "Num Seats"])
    else:
        max_len = max(len(r) - 2 for r in parsed_rows)  # -Count & Num Seats
        norm_rows = []
        for r in parsed_rows:
            newr = {}
            for i in range(1, max_len + 1):
                newr[f"rank{i}"] = r.get(f"rank{i}", "skipped")
            newr["Count"] = r["Count"]
            newr["Num Seats"] = r["Num Seats"]
            norm_rows.append(newr)
        df = pd.DataFrame(norm_rows)

    p = Path(input_filename)
    stem = p.stem
    outname = f"{stem}, {vacancies} seats.csv"
    if output_folder:
        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)
        outname = output_folder / outname

    df.to_csv(outname, index=False, encoding="utf-8")
    return df, outname


# --- Source & target folders ---
# source_folder = "C:/Users/mijones/Documents/Datasets/Australia Complete Data/stv files"
# target_folder = "C:/Users/mijones/Documents/Datasets/Australia Complete Data/fairvote files"
source_folder = Path.home() / "Documents" / "Datasets" / "Australia Complete Data" / "stv files"
target_folder = Path.home() / "Documents" / "Datasets" / "Australia Complete Data" / "fairvote files"
target_folder.mkdir(exist_ok=True)

# --- Parse all .stv files ---
x=0
for stv_file in source_folder.glob("*.stv"):
    x+=1
    print(x,stv_file)
    df, _ = stv_parser_with_groups(stv_file, output_folder=target_folder)