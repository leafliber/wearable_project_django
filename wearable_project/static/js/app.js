/**
 * Main application file for the Surgical Workflow Visualization
 * This initializes the WebSocket client and coordinates the UI updates
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const videoElement = document.getElementById('video-feed');
    const phaseIndicator = document.getElementById('current-phase');
    const confidenceBars = document.querySelectorAll('.confidence-value');
    const confidenceLabels = document.querySelectorAll('.confidence-label');
    const phaseHistoryChart = document.getElementById('phaseHistoryChart');
    const connectionStatus = document.getElementById('connection-status');
    const timelineElement = document.querySelector('.timeline');
    const latencyElement = document.getElementById('latency-value');
    const frameRateElement = document.getElementById('frame-rate');
    const elapsedTimeElement = document.getElementById('elapsed-time');
    
    // Phase names and colors mapping
    const phaseConfig = {
        phases: [
            'additional_injection',
            'circumcision',
            'installation',
            'marking',
            'submucosal_dissection',
            'submucosal_injection'
        ],
        colors: ['#E1BEE7', '#CE93D8', '#BA68C8', '#AB47BC', '#9C27B0', '#8E24AA']
    };
    
    // Initialize Chart.js for phase confidence history
    let phaseHistoryChartInstance;
    let frameCount = 0;
    let lastFrameTime = Date.now();
    let frameRateCalcInterval;
    
    // Initialize the application
    function initApp() {
        console.log("Initializing application...");
        initCharts();
        initWebSocketClient();
        startFrameRateCalculation();
    }
    
    // Initialize Chart.js components
    function initCharts() {
        if (!phaseHistoryChart) {
            console.error("Phase history chart element not found");
            return;
        }
        
        const ctx = phaseHistoryChart.getContext('2d');
        phaseHistoryChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: Array(10).fill(''),
                datasets: [{
                    label: 'Confidence History',
                    data: Array(10).fill(0),
                    borderColor: '#9c27b0',
                    tension: 0.3,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Confidence History (Last Minute)'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Confidence (%)'
                        }
                    }
                }
            }
        });
    }
    
    // Calculate and update frame rate
    function startFrameRateCalculation() {
        frameRateCalcInterval = setInterval(() => {
            const now = Date.now();
            const elapsed = now - lastFrameTime;
            if (elapsed > 0) {
                const fps = Math.round((frameCount / elapsed) * 1000);
                if (frameRateElement) {
                    frameRateElement.textContent = `${fps} FPS`;
                }
                frameCount = 0;
                lastFrameTime = now;
            }
        }, 1000);
    }
    
    // Initialize the WebSocket client
    function initWebSocketClient() {
        console.log("Initializing WebSocket client...");
        const client = new SurgicalWorkflowClient({
            onVideoUpdate: updateVideoFeed,
            onPhaseUpdate: updatePhase,
            onConnectionChange: updateConnectionStatus,
            onError: handleError
        });
        
        client.connect();
        
        // Make client accessible globally for debugging
        window.surgicalClient = client;
    }
    
    // Update the video feed with a new base64 image
    function updateVideoFeed(base64ImageData) {
        if (!videoElement) {
            console.error("Video element not found");
            return;
        }
        videoElement.src = 'data:image/jpeg;base64,' + base64ImageData;
        frameCount++;
    }
    
    // Format time in MM:SS format
    function formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    
    // Update the current phase information and confidence bars
    function updatePhase(phase, confidences, phaseHistory, inferenceTime, elapsedTime) {
        // Update the main phase indicator
        if (phaseIndicator) {
            phaseIndicator.textContent = 'Current Phase: ' + formatPhaseName(phase);
        }
        
        // Update confidence bars for each phase
        if (confidenceBars && confidenceBars.length > 0) {
            confidences.forEach((confidence, index) => {
                if (index < confidenceBars.length) {
                    const bar = confidenceBars[index];
                    bar.style.width = confidence + '%';
                    bar.textContent = confidence.toFixed(1) + '%';
                    
                    // Update labels if they exist
                    if (confidenceLabels && index < confidenceLabels.length) {
                        confidenceLabels[index].textContent = formatPhaseName(phaseConfig.phases[index]);
                    }
                }
            });
        }
        
        // Update elapsed time if available
        if (elapsedTimeElement && phaseHistory && phaseHistory.length > 0) {
            const lastEntry = phaseHistory[phaseHistory.length - 1];
            if (lastEntry.elapsedTime) {
                elapsedTimeElement.textContent = formatTime(lastEntry.elapsedTime);
            }
        }
        
        // Update latency display
        if (latencyElement && inferenceTime) {
            latencyElement.textContent = `${inferenceTime.toFixed(0)}ms`;
        }
        
        // Update the history chart
        updatePhaseHistoryChart(phase, confidences, phaseHistory);
        
        // Update the timeline
        updateTimeline(phaseHistory);
    }
    
    // Format phase name for display
    function formatPhaseName(phase) {
        return phase.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }
    
    // Update the phase history chart
    function updatePhaseHistoryChart(currentPhase, confidences, phaseHistory) {
        if (!phaseHistoryChartInstance) return;
        
        // Find the index of the current phase
        const phaseIndex = phaseConfig.phases.indexOf(currentPhase);
        if (phaseIndex === -1) return;
        
        // Get the confidence history for the current phase
        const confidenceHistory = phaseHistory.map(entry => {
            return entry.confidences[phaseIndex] || 0;
        });
        
        // Create time labels
        const labels = phaseHistory.map(entry => {
            const date = new Date(entry.timestamp);
            return date.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
        });
        
        // Update chart data
        phaseHistoryChartInstance.data.labels = labels;
        phaseHistoryChartInstance.data.datasets[0].data = confidenceHistory;
        phaseHistoryChartInstance.data.datasets[0].label = `${formatPhaseName(currentPhase)} Confidence`;
        phaseHistoryChartInstance.data.datasets[0].borderColor = phaseConfig.colors[phaseIndex] || '#9c27b0';
        phaseHistoryChartInstance.update();
    }
    
    // Update the timeline visualization
    function updateTimeline(phaseHistory) {
        if (!timelineElement || !phaseHistory || phaseHistory.length === 0) return;
        
        // Clear existing segments
        timelineElement.innerHTML = '';
        
        // Find unique phases in the history
        const uniquePhases = [];
        const phaseRanges = [];
        
        let currentPhase = null;
        let startIndex = 0;
        
        // Create phase segments
        phaseHistory.forEach((entry, index) => {
            if (entry.phase !== currentPhase) {
                if (currentPhase !== null) {
                    phaseRanges.push({
                        phase: currentPhase,
                        start: startIndex,
                        end: index - 1
                    });
                }
                currentPhase = entry.phase;
                startIndex = index;
                
                if (!uniquePhases.includes(currentPhase)) {
                    uniquePhases.push(currentPhase);
                }
            }
            
            if (index === phaseHistory.length - 1 && currentPhase !== null) {
                phaseRanges.push({
                    phase: currentPhase,
                    start: startIndex,
                    end: index
                });
            }
        });
        
        // Create HTML elements for each phase range
        phaseRanges.forEach(range => {
            const phaseIndex = phaseConfig.phases.indexOf(range.phase);
            const width = ((range.end - range.start + 1) / phaseHistory.length) * 100;
            const left = (range.start / phaseHistory.length) * 100;
            
            const segmentElement = document.createElement('div');
            segmentElement.className = 'timeline-segment';
            segmentElement.style.left = left + '%';
            segmentElement.style.width = width + '%';
            segmentElement.style.backgroundColor = phaseConfig.colors[phaseIndex] || '#888';
            segmentElement.textContent = formatPhaseName(range.phase);
            
            timelineElement.appendChild(segmentElement);
        });
        
        // Add a marker for the current position
        const markerElement = document.createElement('div');
        markerElement.className = 'phase-marker';
        markerElement.style.left = '100%';
        timelineElement.appendChild(markerElement);
    }
    
    // Update the connection status display
    function updateConnectionStatus(isConnected) {
        if (connectionStatus) {
            connectionStatus.textContent = isConnected ? 'Connected' : 'Disconnected';
            connectionStatus.className = isConnected ? 
                'badge bg-success' : 
                'badge bg-danger';
        }
    }
    
    // Handle WebSocket errors
    function handleError(error) {
        console.error('WebSocket error:', error);
        // Show error notification
        alert('Connection error: ' + error.message);
    }
    
    // Initialize when DOM is loaded
    initApp();
}); 