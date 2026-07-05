"""
example_usage.py -- Demonstrates the LiveChatTriageClient SDK.
"""
from client import LiveChatTriageClient

def main():
    client = LiveChatTriageClient()

    messages = [
        {"id":"M1","message":"I am absolutely furious! My order never arrived and no one is responding. This is unacceptable!","context":{"past_tickets":2}},
        {"id":"M2","message":"Hi! Could you tell me how to use the vitamin C serum? Do I apply it morning or night?","context":{}},
        {"id":"M3","message":"I was double charged on my credit card last week. Please help!","context":{"is_vip":True}},
        {"id":"M4","message":"I love your products! Thank you so much for the fast delivery.","context":{}},
        {"id":"M5","message":"I need to return an item that arrived damaged. What is the process?","context":{"order_id":"ORD-1234"}},
    ]

    print("[Live Chat Triage -- Batch Processing]")
    results = client.batch_triage(messages)

    for r in results:
        escalate_str = "ESCALATE" if r["escalate"] else "auto"
        print(f"\n[{r['urgency'].upper()}] {r['message_id']} -> {r['routed_to'].upper()} [{escalate_str}]")
        print(f"  Intent: {r['intent']} | Sentiment: {r['sentiment']}")
        if r.get("escalate_reason"):
            print(f"  Escalation Reason: {r['escalate_reason']}")
        print(f"  Response: {r['suggested_response'][:80]}...")

if __name__ == "__main__":
    main()
