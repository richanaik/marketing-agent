/**
 * API Integration for Full-Funnel Marketing Agent
 */

const BASE_URL = 'http://localhost:8080';

class ApiService {
    constructor() {
        this.pollingInterval = null;
    }

    /**
     * Show a friendly error message in the UI instead of raw console errors.
     */
    showError(message) {
        // Ideally this would trigger a toast or styled modal in the UI
        alert(`We encountered an issue: ${message}\nPlease try again.`);
    }

    /**
     * Submit the intake brief to start a new campaign
     * POST to http://localhost:8080/api/run
     */
    async submitIntakeBrief(formData) {
        try {
            const response = await fetch(`${BASE_URL}/api/run`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    agent: "supervisor",
                    intake_brief: formData
                })
            });

            if (!response.ok) {
                throw new Error(`Server returned status ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            this.showError("Failed to submit intake brief.");
            return null;
        }
    }

    /**
     * Get the current status of a session
     * GET http://localhost:8080/api/session/{sessionId}/status
     */
    async getSessionStatus(sessionId) {
        try {
            const response = await fetch(`${BASE_URL}/api/session/${sessionId}/status`);
            
            if (!response.ok) {
                throw new Error(`Server returned status ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            this.showError("Failed to fetch session status.");
            return null;
        }
    }

    /**
     * Submit a decision for a HITL checkpoint
     * POST http://localhost:8080/api/session/{sessionId}/checkpoint
     */
    async submitCheckpointDecision(sessionId, checkpoint, decision, feedback) {
        try {
            const response = await fetch(`${BASE_URL}/api/session/${sessionId}/checkpoint`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    checkpoint: checkpoint,
                    decision: decision,
                    feedback: feedback
                })
            });

            if (!response.ok) {
                throw new Error(`Server returned status ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            this.showError("Failed to submit checkpoint decision.");
            return null;
        }
    }

    /**
     * Fetch final outputs for a completed campaign
     * GET http://localhost:8080/api/session/{sessionId}/outputs
     */
    async getOutputs(sessionId) {
        try {
            const response = await fetch(`${BASE_URL}/api/session/${sessionId}/outputs`);
            
            if (!response.ok) {
                throw new Error(`Server returned status ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            this.showError("Failed to fetch campaign outputs.");
            return null;
        }
    }

    /**
     * Start polling the session status every 3 seconds
     */
    startPolling(sessionId) {
        this.stopPolling(); // Clear any existing polling
        this.pollingInterval = setInterval(async () => {
            const data = await this.getSessionStatus(sessionId);

            if (!data) {
                this.stopPolling();
                if (typeof app !== 'undefined' && typeof app.showError === 'function') {
                    app.showError('Lost connection to the backend. Is it still running?');
                }
                return;
            }

            const { overall_status, current_checkpoint, agents } = data;

            // Always sync agent cards on every tick, regardless of overall_status
            if (typeof app !== 'undefined' && typeof app.syncAgentsFromBackend === 'function') {
                app.syncAgentsFromBackend(agents);
            }

            // Stop polling on these specific terminal/wait states
            if (
                overall_status === "complete" ||
                overall_status === "failed" ||
                overall_status === "waiting_for_checkpoint"
            ) {
                this.stopPolling();
            }

            // Trigger HITL UI if we are waiting for a checkpoint
            if (overall_status === "waiting_for_checkpoint") {
                if (typeof app !== 'undefined' && typeof app.showCheckpointPanel === 'function') {
                    app.showCheckpointPanel(current_checkpoint);
                }
            }

            // Show final outputs when complete
            if (overall_status === "complete") {
                if (typeof app !== 'undefined' && typeof app.showOutputsPanel === 'function') {
                    const outputs = await this.getOutputs(sessionId);
                    app.showOutputsPanel(outputs);
                }
            }

            // Show error if the pipeline failed
            if (overall_status === "failed") {
                if (typeof app !== 'undefined' && typeof app.showError === 'function') {
                    app.showError('The pipeline encountered an error. Check the backend terminal for details.');
                }
            }

        }, 3000);
    }
    /**
     * Stop the polling loop
     */
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }
}

// Export the API service
const api = new ApiService();
window.api = api;
