import asyncio
import sys
from services.murf_voice import MurfVoiceOptimized

async def test_murf():
    print("=" * 60)
    print("🧪 Testing Murf API Implementation")
    print("=" * 60)
    
    murf = MurfVoiceOptimized()
    
    # Check API key
    if not murf.api_key:
        print("❌ MURF_API_KEY not found in environment!")
        return
    
    print(f"✅ API Key configured: {murf.api_key[:10]}...")
    print(f"🌐 Base URL: {murf.base_url}")
    print(f"📍 Endpoints: {murf.endpoints}")
    print()
    
    # Initialize
    print("🔄 Initializing Murf service...")
    await murf.initialize()
    print()
    
    if not murf.session:
        print("❌ Failed to initialize session")
        return
    
    # Test simple generation
    print("🎤 Testing voice generation...")
    print("Text: 'Hello! This is a test of the Murf API implementation.'")
    print("Voice: realestate_consultant_female (en-IN-priya)")
    print()
    
    audio = await murf.generate_premium_voice(
        "Hello! This is a test of the Murf API implementation.",
        "realestate_consultant_female"
    )
    
    if audio:
        print(f"✅ SUCCESS: Generated {len(audio)} bytes of audio")
        
        # Save to file
        output_file = "test_voice.mp3"
        with open(output_file, "wb") as f:
            f.write(audio)
        print(f"💾 Audio saved as {output_file}")
        print()
        
        # Test another voice
        print("🎤 Testing Hindi voice...")
        print("Text: 'नमस्ते! यह एक टेस्ट है।'")
        print("Voice: hindi_agent_female (hi-IN-ayushi)")
        print()
        
        audio2 = await murf.generate_premium_voice(
            "नमस्ते! यह एक टेस्ट है।",
            "hindi_agent_female"
        )
        
        if audio2:
            print(f"✅ SUCCESS: Generated {len(audio2)} bytes of Hindi audio")
            with open("test_voice_hindi.mp3", "wb") as f:
                f.write(audio2)
            print(f"💾 Hindi audio saved as test_voice_hindi.mp3")
        else:
            print("❌ Hindi voice generation failed")
    else:
        print("❌ FAILED: No audio generated")
        print("\n💡 Troubleshooting tips:")
        print("   1. Verify your API key is correct in .env file")
        print("   2. Check if your Murf account has API access enabled")
        print("   3. Review the logs above for specific error messages")
    
    print()
    
    # Show statistics
    print("📊 Performance Statistics:")
    stats = await murf.get_performance_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print()
    
    # Test all voices
    print("🎵 Testing all available voice profiles...")
    test_results = await murf.test_voice_generation()
    print()
    
    for voice_name, result in test_results.items():
        status_icon = "✅" if result.get("status") == "success" else "❌"
        print(f"{status_icon} {voice_name}: {result.get('status')}")
        if result.get("status") == "success":
            print(f"   Voice ID: {result.get('voice_id')}")
            print(f"   Time: {result.get('generation_time')}")
            print(f"   Size: {result.get('audio_size_bytes')} bytes")
        elif result.get("error"):
            print(f"   Error: {result.get('error')}")
    
    print()
    await murf.close()
    print("=" * 60)
    print("✅ Test completed")
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(test_murf())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
