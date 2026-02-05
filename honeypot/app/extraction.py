import re
import hashlib
import logging
from typing import List, Optional, Dict, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Try to import optional dependencies with fallbacks
try:
    import validators

    HAS_VALIDATORS = True
except ImportError:
    HAS_VALIDATORS = False
    logging.warning("validators library not available, using fallback validation")

try:
    import tldextract

    HAS_TLDEXTRACT = True
except ImportError:
    HAS_TLDEXTRACT = False
    logging.warning(
        "tldextract library not available, using fallback domain extraction"
    )

from .schemas import *


@dataclass
class ValidationResult:
    is_valid: bool
    confidence: float
    issues: List[str] = field(default_factory=list)
    normalized_value: Optional[str] = None


class BankValidator:
    """Validates Indian bank account numbers and IFSC codes."""

    # Bank name mapping from IFSC prefix
    BANK_NAMES = {
        "SBIN": "State Bank of India",
        "HDFC": "HDFC Bank",
        "ICIC": "ICICI Bank",
        "UTIB": "Axis Bank",
        "KKBK": "Kotak Mahindra Bank",
        "IBKL": "IDBI Bank",
        "PUNB": "Punjab National Bank",
        "CBIN": "Central Bank of India",
        "BARC": "Bank of Baroda",
        "CNRB": "Canara Bank",
        "UBIN": "Union Bank of India",
        "IOBA": "Indian Overseas Bank",
        "SYNB": "Syndicate Bank",
        "ANDB": "Andhra Bank",
        "MAHB": "Bank of Maharashtra",
        "CORP": "Corporation Bank",
        "VIJB": "Vijaya Bank",
        "OBC": "Oriental Bank of Commerce",
        "ALLA": "Allahabad Bank",
        "UCBA": "UCO Bank",
        "BKID": "Bank of India",
        "YESB": "Yes Bank",
        "INDB": "IndusInd Bank",
        "FDRL": "Federal Bank",
        "RATN": "RBL Bank",
        "ESFB": "Equitas Small Finance Bank",
        "UJJI": "Ujjivan Small Finance Bank",
    }

    @classmethod
    def validate_account_number(cls, account: str) -> ValidationResult:
        """Validate bank account number format."""
        issues = []
        confidence = 0.5

        # Check length
        if not (9 <= len(account) <= 18):
            issues.append(f"Invalid length: {len(account)} digits (expected 9-18)")
        else:
            confidence += 0.2

        # Check all digits
        if not account.isdigit():
            issues.append("Contains non-digit characters")
        else:
            confidence += 0.2

        # Check for repeated digits (suspicious)
        if len(set(account)) == 1:
            issues.append("Suspicious: all same digits")
            confidence -= 0.3

        # Check for sequential patterns (suspicious)
        if cls._is_sequential(account):
            issues.append("Suspicious: sequential pattern")
            confidence -= 0.2

        return ValidationResult(
            is_valid=len(issues) < 2,
            confidence=max(0.0, min(1.0, confidence)),
            issues=issues,
            normalized_value=account,
        )

    @classmethod
    def validate_ifsc(cls, ifsc: str) -> ValidationResult:
        """Validate IFSC code format."""
        issues = []
        confidence = 0.5

        # Check format: 4 letters + 0 + 6 alphanumeric
        pattern = r"^[A-Z]{4}0[A-Z0-9]{6}$"
        if not re.match(pattern, ifsc):
            issues.append("Invalid format (expected: AAAA0XXXXXX)")
        else:
            confidence += 0.3

        # Check bank code
        bank_code = ifsc[:4]
        if bank_code in cls.BANK_NAMES:
            confidence += 0.2
        else:
            issues.append(f"Unknown bank code: {bank_code}")

        return ValidationResult(
            is_valid=len(issues) < 2,
            confidence=max(0.0, min(1.0, confidence)),
            issues=issues,
            normalized_value=ifsc.upper(),
        )

    @classmethod
    def get_bank_name(cls, ifsc: str) -> Optional[str]:
        """Get bank name from IFSC code."""
        bank_code = ifsc[:4].upper()
        return cls.BANK_NAMES.get(bank_code)

    @staticmethod
    def _is_sequential(s: str) -> bool:
        """Check if string has sequential digits."""
        if len(s) < 3:
            return False

        # Check ascending
        if all(int(s[i]) == int(s[i - 1]) + 1 for i in range(1, len(s))):
            return True

        # Check descending
        if all(int(s[i]) == int(s[i - 1]) - 1 for i in range(1, len(s))):
            return True

        return False


class UPIValidator:
    """Validates UPI IDs."""

    VALID_HANDLES = {
        "ybl",
        "paytm",
        "okicici",
        "okhdfcbank",
        "okaxis",
        "oksbi",
        "apl",
        "axl",
        "ibl",
        "upi",
        "freecharge",
        "phonepe",
        "icici",
        "hdfcbank",
        "axis",
        "sbi",
        "pnb",
        "bob",
        "unionbank",
        "kotak",
        "indus",
        "yesbank",
        "idfcbank",
        "bandhan",
        "federal",
        "rbl",
        "ujjivan",
        "equitas",
        "airtel",
        "jio",
        "amazon",
        "googlepay",
        "whatsapp",
    }

    SUSPICIOUS_PATTERNS = [
        r"police",
        r"cbi",
        r"rbi",
        r"support",
        r"help",
        r"verify",
        r"confirm",
        r"secure",
        r"official",
        r"admin",
    ]

    @classmethod
    def validate(cls, upi_id: str) -> ValidationResult:
        """Validate UPI ID format."""
        issues = []
        confidence = 0.5

        # Basic format check
        if "@" not in upi_id:
            issues.append("Missing @ symbol")
            return ValidationResult(False, 0.0, issues)

        parts = upi_id.split("@")
        if len(parts) != 2:
            issues.append("Invalid format")
            return ValidationResult(False, 0.0, issues)

        username, handle = parts

        # Validate username
        if len(username) < 3:
            issues.append("Username too short")
        elif len(username) > 50:
            issues.append("Username too long")
        else:
            confidence += 0.2

        # Validate handle
        handle_lower = handle.lower()
        if handle_lower in cls.VALID_HANDLES:
            confidence += 0.3
        else:
            issues.append(f"Unrecognized handle: {handle}")

        # Check for suspicious patterns in username
        for pattern in cls.SUSPICIOUS_PATTERNS:
            if re.search(pattern, username, re.IGNORECASE):
                issues.append(f"Suspicious pattern in username: {pattern}")
                confidence -= 0.2

        return ValidationResult(
            is_valid=len(issues) < 2,
            confidence=max(0.0, min(1.0, confidence)),
            issues=issues,
            normalized_value=f"{username}@{handle_lower}",
        )


class PhoneValidator:
    """Validates Indian phone numbers."""

    CARRIER_PREFIXES = {
        "6": ["Jio", "Vodafone", "Airtel"],
        "7": ["Airtel", "Vodafone", "Jio"],
        "8": ["Vodafone", "Airtel", "Jio", "BSNL"],
        "9": ["Vodafone", "Airtel", "Jio", "BSNL"],
    }

    @classmethod
    def validate(cls, phone: str) -> ValidationResult:
        """Validate Indian phone number."""
        issues = []
        confidence = 0.5

        # Remove all non-digits
        digits = re.sub(r"\D", "", phone)

        # Handle +91 prefix
        if digits.startswith("91") and len(digits) == 12:
            digits = digits[2:]
            confidence += 0.1
        elif digits.startswith("0") and len(digits) == 11:
            digits = digits[1:]

        # Check length
        if len(digits) != 10:
            issues.append(f"Invalid length: {len(digits)} digits (expected 10)")
            return ValidationResult(False, 0.0, issues)

        # Check first digit (must be 6-9)
        first_digit = digits[0]
        if first_digit not in "6789":
            issues.append(f"Invalid prefix: must start with 6, 7, 8, or 9")
        else:
            confidence += 0.2
            if first_digit in cls.CARRIER_PREFIXES:
                confidence += 0.1

        # Check for repeated digits
        if len(set(digits)) == 1:
            issues.append("Suspicious: all same digits")
            confidence -= 0.3

        # Format: +91 XXXXX XXXXX
        normalized = f"+91{digits}"
        formatted = f"+91-{digits[:5]}-{digits[5:]}"

        return ValidationResult(
            is_valid=len(issues) < 2,
            confidence=max(0.0, min(1.0, confidence)),
            issues=issues,
            normalized_value=normalized,
        )


class URLValidator:
    """Validates and analyzes URLs."""

    SUSPICIOUS_TLDS = {
        ".tk",
        ".ml",
        ".ga",
        ".cf",
        ".top",
        ".xyz",
        ".click",
        ".link",
        ".work",
        ".date",
        ".racing",
    }

    TRUSTED_DOMAINS = {
        "sbi.co.in",
        "hdfcbank.com",
        "icicibank.com",
        "axisbank.com",
        "kotak.com",
        "yesbank.in",
        "indusind.com",
        "rblbank.com",
        "paytm.com",
        "phonepe.com",
        "google.com",
        "amazon.in",
        "flipkart.com",
        " RBI.org.in",
        "cbi.gov.in",
    }

    PHISHING_KEYWORDS = [
        "verify",
        "secure",
        "update",
        "login",
        "signin",
        "confirm",
        "account",
        "banking",
        "password",
        "credential",
        "security",
    ]

    BANK_KEYWORDS = [
        "sbi",
        "hdfc",
        "icici",
        "axis",
        "pnb",
        "bob",
        "union",
        "kotak",
        "yes",
        "indusind",
    ]

    @classmethod
    def analyze(cls, url: str) -> Dict:
        """Comprehensive URL analysis."""
        result = {
            "original": url,
            "risk_score": 0.3,
            "suspicious_indicators": [],
            "impersonating": None,
            "domain_age_estimate": "unknown",
            "is_shortened": False,
            "redirects_to": None,
        }

        # Parse URL
        try:
            if HAS_TLDEXTRACT:
                extracted = tldextract.extract(url)
                domain = f"{extracted.domain}.{extracted.suffix}"
                subdomain = extracted.subdomain
                suffix = extracted.suffix
            else:
                # Fallback domain extraction using regex
                domain_match = re.search(r"https?://(?:www\.)?([^/]+)", url)
                if domain_match:
                    domain = domain_match.group(1)
                    subdomain = ""
                    # Extract suffix from domain
                    parts = domain.split(".")
                    suffix = parts[-1] if len(parts) > 1 else ""
                else:
                    raise ValueError("Could not parse URL")
        except Exception as e:
            result["risk_score"] = 0.9
            result["suspicious_indicators"].append(f"Failed to parse URL: {str(e)}")
            return result

        # Check for suspicious TLD
        if f".{suffix}" in cls.SUSPICIOUS_TLDS:
            result["risk_score"] += 0.4
            result["suspicious_indicators"].append(f"Suspicious TLD: .{suffix}")

        # Check for typosquatting
        for trusted in cls.TRUSTED_DOMAINS:
            if cls._is_typosquatting(domain, trusted):
                result["risk_score"] += 0.3
                result["suspicious_indicators"].append(
                    f"Possible typosquatting of {trusted}"
                )
                result["impersonating"] = trusted.split(".")[0].upper()

        # Check for bank impersonation
        for bank in cls.BANK_KEYWORDS:
            if bank in domain.lower():
                # Check if it's actually that bank's domain
                is_legitimate = any(bank in trusted for trusted in cls.TRUSTED_DOMAINS)
                if not is_legitimate:
                    result["risk_score"] += 0.3
                    result["suspicious_indicators"].append(
                        f"Possible {bank.upper()} impersonation"
                    )
                    result["impersonating"] = bank.upper()

        # Check for phishing keywords in domain
        for keyword in cls.PHISHING_KEYWORDS:
            if keyword in domain.lower():
                result["risk_score"] += 0.15
                result["suspicious_indicators"].append(f"Phishing keyword: {keyword}")

        # Check for hyphens in domain (common in phishing)
        if "-" in domain:
            result["risk_score"] += 0.1
            result["suspicious_indicators"].append("Hyphenated domain")

        # Check for IP addresses instead of domains
        if re.match(r"^\d+\.\d+\.\d+\.\d+", domain):
            result["risk_score"] += 0.5
            result["suspicious_indicators"].append("IP address instead of domain")

        # Check for URL shorteners
        shorteners = ["bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly"]
        if any(short in domain.lower() for short in shorteners):
            result["is_shortened"] = True
            result["risk_score"] += 0.2
            result["suspicious_indicators"].append("URL shortener detected")

        result["risk_score"] = min(1.0, result["risk_score"])
        return result

    @staticmethod
    def _is_typosquatting(domain: str, trusted: str) -> bool:
        """Check if domain is typosquatting trusted domain."""
        from difflib import SequenceMatcher

        similarity = SequenceMatcher(None, domain.lower(), trusted.lower()).ratio()

        # High similarity but not exact match
        if 0.7 < similarity < 1.0:
            return True

        # Common typosquatting patterns
        if trusted.replace(".", "") in domain and domain != trusted:
            return True

        return False


class AdvancedExtractionEngine:
    """Enhanced extraction with validation and enrichment."""

    def __init__(self):
        # Patterns
        self.bank_pattern = r"\b\d{9,18}\b"
        self.ifsc_pattern = r"\b[A-Z]{4}0[A-Z0-9]{6}\b"
        self.upi_pattern = r"\b[\w.-]+@[\w.-]+\b"
        self.phone_pattern = r"(?:\+91[-\s]?)?[6-9]\d{9}\b"
        self.url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        self.email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

        # Context patterns for better extraction
        self.bank_contexts = [
            r"(?:account|a/c|acc|account number|ac no)[^\w]*[:\-]?\s*(\d{9,18})",
            r"(?:transfer|send|deposit|payment)[^\w]*(?:to|in|into)?[^\w]*(\d{9,18})",
        ]

        self.upi_handles = {
            "ybl",
            "paytm",
            "okicici",
            "okhdfcbank",
            "okaxis",
            "oksbi",
            "apl",
            "axl",
            "ibl",
            "upi",
            "freecharge",
            "phonepe",
        }

    def extract_bank_accounts(
        self, text: str, context_window: int = 100
    ) -> List[BankAccount]:
        """Extract and validate bank accounts."""
        accounts = []
        seen = set()

        # Find all potential account numbers
        matches = list(re.finditer(self.bank_pattern, text))

        for match in matches:
            num = match.group()

            # Skip if already seen
            if num in seen:
                continue
            seen.add(num)

            # Get context around match
            start = max(0, match.start() - context_window)
            end = min(len(text), match.end() + context_window)
            context = text[start:end]

            # Validate
            validation = BankValidator.validate_account_number(num)

            if validation.is_valid:
                # Try to find IFSC in context
                ifsc_match = re.search(self.ifsc_pattern, context)
                ifsc = None
                bank_name = None

                if ifsc_match:
                    ifsc = ifsc_match.group()
                    ifsc_validation = BankValidator.validate_ifsc(ifsc)
                    if ifsc_validation.is_valid:
                        bank_name = BankValidator.get_bank_name(ifsc)

                # Calculate confidence
                confidence = validation.confidence
                if ifsc:
                    confidence += 0.1
                if bank_name:
                    confidence += 0.05

                accounts.append(
                    BankAccount(
                        account_number=num,
                        ifsc_code=ifsc,
                        bank_name=bank_name,
                        confidence=min(1.0, confidence),
                    )
                )

        return accounts

    def extract_upi_ids(self, text: str) -> List[UPIID]:
        """Extract and validate UPI IDs."""
        upis = []
        seen = set()

        matches = re.finditer(self.upi_pattern, text)

        for match in matches:
            upi_id = match.group()

            # Skip emails
            if re.match(self.email_pattern, upi_id):
                continue

            # Skip if already seen
            if upi_id.lower() in seen:
                continue
            seen.add(upi_id.lower())

            # Must contain @
            if "@" not in upi_id:
                continue

            parts = upi_id.split("@")
            if len(parts) != 2:
                continue

            handle = parts[1].lower()

            # Check if handle is valid UPI handle
            if handle in self.upi_handles or any(h in handle for h in self.upi_handles):
                validation = UPIValidator.validate(upi_id)

                upis.append(
                    UPIID(
                        upi_id=validation.normalized_value or upi_id.lower(),
                        confidence=validation.confidence,
                    )
                )

        return upis

    def extract_phone_numbers(self, text: str) -> List[PhoneNumber]:
        """Extract and validate phone numbers."""
        phones = []
        seen = set()

        matches = re.finditer(self.phone_pattern, text)

        for match in matches:
            raw = match.group()

            # Validate
            validation = PhoneValidator.validate(raw)

            if validation.is_valid and validation.normalized_value:
                normalized = validation.normalized_value

                # Skip duplicates
                if normalized in seen:
                    continue
                seen.add(normalized)

                phones.append(
                    PhoneNumber(number=normalized, confidence=validation.confidence)
                )

        return phones

    def extract_urls(self, text: str) -> List[URL]:
        """Extract and analyze URLs."""
        urls = []
        seen = set()

        matches = re.finditer(self.url_pattern, text)

        for match in matches:
            url = match.group()

            # Skip if already seen
            if url.lower() in seen:
                continue
            seen.add(url.lower())

            # Analyze
            analysis = URLValidator.analyze(url)

            # Extract domain with fallback
            if HAS_TLDEXTRACT:
                domain = tldextract.extract(url).registered_domain
            else:
                # Fallback extraction
                domain_match = re.search(r"https?://(?:www\.)?([^/]+)", url)
                domain = domain_match.group(1) if domain_match else url

            urls.append(
                URL(
                    url=url,
                    domain=domain,
                    risk_score=analysis["risk_score"],
                    impersonating=analysis["impersonating"],
                    is_active=True,
                )
            )

        return urls

    def extract_emails(self, text: str) -> List[Email]:
        """Extract and validate emails."""
        emails = []
        seen = set()

        matches = re.finditer(self.email_pattern, text)

        for match in matches:
            email = match.group()

            # Skip if already seen
            if email.lower() in seen:
                continue
            seen.add(email.lower())

            # Basic validation
            is_valid_email = False
            if HAS_VALIDATORS:
                is_valid_email = validators.email(email)
            else:
                # Fallback email validation using regex
                is_valid_email = bool(
                    re.match(
                        r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$", email
                    )
                )

            if is_valid_email:
                emails.append(Email(email=email.lower(), confidence=0.85))

        return emails

    def extract_identity(self, text: str) -> Optional[ScammerIdentity]:
        """Extract scammer identity with improved accuracy."""
        identity = ScammerIdentity()
        text_lower = text.lower()

        # Name extraction with context
        name_patterns = [
            (
                r"(?:i am|this is|myself|speaking)[,\s]+(?:mr\.?|mrs\.?|ms\.?|dr\.?)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
                1,
            ),
            (
                r"(?:inspector|officer|manager|sir|madam|executive)[,\s]+([A-Z][a-z]+)",
                1,
            ),
            (r"name\s+(?:is)?\s*[:\-]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", 1),
            (r"(?:from|representing)\s+(?:the\s+)?(?:office\s+of\s+)?([A-Z][a-z]+)", 1),
        ]

        for pattern, group in name_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.group(group).strip()
                if len(name) > 2 and not any(
                    x in name.lower() for x in ["the", "this", "that", "from"]
                ):
                    identity.claimed_name = name
                    break
            if identity.claimed_name:
                break

        # Organization extraction with better patterns
        org_patterns = [
            r"(?:from|calling from|department of|office of)\s+(?:the\s+)?(CBI|RBI|Income Tax(?:\s+Department)?|Police(?:\s+Department)?|ED|Enforcement Directorate)",
            r"(?:this is|representing)\s+(?:the\s+)?(Paytm|PhonePe|Google Pay|Amazon|Flipkart|SBI|HDFC Bank|ICICI Bank|Axis Bank)",
            r"(Reserve Bank of India|Central Bureau of Investigation)",
        ]

        for pattern in org_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                org = match.group(1).title()
                identity.claimed_organization = org

                # Set impersonation type
                if any(
                    x in org.lower()
                    for x in ["cbi", "police", "income tax", "ed", "enforcement"]
                ):
                    identity.impersonation_type = "Law_Enforcement"
                elif any(
                    x in org.lower()
                    for x in [
                        "paytm",
                        "phonepe",
                        "google",
                        "sbi",
                        "hdfc",
                        "icici",
                        "axis",
                        "rbi",
                    ]
                ):
                    identity.impersonation_type = "Financial_Institution"
                elif any(x in org.lower() for x in ["amazon", "flipkart"]):
                    identity.impersonation_type = "Corporate"

                break

        # Designation extraction
        desig_patterns = [
            r"(?:senior\s+)?(inspector|officer|manager|director|head|supervisor|executive|representative)(?:\s+of\s+)?(?:the\s+)?([A-Za-z\s]+)?",
            r"(cyber crime officer|investigation officer|nodal officer)",
        ]

        for pattern in desig_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                designation = match.group(0).strip()
                if len(designation) > 3:
                    identity.claimed_designation = designation.title()
                    break

        # Only return if we found something meaningful
        if any(
            [
                identity.claimed_name,
                identity.claimed_organization,
                identity.claimed_designation,
            ]
        ):
            return identity

        return None

    def extract_crypto_wallets(self, text: str) -> List[CryptoWallet]:
        """Extract cryptocurrency wallet addresses."""
        wallets = []
        seen = set()

        # Bitcoin patterns
        btc_patterns = [
            r"\b(1)[A-HJ-NP-Za-km-z1-9]{25,34}\b",  # Legacy P2PKH
            r"\b(3)[A-HJ-NP-Za-km-z1-9]{25,34}\b",  # Legacy P2SH
            r"\bbc1[a-zA-HJ-NP-Z0-9]{39,59}\b",  # Bech32 SegWit
        ]

        # Ethereum pattern
        eth_pattern = r"\b0x[a-fA-F0-9]{40}\b"

        # USDT (ERC-20) - same as Ethereum
        usdt_pattern = r"\b0x[a-fA-F0-9]{40}\b"

        # Extract Bitcoin addresses
        for pattern in btc_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                address = match.group()
                if address not in seen:
                    seen.add(address)
                    wallets.append(
                        CryptoWallet(address=address, currency="BTC", confidence=0.90)
                    )

        # Extract Ethereum addresses
        for match in re.finditer(eth_pattern, text):
            address = match.group()
            if address not in seen:
                seen.add(address)
                wallets.append(
                    CryptoWallet(address=address, currency="ETH", confidence=0.90)
                )

        # Check for USDT mentions nearby
        if any(keyword in text.lower() for keyword in ["usdt", "tether", "usd tether"]):
            for match in re.finditer(usdt_pattern, text):
                address = match.group()
                if address not in seen:
                    seen.add(address)
                    # Check context to determine if it's USDT or ETH
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end].lower()

                    if "usdt" in context or "tether" in context:
                        wallets.append(
                            CryptoWallet(
                                address=address, currency="USDT", confidence=0.85
                            )
                        )

        return wallets

    def extract_all(self, text: str) -> ExtractedIntelligence:
        """Extract all intelligence types with validation."""
        return ExtractedIntelligence(
            bank_accounts=self.extract_bank_accounts(text),
            upi_ids=self.extract_upi_ids(text),
            phone_numbers=self.extract_phone_numbers(text),
            urls=self.extract_urls(text),
            emails=self.extract_emails(text),
            crypto_wallets=self.extract_crypto_wallets(text),
            scammer_identity=self.extract_identity(text),
        )

    def get_intel_summary(self, intel: ExtractedIntelligence) -> Dict:
        """Generate summary of extracted intelligence."""
        return {
            "total_items": (
                len(intel.bank_accounts)
                + len(intel.upi_ids)
                + len(intel.phone_numbers)
                + len(intel.urls)
                + len(intel.emails)
                + len(intel.crypto_wallets)
            ),
            "bank_accounts": len(intel.bank_accounts),
            "upi_ids": len(intel.upi_ids),
            "phone_numbers": len(intel.phone_numbers),
            "urls": len(intel.urls),
            "emails": len(intel.emails),
            "crypto_wallets": len(intel.crypto_wallets),
            "has_identity": intel.scammer_identity is not None,
            "average_confidence": self._calculate_avg_confidence(intel),
        }

    @staticmethod
    def _calculate_avg_confidence(intel: ExtractedIntelligence) -> float:
        """Calculate average confidence score."""
        confidences = []

        for acc in intel.bank_accounts:
            confidences.append(acc.confidence)
        for upi in intel.upi_ids:
            confidences.append(upi.confidence)
        for phone in intel.phone_numbers:
            confidences.append(phone.confidence)
        for email in intel.emails:
            confidences.append(email.confidence)
        for wallet in intel.crypto_wallets:
            confidences.append(wallet.confidence)

        if not confidences:
            return 0.0

        return sum(confidences) / len(confidences)


# Backwards compatibility
ExtractionEngine = AdvancedExtractionEngine
