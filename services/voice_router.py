"""
🎙️ Intelligent Voice Router
Context-aware voice selection for B2B Sales and Real Estate AI agents

Features:
- Automatic voice selection based on language detection
- Context-aware routing (B2B sales vs real estate)
- Gender-based voice preferences per use case
- Voice continuity management (prevents unnecessary switching)
- Performance optimized voice configurations
"""

import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class VoiceSelection:
    """Result of voice selection with context"""
    voice_id: str
    language: str
    gender: str
    confidence: float
    switched: bool
    voice_name: str
    characteristics: str


class IntelligentVoiceRouter:
    """
    Smart voice routing system for multi-language phone AI
    Automatically selects optimal voice based on language, context, and preferences
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Comprehensive voice mapping with characteristics
        self.voice_catalog = {
            "hindi": {
                "description": "Premium Hindi voices for natural Indian conversations",
                "voices": {
                    "female": {
                        "id": "hi-IN-ayushi",
                        "name": "Ayushi",
                        "characteristics": "Warm, professional, clear pronunciation, friendly tone",
                        "best_for": ["b2b_sales", "customer_service", "support"],
                        "settings": {
                            "min_buffer_size": 30,  # Faster response for Hindi
                            "max_buffer_delay_ms": 150,
                            "style": "Conversational"
                        }
                    },
                    "male": {
                        "id": "hi-IN-kabir",
                        "name": "Kabir",
                        "characteristics": "Confident, authoritative, business-friendly, trustworthy",
                        "best_for": ["real_estate", "consulting", "financial_services"],
                        "settings": {
                            "min_buffer_size": 30,
                            "max_buffer_delay_ms": 150,
                            "style": "Professional"
                        }
                    }
                },
                "locale": "hi-IN"
            },
            "english": {
                "description": "Premium English (India) voices for business calls",
                "voices": {
                    "female": {
                        "id": "en-IN-priya",
                        "name": "Priya",
                        "characteristics": "Professional, friendly, tech-savvy, modern accent",
                        "best_for": ["b2b_sales", "tech_support", "api_demos"],
                        "settings": {
                            "min_buffer_size": 40,  # Standard for English
                            "max_buffer_delay_ms": 200,
                            "style": "Conversational"
                        }
                    },
                    "male": {
                        "id": "en-IN-rohan",
                        "name": "Rohan",
                        "characteristics": "Confident, consultative, sales-oriented, articulate",
                        "best_for": ["real_estate", "b2b_sales", "consulting"],
                        "settings": {
                            "min_buffer_size": 40,
                            "max_buffer_delay_ms": 200,
                            "style": "Professional"
                        }
                    }
                },
                "alternate_voices": {
                    "female": ["en-IN-alia", "en-IN-priya"],
                    "male": ["en-IN-eashwar", "en-IN-rohan"]
                },
                "locale": "en-IN"
            },
            "telugu": {
                "description": "Native Telugu voices for regional customer engagement",
                "voices": {
                    "female": {
                        "id": "te-IN-shruti",
                        "name": "Shruti",
                        "characteristics": "Warm, trustworthy, local accent, approachable",
                        "best_for": ["real_estate", "local_business", "community"],
                        "settings": {
                            "min_buffer_size": 35,
                            "max_buffer_delay_ms": 175,
                            "style": "Friendly"
                        }
                    },
                    "male": {
                        "id": "te-IN-mohan",
                        "name": "Mohan",
                        "characteristics": "Authoritative, knowledgeable, regional expert, reliable",
                        "best_for": ["real_estate", "consulting", "government"],
                        "settings": {
                            "min_buffer_size": 35,
                            "max_buffer_delay_ms": 175,
                            "style": "Professional"
                        }
                    }
                },
                "locale": "te-IN"
            }
        }
        
        # Context-specific voice preferences
        self.context_preferences = {
            "b2b_sales": {
                "default_gender": "female",
                "preferred_style": "Conversational",
                "voice_priorities": {
                    "hindi": "hi-IN-ayushi",    # Ayushi for B2B sales
                    "english": "en-IN-priya",   # Priya for tech/API sales
                    "telugu": "te-IN-shruti"    # Shruti for regional B2B
                },
                "characteristics_priority": ["professional", "friendly", "tech-savvy"]
            },
            "real_estate": {
                "default_gender": "male",
                "preferred_style": "Professional",
                "voice_priorities": {
                    "hindi": "hi-IN-kabir",     # Kabir for property consulting
                    "english": "en-IN-rohan",   # Rohan for real estate
                    "telugu": "te-IN-mohan"     # Mohan for regional properties
                },
                "characteristics_priority": ["authoritative", "trustworthy", "knowledgeable"]
            },
            "customer_service": {
                "default_gender": "female",
                "preferred_style": "Friendly",
                "voice_priorities": {
                    "hindi": "hi-IN-ayushi",
                    "english": "en-IN-priya",
                    "telugu": "te-IN-shruti"
                },
                "characteristics_priority": ["warm", "helpful", "patient"]
            }
        }
        
        # Voice continuity settings
        self.continuity_settings = {
            "min_confidence_for_switch": 0.90,  # High bar for switching voices
            "max_switches_per_call": 2,         # Prevent excessive switching
            "switch_cooldown_seconds": 30       # Minimum time between switches
        }
        
        self.logger.info("🎙️ Intelligent Voice Router initialized")
    
    def select_voice(
        self,
        language: str,
        call_context: str,
        language_confidence: float = 1.0,
        previous_voice_id: Optional[str] = None,
        customer_preference: Optional[Dict[str, str]] = None,
        call_metadata: Optional[Dict[str, Any]] = None
    ) -> VoiceSelection:
        """
        Select optimal voice based on multiple factors
        
        Args:
            language: Detected language ('hindi', 'english', 'telugu')
            call_context: Context ('b2b_sales', 'real_estate', 'customer_service')
            language_confidence: Confidence in language detection (0-1)
            previous_voice_id: Currently active voice (for continuity)
            customer_preference: Customer's explicit preferences
            call_metadata: Additional context (e.g., customer location, industry)
            
        Returns:
            VoiceSelection with complete voice configuration
        """
        # Handle customer preference override
        if customer_preference:
            return self._apply_customer_preference(
                customer_preference,
                language,
                call_context
            )
        
        # Get context preferences
        context_pref = self.context_preferences.get(
            call_context,
            self.context_preferences["b2b_sales"]
        )
        
        # Determine gender
        gender = context_pref["default_gender"]
        
        # Get voice configuration
        voice_config = self.voice_catalog[language]["voices"][gender]
        selected_voice_id = voice_config["id"]
        
        # Voice continuity check
        switched = False
        if previous_voice_id and previous_voice_id != selected_voice_id:
            # Should we switch?
            if language_confidence < self.continuity_settings["min_confidence_for_switch"]:
                # Keep previous voice for consistency
                selected_voice_id = previous_voice_id
                voice_config = self._get_voice_config_by_id(previous_voice_id)
                self.logger.debug(
                    f"⚠️ Maintaining voice continuity: confidence {language_confidence:.2%} "
                    f"below threshold {self.continuity_settings['min_confidence_for_switch']:.2%}"
                )
            else:
                switched = True
                self.logger.info(
                    f"🔄 Voice switch: {previous_voice_id} → {selected_voice_id} "
                    f"(confidence: {language_confidence:.2%})"
                )
        
        return VoiceSelection(
            voice_id=selected_voice_id,
            language=language,
            gender=gender,
            confidence=language_confidence,
            switched=switched,
            voice_name=voice_config["name"],
            characteristics=voice_config["characteristics"]
        )
    
    def get_voice_settings(
        self,
        language: str,
        gender: str = "female"
    ) -> Dict[str, Any]:
        """
        Get optimized voice generation settings for a language
        
        Returns:
            Settings dict with min_buffer_size, max_buffer_delay_ms, style
        """
        if language not in self.voice_catalog:
            language = "english"
        
        voice_data = self.voice_catalog[language]["voices"].get(
            gender,
            self.voice_catalog[language]["voices"]["female"]
        )
        
        return voice_data["settings"].copy()
    
    def get_voice_id_for_context(
        self,
        language: str,
        call_context: str
    ) -> str:
        """Quick voice ID lookup for a specific context"""
        context_pref = self.context_preferences.get(
            call_context,
            self.context_preferences["b2b_sales"]
        )
        
        return context_pref["voice_priorities"].get(
            language,
            "en-IN-priya"  # Default fallback
        )
    
    def _apply_customer_preference(
        self,
        preference: Dict[str, str],
        detected_language: str,
        call_context: str
    ) -> VoiceSelection:
        """Apply customer's explicit voice preferences"""
        pref_language = preference.get("language", detected_language)
        pref_gender = preference.get("gender", "female")
        
        voice_config = self.voice_catalog[pref_language]["voices"][pref_gender]
        
        self.logger.info(
            f"👤 Applying customer preference: "
            f"{pref_language}/{pref_gender} ({voice_config['name']})"
        )
        
        return VoiceSelection(
            voice_id=voice_config["id"],
            language=pref_language,
            gender=pref_gender,
            confidence=1.0,  # Customer preference is always confident
            switched=True,
            voice_name=voice_config["name"],
            characteristics=voice_config["characteristics"]
        )
    
    def _get_voice_config_by_id(self, voice_id: str) -> Dict[str, Any]:
        """Reverse lookup voice configuration by voice ID"""
        for lang_data in self.voice_catalog.values():
            for gender, voice_config in lang_data["voices"].items():
                if voice_config["id"] == voice_id:
                    return voice_config
        
        # Fallback to default
        return self.voice_catalog["english"]["voices"]["female"]
    
    def get_available_voices(self, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all available voices, optionally filtered by language
        Useful for UI/configuration purposes
        """
        if language:
            return {
                language: self.voice_catalog.get(language, {})
            }
        
        return self.voice_catalog.copy()
    
    def validate_voice_id(self, voice_id: str) -> bool:
        """Check if a voice ID is valid"""
        for lang_data in self.voice_catalog.values():
            for voice_config in lang_data["voices"].values():
                if voice_config["id"] == voice_id:
                    return True
        return False
    
    def get_copilot_instructions(self) -> str:
        """
        Generate comprehensive instructions for GitHub Copilot integration
        """
        return """
# 🎙️ Intelligent Voice Selection System - GitHub Copilot Guide

## Automatic Voice Routing Pattern

When implementing voice generation, use this intelligent routing:

```python
from services.language_detector import AdvancedLanguageDetector
from services.voice_router import IntelligentVoiceRouter

# Initialize
detector = AdvancedLanguageDetector()
router = IntelligentVoiceRouter()

# In your conversation handler
async def process_customer_speech(call_sid: str, speech: str, call_type: str):
    # Step 1: Detect language with confidence
    lang_result = detector.detect_language(speech)
    
    # Step 2: Select optimal voice
    voice_selection = router.select_voice(
        language=lang_result.language,
        call_context=call_type,  # 'b2b_sales' or 'real_estate'
        language_confidence=lang_result.confidence,
        previous_voice_id=get_current_voice(call_sid)
    )
    
    # Step 3: Generate AI response
    ai_text = await generate_ai_response(speech, call_sid)
    
    # Step 4: Get optimized voice settings
    voice_settings = router.get_voice_settings(
        voice_selection.language,
        voice_selection.gender
    )
    
    # Step 5: Synthesize with Murf
    audio = await murf_service.generate_streaming_audio_optimized(
        text=ai_text,
        voice_id=voice_selection.voice_id,
        language=voice_selection.language,
        **voice_settings
    )
    
    return audio
```

## Voice Selection Rules

### B2B Sales Calls
- Hindi: Ayushi (hi-IN-ayushi) - Professional, friendly
- English: Priya (en-IN-priya) - Tech-savvy, modern
- Telugu: Shruti (te-IN-shruti) - Warm, approachable
- Default Gender: Female

### Real Estate Calls  
- Hindi: Kabir (hi-IN-kabir) - Authoritative, trustworthy
- English: Rohan (en-IN-rohan) - Consultative, confident
- Telugu: Mohan (te-IN-mohan) - Regional expert, reliable
- Default Gender: Male

## Voice Continuity
- Only switch voices when confidence > 90%
- Maximum 2 switches per call
- 30-second cooldown between switches
- Log all switches for analytics

## Performance Optimization
Language-specific buffer settings:
- Hindi: min_buffer_size=30, max_delay=150ms
- English: min_buffer_size=40, max_delay=200ms
- Telugu: min_buffer_size=35, max_delay=175ms
"""


# Testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    router = IntelligentVoiceRouter()
    
    print("\n🧪 Voice Router Tests:\n")
    
    # Test B2B Sales
    print("B2B Sales Context:")
    for lang in ["english", "hindi", "telugu"]:
        selection = router.select_voice(lang, "b2b_sales", 0.95)
        print(f"  {lang.upper()}: {selection.voice_name} ({selection.voice_id})")
        print(f"    → {selection.characteristics}\n")
    
    # Test Real Estate
    print("\nReal Estate Context:")
    for lang in ["english", "hindi", "telugu"]:
        selection = router.select_voice(lang, "real_estate", 0.95)
        print(f"  {lang.upper()}: {selection.voice_name} ({selection.voice_id})")
        print(f"    → {selection.characteristics}\n")
    
    # Test voice continuity
    print("\nVoice Continuity Test:")
    prev_voice = "en-IN-priya"
    
    # Low confidence - should maintain
    selection1 = router.select_voice(
        "hindi", "b2b_sales", 0.70, previous_voice_id=prev_voice
    )
    print(f"Low confidence (70%): Switched = {selection1.switched}")
    
    # High confidence - should switch
    selection2 = router.select_voice(
        "hindi", "b2b_sales", 0.95, previous_voice_id=prev_voice
    )
    print(f"High confidence (95%): Switched = {selection2.switched}")
