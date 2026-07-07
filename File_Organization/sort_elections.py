import os
import shutil
from election_utils import get_seats

# ─── UPDATE THIS PATH ───────────────────────────────────────────────────────
SOURCE_DIR = "/Users/belle/Desktop/rcv_script/processed_data"
# ────────────────────────────────────────────────────────────────────────────

SINGLE_WINNER_DIR = os.path.join(SOURCE_DIR, "single_winner")
MULTI_WINNER_DIR  = os.path.join(SOURCE_DIR, "multi_winner")
UNKNOWN_DIR       = os.path.join(SOURCE_DIR, "unknown")


def delete_empty_folders(root_dir):
    deleted = 0
    for dirpath, dirs, files in os.walk(root_dir, topdown=False):
        if dirpath == root_dir:
            continue
        if not os.listdir(dirpath):
            os.rmdir(dirpath)
            print(f"  [DELETED] {os.path.relpath(dirpath, root_dir)}")
            deleted += 1
    return deleted


def sort_elections():
    os.makedirs(SINGLE_WINNER_DIR, exist_ok=True)
    os.makedirs(MULTI_WINNER_DIR,  exist_ok=True)
    os.makedirs(UNKNOWN_DIR,       exist_ok=True)

    moved   = {"single": 0, "multi": 0, "unknown": 0}
    skipped = []

    for root, dirs, files in os.walk(SOURCE_DIR):
        rel_root = os.path.relpath(root, SOURCE_DIR)
        if rel_root.startswith(("single_winner", "multi_winner", "unknown")):
            continue

        for filename in sorted(files):
            if not filename.lower().endswith(".csv"):
                continue

            src_path = os.path.join(root, filename)

            try:
                seats = get_seats(src_path)
            except Exception as e:
                print(f"  [SKIP] {src_path} — {e}")
                skipped.append(src_path)
                continue

            rel_path  = os.path.relpath(src_path, SOURCE_DIR)
            dest_base = (UNKNOWN_DIR if seats is None else
                         SINGLE_WINNER_DIR if seats == 1 else
                         MULTI_WINNER_DIR)
            dest_path = os.path.join(dest_base, rel_path)

            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.move(src_path, dest_path)

            category = "unknown" if seats is None else ("single" if seats == 1 else "multi")
            moved[category] += 1
            label = {"single": "SINGLE", "multi": "MULTI ", "unknown": "UNKNWN"}[category]
            print(f"  [{label}] {rel_path}")

    print(f"\nCleaning up empty folders...")
    deleted = delete_empty_folders(SOURCE_DIR)

    print(f"\nDone!")
    print(f"  Single-winner files moved : {moved['single']}")
    print(f"  Multi-winner files moved  : {moved['multi']}")
    print(f"  Unknown seat files moved  : {moved['unknown']}")
    print(f"  Empty folders deleted     : {deleted}")
    if skipped:
        print(f"  Skipped (errors)          : {len(skipped)}")
        for s in skipped:
            print(f"    {s}")


if __name__ == "__main__":
    sort_elections()
