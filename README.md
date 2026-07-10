# genpark-live-chat-triage-skill

> **GenPark AI Agent Skill** -- Triage customer chat messages by intent, urgency, and sentiment. Route to the right team and suggest instant responses.

## Features

- 9 intent categories: order status, return/refund, billing, product question, complaint, compliment, account, discount, general
- 4 urgency levels: critical / high / medium / low
- Sentiment detection: negative / neutral / positive
- Team routing with fallback to available teams
- Escalation logic: VIP, repeat contacts, critical urgency
- Pre-built response templates per intent
- Batch triage with urgency-sorted output

## Quick Start

```python
from client import LiveChatTriageClient

client = LiveChatTriageClient()
result = client.triage(
    message="My order never arrived and I want a refund!",
    customer_context={"past_tickets": 2},
)
print(f"Intent: {result['intent']} | Urgency: {result['urgency']} | Escalate: {result['escalate']}")
print(result["suggested_response"])
```

## Installation

```bash
python example_usage.py  # No external dependencies
```

---
Built by [GenPark](https://genpark.ai) | [alphaparkinc](https://github.com/alphaparkinc)
