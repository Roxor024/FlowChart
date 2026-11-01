# FlowPilot v0.3 requirements and design workflow

- Extract known, assumed, unknown and conflicting requirements. Give requirements IDs, types and measurable criteria where confirmed.
- Ask a maximum of five clarification questions per visible response. Store remaining unknowns in `openQuestions`.
- When inputs conflict, stop short of definitive design, record a `CON-###` conflict and offer clear resolution paths. Preserve resolved conflicts with a resolution explanation.
- If design cannot be justified, use `provisional` and empty component/test lists rather than inventing services.
- Compare APIM, Functions, Logic Apps, Service Bus and Event Grid only where appropriate to actual requirements.
- For order intake: establish durable acceptance and idempotency with race-safe state handling; use a transactional outbox when coordinating DB state with messaging. Worker must never overwrite newer state.
- Separate generated artifacts, validation checks and human approval. Never self-approve or fabricate test passes.
- Keep README, schema, examples, report and skill versions synchronized; schema migrations require explicit version change.
