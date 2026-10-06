"""
🌐 Advanced Language Detection System
Multi-factor language detection with confidence scoring for Hindi, English, Telugu

Features:
- Script-based detection (Devanagari, Telugu, Latin)
- Keyword matching with weighted scoring
- Confidence thresholds per language
- Fallback mechanisms for uncertain detection
"""

import re
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LanguageResult:
    """Language detection result with confidence metrics"""
    language: str
    confidence: float
    all_scores: Dict[str, float]
    is_confident: bool
    detection_method: str  # "script", "keywords", "mixed"


class AdvancedLanguageDetector:
    """
    Advanced multi-factor language detection system
    Optimized for Indian languages in B2B sales and real estate contexts
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Language configuration with detection patterns
        self.language_patterns = {
            "hindi": {
                "script": r'[\u0900-\u097F]',  # Devanagari Unicode range
                "keywords": [
                    'है', 'हूं', 'हैं', 'था', 'थी', 'करना', 'होना', 
                    'जी', 'नहीं', 'हाँ', 'क्या', 'कैसे', 'कौन', 'कहां',
                    'के लिए', 'में', 'से', 'को', 'का', 'की', 'भी',
                    'प्रॉपर्टी', 'बिजनेस', 'सर्विस', 'कंपनी'
                ],
                "confidence_threshold": 0.75,
                "locale": "hi-IN"
            },
            "telugu": {
                "script": r'[\u0C00-\u0C7F]',  # Telugu Unicode range
                "keywords": [
                    'అవును', 'లేదు', 'ఎలా', 'ఎంటి', 'ఎవరు', 'ఎక్కడ',
                    'చేయండి', 'ఉంది', 'లేదు', 'కావాలి', 'వచ్చింది',
                    'ప్రాపర్టీ', 'బిజినెస్', 'సర్వీస్', 'కంపెనీ',
                    'హలో', 'నమస్కారం'
                ],
                "confidence_threshold": 0.75,
                "locale": "te-IN"
            },
            "english": {
                "script": r'[a-zA-Z]',  # Latin alphabet
                "keywords": [
                    'yes', 'no', 'how', 'what', 'where', 'when', 'who', 'why',
                    'can', 'will', 'would', 'should', 'please', 'thank', 'sorry',
                    'interested', 'property', 'business', 'service', 'company',
                    'api', 'voice', 'call', 'real', 'estate', 'looking'
                ],
                "confidence_threshold": 0.60,  # Lower threshold (default language)
                "locale": "en-IN"
            }
        }
        
        # Common transliterated words (English words in Hindi/Telugu context)
        self.transliterated_indicators = {
            "hindi": ['ji', 'haan', 'nahi', 'kya', 'hai'],
            "telugu": ['andi', 'avunu', 'ledu'],
            "english": ['hello', 'ok', 'okay', 'sir', 'madam']
        }
        
        self.logger.info("🌐 Advanced Language Detector initialized")
    
    def detect_language(self, text: str) -> LanguageResult:
        """
        Detect language from text using multi-factor analysis
        
        Args:
            text: Input text to analyze
            
        Returns:
            LanguageResult with detected language and confidence
        """
        if not text or not text.strip():
            return LanguageResult(
                language="english",
                confidence=0.5,
                all_scores={"english": 0.5, "hindi": 0.0, "telugu": 0.0},
                is_confident=False,
                detection_method="default"
            )
        
        scores = {}
        detection_methods = []
        
        # Calculate scores for each language
        for lang, config in self.language_patterns.items():
            score, method = self._calculate_language_score(text, lang, config)
            scores[lang] = score
            if score > 0:
                detection_methods.append(method)
        
        # Find best match
        best_lang = max(scores, key=scores.get)
        best_score = scores[best_lang]
        threshold = self.language_patterns[best_lang]["confidence_threshold"]
        
        # Determine detection method
        primary_method = "mixed" if len(set(detection_methods)) > 1 else (
            detection_methods[0] if detection_methods else "default"
        )
        
        result = LanguageResult(
            language=best_lang,
            confidence=best_score,
            all_scores=scores,
            is_confident=best_score >= threshold,
            detection_method=primary_method
        )
        
        self.logger.debug(
            f"🔍 Detected: {best_lang} "
            f"(confidence: {best_score:.2%}, method: {primary_method})"
        )
        
        return result
    
    def _calculate_language_score(
        self,
        text: str,
        language: str,
        config: Dict
    ) -> tuple[float, str]:
        """
        Calculate confidence score for a specific language
        
        Returns:
            (score, detection_method)
        """
        text_lower = text.lower().strip()
        text_length = len(text)
        
        if text_length == 0:
            return 0.0, "none"
        
        # 1. Script Detection (70% weight)
        script_pattern = config["script"]
        script_matches = len(re.findall(script_pattern, text))
        script_score = min(script_matches / text_length, 1.0)
        
        # 2. Keyword Detection (30% weight)
        keyword_matches = sum(
            1 for keyword in config["keywords"]
            if keyword.lower() in text_lower
        )
        keyword_score = min(keyword_matches / max(len(config["keywords"]) * 0.1, 1), 1.0)
        
        # 3. Transliteration Bonus
        transliteration_bonus = 0.0
        if language in self.transliterated_indicators:
            trans_matches = sum(
                1 for word in self.transliterated_indicators[language]
                if word in text_lower
            )
            if trans_matches > 0:
                transliteration_bonus = 0.1
        
        # Combined score with weights
        combined_score = (
            (script_score * 0.70) +
            (keyword_score * 0.30) +
            transliteration_bonus
        )
        
        # Determine primary detection method
        if script_score > 0.5:
            method = "script"
        elif keyword_score > 0.3:
            method = "keywords"
        else:
            method = "mixed"
        
        return min(combined_score, 1.0), method
    
    def get_locale(self, language: str) -> str:
        """Get locale code for language (e.g., 'hi-IN', 'en-IN')"""
        return self.language_patterns.get(
            language,
            self.language_patterns["english"]
        )["locale"]
    
    def should_switch_language(
        self,
        current_language: str,
        detected_language: str,
        confidence: float,
        min_confidence_for_switch: float = 0.85
    ) -> bool:
        """
        Determine if language should be switched mid-conversation
        Prevents unnecessary switching for low-confidence detections
        
        Args:
            current_language: Currently active language
            detected_language: Newly detected language
            confidence: Confidence of new detection
            min_confidence_for_switch: Minimum confidence required to switch
            
        Returns:
            True if language should be switched
        """
        if current_language == detected_language:
            return False
        
        if confidence >= min_confidence_for_switch:
            self.logger.info(
                f"🔄 Language switch recommended: "
                f"{current_language} → {detected_language} "
                f"(confidence: {confidence:.2%})"
            )
            return True
        
        self.logger.debug(
            f"⚠️ Language switch rejected: confidence {confidence:.2%} "
            f"< threshold {min_confidence_for_switch:.2%}"
        )
        return False
    
    def get_language_stats(self, texts: List[str]) -> Dict[str, any]:
        """
        Analyze multiple texts and return language distribution statistics
        Useful for analyzing conversation patterns
        """
        if not texts:
            return {}
        
        language_counts = {"hindi": 0, "english": 0, "telugu": 0}
        total_confidence = {"hindi": 0.0, "english": 0.0, "telugu": 0.0}
        
        for text in texts:
            result = self.detect_language(text)
            language_counts[result.language] += 1
            total_confidence[result.language] += result.confidence
        
        total_texts = len(texts)
        
        # Calculate percentages and averages
        stats = {}
        for lang in language_counts:
            count = language_counts[lang]
            percentage = (count / total_texts) * 100 if total_texts > 0 else 0
            avg_confidence = (
                total_confidence[lang] / count if count > 0 else 0
            )
            
            stats[lang] = {
                "count": count,
                "percentage": round(percentage, 1),
                "avg_confidence": round(avg_confidence, 2)
            }
        
        # Determine dominant language
        dominant = max(language_counts, key=language_counts.get)
        
        return {
            "total_texts": total_texts,
            "languages": stats,
            "dominant_language": dominant,
            "is_multilingual": len([c for c in language_counts.values() if c > 0]) > 1
        }


# Convenience function for quick detection
def detect_language_quick(text: str) -> str:
    """Quick language detection returning just language name"""
    detector = AdvancedLanguageDetector()
    result = detector.detect_language(text)
    return result.language


# Testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    detector = AdvancedLanguageDetector()
    
    # Test cases
    test_texts = [
        "Hello, how are you today?",
        "नमस्ते, आप कैसे हैं?",
        "హలో, మీరు ఎలా ఉన్నారు?",
        "मैं एक property देखना चाहता हूं",  # Mixed Hindi-English
        "Yes, I am interested in your service",
        "అవును, నాకు ఆసక్తి ఉంది",
        "Can you tell me more about the API?",
    ]
    
    print("\n🧪 Language Detection Tests:\n")
    for text in test_texts:
        result = detector.detect_language(text)
        print(f"Text: {text[:50]}...")
        print(f"  → {result.language.upper()} "
              f"(confidence: {result.confidence:.2%}, "
              f"method: {result.detection_method})")
        print(f"  All scores: {result.all_scores}\n")
    
    # Test statistics
    print("\n📊 Language Statistics:")
    stats = detector.get_language_stats(test_texts)
    print(f"Total texts: {stats['total_texts']}")
    print(f"Dominant: {stats['dominant_language']}")
    print(f"Multilingual: {stats['is_multilingual']}")
    for lang, data in stats['languages'].items():
        print(f"  {lang}: {data['count']} texts ({data['percentage']}%), "
              f"avg confidence: {data['avg_confidence']:.2%}")
