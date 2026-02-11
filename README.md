# Waktu Solat MCP

MCP server for Malaysian prayer times via [api.waktusolat.app](https://api.waktusolat.app). Works with Claude, Cursor, and other MCP clients.

**Tools:** `get_prayer_times_today`, `get_prayer_times_month`, `get_next_prayer`, `list_zones`

## Local (stdio)

```bash
uv sync
uv run waktusolat-mcp
```

Claude Desktop config:
```json
{
  "mcpServers": {
    "waktusolat": {
      "command": "uv",
      "args": ["--directory", "/path/to/waktu-solat-mcp", "run", "waktusolat-mcp"]
    }
  }
}
```

## Hosted (HTTP)

Run with HTTP transport to serve a web UI with "Add to Cursor" / "Add to Claude" buttons:

```bash
uv run waktusolat-mcp-http
```

Or: `MCP_TRANSPORT=streamable-http uv run waktusolat-mcp`

- **Web UI:** `http://localhost:8000/`
- **MCP endpoint:** `http://localhost:8000/mcp`

Deploy to Railway, Render, etc. Set `PORT` (PaaS usually provides this). The app binds to `0.0.0.0` and uses `PORT` automatically. If behind a proxy, set `MCP_BASE_URL` to your public URL (e.g. `https://your-app.railway.app`) so install links use the correct URL.

## Docker

```bash
docker compose up --build
# Web UI: http://localhost:8000/
# MCP: http://localhost:8000/mcp
```
