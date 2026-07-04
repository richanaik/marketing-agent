/**
 * Full-Funnel Marketing Agent - App Logic
 */

class App {
    constructor() {
        this.currentScreen = 'landing';
        this.screens = ['landing', 'intake', 'dashboard', 'hitl', 'outputs'];
        this.sessionId = null;
        this.currentCheckpoint = null;

        this.agents = [
            { id: 'agent-intake', name: 'Intake Processing', status: 'pending' },
            { id: 'agent-seo', name: 'SEO/AEO Strategy', status: 'pending' },
            { id: 'agent-google', name: 'Google Ads', status: 'pending' },
            { id: 'agent-meta', name: 'Meta Ads', status: 'pending' },
            { id: 'agent-copy', name: 'Copywriter', status: 'pending' },
            { id: 'agent-visual', name: 'Visual Creative', status: 'pending' }
        ];

        // Maps backend agent ids -> index in this.agents
        this.backendAgentMap = {
            'seo_agent': 1,
            'google_ads_agent': 2,
            'meta_ads_agent': 3,
            'copywriter_agent': 4,
            'visual_agent': 5
            // llm_judge has no card — handled separately at checkpoint 3
        };

        this.checkpointMeta = {
            1: {
                title: 'Review Strategy Bundle',
                desc: 'Please review the SEO, Google Ads, and Meta Ads strategy before we move to creative production.'
            },
            2: {
                title: 'Review Creative Bundle',
                desc: 'Please review the ad copy and visual concepts before evaluation.'
            },
            3: {
                title: 'Review Evaluation & Approve Delivery',
                desc: 'Please review the LLM Judge score and approve final delivery.'
            }
        };

        this.init();
    }

    init() {
        this.renderAgentGrid();
    }

    navigateTo(screenId) {
        if (!this.screens.includes(screenId)) return;

        const currentEl = document.getElementById(`screen-${this.currentScreen}`);
        if (currentEl) {
            currentEl.classList.remove('active');
            setTimeout(() => {
                currentEl.style.display = 'none';
            }, 400);
        }

        this.currentScreen = screenId;
        const newEl = document.getElementById(`screen-${screenId}`);
        if (newEl) {
            setTimeout(() => {
                newEl.style.display = 'block';
                void newEl.offsetWidth;
                newEl.classList.add('active');
            }, 410);
        }
    }

    addUrlRow() {
        const container = document.getElementById('dynamic-url-container');
        const row = document.createElement('div');
        row.className = 'dynamic-row';
        row.innerHTML = `
            <input type="url" class="form-control" placeholder="https://" required>
            <select class="form-control">
                <option value="homepage">Homepage</option>
                <option value="landing">Landing Page</option>
                <option value="product">Product Page</option>
            </select>
        `;
        container.appendChild(row);
    }

    async submitIntake(e) {
        e.preventDefault();

        const formData = {
            business_name: document.querySelector('[name="business_name"]')?.value || document.querySelectorAll('input')[0]?.value || '',
            services: document.querySelector('[name="services"]')?.value || '',
            service_areas: document.querySelector('[name="service_areas"]')?.value || '',
            target_customer: document.querySelector('[name="target_customer"]')?.value || '',
            unique_value_props: document.querySelector('[name="unique_value_props"]')?.value || '',
            monthly_budget: document.querySelector('[name="monthly_budget"]')?.value || '',
            campaign_goal: document.querySelector('[name="campaign_goal"]')?.value || '',
            user_email: document.querySelector('[name="user_email"]')?.value || '',
            competitors: document.querySelector('[name="competitors"]')?.value || '',
            page_urls: JSON.stringify(
    Array.from(document.querySelectorAll('#dynamic-url-container .dynamic-row')).map(row => {
        const urlInput = row.querySelector('input[type="url"]');
        const typeSelect = row.querySelector('select');
        return {
            url: urlInput ? urlInput.value : '',
            type: typeSelect ? typeSelect.value : 'homepage'
        };
    }).filter(item => item.url) // drop empty rows
)
        };

        // Reset UI before starting a fresh run
        this.agents.forEach((a, i) => this.updateAgentStatus(i, 'pending'));
        [1, 2, 3].forEach(i => this.updateCheckpoint(i, 'pending'));
        this.updateAgentStatus(0, 'running'); // intake counts as done once we get session_id

        this.navigateTo('dashboard');

        try {
            const result = await window.api.submitIntakeBrief(formData);

            if (result && result.session_id) {
                this.sessionId = result.session_id;
                this.updateAgentStatus(0, 'complete');
                window.api.startPolling(result.session_id);
            } else {
                console.error('No session_id returned from backend');
                this.simulateProcess(); // fallback only if backend totally fails
            }
        } catch (err) {
            console.error('Backend call failed:', err);
            this.simulateProcess(); // fallback only if backend totally fails
        }
    }

    /**
     * Called by api.js on every poll — keeps agent cards in sync with
     * the real backend status.
     */
    syncAgentsFromBackend(agentsFromBackend) {
        if (!Array.isArray(agentsFromBackend)) return;

        agentsFromBackend.forEach(agent => {
            const index = this.backendAgentMap[agent.id];
            if (index === undefined) return; // e.g. llm_judge — no card

            let uiStatus = 'pending';
            if (agent.status === 'completed') uiStatus = 'complete';
            else if (agent.status === 'running') uiStatus = 'running';
            else if (agent.status === 'failed') uiStatus = 'failed';
            else uiStatus = 'pending';

            this.updateAgentStatus(index, uiStatus);
        });
    }

    /**
     * Called by api.js when overall_status === 'waiting_for_checkpoint'.
     * This is the method api.js was already trying to call — it just
     * didn't exist before.
     */
    showCheckpointPanel(checkpointNumber) {
        this.currentCheckpoint = checkpointNumber;
        this.updateCheckpoint(checkpointNumber, 'review');

        const meta = this.checkpointMeta[checkpointNumber] || {
            title: `Checkpoint ${checkpointNumber}`,
            desc: 'Please review this stage before continuing.'
        };

        document.getElementById('review-title').textContent =
            `Checkpoint ${checkpointNumber}: ${meta.title}`;
        document.getElementById('review-desc').textContent = meta.desc;

        const links = document.getElementById('review-links');
        links.innerHTML = `
            <a href="#" class="drive-link" onclick="event.preventDefault()">
                <div class="drive-icon">D</div>
                <div>
                    <div style="font-weight: 500;">Session ${this.sessionId ? this.sessionId.slice(0, 8) : ''} — Outputs</div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary);">Needs Approval</div>
                </div>
            </a>
        `;

        this.navigateTo('hitl');
    }

    renderAgentGrid() {
        const grid = document.getElementById('agent-grid');
        grid.innerHTML = '';

        this.agents.forEach(agent => {
            const el = document.createElement('div');
            el.className = `agent-card glass-panel ${agent.status}`;
            el.id = agent.id;

            el.innerHTML = `
                <div>
                    <div class="agent-header">
                        <div class="agent-name">${agent.name}</div>
                        <div class="agent-status status-${agent.status}" id="${agent.id}-status-label">
                            ${agent.status}
                        </div>
                    </div>
                </div>
                <div class="agent-progress">
                    <div class="agent-progress-bar"></div>
                </div>
            `;
            grid.appendChild(el);
        });
    }

    updateAgentStatus(index, status) {
        if (index >= this.agents.length) return;

        this.agents[index].status = status;
        const card = document.getElementById(this.agents[index].id);
        const label = document.getElementById(`${this.agents[index].id}-status-label`);

        if (card && label) {
            card.className = `agent-card glass-panel ${status}`;
            label.className = `agent-status status-${status}`;
            label.textContent = status;
        }
    }

    updateCheckpoint(index, status) {
        const pill = document.getElementById(`checkpoint-${index}`);
        if (pill) {
            pill.className = `hitl-pill glass-panel ${status}`;
        }
    }

    toggleFeedback() {
        const section = document.getElementById('feedback-section');
        section.classList.toggle('open');
    }

    /**
     * Real approve/revise handler — calls the backend checkpoint API.
     * decision: 'approve' | 'revise'
     */
    async handleReviewDecision(decision) {
        const feedbackEl = document.getElementById('feedback-text');
        const feedback = feedbackEl ? feedbackEl.value : '';

        document.getElementById('feedback-section').classList.remove('open');

        if (!this.sessionId || !this.currentCheckpoint) {
            console.error('No active session or checkpoint — falling back to simulation');
            this.navigateTo('dashboard');
            return;
        }

        try {
            await window.api.submitCheckpointDecision(
                this.sessionId,
                this.currentCheckpoint,
                decision,
                feedback
            );

            this.updateCheckpoint(this.currentCheckpoint, decision === 'approve' ? 'approved' : 'revising');
            this.navigateTo('dashboard');

            // Resume polling — pipeline continues on backend after approval
            window.api.startPolling(this.sessionId);

        } catch (err) {
            console.error('Checkpoint decision failed:', err);
        }
    }

    /**
     * Called by api.js when overall_status === 'complete'
     */
    async showOutputsPanel(outputs) {
        this.navigateTo('outputs');
        // outputs = { eval_score, drive_files, summary }
        console.log('Final outputs:', outputs);
    }

    showError(message) {
        console.error(message);
        alert(message); // simple fallback — replace with a styled toast if desired
    }

    // ── Fallback simulation — only used if backend is unreachable ──
    simulateProcess() {
        this.agents.forEach((a, i) => this.updateAgentStatus(i, 'pending'));
        [1, 2, 3].forEach(i => this.updateCheckpoint(i, 'pending'));

        setTimeout(() => this.updateAgentStatus(0, 'running'), 1000);
        setTimeout(() => {
            this.updateAgentStatus(0, 'complete');
            this.updateAgentStatus(1, 'running');
        }, 3000);
        setTimeout(() => {
            this.updateAgentStatus(1, 'complete');
            this.showCheckpointPanel(1);
        }, 6000);
    }

    resetApp() {
        this.agents.forEach((a, i) => this.updateAgentStatus(i, 'pending'));
        [1, 2, 3].forEach(i => this.updateCheckpoint(i, 'pending'));
        document.getElementById('intake-form').reset();
        this.sessionId = null;
        this.currentCheckpoint = null;
        this.navigateTo('landing');
    }
}

// Initialize
const app = new App();