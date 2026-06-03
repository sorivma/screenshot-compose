from pathlib import Path


def collect_logs(root: Path) -> list[Path]:
    return sorted(root.glob("*.log"))


if __name__ == "__main__":
    for log_path in collect_logs(Path("build")):
        print(f"found {log_path}")
