"""SYNTHETIC sample for FlowPilot tests: accept an order only once (idempotent insert)."""


def accept(store: dict, order_id: str, payload: dict) -> tuple[int, str]:
    if not order_id:
        return 400, "missing order id"
    if order_id in store:
        return 202, order_id  # duplicate: same answer, no second effect
    store[order_id] = payload
    return 202, order_id
