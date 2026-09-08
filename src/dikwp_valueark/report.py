from __future__ import annotations

if __package__:
    from ._ui_presentation import localize_html as _ui_localize_html
else:
    from _ui_presentation import localize_html as _ui_localize_html


import html
from pathlib import Path
from typing import Any


def _pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def _money(value: float, currency: str) -> str:
    symbols = {"CNY": "¥", "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥"}
    return f"{symbols.get(currency, currency + ' ')}{value:,.0f}"


def markdown_report(analysis: dict[str, Any]) -> str:
    currency = analysis["settings"].get("currency", "CNY")
    tm = analysis["target_metrics"]
    cm = analysis["current_metrics"]
    lines = [
        "# DIKWP FutureValue Ark — 资产韧性分析报告",
        "",
        "> 本报告是教育与决策支持，不是个性化证券推荐、收益保证、法律或税务意见。软件不连接券商，也不执行交易。",
        "",
        f"- 分析组合：{analysis['generated_from']}",
        f"- 组合总额：{_money(analysis['portfolio_total'], currency)}",
        f"- 风险档案：{analysis['profile']['name_zh']}",
        f"- 应急流动性底线：{_pct(analysis['liquidity_floor_weight'])}",
        f"- 情景权重是否为真实概率：否",
        "",
        "## 关键结果",
        "",
        "| 指标 | 当前 | 目标 |",
        "|---|---:|---:|",
        f"| 最差情景实际回报 | {_pct(cm['worst_case'])} | {_pct(tm['worst_case'])} |",
        f"| 尾部25%均值（CVaR） | {_pct(cm['cvar_25'])} | {_pct(tm['cvar_25'])} |",
        f"| 情景加权均值 | {_pct(cm['weighted_mean'])} | {_pct(tm['weighted_mean'])} |",
        f"| 假设驱动长期实际回报 | {_pct(cm['long_run_real'])} | {_pct(tm['long_run_real'])} |",
        f"| 流动性权重 | {_pct(cm['liquidity_weight'])} | {_pct(tm['liquidity_weight'])} |",
        f"| AI/科技集中仓 | {_pct(cm['ai_weight'])} | {_pct(tm['ai_weight'])} |",
        f"| 声明情景财富底线（非保证） | {_money(cm['real_wealth_floor'], currency)} | {_money(tm['real_wealth_floor'], currency)} |",
        "",
        "## 目标区间与再平衡",
        "",
        "| 资产类别 | 当前 | 目标区间 | 目标 | 金额差异 | 动作 |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in analysis["rebalance_plan"]:
        r = row["target_range"]
        lines.append(
            f"| {row['asset_name_zh']} | {_pct(row['current_weight'])} | {_pct(r['lower'])}–{_pct(r['upper'])} | {_pct(row['target_weight'])} | {_money(row['difference'], currency)} | {row['action']} |"
        )
    lines += ["", "## 多世界压力测试", "", "| 情景 | 重要性权重 | 当前实际回报 | 目标实际回报 | 目标情景后价值 |", "|---|---:|---:|---:|---:|"]
    for row in analysis["scenario_outcomes"]:
        lines.append(
            f"| {row['scenario_name_zh']} | {_pct(row['importance_weight'])} | {_pct(row['current_real_return'])} | {_pct(row['target_real_return'])} | {_money(row['target_value_after_scenario'], currency)} |"
        )
    lines += ["", "## 风险提示", ""]
    for warning in analysis["warnings"]:
        lines.append(f"- **{warning['level']} / {warning['code']}**：{warning['message_zh']}")
    lines += [
        "",
        "## 决策纪律",
        "",
        "1. 先核对账户、存款保险、产品信用、税务与提款约束，再实施任何调整。",
        "2. 优先用新增现金流回到目标区间，避免为追求精确权重制造不必要交易和税费。",
        "3. 对高波动主题仓设硬上限，不用杠杆，不以短期涨幅提高风险预算。",
        "4. 每6—12个月或越过区间时复核；重大生活变化时立即重算。",
        "5. 任何无法理解、无法独立验证、无法退出或收费不透明的产品都不应由本软件自动纳入。",
        "",
        "## 方法边界",
        "",
    ]
    lines.extend(f"- {item}" for item in analysis["limitations"])
    return "\n".join(lines) + "\n"


def html_report(analysis: dict[str, Any]) -> str:
    md = markdown_report(analysis)
    # Deliberately simple, dependency-free rendering: paragraphs and preformatted tables remain readable.
    body = html.escape(md)
    return _ui_localize_html(f"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>FutureValue Ark Report</title><style>body{{font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans SC',sans-serif;max-width:1080px;margin:2rem auto;padding:0 1rem;color:#17222d;background:#f7f9fb}}pre{{white-space:pre-wrap;background:white;border:1px solid #d9e1e8;border-radius:12px;padding:1.4rem;line-height:1.55}}.banner{{background:#17324d;color:white;padding:1rem 1.4rem;border-radius:12px;margin-bottom:1rem}}</style></head><body><div class='banner'><strong>DIKWP FutureValue Ark OS v1.0.0</strong><br>Educational decision support only · no automatic trading</div><pre>{body}</pre></body></html>""")


def write_reports(workspace: str | Path, analysis: dict[str, Any]) -> dict[str, str]:
    path = Path(workspace)
    path.mkdir(parents=True, exist_ok=True)
    md_path = path / "valueark-report.md"
    html_path = path / "valueark-report.html"
    md_path.write_text(_ui_localize_html(markdown_report(analysis)), encoding="utf-8")
    html_path.write_text(_ui_localize_html(html_report(analysis)), encoding="utf-8")
    return {"markdown": str(md_path), "html": str(html_path)}
