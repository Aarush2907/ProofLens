import json

from app.evaluation.runner import run_evaluation


def main() -> None:
    print(json.dumps(run_evaluation(), indent=2))


if __name__ == "__main__":
    main()
