# 🎛️ Pre-Generation Control Guide

## ❓ **Why Does Pre-Generation Run Automatically?**

Pre-generation runs at **server startup** to cache common responses, making your AI agents respond **instantly** (< 100ms) instead of waiting 1-2 seconds for voice generation on every call.

### **What It Does:**
- Generates **10-20 common responses** at startup
- Stores them as audio files ready for instant playback
- Uses **rate limiting** to avoid API errors
- Takes **60-90 seconds** (one-time cost)

### **Benefits:**
- ⚡ **First call instant** (< 100ms opening message)
- ⚡ **60%+ instant responses** for common queries
- ⚡ **Better customer experience** (no awkward pauses)
- 💰 **Reduced API costs** (fewer real-time generations)

---

## 🎛️ **3 Ways to Control Pre-Generation**

### **Option 1: Background Mode** (Default - ✅ Recommended)

Server starts **immediately**, pre-generation runs in the background.

**`.env` settings:**
```bash
ENABLE_PREGENERATION=true
PREGENERATION_MODE=background
```

**Startup logs:**
```
⚡ Server READY! Pre-generation running in background...
INFO: Application startup complete.  ← SERVER READY NOW!
✅ [1/10] Cached: Perfect! I have some properties...
✅ [2/10] Cached: Excellent choice! Let me show you...
```

**Pros:**
- ✅ Server ready in ~5 seconds
- ✅ Pre-generation completes in background (~60-90s)
- ✅ Phone calls work immediately (just slower for first few)
- ✅ Best for development and production

**Cons:**
- First 1-2 calls might be slower (1-2.5s instead of instant)

---

### **Option 2: Blocking Mode** (Wait for Pre-Generation)

Server waits for **all pre-generation** to complete before becoming ready.

**`.env` settings:**
```bash
ENABLE_PREGENERATION=true
PREGENERATION_MODE=blocking
```

**Startup logs:**
```
🚀 Pre-generating responses at startup (blocking mode)...
✅ [1/10] Cached: Perfect! I have some properties...
✅ [2/10] Cached: Excellent choice! Let me show you...
...
✅ [10/10] Cached: बढ़िया चुनाव! मैं आपको अच्छे...
⚡ Pre-generation complete! Server ready.
INFO: Application startup complete.  ← SERVER READY AFTER 60-90s
```

**Pros:**
- ✅ First call guaranteed instant
- ✅ Full optimization ready immediately
- ✅ Best for production environments

**Cons:**
- ⏳ Longer startup time (60-90 seconds)
- ⏳ Server not ready during pre-generation

---

### **Option 3: Disabled** (On-Demand Only)

Skip pre-generation entirely. Generate responses **only when needed** during calls.

**`.env` settings:**
```bash
ENABLE_PREGENERATION=false
# PREGENERATION_MODE is ignored when disabled
```

**Startup logs:**
```
⚡ Pre-generation DISABLED - using on-demand generation only
INFO: Application startup complete.  ← SERVER READY IN ~5 SECONDS
```

**Pros:**
- ✅ Fastest startup (5 seconds)
- ✅ No pre-generation delays
- ✅ Good for testing/debugging

**Cons:**
- ❌ All responses slower (1-2.5s every time)
- ❌ No instant cache hits
- ❌ Higher API costs

---

## 📊 **Comparison Table**

| Mode | Startup Time | First Call Speed | Avg Response Time | Best For |
|------|--------------|------------------|-------------------|----------|
| **Background** ✅ | ~5 seconds | 1-2.5s | 500ms (after cache builds) | **Production & Development** |
| **Blocking** | 60-90 seconds | < 100ms | 300ms | Production (when startup time acceptable) |
| **Disabled** | ~5 seconds | 1-2.5s | 1-2.5s | Testing & Debugging |

---

## 🚀 **Recommended Settings**

### **For Development:**
```bash
ENABLE_PREGENERATION=true
PREGENERATION_MODE=background
```
**Why**: Server starts fast, you can test immediately, cache builds while you work.

### **For Production:**
```bash
ENABLE_PREGENERATION=true
PREGENERATION_MODE=background  # or "blocking" if startup time isn't critical
```
**Why**: Best customer experience with instant responses.

### **For Quick Testing:**
```bash
ENABLE_PREGENERATION=false
```
**Why**: Fastest startup, no waiting, but responses are slower.

---

## 📝 **How to Change Settings**

1. **Open `.env` file**
2. **Update these lines:**
   ```bash
   ENABLE_PREGENERATION=true         # or "false"
   PREGENERATION_MODE=background     # or "blocking"
   ```
3. **Restart server:**
   ```powershell
   # Stop server (Ctrl+C)
   uv run uvicorn main:app --reload
   ```

---

## 🔍 **Monitoring Pre-Generation**

### **Watch Logs During Startup:**

**Background Mode:**
```
🚀 Starting BACKGROUND pre-generation...
⚡ Server READY! Pre-generation running in background...
INFO: Application startup complete.
✅ [1/10] Cached: ...
✅ [2/10] Cached: ...
```

**Blocking Mode:**
```
🚀 Pre-generating responses at startup (blocking mode)...
✅ [1/10] Cached: ...
✅ [10/10] Cached: ...
⚡ Pre-generation complete! Server ready.
INFO: Application startup complete.
```

**Disabled:**
```
⚡ Pre-generation DISABLED - using on-demand generation only
INFO: Application startup complete.
```

### **Check Cache Status:**
```powershell
curl http://localhost:8000/api/phone/performance-stats
```

**Response:**
```json
{
  "cache_hit_rate": "65.2%",
  "pre_generated_responses": 10,
  "optimization_status": "active"
}
```

---

## ❓ **FAQs**

### **Q: Why is startup slow?**
**A:** You're in **blocking mode**. Change to `PREGENERATION_MODE=background` for instant startup.

### **Q: Why aren't responses instant?**
**A:** Pre-generation might be disabled or still running. Check:
1. `.env` has `ENABLE_PREGENERATION=true`
2. Wait 60-90 seconds for cache to build
3. Check `/api/phone/performance-stats` endpoint

### **Q: Can I reduce startup time?**
**A:** Yes! Use **background mode**:
```bash
PREGENERATION_MODE=background
```
Server ready in ~5 seconds, pre-generation completes in background.

### **Q: Will this affect my API usage?**
**A:** Pre-generation uses **10-20 API calls** at startup (one-time cost), but **saves 60%+ calls** during runtime through caching. **Net savings**: ~40-50% fewer API calls overall.

### **Q: What if I want even faster startup?**
**A:** Disable pre-generation:
```bash
ENABLE_PREGENERATION=false
```
Startup in ~5 seconds, but all responses will be slower (1-2.5s).

---

## 🎯 **Summary**

**Current Default** (Recommended):
- ✅ **Background mode** enabled
- ✅ Server ready in **5 seconds**
- ✅ Pre-generation completes in **60-90 seconds**
- ✅ First few calls: **1-2.5s**, then **< 500ms**

**To change**, update `.env`:
```bash
# Fast startup (default - recommended)
ENABLE_PREGENERATION=true
PREGENERATION_MODE=background

# OR: Wait for full optimization
PREGENERATION_MODE=blocking

# OR: Skip pre-generation
ENABLE_PREGENERATION=false
```

---

*Guide created: 2025-10-11*  
*Default Mode: Background (recommended)*  
*Change settings in: `.env` file*
