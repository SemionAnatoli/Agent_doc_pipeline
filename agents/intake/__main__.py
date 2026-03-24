import argparse
import json
import sys
from pathlib import Path

from agents.intake.agent import run_intake


def main() -> None:
    parser = argparse.ArgumentParser(description="Intake agent: validate and register a document.")
    parser.add_argument("path", type=Path, help="Path to PDF or image file")
    args = parser.parse_args()
    result = run_intake(args.path)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
    sys.exit(0 if result.status.value == "accepted" else 1)


if __name__ == "__main__":
    main()
