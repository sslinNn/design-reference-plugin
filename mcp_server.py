import os

import requests
from mcp.server.fastmcp import FastMCP

BACKEND_URL = os.environ.get("DESIGN_REFERENCE_BACKEND_URL", "http://localhost:8000")

mcp = FastMCP("design-reference")


@mcp.tool()
def list_references(block_type: str | None = None) -> list[dict]:
    """List available design references, optionally filtered by block type (header or hero)."""
    params = {"block_type": block_type} if block_type else {}
    response = requests.get(f"{BACKEND_URL}/references", params=params, timeout=10)
    response.raise_for_status()
    return response.json()


@mcp.tool()
def get_design_system(reference_ids: list[str]) -> dict:
    """Get design tokens and structural skeletons for the given reference ids, grouped by block type."""
    response = requests.get(
        f"{BACKEND_URL}/design-system",
        params={"ref_ids": ",".join(reference_ids)},
        timeout=10,
    )
    if response.status_code == 404:
        raise ValueError(response.json()["detail"])
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    mcp.run()
