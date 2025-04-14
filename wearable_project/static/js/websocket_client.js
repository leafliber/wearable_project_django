/**
 * WebSocket Client for Surgical Workflow Visualization
 * This module handles the WebSocket connection to the Django backend,
 * processing the incoming video frames and surgical phase data
 */

class SurgicalWorkflowClient {
    constructor(options = {}) {
        this.wsUrl = options.wsUrl || 'ws://' + window.location.host + '/ws/stream/';
        this.onVideoUpdate = options.onVideoUpdate || (() => {});
        this.onPhaseUpdate = options.onPhaseUpdate || (() => {});
        this.onConnectionChange = options.onConnectionChange || (() => {});
        this.onError = options.onError || (() => {});
        this.autoReconnect = options.autoReconnect !== false;
        this.reconnectDelay = options.reconnectDelay || 2000;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.reconnectAttempts = 0;
        
        this.ws = null;
        this.connected = false;
        this.lastPhase = null;
        this.phaseHistory = [];
        this.maxHistoryLength = options.maxHistoryLength || 60; // 1 minute at 1 data point per second
    }
    
    /**
     * Connect to the WebSocket server
     */
    connect() {
        if (this.ws) {
            this.disconnect();
        }
        
        try {
            console.log("Connecting to WebSocket at:", this.wsUrl);
            this.ws = new WebSocket(this.wsUrl);
            this.initEventHandlers();
        } catch (error) {
            this.onError(error);
            this.scheduleReconnect();
        }
    }
    
    /**
     * Initialize WebSocket event handlers
     */
    initEventHandlers() {
        this.ws.onopen = () => {
            this.connected = true;
            this.reconnectAttempts = 0;
            this.onConnectionChange(true);
            console.log('WebSocket connection established');
        };
        
        this.ws.onmessage = (event) => {
            this.handleMessage(event);
        };
        
        this.ws.onclose = () => {
            this.connected = false;
            this.onConnectionChange(false);
            console.log('WebSocket connection closed');
            this.scheduleReconnect();
        };
        
        this.ws.onerror = (error) => {
            this.onError(error);
            console.error('WebSocket error:', error);
        };
    }
    
    /**
     * Handle incoming WebSocket messages
     */
    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            
            // Process video frame data
            if (data.image) {
                this.onVideoUpdate(data.image);
            }
            
            // Process surgical phase data
            if (data.stage) {
                this.lastPhase = data.stage;
                
                // Add to phase history
                const historyEntry = {
                    timestamp: new Date(),
                    phase: data.stage,
                    confidences: data.confidences || [],
                    inferenceTime: data.inference_time || 0,
                    elapsedTime: data.elapsed_time || 0
                };
                
                this.phaseHistory.push(historyEntry);
                
                // Trim history if it exceeds max length
                if (this.phaseHistory.length > this.maxHistoryLength) {
                    this.phaseHistory.shift();
                }
                
                this.onPhaseUpdate(
                    data.stage, 
                    data.confidences || [], 
                    this.phaseHistory, 
                    data.inference_time || 0,
                    data.elapsed_time || 0
                );
            }
        } catch (error) {
            console.error('Error processing message:', error);
            this.onError(error);
        }
    }
    
    /**
     * Schedule a reconnection attempt
     */
    scheduleReconnect() {
        if (this.autoReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay);
        } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached. Giving up.');
        }
    }
    
    /**
     * Disconnect from the WebSocket server
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
            this.connected = false;
        }
    }
    
    /**
     * Get the current connection status
     */
    isConnected() {
        return this.connected;
    }
    
    /**
     * Get the phase history
     */
    getPhaseHistory() {
        return [...this.phaseHistory];
    }
    
    /**
     * Get the current phase
     */
    getCurrentPhase() {
        return this.lastPhase;
    }
} 