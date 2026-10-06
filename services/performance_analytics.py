"""
📊 Performance Monitoring & Analytics System
Real-time tracking and optimization suggestions for phone AI system

Features:
- Voice generation performance tracking
- Language detection accuracy monitoring
- Voice switching analysis
- TTFB (Time To First Byte) metrics
- Customer satisfaction correlation
- Automated optimization recommendations
"""

import logging
import time
import statistics
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


@dataclass
class VoiceGenerationMetric:
    """Single voice generation performance record"""
    timestamp: datetime
    duration_ms: float
    ttfb_ms: float
    voice_id: str
    language: str
    text_length: int
    audio_size_bytes: int
    success: bool
    error: Optional[str] = None


@dataclass
class LanguageDetectionMetric:
    """Language detection performance record"""
    timestamp: datetime
    detected_language: str
    confidence: float
    detection_method: str
    text_length: int
    was_correct: Optional[bool] = None  # If we have ground truth


@dataclass
class VoiceSwitchMetric:
    """Voice switching event record"""
    timestamp: datetime
    call_sid: str
    from_voice: str
    to_voice: str
    from_language: str
    to_language: str
    confidence: float
    reason: str  # "language_change", "low_confidence", "customer_preference"


@dataclass
class CallPerformanceMetric:
    """Overall call performance record"""
    call_sid: str
    call_type: str
    start_time: datetime
    end_time: Optional[datetime]
    total_exchanges: int
    avg_response_time_ms: float
    language_switches: int
    voice_switches: int
    customer_satisfaction: Optional[int] = None  # 1-5 scale


class PerformanceMonitor:
    """
    Comprehensive performance monitoring and analytics system
    Tracks all aspects of phone AI performance for optimization
    """
    
    def __init__(self, history_limit: int = 1000):
        self.logger = logging.getLogger(__name__)
        self.history_limit = history_limit
        
        # Metrics storage
        self.voice_generations: List[VoiceGenerationMetric] = []
        self.language_detections: List[LanguageDetectionMetric] = []
        self.voice_switches: List[VoiceSwitchMetric] = []
        self.call_performances: Dict[str, CallPerformanceMetric] = {}
        
        # Real-time counters
        self.counters = {
            "total_calls": 0,
            "total_generations": 0,
            "total_detections": 0,
            "total_switches": 0,
            "failed_generations": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # Performance thresholds for alerts
        self.thresholds = {
            "max_ttfb_ms": 1500,
            "max_generation_ms": 3000,
            "min_detection_confidence": 0.75,
            "max_switch_rate": 0.30,  # 30% of calls
            "min_avg_satisfaction": 3.5
        }
        
        self.logger.info("📊 Performance Monitor initialized")
    
    def track_voice_generation(
        self,
        voice_id: str,
        language: str,
        text: str,
        duration_ms: float,
        ttfb_ms: float,
        audio_size: int,
        success: bool = True,
        error: Optional[str] = None
    ):
        """Track a voice generation event"""
        metric = VoiceGenerationMetric(
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            ttfb_ms=ttfb_ms,
            voice_id=voice_id,
            language=language,
            text_length=len(text),
            audio_size_bytes=audio_size,
            success=success,
            error=error
        )
        
        self.voice_generations.append(metric)
        self.counters["total_generations"] += 1
        
        if not success:
            self.counters["failed_generations"] += 1
        
        # Trim history
        if len(self.voice_generations) > self.history_limit:
            self.voice_generations.pop(0)
        
        # Alert if threshold exceeded
        if ttfb_ms > self.thresholds["max_ttfb_ms"]:
            self.logger.warning(
                f"⚠️ High TTFB: {ttfb_ms:.0f}ms "
                f"(threshold: {self.thresholds['max_ttfb_ms']}ms) "
                f"for {voice_id}"
            )
    
    def track_language_detection(
        self,
        detected_language: str,
        confidence: float,
        detection_method: str,
        text: str,
        was_correct: Optional[bool] = None
    ):
        """Track a language detection event"""
        metric = LanguageDetectionMetric(
            timestamp=datetime.now(),
            detected_language=detected_language,
            confidence=confidence,
            detection_method=detection_method,
            text_length=len(text),
            was_correct=was_correct
        )
        
        self.language_detections.append(metric)
        self.counters["total_detections"] += 1
        
        if len(self.language_detections) > self.history_limit:
            self.language_detections.pop(0)
        
        # Alert if confidence too low
        if confidence < self.thresholds["min_detection_confidence"]:
            self.logger.warning(
                f"⚠️ Low detection confidence: {confidence:.2%} "
                f"for {detected_language}"
            )
    
    def track_voice_switch(
        self,
        call_sid: str,
        from_voice: str,
        to_voice: str,
        from_language: str,
        to_language: str,
        confidence: float,
        reason: str
    ):
        """Track a voice switching event"""
        metric = VoiceSwitchMetric(
            timestamp=datetime.now(),
            call_sid=call_sid,
            from_voice=from_voice,
            to_voice=to_voice,
            from_language=from_language,
            to_language=to_language,
            confidence=confidence,
            reason=reason
        )
        
        self.voice_switches.append(metric)
        self.counters["total_switches"] += 1
        
        if len(self.voice_switches) > self.history_limit:
            self.voice_switches.pop(0)
        
        self.logger.info(
            f"🔄 Voice switch tracked: {from_voice} → {to_voice} "
            f"(reason: {reason}, confidence: {confidence:.2%})"
        )
    
    def start_call_tracking(
        self,
        call_sid: str,
        call_type: str
    ):
        """Start tracking a new call"""
        self.call_performances[call_sid] = CallPerformanceMetric(
            call_sid=call_sid,
            call_type=call_type,
            start_time=datetime.now(),
            end_time=None,
            total_exchanges=0,
            avg_response_time_ms=0.0,
            language_switches=0,
            voice_switches=0
        )
        
        self.counters["total_calls"] += 1
        self.logger.debug(f"📞 Started tracking call: {call_sid}")
    
    def end_call_tracking(
        self,
        call_sid: str,
        customer_satisfaction: Optional[int] = None
    ):
        """End tracking for a call"""
        if call_sid in self.call_performances:
            call_metric = self.call_performances[call_sid]
            call_metric.end_time = datetime.now()
            call_metric.customer_satisfaction = customer_satisfaction
            
            self.logger.debug(f"📴 Ended tracking call: {call_sid}")
    
    def update_call_metrics(
        self,
        call_sid: str,
        response_time_ms: Optional[float] = None,
        language_switch: bool = False,
        voice_switch: bool = False
    ):
        """Update metrics for an ongoing call"""
        if call_sid not in self.call_performances:
            return
        
        call_metric = self.call_performances[call_sid]
        call_metric.total_exchanges += 1
        
        if response_time_ms:
            # Update rolling average
            current_avg = call_metric.avg_response_time_ms
            exchanges = call_metric.total_exchanges
            new_avg = ((current_avg * (exchanges - 1)) + response_time_ms) / exchanges
            call_metric.avg_response_time_ms = new_avg
        
        if language_switch:
            call_metric.language_switches += 1
        
        if voice_switch:
            call_metric.voice_switches += 1
    
    def track_cache_event(self, hit: bool):
        """Track cache hit/miss"""
        if hit:
            self.counters["cache_hits"] += 1
        else:
            self.counters["cache_misses"] += 1
    
    def get_performance_summary(
        self,
        time_window_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive performance summary
        
        Args:
            time_window_minutes: Only include metrics from last N minutes (None = all time)
        """
        # Filter by time window if specified
        cutoff_time = None
        if time_window_minutes:
            cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        
        # Filter metrics
        generations = self._filter_by_time(self.voice_generations, cutoff_time)
        detections = self._filter_by_time(self.language_detections, cutoff_time)
        switches = self._filter_by_time(self.voice_switches, cutoff_time)
        
        # Voice generation stats
        if generations:
            successful_gens = [g for g in generations if g.success]
            ttfb_times = [g.ttfb_ms for g in successful_gens if g.ttfb_ms > 0]
            total_times = [g.duration_ms for g in successful_gens]
            
            voice_gen_stats = {
                "total": len(generations),
                "successful": len(successful_gens),
                "failed": len(generations) - len(successful_gens),
                "success_rate": len(successful_gens) / len(generations) * 100,
                "avg_ttfb_ms": statistics.mean(ttfb_times) if ttfb_times else 0,
                "median_ttfb_ms": statistics.median(ttfb_times) if ttfb_times else 0,
                "min_ttfb_ms": min(ttfb_times) if ttfb_times else 0,
                "max_ttfb_ms": max(ttfb_times) if ttfb_times else 0,
                "avg_total_ms": statistics.mean(total_times) if total_times else 0,
            }
        else:
            voice_gen_stats = {"error": "No data"}
        
        # Language detection stats
        if detections:
            confidences = [d.confidence for d in detections]
            lang_distribution = defaultdict(int)
            for d in detections:
                lang_distribution[d.detected_language] += 1
            
            lang_detect_stats = {
                "total": len(detections),
                "avg_confidence": statistics.mean(confidences),
                "median_confidence": statistics.median(confidences),
                "min_confidence": min(confidences),
                "distribution": dict(lang_distribution)
            }
        else:
            lang_detect_stats = {"error": "No data"}
        
        # Voice switching stats
        if switches:
            switch_reasons = defaultdict(int)
            for s in switches:
                switch_reasons[s.reason] += 1
            
            switch_stats = {
                "total_switches": len(switches),
                "reasons": dict(switch_reasons),
                "avg_confidence": statistics.mean([s.confidence for s in switches])
            }
        else:
            switch_stats = {"error": "No data"}
        
        # Cache stats
        total_requests = self.counters["cache_hits"] + self.counters["cache_misses"]
        cache_hit_rate = (
            self.counters["cache_hits"] / total_requests * 100
            if total_requests > 0 else 0
        )
        
        return {
            "summary": {
                "total_calls": self.counters["total_calls"],
                "total_generations": self.counters["total_generations"],
                "total_detections": self.counters["total_detections"],
                "total_switches": self.counters["total_switches"],
                "time_window_minutes": time_window_minutes or "all_time"
            },
            "voice_generation": voice_gen_stats,
            "language_detection": lang_detect_stats,
            "voice_switching": switch_stats,
            "cache_performance": {
                "hit_rate": round(cache_hit_rate, 1),
                "hits": self.counters["cache_hits"],
                "misses": self.counters["cache_misses"]
            }
        }
    
    def get_optimization_suggestions(self) -> List[str]:
        """
        Generate AI-driven optimization suggestions based on metrics
        """
        suggestions = []
        
        # Analyze recent performance
        recent_gens = self._filter_by_time(
            self.voice_generations,
            datetime.now() - timedelta(minutes=30)
        )
        
        if not recent_gens:
            return ["Insufficient data for optimization suggestions"]
        
        # Check TTFB performance
        successful = [g for g in recent_gens if g.success]
        if successful:
            ttfb_times = [g.ttfb_ms for g in successful if g.ttfb_ms > 0]
            if ttfb_times:
                avg_ttfb = statistics.mean(ttfb_times)
                
                if avg_ttfb > self.thresholds["max_ttfb_ms"]:
                    suggestions.append(
                        f"🔧 High TTFB detected ({avg_ttfb:.0f}ms). "
                        f"Consider reducing min_buffer_size or enabling connection pooling."
                    )
        
        # Check language detection confidence
        recent_detections = self._filter_by_time(
            self.language_detections,
            datetime.now() - timedelta(minutes=30)
        )
        
        if recent_detections:
            low_confidence = [
                d for d in recent_detections
                if d.confidence < self.thresholds["min_detection_confidence"]
            ]
            
            if len(low_confidence) > len(recent_detections) * 0.2:
                suggestions.append(
                    f"⚠️ {len(low_confidence)} low-confidence language detections. "
                    f"Consider adding more keywords or adjusting confidence thresholds."
                )
        
        # Check voice switching rate
        if self.counters["total_calls"] > 10:
            switch_rate = self.counters["total_switches"] / self.counters["total_calls"]
            
            if switch_rate > self.thresholds["max_switch_rate"]:
                suggestions.append(
                    f"🔄 High voice switching rate ({switch_rate:.1%}). "
                    f"Consider increasing min_confidence_for_switch threshold."
                )
        
        # Check cache performance
        total_requests = self.counters["cache_hits"] + self.counters["cache_misses"]
        if total_requests > 50:
            hit_rate = self.counters["cache_hits"] / total_requests
            
            if hit_rate < 0.50:
                suggestions.append(
                    f"💾 Low cache hit rate ({hit_rate:.1%}). "
                    f"Consider pre-generating more common responses or increasing TTL."
                )
        
        # Check failure rate
        if self.counters["total_generations"] > 20:
            failure_rate = (
                self.counters["failed_generations"] / 
                self.counters["total_generations"]
            )
            
            if failure_rate > 0.05:  # More than 5% failures
                suggestions.append(
                    f"❌ Generation failure rate is {failure_rate:.1%}. "
                    f"Check rate limiting settings and connection stability."
                )
        
        if not suggestions:
            suggestions.append("✅ All systems operating optimally!")
        
        return suggestions
    
    def _filter_by_time(self, metrics: List, cutoff_time: Optional[datetime]) -> List:
        """Filter metrics by timestamp"""
        if not cutoff_time:
            return metrics
        
        return [m for m in metrics if m.timestamp >= cutoff_time]
    
    def export_metrics(self, filepath: str):
        """Export all metrics to JSON file"""
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "counters": self.counters,
            "voice_generations": [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "duration_ms": m.duration_ms,
                    "ttfb_ms": m.ttfb_ms,
                    "voice_id": m.voice_id,
                    "language": m.language,
                    "success": m.success
                }
                for m in self.voice_generations
            ],
            "language_detections": [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "language": m.detected_language,
                    "confidence": m.confidence,
                    "method": m.detection_method
                }
                for m in self.language_detections
            ],
            "voice_switches": [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "from": m.from_voice,
                    "to": m.to_voice,
                    "reason": m.reason,
                    "confidence": m.confidence
                }
                for m in self.voice_switches
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"📁 Metrics exported to {filepath}")


# Testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    monitor = PerformanceMonitor()
    
    # Simulate some events
    print("\n🧪 Testing Performance Monitor\n")
    
    # Track voice generations
    monitor.track_voice_generation(
        "en-IN-priya", "english", "Hello world", 1200, 350, 45000
    )
    monitor.track_voice_generation(
        "hi-IN-ayushi", "hindi", "नमस्ते", 1100, 320, 38000
    )
    
    # Track language detections
    monitor.track_language_detection("english", 0.95, "script", "Hello there")
    monitor.track_language_detection("hindi", 0.88, "mixed", "नमस्ते दोस्त")
    
    # Track voice switch
    monitor.track_voice_switch(
        "test_call_123",
        "en-IN-priya",
        "hi-IN-ayushi",
        "english",
        "hindi",
        0.92,
        "language_change"
    )
    
    # Generate summary
    print("📊 Performance Summary:")
    summary = monitor.get_performance_summary()
    print(json.dumps(summary, indent=2))
    
    print("\n💡 Optimization Suggestions:")
    suggestions = monitor.get_optimization_suggestions()
    for suggestion in suggestions:
        print(f"  {suggestion}")
