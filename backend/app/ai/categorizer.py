from typing import Dict, List, Tuple, Optional
import re

class TransactionCategorizer:
    def __init__(self):
        # Try to load spaCy model (optional)
        self.nlp = None
        try:
            import spacy
            try:
                self.nlp = spacy.load("en_core_web_sm")
                print("spaCy loaded successfully for enhanced categorization")
            except OSError:
                print("spaCy model not found. Using keyword-based categorization only.")
                self.nlp = None
        except ImportError:
            print("spaCy not installed. Using keyword-based categorization only.")
            self.nlp = None
        
        # Comprehensive category keywords mapping with weighted importance
        # Categories are ordered by priority (more specific first)
        self.category_keywords = {
            # INCOME CATEGORIES
            "Income": {
                "keywords": ["salary", "payroll", "paycheck", "wage", "income", "deposit", "transfer in", "direct deposit", 
                            "bonus", "commission", "freelance", "contractor", "dividend", "interest income", "refund", 
                            "reimbursement", "gift received", "allowance", "pension", "social security", "unemployment"],
                "patterns": [r"salary", r"payroll", r"paycheck", r"direct.deposit", r"income", r"dividend", r"interest.income"],
                "weight": 3.0,  # Higher weight for income keywords
                "transaction_types": ["income"]
            },
            "Investment Income": {
                "keywords": ["dividend", "capital gains", "investment return", "stock dividend", "bond interest", 
                            "mutual fund", "etf", "roi", "return on investment"],
                "patterns": [r"dividend", r"capital.gains", r"investment.return", r"stock.dividend"],
                "weight": 2.5,
                "transaction_types": ["income"]
            },
            
            # HOUSING & UTILITIES
            "Housing": {
                "keywords": ["rent", "mortgage", "housing", "apartment", "lease", "landlord", "property management", 
                            "homeowners", "hoa", "homeowners association", "condo fee", "maintenance fee"],
                "patterns": [r"rent", r"mortgage", r"housing", r"apartment", r"lease", r"hoa", r"condo"],
                "weight": 3.0,
                "transaction_types": ["expense"]
            },
            "Bills & Utilities": {
                "keywords": ["electric", "electricity", "power", "water", "hydro", "hydroelectric", "hydro bill", 
                            "hydro one", "hydro quebec", "sewer", "gas bill", "natural gas", "internet", 
                            "wifi", "phone", "telephone", "cell phone", "mobile", "utility", "utilities", "cable", 
                            "tv", "television", "trash", "garbage", "recycling", "heating", "cooling", "ac", 
                            "air conditioning", "utility bill", "public utility"],
                "patterns": [r"electric", r"electricity", r"water", r"hydro", r"hydroelectric", r"hydro.bill", 
                           r"internet", r"phone", r"utility", r"utilities", r"cable", r"wifi"],
                "weight": 3.0,  # Increased weight to prioritize utilities over healthcare
                "transaction_types": ["expense"]
            },
            
            # FOOD & DINING
            "Food & Dining": {
                "keywords": ["restaurant", "cafe", "food", "dining", "pizza", "burger", "coffee", "starbucks", "mcdonald", 
                            "mcdonalds", "uber eats", "doordash", "grubhub", "postmates", "delivery", "takeout", 
                            "fast food", "fastfood", "diner", "bar", "pub", "brewery", "bistro", "brunch", "lunch", 
                            "dinner", "breakfast", "catering", "food truck"],
                "patterns": [r"restaurant", r"cafe", r"food", r"dining", r"pizza", r"burger", r"starbucks", r"mcdonald", 
                           r"uber.eats", r"doordash", r"grubhub"],
                "weight": 2.5,
                "transaction_types": ["expense"]
            },
            "Groceries": {
                "keywords": ["grocery", "supermarket", "walmart", "target", "kroger", "safeway", "whole foods", 
                            "trader joe", "aldi", "costco", "sam's club", "wegmans", "publix", "food lion", 
                            "harris teeter", "stop & shop", "giant", "shoprite", "heb", "food market", "grocery store"],
                "patterns": [r"grocery", r"supermarket", r"walmart", r"target", r"kroger", r"safeway", r"whole.foods", 
                           r"trader.joe", r"costco"],
                "weight": 2.5,
                "transaction_types": ["expense"]
            },
            
            # TRANSPORTATION
            "Transportation": {
                "keywords": ["gas", "fuel", "gasoline", "petrol", "uber", "lyft", "taxi", "cab", "parking", "metro", 
                            "subway", "bus", "train", "airline", "flight", "airport", "transit", "public transport",
                            "rideshare", "ride share", "car rental", "rental car", "toll", "toll road", "ez pass",
                            "maintenance", "car repair", "auto repair", "oil change", "tire", "registration", "dmv"],
                "patterns": [r"gas", r"fuel", r"uber", r"lyft", r"parking", r"metro", r"subway", r"bus", r"train", 
                           r"airline", r"flight", r"toll"],
                "weight": 2.5,
                "transaction_types": ["expense"]
            },
            
            # SHOPPING & RETAIL
            "Shopping": {
                "keywords": ["amazon", "store", "shop", "retail", "clothing", "apparel", "mall", "department store",
                            "nordstrom", "macy's", "target", "walmart", "best buy", "home depot", "lowes", "ikea",
                            "furniture", "electronics", "appliance", "home goods", "decor", "bed bath", "bed bath & beyond"],
                "patterns": [r"amazon", r"store", r"shop", r"retail", r"mall", r"nordstrom", r"macy", r"best.buy"],
                "weight": 2.0,
                "transaction_types": ["expense"]
            },
            
            # ENTERTAINMENT & RECREATION
            "Entertainment": {
                "keywords": ["movie", "cinema", "theater", "theatre", "netflix", "spotify", "streaming", "concert", 
                            "show", "game", "video game", "gaming", "arcade", "bowling", "mini golf", "amusement",
                            "theme park", "disney", "universal", "ticket", "event", "festival", "sports event"],
                "patterns": [r"movie", r"cinema", r"netflix", r"spotify", r"streaming", r"concert", r"theater", r"game"],
                "weight": 2.0,
                "transaction_types": ["expense"]
            },
            "Subscriptions": {
                "keywords": ["subscription", "monthly", "annual", "premium", "membership", "netflix", "spotify", 
                            "apple music", "hulu", "disney+", "disney plus", "amazon prime", "youtube premium",
                            "gym membership", "fitness", "magazine", "newspaper", "software subscription", "saas"],
                "patterns": [r"subscription", r"membership", r"netflix", r"spotify", r"hulu", r"disney", r"amazon.prime"],
                "weight": 2.5,
                "transaction_types": ["expense"]
            },
            
            # HEALTHCARE & FITNESS
            "Healthcare": {
                "keywords": ["pharmacy", "hospital", "doctor", "medical", "drug", "cvs", "walgreens", "clinic", 
                            "urgent care", "emergency room", "er", "dentist", "dental", "optometrist", "eye doctor",
                            "prescription", "medication", "medicine", "health insurance", "copay", "co-pay", 
                            "lab test", "x-ray", "mri", "surgery", "therapy", "physical therapy"],
                "patterns": [r"pharmacy", r"hospital", r"doctor", r"medical", r"cvs", r"walgreens", r"clinic", 
                           r"prescription", r"dentist", r"dental"],
                "weight": 2.5,
                "transaction_types": ["expense"]
            },
            "Fitness & Wellness": {
                "keywords": ["gym", "fitness", "yoga", "pilates", "personal trainer", "fitness class", "workout",
                            "spa", "massage", "salon", "haircut", "barber", "nail", "manicure", "pedicure"],
                "patterns": [r"gym", r"fitness", r"yoga", r"pilates", r"spa", r"massage", r"salon", r"haircut"],
                "weight": 2.0,
                "transaction_types": ["expense"]
            },
            
            # PERSONAL CARE
            "Personal Care": {
                "keywords": ["pharmacy", "cvs", "walgreens", "rite aid", "drugstore", "cosmetics", "makeup", 
                            "skincare", "beauty", "personal care", "toiletries", "shampoo", "soap", "deodorant"],
                "patterns": [r"pharmacy", r"drugstore", r"cosmetics", r"makeup", r"skincare", r"beauty"],
                "weight": 2.0,
                "transaction_types": ["expense"]
            },
            
            # EDUCATION
            "Education": {
                "keywords": ["school", "university", "college", "tuition", "course", "book", "textbook", "education",
                            "student loan", "student debt", "tuition payment", "course fee", "registration fee",
                            "online course", "certification", "training", "workshop", "seminar"],
                "patterns": [r"school", r"university", r"college", r"tuition", r"student.loan", r"textbook"],
                "weight": 2.5,
                "transaction_types": ["expense"]
            },
            
            # INSURANCE
            "Insurance": {
                "keywords": ["insurance", "premium", "health insurance", "car insurance", "auto insurance", 
                            "home insurance", "renters insurance", "life insurance", "disability insurance",
                            "geico", "state farm", "allstate", "progressive", "usaa"],
                "patterns": [r"insurance", r"premium", r"geico", r"state.farm", r"allstate", r"progressive"],
                "weight": 2.5,
                "transaction_types": ["expense"]
            },
            
            # FINANCIAL SERVICES
            "Banking & Fees": {
                "keywords": ["fee", "bank fee", "atm fee", "overdraft", "service charge", "maintenance fee",
                            "transaction fee", "wire transfer", "foreign transaction", "late fee", "penalty",
                            "interest charge", "finance charge", "annual fee"],
                "patterns": [r"fee", r"bank.fee", r"atm.fee", r"overdraft", r"service.charge", r"late.fee"],
                "weight": 2.0,
                "transaction_types": ["expense"]
            },
            "Investments": {
                "keywords": ["investment", "stock", "bond", "mutual fund", "etf", "401k", "ira", "roth ira",
                            "retirement", "brokerage", "robinhood", "fidelity", "vanguard", "charles schwab",
                            "trade", "buy stock", "sell stock", "contribution"],
                "patterns": [r"investment", r"stock", r"bond", r"mutual.fund", r"401k", r"ira", r"retirement", 
                           r"brokerage", r"robinhood", r"fidelity"],
                "weight": 2.5,
                "transaction_types": ["expense", "income"]
            },
            
            # DEBT & LOANS
            "Debt & Loans": {
                "keywords": ["loan", "payment", "credit card", "pay off", "debt", "mortgage payment", 
                            "car loan", "auto loan", "student loan payment", "personal loan", "payday loan",
                            "credit card payment", "minimum payment", "principal", "interest payment"],
                "patterns": [r"loan", r"payment", r"credit.card", r"pay.off", r"debt", r"mortgage.payment"],
                "weight": 2.5,
                "transaction_types": ["expense"]
            },
            
            # TRAVEL
            "Travel": {
                "keywords": ["hotel", "airbnb", "booking", "flight", "airline", "airport", "travel", "vacation",
                            "trip", "cruise", "resort", "car rental", "rental car", "travel agency", "expedia",
                            "priceline", "kayak", "booking.com", "luggage", "passport", "visa"],
                "patterns": [r"hotel", r"airbnb", r"booking", r"flight", r"airline", r"travel", r"vacation", 
                           r"cruise", r"resort", r"expedia"],
                "weight": 2.5,
                "transaction_types": ["expense"]
            },
            
            # GIFTS & DONATIONS
            "Gifts & Donations": {
                "keywords": ["gift", "donation", "charity", "charitable", "nonprofit", "ngo", "fundraiser",
                            "go fund me", "gofundme", "kickstarter", "patreon", "tip", "gratuity"],
                "patterns": [r"gift", r"donation", r"charity", r"charitable", r"nonprofit", r"fundraiser", r"tip"],
                "weight": 2.0,
                "transaction_types": ["expense"]
            },
            
            # BUSINESS & PROFESSIONAL
            "Business Expenses": {
                "keywords": ["business", "office", "supplies", "equipment", "software", "advertising", "marketing",
                            "professional", "consulting", "legal", "lawyer", "attorney", "accountant", "cpa",
                            "conference", "business trip", "client", "contractor", "freelancer"],
                "patterns": [r"business", r"office", r"supplies", r"equipment", r"software", r"advertising", 
                           r"marketing", r"legal", r"lawyer", r"attorney"],
                "weight": 2.0,
                "transaction_types": ["expense"]
            },
            
            # KIDS & FAMILY
            "Kids & Family": {
                "keywords": ["childcare", "daycare", "babysitter", "nanny", "school supplies", "toy", "toys",
                            "baby", "infant", "diaper", "formula", "stroller", "car seat", "children", "kids"],
                "patterns": [r"childcare", r"daycare", r"babysitter", r"nanny", r"school.supplies", r"toy", r"baby"],
                "weight": 2.0,
                "transaction_types": ["expense"]
            },
            
            # PETS
            "Pets": {
                "keywords": ["pet", "dog", "cat", "veterinary", "vet", "pet store", "petco", "petsmart",
                            "pet food", "pet supplies", "grooming", "pet grooming"],
                "patterns": [r"pet", r"dog", r"cat", r"veterinary", r"vet", r"pet.store", r"petco", r"petsmart"],
                "weight": 2.0,
                "transaction_types": ["expense"]
            },
            
            # TAXES
            "Taxes": {
                "keywords": ["tax", "irs", "federal tax", "state tax", "property tax", "sales tax", "income tax",
                            "tax payment", "tax refund", "withholding"],
                "patterns": [r"tax", r"irs", r"federal.tax", r"state.tax", r"property.tax", r"income.tax"],
                "weight": 2.5,
                "transaction_types": ["expense", "income"]
            },
            
            # OTHER
            "Other": {
                "keywords": [],
                "patterns": [],
                "weight": 0.0,
                "transaction_types": ["expense", "income"]
            }
        }
        
        # Build lemmatized keyword cache for better matching
        self.lemmatized_keywords = {}
        if self.nlp:
            self._build_lemmatized_cache()
    
    def _build_lemmatized_cache(self):
        """Build a cache of lemmatized keywords for faster matching."""
        if not self.nlp:
            return
        
        for category, data in self.category_keywords.items():
            lemmatized = []
            for keyword in data["keywords"]:
                doc = self.nlp(keyword)
                lemma = " ".join([token.lemma_ for token in doc])
                lemmatized.append(lemma)
            self.lemmatized_keywords[category] = lemmatized
    
    def _get_transaction_type_hint(self, amount: float, description: str) -> Optional[str]:
        """Infer transaction type from amount and description."""
        description_lower = description.lower()
        
        # Income indicators
        income_indicators = ["deposit", "salary", "payroll", "paycheck", "income", "refund", "reimbursement",
                           "dividend", "interest", "bonus", "commission", "transfer in"]
        if any(indicator in description_lower for indicator in income_indicators):
            return "income"
        
        # If amount is positive and description suggests income
        if amount > 0 and any(word in description_lower for word in ["deposit", "salary", "income", "refund"]):
            return "income"
        
        # Default to expense
        return "expense"
    
    def categorize(self, description: str, amount: float = 0.0, transaction_type: Optional[str] = None) -> Tuple[str, str, float]:
        """
        Categorize a transaction based on its description using enhanced NLP.
        Returns: (category, subcategory, confidence_score)
        """
        if not description or not description.strip():
            return "Other", None, 0.1
        
        description_lower = description.lower().strip()
        
        # Infer transaction type if not provided
        if not transaction_type:
            transaction_type = self._get_transaction_type_hint(amount, description)
        
        # Process with spaCy if available
        doc = None
        lemmatized_description = None
        if self.nlp:
            doc = self.nlp(description_lower)
            lemmatized_description = " ".join([token.lemma_ for token in doc])
        
        best_match = None
        best_score = 0.0
        best_category = "Other"
        best_subcategory = None
        
        # Score each category
        for category, data in self.category_keywords.items():
            if category == "Other":
                continue
            
            # Check if transaction type matches category's expected types
            expected_types = data.get("transaction_types", ["expense", "income"])
            if transaction_type and transaction_type not in expected_types:
                continue  # Skip categories that don't match transaction type
            
            score = 0.0
            weight = data.get("weight", 1.0)
            
            # 1. Direct keyword matching (highest priority)
            for keyword in data["keywords"]:
                keyword_lower = keyword.lower()
                # Check for exact word match (word boundaries) - prevents substring false matches
                if keyword_lower == description_lower:
                    score += 5.0 * weight  # Exact description match gets highest score
                elif f" {keyword_lower} " in f" {description_lower} ":
                    score += 4.0 * weight  # Word boundary match
                elif keyword_lower in description_lower:
                    # Check if it's a utility-specific term that shouldn't match healthcare
                    if keyword_lower in ["hydro", "hydroelectric", "hydro bill"] and category == "Bills & Utilities":
                        score += 4.0 * weight  # High score for utility terms
                    else:
                        score += 2.0 * weight  # Regular substring match
            
            # 2. Pattern matching (regex)
            for pattern in data["patterns"]:
                if re.search(pattern, description_lower, re.IGNORECASE):
                    score += 1.5 * weight
            
            # 3. Lemmatized keyword matching (spaCy)
            if lemmatized_description and category in self.lemmatized_keywords:
                for lemmatized_keyword in self.lemmatized_keywords[category]:
                    if lemmatized_keyword in lemmatized_description:
                        score += 1.5 * weight
            
            # 4. Named entity recognition (spaCy) - merchants, organizations
            if doc:
                for ent in doc.ents:
                    ent_text_lower = ent.text.lower()
                    # Check if entity matches any keyword
                    for keyword in data["keywords"]:
                        if keyword in ent_text_lower or ent_text_lower in keyword:
                            if ent.label_ in ["ORG", "PERSON"]:  # Organizations and person names
                                score += 2.0 * weight
                            elif ent.label_ in ["GPE", "LOC"]:  # Locations
                                score += 1.0 * weight
            
            # 5. Word similarity using spaCy (for typos and variations)
            # Skip if model doesn't have word vectors (en_core_web_sm doesn't have them)
            if doc and len(data["keywords"]) > 0:
                try:
                    # Check if model has vectors loaded
                    if doc.has_vector and len(doc.vector) > 0:
                        # Check similarity with key merchant names
                        for keyword in data["keywords"][:5]:  # Limit to first 5 for performance
                            keyword_doc = self.nlp(keyword)
                            if keyword_doc.has_vector:
                                similarity = doc.similarity(keyword_doc)
                                if similarity > 0.7:  # High similarity threshold
                                    score += similarity * 1.5 * weight
                except (AttributeError, ValueError):
                    # Model doesn't support similarity or vectors not available
                    # Skip this feature silently
                    pass
            
            # 6. POS tag matching (verbs, nouns related to category)
            if doc:
                # Look for relevant POS tags
                relevant_pos = {"NOUN", "PROPN"}  # Nouns and proper nouns
                for token in doc:
                    if token.pos_ in relevant_pos:
                        token_lower = token.text.lower()
                        if any(keyword in token_lower or token_lower in keyword 
                              for keyword in data["keywords"][:10]):  # Check against first 10 keywords
                            score += 0.5 * weight
            
            if score > best_score:
                best_score = score
                best_category = category
                best_match = data
        
        # Determine subcategory based on specific terms and patterns
        subcategory = None
        if doc:
            # Use spaCy for better subcategory detection
            subcategory = self._detect_subcategory(description_lower, doc, lemmatized_description)
        else:
            subcategory = self._detect_subcategory_simple(description_lower)
        
        # Normalize confidence score (0-1)
        # Higher scores get higher confidence, but cap at 1.0
        max_possible_score = 20.0  # Approximate max score for very strong matches
        confidence = min(best_score / max_possible_score, 1.0) if best_score > 0 else 0.2
        
        # Boost confidence for exact matches
        if best_score >= 5.0:
            confidence = min(confidence * 1.2, 1.0)
        
        return best_category, subcategory, confidence
    
    def _detect_subcategory(self, description_lower: str, doc, lemmatized_description: Optional[str]) -> Optional[str]:
        """Detect subcategory using NLP."""
        # Recurring/Subscription
        recurring_terms = ["subscription", "monthly", "annual", "recurring", "auto-pay", "autopay", "renewal"]
        if any(term in description_lower for term in recurring_terms):
            return "Recurring"
        
        # Online/Digital
        online_terms = ["online", "app", "digital", "download", "software", "saas", "cloud"]
        if any(term in description_lower for term in online_terms):
            return "Online"
        
        # Cash
        cash_terms = ["cash", "atm", "withdrawal", "cash back"]
        if any(term in description_lower for term in cash_terms):
            return "Cash"
        
        # In-person
        inperson_terms = ["in-store", "in store", "physical", "retail location"]
        if any(term in description_lower for term in inperson_terms):
            return "In-Person"
        
        return None
    
    def _detect_subcategory_simple(self, description_lower: str) -> Optional[str]:
        """Simple subcategory detection without NLP."""
        if "subscription" in description_lower or "monthly" in description_lower:
            return "Recurring"
        elif "online" in description_lower or "app" in description_lower:
            return "Online"
        elif "cash" in description_lower or "atm" in description_lower:
            return "Cash"
        return None
    
    def batch_categorize(self, transactions: List[Dict]) -> List[Dict]:
        """Categorize multiple transactions at once with enhanced NLP."""
        results = []
        for transaction in transactions:
            category, subcategory, confidence = self.categorize(
                transaction.get("description", ""),
                transaction.get("amount", 0.0),
                transaction.get("transaction_type")
            )
            transaction["category"] = category
            transaction["subcategory"] = subcategory
            transaction["confidence_score"] = confidence
            transaction["ai_categorized"] = True
            results.append(transaction)
        return results
    
    def get_available_categories(self) -> List[str]:
        """Get list of all available categories."""
        return [cat for cat in self.category_keywords.keys() if cat != "Other"]
    
    def get_categories_by_type(self, transaction_type: str) -> List[str]:
        """Get categories available for a specific transaction type."""
        categories = []
        for category, data in self.category_keywords.items():
            if category == "Other":
                categories.append(category)
                continue
            expected_types = data.get("transaction_types", ["expense", "income"])
            if transaction_type in expected_types:
                categories.append(category)
        return categories

