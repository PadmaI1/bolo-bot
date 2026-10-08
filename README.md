# 🤖 B2B AI Phone Agent Solution

## 📋 Project Overview

An intelligent, lightning-fast B2B AI phone agent system built for automated sales and real estate lead qualification. The system leverages premium AI voices (Murf AI) and GPT-4o to conduct natural, bilingual conversations in Hindi and English, achieving <1.5s response times. It handles outbound calls via Twilio, qualifies leads in real-time, updates CRM automatically, and sends personalized email summaries—all while maintaining persistent call records in a local database for analytics and follow-up.

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python), AsyncIO for concurrent operations, WebSocket streaming
- **AI/ML**: Azure OpenAI GPT-4o, Murf AI WebSocket Streaming (Premium Hindi/English voices)
- **Telephony**: Twilio Voice API, Ngrok for local development webhooks
- **Storage**: JSON-based local database, In-memory conversation tracking
- **Frontend**: Bootstrap 5, Vanilla JavaScript, Real-time dashboard updates

## 🔄 Complete User & Data Flow

### 1️⃣ **User Interaction Flow**

```
User Action (Web Dashboard)
         ↓
    Makes Test Call → FastAPI /api/phone/call
         ↓
    Twilio Initiates Call → Customer Phone Rings
         ↓
    Customer Answers → Twilio POST /api/phone/twiml/{call_type}
         ↓
    AI Agent Speaks (Opening Message) → Murf AI generates voice
         ↓
    Customer Speaks → Twilio POST /api/phone/process-speech
         ↓
    (Loop: AI Response → Customer Response) × N times
         ↓
    Call Ends → Twilio POST /api/phone/status (completed)
         ↓
    Dashboard Updates → Shows call record with stats
```

### 2️⃣ **AI Query & Response Flow**

```
Customer Speech (Audio)
         ↓
    Twilio Transcription → Raw text
         ↓
    Lightning Language Detector (<1ms) → Detects Hindi/English/Telugu
         ↓
    Sentiment Analysis → Interested/Neutral/Objection
         ↓
    Intent Detection → general_inquiry/interested/pricing/objection
         ↓
    Conversation History Retrieval → Last 5 exchanges
         ↓
    Azure OpenAI GPT-4o (2024-12-01-preview)
      - Optimized prompt (50-80 tokens)
      - Temperature: 0.8, Max tokens: 200
      - Response time: ~1.2s
         ↓
    AI Response Text (Hindi-English mixed)
         ↓
    Bilingual Enhancement → Natural code-switching
         ↓
    Murf AI WebSocket Streaming
      - Premium voice (hi-IN-shaan/shweta)
      - Phone-optimized (8kHz mono WAV)
      - TTFB: <500ms, Total: <1.5s
         ↓
    Audio File Saved → /Voice_outputs/*.wav
         ↓
    Twilio Plays Audio → Customer hears response
         ↓
    Update Conversation History → Memory store
```

### 3️⃣ **Data Persistence Flow**

```
Call Completion
         ↓
    _process_call_completion()
         ↓
    Generate Call Summary
      - Interest level, Lead score
      - Next steps, Use case
      - Conversation analysis
         ↓
    Update CRM (Mock/Salesforce)
         ↓
    Send Email Summary (via Gmail SMTP)
         ↓
    Save to Local Database
      - database/b2b_sales_records.json
      - database/real_estate_records.json
         ↓
    Dashboard API (/api/records/{call_type})
         ↓
    Frontend JavaScript loads records
         ↓
    Display in Records Page (persistent)
```

## 🏗️ Full System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE LAYER                         │
├─────────────────────────────────────────────────────────────────────┤
│  Web Dashboard        │  B2B Records Page  │  Real Estate Portal    │
│  - Make test calls    │  - View history    │  - Property leads      │
│  - View analytics     │  - Lead scores     │  - Qualification data  │
│  - CRM sync status    │  - Email status    │  - Appointment booking │
└──────────────┬────────────────────┬────────────────────┬────────────┘
               │                    │                    │
               ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FASTAPI APPLICATION LAYER                       │
├─────────────────────────────────────────────────────────────────────┤
│  API Endpoints:                                                      │
│  • /api/phone/call (Initiate)    • /api/phone/twiml (TwiML)        │
│  • /api/phone/process-speech     • /api/phone/status (Webhooks)    │
│  • /api/records/b2b_sales        • /api/records/real_estate        │
│  • /api/dashboard/calls          • /audio/*.wav (Serve audio)      │
└──────────────┬────────────────────┬────────────────────┬────────────┘
               │                    │                    │
               ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      CORE SERVICES LAYER                             │
├─────────────────────────────────────────────────────────────────────┤
│  Phone Service        │  AI Services          │  Storage Service    │
│  ┌─────────────────┐ │  ┌─────────────────┐  │  ┌───────────────┐ │
│  │ TwilioPhoneService│→│ IntelligentPhoneAI│→ │ LocalDataStorage│ │
│  │ - Make calls    │ │  │ - Sentiment     │  │  │ - Save records│ │
│  │ - End calls     │ │  │ - Intent detect │  │  │ - Get stats   │ │
│  │ - Get status    │ │  │ - Context track │  │  │ - Dashboard   │ │
│  └─────────────────┘ │  └─────────────────┘  │  └───────────────┘ │
│                      │                        │                     │
│  Voice Service       │  Language Detector    │  Email Service      │
│  ┌─────────────────┐ │  ┌─────────────────┐  │  ┌───────────────┐ │
│  │UltraFastNativeSales│→│LightningLanguage│→ │ │ EmailService  │ │
│  │ - Premium voices│ │  │  Detector       │  │  │ - Send summary│ │
│  │ - WebSocket     │ │  │ - <1ms detection│  │  │ - Gmail SMTP  │ │
│  │ - Connection pool│ │  │ - Hindi/English │  │  └───────────────┘ │
│  └─────────────────┘ │  └─────────────────┘  │                     │
└──────────────┬────────────────────┬────────────────────┬────────────┘
               │                    │                    │
               ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    EXTERNAL INTEGRATIONS LAYER                       │
├─────────────────────────────────────────────────────────────────────┤
│  Twilio Voice API    │  Azure OpenAI        │  Murf AI WebSocket   │
│  ┌─────────────────┐ │  ┌─────────────────┐ │  ┌───────────────┐  │
│  │ • Outbound calls│ │  │ • GPT-4o        │ │  │ • hi-IN-shaan │  │
│  │ • TwiML webhooks│ │  │ • Chat API      │ │  │ • hi-IN-shweta│  │
│  │ • Transcription │ │  │ • 2024-12-01    │ │  │ • en-IN-priya │  │
│  │ • Recording     │ │  │ • 200 tokens    │ │  │ • Streaming   │  │
│  └─────────────────┘ │  └─────────────────┘ │  └───────────────┘  │
│                      │                        │                     │
│  Mock CRM / SFDC    │  Gmail SMTP           │  Local Database      │
│  ┌─────────────────┐ │  ┌─────────────────┐ │  ┌───────────────┐  │
│  │ • Lead tracking │ │  │ • Send emails   │ │  │ • JSON files  │  │
│  │ • Contact update│ │  │ • Call summaries│ │  │ • Persistent  │  │
│  │ • Sales pipeline│ │  │ • HTML templates│ │  │ • Fast access │  │
│  └─────────────────┘ │  └─────────────────┘ │  └───────────────┘  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         DATA PERSISTENCE LAYER                       │
├─────────────────────────────────────────────────────────────────────┤
│  database/b2b_sales_records.json    │  database/real_estate_records│
│  - Call history                     │  .json                       │
│  - Lead scores                      │  - Property inquiries        │
│  - Conversation summaries           │  - Qualification scores      │
│  - Email status                     │  - Next actions              │
└─────────────────────────────────────────────────────────────────────┘
```

## 🚀 Performance Metrics

- **Response Time**: <1.5s total (TTFB <500ms)
- **Language Detection**: <1ms (regex-based)
- **AI Response**: ~1.2s (GPT-4o optimized)
- **Voice Generation**: ~1.5s (Murf WebSocket streaming)
- **Connection Pooling**: Saves 650ms per call
- **Concurrent Calls**: 20 simultaneous (semaphore-controlled)

## 📦 Key Features

- ✅ **Ultra-fast AI responses** (<1.5s total)
- ✅ **Premium bilingual voices** (Hindi-English code-switching)
- ✅ **Real-time sentiment analysis** and intent detection
- ✅ **Automatic CRM updates** (Mock/Salesforce)
- ✅ **Email summaries** with call details
- ✅ **Persistent call records** (local JSON database)
- ✅ **Interactive dashboards** with analytics
- ✅ **Phone-optimized audio** (8kHz mono WAV)
- ✅ **Connection pooling** for reduced latency

## 👨‍💻 Author

**Padma Iyer**  

## 🙏 Acknowledgments

Special thanks to:

- **Murf AI** for providing premium voice synthesis with WebSocket streaming
- **Azure OpenAI** for GPT-4o model access and powerful language understanding
- **Twilio** for reliable voice communication infrastructure

---

_Built with ❤️ for lightning-fast B2B sales automation_
