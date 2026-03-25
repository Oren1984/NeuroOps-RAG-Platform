# src/cli.py
# Command-line interface for the RAG Agent Kit application.

import argparse
import subprocess
import sys
from pathlib import Path

# Run code audit script
def run_audit() -> None:
    audit = Path("scripts/rag_audit.py")
    if not audit.exists():
        print("[FAIL] scripts/rag_audit.py not found")
        sys.exit(1)

    print("[INFO] Running audit...")
    r = subprocess.run([sys.executable, str(audit)], check=False)
    if r.returncode != 0:
        print("[FAIL] Audit failed. Fix issues before running.")
        sys.exit(r.returncode)

# Write build info to BUILD_INFO.json
def write_build_info() -> None:
    try:
        from src.meta.build_info import write_build_info
        print("[INFO] Writing BUILD_INFO.json ...")
        write_build_info("BUILD_INFO.json")
    except Exception as e:
        print(f"[WARN] Could not write BUILD_INFO.json: {type(e).__name__}")

# Start the API server
def serve(host: str, port: int) -> None:
    run_audit()
    write_build_info()

    print(f"[INFO] Starting server on http://{host}:{port}")
    cmd = [sys.executable, "-m", "uvicorn", "src.main:app", "--host", host, "--port", str(port)]
    raise SystemExit(subprocess.call(cmd))

# Main function to parse arguments and execute commands
def main() -> None:
    parser = argparse.ArgumentParser(prog="rag-agent-kit")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_serve = sub.add_parser("serve", help="Run audit, write BUILD_INFO.json, then start API")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()

    if args.cmd == "serve":
        serve(args.host, args.port)

if __name__ == "__main__":
    main()
