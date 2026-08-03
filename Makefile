.PHONY: install run test

install:
	uv sync

run:
	uv run python mcp_server.py

test:
	uv run pytest
