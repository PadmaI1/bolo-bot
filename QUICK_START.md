# 🚀 Quick Start Guide - VoiceFlow AI Platform

## Server is Running! ✅

Your VoiceFlow AI Platform is now fully operational with Murf voice integration.

### 📍 Access Points

**Main Application**: http://localhost:8000

**Demo Dashboard**: http://localhost:8000/demo

**Sales Dashboard**: http://localhost:8000/sales

**Real Estate Portal**: http://localhost:8000/realestate

**Admin Panel**: http://localhost:8000/admin

## 🎤 Test Voice Generation

### Quick Browser Test
Open: http://localhost:8000/api/voice/profiles

### Test with PowerShell
```powershell
# View available voices
Invoke-RestMethod -Uri "http://localhost:8000/api/voice/profiles" -Method Get | ConvertTo-Json

# Test voice generation (saves as MP3)
Invoke-RestMethod -Uri "http://localhost:8000/api/voice/test" -Method Post `
  -ContentType "application/json" `
  -Body '{"text":"Hello! This is a voice test.","voice_profile":"realestate_consultant_female"}' `
  -OutFile "voice_test.mp3"

# View performance stats
Invoke-RestMethod -Uri "http://localhost:8000/api/voice/performance" -Method Get | ConvertTo-Json
```

### Test with curl (if installed)
```bash
curl http://localhost:8000/api/voice/profiles

curl -X POST http://localhost:8000/api/voice/test \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world","voice_profile":"sales_coach_confident"}' \
  --output test.mp3
```

### Test with Python Script
```powershell
uv run .\test_murf.py
```
This will generate:
- `test_voice.mp3` (English)
- `test_voice_hindi.mp3` (Hindi)

## 🎯 Available Endpoints

### Voice Services
- `GET /api/voice/profiles` - List all voice profiles
- `POST /api/voice/test` - Test voice generation
- `GET /api/voice/performance` - View performance stats
- `GET /api/debug/murf` - Debug Murf configuration

### Analytics
- `GET /api/analytics/dashboard` - Platform analytics
- `GET /api/analytics/real-time` - Real-time metrics

### Health & System
- `GET /health` - Health check
- `GET /api/session/performance/{session_id}` - Session performance

### Demo & Testing
- `POST /api/demo/start-call` - Start demo call
- `POST /api/demo/respond` - Send response
- `GET /api/demo/conversation/{session_id}` - Get conversation
- `POST /api/demo/close-call/{session_id}` - Close call
- `WS /ws/demo-call/{session_id}` - WebSocket demo

## 🎵 Voice Profiles

| Name | Voice ID | Language | Best For |
|------|----------|----------|----------|
| `realestate_consultant_female` | en-IN-priya | English | Property inquiries, warm tone |
| `realestate_consultant_male` | en-IN-eashwar | English | Property tours, professional |
| `sales_coach_confident` | en-IN-rohan | English | B2B sales, confident tone |
| `sales_coach_professional` | en-IN-alia | English | Training, narration |
| `hindi_agent_female` | hi-IN-ayushi | Hindi | Hindi customer service |
| `hindi_agent_male` | hi-IN-kabir | Hindi | Hindi property support |

## 💻 Development

### Start Server
```powershell
uv run .\main.py
```

### View Logs
Check `voiceflow_ai.log` for detailed logs

### Environment Variables
Edit `.env` file:
```
MURF_API_KEY=your_key_here
AZURE_OPENAI_KEY=your_key
```

## 🔧 Troubleshooting

### Issue: Server won't start
**Solution**: Check if port 8000 is available
```powershell
Get-NetTCPConnection -LocalPort 8000
```

### Issue: Voice generation fails
**Solution**: Check API key in `.env` and run debug endpoint:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/debug/murf"
```

### Issue: Module import errors
**Solution**: Reinstall dependencies
```powershell
uv pip install -r requirements.txt
```

## 📊 Current Status

```
✅ Murf API: Connected (161 voices)
✅ Azure Services: Initialized
✅ Conversation AI: Ready
✅ Mock CRM: Active
✅ All Services: Healthy
```

## 🎯 Next Steps

1. **Test Voice Generation**: Visit http://localhost:8000/api/voice/test
2. **Explore Demo**: Visit http://localhost:8000/demo
3. **Check Analytics**: Visit http://localhost:8000/sales or /realestate
4. **Review Logs**: Check `voiceflow_ai.log`

## 📚 Documentation

- `MURF_SUCCESS.md` - Detailed Murf integration guide
- `VOICE_SERVICE_STATUS.md` - Voice service status
- `test_murf.py` - Comprehensive test script

## 🆘 Need Help?

- Check logs: `voiceflow_ai.log`
- Debug endpoint: http://localhost:8000/api/debug/murf
- Performance stats: http://localhost:8000/api/voice/performance

---

**Server**: http://localhost:8000  
**Status**: ✅ Running  
**Murf Voices**: 161 available  
**Your API Key**: Configured ✅

🎉 **Everything is working perfectly!**
