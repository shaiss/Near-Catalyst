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
        
        // Update modal content
        document.getElementById('modal-title').textContent = project.project_name;
        document.getElementById('modal-score').textContent = score;
        document.getElementById('modal-recommendation').textContent = 
            project.recommendation || 'No recommendation available';

        // Remove any existing research quality dashboard to prevent duplication
        const existingDashboard = document.querySelector('.research-quality-dashboard');
        if (existingDashboard) {
            existingDashboard.remove();
        }

        // Render questions overview grid (now persistent above tabs)
        this.renderQuestionsOverview(details?.question_analyses || []);
        
        // Render detailed questions accordion
        this.renderQuestionsAccordion(details?.question_analyses || []);

        // Render research summary
        document.getElementById('research-summary').innerHTML = 
            this.renderStructuredContent(details?.general_research, 'Research data not available');

        // Render final analysis
        document.getElementById('final-analysis').innerHTML = 
            this.renderStructuredContent(project.final_summary, 'Final analysis not available');

        // Render project details from NEAR catalog
        this.renderProjectDetails(project, details);

        // Render research quality dashboard with real data
        if (details) {
            const researchQuality = this.calculateOverallQuality(details);
            document.querySelector('.project-overview').insertAdjacentHTML('afterend', `
                <div class="research-quality-dashboard">
                    <h4><i class="fas fa-chart-bar"></i> Research Quality Overview</h4>
                    <div class="quality-grid">
                        <div class="quality-card">
                            <div class="quality-value">${researchQuality.totalSources}</div>
                            <div class="quality-label">Total Sources</div>
                            <div class="quality-bar">
                                <div class="quality-fill" style="width: ${Math.min(100, researchQuality.totalSources * 10)}%"></div>
                            </div>
                        </div>
                        <div class="quality-card">
                            <div class="quality-value">${researchQuality.averageConfidence}</div>
                            <div class="quality-label">Avg Confidence</div>
                            <div class="quality-bar">
                                <div class="quality-fill confidence-${researchQuality.confidenceClass}" style="width: ${researchQuality.confidencePercent}%"></div>
                            </div>
                        </div>
                        <div class="quality-card">
                            <div class="quality-value">${researchQuality.researchTime}</div>
                            <div class="quality-label">Research Time</div>
                            <div class="quality-bar">
                                <div class="quality-fill" style="width: ${Math.min(100, (parseFloat(researchQuality.researchTime) || 0) * 10)}%"></div>
                            </div>
                        </div>
                        <div class="quality-card">
                            <div class="quality-value">$${researchQuality.totalCost}</div>
                            <div class="quality-label">Analysis Cost</div>
                            <div class="quality-bar">
                                <div class="quality-fill cost" style="width: ${Math.min(100, (parseFloat(researchQuality.totalCost) || 0) * 20)}%"></div>
                            </div>
                        </div>
                    </div>
                </div>
            `);
        }

        // Render deep research if available  
        if (details?.deep_research) {
            this.renderDeepResearch(details.deep_research);
        } else {
            this.renderDeepResearchUnavailable();
        }

        // Reset to project details tab (new home tab)
        this.switchTab('project-details');

        // Show modal
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    async renderProjectDetails(project, details) {
        const detailsElement = document.getElementById('project-details-data');
        
        // Check if we have cached catalog data from backend
        const catalogData = details?.catalog_data;
        
        if (catalogData && catalogData.cached) {
            console.log('✓ Using cached NEAR catalog data from backend');
            // Use cached data from backend
            let detailsHtml = this.formatProjectCatalogData(catalogData.full_data || catalogData, project, details);
            detailsElement.innerHTML = detailsHtml;
        } else {
            console.log('⚠️ No cached catalog data, attempting direct API call...');
            // Show loading state
            detailsElement.innerHTML = '<div class="loading-details"><i class="fas fa-spinner fa-spin"></i> Loading project details...</div>';
            
            try {
                // Fallback: Fetch project details from NEAR catalog directly
                const slug = project.slug || project.project_name.toLowerCase().replace(/\s+/g, '-');
                console.log(`🔍 Fallback: Fetching NEAR catalog data for slug: ${slug}`);
                
                const response = await fetch(`https://api.nearcatalog.org/project?pid=${encodeURIComponent(slug)}`);
                
                if (!response.ok) {
                    throw new Error(`NEAR Catalog API responded with ${response.status}`);
                }
                
                const fallbackCatalogData = await response.json();
                console.log('📊 Fallback NEAR Catalog Data:', fallbackCatalogData);
                
                // Render the project details
                let detailsHtml = this.formatProjectCatalogData(fallbackCatalogData, project, details);
                detailsElement.innerHTML = detailsHtml;
                
            } catch (error) {
                console.warn('⚠️ Could not fetch NEAR catalog data:', error);
                
                // Final fallback to basic project information
                let fallbackHtml = this.formatBasicProjectData(project, details);
                detailsElement.innerHTML = fallbackHtml;
            }
        }
    }

    formatProjectCatalogData(catalogData, project, details) {
        let html = '<div class="project-meta-grid">';
        
        // Basic project metadata
        if (catalogData.name || project.project_name) {
            html += `
                <div class="project-meta-item">
                    <div class="project-meta-label">Project Name</div>
                    <div class="project-meta-value">${catalogData.name || project.project_name}</div>
                </div>
            `;
        }
        
        if (catalogData.category) {
            html += `
                <div class="project-meta-item">
                    <div class="project-meta-label">Category</div>
                    <div class="project-meta-value">${catalogData.category}</div>
                </div>
            `;
        }
        
        if (catalogData.stage) {
            html += `
                <div class="project-meta-item">
                    <div class="project-meta-label">Development Stage</div>
                    <div class="project-meta-value">${catalogData.stage}</div>
                </div>
            `;
        }
        
        if (catalogData.founded) {
            html += `
                <div class="project-meta-item">
                    <div class="project-meta-label">Founded</div>
                    <div class="project-meta-value">${catalogData.founded}</div>
                </div>
            `;
        }
        
        if (catalogData.team_size) {
            html += `
                <div class="project-meta-item">
                    <div class="project-meta-label">Team Size</div>
                    <div class="project-meta-value">${catalogData.team_size}</div>
                </div>
            `;
        }
        
        if (catalogData.location) {
            html += `
                <div class="project-meta-item">
                    <div class="project-meta-label">Location</div>
                    <div class="project-meta-value">${catalogData.location}</div>
                </div>
            `;
        }
        
        html += '</div>';
        
        // Project description
        if (catalogData.description) {
            html += `
                <div class="project-description">
                    <strong>Description:</strong><br>
                    ${this.formatText(catalogData.description)}
                </div>
            `;
        }
        
        // Tags
        if (catalogData.tags && catalogData.tags.length > 0) {
            html += '<div class="project-tags">';
            catalogData.tags.forEach(tag => {
                html += `<span class="project-tag">${tag}</span>`;
            });
            html += '</div>';
        }
        
        // Links
        if (catalogData.website || catalogData.github || catalogData.twitter) {
            html += '<div class="project-links">';
            
            if (catalogData.website) {
                html += `<a href="${catalogData.website}" target="_blank" class="project-link">
                    <i class="fas fa-globe"></i> Website
                </a>`;
            }
            
            if (catalogData.github) {
                html += `<a href="${catalogData.github}" target="_blank" class="project-link">
                    <i class="fab fa-github"></i> GitHub
                </a>`;
            }
            
            if (catalogData.twitter) {
                html += `<a href="${catalogData.twitter}" target="_blank" class="project-link">
                    <i class="fab fa-twitter"></i> Twitter
                </a>`;
            }
            
            html += '</div>';
        }
        
        // Additional technical details
        if (catalogData.tech_stack || catalogData.blockchain_networks) {
            html += '<div class="project-meta-grid">';
            
            if (catalogData.tech_stack) {
                html += `
                    <div class="project-meta-item">
                        <div class="project-meta-label">Tech Stack</div>
                        <div class="project-meta-value">${catalogData.tech_stack}</div>
                    </div>
                `;
            }
            
            if (catalogData.blockchain_networks) {
                html += `
                    <div class="project-meta-item">
                        <div class="project-meta-label">Blockchain Networks</div>
                        <div class="project-meta-value">${catalogData.blockchain_networks}</div>
                    </div>
                `;
            }
            
            html += '</div>';
        }
        
        return html;
    }

    formatBasicProjectData(project, details) {
        let html = '<div class="project-meta-grid">';
        
        html += `
            <div class="project-meta-item">
                <div class="project-meta-label">Project Name</div>
                <div class="project-meta-value">${project.project_name}</div>
            </div>
        `;
        
        if (project.slug) {
            html += `
                <div class="project-meta-item">
                    <div class="project-meta-label">Slug</div>
                    <div class="project-meta-value">${project.slug}</div>
                </div>
            `;
        }
        
        html += `
            <div class="project-meta-item">
                <div class="project-meta-label">Partnership Score</div>
                <div class="project-meta-value">${project.total_score || 0}/6</div>
            </div>
        `;
        
        if (project.created_at) {
            html += `
                <div class="project-meta-item">
                    <div class="project-meta-label">Analysis Date</div>
                    <div class="project-meta-value">${this.formatDate(project.created_at)}</div>
                </div>
            `;
        }
        
        html += '</div>';
        
        if (project.recommendation) {
            html += `
                <div class="project-description">
                    <strong>Partnership Recommendation:</strong><br>
                    ${this.formatText(project.recommendation)}
                </div>
            `;
        }
        
        html += `
            <div class="no-data" style="margin-top: 20px;">
                <i class="fas fa-info-circle" style="margin-right: 8px;"></i>
                Could not fetch additional project details from NEAR Catalog. 
                Please check the project slug or try again later.
            </div>
        `;
        
        return html;
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
    renderDeepResearch(deepResearchData) {
        console.log('🔬 Deep Research Data:', deepResearchData); // Debug log
        
        // Update metrics with real data
        const timeElement = document.querySelector('#deep-research-time span');
        const toolsElement = document.querySelector('#deep-research-tools span');
        const costElement = document.querySelector('#deep-research-cost span');
        
        if (deepResearchData.elapsed_time) {
            const minutes = Math.round(deepResearchData.elapsed_time / 60);
            timeElement.textContent = `${minutes} min`;
            timeElement.title = `Real data: ${deepResearchData.elapsed_time.toFixed(1)} seconds`;
        } else {
            timeElement.textContent = '-- min';
            timeElement.title = 'No timing data available';
        }
        
        if (deepResearchData.tool_calls_made) {
            toolsElement.textContent = `${deepResearchData.tool_calls_made} tools`;
            toolsElement.title = `Real data: ${deepResearchData.tool_calls_made} AI tool calls made`;
        } else {
            toolsElement.textContent = '-- tools';
            toolsElement.title = 'No tool call data available';
        }
        
        if (deepResearchData.estimated_cost) {
            costElement.textContent = `$${deepResearchData.estimated_cost}`;
            costElement.title = `Real estimated cost: $${deepResearchData.estimated_cost}`;
        } else {
            costElement.textContent = '$--';
            costElement.title = 'No cost data available';
        }
        
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

    renderDeepResearchUnavailable() {
        console.log('⚠️ Deep research not available for this project');
        
        document.getElementById('deep-research-content').innerHTML = 
            '<div class="no-data">Deep research not available for this project</div>';
        document.getElementById('deep-research-sources').innerHTML = 
            '<div class="no-data">Run analysis with --deep-research flag to generate enhanced research data</div>';
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
        
        // Calculate metrics
        const researchDepth = researchLength > 3000 ? 'High' : researchLength > 1500 ? 'Med' : 'Low';
        const analysisCompleteness = Math.min(100, Math.round((analysisLength / 1000) * 100));
        
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
        
        // Use REAL data from deep research when available, fallback to calculated estimates
        let researchTime = '0';
        let totalCost = '0.00';
        
        if (projectDetails.deep_research && projectDetails.deep_research.elapsed_time) {
            // REAL data from database
            researchTime = (projectDetails.deep_research.elapsed_time / 60).toFixed(1);
            totalCost = projectDetails.deep_research.estimated_cost ? projectDetails.deep_research.estimated_cost.toFixed(2) : '0.00';
        } else {
            // Estimated data when deep research not available
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
            totalCost
        };
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