# Security Policy

Kodiak handles brokerage credentials, trading automation, and financial data.

## Reporting

Report vulnerabilities privately with:

- affected CLI, REST, or MCP surface
- whether paper or live trading is involved
- reproduction steps
- expected versus actual risk controls

## Baseline Expectations

- Paper-first defaults stay intact.
- Secrets remain out of source control and logs.
- Redaction and privacy controls must be documented and tested.
- Trading write paths require stronger review than read-only reporting paths.
