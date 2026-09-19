"""Writes 8 CSV shards of signup records, each with a known number of bad rows."""

import csv
import os
import random

ROWS = 100
OUT = "shards"

BAD_EMAILS = ["not-an-email", "user@", "@nodomain.com", "user@nodot"]
NAMES = ["ana", "ben", "chen", "dia", "eli", "fay"]

os.makedirs(OUT, exist_ok=True)
expected = {}

for shard in range(8):
    rng = random.Random(42 + shard)
    rows, invalid = [], 0

    for i in range(ROWS):
        uid = f"u{shard:02d}{i:04d}"
        email = f"{rng.choice(NAMES)}{i}@example.com"
        date = f"2026-0{rng.randint(1, 9)}-{rng.randint(10, 28)}"

        r = rng.random()
        if r < 0.12:
            email = rng.choice(BAD_EMAILS)
            invalid += 1
        elif r < 0.18:
            field = rng.choice(["uid", "email", "date"])
            if field == "uid":
                uid = ""
            elif field == "email":
                email = ""
            else:
                date = ""
            invalid += 1

        rows.append({"user_id": uid, "email": email, "signup_date": date})

    with open(f"{OUT}/shard_{shard}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["user_id", "email", "signup_date"])
        w.writeheader()
        w.writerows(rows)

    expected[shard] = invalid
    print(f"shard_{shard}.csv: {ROWS} rows, {invalid} invalid")

print(f"\nexpected: {expected}")
print(f"total invalid: {sum(expected.values())}")
