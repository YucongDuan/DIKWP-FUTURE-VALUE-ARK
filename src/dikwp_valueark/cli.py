from __future__ import annotations

import argparse
import functools
import http.server
import json
import shutil
import threading
import webbrowser
from pathlib import Path

from .dashboard import export_dashboard
from .defaults import load_defaults
from .io import dump_json, load_json
from .optimizer import analyze_and_optimize
from .report import write_reports


def run_analysis(input_path: Path, workspace: Path, *, reset: bool = False) -> dict:
    if reset and workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    portfolio = load_json(input_path)
    analysis = analyze_and_optimize(portfolio)
    dump_json(workspace / "analysis.json", analysis)
    reports = write_reports(workspace, analysis)
    dashboard = export_dashboard(workspace / "futurevalue-ark.html")
    return {
        "workspace": str(workspace),
        "analysis": str(workspace / "analysis.json"),
        "reports": reports,
        "dashboard": str(dashboard),
        "status": analysis["status"],
        "profile": analysis["profile"]["name_zh"],
        "current_worst_case": analysis["current_metrics"]["worst_case"],
        "target_worst_case": analysis["target_metrics"]["worst_case"],
        "automatic_trade_authority": analysis["constitutional_invariants"]["automatic_trade_authority"],
    }


def _sample_path(workspace: Path) -> Path:
    defaults = load_defaults()
    sample = {
        "schema": "dikwp-valueark-portfolio-1.0",
        "name": "合成示例：平衡韧性",
        "settings": defaults["default_settings"],
        "holdings": {asset["id"]: asset["default_amount"] for asset in defaults["assets"]},
        "scenario_weights": defaults["alert_presets"]["yellow"],
        "notes": "Synthetic example only.",
    }
    path = workspace / "sample-portfolio.json"
    dump_json(path, sample)
    return path


def serve_dashboard(directory: Path, port: int, open_browser: bool) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    export_dashboard(directory / "index.html")
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    url = f"http://127.0.0.1:{port}/"
    print(json.dumps({"url": url, "bind": "127.0.0.1", "remote_network": False}, ensure_ascii=False, indent=2))
    if open_browser:
        threading.Timer(0.25, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="valueark", description="DIKWP FutureValue Ark OS")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="run a bundled synthetic portfolio")
    demo.add_argument("--workspace", default=".valueark-demo")
    demo.add_argument("--reset", action="store_true")

    analyze = sub.add_parser("analyze", help="analyze a portfolio JSON file")
    analyze.add_argument("portfolio")
    analyze.add_argument("--workspace", default=".valueark-run")
    analyze.add_argument("--reset", action="store_true")

    serve = sub.add_parser("serve", help="serve the offline dashboard on localhost only")
    serve.add_argument("--directory", default=".valueark-app")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--no-browser", action="store_true")

    export = sub.add_parser("export-html", help="write the standalone offline HTML application")
    export.add_argument("output", nargs="?", default="DIKWP_FUTURE_VALUE_ARK_v1.0.0.html")

    sub.add_parser("snapshot", help="print the bundled official-data reference snapshot")
    sub.add_parser("invariants", help="print non-negotiable execution boundaries")

    args = parser.parse_args(argv)
    if args.command == "demo":
        workspace = Path(args.workspace)
        if args.reset and workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True, exist_ok=True)
        result = run_analysis(_sample_path(workspace), workspace, reset=False)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "analyze":
        result = run_analysis(Path(args.portfolio), Path(args.workspace), reset=args.reset)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "serve":
        serve_dashboard(Path(args.directory), args.port, not args.no_browser)
        return 0
    if args.command == "export-html":
        path = export_dashboard(args.output)
        print(json.dumps({"output": str(path), "offline": True}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "snapshot":
        print(json.dumps(load_defaults()["market_snapshot"], ensure_ascii=False, indent=2))
        return 0
    if args.command == "invariants":
        print(json.dumps(load_defaults()["constitutional_invariants"], ensure_ascii=False, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
