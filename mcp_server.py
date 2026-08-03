import requests
from mcp.server.fastmcp import FastMCP
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DESIGN_REFERENCE_", env_file=".env", extra="ignore")

    backend_url: str = "http://localhost:8000"
    api_key: str | None = None


settings = Settings()

mcp = FastMCP("design-reference")


def _headers() -> dict[str, str]:
    if not settings.api_key:
        raise ValueError(
            "No API key set. Sign up and create a key, then set "
            "DESIGN_REFERENCE_API_KEY in the environment or a .env file."
        )
    return {"X-API-Key": settings.api_key}


@mcp.tool()
def list_references(block_type: str | None = None) -> list[dict]:
    """List available design references, optionally filtered by block type (header or hero)."""
    params = {"block_type": block_type} if block_type else {}
    response = requests.get(
        f"{settings.backend_url}/references", params=params, headers=_headers(), timeout=10
    )
    if response.status_code == 401:
        raise ValueError("API key is invalid or has been revoked. Get a new one from the dashboard.")
    response.raise_for_status()
    return response.json()


@mcp.tool()
def get_design_system(reference_ids: list[str]) -> dict:
    """Get design tokens and structural skeletons for the given reference ids, grouped by block type."""
    response = requests.get(
        f"{settings.backend_url}/design-system",
        params={"ref_ids": ",".join(reference_ids)},
        headers=_headers(),
        timeout=10,
    )
    if response.status_code == 401:
        raise ValueError("API key is invalid or has been revoked. Get a new one from the dashboard.")
    if response.status_code == 404:
        raise ValueError(response.json()["detail"])
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    mcp.run()
