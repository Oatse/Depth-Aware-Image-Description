import argparse
import json
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000/readiness")
    parser.add_argument("--allow-insecure", action="store_true")
    args = parser.parse_args()
    context = None
    if args.allow_insecure:
        import ssl
        context = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(args.url, timeout=10, context=context) as response:
            payload = json.load(response)
    except Exception as exc:
        print(json.dumps({"ready": False, "error": str(exc)}))
        return 2
    print(json.dumps(payload, indent=2))
    return 0 if payload.get("ready") else 2


if __name__ == "__main__":
    raise SystemExit(main())
