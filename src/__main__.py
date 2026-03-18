"""CLI for aquawatch."""
import sys, json, argparse
from .core import Aquawatch

def main():
    parser = argparse.ArgumentParser(description="AquaWatch — Water Quality Monitor. IoT + AI water quality prediction and contamination detection.")
    parser.add_argument("command", nargs="?", default="status", choices=["status", "run", "info"])
    parser.add_argument("--input", "-i", default="")
    args = parser.parse_args()
    instance = Aquawatch()
    if args.command == "status":
        print(json.dumps(instance.get_stats(), indent=2))
    elif args.command == "run":
        print(json.dumps(instance.detect(input=args.input or "test"), indent=2, default=str))
    elif args.command == "info":
        print(f"aquawatch v0.1.0 — AquaWatch — Water Quality Monitor. IoT + AI water quality prediction and contamination detection.")

if __name__ == "__main__":
    main()
