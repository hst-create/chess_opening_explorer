from __future__ import annotations

import csv
from pathlib import Path
from urllib.parse import quote

from .analysis import Finding


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def lichess_analysis_url(fen: str) -> str:
    return f"https://lichess.org/analysis/standard/{quote(fen.replace(' ', '_'), safe='_')}"


def write_markdown(findings: list[Finding], output: Path, sort: str) -> None:
    ordered = sort_findings(findings, sort)
    lines = [
        "# Lichess Opening Analyzer Report",
        "",
        "| Line | Move Played | Times | Explorer Score | Best Alternative | Best Score | Delta | Impact | Explorer Games | Analysis |",
        "|---|---|---:|---:|---|---:|---:|---:|---:|---|",
    ]
    for finding in ordered:
        lines.append(
            f"| {finding.move.line_san or finding.move.move_san} | {finding.move.move_san} | {finding.move.count} | {percent(finding.played_score)} | "
            f"{finding.best_alternative.san} | {percent(finding.best_score)} | {percent(finding.delta)} | "
            f"{finding.impact:.2f} | {finding.explorer_total} | [Lichess]({lichess_analysis_url(finding.move.fen)}) |"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(findings: list[Finding], output: Path, sort: str) -> None:
    ordered = sort_findings(findings, sort)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["line", "move_played", "times", "explorer_score", "best_alternative", "best_score", "delta", "impact", "explorer_games", "analysis_url", "fen"])
        writer.writeheader()
        for finding in ordered:
            writer.writerow({
                "line": finding.move.line_san or finding.move.move_san,
                "move_played": finding.move.move_san,
                "times": finding.move.count,
                "explorer_score": f"{finding.played_score:.4f}",
                "best_alternative": finding.best_alternative.san,
                "best_score": f"{finding.best_score:.4f}",
                "delta": f"{finding.delta:.4f}",
                "impact": f"{finding.impact:.4f}",
                "explorer_games": finding.explorer_total,
                "analysis_url": lichess_analysis_url(finding.move.fen),
                "fen": finding.move.fen,
            })


def sort_findings(findings: list[Finding], sort: str) -> list[Finding]:
    if sort == "impact":
        return sorted(findings, key=lambda item: item.impact, reverse=True)
    return sorted(findings, key=lambda item: item.best_score - item.played_score, reverse=True)
