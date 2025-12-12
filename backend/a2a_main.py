"""Main entry point for A2A framework agents - similar to AgentBeats framework example."""

import typer
import os
from a2a_green_agent import start_green_agent
from a2a_white_agent import start_white_agent
from pydantic_settings import BaseSettings


class AgentSettings(BaseSettings):
    role: str = os.getenv("ROLE", "unspecified")
    host: str = os.getenv("HOST", "0.0.0.0")
    agent_port: int = int(os.getenv("AGENT_PORT", "8001"))


app = typer.Typer(help="Green Agent - A2A Framework compatible")


@app.command()
def green():
    """Start the green agent (assessment manager)."""
    start_green_agent(host="0.0.0.0", port=8001)


@app.command()
def white():
    """Start the white agent (target being tested)."""
    start_white_agent(host="0.0.0.0", port=8002)


@app.command()
def run():
    """Run agent based on ROLE environment variable."""
    settings = AgentSettings()
    if settings.role == "green":
        start_green_agent(host=settings.host, port=settings.agent_port)
    elif settings.role == "white":
        start_white_agent(host=settings.host, port=settings.agent_port)
    else:
        raise ValueError(f"Unknown role: {settings.role}. Set ROLE=green or ROLE=white")


if __name__ == "__main__":
    app()

