#!/bin/bash
# Wrapper script to run MCP server with logging

LOG_FILE="/tmp/sipud_mcp_server.log"

echo "=== SIPUD MCP Server Started at $(date) ===" >> "$LOG_FILE" 2>&1

# Run the Python server and capture all output
python3 /Users/bchavez/Proyectos/SIPUD/mcp_server/server.py 2>> "$LOG_FILE"

# Log exit code
echo "=== Server exited with code $? at $(date) ===" >> "$LOG_FILE" 2>&1
