# Kodiak Blink Status

Kodiak does not currently have a project-local `blink.toml`.

## Current State

- Build and test: local Python and Poetry workflows
- Runtime surfaces: CLI, stdio MCP, REST API, streamable HTTP MCP
- Deployment status: not currently managed by a project-local Blink manifest

## What This Means

- There is no project-local Blink build, deploy, rollback, or verification pipeline today.
- If Kodiak becomes a Blink-managed deployed service later, add a project-local `blink.toml` and update this file to describe the real workflow.
