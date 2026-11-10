import json
from pathlib import Path

from app.main import app

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "openapi.json"


def main() -> None:
    schema = json.dumps(app.openapi(), indent=2, ensure_ascii=False)
    OUTPUT_PATH.write_text(schema + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
