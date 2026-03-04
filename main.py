#!/usr/bin/env python3
"""
Update ESPN/IPNA membership masterlists from order and contact exports.

Usage
-----
python main.py \\
    --bestellungen  "data/Orders (8).csv" \\
    --kontakte      "data/contacts (10).csv" \\
    --pdf           "data/beitrage_2026.pdf"

All three --bestellungen / --kontakte / --pdf arguments are required.
The masterliste paths default to the standard filenames inside --data-dir
but can be overridden individually.

Run  python main.py --help  for the full option list.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from membership import (
    load_csv,
    parse_fee_schedule,
    parse_membership,
    build_new_members,
    update_list,
)
from membership.config import COL


# ── Argument parsing ──────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="main.py",
        description="Update ESPN/IPNA membership masterlists from order exports.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Required inputs
    req = p.add_argument_group("required inputs")
    req.add_argument(
        "-b",
        "--bestellungen",
        required=True,
        metavar="CSV",
        help="Orders export CSV (Bestellungen).",
    )
    req.add_argument(
        "-k",
        "--kontakte",
        required=True,
        metavar="CSV",
        help="Contacts export CSV (Kontakte).",
    )
    req.add_argument(
        "-p",
        "--pdf",
        required=True,
        metavar="PDF",
        help="Fee-schedule PDF (e.g. beitrage_2026.pdf).",
    )

    # Masterliste paths (default to standard names in the same directory as bestellungen)
    ml = p.add_argument_group(
        "masterliste files (default: same directory as --bestellungen)"
    )
    ml.add_argument(
        "--ipna-ml",
        metavar="CSV",
        default=None,
        help="IPNA Masterliste CSV (in/out).",
    )
    ml.add_argument(
        "--neue-ml",
        metavar="CSV",
        default=None,
        help="Masterliste neue Mitglieder CSV (in/out).",
    )
    ml.add_argument(
        "--voll-ml",
        metavar="CSV",
        default=None,
        help="Masterliste_full CSV (in/out).",
    )

    # Encodings
    enc = p.add_argument_group("encodings (override defaults only if needed)")
    enc.add_argument("--enc-bestellungen", default="utf-8", metavar="ENC")
    enc.add_argument("--enc-kontakte", default="utf-8", metavar="ENC")
    enc.add_argument("--enc-ipna", default="windows-1252", metavar="ENC")
    enc.add_argument("--enc-neue", default="windows-1250", metavar="ENC")
    enc.add_argument("--enc-voll", default="windows-1252", metavar="ENC")

    # Behaviour flags
    p.add_argument(
        "--export",
        metavar="FILE",
        default=None,
        help=(
            "Export the resolved new-member rows to a file before updating the "
            "masterlists. Extension determines format: .csv (default) or .xlsx. "
            "When omitted no standalone export is written."
        ),
    )
    p.add_argument(
        "--export-format",
        choices=["csv", "xlsx"],
        default=None,
        help="Force export format regardless of file extension (csv or xlsx).",
    )
    p.add_argument(
        "--enc-export",
        default="utf-8-sig",
        metavar="ENC",
        help="Encoding for the CSV export (ignored for xlsx).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Parse and merge data but do not write any files.",
    )

    return p


# ── Helpers ───────────────────────────────────────────────────────────────────────


def _resolve_ml_path(explicit: str | None, data_dir: Path, default_name: str) -> Path:
    """Use the explicit path when given, otherwise build a default from data_dir."""
    return Path(explicit) if explicit else data_dir / default_name


def _check_file(path: Path) -> None:
    if not path.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(1)


def _export_new_members(
    df,
    out_path: str,
    fmt: str | None,
    encoding: str,
) -> None:
    """
    Write *df* to *out_path* as CSV or Excel.

    Format is determined by *fmt* when given, otherwise inferred from the
    file extension (.xlsx → Excel, anything else → CSV).
    """

    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    resolved_fmt = fmt or ("xlsx" if path.suffix.lower() == ".xlsx" else "csv")

    if resolved_fmt == "xlsx":
        df.to_excel(out_path, index=False, engine="openpyxl")
    else:
        df.to_csv(out_path, sep=";", index=False, encoding=encoding)

    print(
        "\n── Export ─────────────────────────────────────────────────────────────────"
    )
    print(f"  {len(df)} row(s) written → {out_path}  [{resolved_fmt}]")


# ── Main ──────────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    data_dir = Path(args.bestellungen).parent

    # Resolve masterliste paths
    ipna_path = _resolve_ml_path(args.ipna_ml, data_dir, "IPNA Masterliste.csv")
    neue_path = _resolve_ml_path(
        args.neue_ml, data_dir, "Masterliste neue Mitglieder.csv"
    )
    voll_path = _resolve_ml_path(args.voll_ml, data_dir, "Masterliste_full.csv")

    # Validate all inputs exist
    for p in [
        Path(args.bestellungen),
        Path(args.kontakte),
        Path(args.pdf),
        ipna_path,
        neue_path,
        voll_path,
    ]:
        _check_file(p)

    # ── Load source data ──────────────────────────────────────────────────────────
    print("\n── Loading data ─────────────────────────────────────────────────────────")
    bestellungen = load_csv(args.bestellungen, encoding=args.enc_bestellungen)
    kontakte = load_csv(args.kontakte, encoding=args.enc_kontakte)
    ipna_ml = load_csv(str(ipna_path), encoding=args.enc_ipna, sep=";")
    neue_ml = load_csv(str(neue_path), encoding=args.enc_neue, sep=";")
    voll_ml = load_csv(str(voll_path), encoding=args.enc_voll, sep=";")

    print(f"  Bestellungen : {len(bestellungen)} rows")
    print(f"  Kontakte     : {len(kontakte)} rows")
    print(f"  IPNA ML      : {len(ipna_ml)} rows")
    print(f"  Neue ML      : {len(neue_ml)} rows")
    print(f"  Voll ML      : {len(voll_ml)} rows")

    # ── Parse PDF fee schedule ────────────────────────────────────────────────────
    print("\n── Parsing fee schedule ─────────────────────────────────────────────────")
    fee_lookup, ipna_amt_col = parse_fee_schedule(args.pdf)

    # ── Merge orders + contacts ───────────────────────────────────────────────────
    print("\n── Merging orders + contacts ────────────────────────────────────────────")
    email_l, email_r = COL["email"], COL["contact_email"]
    for col, df, name in [
        (email_l, bestellungen, "Bestellungen"),
        (email_r, kontakte, "Kontakte"),
    ]:
        if col not in df.columns:
            print(
                f"ERROR: Email column '{col}' not found in {name}.\n"
                f"  Available: {df.columns.tolist()}",
                file=sys.stderr,
            )
            sys.exit(1)

    merged = bestellungen.merge(kontakte, left_on=email_l, right_on=email_r, how="left")
    merged["Membership"] = merged[COL["item"]].apply(parse_membership)

    new_members = build_new_members(merged, fee_lookup, ipna_amt_col)
    print(f"  New members to process: {len(new_members)}")

    # ── Export new_members ────────────────────────────────────────────────────────
    if args.export:
        _export_new_members(
            new_members, args.export, args.export_format, args.enc_export
        )

    if args.dry_run:
        print(
            "\n── Dry run – no files written ───────────────────────────────────────────"
        )
        print(new_members.to_string())
        return

    # ── Update masterlists ────────────────────────────────────────────────────────
    print("\n── Updating masterlists ─────────────────────────────────────────────────")
    update_list(
        ipna_ml,
        new_members,
        str(ipna_path),
        args.enc_ipna,
        label="IPNA Masterliste",
    )
    update_list(
        neue_ml,
        new_members,
        str(neue_path),
        args.enc_neue,
        label="Masterliste neue Mitglieder",
    )
    update_list(
        voll_ml,
        new_members,
        str(voll_path),
        args.enc_voll,
        label="Masterliste Vollständige Liste",
    )

    print("\n── Done ─────────────────────────────────────────────────────────────────")


if __name__ == "__main__":
    main()
