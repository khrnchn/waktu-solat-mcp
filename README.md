# Waktu Solat MCP

MCP server for Malaysian prayer times via [api.waktusolat.app](https://api.waktusolat.app). Works with Claude Desktop, Cursor, and other MCP clients.

**Tools:** `get_prayer_times_today`, `get_prayer_times_month`, `get_next_prayer`, `list_zones`

## Setup

```bash
uv sync
uv run waktusolat-mcp
```

## Claude Desktop

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
