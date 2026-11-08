"""Record a real Open-Meteo request. No mocks, no AWS; network failure exits nonzero."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from src.services.weather import WeatherService
from src.utils.errors import ApiError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", default="Taipei")
    parser.add_argument("--output", default="docs/evidence/weather-live.json")
    args = parser.parse_args()
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "scope": "Real HTTPS Open-Meteo geocoding and current weather; no AWS",
        "city": args.city,
    }
    try:
        report.update({"status": "PASS", "result": WeatherService().query(args.city)})
    except ApiError as exc:
        report.update(
            {
                "status": "BLOCKED",
                "http_status": exc.status,
                "error": {"code": exc.code, "message": exc.message},
            }
        )
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
