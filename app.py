"""
Streamlit app – Masterliste Updater
====================================
Entry point. All logic lives in sub-packages:

  core/   – pure-Python helpers (config, I/O, PDF parsing, data transforms)
  ui/     – Streamlit rendering functions (sidebar, results)
"""

from __future__ import annotations

import streamlit as st

from core import (
    COL,
    load_csv_bytes,
    parse_pdf_fees,
    parse_membership,
    build_new_members,
    slice_outputs,
)
from ui import render_sidebar, render_results

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Masterliste Updater",
    page_icon="📋",
    layout="wide",
)

st.title("📋 Masterliste Updater")
st.markdown(
    "Upload the export files and the PDF fee schedule, then download the "
    "generated masterlists."
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
inputs = render_sidebar()

# ── Guard: all files required ──────────────────────────────────────────────────
if not all([inputs.bestellungen_f, inputs.kontakte_f, inputs.pdf_f]):
    st.info("Upload all three files in the sidebar, then click **▶ Run**.")
    st.stop()

if not inputs.run_btn and "results" not in st.session_state:
    st.info("Files ready. Click **▶ Run** in the sidebar to proceed.")
    st.stop()

# ── Processing ─────────────────────────────────────────────────────────────────
if inputs.run_btn:
    with st.spinner("Processing…"):
        try:
            bestellungen = load_csv_bytes(inputs.bestellungen_f.read(), "Bestellungen")
            kontakte = load_csv_bytes(inputs.kontakte_f.read(), "Kontakte")
            fee_lookup, mem_col, espn_ipna_col, ipna_amt_col = parse_pdf_fees(
                inputs.pdf_f.read()
            )
        except Exception as exc:
            st.error(f"Error loading files: {exc}")
            st.stop()

        email_l, email_r = COL["email"], COL["contact_email"]
        if email_l not in bestellungen.columns:
            st.error(f"Column '{email_l}' not found in Orders.")
            st.stop()
        if email_r not in kontakte.columns:
            st.error(f"Column '{email_r}' not found in Contacts.")
            st.stop()

        merged = bestellungen.merge(
            kontakte, left_on=email_l, right_on=email_r, how="left"
        )
        merged["Membership"] = merged[COL["item"]].apply(parse_membership)

        new_members = build_new_members(merged, fee_lookup, ipna_amt_col)
        ipna_out, neue_out, voll_out = slice_outputs(new_members)

        st.session_state["results"] = {
            "new_members": new_members,
            "ipna_out": ipna_out,
            "neue_out": neue_out,
            "voll_out": voll_out,
        }

    st.success("Done!")

# ── Results ────────────────────────────────────────────────────────────────────
if "results" not in st.session_state:
    st.stop()

render_results(st.session_state["results"])
