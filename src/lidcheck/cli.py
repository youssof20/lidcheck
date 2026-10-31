import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[
            "data-check",
            "audit",
            "train",
            "stress",
            "transfer",
            "consistency",
            "figures",
            "readme",
            "all",
        ],
    )
    parser.add_argument("--study", type=Path)
    args = parser.parse_args()
    from lidcheck import audit, benchmark, consistency, plotting, stress
    from lidcheck.io import archive_checksums

    jobs = {
        "data-check": lambda: print(archive_checksums()),
        "audit": audit.run,
        "train": benchmark.run,
        "stress": stress.run,
        "transfer": stress.transfer,
        "consistency": lambda: consistency.run(args.study),
        "figures": plotting.figures,
        "readme": plotting.summary,
    }
    if args.command == "all":
        for key in ["audit", "train", "stress", "transfer", "consistency", "figures", "readme"]:
            jobs[key]()
    else:
        jobs[args.command]()


if __name__ == "__main__":
    main()
