from typing import Dict, List, Tuple, Optional, Any
import math
import re


WORD_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?", re.IGNORECASE)
# Match a phrase only on token boundaries so "gas" does not hit "vegas"
# and "cat" does not hit "category".
def _phrase_pattern(phrase: str) -> re.Pattern:
    escaped = re.escape(phrase.lower().strip())
    escaped = re.sub(r"\\ ", r"\\s+", escaped)
    return re.compile(rf"(?<![\w]){escaped}(?![\w])", re.IGNORECASE)


class TransactionCategorizer:
    """
    Score categories with additive log-weights, then convert to probabilities
    with a numerically stable softmax:

        P(c | text) = exp(s_c - max s) / sum_j exp(s_j - max s)

    Longer, rarer phrases get higher weight so specific merchants beat
    generic words. Confidence is the top probability, reduced when the
    runner-up is close (low decision margin).
    """

    TEMPERATURE = 1.15
    MIN_SCORE = 0.35

    def __init__(self):
        self.nlp = None
        try:
            import spacy
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                self.nlp = None
        except ImportError:
            self.nlp = None

        # phrases: high-signal terms. Avoid generic words like "payment",
        # "monthly", "premium", "store" that collide across categories.
        self.category_keywords = {
            "Income": {
                "phrases": [
                    "direct deposit", "paycheck", "payroll", "salary", "wages",
                    "bonus", "commission", "freelance income", "interest income",
                    "tax refund", "reimbursement", "pension", "social security",
                    "unemployment", "allowance",
                ],
                "transaction_types": ["income"],
                "prior": 0.4,
            },
            "Investment Income": {
                "phrases": [
                    "capital gains", "stock dividend", "dividend",
                    "investment return", "bond interest",
                ],
                "transaction_types": ["income"],
                "prior": 0.2,
            },
            "Housing": {
                "phrases": [
                    "property management", "homeowners association", "security deposit",
                    "condo fee", "hoa", "mortgage", "landlord", "apartment",
                    "lease", "rent",
                ],
                "transaction_types": ["expense"],
                "prior": 0.3,
            },
            "Bills & Utilities": {
                "phrases": [
                    "hydro quebec", "hydro one", "hydro bill", "hydroelectric",
                    "natural gas", "gas bill", "electric bill", "utility bill",
                    "air conditioning", "electricity", "electric", "internet",
                    "wifi", "sewer", "water bill", "utilities", "utility",
                    "cable", "telephone", "cell phone", "mobile phone",
                    "heating", "cooling", "recycling", "garbage", "trash",
                    "hydro", "power bill",
                ],
                "transaction_types": ["expense"],
                "prior": 0.35,
            },
            "Food & Dining": {
                "phrases": [
                    "uber eats", "door dash", "doordash", "grubhub", "postmates",
                    "mcdonalds", "mcdonald", "starbucks", "fast food", "food truck",
                    "restaurant", "takeout", "take-out", "delivery", "breakfast",
                    "brunch", "dinner", "lunch", "pizza", "burger", "coffee",
                    "bistro", "brewery", "diner", "cafe", "pub",
                ],
                "transaction_types": ["expense"],
                "prior": 0.25,
            },
            "Groceries": {
                "phrases": [
                    "whole foods", "trader joe", "trader joes", "grocery store",
                    "food market", "supermarket", "harris teeter", "stop & shop",
                    "food lion", "shoprite", "wegmans", "safeway", "publix",
                    "kroger", "aldi", "heb", "costco", "sam's club", "sams club",
                    "grocery",
                ],
                "transaction_types": ["expense"],
                "prior": 0.25,
            },
            "Transportation": {
                "phrases": [
                    "gas station", "car rental", "rental car", "oil change",
                    "auto repair", "car repair", "public transport", "ride share",
                    "rideshare", "ez pass", "toll road", "parking", "gasoline",
                    "petrol", "subway", "metro", "lyft", "uber", "taxi", "cab",
                    "transit", "dmv", "toll", "fuel", "bus", "train",
                ],
                "transaction_types": ["expense"],
                "prior": 0.25,
            },
            "Shopping": {
                "phrases": [
                    "bed bath & beyond", "department store", "home depot",
                    "best buy", "nordstrom", "home goods", "electronics",
                    "appliance", "furniture", "clothing", "apparel", "amazon",
                    "ikea", "lowes", "macy's", "macys", "mall",
                ],
                "transaction_types": ["expense"],
                "prior": 0.15,
            },
            "Entertainment": {
                "phrases": [
                    "theme park", "video game", "sports event", "mini golf",
                    "amusement", "concert", "cinema", "theater", "theatre",
                    "festival", "bowling", "arcade", "movie", "ticket",
                ],
                "transaction_types": ["expense"],
                "prior": 0.15,
            },
            "Subscriptions": {
                "phrases": [
                    "amazon prime", "youtube premium", "apple music", "disney plus",
                    "disney+", "software subscription", "subscription",
                    "netflix", "spotify", "hulu",
                ],
                "transaction_types": ["expense"],
                "prior": 0.2,
            },
            "Healthcare": {
                "phrases": [
                    "physical therapy", "health insurance", "urgent care",
                    "emergency room", "eye doctor", "optometrist", "prescription",
                    "medication", "hospital", "pharmacy", "dentist", "dental",
                    "clinic", "doctor", "medical", "copay", "co-pay",
                    "x-ray", "mri", "surgery", "medicine", "walgreens", "cvs",
                ],
                "transaction_types": ["expense"],
                "prior": 0.2,
            },
            "Fitness & Wellness": {
                "phrases": [
                    "personal trainer", "fitness class", "gym membership",
                    "pilates", "workout", "yoga", "gym", "spa", "massage",
                    "haircut", "barber", "salon",
                ],
                "transaction_types": ["expense"],
                "prior": 0.15,
            },
            "Personal Care": {
                "phrases": [
                    "personal care", "rite aid", "drugstore", "toiletries",
                    "skincare", "cosmetics", "manicure", "pedicure",
                    "makeup", "beauty", "shampoo",
                ],
                "transaction_types": ["expense"],
                "prior": 0.1,
            },
            "Education": {
                "phrases": [
                    "student loan", "online course", "textbook", "tuition",
                    "university", "college", "school", "course",
                    "certification", "workshop",
                ],
                "transaction_types": ["expense"],
                "prior": 0.15,
            },
            "Insurance": {
                "phrases": [
                    "renters insurance", "home insurance", "auto insurance",
                    "car insurance", "life insurance", "health insurance",
                    "state farm", "progressive", "allstate", "insurance",
                    "geico", "usaa",
                ],
                "transaction_types": ["expense"],
                "prior": 0.2,
            },
            "Banking & Fees": {
                "phrases": [
                    "foreign transaction", "service charge", "maintenance fee",
                    "transaction fee", "atm fee", "bank fee", "overdraft",
                    "late fee", "wire transfer", "annual fee", "finance charge",
                ],
                "transaction_types": ["expense"],
                "prior": 0.15,
            },
            "Investments": {
                "phrases": [
                    "charles schwab", "mutual fund", "roth ira", "robinhood",
                    "brokerage", "vanguard", "fidelity", "401k", "ira",
                    "retirement", "etf",
                ],
                "transaction_types": ["expense", "income"],
                "prior": 0.15,
            },
            "Debt & Loans": {
                "phrases": [
                    "credit card payment", "student loan payment", "minimum payment",
                    "personal loan", "payday loan", "auto loan", "car loan",
                    "credit card", "loan payment",
                ],
                "transaction_types": ["expense"],
                "prior": 0.2,
            },
            "Travel": {
                "phrases": [
                    "booking.com", "travel agency", "rental car", "car rental",
                    "airbnb", "expedia", "priceline", "airport", "airline",
                    "flight", "hotel", "vacation", "cruise", "resort",
                    "kayak", "booking",
                ],
                "transaction_types": ["expense"],
                "prior": 0.2,
            },
            "Gifts & Donations": {
                "phrases": [
                    "go fund me", "gofundme", "kickstarter", "donation",
                    "charity", "charitable", "nonprofit", "fundraiser",
                    "patreon", "gratuity",
                ],
                "transaction_types": ["expense"],
                "prior": 0.1,
            },
            "Business Expenses": {
                "phrases": [
                    "business trip", "office supplies", "advertising",
                    "marketing", "consulting", "attorney", "accountant",
                    "conference", "lawyer", "office",
                ],
                "transaction_types": ["expense"],
                "prior": 0.1,
            },
            "Kids & Family": {
                "phrases": [
                    "school supplies", "childcare", "babysitter", "daycare",
                    "car seat", "nanny", "diaper", "formula", "stroller",
                    "infant", "baby",
                ],
                "transaction_types": ["expense"],
                "prior": 0.1,
            },
            "Pets": {
                "phrases": [
                    "pet grooming", "pet supplies", "pet store", "pet food",
                    "petsmart", "petco", "veterinary", "vet",
                ],
                "transaction_types": ["expense"],
                "prior": 0.1,
            },
            "Taxes": {
                "phrases": [
                    "property tax", "income tax", "federal tax", "state tax",
                    "tax payment", "tax refund", "irs",
                ],
                "transaction_types": ["expense", "income"],
                "prior": 0.15,
            },
            "Other": {
                "phrases": [],
                "transaction_types": ["expense", "income"],
                "prior": 0.05,
            },
        }

        # Ambiguous single tokens: split mass using context cues.
        self.context_rules = [
            {
                "token": "gas",
                "utility": (["bill", "utility", "natural", "home", "enbridge"], "Bills & Utilities", 2.4),
                "default": ("Transportation", 1.6),
            },
            {
                "token": "target",
                "grocery": (["grocery", "groceries", "market", "food"], "Groceries", 2.0),
                "default": ("Shopping", 1.4),
            },
            {
                "token": "walmart",
                "grocery": (["grocery", "groceries", "market", "food"], "Groceries", 2.0),
                "default": ("Shopping", 1.3),
            },
            {
                "token": "water",
                "utility": (["bill", "utility", "city", "town"], "Bills & Utilities", 2.2),
            },
            {
                "token": "phone",
                "utility": (["bill", "cell", "mobile", "verizon", "att", "t-mobile"], "Bills & Utilities", 2.0),
            },
        ]

        self._compiled = {}
        for category, data in self.category_keywords.items():
            compiled = []
            for phrase in data["phrases"]:
                tokens = self._tokens(phrase)
                compiled.append({
                    "phrase": phrase,
                    "pattern": _phrase_pattern(phrase),
                    "n_tokens": max(1, len(tokens)),
                    "n_chars": len(phrase),
                })
            # Prefer longer phrases when both match; scoring already does this.
            compiled.sort(key=lambda x: (-x["n_tokens"], -x["n_chars"]))
            self._compiled[category] = compiled

        self.lemmatized_keywords: Dict[str, List[str]] = {}
        if self.nlp:
            self._build_lemmatized_cache()

    def _tokens(self, text: str) -> List[str]:
        return WORD_RE.findall(text.lower())

    def _build_lemmatized_cache(self):
        if not self.nlp:
            return
        for category, data in self.category_keywords.items():
            lemmas = []
            for phrase in data["phrases"]:
                doc = self.nlp(phrase)
                lemmas.append(" ".join(token.lemma_ for token in doc))
            self.lemmatized_keywords[category] = lemmas

    def _get_transaction_type_hint(self, amount: float, description: str) -> str:
        text = description.lower()
        income_cues = (
            "salary", "payroll", "paycheck", "direct deposit", "dividend",
            "bonus", "commission", "tax refund", "interest income",
        )
        if any(cue in text for cue in income_cues):
            return "income"
        if amount > 0 and any(cue in text for cue in ("deposit", "refund", "income")):
            return "income"
        return "expense"

    def _phrase_weight(self, n_tokens: int, n_chars: int) -> float:
        """
        Specificity weight: longer phrases are exponentially more informative.
        w = n_tokens^1.55 * (1 + log(1 + n_chars) / 8)
        """
        return (n_tokens ** 1.55) * (1.0 + math.log1p(n_chars) / 8.0)

    def _has_phrase(self, text: str, phrase: str) -> bool:
        return bool(_phrase_pattern(phrase).search(text))

    def _apply_context(self, text: str, tokens: List[str], scores: Dict[str, float]) -> None:
        token_set = set(tokens)
        for rule in self.context_rules:
            if rule["token"] not in token_set:
                continue
            applied = False
            for key in ("utility", "grocery"):
                if key not in rule:
                    continue
                cues, category, boost = rule[key]
                if any(cue in token_set or self._has_phrase(text, cue) for cue in cues):
                    scores[category] = scores.get(category, 0.0) + boost
                    applied = True
            if not applied and "default" in rule:
                category, boost = rule["default"]
                scores[category] = scores.get(category, 0.0) + boost

        if any(self._has_phrase(text, name) for name in ("uber eats", "doordash", "door dash", "grubhub")):
            scores["Food & Dining"] = scores.get("Food & Dining", 0.0) + 3.0
            scores["Transportation"] = scores.get("Transportation", 0.0) * 0.15

        if any(self._has_phrase(text, name) for name in ("netflix", "spotify", "hulu", "disney+", "disney plus")):
            scores["Subscriptions"] = scores.get("Subscriptions", 0.0) + 2.2
            scores["Entertainment"] = scores.get("Entertainment", 0.0) * 0.35

        if any(self._has_phrase(text, name) for name in ("flight", "airline", "hotel", "airbnb")):
            scores["Travel"] = scores.get("Travel", 0.0) + 1.8
            scores["Transportation"] = scores.get("Transportation", 0.0) * 0.4

        if self._has_phrase(text, "student loan"):
            scores["Debt & Loans"] = scores.get("Debt & Loans", 0.0) + 2.0
            scores["Education"] = scores.get("Education", 0.0) * 0.4

        if self._has_phrase(text, "mortgage") and not self._has_phrase(text, "insurance"):
            scores["Housing"] = scores.get("Housing", 0.0) + 1.6
            scores["Debt & Loans"] = scores.get("Debt & Loans", 0.0) * 0.3

        if self._has_phrase(text, "hydro") or self._has_phrase(text, "hydroelectric"):
            scores["Bills & Utilities"] = scores.get("Bills & Utilities", 0.0) + 3.0
            scores["Healthcare"] = 0.0
            scores["Pets"] = scores.get("Pets", 0.0) * 0.1

        if self._has_phrase(text, "gym"):
            scores["Fitness & Wellness"] = scores.get("Fitness & Wellness", 0.0) + 1.5
            scores["Subscriptions"] = scores.get("Subscriptions", 0.0) * 0.45

    def _softmax(self, scores: Dict[str, float]) -> Dict[str, float]:
        if not scores:
            return {}
        max_s = max(scores.values())
        exps = {k: math.exp((v - max_s) / self.TEMPERATURE) for k, v in scores.items()}
        total = sum(exps.values())
        if total <= 0:
            n = len(exps)
            return {k: 1.0 / n for k in exps}
        return {k: v / total for k, v in exps.items()}

    def _subcategory(self, description_lower: str) -> Optional[str]:
        if any(term in description_lower for term in ("subscription", "auto-pay", "autopay", "recurring")):
            return "Recurring"
        if any(term in description_lower for term in ("online", "app store", "digital")):
            return "Online"
        if any(term in description_lower for term in ("atm", "cash back", "withdrawal")):
            return "Cash"
        return None

    def score_categories(
        self,
        description: str,
        amount: float = 0.0,
        transaction_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not description or not description.strip():
            return {
                "category": "Other",
                "subcategory": None,
                "confidence": 0.0,
                "probabilities": {"Other": 1.0},
            }

        text = re.sub(r"[^a-z0-9&+\s'-]", " ", description.lower())
        text = re.sub(r"\s+", " ", text).strip()
        tokens = self._tokens(text)

        if not transaction_type:
            transaction_type = self._get_transaction_type_hint(amount, description)

        raw_scores: Dict[str, float] = {}
        matched_phrases: Dict[str, List[str]] = {}

        for category, data in self.category_keywords.items():
            if category == "Other":
                continue
            expected = data.get("transaction_types", ["expense", "income"])
            if transaction_type and transaction_type not in expected:
                continue

            score = float(data.get("prior", 0.0))
            hits = []
            for item in self._compiled[category]:
                if item["pattern"].search(text):
                    score += self._phrase_weight(item["n_tokens"], item["n_chars"])
                    hits.append(item["phrase"])

            if self.nlp and category in self.lemmatized_keywords:
                doc = self.nlp(text)
                lemma_text = " ".join(token.lemma_ for token in doc)
                for lemma in self.lemmatized_keywords[category]:
                    if lemma and _phrase_pattern(lemma).search(lemma_text):
                        score += 0.45

            if hits:
                raw_scores[category] = score
                matched_phrases[category] = hits

        self._apply_context(text, tokens, raw_scores)

        # Drop near-zero leftover scores from context-only noise.
        raw_scores = {k: v for k, v in raw_scores.items() if v >= self.MIN_SCORE}

        if not raw_scores:
            return {
                "category": "Other",
                "subcategory": self._subcategory(text),
                "confidence": 0.15,
                "probabilities": {"Other": 1.0},
                "matched_phrases": {},
            }

        probabilities = self._softmax(raw_scores)
        ranked = sorted(probabilities.items(), key=lambda kv: kv[1], reverse=True)
        best_category, best_p = ranked[0]
        second_p = ranked[1][1] if len(ranked) > 1 else 0.0
        margin = best_p - second_p
        # Low margin => ambiguous; shrink confidence toward a coin flip.
        confidence = best_p * (0.55 + 0.45 * min(1.0, margin / 0.35))
        confidence = max(0.05, min(0.99, confidence))

        return {
            "category": best_category,
            "subcategory": self._subcategory(text),
            "confidence": round(confidence, 4),
            "probabilities": {k: round(v, 4) for k, v in ranked[:5]},
            "matched_phrases": matched_phrases.get(best_category, []),
        }

    def categorize(
        self,
        description: str,
        amount: float = 0.0,
        transaction_type: Optional[str] = None,
    ) -> Tuple[str, Optional[str], float]:
        result = self.score_categories(description, amount, transaction_type)
        return result["category"], result["subcategory"], result["confidence"]

    def batch_categorize(self, transactions: List[Dict]) -> List[Dict]:
        results = []
        for transaction in transactions:
            if transaction.get("category"):
                transaction["ai_categorized"] = False
                transaction["confidence_score"] = 1.0
                results.append(transaction)
                continue
            category, subcategory, confidence = self.categorize(
                transaction.get("description", ""),
                transaction.get("amount", 0.0),
                transaction.get("transaction_type"),
            )
            transaction["category"] = category
            transaction["subcategory"] = subcategory
            transaction["confidence_score"] = confidence
            transaction["ai_categorized"] = True
            results.append(transaction)
        return results

    def get_available_categories(self, include_other: bool = True) -> List[str]:
        cats = [cat for cat in self.category_keywords.keys() if cat != "Other"]
        if include_other:
            cats.append("Other")
        return cats

    def get_categories_by_type(self, transaction_type: str) -> List[str]:
        categories = []
        for category, data in self.category_keywords.items():
            expected = data.get("transaction_types", ["expense", "income"])
            if transaction_type in expected:
                categories.append(category)
        return categories
