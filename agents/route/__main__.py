import argparse
import json
import sys

from agents.route.agent import run_route_by_job_id
from core.schemas import RouteStatus


def main() -> None:
    parser = argparse.ArgumentParser(description="Route agent: финальная маршрутизация по job_id.")
    parser.add_argument("job_id", help="UUID каталога data/jobs/{job_id}/")
    args = parser.parse_args()
    result = run_route_by_job_id(args.job_id)
    if result is None:
        print(json.dumps({"error": "job_or_manifest_not_found"}, ensure_ascii=False), file=sys.stderr)
        sys.exit(2)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
    sys.exit(0 if result.status == RouteStatus.READY_FOR_TEMPLATE else 1)


if __name__ == "__main__":
    main()
