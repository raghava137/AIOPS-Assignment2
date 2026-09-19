"""Validates one shard, selected by JOB_COMPLETION_INDEX. Prints one JSON line."""

import csv
import json
import os
import re
import sys

EMAIL = re.compile(r"^[A-Za-z0-9._+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}$")

index = int(os.environ.get("JOB_COMPLETION_INDEX", "0"))
path = f"/data/shards/shard_{index}.csv"

if not os.path.exists(path):
    print(json.dumps({"error": "missing", "path": path, "index": index}))
    sys.exit(1)

total = invalid = 0
with open(path, newline="") as f:
    for row in csv.DictReader(f):
        total += 1
        missing = any(not (row.get(k) or "").strip()
                      for k in ("user_id", "email", "signup_date"))
        email = (row.get("email") or "").strip()
        if missing or not EMAIL.match(email):
            invalid += 1

print(json.dumps({
    "shard": index,
    "total_rows": total,
    "invalid_rows": invalid,
    "pod": os.environ.get("POD_NAME", "?"),
    "node": os.environ.get("NODE_NAME", "?"),
}))
