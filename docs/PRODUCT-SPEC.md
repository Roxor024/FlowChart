# FlowPilot v0.2 product specification

Goal: help an Azure integration engineer navigate requirements, architectural tradeoffs, implementation, testing, security review and operations with one coherent, traceable engineering blueprint.

MVP inputs: natural-language requirements and sanitized artifacts.
MVP outputs: requirements and assumptions, architecture diagram, ADRs, build checklist, test matrix, risks, runbook, JSON blueprint, readable HTML report.
Requirements: explicit unknowns/conflicts, safe defaults, stable IDs, validation and review-state evidence.
Non-goals: production deployment, automatic credentials use, cloud inventory, real-time monitoring, production signoff.
Pilot gate: test across order processing, synchronous lookup, event fan-out, file/SFTP, vague requests, conflicting requirements, and sensitive data.