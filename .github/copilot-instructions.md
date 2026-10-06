# GitHub Copilot Instructions for Lightning-Fast B2B Agent Solution

## Project Context

This is a B2B AI phone agent system with LIGHTNING-FAST performance:

- Target: <500ms TTFB (Time To First Byte)
- Target: <1.5s total response time
- NO preprocessing or caching overhead
- Direct WebSocket streaming only
- ⭐ PREMIUM Hindi voices (shweta/shaan, NOT ayushi)

## Architecture

### Core Components

1. **services/ultra_fast_native_sales.py** - Ultra-fast WebSocket with premium voices

   - Direct streaming with connection pooling
   - PREMIUM Hindi: hi-IN-shweta (female), hi-IN-shaan (male)
   - Phone-optimized audio (8kHz mono WAV)
   - Target: <500ms TTFB, <1.5s total
   - Natural sales conversation with Hindi-English mixing

2. **services/lightning_language_detector.py** - <1ms language detection

   - Regex-based pattern matching (NO AI)
   - Supports: Hindi, Telugu, English
   - Instant voice selection with premium voices

3. **main.py** - FastAPI application (ONLY startup file)
   - NO preprocessing on startup
   - Direct streaming endpoints
   - Real-time phone call handling via Twilio
   - Ultra-fast speech processing

## Critical Rules

### ❌ NEVER Suggest These

1. **NO preprocessing or caching systems**

   - No pre-generation of responses
   - No response caching
   - No prediction systems
   - No "smart" optimization that adds latency

2. **NO old Hindi voice (hi-IN-ayushi)**

   - ALWAYS use hi-IN-shweta for Hindi female
   - ALWAYS use hi-IN-shaan for Hindi male
   - ayushi has poor quality - NEVER use it

3. **NO duplicate implementations**

   - Keep ONLY main.py as startup file
   - Don't create similar services with different names
   - Consolidate functionality

4. **NO AI for simple tasks**
   - Use regex for language detection
   - Don't use LLM for classification
   - Keep fast operations fast

### ✅ ALWAYS Suggest These

1. **Direct streaming everywhere**

   - Stream from WebSocket to client
   - No intermediate buffering
   - Async/await for concurrency

2. **Premium voices for Hindi**

   - hi-IN-shweta (female) - Warm, natural, expressive
   - hi-IN-shaan (male) - Confident, calm, professional
   - NEVER hi-IN-ayushi (poor quality)

3. **Connection pooling**

   - Reuse WebSocket connections
   - Max 3-5 connections
   - Health checks with ping/pong
   - Saves 650ms per call!

4. **Phone optimization**

   - 8kHz sample rate
   - Mono channel
   - Minimal WAV headers
   - Small buffer sizes (15-20 bytes for ultra-fast)

5. **Natural sales conversation**
   - Mix Hindi and English naturally (code-switching)
   - Use customer name frequently
   - Acknowledge concerns immediately
   - SPIN selling approach
   - Feel-Felt-Found for objections

## Voice Quality Guidelines

### Hindi Voices

```python
# ✅ GOOD: Premium voices
"hi-IN-shweta"  # Female - Conversational, warm, natural
"hi-IN-shaan"   # Male - Professional, confident, calm

# ❌ BAD: Poor quality voice
"hi-IN-ayushi"  # DO NOT USE - poor quality
"hi-IN-kabir"   # DO NOT USE - standard quality only
```

### English Voices

```python
# ✅ GOOD: Standard quality
"en-IN-priya"   # Female - Conversational, professional
"en-IN-rohan"   # Male - Friendly, tech-savvy
```

## Code Patterns

### ✅ Good: Ultra-Fast Speech Processing

```python
async def process_speech(call_type: str, request: Request):
    start_time = time.time()

    # 1. Instant language detection (<1ms)
    lang_result = language_detector.detect_lightning_fast(speech_result)

    # 2. Get premium sales persona
    persona = ultra_fast_sales.get_sales_persona(lang_result.language, "female")
    voice_id = persona.voice_id  # hi-IN-shweta or en-IN-priya

    # 3. Quick sentiment analysis (no AI)
    sentiment = sales_agent.analyze_customer_sentiment(speech_result)

    # 4. Generate AI response (concurrent)
    ai_task = asyncio.create_task(azure_service.generate_text_lightning(...))
    ai_response = await ai_task

    # 5. Ultra-fast audio generation
    audio_bytes, metrics = await ultra_fast_sales.generate_ultra_fast(
        text=ai_response,
        voice_id=voice_id  # Premium voice
    )

    # Total time: <1.5s
```

### ❌ Bad: Preprocessing Overhead

```python
# DON'T DO THIS - adds 91s startup time
async def startup():
    optimizer = PerformanceOptimizer()
    await optimizer.pre_generate_responses()  # ❌ NO!
    await optimizer.warm_cache()  # ❌ NO!
```

### ✅ Good: Premium Voice Selection

```python
def get_sales_persona(language: str, gender: str = "female"):
    if language == "hindi":
        if gender == "female":
            return SalesPersona(
                name="Priya Sharma",
                voice_id="hi-IN-shweta",  # ⭐ PREMIUM
                experience="12+ years B2B sales"
            )
        else:
            return SalesPersona(
                name="Rohan Patel",
                voice_id="hi-IN-shaan",  # ⭐ PREMIUM
                experience="15+ years enterprise sales"
            )
```

### ❌ Bad: Using Poor Quality Voice

```python
# DON'T DO THIS - poor quality
voice_id = "hi-IN-ayushi"  # ❌ Poor quality!
voice_id = "hi-IN-kabir"   # ❌ Standard only!
```

## Performance Targets

| Metric             | Target | Method                                |
| ------------------ | ------ | ------------------------------------- |
| TTFB               | <500ms | Ultra-fast streaming + Premium voices |
| Total Response     | <1.5s  | Concurrent processing                 |
| Connection         | <200ms | Connection pooling                    |
| Language Detection | <1ms   | Regex patterns                        |
| Startup Time       | <5s    | NO preprocessing                      |

## Common Questions

### "How to improve Hindi voice quality?"

1. **ALWAYS use premium voices**:

   - Female: `hi-IN-shweta` (NOT ayushi)
   - Male: `hi-IN-shaan` (NOT kabir)

2. **Optimize streaming config**:
   ```python
   "hi-IN-shweta": {
       "min_buffer_size": 15,      # Ultra-fast
       "max_buffer_delay_ms": 80,  # <100ms
       "sample_rate": 8000,
       "style": "Conversational"
   }
   ```

### "How to make conversation more natural?"

```python
# Natural Hindi-English code-switching
system_prompt = f"""You are {persona.name}, an experienced B2B sales expert.

Language: Mix {language.title()} and English naturally
- Use Hindi for greetings: "Namaste", "Ji haan", "Bilkul"
- Use English for technical terms: "API", "demo", "integration"
- Natural transitions: "aap dekho", "exactly", "main samjhata hun"

Personality:
- Warm and consultative
- Use customer name frequently
- Acknowledge concerns immediately
"""
```

### "How to reduce latency?"

1. **Remove preprocessing** - No caching, no pre-generation
2. **Use connection pooling** - Reuse WebSocket connections (saves 650ms)
3. **Stream directly** - No intermediate buffering
4. **Run concurrently** - AI + preparation in parallel
5. **Phone optimization** - 8kHz mono WAV, minimal buffers

## File Structure

```
services/
├── ultra_fast_native_sales.py     ⚡ Use for voice generation
├── lightning_language_detector.py ⚡ Use for language detection
├── intelligent_phone_ai.py        ✅ Use for AI responses
└── azure_services.py              ✅ Use for LLM calls

main.py                            ⚡ ONLY startup file

DON'T use these (old/duplicate):
├── performance_optimizer.py       ❌ Adds 91s startup delay
├── murf_optimized.py             ❌ Use ultra_fast_native_sales.py
├── optimized_phone_ai.py         ❌ Use ultra_fast_native_sales.py
└── voice_router.py               ❌ Integrated into ultra_fast
```

## Key Dependencies

```python
# Always import these
import asyncio  # For concurrent operations
import time     # For performance tracking
import logging  # For monitoring

# Core services
from services.ultra_fast_native_sales import UltraFastNativeSales, ExperiencedSalesAgent
from services.lightning_language_detector import LightningLanguageDetector
from services.azure_services import AzureServicesOptimized

# Twilio for phone calls
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
```

## Quick Reference

### Generate Voice (Ultra-Fast with Premium Quality)

```python
audio_bytes, metrics = await ultra_fast_sales.generate_ultra_fast(
    text="Namaste Arjun! Main aapki kaise madad kar sakti hoon?",
    voice_id="hi-IN-shweta"  # ⭐ PREMIUM Hindi
)
print(f"TTFB: {metrics['ttfb_ms']}ms")  # Target: <500ms
print(f"Total: {metrics['total_ms']}ms")  # Target: <1500ms
```

### Detect Language (Sub-millisecond)

```python
result = language_detector.detect_lightning_fast(
    "नमस्ते! मैं आपकी मदद कर सकता हूं।"
)
print(f"Language: {result.language}")  # hindi
print(f"Voice: {result.voice_id}")     # hi-IN-shweta
print(f"Time: {result.detection_time_ms}ms")  # <1ms
```

## Success Metrics

Your code is optimized when:

✅ TTFB: <500ms
✅ Total response: <1.5s
✅ Connection reuse: >80%
✅ Language detection: <1ms
✅ No preprocessing delays
✅ Concurrent operations
✅ Phone-optimized audio (8kHz mono)
✅ Premium Hindi voices (shweta/shaan)
✅ Natural sales conversation

## Remember

1. **Speed is the priority** - Every millisecond counts
2. **Direct streaming** - No intermediate steps
3. **Connection pooling** - Reuse everything (saves 650ms!)
4. **Premium voices** - ALWAYS use shweta/shaan for Hindi
5. **Phone quality** - 8kHz mono is perfect
6. **No preprocessing** - Real-time only
7. **ONLY main.py** - No duplicate startup files

When in doubt, choose the simplest, fastest solution with premium voices! ⚡
