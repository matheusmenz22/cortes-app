"""Sobe a interface web local: python -m cortes_app.web"""

from __future__ import annotations


def main() -> None:
    import uvicorn

    print("cortes-app: interface em http://localhost:8000  (Ctrl+C para parar)")
    uvicorn.run("cortes_app.web.app:app", host="127.0.0.1", port=8000, log_level="warning")


if __name__ == "__main__":
    main()
