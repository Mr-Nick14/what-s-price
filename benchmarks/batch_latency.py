"""Замер задержки для одного и 500 автомобилей."""

import argparse
import json
from pathlib import Path
from statistics import median
from urllib.request import Request, urlopen

GOOD_ROW = json.loads(Path(__file__).resolve().parents[1].joinpath("good.json").read_text())


def predict(url: str, payload: dict) -> float:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=60) as response:
        return float(json.load(response)["latency_ms"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="http://127.0.0.1:8000")
    parser.add_argument("--repetitions", type=int, default=10)
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error("--repetitions must be positive")

    single_url = args.host.rstrip("/") + "/v1/predict"
    batch_url = args.host.rstrip("/") + "/v1/predict/batch"
    batch = {"rows": [GOOD_ROW] * 500}

    predict(single_url, GOOD_ROW)  # warm-up
    predict(batch_url, batch)
    single = [predict(single_url, GOOD_ROW) for _ in range(args.repetitions)]
    large = [predict(batch_url, batch) for _ in range(args.repetitions)]
    one_ms, five_hundred_ms = median(single), median(large)

    print(f"single median: {one_ms:.2f} ms ({args.repetitions} runs)")
    print(f"batch 500 median: {five_hundred_ms:.2f} ms ({args.repetitions} runs)")
    print(f"ratio: {five_hundred_ms / one_ms:.2f}x")


if __name__ == "__main__":
    main()
