"""Manual performance benchmark for the RackSorter HTTP API.

Run against a running server (uvicorn on :8000) with a real upload:

    python -m uvicorn main:app --host 127.0.0.1 --port 8000
    python benchmarks/bench.py --upload-id 32 --keyword "polo collar" ...

This is NOT collected by pytest (filename does not match test_*.py) and is not part
of CI: timings are machine- and network-dependent, so they are reported, not asserted.
"""

import argparse
import time

import requests


def time_request(label, fn):
    start = time.perf_counter()
    result = fn()
    elapsed = time.perf_counter() - start
    print(f"{label}: {elapsed:.2f}s")
    return result, elapsed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--upload-id", type=int, required=True)
    parser.add_argument("--item-url", default=None)
    args = parser.parse_args()

    base = args.base_url.rstrip("/")

    # /fetch_initial (scrape + embed a fresh pool)
    def fetch():
        r = requests.post(f"{base}/fetch_initial", json={
            "uploadId": args.upload_id,
            "keyword": "polo collar",
            "selectedSizes": "",
            "selectedCategory": "Tops & t-shirts",
            "selectedColors": "",
            "maxPrice": "",
            "selectedConditions": "",
        }, timeout=300)
        r.raise_for_status()
        return r.json()

    data, t_fetch = time_request("fetch_initial", fetch)
    print(f"  pool size: {len(data.get('pool', []))}")

    # Pick an item to give feedback on.
    item_url = args.item_url or (data["pool"][0]["url"] if data.get("pool") else None)
    if not item_url:
        print("no item to feedback on; stopping")
        return

    # /rerank (feedback + fetch-more)
    def rerank():
        r = requests.post(f"{base}/rerank_batch", json={
            "upload_id": args.upload_id,
            "feedback": [{"item_url": item_url, "feedback_type": "MORE", "concept": "sleeves"}],
            "fetch_more": True,
        }, timeout=300)
        r.raise_for_status()
        return r.json()

    data2, t_rerank = time_request("rerank (fetch_more=True)", rerank)
    print(f"  new_items: {data2.get('new_items', 0)}, pool size: {len(data2.get('pool', []))}")

    # /trait-profile (debug view)
    def profile():
        r = requests.get(f"{base}/trait-profile", params={"upload_id": args.upload_id, "item_url": item_url}, timeout=60)
        r.raise_for_status()
        return r.json()

    _, t_profile = time_request("trait-profile", profile)
    print(f"\nTotal feedback round-trip: {t_rerank + t_profile:.2f}s")


if __name__ == "__main__":
    main()
PY
echo "created"