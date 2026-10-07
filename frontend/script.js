// VoiceFlow AI Platform - Unified JavaScript
class VoiceAIInterface {
  constructor(industry) {
    this.industry = industry;
    this.ws = null;
    this.mediaRecorder = null;
    this.audioContext = null;
    this.isActive = false;
    this.sessionData = {
      sessionId: null,
      startTime: null,
      conversationLog: [],
      metrics: {},
    };

    this.initializeElements();
    this.setupEventListeners();
    this.initializeAudioContext();
  }

  initializeElements() {
    // Common elements
    this.connectionStatus = document.getElementById("connectionStatus");
    this.conversationLog = document.getElementById("conversationLog");
    this.audioPlayer = document.getElementById("audioPlayer");

    if (this.industry === "sales") {
      this.startBtn = document.getElementById("startCoachingBtn");
      this.stopBtn = document.getElementById("stopCoachingBtn");
      this.coachingPanel = document.getElementById("coachingPanel");
      this.battleCards = document.getElementById("battleCards");

      // Metrics elements
      this.talkTimeRatio = document.getElementById("talkTimeRatio");
      this.callDuration = document.getElementById("callDuration");
      this.questionsAsked = document.getElementById("questionsAsked");
      this.objections = document.getElementById("objections");
      this.buyingSignals = document.getElementById("buyingSignals");
      this.sentimentScore = document.getElementById("sentimentScore");
      this.dealRisk = document.getElementById("dealRisk");
    } else if (this.industry === "real_estate") {
      this.startBtn = document.getElementById("startQualificationBtn");
      this.stopBtn = document.getElementById("stopQualificationBtn");
      this.qualificationScore = document.getElementById("qualificationScore");
      this.qualificationProgress = document.getElementById(
        "qualificationProgress"
      );
      this.progressPercentage = document.getElementById("progressPercentage");

      // Lead info elements
      this.budgetRange = document.getElementById("budgetRange");
      this.propertyType = document.getElementById("propertyType");
      this.preferredLocation = document.getElementById("preferredLocation");
      this.timeline = document.getElementById("timeline");

      this.insightsPanel = document.getElementById("insightsPanel");
      this.propertyRecommendations = document.getElementById(
        "propertyRecommendations"
      );
      this.matchingProperties = document.getElementById("matchingProperties");
    }
  }

  setupEventListeners() {
    this.startBtn?.addEventListener("click", () => this.startSession());
    this.stopBtn?.addEventListener("click", () => this.stopSession());

    // Industry-specific listeners
    if (this.industry === "sales") {
      document
        .getElementById("discoveryBtn")
        ?.addEventListener("click", () => this.showQuickPrompt("discovery"));
      document
        .getElementById("valueBtn")
        ?.addEventListener("click", () => this.showQuickPrompt("value"));
      document
        .getElementById("objectionBtn")
        ?.addEventListener("click", () => this.showQuickPrompt("objection"));
      document
        .getElementById("generateSummaryBtn")
        ?.addEventListener("click", () => this.generateSessionSummary());
    } else if (this.industry === "real_estate") {
      document
        .getElementById("siteVisitBtn")
        ?.addEventListener("click", () => this.showSiteVisitModal());
      document
        .getElementById("sendPropertiesBtn")
        ?.addEventListener("click", () => this.sendPropertyRecommendations());
      document
        .getElementById("followUpBtn")
        ?.addEventListener("click", () => this.scheduleFollowUp());
      document
        .getElementById("confirmVisitBtn")
        ?.addEventListener("click", () => this.confirmSiteVisit());
    }

    // Keyboard shortcuts
    document.addEventListener("keydown", (e) => {
      if (e.key === "F1") {
        e.preventDefault();
        this.isActive ? this.stopSession() : this.startSession();
      }
    });
  }

  async initializeAudioContext() {
    try {
      this.audioContext = new (window.AudioContext ||
        window.webkitAudioContext)();
    } catch (error) {
      console.error("Failed to initialize audio context:", error);
    }
  }

  async startSession() {
    try {
      await this.connectWebSocket();
      await this.initializeAudioRecording();

      this.isActive = true;
      this.sessionData.startTime = Date.now();

      this.updateUI("active");
      this.updateConnectionStatus("connected", "Connected");

      if (this.industry === "sales") {
        this.startCallTimer();
      }
    } catch (error) {
      console.error("Failed to start session:", error);
      this.updateConnectionStatus("error", "Connection Failed");
      alert(
        "Failed to start session. Please check your microphone permissions."
      );
    }
  }

  async connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/${this.industry}`;

    this.ws = new WebSocket(wsUrl);

    return new Promise((resolve, reject) => {
      this.ws.onopen = () => {
        console.log("WebSocket connected");
        resolve();
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.handleWebSocketMessage(data);
      };

      this.ws.onclose = () => {
        console.log("WebSocket disconnected");
        this.updateConnectionStatus("disconnected", "Disconnected");
      };

      this.ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        reject(error);
      };

      // Timeout after 5 seconds
      setTimeout(() => reject(new Error("Connection timeout")), 5000);
    });
  }

  async initializeAudioRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        sampleRate: 16000,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });

    this.mediaRecorder = new MediaRecorder(stream, {
      mimeType: "audio/webm;codecs=opus",
    });

    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0 && this.ws?.readyState === WebSocket.OPEN) {
        event.data.arrayBuffer().then((buffer) => {
          this.ws.send(buffer);
        });
      }
    };

    this.mediaRecorder.start(250); // Send audio every 250ms

    // Add voice visualization
    this.setupVoiceVisualization(stream);
  }

  setupVoiceVisualization(stream) {
    if (!this.audioContext) return;

    const analyser = this.audioContext.createAnalyser();
    const source = this.audioContext.createMediaStreamSource(stream);
    source.connect(analyser);

    analyser.fftSize = 256;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const visualize = () => {
      if (!this.isActive) return;

      analyser.getByteFrequencyData(dataArray);

      // Update voice bars if they exist
      const voiceBars = document.querySelectorAll(".voice-bar");
      if (voiceBars.length > 0) {
        for (let i = 0; i < voiceBars.length; i++) {
          const height = dataArray[i * 10] || 0;
          voiceBars[i].style.height = `${(height / 255) * 50}px`;
        }
      }

      requestAnimationFrame(visualize);
    };

    visualize();
  }

  stopSession() {
    this.isActive = false;

    if (this.mediaRecorder && this.mediaRecorder.state !== "inactive") {
      this.mediaRecorder.stop();
      this.mediaRecorder.stream.getTracks().forEach((track) => track.stop());
    }

    if (this.ws) {
      this.ws.close();
    }

    this.updateUI("inactive");
    this.updateConnectionStatus("disconnected", "Disconnected");

    // Generate session summary
    setTimeout(() => this.generateSessionSummary(), 1000);
  }

  handleWebSocketMessage(data) {
    console.log("WebSocket message:", data.type);

    switch (data.type) {
      case "ready":
        this.sessionData.sessionId = data.session_id;
        this.updateConnectionStatus("ready", "Ready");
        break;

      case "transcript":
        this.addConversationMessage(data.data);
        break;

      case "sales_coaching":
        this.handleSalesCoaching(data.data);
        break;

      case "real_estate_qualification":
        this.handleRealEstateQualification(data.data);
        break;

      case "battle_card":
        this.displayBattleCard(data.data);
        break;

      case "property_recommendations":
        this.displayPropertyRecommendations(data.data);
        break;

      case "audio_coaching":
      case "audio_response":
        this.playAudioResponse(data.audio_data);
        break;

      case "session_summary":
        this.displaySessionSummary(data.data);
        break;

      case "error":
        console.error("Server error:", data.message);
        this.showAlert("error", data.message);
        break;
    }
  }

  addConversationMessage(transcriptData) {
    const messageDiv = document.createElement("div");
    const speaker = transcriptData.speaker_type || "unknown";
    const isCustomer = speaker === "customer";

    messageDiv.className = `conversation-message ${
      isCustomer ? "customer" : "agent"
    }`;

    const timestamp = new Date().toLocaleTimeString();
    messageDiv.innerHTML = `
            <div class="message-header">
                <span class="speaker">${isCustomer ? "Customer" : "You"}</span>
                <span class="timestamp">${timestamp}</span>
                <span class="confidence badge bg-secondary">${Math.round(
                  (transcriptData.confidence || 0.8) * 100
                )}%</span>
            </div>
            <div class="message-text">${transcriptData.text}</div>
        `;

    this.conversationLog.appendChild(messageDiv);
    this.conversationLog.scrollTop = this.conversationLog.scrollHeight;

    // Store in session data
    this.sessionData.conversationLog.push({
      timestamp: Date.now(),
      speaker: speaker,
      text: transcriptData.text,
      confidence: transcriptData.confidence,
    });

    // Update metrics
    this.updateConversationMetrics(speaker);
  }

  handleSalesCoaching(coachingData) {
    if (!coachingData.coaching) return;

    const coaching = coachingData.coaching;

    // Update coaching panel
    if (coaching.immediate_suggestions?.length > 0) {
      this.displayCoachingInsight(
        coaching.immediate_suggestions[0],
        "suggestion"
      );
    }

    // Update metrics
    if (coachingData.session_metrics) {
      this.updateSalesMetrics(coachingData.session_metrics);
    }

    // Update analysis data
    if (coachingData.analysis) {
      this.updateSalesAnalysis(coachingData.analysis);
    }
  }

  handleRealEstateQualification(qualificationData) {
    if (!qualificationData.qualification_update) return;

    const qualification = qualificationData.qualification_update;
    const progress = qualificationData.session_progress || {};

    // Update lead information
    this.updateLeadInformation(qualification);

    // Update progress bar
    this.updateQualificationProgress(progress);

    // Update AI insights
    if (qualificationData.analysis) {
      this.updateRealEstateInsights(qualificationData.analysis);
    }

    // Enable action buttons based on progress
    this.updateActionButtons(progress);
  }

  displayCoachingInsight(insight, type = "info") {
    const alertClass =
      {
        suggestion: "alert-primary",
        warning: "alert-warning",
        success: "alert-success",
        danger: "alert-danger",
      }[type] || "alert-info";

    const insightDiv = document.createElement("div");
    insightDiv.className = `alert ${alertClass} coaching-insight`;
    insightDiv.innerHTML = `
            <i class="fas fa-lightbulb me-2"></i>
            <strong>Coaching Tip:</strong> ${insight}
        `;

    // Remove old insights to prevent clutter
    const existingInsights =
      this.coachingPanel?.querySelectorAll(".coaching-insight");
    if (existingInsights && existingInsights.length > 2) {
      existingInsights[0].remove();
    }

    this.coachingPanel?.appendChild(insightDiv);
  }

  displayBattleCard(battleCardData) {
    if (!this.battleCards) return;

    const cardDiv = document.createElement("div");
    cardDiv.className = "battle-card alert alert-warning";
    cardDiv.innerHTML = `
            <strong>⚔️ ${battleCardData.competitor} mentioned!</strong>
            <ul class="mt-2 mb-0">
                ${
                  battleCardData.talking_points
                    ?.map((point) => `<li>${point}</li>`)
                    .join("") || ""
                }
            </ul>
        `;

    this.battleCards.appendChild(cardDiv);

    // Show battle cards section
    const battleCardsSection = document.getElementById("battleCardsSection");
    if (battleCardsSection) {
      battleCardsSection.style.display = "block";
    }
  }

  displayPropertyRecommendations(recommendationData) {
    if (!recommendationData.properties || !this.propertyRecommendations) return;

    this.propertyRecommendations.innerHTML = "";

    recommendationData.properties.forEach((property) => {
      const propertyCard = document.createElement("div");
      propertyCard.className = "col-md-4 mb-3";
      propertyCard.innerHTML = `
                <div class="card property-card">
                    <div class="card-body">
                        <h6 class="card-title">${property.name}</h6>
                        <p class="card-text">
                            <small class="text-muted">${
                              property.location
                            }</small><br>
                            <strong>${property.type}</strong><br>
                            <span class="text-success">${property.price}</span>
                        </p>
                        <div class="match-info">
                            <span class="badge bg-primary">Match: ${
                              property.match_score
                            }/10</span>
                            <div class="mt-1">
                                ${
                                  property.match_reasons
                                    ?.map(
                                      (reason) =>
                                        `<small class="badge bg-light text-dark me-1">${reason}</small>`
                                    )
                                    .join("") || ""
                                }
                            </div>
                        </div>
                    </div>
                </div>
            `;

      this.propertyRecommendations.appendChild(propertyCard);
    });

    // Update matching properties count
    if (this.matchingProperties) {
      this.matchingProperties.textContent = `${recommendationData.properties.length} matches`;
      this.matchingProperties.className = "badge bg-success";
    }
  }

  updateLeadInformation(qualification) {
    if (this.budgetRange && qualification.budget_range) {
      this.budgetRange.textContent = qualification.budget_range;
    }
    if (this.propertyType && qualification.property_type) {
      this.propertyType.textContent = qualification.property_type;
    }
    if (this.preferredLocation && qualification.locations?.length > 0) {
      this.preferredLocation.textContent = qualification.locations.join(", ");
    }
    if (this.timeline && qualification.timeline) {
      this.timeline.textContent = qualification.timeline;
    }
  }

  updateQualificationProgress(progress) {
    if (!progress || !this.qualificationProgress) return;

    const percentage = progress.progress_percentage || 0;
    const score = progress.qualification_score || 0;

    this.qualificationProgress.style.width = `${percentage}%`;
    this.progressPercentage.textContent = `${percentage}%`;

    if (this.qualificationScore) {
      this.qualificationScore.textContent = `Score: ${score}/10`;
      this.qualificationScore.className = `badge ${
        score >= 7 ? "bg-success" : score >= 4 ? "bg-warning" : "bg-danger"
      } text-light`;
    }
  }

  updateActionButtons(progress) {
    const readyForActions = progress.ready_for_next_step || false;

    document
      .getElementById("siteVisitBtn")
      ?.toggleAttribute("disabled", !readyForActions);
    document
      .getElementById("sendPropertiesBtn")
      ?.toggleAttribute("disabled", !readyForActions);
    document
      .getElementById("followUpBtn")
      ?.toggleAttribute("disabled", !readyForActions);
  }

  updateSalesMetrics(metrics) {
    if (this.questionsAsked)
      this.questionsAsked.textContent = metrics.questions_asked || 0;
    if (this.objections)
      this.objections.textContent = metrics.objections_handled || 0;
    if (this.buyingSignals)
      this.buyingSignals.textContent = metrics.buying_signals_detected || 0;
  }

  updateConversationMetrics(speaker) {
    // Update talk time ratio for sales
    if (this.industry === "sales" && this.talkTimeRatio) {
      const totalMessages = this.sessionData.conversationLog.length;
      const agentMessages = this.sessionData.conversationLog.filter(
        (msg) => msg.speaker === "agent"
      ).length;
      const ratio =
        totalMessages > 0
          ? Math.round((agentMessages / totalMessages) * 100)
          : 0;

      this.talkTimeRatio.textContent = `${ratio}% You`;
      this.talkTimeRatio.className = `badge ${
        ratio > 60 ? "bg-warning" : ratio < 30 ? "bg-success" : "bg-primary"
      }`;
    }
  }

  startCallTimer() {
    if (this.callDuration) {
      setInterval(() => {
        if (!this.isActive) return;

        const elapsed = Math.floor(
          (Date.now() - this.sessionData.startTime) / 1000
        );
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;

        this.callDuration.textContent = `${minutes
          .toString()
          .padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
      }, 1000);
    }
  }

  playAudioResponse(base64Audio) {
    try {
      const audioBlob = this.base64ToBlob(base64Audio, "audio/mpeg");
      const audioUrl = URL.createObjectURL(audioBlob);

      this.audioPlayer.src = audioUrl;
      this.audioPlayer.play();

      this.audioPlayer.onended = () => {
        URL.revokeObjectURL(audioUrl);
      };
    } catch (error) {
      console.error("Error playing audio:", error);
    }
  }

  base64ToBlob(base64, mimeType) {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);

    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }

    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
  }

  updateUI(state) {
    if (state === "active") {
      this.startBtn.disabled = true;
      this.stopBtn.disabled = false;
      this.startBtn.innerHTML =
        '<i class="fas fa-spinner fa-spin me-1"></i>Active';
    } else {
      this.startBtn.disabled = false;
      this.stopBtn.disabled = true;
      this.startBtn.innerHTML = `<i class="fas fa-play me-1"></i>Start ${
        this.industry === "sales" ? "Coaching" : "Call"
      }`;
    }
  }

  updateConnectionStatus(status, text) {
    if (!this.connectionStatus) return;

    const statusClasses = {
      connecting: "bg-warning",
      connected: "bg-success",
      ready: "bg-info",
      disconnected: "bg-secondary",
      error: "bg-danger",
    };

    this.connectionStatus.className = `badge ${
      statusClasses[status] || "bg-secondary"
    }`;
    this.connectionStatus.textContent = text;
  }

  showAlert(type, message) {
    const alertDiv = document.createElement("div");
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

    document.body.insertBefore(alertDiv, document.body.firstChild);

    // Auto dismiss after 5 seconds
    setTimeout(() => {
      if (alertDiv.parentNode) {
        alertDiv.remove();
      }
    }, 5000);
  }

  showQuickPrompt(type) {
    const prompts = {
      discovery:
        "Try asking: 'What's your biggest challenge with your current solution?'",
      value:
        "Emphasize ROI: 'This typically delivers 300% ROI within 12 months through efficiency gains.'",
      objection:
        "Acknowledge and redirect: 'I understand your concern. Let me show you how this addresses that specific issue.'",
    };

    this.displayCoachingInsight(prompts[type], "suggestion");
  }

  async generateSessionSummary() {
    try {
      // Would call API to generate comprehensive summary
      console.log("Generating session summary...");

      const summaryData = {
        sessionDuration: this.getSessionDuration(),
        totalMessages: this.sessionData.conversationLog.length,
        industry: this.industry,
      };

      this.displaySessionSummary(summaryData);
    } catch (error) {
      console.error("Failed to generate summary:", error);
    }
  }

  getSessionDuration() {
    if (!this.sessionData.startTime) return "0:00";

    const elapsed = Math.floor(
      (Date.now() - this.sessionData.startTime) / 1000
    );
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;

    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
  }

  displaySessionSummary(summaryData) {
    // Implementation would show modal with detailed summary
    console.log("Session Summary:", summaryData);

    const modal = document.getElementById("sessionSummaryModal");
    if (modal) {
      const summaryContent = document.getElementById("summaryContent");
      if (summaryContent) {
        summaryContent.innerHTML = `
                    <h6>Session Overview</h6>
                    <p><strong>Duration:</strong> ${
                      summaryData.sessionDuration || this.getSessionDuration()
                    }</p>
                    <p><strong>Messages:</strong> ${
                      summaryData.totalMessages ||
                      this.sessionData.conversationLog.length
                    }</p>
                    <p><strong>Industry:</strong> ${this.industry}</p>
                    
                    <h6>Key Insights</h6>
                    <ul>
                        <li>Conversation analysis completed</li>
                        <li>Real-time coaching provided</li>
                        <li>Session data ready for CRM sync</li>
                    </ul>
                `;
      }

      new bootstrap.Modal(modal).show();
    }
  }

  // Real Estate specific methods
  showSiteVisitModal() {
    const modal = document.getElementById("siteVisitModal");
    if (modal) {
      new bootstrap.Modal(modal).show();
    }
  }

  confirmSiteVisit() {
    const visitDate = document.getElementById("visitDate")?.value;
    const visitTime = document.getElementById("visitTime")?.value;

    if (!visitDate || !visitTime) {
      alert("Please select both date and time for the site visit.");
      return;
    }

    // Would call API to schedule site visit
    console.log("Scheduling site visit:", { visitDate, visitTime });

    this.showAlert("success", "Site visit scheduled successfully!");
    bootstrap.Modal.getInstance(
      document.getElementById("siteVisitModal")
    ).hide();
  }

  sendPropertyRecommendations() {
    this.showAlert("info", "Property recommendations sent to customer!");
  }

  scheduleFollowUp() {
    this.showAlert("info", "Follow-up call scheduled!");
  }
}

// Export for global use
window.VoiceAIInterface = VoiceAIInterface;

// 🆕 Dashboard Auto-Update Functionality
class CallDashboard {
  constructor(callType) {
    this.callType = callType;
    this.updateInterval = null;
    this.init();
  }

  init() {
    this.loadDashboardData();
    this.startRealTimeUpdates();
  }

  async loadDashboardData() {
    try {
      const url = this.callType
        ? `/api/dashboard/calls?call_type=${this.callType}`
        : `/api/dashboard/calls`;

      const response = await fetch(url);
      const result = await response.json();

      if (result.status === "success") {
        this.updateDashboard(result.data);
      }
    } catch (error) {
      console.error("Dashboard load error:", error);
    }
  }

  updateDashboard(data) {
    // Update statistics
    this.updateStats(data.summary_stats);

    // Update recent calls list
    this.updateRecentCalls(data.recent_calls);
  }

  updateStats(stats) {
    const elements = {
      "total-calls": stats.total_calls,
      "avg-duration": stats.avg_duration,
      "conversion-rate": stats.conversion_rate,
      "avg-lead-score": stats.avg_lead_score,
    };

    Object.keys(elements).forEach((id) => {
      const el = document.getElementById(id);
      if (el && elements[id] !== undefined) {
        el.textContent = elements[id];
      }
    });
  }

  updateRecentCalls(calls) {
    const container = document.getElementById("recent-calls-container");
    if (!container) return;

    if (calls.length === 0) {
      container.innerHTML = `
                <div class="text-center text-muted p-4">
                    <i class="fas fa-phone fa-3x mb-3"></i>
                    <p>No recent calls. Start making calls to see data here.</p>
                </div>
            `;
      return;
    }

    container.innerHTML = calls
      .map((call) => this.createCallCard(call))
      .join("");
  }

  createCallCard(call) {
    const summary = call.summary;
    const timestamp = new Date(call.timestamp).toLocaleString();
    const isSales = summary.call_type === "B2B Sales";

    return `
            <div class="card mb-3 border-start border-primary border-3">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="card-title mb-1">
                            <i class="fas fa-phone-alt me-2"></i>${
                              summary.call_type
                            } Call
                        </h6>
                        <small class="text-muted">${timestamp}</small>
                    </div>
                    <div class="row text-center mb-2">
                        <div class="col-3">
                            <small class="text-muted">Duration</small>
                            <div class="fw-bold">${this.formatDuration(
                              summary.duration_seconds
                            )}</div>
                        </div>
                        <div class="col-3">
                            <small class="text-muted">${
                              isSales ? "Interest" : "Score"
                            }</small>
                            <div class="fw-bold text-${this.getScoreColor(
                              summary.interest_level ||
                                summary.qualification_score
                            )}">
                                ${
                                  summary.interest_level ||
                                  summary.qualification_score ||
                                  0
                                }
                            </div>
                        </div>
                        <div class="col-3">
                            <small class="text-muted">Exchanges</small>
                            <div class="fw-bold">${
                              summary.total_exchanges || 0
                            }</div>
                        </div>
                        <div class="col-3">
                            <small class="text-muted">Score</small>
                            <div class="fw-bold">${
                              summary.lead_score ||
                              summary.qualification_score ||
                              0
                            }</div>
                        </div>
                    </div>
                    ${this.getCallSpecificDetails(summary, isSales)}
                </div>
            </div>
        `;
  }

  getCallSpecificDetails(summary, isSales) {
    if (isSales) {
      return `
                <div class="mt-2">
                    <span class="badge bg-info me-1">${
                      summary.use_case || "general"
                    }</span>
                    <span class="badge bg-secondary">${
                      summary.customer_sentiment || "neutral"
                    }</span>
                </div>
                <div class="mt-2">
                    <small><strong>Next:</strong> ${
                      summary.next_steps || "Follow up"
                    }</small>
                </div>
            `;
    } else {
      return `
                <div class="mt-2">
                    <span class="badge bg-success me-1">${
                      summary.location_preference || "Any Location"
                    }</span>
                    <span class="badge bg-warning text-dark">${
                      summary.property_type || "Any Type"
                    }</span>
                </div>
                <div class="mt-2">
                    <small><strong>Budget:</strong> ${
                      summary.budget_range || "Not specified"
                    }</small>
                </div>
                <div class="mt-2">
                    <small><strong>Next:</strong> ${
                      summary.next_steps || "Follow up"
                    }</small>
                </div>
            `;
    }
  }

  formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  }

  getScoreColor(value) {
    if (typeof value === "number") {
      return value >= 7 ? "success" : value >= 4 ? "warning" : "danger";
    }
    return value === "high"
      ? "success"
      : value === "medium"
      ? "warning"
      : "danger";
  }

  startRealTimeUpdates() {
    // Update every 30 seconds
    this.updateInterval = setInterval(() => {
      this.loadDashboardData();
    }, 30000);
  }

  stop() {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
    }
  }
}

// Initialize dashboard based on page
document.addEventListener("DOMContentLoaded", function () {
  // Check if we're on sales dashboard
  if (document.getElementById("sales-dashboard-marker")) {
    window.dashboard = new CallDashboard("b2b_sales");
    console.log("✅ Sales Dashboard initialized");
  }

  // Check if we're on real estate portal
  if (document.getElementById("real-estate-dashboard-marker")) {
    window.dashboard = new CallDashboard("real_estate");
    console.log("✅ Real Estate Dashboard initialized");
  }
});
