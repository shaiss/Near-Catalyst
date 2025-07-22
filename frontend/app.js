// NEAR Partnership Analysis Dashboard
class PartnershipDashboard {
    constructor() {
        this.projects = [];
        this.filteredProjects = [];
        this.currentView = 'cards';
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.loadData();
        this.renderDashboard();
    }

    setupEventListeners() {
        // View toggle
        document.getElementById('card-view').addEventListener('click', () => this.switchView('cards'));
        document.getElementById('table-view').addEventListener('click', () => this.switchView('table'));

        // Filters
        document.getElementById('score-filter').addEventListener('change', () => this.applyFilters());
        document.getElementById('search-filter').addEventListener('input', () => this.applyFilters());
        document.getElementById('refresh-btn').addEventListener('click', () => this.refreshData());

        // Modal
        document.getElementById('close-modal').addEventListener('click', () => this.closeModal());
        document.getElementById('project-modal').addEventListener('click', (e) => {
            if (e.target.id === 'project-modal') this.closeModal();
        });

        // Escape key to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.closeModal();
        });

        // Tab navigation
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('tab-btn') || e.target.closest('.tab-btn')) {
                const tabBtn = e.target.closest('.tab-btn') || e.target;
                const tabId = tabBtn.dataset.tab;
                this.switchTab(tabId);
            }
        });

        // Accordion functionality
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('accordion-header') || e.target.closest('.accordion-header')) {
                const header = e.target.closest('.accordion-header') || e.target;
                this.toggleAccordion(header);
            }
        });

        // Question overview card clicks
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('question-overview-card') || e.target.closest('.question-overview-card')) {
                const card = e.target.closest('.question-overview-card') || e.target;
                const questionId = card.dataset.questionId;
                this.expandQuestionAccordion(questionId);
            }
        });
    }

    async loadData() {
        try {
            this.showLoading(true);
            const response = await fetch('/api/projects');
            if (!response.ok) throw new Error('Failed to fetch data');
            
            this.projects = await response.json();
            this.filteredProjects = [...this.projects];
            this.showLoading(false);
        } catch (error) {
            console.error('Error loading data:', error);
            this.showError('Failed to load data. Please refresh the page.');
        }
    }

    async refreshData() {
        const refreshBtn = document.getElementById('refresh-btn');
        const icon = refreshBtn.querySelector('i');
        
        // Add spinning animation
        icon.style.animation = 'spin 1s linear infinite';
        refreshBtn.disabled = true;
        
        await this.loadData();
        this.renderDashboard();
        
        // Remove spinning animation
        setTimeout(() => {
            icon.style.animation = '';
            refreshBtn.disabled = false;
        }, 500);
    }

    showLoading(show) {
        const loading = document.getElementById('loading');
        const projectsGrid = document.getElementById('projects-grid');
        const projectsTable = document.getElementById('projects-table');

        if (show) {
            loading.style.display = 'block';
            projectsGrid.style.display = 'none';
            projectsTable.style.display = 'none';
        } else {
            loading.style.display = 'none';
        }
    }

    showError(message) {
        const loading = document.getElementById('loading');
        loading.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-circle" style="font-size: 3rem; color: #f44336; margin-bottom: 16px;"></i>
                <p>${message}</p>
            </div>
        `;
        this.showLoading(false);
    }

    renderDashboard() {
        this.updateStats();
        this.updateSummaryCards();
        this.renderProjects();
    }

    updateStats() {
        const totalProjects = this.projects.length;
        const avgScore = totalProjects > 0 
            ? (this.projects.reduce((sum, p) => sum + (p.total_score || 0), 0) / totalProjects).toFixed(1)
            : '0';

        document.getElementById('total-projects').textContent = totalProjects;
        document.getElementById('avg-score').textContent = avgScore;
    }

    updateSummaryCards() {
        const greenCount = this.projects.filter(p => (p.total_score || 0) >= 4).length;
        const midCount = this.projects.filter(p => (p.total_score || 0) >= 0 && (p.total_score || 0) < 4).length;
        const redCount = this.projects.filter(p => (p.total_score || 0) < 0).length;

        document.getElementById('green-count').textContent = greenCount;
        document.getElementById('mid-count').textContent = midCount;
        document.getElementById('red-count').textContent = redCount;
    }

    applyFilters() {
        const scoreFilter = document.getElementById('score-filter').value;
        const searchFilter = document.getElementById('search-filter').value.toLowerCase();

        this.filteredProjects = this.projects.filter(project => {
            // Score filter
            const score = project.total_score || 0;
            let scoreMatch = true;
            
            switch (scoreFilter) {
                case 'green':
                    scoreMatch = score >= 4;
                    break;
                case 'mid':
                    scoreMatch = score >= 0 && score < 4;
                    break;
                case 'red':
                    scoreMatch = score < 0;
                    break;
                default:
                    scoreMatch = true;
            }

            // Search filter
            const searchMatch = !searchFilter || 
                project.project_name.toLowerCase().includes(searchFilter) ||
                (project.slug && project.slug.toLowerCase().includes(searchFilter));

            return scoreMatch && searchMatch;
        });

        this.renderProjects();
    }

    switchView(view) {
        this.currentView = view;
        
        // Update button states
        document.getElementById('card-view').classList.toggle('active', view === 'cards');
        document.getElementById('table-view').classList.toggle('active', view === 'table');
        
        this.renderProjects();
    }

    renderProjects() {
        if (this.currentView === 'cards') {
            this.renderCardsView();
        } else {
            this.renderTableView();
        }
    }

    renderCardsView() {
        const grid = document.getElementById('projects-grid');
        const table = document.getElementById('projects-table');
        
        grid.style.display = 'grid';
        table.style.display = 'none';

        if (this.filteredProjects.length === 0) {
            grid.innerHTML = '<div class="no-results">No projects match your filters.</div>';
            return;
        }

        grid.innerHTML = this.filteredProjects.map(project => {
            const score = project.total_score || 0;
            const scoreClass = this.getScoreClass(score);
            const recommendation = this.getShortRecommendation(project.recommendation);
            
            return `
                <div class="project-card glass" onclick="dashboard.showProjectDetails('${project.project_name}')">
                    <div class="project-header">
                        <div>
                            <div class="project-name">${project.project_name}</div>
                            <div class="project-slug">${project.slug || ''}</div>
                        </div>
                        <div class="score-badge ${scoreClass}">
                            ${score >= 0 ? '+' : ''}${score}/6
                        </div>
                    </div>
                    <div class="project-recommendation">
                        ${recommendation}
                    </div>
                    <div class="project-meta">
                        <span>Updated: ${this.formatDate(project.created_at)}</span>
                        <span>Click to view details</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    renderTableView() {
        const grid = document.getElementById('projects-grid');
        const table = document.getElementById('projects-table');
        const tbody = document.getElementById('table-body');
        
        grid.style.display = 'none';
        table.style.display = 'block';

        if (this.filteredProjects.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">No projects match your filters.</td></tr>';
            return;
        }

        tbody.innerHTML = this.filteredProjects.map(project => {
            const score = project.total_score || 0;
            const scoreClass = this.getScoreClass(score);
            const recommendation = this.getShortRecommendation(project.recommendation);
            
            return `
                <tr>
                    <td>
                        <div>
                            <strong>${project.project_name}</strong>
                            <br><small style="opacity: 0.7;">${project.slug || ''}</small>
                        </div>
                    </td>
                    <td>
                        <span class="table-score ${scoreClass}">
                            ${score >= 0 ? '+' : ''}${score}/6
                        </span>
                    </td>
                    <td style="max-width: 300px;">${recommendation}</td>
                    <td>${this.formatDate(project.created_at)}</td>
                    <td>
                        <button class="view-btn" onclick="dashboard.showProjectDetails('${project.project_name}')">
                            View Details
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    getScoreClass(score) {
        if (score >= 4) return 'positive';
        if (score >= 0) return 'neutral';
        return 'negative';
    }

    getShortRecommendation(recommendation) {
        if (!recommendation) return 'No recommendation available';
        return recommendation.length > 120 
            ? recommendation.substring(0, 120) + '...'
            : recommendation;
    }

    formatDate(dateString) {
        if (!dateString) return 'Unknown';
        try {
            return new Date(dateString).toLocaleDateString();
        } catch {
            return 'Invalid date';
        }
    }

    async showProjectDetails(projectName) {
        const project = this.projects.find(p => p.project_name === projectName);
        if (!project) return;

        // Load detailed analysis
        try {
            const response = await fetch(`/api/project/${encodeURIComponent(projectName)}`);
            if (!response.ok) throw new Error('Failed to fetch project details');
            
            const details = await response.json();
            this.renderProjectModal(project, details);
        } catch (error) {
            console.error('Error loading project details:', error);
            this.renderProjectModal(project, null);
        }
    }

    renderProjectModal(project, details) {
        const modal = document.getElementById('project-modal');
        const score = project.total_score || 0;
        
        // Update modal content
        document.getElementById('modal-title').textContent = project.project_name;
        document.getElementById('modal-score').textContent = score;
        document.getElementById('modal-recommendation').textContent = 
            project.recommendation || 'No recommendation available';

        // Render questions overview grid
        this.renderQuestionsOverview(details?.question_analyses || []);
        
        // Render detailed questions accordion
        this.renderQuestionsAccordion(details?.question_analyses || []);

        // Render research summary
        document.getElementById('research-summary').innerHTML = 
            this.renderStructuredContent(details?.general_research, 'Research data not available');

        // Render final analysis
        document.getElementById('final-analysis').innerHTML = 
            this.renderStructuredContent(project.final_summary, 'Final analysis not available');

        // Reset to first tab
        this.switchTab('questions');

        // Show modal
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    renderQuestionsOverview(questionAnalyses) {
        const grid = document.getElementById('questions-grid');
        
        if (!questionAnalyses || questionAnalyses.length === 0) {
            grid.innerHTML = '<div class="no-data">No question analysis available</div>';
            return;
        }

        grid.innerHTML = questionAnalyses.map(q => {
            const scoreClass = this.getScoreClass(q.score);
            return `
                <div class="question-overview-card ${scoreClass}" data-question-id="${q.question_id}">
                    <div class="question-card-header">
                        <div class="question-card-title">Q${q.question_id}: ${this.getQuestionTitle(q.question_id)}</div>
                        <div class="question-card-score ${scoreClass}">
                            ${q.score >= 0 ? '+' : ''}${q.score}
                        </div>
                    </div>
                    <div class="question-card-confidence">Confidence: ${q.confidence}</div>
                </div>
            `;
        }).join('');
    }

    renderQuestionsAccordion(questionAnalyses) {
        const accordion = document.getElementById('questions-breakdown');
        
        if (!questionAnalyses || questionAnalyses.length === 0) {
            accordion.innerHTML = '<div class="no-data">No detailed analysis available</div>';
            return;
        }

        accordion.innerHTML = questionAnalyses.map(q => {
            const scoreClass = this.getScoreClass(q.score);
            return `
                <div class="accordion-item" data-question-id="${q.question_id}">
                    <div class="accordion-header ${scoreClass}">
                        <div class="accordion-title">Q${q.question_id}: ${this.getQuestionTitle(q.question_id)}</div>
                        <div class="accordion-meta">
                            <div class="accordion-score ${scoreClass}">
                                ${q.score >= 0 ? '+' : ''}${q.score}
                            </div>
                            <div class="accordion-toggle">
                                <i class="fas fa-chevron-down"></i>
                            </div>
                        </div>
                    </div>
                    <div class="accordion-content">
                        <div class="accordion-body">
                            <div style="margin-bottom: 12px;">
                                <strong>Confidence:</strong> ${q.confidence}
                            </div>
                            <div>${this.formatText(q.analysis || 'No detailed analysis available')}</div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    switchTab(tabId) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabId);
        });

        // Update tab panes
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.toggle('active', pane.id === `${tabId}-tab`);
        });
    }

    toggleAccordion(header) {
        const content = header.nextElementSibling;
        const isExpanded = header.classList.contains('expanded');

        if (isExpanded) {
            header.classList.remove('expanded');
            content.classList.remove('expanded');
        } else {
            header.classList.add('expanded');
            content.classList.add('expanded');
        }
    }

    expandQuestionAccordion(questionId) {
        // First switch to questions tab if not already active
        this.switchTab('questions');

        // Find and expand the accordion item
        setTimeout(() => {
            const accordionItem = document.querySelector(`[data-question-id="${questionId}"]`);
            if (accordionItem) {
                const header = accordionItem.querySelector('.accordion-header');
                const content = accordionItem.querySelector('.accordion-content');
                
                if (header && content) {
                    header.classList.add('expanded');
                    content.classList.add('expanded');
                    
                    // Scroll to the expanded item
                    accordionItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        }, 100); // Small delay to ensure tab switch completes
    }

    getQuestionTitle(questionId) {
        const titles = {
            1: 'Gap-Filler?',
            2: 'New Proof-Points?',
            3: 'One-Sentence Story?',
            4: 'Developer-Friendly?',
            5: 'Aligned Incentives?',
            6: 'Ecosystem Fit?'
        };
        return titles[questionId] || `Question ${questionId}`;
    }

    truncateText(text, maxLength) {
        if (!text) return '';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }

    formatText(text) {
        if (!text) return '';
        
        // Convert markdown-style formatting to HTML
        return text
            // Bold text **text** or __text__
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/__(.*?)__/g, '<strong>$1</strong>')
            // Italic text *text* or _text_
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/_(.*?)_/g, '<em>$1</em>')
            // Headers ### text
            .replace(/^### (.*$)/gm, '<h4>$1</h4>')
            .replace(/^## (.*$)/gm, '<h3>$1</h3>')
            .replace(/^# (.*$)/gm, '<h2>$1</h2>')
            // Code blocks ```code```
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            // Inline code `code`
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            // Line breaks
            .replace(/\n/g, '<br>')
            // Links [text](url)
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
            // Bullet points - item or * item
            .replace(/^[\-\*] (.*)$/gm, '<li>$1</li>')
            // Numbered lists 1. item
            .replace(/^\d+\. (.*)$/gm, '<li>$1</li>')
            // Wrap consecutive list items in ul tags
            .replace(/(<li>.*<\/li>)/g, '<ul>$1</ul>')
            .replace(/<\/ul>\s*<ul>/g, ''); // Remove duplicate ul tags
    }

    renderStructuredContent(data, fallback) {
        if (!data) return fallback;
        
        // If data is a string, just format it
        if (typeof data === 'string') {
            return this.formatText(data);
        }
        
        // If data is structured object from backend
        if (data && typeof data === 'object') {
            let html = '';
            
            // Add summary
            if (data.summary) {
                html += `<div class="content-summary">${this.formatText(data.summary)}</div>`;
            }
            
            // Add key points
            if (data.key_points && data.key_points.length > 0) {
                html += '<div class="key-points"><h5>Key Points:</h5><ul>';
                data.key_points.forEach(point => {
                    html += `<li>${this.formatText(point)}</li>`;
                });
                html += '</ul></div>';
            }
            
            // Add analysis sections
            if (data.analysis_sections && data.analysis_sections.length > 0) {
                html += '<div class="analysis-sections">';
                data.analysis_sections.forEach(section => {
                    html += `<div class="analysis-section">${this.formatText(section)}</div>`;
                });
                html += '</div>';
            }
            
            // If no structured content, show full text
            if (!html && data.full_text) {
                html = this.formatText(this.truncateText(data.full_text, 1000));
            }
            
            return html || fallback;
        }
        
        return fallback;
    }

    closeModal() {
        const modal = document.getElementById('project-modal');
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new PartnershipDashboard();
});

// Global error handler
window.addEventListener('error', (e) => {
    console.error('JavaScript error:', e.error);
});

// Handle online/offline status
window.addEventListener('online', () => {
    console.log('Connection restored');
});

window.addEventListener('offline', () => {
    console.log('Connection lost');
}); 