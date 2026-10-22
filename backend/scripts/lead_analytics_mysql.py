#!/usr/bin/env python3
"""
lead_analytics_mysql.py

Pull Prospex lead data straight out of MySQL, crunch it with pandas, and write
a small analytics report (CSV + XLSX + console summary).

Usage
-----
    export MYSQL_URL="mysql+pymysql://prospex:prospex@127.0.0.1:3306/prospex?charset=utf8mb4"
    python lead_analytics_mysql.py --out reports
    python lead_analytics_mysql.py --url "$MYSQL_URL" --out reports
    python lead_analytics_mysql.py --demo            # no database needed

Requires: pandas, sqlalchemy, pymysql (openpyxl only for the XLSX report).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

DEFAULT_URL = os.getenv(
    "MYSQL_URL",
    "mysql+pymysql://prospex:prospex@127.0.0.1:3306/prospex?charset=utf8mb4",
)

LEADS_SQL = """
SELECT
    l.id             AS lead_id,
    l.score          AS score,
    l.status         AS status,
    l.source         AS source,
    l.is_duplicate   AS is_duplicate,
    l.created_at     AS created_at,
    i.name           AS icp_name,
    i.raw_input      AS icp_input,
    c.name           AS company_name,
    c.domain         AS domain,
    c.industry       AS industry,
    c.size           AS company_size,
    c.country        AS country,
    c.employee_count AS employees,
    c.annual_revenue AS revenue
FROM leads l
LEFT JOIN icps i      ON i.id = l.icp_id
LEFT JOIN companies c ON c.lead_id = l.id
WHERE l.is_duplicate = 0
ORDER BY l.id
"""

CONTACTS_SQL = """
SELECT
    ct.lead_id           AS lead_id,
    ct.full_name         AS full_name,
    ct.title             AS title,
    ct.email             AS email,
    ct.is_decision_maker AS is_decision_maker
FROM contacts ct
WHERE ct.lead_id IS NOT NULL
"""


# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
def load_from_mysql(url: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read leads + contacts from MySQL into pandas DataFrames."""
    engine = create_engine(url, pool_pre_ping=True, future=True)
    try:
        with engine.connect() as conn:
            leads = pd.read_sql_query(text(LEADS_SQL), conn)
            contacts = pd.read_sql_query(text(CONTACTS_SQL), conn)
    finally:
        engine.dispose()
    return leads, contacts


def demo_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fabricate a small dataset so the report can be tried without MySQL."""
    rng = pd.Series(range(240))
    statuses = ["new", "contacted", "qualified", "won", "lost"]
    sources = ["web", "crunchbase", "linkedin", "hunter"]
    industries = ["SaaS", "Fintech", "Healthtech", "E-commerce", "AI/ML"]
    company_sizes = ["11-50", "51-200", "201-500", "500+"]
    countries = ["US", "DE", "GB", "IN"]

    leads = pd.DataFrame(
        {
            "lead_id": rng + 1,
            "score": ((rng * 37) % 100).astype(float),
            "status": [statuses[i % len(statuses)] for i in rng],
            "source": [sources[i % len(sources)] for i in rng],
            "is_duplicate": 0,
            "created_at": pd.Timestamp("2026-01-05")
            + pd.to_timedelta(rng * 5, unit="h"),
            "icp_name": [f"ICP {i % 6 + 1}" for i in rng],
            "icp_input": "demo ICP",
            "company_name": [f"Acme {i}" for i in rng],
            "domain": [f"acme{i}.com" for i in rng],
            "industry": [industries[i % len(industries)] for i in rng],
            "company_size": [company_sizes[i % len(company_sizes)] for i in rng],
            "country": [countries[i % len(countries)] for i in rng],
            "employees": ((rng * 13) % 900 + 10).astype(int),
            "revenue": ((rng * 7919) % 50_000_000).astype(float),
        }
    )
    contacts = leads.loc[leads["score"] > 40, ["lead_id"]].copy()
    contacts["full_name"] = "Demo Contact"
    contacts["title"] = "VP Sales"
    contacts["email"] = "demo@example.com"
    contacts["is_decision_maker"] = 1
    return leads, contacts


# --------------------------------------------------------------------------- #
# pandas transforms
# --------------------------------------------------------------------------- #
def clean_leads(leads: pd.DataFrame) -> pd.DataFrame:
    df = leads.copy()
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["score"] = (
        pd.to_numeric(df["score"], errors="coerce").fillna(0).clip(lower=0, upper=100)
    )
    df["employees"] = pd.to_numeric(df["employees"], errors="coerce")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    for col in ("status", "source", "industry", "country", "company_name"):
        if col in df.columns:
            df[col] = df[col].fillna("unknown").replace("", "unknown")
    df["score_band"] = pd.cut(
        df["score"],
        bins=[-1, 39, 59, 79, 100],
        labels=["low (0-39)", "medium (40-59)", "high (60-79)", "hot (80-100)"],
    )
    return df


def _grouped(df: pd.DataFrame, by: str, label: str, top: int | None = None) -> pd.DataFrame:
    out = (
        df.groupby(by, dropna=False, observed=False)
        .agg(
            leads=("lead_id", "count"),
            avg_score=("score", "mean"),
            hot_leads=("score", lambda s: int((s >= 80).sum())),
        )
        .reset_index()
        .rename(columns={by: label})
    )
    out["pct"] = (out["leads"] / max(len(df), 1) * 100).round(1)
    out["avg_score"] = out["avg_score"].round(1).fillna(0.0)
    out = out.sort_values(["leads", "avg_score"], ascending=False).reset_index(drop=True)
    return out.head(top) if top else out


def build_report(leads: pd.DataFrame, contacts: pd.DataFrame) -> dict[str, pd.DataFrame]:
    df = clean_leads(leads)

    funnel = _grouped(df, "status", "status")
    sources = _grouped(df, "source", "source")
    industries = _grouped(df, "industry", "industry", top=10)
    countries = _grouped(df, "country", "country", top=10)
    bands = _grouped(df, "score_band", "score_band")

    dated = df.dropna(subset=["created_at"]).copy()
    if dated.empty:
        weekly = pd.DataFrame(columns=["week", "leads", "avg_score", "hot_leads"])
    else:
        dated["week"] = dated["created_at"].dt.to_period("W-MON").dt.start_time
        weekly = (
            dated.groupby("week")
            .agg(
                leads=("lead_id", "count"),
                avg_score=("score", "mean"),
                hot_leads=("score", lambda s: int((s >= 80).sum())),
            )
            .reset_index()
        )
        weekly["avg_score"] = weekly["avg_score"].round(1)

    if contacts.empty:
        contacted: set[int] = set()
        decision_makers = contacts
        with_email = contacts
    else:
        contacted = set(pd.to_numeric(contacts["lead_id"], errors="coerce").dropna().astype(int))
        decision_makers = contacts[
            pd.to_numeric(contacts["is_decision_maker"], errors="coerce").fillna(0).astype(int) == 1
        ]
        with_email = contacts[contacts["email"].fillna("").str.contains("@")]

    coverage = pd.DataFrame(
        [
            {"metric": "leads in report", "value": len(df)},
            {"metric": "leads with at least one contact", "value": len(df[df["lead_id"].isin(contacted)])},
            {"metric": "contacts found", "value": len(contacts)},
            {"metric": "decision-maker contacts", "value": len(decision_makers)},
            {"metric": "contacts with an email", "value": len(with_email)},
            {"metric": "average lead score", "value": round(float(df["score"].mean()) if len(df) else 0, 1)},
            {"metric": "median lead score", "value": round(float(df["score"].median()) if len(df) else 0, 1)},
        ]
    )

    return {
        "leads": df.drop(columns=["score_band"]),
        "funnel": funnel,
        "sources": sources,
        "industries": industries,
        "countries": countries,
        "score_bands": bands,
        "weekly": weekly,
        "coverage": coverage,
    }


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
def write_outputs(report: dict[str, pd.DataFrame], out_dir: Path, with_excel: bool) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    report["leads"].to_csv(out_dir / "leads_raw.csv", index=False)
    for name, frame in report.items():
        if name != "leads":
            frame.to_csv(out_dir / f"{name}.csv", index=False)

    if not with_excel:
        return
    try:
        import openpyxl  # noqa: F401  (validates the optional dependency)
    except ImportError:
        print("! openpyxl is not installed - skipping the XLSX report", file=sys.stderr)
        return

    xlsx_path = out_dir / "lead_report.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        for sheet in ("funnel", "sources", "industries", "countries", "score_bands", "weekly", "coverage"):
            report[sheet].to_excel(writer, sheet_name=sheet[:31], index=False)
    print(f"  wrote {xlsx_path}")


def print_summary(report: dict[str, pd.DataFrame]) -> None:
    """A tiny terminal dashboard - no tabulate dependency required."""
    print("\n=== Prospex lead analytics ===")
    for title in ("funnel", "sources", "industries", "score_bands"):
        frame = report[title]
        print(f"\n-- {title} --")
        print(frame.to_string(index=False) if not frame.empty else "(no data)")

    print("\n-- coverage --")
    for _, row in report["coverage"].iterrows():
        print(f"{row['metric']:<38} {row['value']:>8g}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pandas + MySQL analytics report for Prospex leads.")
    parser.add_argument("--url", default=DEFAULT_URL, help="SQLAlchemy MySQL URL (default: $MYSQL_URL)")
    parser.add_argument("--out", default="reports", type=Path, help="output directory (default: reports)")
    parser.add_argument("--demo", action="store_true", help="use generated data instead of MySQL")
    parser.add_argument("--no-excel", action="store_true", help="only write CSV files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.demo:
        print("Using generated demo data (no MySQL connection).")
        leads, contacts = demo_frames()
    else:
        safe_url = args.url.split("@")[-1] if "@" in args.url else args.url
        print(f"Connecting to database: {safe_url}")
        try:
            leads, contacts = load_from_mysql(args.url)
        except Exception as exc:  # pragma: no cover - depends on the environment
            print(f"! Could not read from MySQL: {exc}", file=sys.stderr)
            print("  Check MYSQL_URL / --url, or run with --demo to see the report format.", file=sys.stderr)
            return 1

    if leads.empty:
        print("No leads found - nothing to report.")
        return 0

    report = build_report(leads, contacts)
    print_summary(report)
    write_outputs(report, args.out, with_excel=not args.no_excel)

    print(f"\nDone. {len(leads)} leads written to {args.out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
