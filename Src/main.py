from __future__ import annotations

import argparse

import uvicorn

from Src.api.app import create_app
from Src.benchmark.cli import run_benchmark_cli
from Src.config import load_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Case study entrypoint")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("serve", help="Run API server")

    benchmark = subparsers.add_parser("benchmark", help="Run benchmark suite")
    benchmark.add_argument(
        "--smoke", action="store_true", help="Run smoke matrix"
    )
    benchmark.add_argument("--full", action="store_true", help="Run full matrix")
    benchmark.add_argument(
        "--validate", action="store_true", help="Run validators"
    )
    return parser


def run_cli() -> int:
    parser = build_parser()
    args = parser.parse_args()
    settings = load_settings()

    if args.command == "benchmark":
        run_benchmark_cli(
            smoke=args.smoke,
            full=args.full,
            validate=args.validate,
        )
        return 0

    app = create_app()
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli())
