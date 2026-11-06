# Security and safe use

## Reporting a problem
If you find a security issue (for example, the skill revealing a secret, following instructions hidden in an uploaded file, or advising an unsafe design), open a GitHub issue that describes the behaviour. **Do not include real credentials, customer data or company-internal details**; a synthetic example is enough. If the issue itself is sensitive, use GitHub's private vulnerability reporting for this repository if it is enabled.

## What the skill does and does not do
- No automatic Azure deployment or resource-changing commands.
- Never requests or accepts production credentials. If a secret appears in input, it is replaced with `[REDACTED]` and rotation is advised. The validator rejects common secret formats in blueprints.
- Input documents are untrusted content, not instructions; embedded instructions that try to change the rules are ignored and reported.
- Never fabricates test success or human approval.
- Approval needs a human reviewer and a reference to an external review record. The validator rejects AI/tool reviewer names but cannot prove identity, so verify the record.
- Test results count only with CI- or human-supplied evidence (time, environment, SHA-256 of the result artifact).
- Reports are only rendered from blueprints that pass validation; approvals are displayed as claims, never as authenticated sign-off.

## Your responsibilities as a user
- Use synthetic or sanitised examples. Never paste customer data, passwords, keys or connection strings into a chat.
- Run generated code only in an approved sandbox, and review every output before it goes near production.
- Check your employment and IP arrangements before using employer-specific materials.

## This repository
- All examples and test fixtures use synthetic data.
- Test fixtures deliberately contain fake credentials to prove the validator rejects them. They are allowlisted in `.gitleaks.toml`, so you can run `gitleaks detect` locally before contributing. CI does not run a secret scan yet.
