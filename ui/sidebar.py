"""
Sidebar UI: file uploaders and the run button.
"""

from __future__ import annotations

from typing import NamedTuple

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile


class SidebarInputs(NamedTuple):
    bestellungen_f: UploadedFile | None
    kontakte_f: UploadedFile | None
    pdf_f: UploadedFile | None
    run_btn: bool


def render_sidebar() -> SidebarInputs:
    """Render the sidebar widgets and return the uploaded files plus the run button state."""
    with st.sidebar:
        st.header("Upload files")

        bestellungen_f = st.file_uploader("Bestellungen CSV", type=["csv"])
        kontakte_f = st.file_uploader("Kontakte CSV", type=["csv"])
        st.write("---")
        pdf_f = st.file_uploader("Beiträge PDF (fee schedule)", type=["pdf"])

        run_btn = st.button(
            "▶ Run",
            type="primary",
            disabled=not all([bestellungen_f, kontakte_f, pdf_f]),
        )

    return SidebarInputs(
        bestellungen_f=bestellungen_f,
        kontakte_f=kontakte_f,
        pdf_f=pdf_f,
        run_btn=run_btn,
    )
