"""
Quick Test Script for Lightning Optimization
=============================================
Run this to validate all optimizations are working correctly.

Usage:
    uv run test_lightning_optimization.py
"""

import asyncio
import time
import sys
from pathlib import Path

# Add services to path
sys.path.insert(0, str(Path(__file__).parent))

from services.lightning_murf import LightningMurfStreaming
from services.lightning_language_detector import LightningLanguageDetector


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print colored header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")


def print_test(text: str):
    """Print test description"""
    print(f"{Colors.BLUE}📋 {text}{Colors.RESET}")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")


def print_metric(name: str, value: str, target: str, passed: bool):
    """Print performance metric"""
    icon = "✅" if passed else "❌"
    color = Colors.GREEN if passed else Colors.RED
    print(f"   {icon} {name}: {color}{value}{Colors.RESET} (target: {target})")


async def test_language_detection():
    """Test lightning language detection"""
    print_header("TEST 1: Lightning Language Detection")
    
    detector = LightningLanguageDetector()
    
    test_cases = [
        ("Hello! How can I help you?", "english", "en-IN-priya"),
        ("नमस्ते! मैं आपकी मदद कर सकता हूं।", "hindi", "hi-IN-ayushi"),
        ("Hi, mujhe property chahiye", "english", "en-IN-priya"),  # Hinglish
    ]
    
    all_passed = True
    
    for text, expected_lang, expected_voice in test_cases:
        print_test(f"Testing: {text[:50]}...")
        
        result = detector.detect_lightning_fast(text)
        
        # Check detection time
        detection_passed = result.detection_time_ms < 1.0
        print_metric(
            "Detection Time",
            f"{result.detection_time_ms:.3f}ms",
            "<1ms",
            detection_passed
        )
        
        # Check language
        lang_passed = result.language == expected_lang
        if lang_passed:
            print_success(f"Language: {result.language} (confidence: {result.confidence})")
        else:
            print_error(f"Language: {result.language} (expected: {expected_lang})")
            all_passed = False
        
        # Check voice
        voice_passed = result.voice_id == expected_voice
        if voice_passed:
            print_success(f"Voice: {result.voice_id}")
        else:
            print_warning(f"Voice: {result.voice_id} (expected: {expected_voice})")
        
        print()
        
        if not detection_passed:
            all_passed = False
    
    return all_passed


async def test_murf_streaming():
    """Test lightning Murf streaming"""
    print_header("TEST 2: Lightning Murf Streaming")
    
    # Check if MURF_API_KEY is set
    import os
    if not os.getenv("MURF_API_KEY"):
        print_error("MURF_API_KEY not set - skipping Murf tests")
        print_warning("Set MURF_API_KEY environment variable to run Murf tests")
        return False
    
    lightning = LightningMurfStreaming()
    
    test_cases = [
        ("Hello! This is a test.", "en-IN-priya"),
        ("नमस्ते! यह एक परीक्षण है।", "hi-IN-ayushi"),
    ]
    
    all_passed = True
    
    for text, voice_id in test_cases:
        print_test(f"Testing: {text[:50]}... with {voice_id}")
        
        try:
            audio, metrics = await lightning.generate_phone_optimized_audio(text, voice_id)
            
            # Check TTFB
            ttfb_passed = metrics.ttfb_ms < 500
            print_metric(
                "TTFB",
                f"{metrics.ttfb_ms:.0f}ms",
                "<500ms",
                ttfb_passed
            )
            
            # Check total time
            total_passed = metrics.total_time_ms < 1500
            print_metric(
                "Total Time",
                f"{metrics.total_time_ms:.0f}ms",
                "<1500ms",
                total_passed
            )
            
            # Check audio size
            if audio:
                print_success(f"Audio Size: {metrics.audio_size_bytes:,} bytes")
                print_success(f"Chunks: {metrics.chunk_count}")
                print_success(f"Connection Reused: {metrics.connection_reused}")
            else:
                print_error("No audio generated")
                all_passed = False
            
            print()
            
            if not (ttfb_passed and total_passed):
                all_passed = False
        
        except Exception as e:
            print_error(f"Streaming failed: {e}")
            all_passed = False
            print()
    
    # Show connection pool stats
    pool_stats = lightning.get_pool_stats()
    print_success(f"Connection Pool: {pool_stats['active_connections']}/{pool_stats['max_connections']}")
    print_success(f"Pool Usage: {pool_stats['pool_usage_percent']:.1f}%")
    
    await lightning.close_all_connections()
    
    return all_passed


async def test_end_to_end():
    """Test end-to-end flow"""
    print_header("TEST 3: End-to-End Flow")
    
    # Check if MURF_API_KEY is set
    import os
    if not os.getenv("MURF_API_KEY"):
        print_error("MURF_API_KEY not set - skipping end-to-end test")
        return False
    
    detector = LightningLanguageDetector()
    lightning = LightningMurfStreaming()
    
    test_speech = "Hi, I am interested in your product. Can you tell me more?"
    
    print_test(f"Processing: {test_speech}")
    
    try:
        start_time = time.time()
        
        # 1. Detect language
        lang_start = time.time()
        lang_result = detector.detect_lightning_fast(test_speech)
        lang_time = (time.time() - lang_start) * 1000
        
        print_success(f"Language detected: {lang_result.language} in {lang_time:.2f}ms")
        
        # 2. Generate mock AI response (in real system, this would call Azure OpenAI)
        ai_response = "Great! I'd be happy to tell you more about our product..."
        
        # 3. Generate audio
        audio, metrics = await lightning.generate_phone_optimized_audio(
            ai_response, lang_result.voice_id
        )
        
        total_time = (time.time() - start_time) * 1000
        
        # Check metrics
        print_metric("Language Detection", f"{lang_time:.2f}ms", "<1ms", lang_time < 1.0)
        print_metric("TTFB", f"{metrics.ttfb_ms:.0f}ms", "<500ms", metrics.ttfb_ms < 500)
        print_metric("Voice Generation", f"{metrics.total_time_ms:.0f}ms", "<1500ms", metrics.total_time_ms < 1500)
        print_metric("Total E2E Time", f"{total_time:.0f}ms", "<2000ms", total_time < 2000)
        
        passed = (
            lang_time < 1.0 and
            metrics.ttfb_ms < 500 and
            metrics.total_time_ms < 1500 and
            total_time < 2000
        )
        
        await lightning.close_all_connections()
        
        return passed
    
    except Exception as e:
        print_error(f"End-to-end test failed: {e}")
        return False


async def run_all_tests():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║          Lightning Optimization Test Suite                      ║")
    print("║          B2B AI Phone Agent Solution                            ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(Colors.RESET)
    
    results = {}
    
    # Test 1: Language Detection
    try:
        results['language_detection'] = await test_language_detection()
    except Exception as e:
        print_error(f"Language detection test crashed: {e}")
        results['language_detection'] = False
    
    # Test 2: Murf Streaming
    try:
        results['murf_streaming'] = await test_murf_streaming()
    except Exception as e:
        print_error(f"Murf streaming test crashed: {e}")
        results['murf_streaming'] = False
    
    # Test 3: End-to-End
    try:
        results['end_to_end'] = await test_end_to_end()
    except Exception as e:
        print_error(f"End-to-end test crashed: {e}")
        results['end_to_end'] = False
    
    # Print summary
    print_header("TEST SUMMARY")
    
    for test_name, passed in results.items():
        status = f"{Colors.GREEN}PASSED ✅{Colors.RESET}" if passed else f"{Colors.RED}FAILED ❌{Colors.RESET}"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    all_passed = all(results.values())
    
    print()
    if all_passed:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! Lightning optimization working correctly! ⚡{Colors.RESET}")
        print(f"\n{Colors.GREEN}Your system is ready for production with lightning-fast performance:{Colors.RESET}")
        print(f"{Colors.GREEN}  ✅ TTFB: <500ms{Colors.RESET}")
        print(f"{Colors.GREEN}  ✅ Total Response: <1.5s{Colors.RESET}")
        print(f"{Colors.GREEN}  ✅ Language Detection: <1ms{Colors.RESET}")
        print(f"{Colors.GREEN}  ✅ Connection Pooling: Active{Colors.RESET}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}⚠️  SOME TESTS FAILED - Please review errors above{Colors.RESET}")
        print(f"\n{Colors.YELLOW}Common fixes:{Colors.RESET}")
        print(f"{Colors.YELLOW}  1. Set MURF_API_KEY environment variable{Colors.RESET}")
        print(f"{Colors.YELLOW}  2. Check internet connection{Colors.RESET}")
        print(f"{Colors.YELLOW}  3. Verify Murf API is accessible{Colors.RESET}")
    
    print()
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
