"""Measures the cache-miss vs cache-hit latency difference.

The rubric wants concrete evidence of a speedup, not an assertion that caching
should help. This sends the same text twice, times both calls from the client
side, then repeats over several distinct messages and reports the aggregate.

  python cache_benchmark.py
  python cache_benchmark.py --url http://localhost:8080 --repeats 20
"""

import argparse
import statistics
import time

import requests

MESSAGES = [
    "WIN a FREE iPhone now! Click here: bit.ly/xyz123",
    "Hey, are we still meeting for lunch on Friday?",
    "URGENT: Your account will be suspended. Verify at tinyurl.com/abc",
    "Can you send me the notes from the study group class?",
    "Congratulations! You have WON a laptop. Claim NOW at win-now.co/claim",
]


def timed_post(url, text):
    start = time.perf_counter()
    resp = requests.post(f"{url}/predict", json={"text": text}, timeout=10)
    wall_ms = (time.perf_counter() - start) * 1000
    body = resp.json()
    return wall_ms, body


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://localhost:8080")
    p.add_argument("--repeats", type=int, default=10,
                   help="hit measurements per message after the first miss")
    args = p.parse_args()

    resp = requests.get(f"{args.url}/healthz", timeout=10)
    print(f"GET /healthz -> {resp.status_code} {resp.json()}\n")

    misses, hits = [], []

    print(f"{'message':<46} {'miss ms':>9} {'hit ms':>9} {'speedup':>9}")
    print("-" * 78)

    for text in MESSAGES:
        # first call: nothing in Redis for this text yet
        miss_ms, miss_body = timed_post(args.url, text)
        assert miss_body["cached"] is False, "expected a cache MISS on first call"

        # subsequent calls: should be served from Redis
        per_message_hits = []
        for _ in range(args.repeats):
            hit_ms, hit_body = timed_post(args.url, text)
            assert hit_body["cached"] is True, "expected a cache HIT on repeat"
            assert hit_body["label"] == miss_body["label"], "label changed between hit and miss"
            per_message_hits.append(hit_ms)

        hit_ms = statistics.median(per_message_hits)
        misses.append(miss_ms)
        hits.append(hit_ms)

        label = miss_body["label"]
        short = (text[:40] + "...") if len(text) > 43 else text
        print(f"{short:<46} {miss_ms:>9.2f} {hit_ms:>9.2f} {miss_ms / hit_ms:>8.1f}x")

    print("-" * 78)
    print(f"{'median':<46} {statistics.median(misses):>9.2f} "
          f"{statistics.median(hits):>9.2f} "
          f"{statistics.median(misses) / statistics.median(hits):>8.1f}x")
    print()
    print("Every repeat returned cached=true with the same label as the miss,")
    print("so the speedup comes from skipping the model, not from a different answer.")


if __name__ == "__main__":
    main()
