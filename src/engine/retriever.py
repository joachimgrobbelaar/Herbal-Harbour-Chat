import json
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from config.settings import settings

SYMPTOM_MAP: Dict[str, List[str]] = {
    "sleep": ["chamomile", "lavender", "sleep", "insomnia", "restless", "night"],
    "insomnia": ["chamomile", "lavender", "sleep", "restful", "night"],
    "anxiety": ["ashwagandha", "chamomile", "lavender", "stress", "calm", "relax"],
    "stress": ["ashwagandha", "chamomile", "calm", "tension", "cortisol"],
    "energy": ["citrus", "green tea", "morning", "fatigue", "tired"],
    "fatigue": ["citrus", "green tea", "ashwagandha", "energy"],
    "focus": ["lion's mane", "clarity", "memory", "brain", "concentration"],
    "brain fog": ["lion's mane", "clarity", "focus", "memory"],
    "pain": ["arnica", "turmeric", "recovery", "muscle", "joint", "inflammation"],
    "inflammation": ["turmeric", "ginger", "arnica", "joint"],
    "cold": ["elderberry", "immune", "cough", "flu", "throat", "sick"],
    "flu": ["elderberry", "immune", "syrup", "honey", "throat"],
    "cough": ["elderberry", "syrup", "honey", "throat"],
    "skin": ["calendula", "salve", "eczema", "dry", "rash", "burns"],
    "eczema": ["calendula", "salve", "dry", "skin", "nourish"],
    "digestion": ["ginger", "turmeric", "stomach", "bloating"],
    "cannabis": ["cannabis", "sleep", "tension", "ease", "restful"],
    "microdose": ["lion's mane", "clarity", "mood", "fadiman", "stamets"],
    "microdosing": ["lion's mane", "clarity", "mood", "fadiman", "stamets"],
    "mushroom": ["lion's mane", "reishi", "cordyceps", "focus"],
    "spin": ["spin", "wheel", "perk", "charity", "waiver"],
    "delivery": ["delivery", "dispatch", "courier", "drop"],
    "weedliver": ["delivery", "dispatch", "courier", "drop"],
    "weeddeliver": ["delivery", "dispatch", "courier", "drop"],
}

ECOSYSTEM_CONTEXT = (
    "[AGY ECOSYSTEM ROLES]\n"
    "- Herbal Harbour: botanical apothecary (medicinal cannabis guidance, Lion's Mane, microdosing packages).\n"
    "- Canna-Spin-and-Win: interactive web hub; members spin the wheel to unlock donation perks, bonus herbal samples, delivery fee waivers, and charity multipliers.\n"
    "- WeeDeliver: private discreet courier; unbranded smell-proof packaging; never disclose driver routes or drop schedules in chat.\n"
    "- Squigl: digital design studio operating the platform infrastructure.\n"
    "House rules: cooperative donation model. Never say buy/sell/price/charge/cart/checkout/store/purchase. "
    "Say donate, contribution tier, gift, mutual aid, care package, allocation. "
    "A designated percentage of every contribution funds partner charities. Cannabis guidance follows 'start low, go slow'. "
    "Microdosing rhythms: Fadiman (1 day on, 2 days off) or Stamets stack with Lion's Mane."
)


class KnowledgeRetriever:
    def __init__(self, products_path: Optional[Path] = None, faq_path: Optional[Path] = None, custom_training_path: Optional[Path] = None):
        self.products_path = products_path or settings.PRODUCTS_FILE
        self.faq_path = faq_path or settings.FAQ_FILE
        self.custom_training_path = custom_training_path or (settings.PRODUCTS_FILE.parent / "custom_training.json")
        self.products: List[Dict[str, Any]] = []
        self.business_info: Dict[str, Any] = {}
        self.faqs: List[Dict[str, Any]] = []
        self.custom_rules: List[str] = []
        self.custom_faqs: List[Dict[str, str]] = []
        self.currency: str = "USD"
        self._load_data()

    def reload(self) -> None:
        """Reloads all catalogs, business policies, and custom training data."""
        self._load_data()

    def _load_data(self) -> None:
        if self.products_path.exists():
            with open(self.products_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.products = data.get("products", [])
                self.currency = data.get("currency", "USD")

        if self.faq_path.exists():
            with open(self.faq_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.business_info = data.get("business", {})
                self.faqs = data.get("faq", [])

        if self.custom_training_path.exists():
            try:
                with open(self.custom_training_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.custom_rules = data.get("custom_rules", [])
                    self.custom_faqs = data.get("custom_faqs", [])
            except Exception:
                pass

    def _tokenize(self, text: str) -> set[str]:
        return set(re.findall(r"\w+", text.lower()))

    def _expand_tokens(self, query: str) -> set[str]:
        tokens = self._tokenize(query)
        q_lower = query.lower()
        expanded = set(tokens)
        for symptom, related in SYMPTOM_MAP.items():
            if symptom in q_lower or any(t == symptom for t in tokens):
                expanded.update(related)
        return expanded

    def search_products(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Matches products by relevance score against query terms with symptom expansion."""
        query_tokens = self._expand_tokens(query)
        if not query_tokens:
            return self.products[:top_k]

        scored_products = []
        for p in self.products:
            score = 0
            name_tokens = self._tokenize(p.get("name", ""))
            category_tokens = self._tokenize(p.get("category", ""))
            benefits_text = " ".join(p.get("benefits", []))
            benefits_tokens = self._tokenize(benefits_text)
            desc_tokens = self._tokenize(p.get("description", ""))
            ingredients_tokens = self._tokenize(" ".join(p.get("ingredients", [])))

            score += len(query_tokens.intersection(name_tokens)) * 5
            score += len(query_tokens.intersection(category_tokens)) * 3
            score += len(query_tokens.intersection(benefits_tokens)) * 4
            score += len(query_tokens.intersection(ingredients_tokens)) * 2
            score += len(query_tokens.intersection(desc_tokens)) * 1

            if score > 0:
                scored_products.append((score, p))

        scored_products.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored_products[:top_k]]

    def search_faq(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Matches standard and custom FAQs by relevance score against query terms."""
        query_tokens = self._expand_tokens(query)
        all_faqs = list(self.faqs)
        for cf in self.custom_faqs:
            all_faqs.append({
                "topic": "custom",
                "question": cf.get("question", ""),
                "answer": cf.get("answer", "")
            })

        if not query_tokens:
            return all_faqs[:top_k]

        scored_faqs = []
        for item in all_faqs:
            topic_tokens = self._tokenize(item.get("topic", ""))
            q_tokens = self._tokenize(item.get("question", ""))
            ans_tokens = self._tokenize(item.get("answer", ""))

            score = (
                len(query_tokens.intersection(topic_tokens)) * 3 +
                len(query_tokens.intersection(q_tokens)) * 4 +
                len(query_tokens.intersection(ans_tokens)) * 1
            )
            if score > 0:
                scored_faqs.append((score, item))

        scored_faqs.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored_faqs[:top_k]]

    def get_grounding_context(self, user_query: str) -> str:
        """Constructs a concise markdown context block for LLM prompt injection."""
        matched_products = self.search_products(user_query, top_k=3)
        matched_faqs = self.search_faq(user_query, top_k=3)

        lines = ["[HERBAL HARBOUR STORE PROFILE]"]
        lines.append(ECOSYSTEM_CONTEXT)
        lines.append(f"Name: {self.business_info.get('name', 'Herbal Harbour')}")
        lines.append(f"Tagline: {self.business_info.get('tagline', '')}")
        lines.append(f"Hours: {self.business_info.get('operating_hours', '')}")
        lines.append(f"Website: {self.business_info.get('contact', {}).get('website', '')}")

        if self.custom_rules:
            lines.append("\n[CUSTOM BUSINESS POLICIES & SPECIAL INSTRUCTIONS]")
            for rule in self.custom_rules:
                lines.append(f"- {rule}")

        lines.append("\n[AVAILABLE CATALOG PRODUCTS]")
        if matched_products:
            for p in matched_products:
                lines.append(f"- **{p['name']}** ({p['category']}, suggested contribution {p['price']:.2f} {self.currency}, {p['size']})")
                lines.append(f"  Description: {p['description']}")
                lines.append(f"  Benefits: {', '.join(p['benefits'])}")
                lines.append(f"  Suggested Use: {p['directions']}")
                lines.append(f"  Precautions: {p['cautions']}")
        else:
            for p in self.products[:4]:
                lines.append(f"- {p['name']} (${p['price']:.2f} {self.currency}) - {p['category']}")

        if matched_faqs:
            lines.append("\n[BUSINESS FAQ & POLICIES]")
            for f in matched_faqs:
                lines.append(f"- Q: {f['question']}")
                lines.append(f"  A: {f['answer']}")

        return "\n".join(lines)

retriever = KnowledgeRetriever()
