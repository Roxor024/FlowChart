"""Executable model of the Service Bus behaviour behind FlowPilot's retry guidance.

This is a MODEL, not a test against Azure. It encodes documented Service Bus semantics:
  * duplicate detection drops a send whose MessageId was seen within the window, while reporting success;
  * scheduled messages take part in duplicate detection;
  * abandon (or lock expiry after a crash) makes the message available again and increments its delivery count;
  * a message whose delivery count exceeds maxDeliveryCount (default 10) is dead-lettered.
It then checks that the strategies in references/azure-patterns.md lose no orders, and that the
strategies the guidance warns against do lose orders, so the guidance cannot silently regress.
"""
import unittest

OUTAGE_END = 45 * 60          # ERP unavailable for the first 45 minutes
DUP_WINDOW = 10 * 60          # default duplicate-detection window
MAX_DELIVERY = 10             # default maxDeliveryCount
STEP = 5                      # simulation step in seconds
HORIZON = 3 * 60 * 60
ORDERS = [f"ORD-{i:03}" for i in range(20)]


class Crash(Exception):
    """Worker process dies; the message lock later expires."""


class Broker:
    def __init__(self, duplicate_detection=True):
        self.dup = duplicate_detection
        self.seen = {}            # MessageId -> time first accepted
        self.queue = []           # dicts: id, order, visible_at, deliveries
        self.dlq = []
        self.dropped = []         # sends silently discarded by duplicate detection

    def send(self, now, message_id, order, delay=0):
        if self.dup and message_id in self.seen and now - self.seen[message_id] < DUP_WINDOW:
            self.dropped.append(message_id)          # caller still sees success
            return
        self.seen[message_id] = now
        self.queue.append({"id": message_id, "order": order, "visible_at": now + delay, "deliveries": 0})

    def receive(self, now):
        ready = [m for m in self.queue if m["visible_at"] <= now]
        for m in ready:
            self.queue.remove(m)
            m["deliveries"] += 1
            yield m

    def complete(self, message):
        message["completed"] = True                   # settled: the broker will never redeliver it

    def abandon(self, now, message, reason="abandoned"):
        if message["deliveries"] >= MAX_DELIVERY:
            self.dlq.append((message, reason))
        else:
            message["visible_at"] = now
            self.queue.append(message)

    def lock_expired(self, now, message):
        if not message.get("completed"):              # a completed message is gone for good
            self.abandon(now, message, "lock expired")


class Erp:
    def __init__(self):
        self.orders = {}

    def create(self, now, order):
        if now < OUTAGE_END:
            raise ConnectionError("ERP unavailable")
        self.orders[order] = self.orders.get(order, 0) + 1   # counts *business* records

    def create_idempotent(self, now, order):
        if now < OUTAGE_END:
            raise ConnectionError("ERP unavailable")
        self.orders.setdefault(order, 1)                    # external reference = order ID


def backoff(attempt):
    return min(30 * 2 ** attempt, 600) + (attempt * 7) % 11


def simulate(strategy, duplicate_detection=True, crash_points=(), sweeper=False, delete=()):
    broker, erp = Broker(duplicate_detection), Erp()
    state = {o: "accepted" for o in ORDERS}       # the order database (source of truth)
    accepted_at = {o: 0 for o in ORDERS}
    crashes = set(crash_points)
    for order in ORDERS:
        broker.send(0, order, order)              # first publish from the outbox: MessageId = order ID
    for order in delete:                           # simulate a message lost by an operator or a bug
        broker.queue = [m for m in broker.queue if m["order"] != order]
    sweep_run = 0
    for now in range(0, HORIZON, STEP):
        for msg in list(broker.receive(now)):
            order, attempt = msg["order"], msg.get("attempt", 0)
            try:
                if state[order] == "confirmed":
                    broker.complete(msg)
                    continue
                erp.create_idempotent(now, order)
                state[order] = "confirmed"
                broker.complete(msg)
            except ConnectionError:
                try:
                    strategy(broker, now, msg, order, attempt, crashes)
                except Crash:
                    broker.lock_expired(now + 60, msg)      # lock expires after the crash
        if sweeper and now % 300 == 0 and now > 0:
            sweep_run += 1
            for order, st in state.items():
                in_flight = any(m["order"] == order for m in broker.queue)
                if st != "confirmed" and not in_flight and now - accepted_at[order] > OUTAGE_END + 600:
                    broker.send(now, f"{order}:sweep:{sweep_run}", order)
    lost = [o for o in ORDERS if state[o] != "confirmed"
            and not any(m["order"] == o for m in broker.queue)
            and not any(m["order"] == o for m, _ in broker.dlq)]
    return {"confirmed": sum(1 for s in state.values() if s == "confirmed"), "dlq": len(broker.dlq),
            "lost": lost, "dropped": broker.dropped, "erp": erp.orders}


# ---------------- strategies
def abandon_every_failure(broker, now, msg, order, attempt, crashes):
    broker.abandon(now, msg)


def complete_then_reschedule_same_id(broker, now, msg, order, attempt, crashes):
    """The flawed v0.4 guidance: complete, then schedule a re-send with MessageId = order ID."""
    broker.complete(msg)
    if ("between", order) in crashes:
        crashes.discard(("between", order)); raise Crash()
    broker.send(now, order, order, delay=backoff(attempt))
    broker.queue[-1:] and broker.queue[-1].__setitem__("attempt", attempt + 1)


def schedule_new_id_then_complete(broker, now, msg, order, attempt, crashes):
    """v0.4.1 guidance: schedule a NEW message first, then complete the original."""
    retry_id = f"{order}:retry:{attempt + 1}"
    before = len(broker.queue)
    broker.send(now, retry_id, order, delay=backoff(attempt))
    if len(broker.queue) > before:
        broker.queue[-1]["attempt"] = attempt + 1
    if ("between", order) in crashes:
        crashes.discard(("between", order)); raise Crash()   # retry scheduled, original not completed
    broker.complete(msg)


def complete_then_schedule_new_id(broker, now, msg, order, attempt, crashes):
    """Right identity, wrong order: completing first loses the order on a crash."""
    broker.complete(msg)
    if ("between", order) in crashes:
        crashes.discard(("between", order)); raise Crash()
    broker.send(now, f"{order}:retry:{attempt + 1}", order, delay=backoff(attempt))
    broker.queue[-1]["attempt"] = attempt + 1


class GuidanceIsSafe(unittest.TestCase):
    def assertNoLoss(self, result):
        self.assertEqual(result["lost"], [], f"orders lost: {result['lost']}")
        self.assertEqual(result["dlq"], 0, "healthy orders were dead-lettered")
        self.assertEqual(result["confirmed"], len(ORDERS))
        self.assertTrue(all(count == 1 for count in result["erp"].values()), "duplicate ERP business records")

    def test_recommended_retry_survives_45_minute_outage(self):
        self.assertNoLoss(simulate(schedule_new_id_then_complete))

    def test_recommended_retry_with_duplicate_detection_disabled(self):
        self.assertNoLoss(simulate(schedule_new_id_then_complete, duplicate_detection=False))

    def test_crash_between_schedule_and_complete(self):
        crashes = [("between", o) for o in ORDERS[:5]]
        self.assertNoLoss(simulate(schedule_new_id_then_complete, crash_points=crashes))

    def test_sweeper_recovers_a_lost_message(self):
        result = simulate(schedule_new_id_then_complete, sweeper=True, delete=["ORD-007"])
        self.assertNoLoss(result)

    def test_without_sweeper_a_lost_message_stays_lost(self):
        """Shows why the sweeper backstop is mandatory."""
        result = simulate(schedule_new_id_then_complete, sweeper=False, delete=["ORD-007"])
        self.assertEqual(result["lost"], ["ORD-007"])


class AntiPatternsAreUnsafe(unittest.TestCase):
    """If these ever stop failing, the model no longer reflects the documented behaviour."""

    def test_abandon_dead_letters_healthy_orders(self):
        self.assertEqual(simulate(abandon_every_failure)["dlq"], len(ORDERS))

    def test_reusing_message_id_silently_drops_retries(self):
        result = simulate(complete_then_reschedule_same_id)
        self.assertTrue(result["dropped"], "duplicate detection should have dropped the reused MessageId")
        self.assertEqual(sorted(result["lost"]), ORDERS)

    def test_complete_before_schedule_loses_order_on_crash(self):
        result = simulate(complete_then_schedule_new_id, crash_points=[("between", "ORD-003")])
        self.assertIn("ORD-003", result["lost"])


if __name__ == "__main__":
    unittest.main()
