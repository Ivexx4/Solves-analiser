"""ASGI entry point for Vercel and direct Python launches."""

import streamlit as st


app = st.App("dashboard.py")


if __name__ == "__main__":
    app.run()
