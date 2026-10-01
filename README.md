Copilot_self/
├── main.py                     # Unified FastAPI server
├── services/
│   ├── azure_core/             # Shared Azure services
│   │   ├── stt_service.py     # Universal speech-to-text
│   │   ├── llm_service.py     # Multi-industry LLM router
│   │   └── murf_tts.py        # Enhanced voice synthesis
│   ├── sales_copilot/         # B2B sales intelligence
│   │   ├── sales_coach.py     # Real-time coaching
│   │   ├── battle_cards.py    # Competitor intelligence
│   │   └── crm_sync.py        # CRM integration
│   └── real_estate/           # Property lead automation
│       ├── lead_qualifier.py  # Property lead scoring
│       ├── property_matcher.py # Inventory matching
│       └── appointment_setter.py # Site visit booking
├── industry_prompts/          # Industry-specific prompts
│   ├── sales_personas.json
│   └── real_estate_scripts.json
├── frontend/
│   ├── sales_dashboard.html   # B2B sales interface
│   ├── real_estate_portal.html # Property lead interface
│   └── admin_panel.html       # Multi-tenant management
└── integrations/              # Third-party connectors
    ├── zoho_crm.py
    ├── salesforce.py
    └── property_portals.py


Customer Phone Call
       ↓
   Twilio (receives call)
       ↓
Your Server (FastAPI)
       ↓
IntelligentPhoneAI (thinks)
       ↓
Azure OpenAI (generates response)
       ↓
Murf AI (generates voice)
       ↓
Twilio (speaks to customer)
       ↓
Customer responds → Loop continues