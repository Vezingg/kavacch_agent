"""
Entry point for the Translation API.

Run with:
    python -m box_retail_agent.appliation.transaltion

Or directly via uvicorn:
    uvicorn box_retail_agent.appliation.transaltion.main:app --host 0.0.0.0 --port 8081
"""

import os
import uvicorn


def main():
    host = os.getenv("TRANSLATION_API_HOST", "0.0.0.0")
    port = int(os.getenv("TRANSLATION_API_PORT", "8081"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()

    uvicorn.run(
        "box_retail_agent.appliation.transaltion.main:app",
        host=host,
        port=port,
        log_level=log_level,
    )


if __name__ == "__main__":
    main()
