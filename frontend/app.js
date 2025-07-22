// NEAR Catalyst Framework Dashboard
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
            console.log(`🔍 Loading details for: ${projectName}`);
            const response = await fetch(`/api/project/${encodeURIComponent(projectName)}`);
            if (!response.ok) {
                console.error(`❌ API Error: ${response.status} ${response.statusText}`);
                throw new Error('Failed to fetch project details');
            }
            
            const details = await response.json();
            console.log('📊 Project Details Response:', details);
            console.log('🔬 Deep Research Available:', !!details.deep_research);
            
            this.renderProjectModal(project, details);
        } catch (error) {
            console.error('❌ Error loading project details:', error);
            this.renderProjectModal(project, null);
        }
    }

    renderProjectModal(project, details) {
        const modal = document.getElementById('project-modal');
        const score = project.total_score || 0;
        
        // Update modal title (in header) - just show "Project Details" instead of project name
        document.getElementById('modal-title').textContent = 'Project Details';
        
        // Update consolidated project header
        document.getElementById('modal-project-name').textContent = project.project_name;
        document.getElementById('modal-score').textContent = score;
        
        // Remove any existing research quality dashboard to prevent duplication
        const existingDashboard = document.querySelector('.research-quality-dashboard');
        if (existingDashboard) {
            existingDashboard.remove();
        }

        // Render consolidated project details and social links
        this.renderConsolidatedProjectDetails(project, details);
        
        // Render partnership assessment in decision tab
        this.renderPartnershipAssessmentDetailed(details?.question_analyses || []);
        
        // Render detailed questions accordion (for partnership evaluation tab)
        this.renderQuestionsAccordion(details?.question_analyses || []);

        // Render enhanced decision recommendation
        document.getElementById('decision-analysis').innerHTML = 
            this.renderDecisionRecommendation(project, details);

        // Render deep research if available  
        if (details?.deep_research) {
            this.renderDeepResearch(details.deep_research, details);
        } else {
            this.renderDeepResearchUnavailable(details);
        }

        // Reset to decision recommendation tab (now default first tab)
        this.switchTab('decision');

        // Show modal
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    async renderConsolidatedProjectDetails(project, details) {
        // Check if we have cached catalog data from backend
        const catalogData = details?.catalog_data;
        let projectData = null;
        
        if (catalogData && catalogData.cached) {
            console.log('✓ Using cached NEAR catalog data from backend');
            projectData = catalogData.full_data || catalogData;
        } else {
            console.log('⚠️ No cached catalog data, attempting direct API call...');
            
            try {
                // Fallback: Fetch project details from NEAR catalog directly
                const slug = project.slug || project.project_name.toLowerCase().replace(/\s+/g, '-');
                console.log(`🔍 Fallback: Fetching NEAR catalog data for slug: ${slug}`);
                
                const response = await fetch(`https://api.nearcatalog.org/project?pid=${encodeURIComponent(slug)}`);
                
                if (!response.ok) {
                    throw new Error(`NEAR Catalog API responded with ${response.status}`);
                }
                
                projectData = await response.json();
                console.log('📊 Fallback NEAR Catalog Data:', projectData);
                
            } catch (error) {
                console.warn('⚠️ Could not fetch NEAR catalog data:', error);
                projectData = null;
            }
        }
        
        // Update tagline
        const profile = projectData?.profile || {};
        const taglineElement = document.getElementById('modal-project-tagline');
        if (profile.tagline) {
            taglineElement.textContent = profile.tagline;
            taglineElement.style.display = 'block';
        } else {
            taglineElement.textContent = project.recommendation || 'No tagline available';
            taglineElement.style.display = 'block';
        }
        
        // Update dApp link if available
        const dappLinkContainer = document.getElementById('dapp-link-container');
        const dappLink = document.getElementById('dapp-link');
        // Hide dApp link box since we have globe icon in social links
        dappLinkContainer.style.display = 'none';
        
        // Populate consolidated project details
        const consolidatedDetails = document.getElementById('consolidated-project-details');
        let detailsHtml = this.formatConsolidatedProjectData(projectData, project, details);
        consolidatedDetails.innerHTML = detailsHtml;
        
        // Populate social links
        this.renderSocialLinks(profile);
    }

    formatConsolidatedProjectData(projectData, project, details) {
        let html = '<div class="project-details-grid-consolidated">';
        
        const profile = projectData?.profile || {};
        const catalogInfo = projectData || {};
        
        // Phase/Stage
        if (profile.phase) {
            html += `
                <div class="project-detail-item-consolidated">
                    <div class="project-detail-label">Phase</div>
                    <div class="project-detail-value">${profile.phase}</div>
                </div>
            `;
        } else if (catalogInfo.stage) {
            html += `
                <div class="project-detail-item-consolidated">
                    <div class="project-detail-label">Stage</div>
                    <div class="project-detail-value">${catalogInfo.stage}</div>
                </div>
            `;
        }
        
        // Category
        if (catalogInfo.category) {
            html += `
                <div class="project-detail-item-consolidated">
                    <div class="project-detail-label">Category</div>
                    <div class="project-detail-value">${catalogInfo.category}</div>
                </div>
            `;
        }
        
        // Founded/Created
        if (catalogInfo.founded) {
            html += `
                <div class="project-detail-item-consolidated">
                    <div class="project-detail-label">Founded</div>
                    <div class="project-detail-value">${catalogInfo.founded}</div>
                </div>
            `;
        }
        
        // Team Size
        if (catalogInfo.team_size) {
            html += `
                <div class="project-detail-item-consolidated">
                    <div class="project-detail-label">Team Size</div>
                    <div class="project-detail-value">${catalogInfo.team_size}</div>
                </div>
            `;
        }
        
        // Location
        if (catalogInfo.location) {
            html += `
                <div class="project-detail-item-consolidated">
                    <div class="project-detail-label">Location</div>
                    <div class="project-detail-value">${catalogInfo.location}</div>
                </div>
            `;
        }
        
        // Partnership Score
        html += `
            <div class="project-detail-item-consolidated">
                <div class="project-detail-label">Partnership Score</div>
                <div class="project-detail-value">${project.total_score || 0}/6</div>
            </div>
        `;
        
        // Analysis Date
        if (project.created_at) {
            html += `
                <div class="project-detail-item-consolidated">
                    <div class="project-detail-label">Analysis Date</div>
                    <div class="project-detail-value">${this.formatDate(project.created_at)}</div>
                </div>
            `;
        }
        
        html += '</div>';
        
        // Add description if available
        if (catalogInfo.description) {
            html += `
                <div class="project-description-consolidated" style="margin-top: 16px; padding: 16px; background: rgba(255, 255, 255, 0.05); border-radius: 8px; font-size: 0.85rem; line-height: 1.5; color: rgba(255, 255, 255, 0.9);">
                    ${this.formatText(catalogInfo.description.substring(0, 300))}${catalogInfo.description.length > 300 ? '...' : ''}
                </div>
            `;
        }
        
        return html;
    }

    renderSocialLinks(profile) {
        const socialContainer = document.getElementById('social-links-container');
        
        if (!socialContainer) {
            console.warn('Social links container not found');
            return;
        }

        // Clear existing content
        socialContainer.innerHTML = '';
        
        let socialLinksHtml = '';
        
        // Map of platforms to their specific icons
        const socialIconMap = {
            'discord': 'fab fa-discord',
            'github': 'fab fa-github', 
            'twitter': 'fab fa-twitter',
            'telegram': 'fab fa-telegram',
            'medium': 'fab fa-medium',
            'linkedin': 'fab fa-linkedin',
            'youtube': 'fab fa-youtube',
            'facebook': 'fab fa-facebook',
            'instagram': 'fab fa-instagram',
            'reddit': 'fab fa-reddit',
            'website': 'fas fa-globe',
            'blog': 'fas fa-blog',
            'docs': 'fas fa-book'
        };

        // From enhanced catalog data (profile.linktree)
        if (profile.linktree) {
            Object.entries(profile.linktree).forEach(([platform, url]) => {
                if (url && url.trim()) {
                    const iconClass = socialIconMap[platform.toLowerCase()] || 'fas fa-link';
                    socialLinksHtml += `
                        <a href="${url}" target="_blank" rel="noopener" class="social-icon ${platform.toLowerCase()}" title="${platform}">
                            <i class="${iconClass}"></i>
                        </a>
                    `;
                }
            });
        }
        
        // Add dApp link as globe icon if available
        if (profile.dapp) {
            socialLinksHtml += `
                <a href="${profile.dapp}" target="_blank" rel="noopener" class="social-icon dapp" title="dApp">
                    <i class="fas fa-globe"></i>
                </a>
            `;
        }

        // Show container and populate with grid items
        if (socialLinksHtml) {
            socialContainer.innerHTML = socialLinksHtml;
            socialContainer.style.display = 'grid';
        } else {
            socialContainer.style.display = 'none';
        }
    }

    renderQuestionsOverview(questionAnalyses) {
        const grid = document.getElementById('questions-grid');
        
        if (!questionAnalyses || questionAnalyses.length === 0) {
            grid.innerHTML = '<div class="no-data">No question analysis available</div>';
            return;
        }

        grid.innerHTML = questionAnalyses.map(q => {
            const scoreClass = this.getScoreClass(q.score);
            const qualityMetrics = this.calculateQuestionQuality(q);
            
            return `
                <div class="question-overview-card ${scoreClass}" data-question-id="${q.question_id}">
                    <div class="question-card-header">
                        <div class="question-card-title">Q${q.question_id}: ${this.getQuestionTitle(q.question_id)}</div>
                        <div class="question-card-score ${scoreClass}">
                            ${q.score >= 0 ? '+' : ''}${q.score}
                        </div>
                    </div>
                    <div class="question-card-confidence">Confidence: ${q.confidence}</div>
                    
                    <!-- Quality Indicators -->
                    <div class="quality-indicators">
                        <div class="quality-metric" title="Source diversity">
                            <i class="fas fa-link"></i>
                            <span>${qualityMetrics.sourceCount}</span>
                        </div>
                        <div class="quality-metric" title="Research depth">
                            <i class="fas fa-search"></i>
                            <span>${qualityMetrics.researchDepth}</span>
                        </div>
                        <div class="quality-metric" title="Analysis completeness">
                            <i class="fas fa-brain"></i>
                            <span>${qualityMetrics.analysisCompleteness}%</span>
                        </div>
                    </div>
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
            const sourceCount = q.sources ? q.sources.length : 0;
            
            return `
                <div class="accordion-item" data-question-id="${q.question_id}">
                    <div class="accordion-header ${scoreClass}">
                        <div class="accordion-title">
                            Q${q.question_id}: ${this.getQuestionTitle(q.question_id)}
                            <span class="research-indicator">
                                <i class="fas fa-search"></i>
                                ${sourceCount} sources
                            </span>
                        </div>
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
                            <!-- Research Context Section -->
                            <div class="research-context-section">
                                <div class="research-context-header" onclick="dashboard.toggleResearchContext(${q.question_id})">
                                    <span><i class="fas fa-microscope"></i> Research Context & Sources</span>
                                    <i class="fas fa-chevron-right research-context-toggle"></i>
                                </div>
                                <div class="research-context-content" id="research-context-${q.question_id}">
                                    <div class="research-context-body">
                                        ${this.renderQuestionResearchContext(q)}
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Analysis Section -->
                            <div class="analysis-section">
                                <div class="analysis-header">
                                    <span><i class="fas fa-brain"></i> AI Analysis</span>
                                    <span class="confidence-badge ${scoreClass}">
                                        Confidence: ${q.confidence}
                                    </span>
                                </div>
                                <div class="analysis-content">
                                    ${this.formatText(q.analysis || 'No detailed analysis available')}
                                </div>
                            </div>
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
        // CORRECTED: These must align with the 6 diagnostic questions from config/config.py
        const titles = {
            1: 'Gap-Filler?',
            2: 'New Proof-Points?', 
            3: 'Clear Story?',
            4: 'Shared Audience, Different Function?',
            5: 'Low-Friction Integration?',
            6: 'Hands-On Support?'
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
        let formatted = text
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
            // Links [text](url)
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

        // Handle markdown tables
        const lines = formatted.split('\n');
        const processedLines = [];
        let inTable = false;
        let tableRows = [];

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            
            // Check if this line looks like a table row (contains | characters)
            if (line.includes('|') && line.split('|').length >= 3) {
                if (!inTable) {
                    inTable = true;
                    tableRows = [];
                }
                
                // Parse table row
                const cells = line.split('|').map(cell => cell.trim()).filter(cell => cell !== '');
                
                // Skip separator rows (containing only hyphens, spaces, and pipes)
                if (!line.match(/^[\s\|\-\:]+$/)) {
                    tableRows.push(cells);
                }
            } else {
                // End of table - render it
                if (inTable && tableRows.length > 0) {
                    let tableHtml = '<table class="markdown-table">';
                    
                    // First row is header
                    if (tableRows.length > 0) {
                        tableHtml += '<thead><tr>';
                        tableRows[0].forEach(cell => {
                            tableHtml += `<th>${cell}</th>`;
                        });
                        tableHtml += '</tr></thead>';
                    }
                    
                    // Rest are body rows
                    if (tableRows.length > 1) {
                        tableHtml += '<tbody>';
                        for (let j = 1; j < tableRows.length; j++) {
                            tableHtml += '<tr>';
                            tableRows[j].forEach(cell => {
                                tableHtml += `<td>${cell}</td>`;
                            });
                            tableHtml += '</tr>';
                        }
                        tableHtml += '</tbody>';
                    }
                    
                    tableHtml += '</table>';
                    processedLines.push(tableHtml);
                    
                    inTable = false;
                    tableRows = [];
                }
                
                processedLines.push(line);
            }
        }
        
        // Handle table at end of text
        if (inTable && tableRows.length > 0) {
            let tableHtml = '<table class="markdown-table">';
            
            if (tableRows.length > 0) {
                tableHtml += '<thead><tr>';
                tableRows[0].forEach(cell => {
                    tableHtml += `<th>${cell}</th>`;
                });
                tableHtml += '</tr></thead>';
            }
            
            if (tableRows.length > 1) {
                tableHtml += '<tbody>';
                for (let j = 1; j < tableRows.length; j++) {
                    tableHtml += '<tr>';
                    tableRows[j].forEach(cell => {
                        tableHtml += `<td>${cell}</td>`;
                    });
                    tableHtml += '</tr>';
                }
                tableHtml += '</tbody>';
            }
            
            tableHtml += '</table>';
            processedLines.push(tableHtml);
        }

        // Rejoin lines and continue with other formatting
        formatted = processedLines.join('\n')
            // Line breaks
            .replace(/\n/g, '<br>')
            // Clean bullet points - handle common bullet formats without duplicating
            .replace(/^[\-\*\•]\s*(.*)$/gm, '<li>$1</li>')
            // Numbered lists 1. item
            .replace(/^\d+\.\s*(.*)$/gm, '<li>$1</li>')
            // Wrap consecutive list items in ul tags
            .replace(/(<li>.*?<\/li>)/g, '<ul>$1</ul>')
            .replace(/<\/ul>\s*<ul>/g, ''); // Remove duplicate ul tags

        return formatted;
    }

    // ===== ENHANCED DECISION RECOMMENDATION SYSTEM =====
    
    renderDecisionRecommendation(project, details) {
        if (!project.final_summary) {
            return '<div class="no-data">Decision recommendation not available</div>';
        }

        return `
            <!-- 1. DECISION HEADER (Score Removed) -->
            <div class="decision-header-clean">
                <div class="recommendation-text-clean">
                    <h4>${project.recommendation}</h4>
                    <p class="confidence">${this.getOverallConfidence(details?.question_analyses)}</p>
                </div>
            </div>

            <!-- 2. KEY INSIGHTS -->
            <div class="decision-insights">
                <div class="insight-card strengths">
                    <h6><i class="fas fa-thumbs-up"></i> Key Strengths</h6>
                    ${this.extractStrengths(project.final_summary)}
                </div>
                <div class="insight-card risks">
                    <h6><i class="fas fa-exclamation-triangle"></i> Key Risks</h6>
                    ${this.extractRisks(project.final_summary)}
                </div>
            </div>

            <!-- 3. ACTION PLAN -->
            <div class="action-plan">
                <h5><i class="fas fa-tasks"></i> Recommended Actions</h5>
                ${this.extractNextSteps(project.final_summary)}
            </div>

            <!-- 4. FULL ANALYSIS (Collapsible) -->
            <details class="full-analysis">
                <summary><i class="fas fa-file-alt"></i> View Complete Analysis Report</summary>
                <div class="analysis-content">
                    ${this.formatText(project.final_summary.full_text || 'Full analysis not available')}
                </div>
            </details>
        `;
    }

    getScoreClass(score) {
        if (score >= 4) return 'score-high';
        if (score >= 1) return 'score-mid';
        return 'score-low';
    }

    getOverallConfidence(questionAnalyses) {
        if (!questionAnalyses || questionAnalyses.length === 0) return 'Confidence not available';
        
        const confidenceCounts = { High: 0, Medium: 0, Low: 0 };
        questionAnalyses.forEach(q => {
            if (q.confidence && confidenceCounts[q.confidence] !== undefined) {
                confidenceCounts[q.confidence]++;
            }
        });
        
        const total = questionAnalyses.length;
        const highPct = (confidenceCounts.High / total) * 100;
        
        if (highPct >= 70) return 'High Confidence';
        if (highPct >= 40) return 'Medium Confidence';
        return 'Mixed Confidence';
    }

    renderQuestionScores(questionAnalyses) {
        const questionLabels = {
            'gap_filler': 'Gap-Filler?',
            'new_proof_points': 'New Proof-Points?',
            'clear_story': 'Clear Story?',
            'shared_audience_different_function': 'Shared Audience?',
            'low_friction_integration': 'Low-Friction Integration?',
            'hands_on_support': 'Hands-On Support?'
        };

        return questionAnalyses.map(q => `
            <div class="question-score-item" data-question="${q.question_key}" onclick="dashboard.expandQuestionAccordion(${q.question_id})">
                <div class="score-badge ${this.getScoreClass(q.score + 3)}">
                    ${q.score > 0 ? '+' : ''}${q.score}
                </div>
                <div class="question-label">${questionLabels[q.question_key] || q.question_key}</div>
                <div class="confidence confidence-${q.confidence?.toLowerCase()}">${q.confidence}</div>
            </div>
        `).join('');
    }

    extractStrengths(finalSummary) {
        if (!finalSummary.key_points) return '<p>No specific strengths identified</p>';
        
        const strengths = finalSummary.key_points.filter(point => 
            point.includes('Strategic Gap Filler') || 
            point.includes('New Proof-Points') ||
            point.includes('Developer Experience') ||
            point.includes('Support Commitment') ||
            point.includes('Chain Abstraction') ||
            point.includes('Synergy') ||
            point.includes('✅') ||
            point.includes('Strong') ||
            point.includes('High') ||
            point.includes('Good')
        );

        if (strengths.length === 0) {
            // Fallback: extract from full text
            const fullText = finalSummary.full_text || '';
            const strengthsSection = this.extractSection(fullText, 'Strengths & Opportunities', 'Challenges & Risks');
            if (strengthsSection) {
                const bullets = strengthsSection.split('- ').slice(1).map(item => item.split('\n')[0].trim());
                return '<ul>' + bullets.slice(0, 4).map(item => `<li>${item}</li>`).join('') + '</ul>';
            }
            return '<p>Strategic benefits identified in partnership evaluation</p>';
        }

        return '<ul>' + strengths.slice(0, 4).map(strength => 
            `<li>${this.formatText(strength.replace(/^- /, ''))}</li>`
        ).join('') + '</ul>';
    }

    extractRisks(finalSummary) {
        if (!finalSummary.key_points) return '<p>No specific risks identified</p>';
        
        const risks = finalSummary.key_points.filter(point => 
            point.includes('Integration Complexity') || 
            point.includes('Solver Network') ||
            point.includes('Security Assumptions') ||
            point.includes('Docs & Tooling') ||
            point.includes('❌') ||
            point.includes('Risk') ||
            point.includes('Challenge') ||
            point.includes('Friction') ||
            point.includes('Limited')
        );

        if (risks.length === 0) {
            // Fallback: extract from full text
            const fullText = finalSummary.full_text || '';
            const risksSection = this.extractSection(fullText, 'Challenges & Risks', 'Recommendation Rationale');
            if (risksSection) {
                const bullets = risksSection.split('- ').slice(1).map(item => item.split('\n')[0].trim());
                return '<ul>' + bullets.slice(0, 3).map(item => `<li>${item}</li>`).join('') + '</ul>';
            }
            return '<p>Implementation considerations require attention</p>';
        }

        return '<ul>' + risks.slice(0, 3).map(risk => 
            `<li>${this.formatText(risk.replace(/^- /, ''))}</li>`
        ).join('') + '</ul>';
    }

    extractNextSteps(finalSummary) {
        const fullText = finalSummary.full_text || '';
        const nextStepsSection = this.extractSection(fullText, 'Next Steps', '');
        
        if (nextStepsSection) {
            const steps = nextStepsSection.split(/\d+\./).slice(1).map(step => step.split('\n')[0].trim());
            if (steps.length > 0) {
                return '<ol>' + steps.slice(0, 4).map(step => 
                    `<li class="action-item">${this.formatText(step)}</li>`
                ).join('') + '</ol>';
            }
        }

        // Fallback: generic next steps based on score
        const score = parseInt(finalSummary.summary?.match(/(\d+)\/6/) || [0, 0])[1];
        if (score >= 4) {
            return `
                <ol>
                    <li class="action-item">Initiate partnership discussions</li>
                    <li class="action-item">Develop joint hackathon track</li>
                    <li class="action-item">Create co-marketing materials</li>
                </ol>
            `;
        } else if (score >= 1) {
            return `
                <ol>
                    <li class="action-item">Address integration concerns</li>
                    <li class="action-item">Pilot small-scale collaboration</li>
                    <li class="action-item">Re-evaluate after improvements</li>
                </ol>
            `;
        } else {
            return `
                <ol>
                    <li class="action-item">Monitor project development</li>
                    <li class="action-item">Reassess in 6 months</li>
                </ol>
            `;
        }
    }

    extractSection(text, startMarker, endMarker) {
        const startIndex = text.indexOf(startMarker);
        if (startIndex === -1) return null;
        
        const contentStart = startIndex + startMarker.length;
        let endIndex = text.length;
        
        if (endMarker) {
            const foundEnd = text.indexOf(endMarker, contentStart);
            if (foundEnd !== -1) endIndex = foundEnd;
        }
        
        return text.substring(contentStart, endIndex).trim();
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

    // Deep Research Methods
    renderDeepResearch(deepResearchData, projectDetails) {
        console.log('🔬 Deep Research Data:', deepResearchData); // Debug log
        
        // Calculate quality metrics
        const researchQuality = this.calculateOverallQuality(projectDetails);
        
        // Update metrics with real data (cost removed) + add quality metrics
        const timeElement = document.querySelector('#deep-research-time span');
        const toolsElement = document.querySelector('#deep-research-tools span');
        
        if (deepResearchData.elapsed_time) {
            const minutes = Math.round(deepResearchData.elapsed_time / 60);
            timeElement.textContent = `${minutes} minutes`;
            timeElement.title = `Real data: ${deepResearchData.elapsed_time.toFixed(1)} seconds`;
        } else {
            timeElement.textContent = '-- minutes';
            timeElement.title = 'No timing data available';
        }
        
        if (deepResearchData.tool_calls_made) {
            toolsElement.textContent = `${deepResearchData.tool_calls_made} tools`;
            toolsElement.title = `Real data: ${deepResearchData.tool_calls_made} AI tool calls made`;
        } else {
            toolsElement.textContent = '-- tools';
            toolsElement.title = 'No tool call data available';
        }
        
        // Add quality metrics as simple bubbles
        const researchMetrics = document.querySelector('.research-metrics');
        
        // Remove any existing quality bubbles first
        const existingQualityBubbles = researchMetrics.querySelectorAll('.quality-bubble');
        existingQualityBubbles.forEach(bubble => bubble.remove());
        
        // Add quality metric bubbles
        const qualityBubblesHtml = `
            <div class="metric-badge quality-bubble" title="Total research sources analyzed">
                <i class="fas fa-link"></i>
                <span>${researchQuality.totalSources} sources</span>
            </div>
            <div class="metric-badge quality-bubble" title="Average confidence across all analyses">
                <i class="fas fa-brain"></i>
                <span>${researchQuality.averageConfidence} confidence</span>
            </div>
            <div class="metric-badge quality-bubble" title="Total analysis cost ${researchQuality.hasRealData ? '(Real data)' : '(Estimated)'}">
                <i class="fas fa-dollar-sign"></i>
                <span>$${researchQuality.totalCost}${researchQuality.hasRealData ? ' ✓' : ' ~'}</span>
            </div>
        `;
        
        researchMetrics.insertAdjacentHTML('beforeend', qualityBubblesHtml);
        
        // Render content
        const contentElement = document.getElementById('deep-research-content');
        if (deepResearchData.research_data && deepResearchData.research_data.trim()) {
            contentElement.innerHTML = this.renderStructuredContent(
                deepResearchData.research_data, 
                'Deep research data not available'
            );
        } else {
            contentElement.innerHTML = '<div class="no-data">Deep research content not available</div>';
        }
        
        // Render sources
        const sourcesElement = document.getElementById('deep-research-sources');
        if (deepResearchData.sources && deepResearchData.sources.length > 0) {
            sourcesElement.innerHTML = `
                <h4>Enhanced Research Sources (${deepResearchData.sources.length}) 
                    <span style="font-size: 0.8rem; font-weight: normal; opacity: 0.7;">✓ Real data</span>
                </h4>
                ${this.renderSourcesList(deepResearchData.sources, 'deep-research')}
            `;
        } else {
            sourcesElement.innerHTML = '<div class="no-data">No enhanced sources available</div>';
        }
    }

    renderDeepResearchUnavailable(projectDetails) {
        console.log('⚠️ Deep research not available for this project');
        
        document.getElementById('deep-research-content').innerHTML = 
            '<div class="no-data">Deep research not available for this project</div>';
        document.getElementById('deep-research-sources').innerHTML = 
            '<div class="no-data">Run analysis with --deep-research flag to generate enhanced research data</div>';
            
        // Clear any existing quality bubbles since we don't have project details
        const researchMetrics = document.querySelector('.research-metrics');
        if (researchMetrics) {
            const existingQualityBubbles = researchMetrics.querySelectorAll('.quality-bubble');
            existingQualityBubbles.forEach(bubble => bubble.remove());
        }

        // Show basic quality metrics if project details are available
        if (projectDetails) {
            const researchQuality = this.calculateOverallQuality(projectDetails);
            const researchMetrics = document.querySelector('.research-metrics');
            const qualityBubblesHtml = `
                <div class="metric-badge quality-bubble" title="Total research sources analyzed">
                    <i class="fas fa-link"></i>
                    <span>${researchQuality.totalSources} sources</span>
                </div>
                <div class="metric-badge quality-bubble" title="Average confidence across all analyses">
                    <i class="fas fa-brain"></i>
                    <span>${researchQuality.averageConfidence} confidence</span>
                </div>
                <div class="metric-badge quality-bubble" title="Total analysis cost ${researchQuality.hasRealData ? '(Real data)' : '(Estimated)'}">
                    <i class="fas fa-dollar-sign"></i>
                    <span>$${researchQuality.totalCost}${researchQuality.hasRealData ? ' ✓' : ' ~'}</span>
                </div>
            `;
            researchMetrics.insertAdjacentHTML('beforeend', qualityBubblesHtml);
        }
    }

    // Question Research Context Methods
    renderQuestionResearchContext(questionData) {
        let html = '';
        
        // Question-specific research summary
        if (questionData.research_data) {
            html += `
                <div class="question-research-summary">
                    <h5><i class="fas fa-search"></i> Question-Specific Research</h5>
                    <div class="research-summary-content">
                        ${this.truncateText(questionData.research_data, 500)}
                    </div>
                </div>
            `;
        }
        
        // Sources
        if (questionData.sources && questionData.sources.length > 0) {
            html += `
                <div class="question-sources">
                    <h5><i class="fas fa-link"></i> Sources Analyzed (${questionData.sources.length})</h5>
                    ${this.renderSourcesList(questionData.sources, `question-${questionData.question_id}`)}
                </div>
            `;
        }
        
        return html || '<div class="no-data">No research context available</div>';
    }

    toggleResearchContext(questionId) {
        const content = document.getElementById(`research-context-${questionId}`);
        const toggle = content.previousElementSibling.querySelector('.research-context-toggle');
        
        if (content.classList.contains('expanded')) {
            content.classList.remove('expanded');
            toggle.style.transform = 'rotate(0deg)';
        } else {
            content.classList.add('expanded');
            toggle.style.transform = 'rotate(90deg)';
        }
    }

    // Universal Source Renderer
    renderSourcesList(sources, contextId) {
        if (!sources || sources.length === 0) {
            return '<div class="no-data">No sources available</div>';
        }
        
        return `
            <div class="sources-list" id="sources-${contextId}">
                ${sources.map((source, index) => `
                    <div class="source-item" data-source-index="${index}">
                        <div class="source-header">
                            <div class="source-info">
                                <a href="${source.url}" target="_blank" rel="noopener" class="source-title">
                                    <i class="fas fa-external-link-alt"></i>
                                    ${source.title || 'External Source'}
                                </a>
                                <div class="source-url">${this.truncateText(source.url, 60)}</div>
                            </div>
                            <div class="source-meta">
                                ${source.start_index && source.end_index ? 
                                    `<span class="relevance-indicator" title="Content relevance range">
                                        <i class="fas fa-crosshairs"></i>
                                        ${source.end_index - source.start_index} chars
                                    </span>` : ''
                                }
                                <button class="source-expand-btn" onclick="dashboard.toggleSourceDetail(${index}, '${contextId}')" title="Toggle source details">
                                    <i class="fas fa-chevron-down"></i>
                                </button>
                            </div>
                        </div>
                        <div class="source-details" id="source-detail-${contextId}-${index}">
                            <div class="source-details-content">
                                ${this.renderSourceDetails(source)}
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderSourceDetails(source) {
        let html = '<div class="source-detail-grid">';
        
        // URL analysis
        try {
            html += `
                <div class="source-detail-item">
                    <strong>Domain:</strong> ${new URL(source.url).hostname}
                </div>
            `;
        } catch (e) {
            html += `
                <div class="source-detail-item">
                    <strong>Domain:</strong> Invalid URL
                </div>
            `;
        }
        
        // Relevance metrics
        if (source.start_index !== undefined && source.end_index !== undefined) {
            html += `
                <div class="source-detail-item">
                    <strong>Content Range:</strong> ${source.start_index}-${source.end_index}
                    <span class="relevance-bar">
                        <div class="relevance-fill" style="width: ${Math.min(100, (source.end_index - source.start_index) / 10)}%"></div>
                    </span>
                </div>
            `;
        }
        
        // Additional metadata if available
        if (source.excerpt) {
            html += `
                <div class="source-detail-item full-width">
                    <strong>Relevant Excerpt:</strong>
                    <div class="source-excerpt">${this.truncateText(source.excerpt, 200)}</div>
                </div>
            `;
        }
        
        html += '</div>';
        return html;
    }

    toggleSourceDetail(sourceIndex, contextId) {
        const details = document.getElementById(`source-detail-${contextId}-${sourceIndex}`);
        const button = details.previousElementSibling.querySelector('.source-expand-btn i');
        
        if (details.classList.contains('expanded')) {
            details.classList.remove('expanded');
            button.style.transform = 'rotate(0deg)';
        } else {
            details.classList.add('expanded');
            button.style.transform = 'rotate(180deg)';
        }
    }

    // Quality Indicators Methods
    calculateQuestionQuality(questionData) {
        const sourceCount = questionData.sources ? questionData.sources.length : 0;
        const researchLength = questionData.research_data ? questionData.research_data.length : 0;
        const analysisLength = questionData.analysis ? questionData.analysis.length : 0;
        
        // Calculate metrics with more generous scoring
        const researchDepth = researchLength > 3000 ? 'High' : researchLength > 1500 ? 'Med' : 'Low';
        
        // More realistic analysis completeness calculation
        // 600 chars = 85%, 800+ chars = 95%+, with a generous curve
        let analysisCompleteness;
        if (analysisLength >= 800) {
            analysisCompleteness = Math.min(100, 95 + Math.round((analysisLength - 800) / 200 * 5));
        } else if (analysisLength >= 600) {
            analysisCompleteness = 85 + Math.round((analysisLength - 600) / 200 * 10);
        } else if (analysisLength >= 400) {
            analysisCompleteness = 70 + Math.round((analysisLength - 400) / 200 * 15);
        } else if (analysisLength >= 200) {
            analysisCompleteness = 50 + Math.round((analysisLength - 200) / 200 * 20);
        } else {
            analysisCompleteness = Math.round((analysisLength / 200) * 50);
        }
        
        return {
            sourceCount,
            researchDepth,
            analysisCompleteness
        };
    }

    calculateOverallQuality(projectDetails) {
        let totalSources = 0;
        let confidenceSum = 0;
        let confidenceCount = 0;
        
        // Calculate from question analyses
        if (projectDetails.question_analyses) {
            projectDetails.question_analyses.forEach(q => {
                if (q.sources) totalSources += q.sources.length;
                if (q.confidence) {
                    const confValue = q.confidence === 'High' ? 3 : q.confidence === 'Medium' ? 2 : 1;
                    confidenceSum += confValue;
                    confidenceCount++;
                }
            });
        }
        
        // Add general sources
        if (projectDetails.general_sources) {
            totalSources += projectDetails.general_sources.length;
        }
        
        const averageConfidence = confidenceCount > 0 ? (confidenceSum / confidenceCount) : 0;
        const confidenceLabel = averageConfidence >= 2.5 ? 'High' : averageConfidence >= 1.5 ? 'Medium' : 'Low';
        const confidenceClass = averageConfidence >= 2.5 ? 'high' : averageConfidence >= 1.5 ? 'medium' : 'low';
        const confidencePercent = (averageConfidence / 3) * 100;
        
        // Use REAL data from usage tracking when available, fallback to estimates
        let researchTime = '0';
        let totalCost = '0.00';
        let hasRealData = false;
        
        if (projectDetails.usage_data && projectDetails.usage_data.has_real_data) {
            // REAL data from comprehensive API usage tracking
            researchTime = (projectDetails.usage_data.total_time / 60).toFixed(1);
            totalCost = projectDetails.usage_data.total_cost.toFixed(4);
            hasRealData = true;
        } else if (projectDetails.deep_research && projectDetails.deep_research.elapsed_time) {
            // REAL data from deep research only (partial)
            researchTime = (projectDetails.deep_research.elapsed_time / 60).toFixed(1);
            totalCost = projectDetails.deep_research.estimated_cost ? projectDetails.deep_research.estimated_cost.toFixed(2) : '0.00';
            hasRealData = true;
        } else {
            // Estimated data when no tracking available
            const questionCount = projectDetails.question_analyses ? projectDetails.question_analyses.length : 0;
            researchTime = (questionCount * 1.5).toFixed(1); // Estimate 1.5 min per question
            totalCost = (questionCount * 0.30).toFixed(2); // Estimate $0.30 per question
        }
        
        return {
            totalSources,
            averageConfidence: confidenceLabel,
            confidenceClass,
            confidencePercent,
            researchTime,
            totalCost,
            hasRealData
        };
    }

    closeModal() {
        const modal = document.getElementById('project-modal');
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }

    renderPartnershipAssessmentDetailed(questionAnalyses) {
        const grid = document.getElementById('questions-grid-decision');
        
        if (!questionAnalyses || questionAnalyses.length === 0) {
            grid.innerHTML = '<div class="no-data">No partnership assessment data available</div>';
            return;
        }

        grid.innerHTML = questionAnalyses.map(q => {
            const scoreClass = this.getScoreClass(q.score);
            const qualityMetrics = this.calculateQuestionQuality(q);
            
            return `
                <div class="question-card-detailed ${scoreClass}" data-question-id="${q.question_id}" onclick="dashboard.switchToQuestionDetail(${q.question_id})">
                    <div class="question-card-header-detailed">
                        <div class="question-card-title-detailed">Q${q.question_id}: ${this.getQuestionTitle(q.question_id)}</div>
                        <div class="question-card-score-detailed">
                            ${q.score >= 0 ? '+' : ''}${q.score}
                        </div>
                    </div>
                    <div class="question-card-confidence-detailed">Confidence: ${q.confidence}</div>
                    
                    <!-- Quality Indicators -->
                    <div class="question-quality-metrics">
                        <div class="quality-metric-detailed" title="Source diversity">
                            <i class="fas fa-link"></i>
                            <span>${qualityMetrics.sourceCount} sources</span>
                        </div>
                        <div class="quality-metric-detailed" title="Research depth">
                            <i class="fas fa-search"></i>
                            <span>${qualityMetrics.researchDepth}</span>
                        </div>
                        <div class="quality-metric-detailed" title="Analysis completeness">
                            <i class="fas fa-brain"></i>
                            <span>${qualityMetrics.analysisCompleteness}%</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    switchToQuestionDetail(questionId) {
        // Switch to questions tab and expand the specific question
        this.switchTab('questions');
        this.expandQuestionAccordion(questionId);
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