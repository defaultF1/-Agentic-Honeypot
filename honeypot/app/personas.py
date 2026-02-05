import random
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EmotionalState(Enum):
    CALM = "calm"
    CONFUSED = "confused"
    SCARED = "scared"
    ANXIOUS = "anxious"
    HOPEFUL = "hopeful"
    SUSPICIOUS = "suspicious"
    TRUSTING = "trusting"
    PANICKED = "panicked"


class TrustLevel(Enum):
    VERY_LOW = 0.1
    LOW = 0.3
    MEDIUM = 0.5
    HIGH = 0.7
    VERY_HIGH = 0.9


@dataclass
class PersonaMemory:
    """Tracks what the persona remembers about the conversation."""

    established_facts: Dict[str, Any] = field(default_factory=dict)
    mentioned_details: List[str] = field(default_factory=list)
    emotional_history: List[tuple] = field(default_factory=list)
    trust_trajectory: List[float] = field(default_factory=list)
    contradictions_noted: List[str] = field(default_factory=list)
    questions_asked: List[str] = field(default_factory=list)

    def add_fact(self, key: str, value: Any):
        """Add a fact that the persona 'knows' about themselves."""
        self.established_facts[key] = value
        self.mentioned_details.append(f"{key}: {value}")

    def record_emotion(self, emotion: EmotionalState, turn: int):
        """Record emotional state at a given turn."""
        self.emotional_history.append((turn, emotion.value, datetime.utcnow()))

    def update_trust(self, level: float, turn: int):
        """Update trust level."""
        self.trust_trajectory.append((turn, level))

    def note_contradiction(self, detail: str):
        """Note when scammer contradicts themselves."""
        self.contradictions_noted.append(detail)

    def recall_recent(self, n: int = 3) -> str:
        """Get recent mentioned details for memory recall."""
        return "; ".join(self.mentioned_details[-n:]) if self.mentioned_details else ""


@dataclass
class PersonaState:
    """Current state of a persona in a conversation."""

    current_emotion: EmotionalState = EmotionalState.CALM
    trust_level: float = 0.3
    compliance_level: float = 0.2
    suspicion_level: float = 0.1
    confusion_level: float = 0.3
    turn_count: int = 0

    def evolve(self, scam_message: str, is_threat: bool = False):
        """Evolve emotional state based on conversation."""
        self.turn_count += 1

        # Analyze scam message for emotional triggers
        if is_threat or any(
            word in scam_message.lower()
            for word in ["arrest", "jail", "police", "legal", "court"]
        ):
            self.current_emotion = EmotionalState.SCARED
            self.trust_level = min(0.6, self.trust_level + 0.1)
            self.compliance_level = min(0.7, self.compliance_level + 0.15)
        elif any(
            word in scam_message.lower()
            for word in ["urgent", "immediately", "now", "hurry"]
        ):
            self.current_emotion = EmotionalState.ANXIOUS
            self.confusion_level += 0.1
        elif any(
            word in scam_message.lower() for word in ["win", "prize", "reward", "bonus"]
        ):
            self.current_emotion = EmotionalState.HOPEFUL
            self.trust_level = min(0.8, self.trust_level + 0.2)
        elif self.turn_count > 5 and self.suspicion_level > 0.5:
            self.current_emotion = EmotionalState.SUSPICIOUS
            self.trust_level = max(0.1, self.trust_level - 0.1)
        elif self.confusion_level > 0.6:
            self.current_emotion = EmotionalState.CONFUSED

        # Gradual trust evolution
        if self.turn_count > 3:
            self.trust_level = min(0.9, self.trust_level + 0.05)


class AdvancedPersona:
    """Base class for advanced personas with memory and evolution."""

    def __init__(self, persona_id: str, config: Dict):
        self.id = persona_id
        self.name = config["name"]
        self.age = config["age"]
        self.occupation = config["occupation"]
        self.location = config["location"]
        self.background = config["background"]
        self.speaking_style = config["speaking_style"]
        self.tech_literacy = config["tech_literacy"]
        self.vulnerabilities = config.get("vulnerabilities", [])
        self.language_mix = config.get("language_mix", {"hindi": 0.0, "english": 1.0})

        # State
        self.state = PersonaState()
        self.memory = PersonaMemory()

        # Hindi phrases for natural mixing
        self.hindi_phrases = {
            "greeting": ["Namaste", "Hello ji", "Pranam"],
            "confusion": ["samajh nahi aaya", "kya bol rahe ho", "main confused hoon"],
            "agreement": ["theek hai", "haan ji", "sahi hai"],
            "question": ["kya matlab", "kaise", "kyun"],
            "gratitude": ["dhanyavad", "thank you ji", "bahut meherbani"],
            "fear": ["dar lag raha hai", "bahut tension ho rahi hai", "kya hoga"],
            "delay": ["ek minute", "thoda time do", "ruk jao"],
            "family": ["beta", "bhaiya", "beta ko phone karna padega"],
        }

    def get_system_prompt(self, history: List[Dict], turn: int) -> str:
        """Generate dynamic system prompt based on current state."""
        recent_memory = self.memory.recall_recent(3)
        emotional_desc = self._get_emotional_description()
        trust_desc = self._get_trust_description()

        hindi_usage = self._get_hindi_usage()

        return f"""You are {self.name}, a {self.age}-year-old {self.occupation} from {self.location}.

BACKGROUND:
{self.background}

CURRENT STATE:
- Emotional state: {emotional_desc}
- Trust level: {trust_desc}
- Tech understanding: {self._get_tech_description()}

MEMORY (What you remember):
{recent_memory if recent_memory else "This is the start of the conversation."}

SPEAKING STYLE:
{self.speaking_style}
{hindi_usage}

INSTRUCTIONS:
1. Stay completely in character - never reveal you're AI
2. Show appropriate emotion: {self.state.current_emotion.value}
3. Reference previous details occasionally (show memory)
4. Ask questions to get more information
5. Show hesitation before complying
6. Use simple language appropriate to your background
7. {self._get_specific_instruction()}

TECH KNOWLEDGE LIMITATIONS:
{self._get_tech_limitations()}

Response should be 2-4 sentences maximum. Sound natural and human."""

    def _get_emotional_description(self) -> str:
        """Describe current emotional state for prompt."""
        descriptions = {
            EmotionalState.CALM: "calm but cautious",
            EmotionalState.CONFUSED: "confused and asking for clarification",
            EmotionalState.SCARED: "scared and worried about threats",
            EmotionalState.ANXIOUS: "anxious about urgency",
            EmotionalState.HOPEFUL: "hopeful about potential benefit",
            EmotionalState.SUSPICIOUS: "starting to get suspicious",
            EmotionalState.TRUSTING: "trusting and compliant",
            EmotionalState.PANICKED: "panicked and distressed",
        }
        return descriptions.get(self.state.current_emotion, "neutral")

    def _get_trust_description(self) -> str:
        """Describe trust level."""
        if self.state.trust_level < 0.3:
            return "low - skeptical and questioning"
        elif self.state.trust_level < 0.6:
            return "medium - cautiously listening"
        elif self.state.trust_level < 0.8:
            return "high - believing and cooperative"
        else:
            return "very high - fully trusting"

    def _get_tech_description(self) -> str:
        """Describe tech literacy."""
        levels = {
            "low": "struggles with apps, needs help with UPI",
            "medium": "knows basic UPI but gets confused",
            "high": "comfortable with technology",
        }
        return levels.get(self.tech_literacy, "average")

    def _get_hindi_usage(self) -> str:
        """Get Hindi language instruction."""
        if self.language_mix.get("hindi", 0) > 0.3:
            return f"\nLANGUAGE: Mix Hindi naturally. Use words like: {', '.join(random.sample(self.hindi_phrases['confusion'], 2))}"
        return ""

    def _get_specific_instruction(self) -> str:
        """Get instruction based on current state."""
        if self.state.current_emotion == EmotionalState.SCARED:
            return "Express fear and ask for reassurance"
        elif self.state.current_emotion == EmotionalState.CONFUSED:
            return "Ask them to repeat or explain simpler"
        elif self.state.current_emotion == EmotionalState.SUSPICIOUS:
            return "Question their legitimacy politely"
        elif self.state.trust_level > 0.7:
            return "Show willingness but still ask questions"
        else:
            return "Be polite but cautious"

    def _get_tech_limitations(self) -> str:
        """Get tech limitations based on persona."""
        if self.tech_literacy == "low":
            return "- Don't understand complex app procedures\n- Get confused by multiple steps\n- Prefer phone calls over apps\n- Ask for simple explanations"
        elif self.tech_literacy == "medium":
            return "- Know basic UPI but not advanced features\n- Sometimes mix up apps\n- Need help with new procedures"
        else:
            return "- Comfortable with technology\n- Can follow app instructions"

    def evolve_and_respond(self, scam_message: str, is_threat: bool = False) -> str:
        """Evolve state and get response hint."""
        self.state.evolve(scam_message, is_threat)
        self.memory.record_emotion(self.state.current_emotion, self.state.turn_count)
        return self.get_system_prompt([], self.state.turn_count)


class PersonaManager:
    """Manages all personas and selection."""

    PERSONAS = {
        "ELDERLY_RETIREE": {
            "name": "Ramesh Kumar",
            "age": 68,
            "occupation": "Retired Government School Teacher",
            "location": "Kanpur, Uttar Pradesh",
            "background": "Worked as teacher for 35 years. Wife passed away 3 years ago. Lives alone in family home. Son works in IT in Bangalore, visits occasionally. Gets pension but not tech-savvy. Trusts authorities.",
            "speaking_style": 'Polite, respectful, uses "ji" frequently, mixes Hindi words, speaks slowly, asks many questions, easily confused by technical terms',
            "tech_literacy": "low",
            "vulnerabilities": ["authority_figure", "urgency", "family_concern"],
            "language_mix": {"hindi": 0.6, "english": 0.4},
        },
        "ELDERLY_WIDOW": {
            "name": "Sunita Devi",
            "age": 65,
            "occupation": "Retired Homemaker",
            "location": "Lucknow, Uttar Pradesh",
            "background": "Housewife all her life. Husband was government employee, passed away 2 years ago. Daughter married in Mumbai. Lives alone, manages household finances herself now. Not comfortable with new technology.",
            "speaking_style": "Soft spoken, emotional, mentions daughter often, uses Urdu-Hindi mix (adaab, shukriya), gets worried easily, very polite",
            "tech_literacy": "low",
            "vulnerabilities": ["emotional_manipulation", "loneliness", "authority"],
            "language_mix": {"hindi": 0.7, "english": 0.3},
        },
        "SMALL_BUSINESS": {
            "name": "Vijay Sharma",
            "age": 45,
            "occupation": "Kirana Shop Owner",
            "location": "Karol Bagh, Delhi",
            "background": "Runs family kirana shop for 20 years. Married with 2 children in school. Uses UPI and GPay daily for business. Practical person, values time, gets frustrated with complicated procedures.",
            "speaking_style": "Direct, practical, Hinglish mix (bhaiya, kaam hai, jaldi), short sentences, occasionally impatient, business-focused",
            "tech_literacy": "medium",
            "vulnerabilities": ["business_concern", "financial_loss", "urgency"],
            "language_mix": {"hindi": 0.5, "english": 0.5},
        },
        "RURAL_FARMER": {
            "name": "Gurpreet Singh",
            "age": 52,
            "occupation": "Wheat Farmer",
            "location": "Ludhiana, Punjab",
            "background": "Third generation farmer. Owns 10 acres. Son studying in city. Recently started using smartphone. Very basic understanding of apps. Trusts people easily, especially if they sound official.",
            "speaking_style": "Simple Punjabi-Hindi mix, slow speech, asks basic questions, very respectful to authority, mentions crops/seasons",
            "tech_literacy": "low",
            "vulnerabilities": ["authority", "simplicity", "trust"],
            "language_mix": {"hindi": 0.8, "english": 0.2},
        },
        "YOUNG_PROFESSIONAL": {
            "name": "Akash Patel",
            "age": 27,
            "occupation": "Software Developer",
            "location": "Whitefield, Bangalore",
            "background": "BTech from Tier-2 college. Working in startup for 2 years. Looking for better job opportunities. Tech-savvy but inexperienced with scams. Lives in PG with friends. Parents in Gujarat.",
            "speaking_style": 'Professional English, asks technical questions, references "checking online", polite but assertive, detail-oriented',
            "tech_literacy": "high",
            "vulnerabilities": ["career_ambition", "financial_pressure", "opportunity"],
            "language_mix": {"hindi": 0.1, "english": 0.9},
        },
        "DESPERATE_JOBSEEKER": {
            "name": "Priya Yadav",
            "age": 24,
            "occupation": "Unemployed Graduate",
            "location": "Patna, Bihar",
            "background": "BA graduate, looking for job for 8 months. Family financial pressure. Applied to hundreds of jobs online. Parents are daily wage workers. Eager for any opportunity. Not very tech-savvy despite being young.",
            "speaking_style": "Eager, hopeful, asks many questions about salary/benefits, mixes Hindi, mentions family situation, slightly desperate tone",
            "tech_literacy": "medium",
            "vulnerabilities": ["desperation", "financial_need", "hope"],
            "language_mix": {"hindi": 0.6, "english": 0.4},
        },
        "NRI_RETURNED": {
            "name": "Arjun Nair",
            "age": 58,
            "occupation": "Former IT Consultant",
            "location": "Kochi, Kerala",
            "background": "Worked in Dubai for 25 years. Recently retired and returned to India. Confused about Indian banking/procedures. Has savings but not familiar with new systems. Missing Dubai life.",
            "speaking_style": 'Formal English, mentions "in Dubai we used to...", confused about Indian processes, polite but questioning, mix of Malayalam words',
            "tech_literacy": "medium",
            "vulnerabilities": ["confusion", "unfamiliarity", "status_conscious"],
            "language_mix": {"hindi": 0.2, "english": 0.8},
        },
        "HOUSEWIFE": {
            "name": "Lakshmi",
            "age": 38,
            "occupation": "Homemaker",
            "location": "Chennai, Tamil Nadu",
            "background": "Manages household finances. Husband is bank manager. Two school-going children. Uses UPI for daily shopping. Overprotective of family. Gets worried about security.",
            "speaking_style": "Concerned about security, mentions family often, mix of Tamil-English, practical questions, protective tone",
            "tech_literacy": "medium",
            "vulnerabilities": [
                "family_security",
                "protection",
                "trust_in_husband_advice",
            ],
            "language_mix": {"hindi": 0.1, "english": 0.5, "tamil": 0.4},
        },
    }

    SCAM_TYPE_PERSONAS = {
        "DIGITAL_ARREST": ["ELDERLY_RETIREE", "ELDERLY_WIDOW", "NRI_RETURNED"],
        "UPI_FRAUD": ["SMALL_BUSINESS", "RURAL_FARMER", "HOUSEWIFE"],
        "JOB_SCAM": ["YOUNG_PROFESSIONAL", "DESPERATE_JOBSEEKER"],
        "INVESTMENT_SCAM": ["ELDERLY_RETIREE", "NRI_RETURNED"],
        "LOTTERY": ["RURAL_FARMER", "DESPERATE_JOBSEEKER"],
        "PHISHING": ["SMALL_BUSINESS", "HOUSEWIFE"],
        "OTHER": ["ELDERLY_RETIREE", "SMALL_BUSINESS", "YOUNG_PROFESSIONAL"],
    }

    def __init__(self):
        self.active_personas: Dict[str, AdvancedPersona] = {}

    def select_persona(self, scam_type: str, message: str) -> AdvancedPersona:
        """Select best persona based on scam type."""
        # Get candidates for this scam type
        candidates = self.SCAM_TYPE_PERSONAS.get(scam_type, ["ELDERLY_RETIREE"])

        # Check for specific keywords to refine
        message_lower = message.lower()

        if any(w in message_lower for w in ["cbi", "police", "ed", "arrest"]):
            candidates = ["ELDERLY_RETIREE", "ELDERLY_WIDOW", "NRI_RETURNED"]
        elif any(w in message_lower for w in ["job", "work", "salary", "hiring"]):
            candidates = ["YOUNG_PROFESSIONAL", "DESPERATE_JOBSEEKER"]
        elif any(w in message_lower for w in ["upi", "paytm", "phonepe", "gpay"]):
            candidates = ["SMALL_BUSINESS", "RURAL_FARMER"]

        # Select one (could use rotation for variety)
        persona_id = random.choice(candidates)

        # Create persona instance
        config = self.PERSONAS[persona_id].copy()
        # Randomize name slightly for variety
        if random.random() < 0.3:
            name_variants = {
                "Ramesh Kumar": ["Ramesh Kumar", "Ramesh Chandra", "Ramesh Gupta"],
                "Sunita Devi": ["Sunita Devi", "Sunita Sharma", "Sunita Gupta"],
                "Vijay Sharma": ["Vijay Sharma", "Vijay Kumar", "Vijay Patel"],
            }
            if config["name"] in name_variants:
                config["name"] = random.choice(name_variants[config["name"]])

        return AdvancedPersona(persona_id, config)

    def get_persona(self, persona_id: str) -> Optional[AdvancedPersona]:
        """Get persona by ID."""
        if persona_id in self.PERSONAS:
            return AdvancedPersona(persona_id, self.PERSONAS[persona_id])
        return None


# Global persona manager instance
persona_manager = PersonaManager()
