# GitHub Copilot Instructions for Lightning-Fast B2B Agent Solution

## Project Context

This is a B2B AI phone agent system that needs LIGHTNING-FAST performance:

- Target: <500ms TTFB (Time To First Byte)
- Target: <1.5s total response time
- NO preprocessing or caching overhead
- Direct WebSocket streaming only

## Architecture

### Core Components

1. **services/lightning_murf.py** - Ultra-fast Murf WebSocket streaming

   - Direct streaming with connection pooling
   - Phone-optimized audio (8kHz mono WAV)
   - Target: <500ms TTFB, <1.5s total

2. **services/lightning_language_detector.py** - <1ms language detection

   - Regex-based pattern matching (NO AI)
   - Supports: Hindi, Telugu, English
   - Instant voice selection

3. **main.py** - FastAPI application
   - NO preprocessing on startup
   - Direct streaming endpoints
   - Real-time phone call handling via Twilio

## Critical Rules

### ❌ NEVER Suggest These

1. **NO preprocessing or caching systems**

   - No pre-generation of responses
   - No response caching
   - No prediction systems
   - No "smart" optimization that adds latency

2. **NO additional abstraction layers**

   - Keep code direct and simple
   - No unnecessary wrappers
   - No complex class hierarchies

3. **NO AI for simple tasks**

   - Use regex for language detection
   - Don't use LLM for classification
   - Keep fast operations fast

4. **NO duplicate implementations**
   - Don't create similar services with different names
   - Consolidate functionality
   - One service per responsibility

### ✅ ALWAYS Suggest These

1. **Direct streaming everywhere**

   - Stream from WebSocket to client
   - No intermediate buffering
   - Async/await for concurrency

2. **Connection pooling**

   - Reuse WebSocket connections
   - Max 3-5 connections
   - Health checks with ping/pong

3. **Phone optimization**

   - 8kHz sample rate
   - Mono channel
   - Minimal WAV headers
   - Small buffer sizes (20-25 bytes)

4. **Concurrent processing**

   - AI + voice generation in parallel
   - Non-blocking operations
   - asyncio.create_task() for parallelism

5. **Simple error handling**
   - Fast fallbacks
   - Clear error messages
   - No retry loops that add latency

## Code Patterns

### ✅ Good: Direct Streaming

```python
async def process_speech(text: str):
    # 1. Detect language (fast - <1ms)
    lang = detector.detect_lightning_fast(text)

    # 2. Get AI response and generate audio concurrently
    ai_task = asyncio.create_task(get_ai_response(text))
    ai_response = await ai_task

    # 3. Stream audio directly
    audio, metrics = await lightning_murf.generate_phone_optimized_audio(
        ai_response, lang.voice_id
    )

    return audio  # Total time: <1.5s
```

### ❌ Bad: Preprocessing Overhead

```python
# DON'T DO THIS - adds 94s startup time
async def startup():
    optimizer = PerformanceOptimizer()
    await optimizer.pre_generate_responses()  # ❌ NO!
    await optimizer.warm_cache()  # ❌ NO!
```

### ✅ Good: Connection Pooling

```python
async def get_connection(voice_id: str):
    # Reuse existing connection
    if voice_id in self.connection_pool:
        ws = self.connection_pool[voice_id]
        await ws.ping()  # Health check
        return ws, True  # Reused!

    # Create new connection only if needed
    ws = await websockets.connect(url)
    self.connection_pool[voice_id] = ws
    return ws, False
```

### ❌ Bad: Always Creating New Connections

```python
# DON'T DO THIS - 650ms per connection
async def stream_audio(text: str):
    ws = await websockets.connect(url)  # ❌ Slow!
    # ... use connection
    await ws.close()  # ❌ Wasteful!
```

### ✅ Good: Fast Language Detection

```python
def detect_language(text: str) -> str:
    # Regex pattern matching - <1ms
    if re.search(r'[\u0900-\u097F]', text):
        return 'hindi'
    elif re.search(r'[\u0C00-\u0C7F]', text):
        return 'telugu'
    else:
        return 'english'
```

### ❌ Bad: AI for Language Detection

```python
# DON'T DO THIS - adds 500-1000ms
async def detect_language(text: str):
    response = await llm.classify(text)  # ❌ Too slow!
    return response.language
```

## Performance Targets

When suggesting code, ensure it meets these targets:

| Metric             | Target | Current     | Improvement |
| ------------------ | ------ | ----------- | ----------- |
| TTFB               | <500ms | 1400-1500ms | 66% faster  |
| Connection         | <200ms | 650ms       | 92% faster  |
| Language Detection | <1ms   | N/A         | Instant     |
| Total Response     | <1.5s  | 3-4s        | 62% faster  |
| Startup Time       | <3s    | 94s         | 100% faster |

## Common Questions

### "How to make this faster?"

1. **Remove preprocessing** - No caching, no pre-generation
2. **Use connection pooling** - Reuse WebSocket connections
3. **Stream directly** - No intermediate buffering
4. **Run concurrently** - AI + voice generation in parallel
5. **Phone optimization** - 8kHz mono WAV

### "How to handle errors?"

```python
try:
    audio = await generate_audio(text, voice_id)
    return audio
except Exception as e:
    logger.error(f"❌ Generation failed: {e}")
    # Fast fallback - don't retry
    return generate_fallback_audio()
```

### "How to add new feature?"

Ask yourself:

1. Does it add latency? ❌ Don't add it
2. Can it run concurrently? ✅ Use asyncio.create_task()
3. Is it phone-optimized? ✅ 8kHz mono
4. Does it need AI? ❌ Use regex/patterns instead

## File Structure

```
services/
├── lightning_murf.py              ⚡ Use for voice generation
├── lightning_language_detector.py ⚡ Use for language detection
├── intelligent_phone_ai.py        ✅ Use for AI responses
└── azure_services.py              ✅ Use for LLM calls

DON'T use these (delete them):
├── performance_optimizer.py       ❌ Adds 94s startup delay
├── murf_optimized.py             ❌ Use lightning_murf.py instead
├── language_detector.py          ❌ Use lightning_language_detector.py
└── voice_router.py               ❌ Integrated into lightning_murf.py
```

## Testing Commands

```bash
# Test lightning streaming
uv run python -m services.lightning_murf

# Test language detection
uv run python -m services.lightning_language_detector

# Run main server
uv run main.py

# Test phone call
curl -X POST "http://localhost:8000/api/phone/call" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+916397983037", "call_type": "b2b_sales"}'
```

## Monitoring

Look for these log messages:

```
✅ Good performance:
⚡ Lightning-fast system ready - NO preprocessing!
⚡ LIGHTNING TTFB: 450ms (target: <500ms) ✅
🚀 LIGHTNING complete: 1200ms (target: <1500ms) ✅
⚡ FAST REQUEST: /api/phone/process-speech - 1420ms ✅

⚠️ Performance issues:
⚠️ SLOW REQUEST: /api/phone/process-speech - 2500ms
❌ WebSocket streaming failed
❌ No audio received from Murf
```

## Key Dependencies

```python
# Always import these
import asyncio  # For concurrent operations
import time     # For performance tracking
import logging  # For monitoring

# Core services
from services.lightning_murf import LightningMurfStreaming
from services.lightning_language_detector import LightningLanguageDetector
from services.azure_services import AzureServicesOptimized

# Twilio for phone calls
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
```

## Environment Variables

```bash
# Required
MURF_API_KEY=your_murf_api_key
AZURE_OPENAI_API_KEY=your_azure_key
AZURE_OPENAI_ENDPOINT=your_endpoint
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
WEBHOOK_BASE_URL=https://your-domain.ngrok-free.app
```

## Quick Reference

### Generate Voice (Lightning Fast)

```python
audio, metrics = await lightning_murf.generate_phone_optimized_audio(
    text="Hello! How can I help you?",
    voice_id="en-IN-priya"
)
print(f"TTFB: {metrics.ttfb_ms}ms")
print(f"Total: {metrics.total_time_ms}ms")
```

### Detect Language (Sub-millisecond)

```python
result = language_detector.detect_lightning_fast(
    "नमस्ते! मैं आपकी मदद कर सकता हूं।"
)
print(f"Language: {result.language}")
print(f"Voice: {result.voice_id}")
print(f"Confidence: {result.confidence}")
```

### Process Phone Call (End-to-End)

```python
# 1. Detect language
lang = language_detector.detect_lightning_fast(speech_text)

# 2. Generate AI response (concurrent)
ai_task = asyncio.create_task(generate_ai_response(speech_text))
ai_response = await ai_task

# 3. Generate and stream audio
audio, metrics = await lightning_murf.generate_phone_optimized_audio(
    ai_response, lang.voice_id
)

# 4. Serve to Twilio
response = VoiceResponse()
response.play(audio_url)
```

## Success Metrics

Your code is optimized when:

✅ TTFB: <500ms
✅ Total response: <1.5s
✅ Connection reuse: >80%
✅ Language detection: <1ms
✅ No preprocessing delays
✅ Concurrent operations
✅ Phone-optimized audio

## Remember

1. **Speed is the priority** - Every millisecond counts
2. **Direct streaming** - No intermediate steps
3. **Connection pooling** - Reuse everything
4. **Phone quality** - 8kHz mono is perfect
5. **No preprocessing** - Real-time only

When in doubt, choose the simplest, fastest solution! ⚡
