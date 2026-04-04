"""
Results UI: summary metrics, new-members preview, per-masterliste tabs and downloads.
"""

from __future__ import annotations

import streamlit as st

from core.io import df_to_csv_bytes, df_to_excel_bytes

# (filename, session-state key, download encoding)
_MASTERLISTE_CONFIG = [
    ("IPNA Masterliste", "ipna_out", "IPNA Masterliste.csv", "windows-1252"),
]


def render_results(res: dict) -> None:
    """Render the full results section from the *res* dict stored in session state."""

    # ── Summary ────────────────────────────────────────────────────────────────
    st.subheader("Summary")
    st.metric("New members found", len(res["new_members"]))

    st.write("---")

    # ── New members preview ────────────────────────────────────────────────────
    st.subheader("New members")
    st.dataframe(
        res["new_members"].drop(columns=["IPNA amount"], errors="ignore"),
        width="stretch",
    )
    st.download_button(
        label="⬇ Download New Members.xlsx",
        data=df_to_excel_bytes(res["new_members"], sheet_name="NewMembers"),
        file_name="New Members.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="dl_xlsx_new_members",
    )

    st.write("---")

    # ── Per-masterliste tabs ───────────────────────────────────────────────────
    tab_labels = [label for label, _, _, _ in _MASTERLISTE_CONFIG]
    tabs = st.tabs(tab_labels)

    for tab, (label, key, filename, enc) in zip(tabs, _MASTERLISTE_CONFIG):
        df = res[key]
        with tab:
            st.caption(f"{len(df)} row(s)")
            st.data_editor(
                df,
                width="stretch",
                num_rows="dynamic",
                key=f"editor_{key}",
            )

            excel_filename = filename.replace(".csv", ".xlsx")
            st.download_button(
                label=f"⬇ Download {excel_filename}",
                data=df_to_excel_bytes(df),
                file_name=excel_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_xlsx_{key}",
            )

            st.download_button(
                label=f"⬇ Download {filename}",
                data=df_to_csv_bytes(df, encoding=enc),
                file_name=filename,
                mime="text/csv",
                key=f"dl_{key}",
            )
