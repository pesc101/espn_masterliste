"""Results UI: New Members and IPNA output previews and downloads."""

from __future__ import annotations

import streamlit as st

from core.io import df_to_csv_bytes, df_to_excel_bytes


def render_results(res: dict) -> None:
    """Render the full results section from the *res* dict stored in session state."""

    new_members_public = res["neue_out"]
    ipna_out = res["ipna_out"]

    # ── Summary ────────────────────────────────────────────────────────────────
    st.subheader("Summary")
    st.metric("New members found", len(new_members_public))

    st.write("---")

    # ── New members preview ────────────────────────────────────────────────────
    st.subheader("New members")
    st.dataframe(
        new_members_public,
        width="stretch",
    )
    st.download_button(
        label="⬇ Download New Members.xlsx",
        data=df_to_excel_bytes(new_members_public, sheet_name="NewMembers"),
        file_name="New Members.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="dl_xlsx_new_members",
    )

    st.write("---")

    # ── IPNA output ────────────────────────────────────────────────────────────
    st.subheader("IPNA Masterliste")
    st.caption(f"{len(ipna_out)} row(s)")
    st.data_editor(
        ipna_out,
        width="stretch",
        num_rows="dynamic",
        key="editor_ipna_out",
    )

    st.download_button(
        label="⬇ Download IPNA Masterliste.xlsx",
        data=df_to_excel_bytes(ipna_out),
        file_name="IPNA Masterliste.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="dl_xlsx_ipna_out",
    )

    st.download_button(
        label="⬇ Download IPNA Masterliste.csv",
        data=df_to_csv_bytes(ipna_out, encoding="windows-1252"),
        file_name="IPNA Masterliste.csv",
        mime="text/csv",
        key="dl_ipna_out",
    )
