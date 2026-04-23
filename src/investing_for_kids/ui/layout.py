"""Top-level Streamlit layout for the investing_for_kids app."""

import streamlit as st

from investing_for_kids.accounts import views as account_views
from investing_for_kids.accounts.config import load_accounts
from investing_for_kids.theoretical import views as theoretical_views


def render() -> None:
    """Render the top-level tabbed layout: Theory + one tab per configured child."""
    st.set_page_config(page_title="Investing for Kids", layout="wide")
    st.title("Investing for Kids")

    accounts = load_accounts()
    tab_names = ["Theory"] + [acc.display_name for acc in accounts.values()]
    tabs = st.tabs(tab_names)

    with tabs[0]:
        theoretical_views.render()

    for tab, account in zip(tabs[1:], accounts.values(), strict=True):
        with tab:
            account_views.render(account)
