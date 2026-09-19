"""Validates exactly ONE shard, chosen by JOB_COMPLETION_INDEX.

Each pod of the Indexed Job runs this. Kubernetes sets JOB_COMPLETION_INDEX to
a distinct value per pod (0..completions-1), so pod N validates shard N and no
coordination between pods is needed.

Results go to stdout as a single JSON line. They are collected afterwards by
reading pod logs through the Kubernetes API, not via a shared volume; see the
README for why.
"""

import csv
import json
import os
import re
import sys

# Deliberately strict but simple: local@domain.tld, no leading/trailing dot in
# the local part, no consecutive dots, no double @.
EMAIL_RE = re.compile(r"^[A-Za-z0-9_+-]+(\.[A-Za-z0-9_+-]+)*@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$")

REQUIRED = ["user_id", "email", "signup_date"]


def row_errors(row):
    errs = []
    for field in REQUIRED:
        if not (row.get(field) or "").strip():
            errs.append(f"missing:{field}")
    email = (row.get("email") or "").strip()
    if email and not EMAIL_RE.match(email):
        errs.append("malformed:email")
    return errs


def main():
    index = int(os.environ.get("JOB_COMPLETION_INDEX", "0"))
    shard_dir = os.environ.get("SHARD_DIR", "/data/shards")
    path = os.path.join(shard_dir, f"shard_{index}.csv")

    pod_name = os.environ.get("POD_NAME", "unknown")
    node_name = os.environ.get("NODE_NAME", "unknown")

    if not os.path.exists(path):
        print(json.dumps({"error": f"shard not found: {path}", "index": index}))
        sys.exit(1)

    total = invalid = 0
    reasons = {}

    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            total += 1
            errs = row_errors(row)
            if errs:
                invalid += 1
                for e in errs:
                    reasons[e] = reasons.get(e, 0) + 1

    # one JSON line on stdout: this is the result the API reads back
    print(json.dumps({
        "shard_index": index,
        "shard_file": f"shard_{index}.csv",
        "total_rows": total,
        "invalid_rows": invalid,
        "valid_rows": total - invalid,
        "reasons": reasons,
        "pod_name": pod_name,
        "node_name": node_name,
    }))


if __name__ == "__main__":
    main()
