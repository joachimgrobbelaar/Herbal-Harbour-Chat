import json
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from config.settings import settings

class KnowledgeRetriever:
    def __init__(self, products_path: Optional[Path] = None, faq_path: Optional[Path] = None):
        self.products_path = products_path or settings.PRODUCTS_FILE
        self.faq_path = faq_path or settings.FAQ_FILE
        self.products: List[Dict[str, Any]] = []
        self.business_info: Dict[str, Any] = {}
        self.faqs: List[Dict[str, Any]] = []
        self.currency: str = "USD"
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

    def _tokenize(self, text: str) -> set[str]:
        return set(re.findall(r"\w+", text.lower()))

    def search_products(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Matches products by relevance score against query terms."""
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return self.products[:top_k]

        scored_products = []
        for p in self.products:
            score = 0
            # Search fields
            name_tokens = self._tokenize(p.get("name", ""))
            category_tokens = self._tokenize(p.get("category", ""))
            benefits_text = " ".join(p.get("benefits", []))
            benefits_tokens = self._tokenize(benefits_text)
            desc_tokens = self._tokenize(p.get("description", ""))
            ingredients_tokens = self._tokenize(" ".join(p.get("ingredients", [])))

            # Keyword scoring weights
            score += len(query_tokens.intersection(name_tokens)) * 5
            score += len(query_tokens.intersection(category_tokens)) * 3
            score += len(query_tokens.intersection(benefits_tokens)) * 4
            score += len(query_tokens.intersection(ingredients_tokens)) * 2
            score += len(query_tokens.intersection(desc_tokens)) * 1

            if score > 0:
                scored_products.append((score, p))

        scored_products.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored_products[:top_k]]

    def search_faq(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """Matches business FAQs by relevance score against query terms."""
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return self.faqs[:top_k]

        scored_faqs = []
        for item in self.faqs:
            topic_tokens = self._tokenize(item.get("topic", ""))
            q_tokens = self._tokenize(item.get("question", ""))
            ans_tokens = self._tokenize(item.get("answer", ""))

            score = (
                len(query_tokens.intersection(topic_tokens)) * 3 +
                len(query_tokens.intersection(q_tokens)) * 3 +
                len(query_tokens.intersection(ans_tokens)) * 1
            )
            if score > 0:
                scored_faqs.append((score, item))

        scored_faqs.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored_faqs[:top_k]]

    def get_grounding_context(self, user_query: str) -> str:
        """Constructs a concise markdown context block for LLM prompt injection."""
        matched_products = self.search_products(user_query, top_k=3)
        matched_faqs = self.search_faq(user_query, top_k=2)

        lines = ["[HERBAL HARBOUR STORE PROFILE]"]
        lines.append(f"Name: {self.business_info.get('name', 'Herbal Harbour')}")
        lines.append(f"Tagline: {self.business_info.get('tagline', '')}")
        lines.append(f"Hours: {self.business_info.get('operating_hours', '')}")
        lines.append(f"Website: {self.business_info.get('contact', {}).get('website', '')}")

        lines.append("\n[AVAILABLE CATALOG PRODUCTS]")
        if matched_products:
            for p in matched_products:
                lines.append(f"- **{p['name']}** ({p['category']}, ${p['price']:.2f} {self.currency}, {p['size']})")
                lines.append(f"  Description: {p['description']}")
                lines.append(f"  Benefits: {', '.join(p['benefits'])}")
                lines.append(f"  Suggested Use: {p['directions']}")
                lines.append(f"  Precautions: {p['cautions']}")
        else:
            # Fallback list of top products
            for p in self.products[:4]:
                lines.append(f"- {p['name']} (${p['price']:.2f} {self.currency}) - {p['category']}")

        if matched_faqs:
            lines.append("\n[BUSINESS FAQ & POLICIES]")
            for f in matched_faqs:
                lines.append(f"- Q: {f['question']}")
                lines.append(f"  A: {f['answer']}")

        return "\n".join(lines)

retriever = KnowledgeRetriever()
