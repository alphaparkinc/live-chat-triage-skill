"""
live-chat-triage-skill: Client SDK
Triage customer chat messages by intent, urgency, and sentiment. Route to correct team.
"""
from __future__ import annotations
from typing import Optional
import re

INTENT_PATTERNS = {
    "order_status":     ["where is my order", "track", "tracking", "shipped", "delivery", "when will", "order status", "not received", "never arrived"],
    "return_refund":    ["return", "refund", "exchange", "send back", "money back", "cancel order", "wrong item", "damaged", "broken"],
    "billing_payment":  ["charge", "charged", "payment", "invoice", "receipt", "credit card", "billing", "overcharged", "double charged"],
    "product_question": ["how to use", "ingredients", "size", "fit", "available", "in stock", "compatible", "instructions", "manual"],
    "complaint":        ["unacceptable", "terrible", "horrible", "worst", "disgusting", "angry", "furious", "lawsuit", "report", "fraud"],
    "compliment":       ["love", "amazing", "excellent", "great", "fantastic", "recommend", "best", "thank you", "perfect"],
    "account":          ["login", "password", "account", "profile", "subscription", "cancel subscription", "email address"],
    "discount_promo":   ["discount", "coupon", "promo code", "sale", "deal", "offer", "free shipping"],
    "general":          [],
}

URGENCY_RULES = {
    "critical": ["fraud", "lawsuit", "stolen", "chargeback", "unauthorized", "hacked", "illegal", "scam"],
    "high":     ["angry", "furious", "terrible", "horrible", "unacceptable", "broken", "damaged", "never arrived", "refund", "cancel"],
    "medium":   ["where is", "tracking", "return", "exchange", "wrong", "billing", "charged"],
    "low":      ["question", "how to", "size", "available", "love", "thank"],
}

NEGATIVE_WORDS = ["angry", "furious", "terrible", "horrible", "worst", "disgusting", "disappointed", "broken", "damaged", "wrong", "missing", "fraud", "scam", "unacceptable", "awful", "useless"]
POSITIVE_WORDS = ["love", "great", "amazing", "excellent", "fantastic", "perfect", "recommend", "happy", "wonderful", "best", "thank"]

ROUTING_MAP = {
    "order_status":     "shipping",
    "return_refund":    "returns",
    "billing_payment":  "billing",
    "product_question": "general",
    "complaint":        "general",
    "compliment":       "general",
    "account":          "billing",
    "discount_promo":   "general",
    "general":          "general",
}

RESPONSE_TEMPLATES = {
    "order_status":     "Hi! I understand you are checking on your order. I am pulling up your order details right now. Could you confirm your order number so I can provide the latest tracking update?",
    "return_refund":    "I am sorry to hear that! I will make this right for you. Our returns process is simple -- let me guide you through it step by step. Can you share your order number?",
    "billing_payment":  "I understand your concern about the billing. Let me review your account immediately. Could you confirm the email address associated with your account?",
    "product_question": "Great question! I am happy to help with product information. Let me get the details for you right away.",
    "complaint":        "I sincerely apologize for the experience you have had. This is not the standard we hold ourselves to, and I want to make this right immediately. May I have your order number?",
    "compliment":       "Thank you so much for your kind words! We truly appreciate your support. Is there anything else I can help you with today?",
    "account":          "I can help you with your account. For security, I will need to verify a few details. Could you confirm the email address on your account?",
    "discount_promo":   "I would be happy to help you with our current offers! Let me check what promotions are available for you right now.",
    "general":          "Thank you for reaching out! I am here to help. Could you please provide a bit more detail so I can assist you as quickly as possible?",
}


class LiveChatTriageClient:
    """
    SDK for triaging live customer chat messages.
    Detects intent, urgency, sentiment, and recommends routing and response.
    """

    def triage(
        self,
        message: str,
        customer_context: Optional[dict] = None,
        available_teams: Optional[list[str]] = None,
    ) -> dict:
        """
        Triage a customer chat message.

        Args:
            message:          Raw customer message text.
            customer_context: Optional: {order_id, past_tickets, is_vip}.
            available_teams:  List of team names available for routing.

        Returns:
            dict with intent, urgency, sentiment, routed_to, suggested_response, escalate
        """
        ctx = customer_context or {}
        available = [t.lower() for t in (available_teams or ["billing", "shipping", "returns", "general"])]
        msg_lower = message.lower()

        # Intent detection
        intent = self._detect_intent(msg_lower)

        # Urgency
        urgency = self._detect_urgency(msg_lower, ctx)

        # Sentiment
        sentiment = self._detect_sentiment(msg_lower)

        # Routing
        preferred_team = ROUTING_MAP.get(intent, "general")
        routed_to = preferred_team if preferred_team in available else (available[0] if available else "general")

        # Escalation logic
        is_vip = bool(ctx.get("is_vip"))
        past_tickets = int(ctx.get("past_tickets", 0))
        escalate = (
            urgency == "critical" or
            (urgency == "high" and sentiment == "negative") or
            is_vip or
            past_tickets >= 3
        )

        # Response
        response = RESPONSE_TEMPLATES.get(intent, RESPONSE_TEMPLATES["general"])

        return {
            "intent": intent,
            "urgency": urgency,
            "sentiment": sentiment,
            "routed_to": routed_to,
            "suggested_response": response,
            "escalate": escalate,
            "escalate_reason": self._escalate_reason(urgency, sentiment, is_vip, past_tickets) if escalate else None,
            "message_length": len(message),
        }

    def batch_triage(self, messages: list[dict]) -> list[dict]:
        """Triage multiple messages at once."""
        results = []
        for m in messages:
            result = self.triage(
                message=m.get("message", ""),
                customer_context=m.get("context", {}),
                available_teams=m.get("teams"),
            )
            result["message_id"] = m.get("id", "")
            results.append(result)
        # Sort by urgency
        urgency_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        results.sort(key=lambda x: urgency_order.get(x["urgency"], 4))
        return results

    @staticmethod
    def _detect_intent(text: str) -> str:
        scores = {}
        for intent, patterns in INTENT_PATTERNS.items():
            scores[intent] = sum(1 for p in patterns if p in text)
        best = max(scores, key=lambda k: scores[k])
        return best if scores[best] > 0 else "general"

    @staticmethod
    def _detect_urgency(text: str, ctx: dict) -> str:
        for level, keywords in URGENCY_RULES.items():
            if any(kw in text for kw in keywords):
                return level
        if ctx.get("past_tickets", 0) >= 3:
            return "high"
        return "medium"

    @staticmethod
    def _detect_sentiment(text: str) -> str:
        neg = sum(1 for w in NEGATIVE_WORDS if w in text)
        pos = sum(1 for w in POSITIVE_WORDS if w in text)
        if neg > pos: return "negative"
        if pos > neg: return "positive"
        return "neutral"

    @staticmethod
    def _escalate_reason(urgency, sentiment, is_vip, tickets) -> str:
        if urgency == "critical": return "Critical urgency detected in message"
        if is_vip: return "VIP customer -- requires immediate human attention"
        if tickets >= 3: return "Repeat contact -- 3+ previous tickets"
        return "High urgency with negative sentiment"
