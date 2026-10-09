/**
 * BoloBot AI Platform - Audio Worklet Processor
 * Ultra-low latency real-time audio processing for WebRTC
 */

class BoloBotAudioProcessor extends AudioWorkletProcessor {
    constructor(options) {
        super();
        
        // Audio configuration for optimal processing
        this.sampleRate = 16000; // Azure STT optimal sample rate
        this.channels = 1; // Mono for efficiency
        this.bufferSize = 2048; // Small buffer for low latency
        this.chunkDuration = 0.25; // 250ms chunks
        this.chunkSamples = Math.floor(this.sampleRate * this.chunkDuration);
        
        // Audio buffers
        this.inputBuffer = new Float32Array(this.chunkSamples * 2); // Double buffer
        this.outputBuffer = new Float32Array(this.chunkSamples);
        this.bufferIndex = 0;
        
        // Voice Activity Detection (VAD)
        this.vadThreshold = 0.01; // Minimum energy for speech detection
        this.vadSmoothingFactor = 0.95;
        this.smoothedEnergy = 0;
        this.silenceFrames = 0;
        this.maxSilenceFrames = Math.floor(1.0 / this.chunkDuration); // 1 second of silence
        
        // Noise reduction parameters
        this.noiseFloor = 0.001;
        this.noiseSuppression = 0.5;
        this.preEmphasisAlpha = 0.97;
        this.previousSample = 0;
        
        // Performance monitoring
        this.processedChunks = 0;
        this.lastProcessTime = 0;
        this.averageProcessTime = 0;
        
        // Initialize message handler
        this.port.onmessage = this.handleMessage.bind(this);
        
        console.log('[AudioWorklet] BoloBot Audio Processor initialized');
    }
    
    handleMessage(event) {
        const { type, data } = event.data;
        
        switch (type) {
            case 'configure':
                this.configureProcessor(data);
                break;
            case 'setVADThreshold':
                this.vadThreshold = data.threshold;
                break;
            case 'enableNoiseReduction':
                this.noiseReductionEnabled = data.enabled;
                break;
            case 'getPerformanceStats':
                this.sendPerformanceStats();
                break;
        }
    }
    
    configureProcessor(config) {
        if (config.sampleRate) this.sampleRate = config.sampleRate;
        if (config.vadThreshold) this.vadThreshold = config.vadThreshold;
        if (config.chunkDuration) {
            this.chunkDuration = config.chunkDuration;
            this.chunkSamples = Math.floor(this.sampleRate * this.chunkDuration);
            this.inputBuffer = new Float32Array(this.chunkSamples * 2);
            this.outputBuffer = new Float32Array(this.chunkSamples);
        }
        
        this.port.postMessage({
            type: 'configured',
            config: {
                sampleRate: this.sampleRate,
                chunkSamples: this.chunkSamples,
                vadThreshold: this.vadThreshold
            }
        });
    }
    
    process(inputs, outputs, parameters) {
        const startTime = performance.now();
        
        const input = inputs[0];
        const output = outputs[0];
        
        // Process only if we have input
        if (input.length > 0 && input[0].length > 0) {
            const inputChannel = input[0]; // Use first channel (mono)
            const outputChannel = output[0];
            
            // Process each sample
            for (let i = 0; i < inputChannel.length; i++) {
                const processedSample = this.processSample(inputChannel[i]);
                
                // Add to buffer
                this.inputBuffer[this.bufferIndex] = processedSample;
                this.bufferIndex++;
                
                // Copy to output (real-time monitoring)
                if (outputChannel) {
                    outputChannel[i] = processedSample * 0.5; // Lower volume for monitoring
                }
                
                // Process chunk when buffer is full
                if (this.bufferIndex >= this.chunkSamples) {
                    this.processAudioChunk();
                    this.bufferIndex = 0;
                }
            }
        }
        
        // Update performance statistics
        const processTime = performance.now() - startTime;
        this.updatePerformanceStats(processTime);
        
        return true; // Keep processor alive
    }
    
    processSample(sample) {
        // Apply pre-emphasis filter (high-pass)
        const emphasized = sample - this.preEmphasisAlpha * this.previousSample;
        this.previousSample = sample;
        
        // Apply noise reduction
        let processed = emphasized;
        
        if (this.noiseReductionEnabled && Math.abs(processed) < this.noiseFloor) {
            processed *= this.noiseSuppression;
        }
        
        // Soft limiting to prevent clipping
        if (Math.abs(processed) > 0.95) {
            processed = Math.sign(processed) * (0.95 + 0.05 * Math.tanh((Math.abs(processed) - 0.95) * 10));
        }
        
        return processed;
    }
    
    processAudioChunk() {
        try {
            // Copy buffer to output array
            this.outputBuffer.set(this.inputBuffer.slice(0, this.chunkSamples));
            
            // Voice Activity Detection
            const vadResult = this.detectVoiceActivity(this.outputBuffer);
            
            // Only send chunks with voice activity (with some context)
            if (vadResult.hasVoice || this.silenceFrames < 2) {
                // Convert to 16-bit PCM for transmission
                const pcmData = this.float32ToPCM16(this.outputBuffer);
                
                // Send processed chunk to main thread
                this.port.postMessage({
                    type: 'audioChunk',
                    data: {
                        audioData: pcmData,
                        sampleRate: this.sampleRate,
                        channels: this.channels,
                        vadResult: vadResult,
                        timestamp: performance.now(),
                        chunkIndex: this.processedChunks
                    }
                });
                
                this.silenceFrames = 0;
            } else {
                this.silenceFrames++;
                
                // Send periodic silence indication
                if (this.silenceFrames % 10 === 0) {
                    this.port.postMessage({
                        type: 'silenceDetected',
                        data: {
                            silenceDuration: this.silenceFrames * this.chunkDuration,
                            timestamp: performance.now()
                        }
                    });
                }
            }
            
            this.processedChunks++;
            
        } catch (error) {
            console.error('[AudioWorklet] Chunk processing error:', error);
            this.port.postMessage({
                type: 'error',
                error: error.message
            });
        }
    }
    
    detectVoiceActivity(audioData) {
        // Calculate RMS energy
        let sumSquares = 0;
        for (let i = 0; i < audioData.length; i++) {
            sumSquares += audioData[i] * audioData[i];
        }
        const rmsEnergy = Math.sqrt(sumSquares / audioData.length);
        
        // Apply smoothing
        this.smoothedEnergy = this.vadSmoothingFactor * this.smoothedEnergy + 
                            (1 - this.vadSmoothingFactor) * rmsEnergy;
        
        // Detect voice based on smoothed energy
        const hasVoice = this.smoothedEnergy > this.vadThreshold;
        
        // Calculate spectral characteristics for better detection
        const spectralCentroid = this.calculateSpectralCentroid(audioData);
        const zeroCrossingRate = this.calculateZeroCrossingRate(audioData);
        
        // Enhanced VAD using multiple features
        const enhancedVAD = hasVoice && 
                           spectralCentroid > 500 && // Voice typically has higher spectral centroid
                           zeroCrossingRate < 0.3;   // Speech has lower zero-crossing rate than noise
        
        return {
            hasVoice: enhancedVAD,
            rmsEnergy: rmsEnergy,
            smoothedEnergy: this.smoothedEnergy,
            spectralCentroid: spectralCentroid,
            zeroCrossingRate: zeroCrossingRate,
            confidence: Math.min(1.0, this.smoothedEnergy / (this.vadThreshold * 2))
        };
    }
    
    calculateSpectralCentroid(audioData) {
        // Simple approximation of spectral centroid
        // In production, this would use FFT
        let weightedSum = 0;
        let magnitudeSum = 0;
        
        for (let i = 1; i < audioData.length; i++) {
            const magnitude = Math.abs(audioData[i] - audioData[i-1]);
            weightedSum += i * magnitude;
            magnitudeSum += magnitude;
        }
        
        return magnitudeSum > 0 ? (weightedSum / magnitudeSum) * (this.sampleRate / 2) / audioData.length : 0;
    }
    
    calculateZeroCrossingRate(audioData) {
        let crossings = 0;
        
        for (let i = 1; i < audioData.length; i++) {
            if ((audioData[i] >= 0) !== (audioData[i-1] >= 0)) {
                crossings++;
            }
        }
        
        return crossings / (audioData.length - 1);
    }
    
    float32ToPCM16(float32Array) {
        const pcm16 = new Int16Array(float32Array.length);
        
        for (let i = 0; i < float32Array.length; i++) {
            // Convert to 16-bit PCM
            const sample = Math.max(-1, Math.min(1, float32Array[i]));
            pcm16[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
        }
        
        return pcm16;
    }
    
    updatePerformanceStats(processTime) {
        const alpha = 0.1; // Smoothing factor
        this.averageProcessTime = alpha * processTime + (1 - alpha) * this.averageProcessTime;
        this.lastProcessTime = processTime;
    }
    
    sendPerformanceStats() {
        const stats = {
            processedChunks: this.processedChunks,
            averageProcessTime: this.averageProcessTime,
            lastProcessTime: this.lastProcessTime,
            bufferUtilization: this.bufferIndex / this.chunkSamples,
            vadThreshold: this.vadThreshold,
            smoothedEnergy: this.smoothedEnergy,
            silenceFrames: this.silenceFrames
        };
        
        this.port.postMessage({
            type: 'performanceStats',
            data: stats
        });
    }
}

// Register the processor
registerProcessor('bolobot-audio-processor', BoloBotAudioProcessor);
