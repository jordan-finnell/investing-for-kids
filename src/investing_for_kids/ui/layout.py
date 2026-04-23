"""Top-level Streamlit layout for the investing_for_kids app."""

import streamlit as st

from investing_for_kids.theoretical import views as theoretical_views


def render() -> None:
    """Render the top-level tabbed layout: Theory, Child A, Child B."""
    st.set_page_config(page_title="Investing for Kids", layout="wide")
    st.title("Investing for Kids")

    theory_tab, child_a_tab, child_b_tab = st.tabs(["Theory", "Child A", "Child B"])

    with theory_tab:
        theoretical_views.render()

    with child_a_tab:
        st.header("Child A's account")
        st.info("Coming in Phase 3 — balance, transactions, history.")

    with child_b_tab:
        st.header("Child B's account")
        st.info("Coming in Phase 3 — balance, transactions, history.")
