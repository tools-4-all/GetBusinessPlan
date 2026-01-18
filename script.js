// ============================================
// CONFIGURAZIONE API BACKEND
// ============================================
// Backend su Render. Le credenziali API sono configurate sul server.
// Nota: sul piano free Render il servizio può andare in sleep; la prima richiesta dopo un po' di inattività può richiedere 1-2 minuti (cold start).
const API_BASE_URL = 'https://getbusinessplan.onrender.com';
if (typeof console !== 'undefined') console.log('[SeedWise] API Backend:', API_BASE_URL, '(Render)');

// ============================================
// UTILITY FUNCTIONS
// ============================================
// Funzione per sanitizzare HTML (escape)
function escape(str) {
    if (str == null) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// DOM Elements - will be initialized when DOM is ready
let planModal;
let closeModal;
let startPlanBtn;
let createPlanBtn;
let ctaPlanBtn;
let loadingState;
let resultState;
let planContent;
let downloadPdfBtn;
let editPlanBtn;
let wizardContainer;
let wizardNavigation;
let prevBtn;
let nextBtn;
let progressBar;
let progressSteps;

// Wizard State
let currentStep = 0;
let wizardData = {};

// Questions Configuration
const questions = [
    {
        id: 'companyName',
        title: 'Qual è il nome della tua azienda?',
        description: 'Inserisci il nome ufficiale della tua azienda o startup',
        type: 'text',
        required: true,
        placeholder: 'Es. TechStart S.r.l.'
    },
    {
        id: 'industry',
        title: 'In quale settore opera la tua azienda?',
        description: 'Seleziona il settore più appropriato',
        type: 'select',
        required: true,
        options: [
            { value: '', label: 'Seleziona un settore' },
            { value: 'ristorazione', label: 'Ristorazione e Food & Beverage' },
            { value: 'tech', label: 'Tecnologia e Software' },
            { value: 'retail', label: 'Vendita al Dettaglio' },
            { value: 'ecommerce', label: 'E-commerce' },
            { value: 'servizi', label: 'Servizi Professionali' },
            { value: 'manufacturing', label: 'Produzione e Manifattura' },
            { value: 'healthcare', label: 'Sanità e Benessere' },
            { value: 'education', label: 'Educazione e Formazione' },
            { value: 'realestate', label: 'Immobiliare' },
            { value: 'finance', label: 'Finanza e Investimenti' },
            { value: 'altro', label: 'Altro' }
        ]
    },
    {
        id: 'location',
        title: 'Dove si trova la tua azienda?',
        description: 'Indica la città e la regione principale',
        type: 'text',
        required: true,
        placeholder: 'Es. Milano, Lombardia'
    },
    {
        id: 'foundingYear',
        title: 'Quando è stata fondata la tua azienda?',
        description: 'Anno di fondazione o lancio (lascia vuoto se è una startup in fase di lancio)',
        type: 'number',
        required: false,
        min: 1900,
        max: new Date().getFullYear(),
        placeholder: 'Es. 2023'
    },
    {
        id: 'description',
        title: 'Descrivi la tua attività in dettaglio',
        description: 'Spiega cosa fa la tua azienda, quali prodotti o servizi offre e qual è la sua mission',
        type: 'textarea',
        required: true,
        rows: 5,
        placeholder: 'Descrivi la tua attività, i prodotti/servizi principali e la mission aziendale...'
    },
    {
        id: 'businessModel',
        title: 'Qual è il tuo modello di business?',
        description: 'Descrivi come generi ricavi (es. vendita prodotti, abbonamenti, commissioni, pubblicità, ecc.)',
        type: 'textarea',
        required: true,
        rows: 4,
        placeholder: 'Es. Vendita diretta di prodotti online, abbonamento mensile per servizi SaaS, commissioni su transazioni, pubblicità su piattaforma...'
    },
    {
        id: 'targetMarket',
        title: 'Chi è il tuo mercato target?',
        description: 'Descrivi i tuoi clienti ideali: caratteristiche demografiche, dimensioni, settore, ecc.',
        type: 'textarea',
        required: true,
        rows: 4,
        placeholder: 'Es. Piccole e medie imprese (PMI) nel settore tecnologico, 50-200 dipendenti, con budget IT mensile superiore a €5.000...',
        allowAutoDetect: true
    },
    {
        id: 'competitiveAdvantage',
        title: 'Qual è il tuo vantaggio competitivo?',
        description: 'Cosa rende unica la tua azienda rispetto ai concorrenti?',
        type: 'textarea',
        required: true,
        rows: 4,
        placeholder: 'Es. Tecnologia proprietaria, team esperto, partnership esclusive, prezzo competitivo, qualità superiore...'
    },
    {
        id: 'pricing',
        title: 'Qual è la tua strategia di pricing?',
        description: 'Indica i prezzi dei tuoi prodotti/servizi principali (se non ancora definiti, indica un range)',
        type: 'textarea',
        required: false,
        rows: 4,
        placeholder: 'Es. Prodotto base: €99/mese, Prodotto premium: €299/mese, Consulenza: €150/ora, Prodotto fisico: €49-€199...'
    },
    {
        id: 'employees',
        title: 'Quanti dipendenti/collaboratori hai attualmente?',
        description: 'Includi anche i fondatori e collaboratori part-time (se startup, indica il numero previsto)',
        type: 'number',
        required: false,
        min: 0,
        placeholder: 'Es. 5'
    },
    {
        id: 'revenue',
        title: 'Qual è il fatturato attuale o previsto?',
        description: 'Inserisci il fatturato annuale in euro (se startup, indica la previsione per il primo anno)',
        type: 'number',
        required: false,
        min: 0,
        placeholder: 'Es. 50000'
    },
    {
        id: 'costs',
        title: 'Quali sono i principali costi operativi?',
        description: 'Descrivi i costi principali: personale, affitto, marketing, materie prime, tecnologia, ecc.',
        type: 'textarea',
        required: false,
        rows: 4,
        placeholder: 'Es. Personale: €30.000/mese, Affitto ufficio: €2.000/mese, Marketing: €5.000/mese, Server/Cloud: €1.000/mese...'
    },
    {
        id: 'initialInvestment',
        title: 'Quale investimento iniziale è necessario?',
        description: 'Indica l\'investimento iniziale richiesto per avviare o far crescere l\'attività (se applicabile)',
        type: 'number',
        required: false,
        min: 0,
        placeholder: 'Es. 100000'
    },
    {
        id: 'fundingNeeds',
        title: 'Hai bisogno di finanziamenti esterni?',
        description: 'Se sì, indica l\'importo necessario e come lo utilizzeresti (sviluppo prodotto, marketing, personale, ecc.)',
        type: 'textarea',
        required: false,
        rows: 4,
        placeholder: 'Es. Sì, €100.000 per espansione marketing (€40K), assunzione personale (€50K) e sviluppo prodotto (€10K)...'
    },
    {
        id: 'channels',
        title: 'Quali sono i tuoi canali di vendita/distribuzione?',
        description: 'Descrivi come raggiungi i clienti (online, negozi fisici, venditori, partner, ecc.)',
        type: 'textarea',
        required: false,
        rows: 4,
        placeholder: 'Es. E-commerce diretto, marketplace (Amazon, eBay), venditori diretti, distributori, app mobile...'
    },
    {
        id: 'goals',
        title: 'Quali sono i tuoi obiettivi principali?',
        description: 'Descrivi gli obiettivi a breve e lungo termine della tua azienda',
        type: 'textarea',
        required: false,
        rows: 4,
        placeholder: 'Es. Raggiungere €500K di fatturato entro 2 anni, espandere in 3 nuove città, assumere 10 nuovi dipendenti, acquisire 1.000 clienti...'
    },
    {
        id: 'horizonMonths',
        title: 'Quale orizzonte temporale vuoi analizzare?',
        description: 'Seleziona l\'orizzonte temporale per le proiezioni finanziarie (da 6 a 60 mesi)',
        type: 'select',
        required: true,
        options: [
            { value: '', label: 'Seleziona orizzonte temporale' },
            { value: '6', label: '6 mesi' },
            { value: '12', label: '12 mesi (1 anno)' },
            { value: '18', label: '18 mesi' },
            { value: '24', label: '24 mesi (2 anni)' },
            { value: '36', label: '36 mesi (3 anni)' },
            { value: '48', label: '48 mesi (4 anni)' },
            { value: '60', label: '60 mesi (5 anni)' }
        ]
    }
];

// Modal Functions
function openModal() {
    if (!planModal) {
        planModal = document.getElementById('planModal');
    }
    if (!planModal) {
        console.error('planModal not found');
        return;
    }
    planModal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    initWizard();
}

function closeModalFunc() {
    if (!planModal) {
        planModal = document.getElementById('planModal');
    }
    if (planModal) {
        planModal.style.display = 'none';
        document.body.style.overflow = 'auto';
        resetWizard();
    }
}

function resetWizard() {
    currentStep = 0;
    wizardData = {};
    if (!wizardContainer) wizardContainer = document.getElementById('wizardContainer');
    if (!progressSteps) progressSteps = document.getElementById('progressSteps');
    if (!wizardNavigation) wizardNavigation = document.getElementById('wizardNavigation');
    if (!loadingState) loadingState = document.getElementById('loadingState');
    if (!resultState) resultState = document.getElementById('resultState');
    
    if (wizardContainer) wizardContainer.innerHTML = '';
    if (progressSteps) progressSteps.innerHTML = '';
    if (wizardNavigation) wizardNavigation.style.display = 'none';
    if (loadingState) loadingState.style.display = 'none';
    if (resultState) resultState.style.display = 'none';
}

function initWizard() {
    resetWizard();
    renderProgressSteps();
    renderCurrentStep();
    updateNavigation();
}

function renderProgressSteps() {
    if (!progressSteps) progressSteps = document.getElementById('progressSteps');
    if (!progressSteps) return;
    
    progressSteps.innerHTML = '';
    questions.forEach((q, index) => {
        const step = document.createElement('div');
        step.className = `progress-step ${index === currentStep ? 'active' : ''} ${wizardData[q.id] ? 'completed' : ''}`;
        step.textContent = index + 1;
        progressSteps.appendChild(step);
    });
    updateProgressBar();
}

function updateProgressBar() {
    if (!progressBar) progressBar = document.getElementById('progressBar');
    if (!progressBar) return;
    
    const progress = ((currentStep + 1) / questions.length) * 100;
    progressBar.style.width = `${progress}%`;
}

// Funzione per ottenere suggerimenti dall'API
async function getSuggestions(questionId, questionTitle, questionDescription, currentValue, formType = 'business-plan', contextData = {}) {
    try {
        const API_BASE_URL = window.API_BASE_URL || 'https://getbusinessplan.onrender.com';
        const response = await fetch(`${API_BASE_URL}/api/get-suggestions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                questionId,
                questionTitle,
                questionDescription,
                currentValue,
                formType,
                contextData
            })
        });
        
        const data = await response.json();
        return data.success ? data.suggestions : [];
    } catch (error) {
        console.error('Errore nel recupero suggerimenti:', error);
        return [];
    }
}

// Funzione per visualizzare i suggerimenti
function displaySuggestions(suggestions, container, input) {
    if (!suggestions || suggestions.length === 0) {
        container.innerHTML = '';
        return;
    }
    
    container.innerHTML = `
        <div class="suggestions-box">
            <div class="suggestions-header">
                <span class="suggestions-title">Suggerimenti per migliorare la risposta</span>
            </div>
            <ul class="suggestions-list">
                ${suggestions.map((suggestion, index) => {
                    const escapedSuggestion = escape(suggestion);
                    const safeSuggestion = escapedSuggestion.replace(/'/g, "\\'").replace(/\n/g, ' ');
                    return `
                    <li class="suggestion-item" data-index="${index}" onclick="applySuggestion('${safeSuggestion}', '${input.id}')">
                        <div class="suggestion-content">
                            <span class="suggestion-text">${escapedSuggestion}</span>
                        </div>
                    </li>
                `;
                }).join('')}
            </ul>
        </div>
    `;
}

// Funzione per applicare un suggerimento
function applySuggestion(suggestion, inputId) {
    const input = document.getElementById(inputId);
    if (input) {
        const currentValue = input.value.trim();
        if (currentValue) {
            input.value = currentValue + '\n\n' + suggestion;
        } else {
            input.value = suggestion;
        }
        input.focus();
        
        // Salva il valore
        const questionId = inputId.replace('wizard-', '');
        if (wizardData) {
            wizardData[questionId] = input.value;
        } else if (typeof analysisWizardData !== 'undefined') {
            analysisWizardData[questionId] = input.value;
        }
        
        // Nascondi i suggerimenti dopo l'applicazione
        const suggestionsContainer = document.getElementById(`suggestions-${questionId}`);
        if (suggestionsContainer) {
            suggestionsContainer.innerHTML = '';
        }
        
        // Trigger input event per salvare
        input.dispatchEvent(new Event('input', { bubbles: true }));
    }
}

function renderCurrentStep() {
    if (!wizardContainer) wizardContainer = document.getElementById('wizardContainer');
    if (!wizardContainer) return;
    
    const question = questions[currentStep];
    if (!question) return;

    wizardContainer.innerHTML = `
        <div class="wizard-step">
            <h2 class="wizard-question-title">${question.title}</h2>
            ${question.description ? `<p class="wizard-question-desc">${question.description}</p>` : ''}
            <div class="wizard-input-container">
                ${renderInput(question)}
            </div>
        </div>
    `;

    // Gestisci checkbox per auto-rilevamento mercato target
    if (question.allowAutoDetect) {
        const autoDetectId = `${question.id}_auto_detect`;
        const checkbox = document.getElementById(autoDetectId);
        const textarea = document.getElementById(`wizard-${question.id}`);
        
        if (checkbox && textarea) {
            // Carica stato salvato
            if (wizardData[`${question.id}_auto_detect`]) {
                checkbox.checked = true;
                textarea.disabled = true;
                textarea.required = false;
                textarea.placeholder = 'Il mercato target verrà identificato automaticamente in base alle informazioni fornite.';
            }
            
            // Gestisci cambio stato checkbox
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    textarea.disabled = true;
                    textarea.required = false;
                    textarea.value = '';
                    textarea.placeholder = 'Il mercato target verrà identificato automaticamente in base alle informazioni fornite.';
                    // Nascondi suggerimenti se auto-detect è attivo
                    const suggestionsContainer = document.getElementById(`suggestions-${question.id}`);
                    if (suggestionsContainer) {
                        suggestionsContainer.innerHTML = '';
                    }
                } else {
                    textarea.disabled = false;
                    textarea.required = question.required;
                    textarea.placeholder = question.placeholder || '';
                }
            });
        }
    }

    // Aggiungi gestione suggerimenti per campi text e textarea
    const input = wizardContainer.querySelector(`#wizard-${question.id}`);
    const suggestionsContainer = document.getElementById(`suggestions-${question.id}`);
    
    if (input && suggestionsContainer && (question.type === 'text' || question.type === 'textarea')) {
        let suggestionTimeout;
        let isLoadingSuggestions = false;
        let lastLoadedValue = '';
        let hasSuggestions = false;
        
        // Funzione per mostrare loading senza nascondere i suggerimenti esistenti
        const showLoading = () => {
            const existingBox = suggestionsContainer.querySelector('.suggestions-box');
            if (existingBox) {
                // Aggiungi indicatore di aggiornamento senza nascondere i suggerimenti
                const loadingIndicator = document.createElement('div');
                loadingIndicator.className = 'suggestions-loading';
                loadingIndicator.style.cssText = 'padding: 8px; text-align: center; font-size: 13px; color: #64748b; border-top: 1px solid #e2e8f0; margin-top: 12px;';
                loadingIndicator.textContent = 'Aggiornamento suggerimenti...';
                existingBox.appendChild(loadingIndicator);
            } else {
                suggestionsContainer.innerHTML = '<div class="suggestions-loading">Caricamento suggerimenti...</div>';
            }
        };
        
        // Funzione per rimuovere l'indicatore di loading
        const hideLoading = () => {
            const loadingIndicator = suggestionsContainer.querySelector('.suggestions-loading');
            if (loadingIndicator && loadingIndicator.parentElement) {
                loadingIndicator.remove();
            }
        };
        
        // Funzione per caricare e mostrare suggerimenti
        const loadSuggestions = async () => {
            if (isLoadingSuggestions) return;
            
            // Non mostrare suggerimenti se auto-detect è attivo
            if (question.allowAutoDetect) {
                const autoDetectCheckbox = document.getElementById(`${question.id}_auto_detect`);
                if (autoDetectCheckbox && autoDetectCheckbox.checked) {
                    suggestionsContainer.innerHTML = '';
                    hasSuggestions = false;
                    return;
                }
            }
            
            const currentValue = input.value.trim();
            
            // Evita ricaricamenti se il valore non è cambiato significativamente
            if (currentValue === lastLoadedValue && hasSuggestions) {
                return;
            }
            
            const contextData = { ...wizardData }; // Dati già compilati
            
            isLoadingSuggestions = true;
            showLoading();
            
            try {
                const suggestions = await getSuggestions(
                    question.id,
                    question.title,
                    question.description || '',
                    currentValue,
                    'business-plan',
                    contextData
                );
                
                hideLoading();
                
                if (suggestions && suggestions.length > 0) {
                    displaySuggestions(suggestions, suggestionsContainer, input);
                    lastLoadedValue = currentValue;
                    hasSuggestions = true;
                } else {
                    // Nascondi solo se non ci sono suggerimenti e non c'erano prima
                    if (!hasSuggestions) {
                        suggestionsContainer.innerHTML = '';
                    }
                    hasSuggestions = false;
                }
            } catch (error) {
                console.error('Errore caricamento suggerimenti:', error);
                hideLoading();
                // Non nascondere i suggerimenti esistenti in caso di errore
                if (!hasSuggestions) {
                    suggestionsContainer.innerHTML = '';
                }
            } finally {
                isLoadingSuggestions = false;
            }
        };
        
        // Carica suggerimenti al focus (solo se non ci sono già)
        input.addEventListener('focus', () => {
            if (!hasSuggestions) {
                clearTimeout(suggestionTimeout);
                suggestionTimeout = setTimeout(loadSuggestions, 500);
            }
        });
        
        // Carica suggerimenti dopo che l'utente smette di digitare (debounce più lungo)
        input.addEventListener('input', () => {
            clearTimeout(suggestionTimeout);
            // Aumenta il debounce a 2 secondi per evitare ricaricamenti troppo frequenti
            suggestionTimeout = setTimeout(loadSuggestions, 2000);
        });
        
        // Carica suggerimenti iniziali dopo un breve delay
        setTimeout(loadSuggestions, 800);
    }

    // Focus on input
    if (input && !input.disabled) {
        setTimeout(() => input.focus(), 100);
    }

    // Load saved value if exists
    if (wizardData[question.id]) {
        if (input && !input.disabled) {
            input.value = wizardData[question.id];
        }
    }
}

function renderInput(question) {
    let html = '';
    const suggestionContainerId = `suggestions-${question.id}`;
    const showSuggestions = question.type === 'text' || question.type === 'textarea';

    switch (question.type) {
        case 'text':
            html = `<input 
                type="text" 
                id="wizard-${question.id}" 
                class="wizard-input" 
                placeholder="${question.placeholder || ''}"
                ${question.required ? 'required' : ''}
            >`;
            if (showSuggestions) {
                html += `<div id="${suggestionContainerId}" class="suggestions-container"></div>`;
            }
            break;
        case 'number':
            html = `<input 
                type="number" 
                id="wizard-${question.id}" 
                class="wizard-input" 
                placeholder="${question.placeholder || ''}"
                ${question.min !== undefined ? `min="${question.min}"` : ''}
                ${question.max !== undefined ? `max="${question.max}"` : ''}
                ${question.required ? 'required' : ''}
            >`;
            break;
        case 'textarea':
            html = `<textarea 
                id="wizard-${question.id}" 
                class="wizard-input wizard-textarea" 
                rows="${question.rows || 4}"
                placeholder="${question.placeholder || ''}"
                ${question.required && !question.allowAutoDetect ? 'required' : ''}
            ></textarea>`;
            
            if (showSuggestions) {
                html += `<div id="${suggestionContainerId}" class="suggestions-container"></div>`;
            }
            
            // Aggiungi checkbox per auto-rilevamento se consentito
            if (question.allowAutoDetect) {
                const autoDetectId = `${question.id}_auto_detect`;
                html += `
                    <div style="margin-top: 15px;">
                        <label style="display: flex; align-items: center; cursor: pointer; font-size: 14px; color: #64748b;">
                            <input 
                                type="checkbox" 
                                id="${autoDetectId}" 
                                style="margin-right: 8px; width: 18px; height: 18px; cursor: pointer;"
                            >
                            <span>Non lo so, trova tu il mercato target</span>
                        </label>
                    </div>
                `;
            }
            break;
        case 'select':
            html = `<select 
                id="wizard-${question.id}" 
                class="wizard-input wizard-select"
                ${question.required ? 'required' : ''}
            >`;
            question.options.forEach(opt => {
                html += `<option value="${opt.value}">${opt.label}</option>`;
            });
            html += `</select>`;
            break;
    }

    return html;
}

function updateNavigation() {
    if (!wizardNavigation) wizardNavigation = document.getElementById('wizardNavigation');
    if (!prevBtn) prevBtn = document.getElementById('prevBtn');
    if (!nextBtn) nextBtn = document.getElementById('nextBtn');
    
    if (!wizardNavigation || !prevBtn || !nextBtn) return;
    
    wizardNavigation.style.display = 'flex';
    prevBtn.style.display = currentStep > 0 ? 'block' : 'none';
    
    if (currentStep === questions.length - 1) {
        nextBtn.textContent = 'Genera Business Plan';
        nextBtn.classList.add('btn-large');
    } else {
        nextBtn.textContent = 'Avanti';
        nextBtn.classList.remove('btn-large');
    }
}

function validateWizardStep() {
    const question = questions[currentStep];
    if (!question) return true;

    // Se ha auto-rilevamento e checkbox selezionato, skip validazione
    if (question.allowAutoDetect) {
        const autoDetectCheckbox = document.getElementById(`${question.id}_auto_detect`);
        if (autoDetectCheckbox && autoDetectCheckbox.checked) {
            return true;
        }
    }

    const input = document.getElementById(`wizard-${question.id}`);
    if (!input) return true;

    if (question.required && !input.value.trim()) {
        input.classList.add('error');
        input.focus();
        return false;
    }

    input.classList.remove('error');
    return true;
}

function saveCurrentStep() {
    const question = questions[currentStep];
    if (!question) return;

    // Gestisci auto-rilevamento mercato target
    if (question.allowAutoDetect) {
        const autoDetectCheckbox = document.getElementById(`${question.id}_auto_detect`);
        if (autoDetectCheckbox && autoDetectCheckbox.checked) {
            wizardData[question.id] = 'AUTO_DETECT';
            wizardData[`${question.id}_auto_detect`] = true;
            return;
        } else {
            wizardData[`${question.id}_auto_detect`] = false;
        }
    }

    const input = document.getElementById(`wizard-${question.id}`);
    if (input) {
        wizardData[question.id] = input.value.trim();
    }
}

function nextStep() {
    if (!validateWizardStep()) {
        return;
    }

    saveCurrentStep();

    if (currentStep < questions.length - 1) {
        currentStep++;
        renderCurrentStep();
        renderProgressSteps();
        updateNavigation();
    } else {
        // Last step - generate business plan
        generateBusinessPlanFromWizard();
    }
}

function prevStep() {
    if (currentStep > 0) {
        saveCurrentStep();
        currentStep--;
        renderCurrentStep();
        renderProgressSteps();
        updateNavigation();
    }
}

async function generateBusinessPlanFromWizard() {
    saveCurrentStep();
    
    // Ensure elements are initialized
    if (!wizardContainer) wizardContainer = document.getElementById('wizardContainer');
    if (!wizardNavigation) wizardNavigation = document.getElementById('wizardNavigation');
    if (!loadingState) loadingState = document.getElementById('loadingState');
    if (!resultState) resultState = document.getElementById('resultState');
    if (!planContent) planContent = document.getElementById('planContent');
    
    // Hide wizard
    if (wizardContainer) wizardContainer.style.display = 'none';
    if (wizardNavigation) wizardNavigation.style.display = 'none';
    
    // PRIMA: Richiedi il pagamento prima di generare il documento
    try {
        // Salva i dati del wizard in localStorage per recuperarli dopo il redirect
        try {
            const dataToSave = JSON.stringify(wizardData);
            localStorage.setItem('pendingBusinessPlanData', dataToSave);
            localStorage.setItem('pendingDocumentType', 'business-plan');
            console.log('✅ Dati wizard salvati in localStorage');
            console.log('Dimensione dati salvati:', dataToSave.length, 'caratteri');
            
            // Verifica che siano stati salvati correttamente
            const verify = localStorage.getItem('pendingBusinessPlanData');
            if (!verify) {
                throw new Error('Dati non salvati correttamente in localStorage');
            }
            console.log('✅ Verifica salvataggio: dati presenti in localStorage');
        } catch (e) {
            console.error('❌ ERRORE nel salvataggio localStorage:', e);
            console.warn('⚠️ Fallback: salva in memoria (i dati potrebbero andare persi dopo il redirect)');
            // Fallback: salva in memoria
            window.pendingBusinessPlanData = wizardData;
        }
        
        await handlePayment('business-plan');
        // Se il pagamento è stato avviato, la funzione reindirizza a Stripe
        // Il codice qui sotto verrà eseguito solo se l'utente annulla
        return;
    } catch (error) {
        if (error.message !== 'Pagamento annullato') {
            alert('Errore nel pagamento: ' + error.message);
        }
        // Rimuovi i dati salvati se l'utente annulla
        try {
            localStorage.removeItem('pendingBusinessPlanData');
            localStorage.removeItem('pendingDocumentType');
        } catch (e) {}
        // Ripristina il wizard se l'utente annulla
        if (wizardContainer) wizardContainer.style.display = 'block';
        if (wizardNavigation) wizardNavigation.style.display = 'flex';
        return;
    }
}

// Funzione per generare il business plan dopo il pagamento verificato
async function generateBusinessPlanAfterPayment(wizardData) {
    // Ensure elements are initialized
    if (!loadingState) loadingState = document.getElementById('loadingState');
    if (!resultState) resultState = document.getElementById('resultState');
    if (!planContent) planContent = document.getElementById('planContent');
    
    // Show loading
    if (loadingState) {
        loadingState.style.display = 'block';
        const loadingText = loadingState.querySelector('p');
        if (loadingText) {
            loadingText.textContent = 'Stiamo creando il tuo business plan professionale... Questo può richiedere 3-5 minuti. Attendi, non chiudere la pagina.';
            
            setTimeout(() => {
                if (loadingText && loadingState.style.display !== 'none') {
                    loadingText.textContent = 'Generazione in corso... Stiamo analizzando i dati e creando il documento. Attendi ancora qualche minuto.';
                }
            }, 30000);
            
            setTimeout(() => {
                if (loadingText && loadingState.style.display !== 'none') {
                    loadingText.textContent = 'Generazione ancora in corso... Stiamo finalizzando tutti i dettagli del tuo business plan. Attendi ancora.';
                }
            }, 120000);
        }
    }

    try {
        console.log('=== INIZIO GENERAZIONE BUSINESS PLAN (DOPO PAGAMENTO) ===');
        console.log('Dati wizard:', wizardData);
        
        // Usa generateWithAI che chiama GPT tramite prompt.json
        // Se fallisce, usa automaticamente il template come fallback
        console.log('Chiamata generateWithAI...');
        const result = await generateWithAI(wizardData);
        
        // Gestisci sia il caso in cui viene restituito un oggetto {html, json} che una stringa (fallback)
        let businessPlanHTML;
        let jsonData = null;
        
        if (typeof result === 'object' && result !== null && result.html) {
            // Nuovo formato: oggetto con html e json
            businessPlanHTML = result.html;
            jsonData = result.json || null;
            console.log('Risultato in formato oggetto - HTML e JSON ricevuti');
        } else if (typeof result === 'string') {
            // Formato legacy: solo stringa HTML (fallback template)
            businessPlanHTML = result;
            jsonData = null;
            console.log('Risultato in formato stringa (template fallback)');
        } else {
            throw new Error('generateWithAI ha restituito un formato non valido: ' + typeof result);
        }
        
        console.log('HTML ricevuto. Lunghezza:', businessPlanHTML?.length || 0);
        console.log('JSON disponibile:', !!jsonData);
        
        if (!businessPlanHTML) {
            throw new Error('generateWithAI ha restituito un HTML null o undefined');
        }
        
        // Verifica che gli elementi DOM esistano
        if (!planContent) {
            console.error('ERRORE: planContent non trovato!');
            planContent = document.getElementById('planContent');
        }
        if (!loadingState) {
            loadingState = document.getElementById('loadingState');
        }
        if (!resultState) {
            resultState = document.getElementById('resultState');
        }
        
        console.log('Elementi DOM:', {
            planContent: !!planContent,
            loadingState: !!loadingState,
            resultState: !!resultState
        });
        
        // Inserisci l'HTML nel contenuto (solo preview iniziale)
        if (planContent) {
            console.log('Inserimento HTML in planContent...');
            
            // Mostra solo una preview (primi 6000 caratteri) con pulsante per espandere
            const previewLength = 6000;
            const showFullContent = businessPlanHTML.length <= previewLength;
            
            if (showFullContent) {
                // Se il contenuto è breve, mostra tutto
                planContent.innerHTML = businessPlanHTML;
            } else {
                // Mostra solo preview con pulsante per espandere
                const previewHTML = businessPlanHTML.substring(0, previewLength);
                // Trova l'ultimo tag chiuso per evitare HTML rotto
                const lastTagIndex = previewHTML.lastIndexOf('</');
                const safePreview = lastTagIndex > 0 ? previewHTML.substring(0, previewHTML.indexOf('>', lastTagIndex) + 1) : previewHTML;
                
                planContent.innerHTML = safePreview + 
                    '<div style="margin: 30px 0; padding: 20px; background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 8px; text-align: center;">' +
                    '<p style="margin: 0 0 15px 0; color: #64748b; font-size: 1.1em;">📄 Contenuto troncato per migliorare la leggibilità</p>' +
                    '<button id="showFullContentBtn" style="padding: 12px 24px; background: #2563eb; color: white; border: none; border-radius: 6px; font-size: 1em; cursor: pointer; font-weight: 600;">Mostra tutto il contenuto</button>' +
                    '<p style="margin: 15px 0 0 0; color: #94a3b8; font-size: 0.9em;">Il PDF completo contiene tutte le informazioni</p>' +
                    '</div>';
                
                // Salva l'HTML completo per quando l'utente clicca "Mostra tutto"
                planContent.dataset.fullContent = businessPlanHTML;
                
                // Aggiungi event listener al pulsante
                setTimeout(() => {
                    const showFullBtn = document.getElementById('showFullContentBtn');
                    if (showFullBtn) {
                        showFullBtn.addEventListener('click', () => {
                            planContent.innerHTML = planContent.dataset.fullContent;
                        });
                    }
                }, 100);
            }
            
            console.log('HTML inserito. Contenuto planContent:', planContent.innerHTML.substring(0, 200));
        } else {
            console.error('ERRORE: planContent non disponibile!');
        }
        
        // Nascondi loading
        if (loadingState) {
            loadingState.style.display = 'none';
            console.log('Loading nascosto');
        }
        
        // Salva anche il JSON raw se disponibile (dalla chiamata GPT)
        window.currentPlanData = {
            ...wizardData,
            content: businessPlanHTML,
            jsonData: jsonData // JSON estratto dal risultato
        };
        
        // Salva anche in window.lastBusinessPlanJSON per compatibilità
        if (jsonData) {
            window.lastBusinessPlanJSON = jsonData;
            console.log('✅ JSON salvato anche in window.lastBusinessPlanJSON per compatibilità');
        }
        
        console.log('Dati salvati in window.currentPlanData');
        console.log('JSON disponibile in currentPlanData:', !!window.currentPlanData.jsonData);
        if (window.currentPlanData.jsonData) {
            console.log('Chiavi JSON salvate:', Object.keys(window.currentPlanData.jsonData));
        } else {
            console.warn('⚠️ JSON non disponibile - potrebbe essere stato usato il template fallback');
        }
        
        // Mostra offerta upsell prima del risultato
        showUpsellOffer('business-plan', jsonData).then(accepted => {
            if (accepted) {
                // L'utente ha accettato l'upsell, genereremo anche l'analisi di mercato
                console.log('✅ Upsell accettato, procederemo con entrambi i servizi');
            }
            // Mostra il risultato dopo l'upsell (accettato o rifiutato)
            if (resultState) {
                resultState.style.display = 'block';
                console.log('✅ Result mostrato');
            }
        });
        
        console.log('=== GENERAZIONE COMPLETATA ===');
        
    } catch (error) {
        console.error('=== ERRORE NELLA GENERAZIONE ===');
        console.error('Errore completo:', error);
        console.error('Stack:', error.stack);
        alert('Si è verificato un errore durante la generazione del business plan: ' + error.message + '\n\nControlla la console per maggiori dettagli.');
        if (wizardContainer) wizardContainer.style.display = 'block';
        if (wizardNavigation) wizardNavigation.style.display = 'flex';
        if (loadingState) loadingState.style.display = 'none';
    }
}

// Initialize all event listeners when DOM is ready
function initializeEventListeners() {
    console.log('Initializing event listeners...');
    
    // Initialize DOM Elements
    planModal = document.getElementById('planModal');
    closeModal = document.getElementById('closeModal');
    startPlanBtn = document.getElementById('startPlanBtn');
    createPlanBtn = document.getElementById('createPlanBtn');
    ctaPlanBtn = document.getElementById('ctaPlanBtn');
    loadingState = document.getElementById('loadingState');
    resultState = document.getElementById('resultState');
    planContent = document.getElementById('planContent');
    downloadPdfBtn = document.getElementById('downloadPdfBtn');
    editPlanBtn = document.getElementById('editPlanBtn');
    wizardContainer = document.getElementById('wizardContainer');
    wizardNavigation = document.getElementById('wizardNavigation');
    prevBtn = document.getElementById('prevBtn');
    nextBtn = document.getElementById('nextBtn');
    progressBar = document.getElementById('progressBar');
    progressSteps = document.getElementById('progressSteps');

    console.log('Elements found:', {
        planModal: !!planModal,
        startPlanBtn: !!startPlanBtn,
        createPlanBtn: !!createPlanBtn,
        ctaPlanBtn: !!ctaPlanBtn
    });

    if (startPlanBtn) {
        startPlanBtn.addEventListener('click', () => {
            console.log('startPlanBtn clicked');
            openModal();
        });
        console.log('startPlanBtn listener added');
    } else {
        console.warn('startPlanBtn not found!');
    }
    if (createPlanBtn) {
        createPlanBtn.addEventListener('click', () => {
            console.log('createPlanBtn clicked');
            openModal();
        });
        console.log('createPlanBtn listener added');
    } else {
        console.warn('createPlanBtn not found!');
    }
    if (ctaPlanBtn) {
        ctaPlanBtn.addEventListener('click', () => {
            console.log('ctaPlanBtn clicked');
            openModal();
        });
        console.log('ctaPlanBtn listener added');
    } else {
        console.warn('ctaPlanBtn not found!');
    }
    if (closeModal) closeModal.addEventListener('click', closeModalFunc);
    if (nextBtn) nextBtn.addEventListener('click', nextStep);
    if (prevBtn) prevBtn.addEventListener('click', prevStep);
    if (downloadPdfBtn) downloadPdfBtn.addEventListener('click', generatePDF);
    
    // Pulsante per scaricare JSON
    const downloadJsonBtn = document.getElementById('downloadJsonBtn');
    if (downloadJsonBtn) {
        downloadJsonBtn.addEventListener('click', () => {
            if (!window.currentPlanData || !window.currentPlanData.jsonData) {
                alert('Nessun dato JSON disponibile. Il business plan potrebbe essere stato generato con il template base.');
                return;
            }
            
            const jsonData = window.currentPlanData.jsonData;
            const jsonString = JSON.stringify(jsonData, null, 2);
            const blob = new Blob([jsonString], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `business-plan-${window.currentPlanData.companyName?.replace(/\s+/g, '-') || 'data'}.json`;
            a.click();
            URL.revokeObjectURL(url);
        });
    }
    
    if (editPlanBtn) {
        editPlanBtn.addEventListener('click', () => {
            const editText = prompt('Descrivi cosa vorresti modificare nel business plan:');
            if (!editText) return;
            
            const loadingState = document.getElementById('loadingState');
            const resultState = document.getElementById('resultState');
            if (loadingState) loadingState.style.display = 'block';
            if (resultState) resultState.style.display = 'none';
            
            setTimeout(() => {
                alert('Funzionalità di modifica AI in sviluppo. Per ora, puoi rigenerare il piano con nuove informazioni.');
                if (loadingState) loadingState.style.display = 'none';
                if (resultState) resultState.style.display = 'block';
            }, 1500);
        });
    }

    // Feature buttons
    const marketAnalysisBtn = document.getElementById('marketAnalysisBtn');
    const featurePlanBtn = document.getElementById('featurePlanBtn');
    const featureAnalysisBtn = document.getElementById('featureAnalysisBtn');

    if (marketAnalysisBtn) {
        marketAnalysisBtn.addEventListener('click', () => {
            console.log('marketAnalysisBtn clicked');
            openAnalysisModal();
        });
    }
    if (featurePlanBtn) {
        featurePlanBtn.addEventListener('click', () => {
            console.log('featurePlanBtn clicked');
            openModal();
        });
    }
    if (featureAnalysisBtn) {
        featureAnalysisBtn.addEventListener('click', () => {
            console.log('featureAnalysisBtn clicked');
            openAnalysisModal();
        });
    }


    // Login buttons (funzionalità in sviluppo)
    const loginBtn = document.getElementById('loginBtn');
    const ctaLoginBtn = document.getElementById('ctaLoginBtn');
    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            console.log('Login button clicked');
            alert('Funzionalità di login in sviluppo');
        });
    }
    if (ctaLoginBtn) {
        ctaLoginBtn.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('CTA Login button clicked');
            alert('Funzionalità di login in sviluppo');
        });
    }

    // Close modals when clicking outside
    window.addEventListener('click', (e) => {
        if (planModal && e.target === planModal) {
            closeModalFunc();
        }
    });

    // Allow Enter key to proceed in wizard
    document.addEventListener('keydown', (e) => {
        if (planModal && planModal.style.display === 'block' && e.key === 'Enter' && !e.shiftKey) {
            const activeElement = document.activeElement;
            if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA' || activeElement.tagName === 'SELECT')) {
                e.preventDefault();
                nextStep();
            }
        }
    });
    
    console.log('Event listeners initialized');
}

// Wait for DOM to be fully loaded with retry mechanism
function initializeAll() {
    console.log('🚀 ===== INITIALIZE ALL =====');
    console.log('DOM loaded, initializing...');
    console.log('URL corrente:', window.location.href);
    
    // Inizializza gli elementi DOM necessari PRIMA di tutto
    initializeEventListeners();
    initializeAnalysisListeners();
    
    // Verifica pagamento dopo redirect da Stripe
    const urlParams = new URLSearchParams(window.location.search);
    const paymentStatus = urlParams.get('payment');
    const sessionId = urlParams.get('session_id');
    
    console.log('Parametri URL:', { paymentStatus, sessionId });
    
    if (paymentStatus === 'success' && sessionId) {
        console.log('🔍 ===== VERIFICA PAGAMENTO DOPO REDIRECT =====');
        console.log('Session ID:', sessionId);
        console.log('Payment Status:', paymentStatus);
        console.log('URL completa:', window.location.href);
        
        // Determina il tipo di documento dal localStorage
        const pendingDocType = localStorage.getItem('pendingDocumentType');
        console.log('Tipo documento salvato in localStorage:', pendingDocType);
        console.log('pendingBusinessPlanData:', localStorage.getItem('pendingBusinessPlanData') ? 'Presente' : 'Assente');
        console.log('pendingMarketAnalysisData:', localStorage.getItem('pendingMarketAnalysisData') ? 'Presente' : 'Assente');
        
        // Alert di debug (rimuovi in produzione)
        if (!pendingDocType) {
            console.error('❌ ERRORE CRITICO: pendingDocumentType non trovato in localStorage!');
            console.error('Tutti i dati localStorage:', {
                pendingDocumentType: localStorage.getItem('pendingDocumentType'),
                pendingBusinessPlanData: localStorage.getItem('pendingBusinessPlanData') ? 'Presente' : 'Assente',
                pendingMarketAnalysisData: localStorage.getItem('pendingMarketAnalysisData') ? 'Presente' : 'Assente'
            });
        }
        
        // Verifica solo il tipo di documento corretto
        if (pendingDocType === 'business-plan') {
            verifyPaymentAfterRedirect('business-plan').then(bpVerified => {
            if (bpVerified) {
                window.paymentVerified = true;
                window.paymentSessionId = sessionId;
                console.log('✅ Pagamento business plan verificato');
                
                // Se include upsell per analisi di mercato, verifica anche quello
                if (window.upsellPaid && window.upsellType === 'market-analysis') {
                    window.paymentVerified_analysis = true;
                    window.paymentSessionId_analysis = sessionId;
                    console.log('✅ Upsell analisi di mercato incluso nel pagamento');
                }
                
                // Genera il business plan dopo il pagamento verificato
                // Recupera i dati da localStorage o da memoria
                let wizardData = null;
                try {
                    const savedData = localStorage.getItem('pendingBusinessPlanData');
                    if (savedData) {
                        wizardData = JSON.parse(savedData);
                        localStorage.removeItem('pendingBusinessPlanData');
                        localStorage.removeItem('pendingDocumentType');
                        console.log('✅ Dati wizard recuperati da localStorage');
                    } else if (window.pendingBusinessPlanData) {
                        wizardData = window.pendingBusinessPlanData;
                        window.pendingBusinessPlanData = null;
                        console.log('✅ Dati wizard recuperati da memoria');
                    }
                } catch (e) {
                    console.error('Errore nel recupero dati wizard:', e);
                }
                
                if (wizardData) {
                    console.log('📄 Generazione business plan dopo pagamento verificato...');
                    console.log('Dati wizard recuperati:', Object.keys(wizardData));
                    
                    // Assicurati che gli elementi DOM siano inizializzati
                    if (!planModal) planModal = document.getElementById('planModal');
                    if (!wizardContainer) wizardContainer = document.getElementById('wizardContainer');
                    if (!wizardNavigation) wizardNavigation = document.getElementById('wizardNavigation');
                    if (!loadingState) loadingState = document.getElementById('loadingState');
                    if (!resultState) resultState = document.getElementById('resultState');
                    if (!planContent) planContent = document.getElementById('planContent');
                    
                    // Apri il modal del business plan
                    if (planModal) {
                        planModal.style.display = 'block';
                        document.body.style.overflow = 'hidden';
                        console.log('✅ Modal business plan aperto');
                        
                        // Nascondi wizard
                        if (wizardContainer) wizardContainer.style.display = 'none';
                        if (wizardNavigation) wizardNavigation.style.display = 'none';
                        if (resultState) resultState.style.display = 'none';
                        
                        // Genera il business plan dopo un breve delay
                        setTimeout(() => {
                            generateBusinessPlanAfterPayment(wizardData);
                        }, 300);
                    } else {
                        console.error('❌ Modal business plan non trovato');
                        alert('Errore: modal non trovato. Ricarica la pagina.');
                    }
                } else {
                    console.error('❌ Dati wizard non trovati dopo il pagamento');
                    alert('Errore: dati del wizard non trovati. Completa nuovamente il wizard.');
                }
            } else {
                console.error('❌ Pagamento business plan non verificato');
            }
        });
        } else if (pendingDocType === 'market-analysis') {
            console.log('📋 Verifica pagamento per market-analysis...');
            verifyPaymentAfterRedirect('market-analysis').then(maVerified => {
                console.log('📋 Risultato verifica market-analysis:', maVerified);
                if (maVerified) {
                    window.paymentVerified_analysis = true;
                    window.paymentSessionId_analysis = sessionId;
                    console.log('✅ Pagamento analisi di mercato verificato');
                    
                    // Se include upsell per business plan, verifica anche quello
                    if (window.upsellPaid && window.upsellType === 'business-plan') {
                        window.paymentVerified = true;
                        window.paymentSessionId = sessionId;
                        console.log('✅ Upsell business plan incluso nel pagamento');
                    }
                    
                    // Genera l'analisi di mercato dopo il pagamento verificato
                    // Recupera i dati da localStorage o da memoria
                    let analysisWizardData = null;
                    try {
                        const savedData = localStorage.getItem('pendingMarketAnalysisData');
                        if (savedData) {
                            analysisWizardData = JSON.parse(savedData);
                            localStorage.removeItem('pendingMarketAnalysisData');
                            localStorage.removeItem('pendingDocumentType');
                            console.log('✅ Dati analisi recuperati da localStorage');
                        } else if (window.pendingMarketAnalysisData) {
                            analysisWizardData = window.pendingMarketAnalysisData;
                            window.pendingMarketAnalysisData = null;
                            console.log('✅ Dati analisi recuperati da memoria');
                        }
                    } catch (e) {
                        console.error('Errore nel recupero dati analisi:', e);
                    }
                    
                    if (analysisWizardData) {
                        console.log('📄 Generazione analisi di mercato dopo pagamento verificato...');
                        console.log('Dati analisi recuperati:', Object.keys(analysisWizardData));
                        
                        // Assicurati che gli elementi DOM siano inizializzati
                        if (!analysisModal) analysisModal = document.getElementById('analysisModal');
                        if (!analysisWizardContainer) analysisWizardContainer = document.getElementById('analysisWizardContainer');
                        if (!analysisWizardNavigation) analysisWizardNavigation = document.getElementById('analysisWizardNavigation');
                        if (!analysisLoadingState) analysisLoadingState = document.getElementById('analysisLoadingState');
                        if (!analysisResultState) analysisResultState = document.getElementById('analysisResultState');
                        if (!analysisContent) analysisContent = document.getElementById('analysisContent');
                        
                        // Apri il modal dell'analisi
                        if (analysisModal) {
                            analysisModal.style.display = 'block';
                            document.body.style.overflow = 'hidden';
                            console.log('✅ Modal analisi aperto');
                            
                            // Nascondi wizard
                            if (analysisWizardContainer) analysisWizardContainer.style.display = 'none';
                            if (analysisWizardNavigation) analysisWizardNavigation.style.display = 'none';
                            if (analysisResultState) analysisResultState.style.display = 'none';
                            
                            // Genera l'analisi dopo un breve delay
                            setTimeout(() => {
                                generateMarketAnalysisAfterPayment(analysisWizardData);
                            }, 300);
                        } else {
                            console.error('❌ Modal analisi non trovato');
                            alert('Errore: modal non trovato. Ricarica la pagina.');
                        }
                    } else {
                        console.error('❌ Dati analisi non trovati dopo il pagamento');
                        console.log('localStorage pendingMarketAnalysisData:', localStorage.getItem('pendingMarketAnalysisData'));
                        alert('Errore: dati dell\'analisi non trovati. Completa nuovamente il wizard.');
                    }
                } else {
                    console.error('❌ Pagamento analisi di mercato non verificato');
                }
            });
        } else {
            console.warn('⚠️ Tipo documento non trovato in localStorage!');
            console.warn('Tentativo di recupero da URL o verifica entrambi...');
            
            // Prova a determinare dal sessionId verificando entrambi
            Promise.all([
                verifyPaymentAfterRedirect('business-plan'),
                verifyPaymentAfterRedirect('market-analysis')
            ]).then(([bpVerified, maVerified]) => {
                console.log('Verifica fallback - BP:', bpVerified, 'MA:', maVerified);
                
                if (bpVerified) {
                    // Prova a recuperare i dati business plan
                    const savedData = localStorage.getItem('pendingBusinessPlanData');
                    if (savedData) {
                        try {
                            const wizardData = JSON.parse(savedData);
                            localStorage.removeItem('pendingBusinessPlanData');
                            localStorage.setItem('pendingDocumentType', 'business-plan');
                            console.log('✅ Dati business plan recuperati in fallback');
                            
                            // Inizializza elementi DOM
                            if (!planModal) planModal = document.getElementById('planModal');
                            if (!wizardContainer) wizardContainer = document.getElementById('wizardContainer');
                            if (!wizardNavigation) wizardNavigation = document.getElementById('wizardNavigation');
                            
                            // Apri modal e genera
                            if (planModal) {
                                planModal.style.display = 'block';
                                document.body.style.overflow = 'hidden';
                                if (wizardContainer) wizardContainer.style.display = 'none';
                                if (wizardNavigation) wizardNavigation.style.display = 'none';
                                setTimeout(() => generateBusinessPlanAfterPayment(wizardData), 300);
                            }
                        } catch (e) {
                            console.error('Errore parsing dati business plan:', e);
                        }
                    } else {
                        console.error('❌ Dati business plan non trovati in localStorage');
                    }
                } else if (maVerified) {
                    // Prova a recuperare i dati analisi
                    const savedData = localStorage.getItem('pendingMarketAnalysisData');
                    if (savedData) {
                        try {
                            const analysisWizardData = JSON.parse(savedData);
                            localStorage.removeItem('pendingMarketAnalysisData');
                            localStorage.setItem('pendingDocumentType', 'market-analysis');
                            console.log('✅ Dati analisi recuperati in fallback');
                            
                            // Inizializza elementi DOM
                            if (!analysisModal) analysisModal = document.getElementById('analysisModal');
                            if (!analysisWizardContainer) analysisWizardContainer = document.getElementById('analysisWizardContainer');
                            if (!analysisWizardNavigation) analysisWizardNavigation = document.getElementById('analysisWizardNavigation');
                            
                            // Apri modal e genera
                            if (analysisModal) {
                                analysisModal.style.display = 'block';
                                document.body.style.overflow = 'hidden';
                                if (analysisWizardContainer) analysisWizardContainer.style.display = 'none';
                                if (analysisWizardNavigation) analysisWizardNavigation.style.display = 'none';
                                setTimeout(() => generateMarketAnalysisAfterPayment(analysisWizardData), 300);
                            }
                        } catch (e) {
                            console.error('Errore parsing dati analisi:', e);
                        }
                    } else {
                        console.error('❌ Dati analisi non trovati in localStorage');
                    }
                } else {
                    console.error('❌ Nessun pagamento verificato in fallback');
                    alert('Errore: impossibile verificare il pagamento. Se hai già pagato, contatta il supporto.');
                }
            });
        }
    }
    
    // Inizializza gli event listeners solo se non c'è un pagamento in corso
    // (se c'è un pagamento, sono già stati inizializzati all'inizio)
    if (paymentStatus !== 'success') {
        initializeEventListeners();
        initializeAnalysisListeners();
        console.log('All listeners initialized');
        
        // Verify that key buttons are working
        setTimeout(() => {
            const testBtn = document.getElementById('startPlanBtn');
            if (testBtn) {
                console.log('✓ startPlanBtn found and should be working');
            } else {
                console.error('✗ startPlanBtn NOT found after initialization!');
            }
        }, 100);
    } else {
        console.log('⚠️ Pagamento in corso, event listeners già inizializzati');
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAll);
} else {
    // DOM already loaded, but wait a bit to ensure everything is ready
    if (document.body) {
        initializeAll();
    } else {
        // Fallback: wait for body
        setTimeout(initializeAll, 10);
    }
}

// Business Plan Template Generator
function generateBusinessPlan(data) {
    const getIndustryLabel = (value) => {
        const industry = questions.find(q => q.id === 'industry');
        if (industry && industry.options) {
            const option = industry.options.find(opt => opt.value === value);
            return option ? option.label : value;
        }
        return value;
    };

    const sections = {
        executiveSummary: `
            <h4>Sintesi Esecutiva</h4>
            <p><strong>Panoramica del Business</strong></p>
            <p>Benvenuti a <strong>${data.companyName || 'N/A'}</strong>, un'azienda operante nel settore ${getIndustryLabel(data.industry) || 'N/A'} situata a ${data.location || 'N/A'}.</p>
            ${data.foundingYear ? `<p>Fondata nel ${data.foundingYear}, la nostra azienda è dedicata a ${data.description || 'N/A'}.</p>` : `<p>La nostra azienda è dedicata a ${data.description || 'N/A'}.</p>`}
            <p>Operiamo nel settore ${getIndustryLabel(data.industry) || 'N/A'} con un team di ${data.employees || 'N/A'} dipendenti dedicati, impegnati a fornire un eccellente servizio ai nostri clienti.</p>
        `,
        businessDescription: `
            <h4>Descrizione del Business</h4>
            <p>${data.description || 'N/A'}</p>
            ${data.targetMarket ? `<p><strong>Mercato Target:</strong> ${data.targetMarket}</p>` : ''}
            ${data.competitiveAdvantage ? `<p><strong>Vantaggio Competitivo:</strong> ${data.competitiveAdvantage}</p>` : ''}
        `,
        marketAnalysis: `
            <h4>Analisi di Mercato</h4>
            ${data.targetMarket ? `<p>Il nostro mercato target è composto da: ${data.targetMarket}</p>` : ''}
            <p>Il mercato per ${getIndustryLabel(data.industry) || 'il nostro settore'} mostra segnali positivi di crescita. La nostra posizione strategica a ${data.location || 'N/A'} ci permette di servire efficacemente il nostro mercato target.</p>
            <p>Analizzando le tendenze del settore, identificiamo opportunità significative per la crescita e l'espansione del nostro business.</p>
        `,
        organization: `
            <h4>Organizzazione e Management</h4>
            <p>La nostra organizzazione è strutturata per supportare efficacemente le operazioni aziendali. Con ${data.employees || 'N/A'} dipendenti, abbiamo creato un team coeso e competente.</p>
            <p>La struttura organizzativa è progettata per promuovere l'innovazione, l'efficienza operativa e l'eccellenza nel servizio clienti.</p>
        `,
        productsServices: `
            <h4>Prodotti e Servizi</h4>
            <p>Offriamo una gamma completa di prodotti e servizi nel settore ${getIndustryLabel(data.industry) || 'N/A'}, progettati per soddisfare le esigenze dei nostri clienti.</p>
            <p>Il nostro focus principale è sulla qualità, l'innovazione e il valore aggiunto che portiamo ai nostri clienti.</p>
        `,
        marketingStrategy: `
            <h4>Strategia di Marketing</h4>
            <p>La nostra strategia di marketing si concentra su canali digitali e tradizionali per raggiungere il nostro mercato target.</p>
            <p>Utilizziamo un approccio integrato che include marketing digitale, partnership strategiche e presenza locale per massimizzare la nostra visibilità e acquisizione clienti.</p>
        `,
        financialProjections: `
            <h4>Proiezioni Finanziarie</h4>
            ${data.revenue ? `<p><strong>Fatturato Attuale/Previsto:</strong> €${parseInt(data.revenue).toLocaleString('it-IT')}</p>` : '<p>Le proiezioni finanziarie mostrano una crescita sostenibile nel tempo.</p>'}
            <p>Il nostro modello di business è progettato per garantire redditività e sostenibilità a lungo termine.</p>
            <p>Prevediamo una crescita costante dei ricavi attraverso l'espansione della base clienti e l'ottimizzazione delle operazioni.</p>
        `,
        fundingRequest: `
            <h4>Richiesta di Finanziamento</h4>
            ${data.fundingNeeds ? `<p>${data.fundingNeeds}</p>` : '<p>Stiamo cercando finanziamenti per supportare la crescita e l\'espansione del nostro business.</p>'}
            <p>I fondi saranno utilizzati per migliorare le infrastrutture, espandere il team e aumentare le attività di marketing.</p>
        `,
        goals: data.goals ? `
            <h4>Obiettivi e Strategia</h4>
            <p>${data.goals}</p>
        ` : '',
        appendix: `
            <h4>Appendice</h4>
            <p>Documenti aggiuntivi e informazioni di supporto sono disponibili su richiesta.</p>
        `
    };

    return Object.values(sections).filter(s => s.trim()).join('');
}

// Carica e prepara il prompt dal file prompt.json
async function loadPromptTemplate() {
    try {
        const response = await fetch('prompt.json');
        if (!response.ok) {
            throw new Error('Errore nel caricamento di prompt.json');
        }
        return await response.json();
    } catch (error) {
        console.error('Errore nel caricamento del template:', error);
        return null;
    }
}

// Prepara i dati utente in formato JSON per il prompt
function prepareUserInputJSON(formData) {
    const getIndustryLabel = (value) => {
        if (!value) return '';
        const industry = questions.find(q => q.id === 'industry');
        if (industry && industry.options) {
            const option = industry.options.find(opt => opt.value === value);
            return option ? option.label : value;
        }
        return value;
    };

    // Formatta i dati in un oggetto JSON strutturato
    // Rimuove i campi vuoti per mantenere il JSON pulito
    const userData = {};
    
    if (formData.companyName) userData.nome_azienda = formData.companyName;
    if (formData.industry) {
        const industryLabel = getIndustryLabel(formData.industry);
        if (industryLabel) userData.settore = industryLabel;
    }
    if (formData.location) userData.localita = formData.location;
    if (formData.foundingYear) userData.anno_fondazione = parseInt(formData.foundingYear);
    if (formData.description) userData.descrizione = formData.description;
    if (formData.businessModel) userData.modello_business = formData.businessModel;
    // Gestisci auto-rilevamento mercato target
    if (formData.targetMarket === 'AUTO_DETECT') {
        userData.mercato_target = '[DA IDENTIFICARE AUTOMATICAMENTE IN BASE ALLE INFORMAZIONI FORNITE]';
    } else if (formData.targetMarket) {
        userData.mercato_target = formData.targetMarket;
    }
    if (formData.competitiveAdvantage) userData.vantaggio_competitivo = formData.competitiveAdvantage;
    if (formData.pricing) userData.strategia_pricing = formData.pricing;
    if (formData.employees) userData.numero_dipendenti = parseInt(formData.employees) || 0;
    if (formData.revenue) userData.fatturato_attuale_previsto = parseFloat(formData.revenue);
    if (formData.costs) userData.costi_operativi = formData.costs;
    if (formData.initialInvestment) userData.investimento_iniziale = parseFloat(formData.initialInvestment);
    if (formData.fundingNeeds) userData.esigenze_finanziamento = formData.fundingNeeds;
    if (formData.channels) userData.canali_vendita = formData.channels;
    if (formData.goals) userData.obiettivi = formData.goals;

    return JSON.stringify(userData, null, 2);
}

// Costruisce il prompt completo sostituendo i placeholder
async function buildBusinessPlanPrompt(formData) {
    const promptTemplate = await loadPromptTemplate();
    
    if (!promptTemplate) {
        console.warn('Template non disponibile, uso fallback');
        return null;
    }

    // Prepara i dati utente in formato JSON
    const userInputJSON = prepareUserInputJSON(formData);
    
    // Ottieni l'orizzonte temporale selezionato dall'utente (default 24 mesi)
    const horizonMonths = formData.horizonMonths ? parseInt(formData.horizonMonths) : 24;
    
    // Crea una copia del template
    const prompt = JSON.parse(JSON.stringify(promptTemplate));
    
    // Sostituisci i placeholder nel testo del prompt
    const userMessage = prompt.input[1].content[0].text;
    const updatedUserMessage = userMessage
        .replace('{{USER_INPUT_JSON}}', userInputJSON)
        .replace('{{HORIZON_MONTHS}}', horizonMonths.toString());
    
    prompt.input[1].content[0].text = updatedUserMessage;
    
    // Stampa il prompt completo in console con formattazione migliore
    console.log('\n%c=== PROMPT COMPLETO PER BUSINESS PLAN ===', 'color: #2563eb; font-weight: bold; font-size: 14px;');
    console.log('%cPrompt JSON completo:', 'color: #10b981; font-weight: bold;');
    console.log(JSON.stringify(prompt, null, 2));
    console.log('\n%cTesto del messaggio utente:', 'color: #f59e0b; font-weight: bold;');
    console.log(updatedUserMessage);
    console.log('\n%cDati utente inseriti (JSON):', 'color: #8b5cf6; font-weight: bold;');
    console.log(userInputJSON);
    console.log('%cOrizzonte temporale:', 'color: #ef4444; font-weight: bold;', horizonMonths, 'mesi');
    console.log('%c=== FINE PROMPT ===\n', 'color: #2563eb; font-weight: bold; font-size: 14px;');
    
    return prompt;
}

// Generazione Business Plan tramite API Python Backend
async function generateWithAI(formData) {
    console.log('=== INIZIO generateWithAI ===');
    console.log('Timestamp:', new Date().toISOString());
    console.log('FormData ricevuto:', formData);
    console.log('API Base URL:', API_BASE_URL);
    
    // Ottieni l'orizzonte temporale
    const horizonMonths = formData.horizonMonths ? parseInt(formData.horizonMonths) : 24;
    
    try {
        console.log('Chiamata API backend Python...');
        console.log('URL:', `${API_BASE_URL}/api/generate-business-plan`);
        console.log('⚠️ NOTA: La generazione di un business plan completo può richiedere 3-5 minuti. Attendi...');
        console.log('⏱️ Timestamp inizio:', new Date().toISOString());
        
        // Crea un AbortController per timeout - aumentato a 20 minuti
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 1200000); // 20 minuti timeout
        const startTime = Date.now();
        
        let response;
        try {
            response = await fetch(`${API_BASE_URL}/api/generate-business-plan`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    formData: formData,
                    horizonMonths: horizonMonths
                }),
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            const fetchTime = ((Date.now() - startTime) / 1000).toFixed(2);
            console.log('✅ Fetch completata. Status:', response.status, response.statusText);
            console.log('⏱️ Tempo impiegato:', fetchTime, 'secondi');
        } catch (fetchError) {
            clearTimeout(timeoutId);
            console.error('❌ Errore nella chiamata fetch:', fetchError);
            
            let errorMessage = 'Errore sconosciuto nella chiamata API';
            if (fetchError.name === 'AbortError') {
                errorMessage = 'Timeout: la richiesta ha impiegato troppo tempo (oltre 20 minuti).';
            } else if (fetchError.name === 'TypeError') {
                if (fetchError.message.includes('Failed to fetch') || fetchError.message.includes('Load failed')) {
                    errorMessage = 'Errore di connessione: impossibile raggiungere il backend su Render. Verifica:\n' +
                        '- La connessione internet\n' +
                        '- Se il servizio era in pausa (cold start), riprova: la prima richiesta può richiedere 1-2 minuti\n' +
                        '- Eventuali problemi CORS';
                } else {
                    errorMessage = `Errore di tipo: ${fetchError.message}`;
                }
            } else {
                errorMessage = `Errore nella chiamata API: ${fetchError.message || 'Errore sconosciuto'}`;
            }
            
            throw new Error(errorMessage);
        }
        
        if (!response.ok) {
            let errorData;
            try {
                const text = await response.text();
                console.error('Risposta errore (raw):', text);
                errorData = JSON.parse(text);
            } catch (e) {
                errorData = { detail: `Errore HTTP ${response.status}: ${response.statusText}` };
            }
            console.error('Errore API - Status:', response.status);
            console.error('Dati errore:', errorData);
            const errorMessage = errorData.detail || errorData.message || errorData.error || 'Errore sconosciuto';
            throw new Error(`Errore API: ${response.status} - ${errorMessage}`);
        }
        
        const result = await response.json();
        console.log('✅ Risposta ricevuta dal backend');
        
        if (!result.success || !result.json) {
            throw new Error('Risposta API non valida - formato dati inatteso');
        }
        
        const businessPlanJSON = result.json;
        
        // LOG DETTAGLIATO DEL JSON PER DEBUG
        console.log('=== JSON BUSINESS PLAN RICEVUTO ===');
        console.log('Tipo dati ricevuti:', typeof businessPlanJSON);
        console.log('Chiavi disponibili:', Object.keys(businessPlanJSON || {}));
        console.log('--- JSON COMPLETO (formattato) ---');
        try {
            const jsonString = JSON.stringify(businessPlanJSON, null, 2);
            console.log(jsonString);
            console.log('--- FINE JSON ---');
        } catch (stringifyError) {
            console.error('Errore nella stringificazione JSON:', stringifyError);
            console.log('JSON raw:', businessPlanJSON);
        }
        console.log('=== FINE LOG JSON ===');
        
        // Salva il JSON in variabile globale e localStorage
        window.lastBusinessPlanJSON = businessPlanJSON;
        console.log('✅ JSON salvato in window.lastBusinessPlanJSON');
        
        try {
            localStorage.setItem('lastBusinessPlanJSON', JSON.stringify(businessPlanJSON));
            console.log('✅ JSON salvato anche in localStorage');
        } catch (storageError) {
            console.warn('⚠️ Impossibile salvare in localStorage:', storageError);
        }
        
        // Converti il JSON in HTML per la visualizzazione
        console.log('Inizio conversione JSON -> HTML...');
        const businessPlanHTML = convertBusinessPlanJSONToHTML(businessPlanJSON);
        console.log('Conversione completata. Lunghezza HTML:', businessPlanHTML.length);
        
        if (!businessPlanHTML || businessPlanHTML.trim() === '') {
            console.error('ERRORE: HTML generato è vuoto!');
            throw new Error('La conversione JSON->HTML ha prodotto un risultato vuoto');
        }
        
        console.log('=== generateWithAI completata con successo ===');
        return {
            html: businessPlanHTML,
            json: businessPlanJSON
        };
        
    } catch (error) {
        console.log('=== generateWithAI terminata con errore ===');
        console.error('Errore nella chiamata API:', error);
        console.error('Stack trace:', error.stack);
        
        const errorMessage = error.message || 'Errore sconosciuto';
        console.warn(`Errore API: ${errorMessage}. Uso template fallback.`);
        
        // Mostra popup di errore se si tratta di un errore di connessione
        if (errorMessage.includes('Errore di connessione') || errorMessage.includes('Failed to fetch')) {
            alert('❌ Errore di Connessione\n\n' + errorMessage + '\n\nSe il backend su Render era in pausa, riprova tra 1-2 minuti.\nIl sistema utilizzerà un template predefinito per continuare.');
        }
        
        // Fallback al template se la chiamata fallisce
        return generateBusinessPlan(formData);
    }
}

// Converte il JSON del business plan (da prompt.json) in HTML
// Funzione helper per convertire markdown in HTML
function markdownToHTML(markdown) {
    if (!markdown) return '';
    
    // Prima converti gli heading, bold, italic e liste
    let html = markdown
        // Headers (ordine importante: prima ###, poi ##, poi #)
        .replace(/^### (.*$)/gim, '<h5>$1</h5>')
        .replace(/^## (.*$)/gim, '<h4>$1</h4>')
        .replace(/^# (.*$)/gim, '<h3>$1</h3>')
        // Bold
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // Lists
        .replace(/^\- (.*$)/gim, '<li>$1</li>');
    
    // Ora dividi per paragrafi (doppio newline) ma gestisci correttamente heading e liste
    const paragraphs = html.split(/\n\n+/);
    let result = paragraphs.map(para => {
        para = para.trim();
        if (!para) return '';
        
        // Se contiene già un tag di heading, non avvolgere in <p>
        if (para.match(/^<h[1-6]>/)) {
            // Se l'heading è seguito da testo sulla stessa riga o righe successive, gestiscilo
            const lines = para.split('\n');
            let output = '';
            let currentParagraph = '';
            
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i].trim();
                if (!line) continue;
                
                if (line.match(/^<h[1-6]>/)) {
                    // Se c'era testo accumulato, chiudi il paragrafo
                    if (currentParagraph) {
                        output += '<p>' + currentParagraph.replace(/\n/g, '<br>') + '</p>';
                        currentParagraph = '';
                    }
                    output += line;
                } else if (line.startsWith('<li>')) {
                    // Se c'era testo accumulato, chiudi il paragrafo
                    if (currentParagraph) {
                        output += '<p>' + currentParagraph.replace(/\n/g, '<br>') + '</p>';
                        currentParagraph = '';
                    }
                    // Raggruppa le liste consecutive
                    let listItems = line;
                    while (i + 1 < lines.length && lines[i + 1].trim().startsWith('<li>')) {
                        i++;
                        listItems += '\n' + lines[i].trim();
                    }
                    output += '<ul>' + listItems + '</ul>';
                } else {
                    // Accumula testo normale
                    currentParagraph += (currentParagraph ? '\n' : '') + line;
                }
            }
            
            // Se rimane testo accumulato, chiudilo
            if (currentParagraph) {
                output += '<p>' + currentParagraph.replace(/\n/g, '<br>') + '</p>';
            }
            
            return output;
        }
        
        // Se inizia con <li>, è una lista
        if (para.startsWith('<li>')) {
            return '<ul>' + para + '</ul>';
        }
        
        // Altrimenti è un paragrafo normale
        return '<p>' + para.replace(/\n/g, '<br>') + '</p>';
    }).join('');
    
    return result;
}

function convertBusinessPlanJSONToHTML(bpData) {
    let html = '<div class="analysis-output">';
    
    // Helper per escape HTML
    const escape = (str) => String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    const formatCurrency = (num) => num?.toLocaleString('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00';
    const formatNumber = (num) => num?.toLocaleString('it-IT') || '0';

    // PDF Layout - Titolo e sottotitolo (stile come analisi di mercato)
    if (bpData.pdf_layout) {
        html += `<div class="analysis-header">`;
        html += `<h1>${escape(bpData.pdf_layout.titolo_documento || 'Business Plan')}</h1>`;
        if (bpData.pdf_layout.sottotitolo) {
            html += `<h2>${escape(bpData.pdf_layout.sottotitolo)}</h2>`;
        }
        // Meta info
        const meta = bpData.meta || {};
        const data = bpData.data || {};
        if (meta.data_generazione || data.company_name) {
            html += `<div class="meta-info">`;
            if (data.company_name) {
                html += `<span>Azienda: ${escape(data.company_name)}</span>`;
            }
            if (meta.data_generazione) {
                html += `<span>Generato il: ${escape(meta.data_generazione)}</span>`;
            }
            html += `</div>`;
        }
        html += `</div>`;
    }

    // Executive Summary (stile come analisi di mercato)
    if (bpData.executive_summary) {
        html += `<div class="analysis-section">`;
        html += `<h3>Executive Summary</h3>`;
        
        if (bpData.executive_summary.sintesi) {
            html += `<div class="analysis-card">${markdownToHTML(bpData.executive_summary.sintesi)}</div>`;
        }
        
        if (bpData.executive_summary.punti_chiave && bpData.executive_summary.punti_chiave.length > 0) {
            html += `<h4>Punti Chiave</h4>`;
            html += `<ul>`;
            bpData.executive_summary.punti_chiave.forEach(punto => {
                html += `<li>${escape(punto)}</li>`;
            });
            html += `</ul>`;
        }
        
        if (bpData.executive_summary.kpi_principali && bpData.executive_summary.kpi_principali.length > 0) {
            html += `<h4>KPI Principali</h4>`;
            html += `<div class="analysis-info-box">`;
            html += `<table style="width: 100%; border-collapse: collapse;">`;
            html += `<thead><tr><th>KPI</th><th>Valore</th><th>Scenario</th></tr></thead>`;
            html += `<tbody>`;
            bpData.executive_summary.kpi_principali.forEach(kpi => {
                html += `<tr>`;
                html += `<td><strong>${escape(kpi.nome)}</strong></td>`;
                html += `<td>${formatNumber(kpi.valore)} ${escape(kpi.unita)}</td>`;
                html += `<td>${escape(kpi.scenario)}</td>`;
                html += `</tr>`;
            });
            html += `</tbody></table>`;
            html += `</div>`;
        }
        
        if (bpData.executive_summary.raccomandazioni_30_60_90 && bpData.executive_summary.raccomandazioni_30_60_90.length > 0) {
            html += `<h4>Raccomandazioni 30-60-90 giorni</h4>`;
            html += `<ol>`;
            bpData.executive_summary.raccomandazioni_30_60_90.forEach(rec => {
                html += `<li><strong>${rec.orizzonte_giorni} giorni:</strong> ${escape(rec.azione)} (priorità: ${escape(rec.priorita)}) - ${escape(rec.motivazione)}</li>`;
            });
            html += `</ol>`;
        }
        html += `</div>`;
    }

    // Narrative Chapters - seguendo l'ordine di pdf_layout.chapter_order se disponibile
    const chapterOrder = bpData.pdf_layout?.chapter_order || [];
    const chaptersMap = {};
    
    if (bpData.narrative && bpData.narrative.chapters) {
        bpData.narrative.chapters.forEach(chapter => {
            chaptersMap[chapter.id] = chapter;
        });
        
        // Ordina i capitoli secondo chapter_order
        const orderedChapters = chapterOrder.length > 0 
            ? chapterOrder.map(id => chaptersMap[id]).filter(Boolean)
            : bpData.narrative.chapters;
        
        orderedChapters.forEach(chapter => {
            html += `<div class="analysis-section">`;
            html += `<h3>${escape(chapter.titolo || chapter.id)}</h3>`;
            if (chapter.contenuto_markdown) {
                html += `<div class="analysis-card">${markdownToHTML(chapter.contenuto_markdown)}</div>`;
            }
            
            // Aggiungi grafici associati al capitolo se presenti
            if (chapter.chart_ids && chapter.chart_ids.length > 0 && bpData.charts) {
                chapter.chart_ids.forEach(chartId => {
                    const chart = bpData.charts.find(c => c.id === chartId);
                    if (chart) {
                        html += `<div class="analysis-info-box">`;
                        html += `<h4>${escape(chart.titolo)}</h4>`;
                        html += `<p><em>Tipo:</em> ${escape(chart.tipo)} | <em>X:</em> ${escape(chart.x_label)} | <em>Y:</em> ${escape(chart.y_label)}</p>`;
                        if (chart.series && chart.series.length > 0) {
                            html += `<table style="width: 100%; border-collapse: collapse; margin: 10px 0;">`;
                            chart.series.forEach(serie => {
                                html += `<tr><th colspan="2" style="text-align: left; padding: 8px; background: #f1f5f9;">${escape(serie.name)}</th></tr>`;
                                if (serie.points && serie.points.length > 0) {
                                    serie.points.forEach(point => {
                                        html += `<tr><td style="padding: 6px; border-bottom: 1px solid #e2e8f0;">${escape(point.x)}</td><td style="padding: 6px; border-bottom: 1px solid #e2e8f0; text-align: right;">${formatNumber(point.y)}</td></tr>`;
                                    });
                                }
                            });
                            html += `</table>`;
                        }
                        if (chart.caption) {
                            html += `<p style="font-size: 0.9em; color: #64748b; font-style: italic;">${escape(chart.caption)}</p>`;
                        }
                        html += `</div>`;
                    }
                });
            }
            html += `</div>`;
        });
    }

    // Financials - Tabelle dettagliate mensili
    if (bpData.data && bpData.data.financials && bpData.data.financials.scenarios) {
        html += `<div class="analysis-section">`;
        html += `<h3>Proiezioni Finanziarie Dettagliate</h3>`;
        
        bpData.data.financials.scenarios.forEach(scenario => {
            html += `<div class="analysis-card">`;
            html += `<h4>Scenario ${escape(scenario.name)}</h4>`;
            
            if (scenario.assumption_deltas && scenario.assumption_deltas.length > 0) {
                html += `<p><strong>Assunzioni:</strong></p><ul>`;
                scenario.assumption_deltas.forEach(ass => {
                    html += `<li>${escape(ass)}</li>`;
                });
                html += `</ul>`;
            }
            
            if (scenario.monthly && scenario.monthly.length > 0) {
                html += `<table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 0.9em;">`;
                html += `<thead><tr style="background: #f1f5f9;">`;
                html += `<th style="padding: 8px; border: 1px solid #cbd5e1; text-align: left;">Mese</th>`;
                html += `<th style="padding: 8px; border: 1px solid #cbd5e1; text-align: right;">Clienti</th>`;
                html += `<th style="padding: 8px; border: 1px solid #cbd5e1; text-align: right;">Ricavi</th>`;
                html += `<th style="padding: 8px; border: 1px solid #cbd5e1; text-align: right;">COGS</th>`;
                html += `<th style="padding: 8px; border: 1px solid #cbd5e1; text-align: right;">Margine Lordo</th>`;
                html += `<th style="padding: 8px; border: 1px solid #cbd5e1; text-align: right;">Costi Fissi</th>`;
                html += `<th style="padding: 8px; border: 1px solid #cbd5e1; text-align: right;">Marketing</th>`;
                html += `<th style="padding: 8px; border: 1px solid #cbd5e1; text-align: right;">EBITDA</th>`;
                html += `<th style="padding: 8px; border: 1px solid #cbd5e1; text-align: right;">Cash Balance</th>`;
                html += `</tr></thead><tbody>`;
                
                scenario.monthly.forEach(month => {
                    html += `<tr>`;
                    html += `<td style="padding: 6px; border: 1px solid #cbd5e1;">M${month.month}</td>`;
                    html += `<td style="padding: 6px; border: 1px solid #cbd5e1; text-align: right;">${formatNumber(month.customers)}</td>`;
                    html += `<td style="padding: 6px; border: 1px solid #cbd5e1; text-align: right;">€${formatCurrency(month.revenue)}</td>`;
                    html += `<td style="padding: 6px; border: 1px solid #cbd5e1; text-align: right;">€${formatCurrency(month.cogs)}</td>`;
                    html += `<td style="padding: 6px; border: 1px solid #cbd5e1; text-align: right;">€${formatCurrency(month.gross_profit)}</td>`;
                    html += `<td style="padding: 6px; border: 1px solid #cbd5e1; text-align: right;">€${formatCurrency(month.fixed_costs)}</td>`;
                    html += `<td style="padding: 6px; border: 1px solid #cbd5e1; text-align: right;">€${formatCurrency(month.marketing_costs)}</td>`;
                    html += `<td style="padding: 6px; border: 1px solid #cbd5e1; text-align: right;">€${formatCurrency(month.ebitda)}</td>`;
                    html += `<td style="padding: 6px; border: 1px solid #cbd5e1; text-align: right;">€${formatCurrency(month.cash_balance)}</td>`;
                    html += `</tr>`;
                });
                
                html += `</tbody></table>`;
            }
            
            if (scenario.summary) {
                html += `<p><strong>Riepilogo Scenario ${escape(scenario.name)}:</strong></p>`;
                html += `<ul>`;
                html += `<li><strong>Ricavi Totali:</strong> €${formatCurrency(scenario.summary.total_revenue)}</li>`;
                html += `<li><strong>Margine Lordo Medio:</strong> ${formatNumber(scenario.summary.avg_gross_margin_percent)}%</li>`;
                html += `<li><strong>Break-even stimato:</strong> Mese ${scenario.summary.breakeven_month_estimate || 'N/A'}</li>`;
                html += `<li><strong>Saldo minimo di cassa:</strong> €${formatCurrency(scenario.summary.min_cash_balance)}</li>`;
                html += `<li><strong>Saldo finale di cassa:</strong> €${formatCurrency(scenario.summary.end_cash_balance)}</li>`;
                html += `</ul>`;
            }
            html += `</div>`;
        });
        html += `</div>`;
    }

    // Assumptions
    if (bpData.assumptions && bpData.assumptions.length > 0) {
        html += `<div class="analysis-section">`;
        html += `<h3>Assunzioni</h3>`;
        html += `<ul>`;
        bpData.assumptions.forEach(ass => {
            html += `<li>${escape(ass)}</li>`;
        });
        html += `</ul>`;
        html += `</div>`;
    }

    // Dati Mancanti
    if (bpData.dati_mancanti && bpData.dati_mancanti.length > 0) {
        html += `<div class="analysis-section">`;
        html += `<h3>Dati Mancanti</h3>`;
        html += `<ul>`;
        bpData.dati_mancanti.forEach(dato => {
            html += `<li>${escape(dato)}</li>`;
        });
        html += `</ul>`;
        html += `</div>`;
    }

    // Disclaimer
    if (bpData.disclaimer) {
        html += `<div class="analysis-section">`;
        html += `<h3>Disclaimer</h3>`;
        html += `<div class="analysis-card"><p><em>${escape(bpData.disclaimer)}</em></p></div>`;
        html += `</div>`;
    }

    html += `</div>`; // Chiude analysis-output

    // Se non è stato generato nessun contenuto, mostra un messaggio
    if (html.trim() === '<div class="analysis-output"></div>') {
        console.warn('convertBusinessPlanJSONToHTML: Nessun contenuto generato!');
        html = '<div class="analysis-output"><p><strong>Attenzione:</strong> Il JSON ricevuto non contiene dati visualizzabili.</p>';
        html += '<p>Dati ricevuti: <pre>' + escape(JSON.stringify(bpData, null, 2).substring(0, 500)) + '</pre></p></div>';
    }
    
    console.log('convertBusinessPlanJSONToHTML completata. Lunghezza HTML finale:', html.length);
    return html;
}

// Funzione rimossa per motivi di sicurezza: le chiavi API non devono essere esposte nel frontend.
// Tutte le chiamate API vengono gestite dal backend che mantiene le credenziali in modo sicuro.

// Form data is now collected through wizard

// Funzione per generare HTML completo dal JSON (basata su generate.js)
// Versione browser-compatibile della funzione buildHtml da generate.js
function buildHtmlFromJSON(model) {
    const safeArray = (v) => Array.isArray(v) ? v : [];
    const escapeHtml = (str) => String(str ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    const formatEUR = (n) => {
        if (typeof n !== "number" || !isFinite(n)) return "—";
        return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
    };
    const chunkBy = (arr, size) => {
        const out = [];
        for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size));
        return out;
    };

    const meta = model.meta || {};
    const layout = model.pdf_layout || {};
    const narrativeChapters = safeArray(model?.narrative?.chapters);
    const charts = safeArray(model?.charts);

    // Funzione helper per verificare se un grafico ha dati validi
    function hasChartData(chart) {
        if (!chart || !chart.series || !Array.isArray(chart.series) || chart.series.length === 0) {
            console.log('❌ Grafico senza serie:', chart?.id);
            return false;
        }
        // Verifica che almeno una serie abbia punti con dati validi
        const hasData = chart.series.some(serie => {
            if (!serie.points || !Array.isArray(serie.points) || serie.points.length === 0) {
                return false;
            }
            // Verifica che ci sia almeno un punto con un valore y valido
            // Accetta numeri, stringhe numeriche, e 0 come valori validi
            return serie.points.some(point => {
                if (!point || point.y === null || point.y === undefined) {
                    return false;
                }
                // Converti in numero se è una stringa
                const y = typeof point.y === 'string' ? parseFloat(point.y) : point.y;
                // Accetta 0 come valore valido e verifica che non sia NaN
                return !isNaN(y) && y !== '';
            });
        });
        if (!hasData) {
            console.log('❌ Grafico senza dati validi:', chart?.id, 'Series:', chart.series.map(s => ({
                name: s.name,
                pointsCount: s.points?.length || 0,
                samplePoint: s.points?.[0]
            })));
        } else {
            console.log('✅ Grafico con dati validi:', chart?.id);
        }
        return hasData;
    }

    // Filtra i grafici che hanno dati validi
    console.log('📊 Totale grafici nel modello:', charts.length);
    const chartsWithData = charts.filter(hasChartData);
    console.log('📊 Grafici con dati validi:', chartsWithData.length, 'su', charts.length);
    const chartById = new Map(chartsWithData.map(c => [c.id, c]));
    const chaptersInOrder = safeArray(layout.chapter_order);

    const narrativeById = new Map(narrativeChapters.map(ch => [ch.id, ch]));
    const orderedChapterIds = [
        ...chaptersInOrder.filter(id => narrativeById.has(id)),
        ...narrativeChapters.map(ch => ch.id).filter(id => !chaptersInOrder.includes(id)),
    ];

    // TOC
    const tocItems = orderedChapterIds
        .map((id, idx) => {
            const ch = narrativeById.get(id);
            if (!ch) return "";
            return `<div class="toc-row">
                <div class="toc-left"><span class="toc-num">${idx + 1}.</span> <a href="#${escapeHtml(id)}">${escapeHtml(ch.titolo)}</a></div>
                <div class="toc-right"></div>
            </div>`;
        })
        .join("");

    const includeTOC = !!layout?.style_hints?.include_table_of_contents;
    const maxChartsPerPage = Number(layout?.style_hints?.max_charts_per_page || 2) || 2;

    // Executive summary
    const exec = model.executive_summary || {};
    const kpis = safeArray(exec.kpi_principali);
    const recs = safeArray(exec.raccomandazioni_30_60_90);

    const kpiTable = kpis.length
        ? `<table class="table">
            <thead><tr><th>KPI</th><th>Valore</th><th>Scenario</th></tr></thead>
            <tbody>
                ${kpis.map(k => {
                    const val = k.unita === "EUR" ? formatEUR(k.valore) : k.unita === "%" ? `${k.valore}%` : (k.valore ?? "—");
                    return `<tr>
                        <td>${escapeHtml(k.nome)}</td>
                        <td class="num">${escapeHtml(String(val))}</td>
                        <td>${escapeHtml(k.scenario)}</td>
                    </tr>`;
                }).join("")}
            </tbody>
        </table>`
        : `<div class="muted">Nessun KPI fornito.</div>`;

    const recTable = recs.length
        ? `<table class="table">
            <thead><tr><th>Orizzonte</th><th>Azione</th><th>Motivazione</th><th>Priorità</th></tr></thead>
            <tbody>
                ${recs.map(r => `<tr>
                    <td>${escapeHtml(String(r.orizzonte_giorni))} gg</td>
                    <td>${escapeHtml(r.azione)}</td>
                    <td>${escapeHtml(r.motivazione)}</td>
                    <td>${escapeHtml(r.priorita)}</td>
                </tr>`).join("")}
            </tbody>
        </table>`
        : `<div class="muted">Nessuna raccomandazione fornita.</div>`;

    // Capitoli + grafici
    const chaptersHtml = orderedChapterIds
        .map((id, idx) => {
            const ch = narrativeById.get(id);
            if (!ch) return "";

            // markdown → html (usa marked se disponibile, altrimenti conversione base)
            let bodyHtml = ch.contenuto_markdown || "";
            if (typeof marked !== 'undefined') {
                bodyHtml = marked.parse(bodyHtml);
            } else {
                // Fallback: conversione markdown base
                bodyHtml = markdownToHTML(bodyHtml);
            }

            // charts referenced by chapter - solo quelli con dati validi
            const allChartIds = safeArray(ch.chart_ids);
            console.log('📊 Chart IDs nel capitolo', ch.id, ':', allChartIds);
            const ids = allChartIds.filter(cid => {
                const chart = chartById.get(cid);
                if (!chart) {
                    console.log('⚠️ Grafico non trovato nella mappa:', cid);
                    return false;
                }
                const hasData = hasChartData(chart);
                if (!hasData) {
                    console.log('⚠️ Grafico escluso per mancanza di dati:', cid);
                }
                return hasData;
            });
            console.log('📊 Chart IDs validi per capitolo', ch.id, ':', ids.length, 'su', allChartIds.length);
            const chartBlocks = ids.length
                ? chunkBy(ids, maxChartsPerPage)
                    .map(group => {
                        const canvases = group
                            .map(cid => {
                                const c = chartById.get(cid);
                                return `<div class="chart-card">
                                    <div class="chart-title">${escapeHtml(c.titolo || cid)}</div>
                                    <canvas class="chart" id="chart_${escapeHtml(cid)}" width="900" height="420"></canvas>
                                    ${c.caption ? `<div class="chart-caption">${escapeHtml(c.caption)}</div>` : ""}
                                </div>`;
                            })
                            .join("");
                        return `<div class="charts-page page-break">${canvases}</div>`;
                    })
                    .join("")
                : "";

            return `
                <section class="chapter" id="${escapeHtml(id)}">
                    <div class="chapter-kicker">Capitolo ${idx + 1}</div>
                    <h1 class="chapter-title">${escapeHtml(ch.titolo)}</h1>
                    <div class="chapter-body">${bodyHtml}</div>
                    ${chartBlocks}
                </section>
            `;
        })
        .join("");

    // Executive Summary section
    const execHtml = `
        <section class="chapter" id="EXEC_SUMMARY">
            <div class="chapter-kicker">Sezione iniziale</div>
            <h1 class="chapter-title">Executive Summary</h1>
            <div class="chapter-body">
                <p>${escapeHtml(exec.sintesi || "")}</p>
                ${safeArray(exec.punti_chiave).length ? `
                    <h2>Punti chiave</h2>
                    <ul>
                        ${safeArray(exec.punti_chiave).map(x => `<li>${escapeHtml(x)}</li>`).join("")}
                    </ul>
                ` : ""}
                <h2>KPI principali</h2>
                ${kpiTable}
                <h2>Raccomandazioni 30/60/90</h2>
                ${recTable}
            </div>
        </section>
    `;

    const title = layout.titolo_documento || "Business Plan";
    const subtitle = layout.sottotitolo || "";
    const confidentiality = layout.confidenzialita || "uso_interno";

    // CSS styles (stessi di generate.js)
    const styles = `
        :root{
            --text:#111;
            --muted:#666;
            --border:#e6e6e6;
            --bg:#fff;
            --soft:#f7f7f8;
            --accent:#111;
        }
        *{ box-sizing:border-box; }
        body{
            margin:0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, Arial, sans-serif;
            color:var(--text);
            background:var(--bg);
            line-height:1.35;
        }
        .page{ padding: 42px 52px 56px; }
        .cover{
            padding: 70px 52px 56px;
            border-bottom: 1px solid var(--border);
        }
        .cover .badge{
            display:inline-block;
            padding:6px 10px;
            border:1px solid var(--border);
            border-radius:999px;
            font-size:12px;
            color:var(--muted);
            background:var(--soft);
            letter-spacing:.02em;
        }
        .cover h1{
            margin: 14px 0 8px;
            font-size: 30px;
            letter-spacing: -0.02em;
        }
        .cover h2{
            margin:0 0 18px;
            font-weight:500;
            color:var(--muted);
            font-size:16px;
        }
        .cover .meta{
            margin-top:24px;
            display:grid;
            grid-template-columns: 1fr 1fr;
            gap:10px 24px;
            font-size:12px;
            color:var(--muted);
        }
        .toc{
            padding: 42px 52px 0;
        }
        .toc h1{
            font-size: 18px;
            margin: 0 0 14px;
        }
        .toc-row{
            display:flex;
            align-items:baseline;
            justify-content:space-between;
            padding: 7px 0;
            border-bottom: 1px dashed var(--border);
            font-size: 13px;
        }
        .toc-left a{ color: var(--text); text-decoration:none; }
        .toc-num{ color:var(--muted); margin-right:6px; }
        .chapter{
            padding: 36px 52px 0;
        }
        .chapter-kicker{
            color: var(--muted);
            font-size: 12px;
            letter-spacing: .06em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        .chapter-title{
            margin: 0 0 14px;
            font-size: 22px;
            letter-spacing: -0.01em;
        }
        .chapter-body{
            font-size: 13.2px;
            color: var(--text);
        }
        .chapter-body h2{
            font-size: 15px;
            margin-top: 14px;
            margin-bottom: 8px;
            letter-spacing: -0.01em;
        }
        .chapter-body ul{
            margin: 8px 0 12px 18px;
        }
        .muted{ color: var(--muted); }
        .table{
            width:100%;
            border-collapse: collapse;
            font-size: 12.6px;
            margin: 8px 0 14px;
        }
        .table th, .table td{
            border:1px solid var(--border);
            padding: 8px 10px;
            vertical-align: top;
        }
        .table th{
            background: var(--soft);
            text-align:left;
            font-weight: 650;
        }
        .table .num{ text-align:right; white-space:nowrap; }
        .charts-page{
            display:grid;
            grid-template-columns: 1fr;
            gap: 12px;
            margin-top: 16px;
        }
        .chart-card{
            border: 1px solid var(--border);
            background: #fff;
            border-radius: 12px;
            padding: 12px 14px 10px;
        }
        .chart-title{
            font-size: 12.5px;
            font-weight: 650;
            margin-bottom: 8px;
        }
        .chart-caption{
            margin-top: 6px;
            font-size: 11.5px;
            color: var(--muted);
        }
        canvas.chart{
            width: 100% !important;
            height: 320px !important;
            display:block;
        }
        .page-break{
            break-before: page;
            page-break-before: always;
        }
        pre{
            background: var(--soft);
            border: 1px solid var(--border);
            padding: 10px 12px;
            border-radius: 10px;
            overflow:auto;
            font-size: 12px;
        }
        code{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
    `;

    const html = `<!doctype html>
<html lang="${escapeHtml(meta.lingua || "it-IT")}">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>${escapeHtml(title)}</title>
    ${chartsWithData.length > 0 ? '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>' : ''}
    <style>${styles}</style>
</head>
<body>
    <div class="cover">
        <div class="badge">${escapeHtml(confidentiality)}</div>
        <h1>${escapeHtml(title)}</h1>
        <h2>${escapeHtml(subtitle)}</h2>
        <div class="meta">
            <div><strong>Lingua</strong>: ${escapeHtml(meta.lingua || "it-IT")}</div>
            <div><strong>Stile</strong>: ${escapeHtml(meta.stile || "formale")}</div>
            <div><strong>Orizzonte</strong>: ${escapeHtml(String(meta.orizzonte_mesi ?? ""))} mesi</div>
            <div><strong>Data generazione</strong>: ${escapeHtml(meta.data_generazione || "")}</div>
            <div><strong>Versione</strong>: ${escapeHtml(meta.versione || "1.0")}</div>
        </div>
    </div>
    ${includeTOC ? `
        <div class="toc page-break">
            <h1>Indice</h1>
            <div class="toc-row">
                <div class="toc-left"><span class="toc-num">0.</span> <a href="#EXEC_SUMMARY">Executive Summary</a></div>
                <div class="toc-right"></div>
            </div>
            ${tocItems}
        </div>
    ` : ""}
    ${execHtml}
    ${chaptersHtml}
    ${chartsWithData.length > 0 ? `
    <script>
        (function(){
            // Aspetta che Chart.js sia caricato
            function waitForChart(callback, maxAttempts) {
                let attempts = 0;
                const checkChart = setInterval(() => {
                    attempts++;
                    if (typeof Chart !== 'undefined') {
                        clearInterval(checkChart);
                        callback();
                    } else if (attempts >= maxAttempts) {
                        clearInterval(checkChart);
                        console.warn('Chart.js non disponibile dopo ' + maxAttempts + ' tentativi');
                    }
                }, 100);
            }
            
            waitForChart(() => {
                const charts = ${JSON.stringify(chartsWithData)};
                function toXY(points){
                    return points.map(p => ({ x: p.x, y: p.y }));
                }
                function buildDataset(series, type){
                    return series.map((s, idx) => {
                        const data = toXY(s.points || []);
                        return {
                            label: (s.name || ("Serie " + (idx+1))).trim(),
                            data,
                            parsing: { xAxisKey: "x", yAxisKey: "y" },
                            tension: type === "line" ? 0.25 : 0,
                        };
                    });
                }
                function makeChart(cfg){
                    const canvas = document.getElementById("chart_" + cfg.id);
                    if(!canvas) {
                        console.warn('Canvas non trovato per grafico:', cfg.id);
                        return;
                    }
                    // Verifica che il grafico abbia dati validi prima di renderizzarlo
                    if(!cfg.series || !Array.isArray(cfg.series) || cfg.series.length === 0) {
                        console.warn('Grafico senza serie dati:', cfg.id);
                        canvas.parentElement?.remove(); // Rimuovi il canvas se non ha dati
                        return;
                    }
                    const hasValidData = cfg.series.some(serie => {
                        if (!serie.points || !Array.isArray(serie.points) || serie.points.length === 0) {
                            return false;
                        }
                        // Verifica che ci sia almeno un punto con un valore y valido
                        // Accetta numeri, stringhe numeriche, e 0 come valori validi
                        return serie.points.some(p => {
                            if (!p || p.y === null || p.y === undefined) {
                                return false;
                            }
                            // Converti in numero se è una stringa
                            const y = typeof p.y === 'string' ? parseFloat(p.y) : p.y;
                            // Accetta 0 come valore valido e verifica che non sia NaN
                            return !isNaN(y) && y !== '';
                        });
                    });
                    if(!hasValidData) {
                        console.warn('Grafico senza dati validi nel rendering:', cfg.id, 'Series:', cfg.series.map(s => ({
                            name: s.name,
                            pointsCount: s.points?.length || 0,
                            samplePoint: s.points?.[0]
                        })));
                        canvas.parentElement?.remove(); // Rimuovi il canvas se non ha dati validi
                        return;
                    }
                    console.log('✅ Rendering grafico:', cfg.id);
                    const ctx = canvas.getContext("2d");
                    const type = (cfg.tipo || "line").toLowerCase();
                    let chartType = type;
                    if(type === "pie") chartType = "pie";
                    const datasets = buildDataset(cfg.series || [], type);
                    const commonOptions = {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: true, position: "bottom", labels: { boxWidth: 10 } },
                            title: { display: false },
                            tooltip: { enabled: true }
                        },
                        animation: false
                    };
                    if(chartType === "pie"){
                        const pieData = (cfg.series?.[0]?.points || []).map(p => p.y);
                        const pieLabels = (cfg.series?.[0]?.points || []).map(p => p.x);
                        new Chart(ctx, {
                            type: "pie",
                            data: {
                                labels: pieLabels,
                                datasets: [{ label: cfg.titolo || cfg.id, data: pieData }]
                            },
                            options: commonOptions
                        });
                        return;
                    }
                    new Chart(ctx, {
                        type: chartType,
                        data: { datasets },
                        options: {
                            ...commonOptions,
                            scales: {
                                x: {
                                    type: "category",
                                    title: { display: !!cfg.x_label, text: cfg.x_label || "" },
                                    grid: { display: false }
                                },
                                y: {
                                    title: { display: !!cfg.y_label, text: cfg.y_label || "" },
                                    ticks: { callback: (v) => {
                                        if (typeof v === "number") return new Intl.NumberFormat("it-IT").format(v);
                                        return v;
                                    }}
                                }
                            }
                        }
                    });
                }
                charts.forEach(makeChart);
                window.__CHARTS_RENDERED__ = true;
                console.log('✅ Grafici renderizzati:', charts.length);
                // Rimuovi eventuali chart-card vuote rimaste dopo la rimozione dei canvas
                document.querySelectorAll('.chart-card').forEach(card => {
                    if (!card.querySelector('canvas')) {
                        card.remove();
                    }
                });
            }, 50);
        })();
    </script>
    ` : ''}
</body>
</html>`;

    return html;
}

// Funzione per generare PDF standalone usando window.print() (qualità professionale)
// Funzione rimossa: la generazione PDF viene ora gestita completamente dal backend
// Usa generatePDF() che chiama /api/generate-pdf
async function generatePDFStandaloneFromJSON(jsonData) {
    // Redirect alla funzione che usa il backend
    console.log('📄 Generazione PDF tramite backend...');
    return await generatePDF();
}

async function generatePDFAnalysis(marketAnalysisJSON) {
    if (!downloadAnalysisPdfBtn) downloadAnalysisPdfBtn = document.getElementById('downloadAnalysisPdfBtn');
    if (!downloadAnalysisPdfBtn) {
        console.error('downloadAnalysisPdfBtn not found');
        return;
    }
    
    if (!marketAnalysisJSON) {
        alert('Nessuna analisi di mercato disponibile');
        return;
    }
    
    // Verifica se il pagamento è già stato completato (con chiave separata per analisi)
    const paymentKey = 'paymentVerified_analysis';
    const sessionKey = 'paymentSessionId_analysis';
    
    // Il pagamento è già stato verificato prima della generazione del documento
    if (!window[paymentKey] || !window[sessionKey]) {
        alert('Pagamento non verificato. Genera prima l\'analisi di mercato.');
        return;
    }
    
    downloadAnalysisPdfBtn.disabled = true;
    downloadAnalysisPdfBtn.textContent = 'Generazione PDF...';
    
    try {
        console.log('=== INIZIO GENERAZIONE PDF ANALISI DI MERCATO ===');
        console.log('Chiamata API backend Python...');
        
        // Aggiungi il sessionId al JSON per la verifica
        const jsonWithPayment = {
            ...marketAnalysisJSON,
            _payment_session_id: window[sessionKey]
        };
        
        const response = await fetch(`${API_BASE_URL}/api/generate-pdf-analysis`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                marketAnalysisJson: jsonWithPayment
            })
        });
        
        if (!response.ok) {
            if (response.status === 402) {
                // Pagamento non completato, richiedi di nuovo
                window[paymentKey] = false;
                window[sessionKey] = null;
                alert('Pagamento non completato. Completa il pagamento per scaricare il PDF.');
                await handlePayment('market-analysis');
                return;
            }
            const errorData = await response.json().catch(() => ({ detail: 'Errore sconosciuto' }));
            throw new Error(`Errore API: ${response.status} - ${errorData.detail || 'Errore sconosciuto'}`);
        }
        
        // Scarica il PDF
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'analisi-mercato.pdf';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        console.log('✅ PDF analisi di mercato generato e scaricato con successo');
        
        // Reset pagamento dopo il download
        window[paymentKey] = false;
        window[sessionKey] = null;
        
        downloadAnalysisPdfBtn.disabled = false;
        downloadAnalysisPdfBtn.textContent = 'Scarica PDF';
    } catch (error) {
        console.error('Errore nella generazione PDF analisi:', error);
        alert('Errore nella generazione del PDF: ' + error.message);
        downloadAnalysisPdfBtn.disabled = false;
        downloadAnalysisPdfBtn.textContent = 'Scarica PDF';
    }
}

// PDF Generation using window.print() (qualità professionale - come lo script da console)

// Funzione per mostrare l'offerta upsell
async function showUpsellOffer(currentDocumentType, currentJsonData) {
    return new Promise((resolve) => {
        const upsellModal = document.getElementById('upsellModal');
        const closeUpsellModal = document.getElementById('closeUpsellModal');
        const acceptUpsellBtn = document.getElementById('acceptUpsellBtn');
        const declineUpsellBtn = document.getElementById('declineUpsellBtn');
        
        if (!upsellModal) {
            console.warn('Modal upsell non trovato, procedo senza offerta');
            resolve(false);
            return;
        }
        
        // Determina l'offerta in base al tipo di documento corrente
        let otherServiceName, otherServiceType, originalPrice, discountedPrice, discountPercent, description;
        
        if (currentDocumentType === 'business-plan') {
            otherServiceName = 'Analisi di Mercato';
            otherServiceType = 'market-analysis';
            originalPrice = 14.99; // Prezzo originale analisi
            discountPercent = 30;
            discountedPrice = (originalPrice * (1 - discountPercent / 100)).toFixed(2);
            description = 'Ottieni un\'analisi completa del mercato con competitor, tendenze e opportunità';
        } else {
            otherServiceName = 'Business Plan Professionale';
            otherServiceType = 'business-plan';
            originalPrice = 19.99; // Prezzo originale business plan
            discountPercent = 30;
            discountedPrice = (originalPrice * (1 - discountPercent / 100)).toFixed(2);
            description = 'Ottieni un business plan completo con proiezioni finanziarie e strategia';
        }
        
        // Popola il modal con i dati dell'offerta
        const serviceNameEl = document.getElementById('upsellServiceName');
        const originalPriceEl = document.getElementById('upsellOriginalPrice');
        const discountedPriceEl = document.getElementById('upsellDiscountedPrice');
        const discountBadgeEl = document.getElementById('upsellDiscountBadge');
        const descriptionEl = document.getElementById('upsellDescription');
        
        if (serviceNameEl) serviceNameEl.textContent = otherServiceName;
        if (originalPriceEl) originalPriceEl.textContent = `${originalPrice.toFixed(2)}€`;
        if (discountedPriceEl) discountedPriceEl.textContent = `${discountedPrice}€`;
        if (discountBadgeEl) discountBadgeEl.textContent = `-${discountPercent}%`;
        if (descriptionEl) descriptionEl.textContent = description;
        
        // Mostra il modal
        upsellModal.style.display = 'block';
        
        // Gestisci chiusura
        if (closeUpsellModal) {
            closeUpsellModal.onclick = () => {
                upsellModal.style.display = 'none';
                resolve(false);
            };
        }
        
        upsellModal.onclick = (e) => {
            if (e.target === upsellModal) {
                upsellModal.style.display = 'none';
                resolve(false);
            }
        };
        
        // Gestisci accettazione
        if (acceptUpsellBtn) {
            acceptUpsellBtn.onclick = async () => {
                upsellModal.style.display = 'none';
                
                // Salva che l'utente ha accettato l'upsell
                window.upsellAccepted = true;
                window.upsellOtherServiceType = otherServiceType;
                window.upsellCurrentServiceType = currentDocumentType;
                window.upsellCurrentJsonData = currentJsonData;
                
                // Se l'utente ha accettato, genereremo anche l'altro servizio
                // ma prima procediamo con il pagamento combinato
                resolve(true);
            };
        }
        
        // Gestisci rifiuto
        if (declineUpsellBtn) {
            declineUpsellBtn.onclick = () => {
                upsellModal.style.display = 'none';
                window.upsellAccepted = false;
                resolve(false);
            };
        }
    });
}

// Funzione per gestire il pagamento Stripe
async function handlePayment(documentType) {
    return new Promise(async (resolve, reject) => {
        const paymentModal = document.getElementById('paymentModal');
        const closePaymentModal = document.getElementById('closePaymentModal');
        const paymentLoading = document.getElementById('paymentLoading');
        const paymentError = document.getElementById('paymentError');
        
        if (!paymentModal) {
            reject(new Error('Modal di pagamento non trovato'));
            return;
        }
        
        // Mostra il modal
        paymentModal.style.display = 'block';
        paymentLoading.style.display = 'block';
        paymentError.style.display = 'none';
        
        // Chiudi il modal quando si clicca sulla X
        if (closePaymentModal) {
            closePaymentModal.onclick = () => {
                paymentModal.style.display = 'none';
                reject(new Error('Pagamento annullato'));
            };
        }
        
        // Chiudi quando si clicca fuori dal modal
        paymentModal.onclick = (e) => {
            if (e.target === paymentModal) {
                paymentModal.style.display = 'none';
                reject(new Error('Pagamento annullato'));
            }
        };
        
        try {
            // Crea la sessione di checkout
            const successUrl = window.location.href.split('?')[0] + '?payment=success';
            const cancelUrl = window.location.href.split('?')[0] + '?payment=cancel';
            
            // Verifica se l'utente ha accettato l'upsell
            const includeUpsell = window.upsellAccepted === true && 
                                 window.upsellOtherServiceType && 
                                 window.upsellOtherServiceType !== documentType;
            
            const response = await fetch(`${API_BASE_URL}/api/create-checkout-session`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    documentType: documentType,
                    successUrl: successUrl,
                    cancelUrl: cancelUrl,
                    includeUpsell: includeUpsell
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Errore sconosciuto' }));
                throw new Error(errorData.detail || 'Errore nella creazione della sessione di pagamento');
            }
            
            const data = await response.json();
            
            if (!data.success || !data.url) {
                throw new Error('Risposta API non valida');
            }
            
            // Salva il sessionId per la verifica successiva in base al tipo di documento
            if (documentType === 'business-plan') {
                window.paymentSessionId = data.sessionId;
            } else if (documentType === 'market-analysis') {
                window.paymentSessionId_analysis = data.sessionId;
            }
            
            // Reindirizza a Stripe Checkout
            window.location.href = data.url;
            
        } catch (error) {
            console.error('Errore nella creazione checkout session:', error);
            paymentLoading.style.display = 'none';
            paymentError.style.display = 'block';
            paymentError.textContent = 'Errore: ' + error.message;
            reject(error);
        }
    });
}

// Verifica il pagamento dopo il redirect da Stripe
async function verifyPaymentAfterRedirect(documentType) {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    const paymentStatus = urlParams.get('payment');
    
    console.log(`🔍 Verifica pagamento per ${documentType}:`, { sessionId, paymentStatus });
    
    if (paymentStatus === 'success' && sessionId) {
        try {
            console.log(`📡 Chiamata API verify-payment per ${documentType}...`);
            const response = await fetch(`${API_BASE_URL}/api/verify-payment`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    sessionId: sessionId,
                    documentType: documentType
                })
            });
            
            if (!response.ok) {
                console.error(`❌ Errore API verify-payment: ${response.status}`);
                return false;
            }
            
            const data = await response.json();
            console.log(`📥 Risposta verify-payment per ${documentType}:`, data);
            
            if (data.success && data.paid) {
                console.log(`✅ Pagamento ${documentType} verificato con successo`);
                // Salva il sessionId per usarlo nella generazione PDF
                if (documentType === 'business-plan') {
                    window.paymentSessionId = sessionId;
                    window.paymentVerified = true;
                } else if (documentType === 'market-analysis') {
                    window.paymentSessionId_analysis = sessionId;
                    window.paymentVerified_analysis = true;
                }
                
                // Se include upsell, salva anche le informazioni
                if (data.includeUpsell && data.upsellType) {
                    window.upsellPaid = true;
                    window.upsellType = data.upsellType;
                    window.upsellSessionId = sessionId;
                    
                    if (data.upsellType === 'business-plan') {
                        window.paymentSessionId = sessionId;
                        window.paymentVerified = true;
                    } else if (data.upsellType === 'market-analysis') {
                        window.paymentSessionId_analysis = sessionId;
                        window.paymentVerified_analysis = true;
                    }
                }
                
                // Rimuovi i parametri dalla URL solo se è l'ultima verifica
                setTimeout(() => {
                    const newParams = new URLSearchParams(window.location.search);
                    if (newParams.get('payment') === 'success') {
                        window.history.replaceState({}, document.title, window.location.pathname);
                    }
                }, 1000);
                
                return true;
            } else {
                return false;
            }
        } catch (error) {
            console.error('Errore nella verifica pagamento:', error);
            alert('Errore nella verifica del pagamento. Riprova.');
            return false;
        }
    }
    
    return false;
}

async function generatePDF() {
    if (!window.currentPlanData) {
        alert('Nessun business plan disponibile');
        return;
    }

    // Ensure button is initialized
    if (!downloadPdfBtn) downloadPdfBtn = document.getElementById('downloadPdfBtn');
    if (!downloadPdfBtn) {
        console.error('downloadPdfBtn not found');
        return;
    }

    // Verifica che ci sia JSON
    const hasJSON = window.currentPlanData.jsonData && typeof window.currentPlanData.jsonData === 'object';
    const jsonData = window.lastBusinessPlanJSON || window.currentPlanData.jsonData;
    
    if (!hasJSON && !jsonData) {
        alert('Nessun JSON disponibile per il PDF. Assicurati che il business plan sia stato generato correttamente.');
        return;
    }

    // Il pagamento è già stato verificato prima della generazione del documento
    if (!window.paymentVerified || !window.paymentSessionId) {
        alert('Pagamento non verificato. Genera prima il business plan.');
        return;
    }

    // Show loading
    downloadPdfBtn.disabled = true;
    downloadPdfBtn.textContent = 'Generazione PDF...';

    try {
        console.log('📄 Generazione PDF tramite API backend...');
        
        // Aggiungi il sessionId al JSON per la verifica
        const jsonWithPayment = {
            ...jsonData,
            _payment_session_id: window.paymentSessionId
        };
        
        const response = await fetch(`${API_BASE_URL}/api/generate-pdf`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                businessPlanJson: jsonWithPayment
            })
        });
        
        if (!response.ok) {
            if (response.status === 402) {
                // Pagamento non completato, richiedi di nuovo
                window.paymentVerified = false;
                window.paymentSessionId = null;
                alert('Pagamento non completato. Completa il pagamento per scaricare il PDF.');
                await handlePayment('business-plan');
                return;
            }
            const errorData = await response.json().catch(() => ({ detail: 'Errore sconosciuto' }));
            throw new Error(`Errore API: ${response.status} - ${errorData.detail || 'Errore sconosciuto'}`);
        }
        
        // Ottieni il blob del PDF
        const blob = await response.blob();
        
        // Crea un URL temporaneo e scarica il file
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'business-plan.pdf';
        document.body.appendChild(a);
        a.click();
        
        // Pulisci
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        console.log('✅ PDF scaricato con successo!');
        
        // Reset pagamento dopo il download
        window.paymentVerified = false;
        window.paymentSessionId = null;
        
        downloadPdfBtn.disabled = false;
        downloadPdfBtn.textContent = 'Scarica PDF';
        
    } catch (error) {
        console.error('Errore nella generazione PDF:', error);
        alert('Errore nella generazione del PDF: ' + error.message + '\n\nSe il backend su Render era in pausa, riprova tra 1-2 minuti.');
        downloadPdfBtn.disabled = false;
        downloadPdfBtn.textContent = 'Scarica PDF';
    }
}

// These are now handled in DOMContentLoaded

// Language Selector - initialized in initializeEventListeners

// Smooth Scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Animations on scroll removed - sections appear immediately


// ============================================
// MARKET ANALYSIS WIZARD
// ============================================

// Analysis type selection
let analysisType = null; // 'standard' or 'deep'

const analysisTypeQuestions = [
    {
        id: 'analysisType',
        title: 'Che tipo di analisi di mercato desideri?',
        description: 'Scegli tra un\'analisi standard o un\'analisi approfondita con dettagli estesi',
        type: 'choice',
        required: true,
        options: [
            {
                value: 'standard',
                label: 'Analisi Standard',
                description: 'Analisi rapida del mercato italiano con informazioni essenziali su competitor, tendenze e opportunità. Tempo stimato: 2-3 minuti.'
            },
            {
                value: 'deep',
                label: 'Analisi Approfondita',
                description: 'Analisi completa e dettagliata del mercato italiano con approfondimenti su dimensioni del mercato, analisi SWOT, competitor dettagliati, barriere all\'ingresso e strategie di posizionamento. Tempo stimato: 5-7 minuti.'
            }
        ]
    }
];

const analysisQuestionsStandard = [
    {
        id: 'industry',
        title: 'In quale settore vuoi analizzare il mercato italiano?',
        description: 'Seleziona il settore di interesse per il mercato italiano',
        type: 'select',
        required: true,
        options: [
            { value: '', label: 'Seleziona un settore' },
            { value: 'ristorazione', label: 'Ristorazione e Food & Beverage' },
            { value: 'tech', label: 'Tecnologia e Software' },
            { value: 'retail', label: 'Vendita al Dettaglio' },
            { value: 'ecommerce', label: 'E-commerce' },
            { value: 'servizi', label: 'Servizi Professionali' },
            { value: 'manufacturing', label: 'Produzione e Manifattura' },
            { value: 'healthcare', label: 'Sanità e Benessere' },
            { value: 'education', label: 'Educazione e Formazione' },
            { value: 'realestate', label: 'Immobiliare' },
            { value: 'finance', label: 'Finanza e Investimenti' },
            { value: 'altro', label: 'Altro' }
        ]
    },
    {
        id: 'geographicMarket',
        title: 'Quale area geografica italiana vuoi analizzare?',
        description: 'Indica la regione, provincia o area specifica del mercato italiano',
        type: 'text',
        required: true,
        placeholder: 'Es. Lombardia, Milano, Nord Italia, Italia intera'
    },
    {
        id: 'targetSegment',
        title: 'Quale segmento di mercato specifico?',
        description: 'Descrivi il segmento specifico che vuoi analizzare',
        type: 'textarea',
        required: true,
        rows: 4,
        placeholder: 'Es. PMI nel settore tecnologico, startup B2B, consumatori 25-45 anni...'
    },
    {
        id: 'competitors',
        title: 'Conosci alcuni competitor italiani principali?',
        description: 'Elenca i principali competitor italiani o lascia vuoto per un\'analisi generale del mercato',
        type: 'textarea',
        required: false,
        rows: 4,
        placeholder: 'Es. Azienda A, Azienda B, Azienda C...'
    },
    {
        id: 'marketTrends',
        title: 'Hai notato tendenze specifiche nel mercato italiano?',
        description: 'Descrivi eventuali tendenze, cambiamenti o fenomeni che hai osservato nel contesto italiano',
        type: 'textarea',
        required: false,
        rows: 4,
        placeholder: 'Es. Crescita del digitale, sostenibilità, remote work, Made in Italy...'
    }
];

const analysisQuestionsDeep = [
    {
        id: 'industry',
        title: 'In quale settore vuoi analizzare il mercato italiano?',
        description: 'Seleziona il settore di interesse per il mercato italiano',
        type: 'select',
        required: true,
        options: [
            { value: '', label: 'Seleziona un settore' },
            { value: 'ristorazione', label: 'Ristorazione e Food & Beverage' },
            { value: 'tech', label: 'Tecnologia e Software' },
            { value: 'retail', label: 'Vendita al Dettaglio' },
            { value: 'ecommerce', label: 'E-commerce' },
            { value: 'servizi', label: 'Servizi Professionali' },
            { value: 'manufacturing', label: 'Produzione e Manifattura' },
            { value: 'healthcare', label: 'Sanità e Benessere' },
            { value: 'education', label: 'Educazione e Formazione' },
            { value: 'realestate', label: 'Immobiliare' },
            { value: 'finance', label: 'Finanza e Investimenti' },
            { value: 'altro', label: 'Altro' }
        ]
    },
    {
        id: 'geographicMarket',
        title: 'Quale area geografica italiana vuoi analizzare?',
        description: 'Indica la regione, provincia o area specifica del mercato italiano',
        type: 'text',
        required: true,
        placeholder: 'Es. Lombardia, Milano, Nord Italia, Italia intera'
    },
    {
        id: 'targetSegment',
        title: 'Quale segmento di mercato specifico?',
        description: 'Descrivi il segmento specifico che vuoi analizzare nel contesto italiano',
        type: 'textarea',
        required: true,
        rows: 4,
        placeholder: 'Es. PMI nel settore tecnologico, startup B2B, consumatori 25-45 anni...'
    },
    {
        id: 'competitors',
        title: 'Conosci alcuni competitor italiani principali?',
        description: 'Elenca i principali competitor italiani con dettagli se disponibili',
        type: 'textarea',
        required: false,
        rows: 4,
        placeholder: 'Es. Azienda A (leader nel settore X), Azienda B (focus su Y)...'
    },
    {
        id: 'marketTrends',
        title: 'Hai notato tendenze specifiche nel mercato italiano?',
        description: 'Descrivi eventuali tendenze, cambiamenti o fenomeni che hai osservato nel contesto italiano',
        type: 'textarea',
        required: false,
        rows: 4,
        placeholder: 'Es. Crescita del digitale, sostenibilità, remote work, Made in Italy...'
    },
    {
        id: 'marketSize',
        title: 'Hai informazioni sulla dimensione del mercato?',
        description: 'Se disponibili, indica dati su dimensioni, crescita o previsioni del mercato italiano',
        type: 'textarea',
        required: false,
        rows: 4,
        placeholder: 'Es. Mercato da €X miliardi, crescita Y% annua, previsioni...'
    },
    {
        id: 'regulations',
        title: 'Ci sono normative o regolamentazioni specifiche?',
        description: 'Indica eventuali normative italiane, GDPR, o regolamentazioni che influenzano il settore',
        type: 'textarea',
        required: false,
        rows: 4,
        placeholder: 'Es. Normative GDPR, regolamenti settoriali, licenze necessarie...'
    },
    {
        id: 'barriers',
        title: 'Quali barriere all\'ingresso vedi nel mercato italiano?',
        description: 'Descrivi eventuali barriere come costi, competenze, licenze, ecc.',
        type: 'textarea',
        required: false,
        rows: 4,
        placeholder: 'Es. Costi elevati, competenze specialistiche, licenze, capitale iniziale...'
    }
];

let analysisCurrentStep = 0;
let analysisWizardData = {};
let currentAnalysisQuestions = [];

// Analysis modal elements - will be initialized when DOM is ready
let analysisModal;
let closeAnalysisModal;
let analysisWizardContainer;
let analysisWizardNavigation;
let analysisPrevBtn;
let analysisNextBtn;
let analysisProgressBar;
let analysisProgressSteps;
let analysisLoadingState;
let analysisResultState;
let analysisContent;
let downloadAnalysisPdfBtn;

function openAnalysisModal() {
    if (!analysisModal) {
        analysisModal = document.getElementById('analysisModal');
    }
    if (!analysisModal) {
        console.error('analysisModal not found');
        return;
    }
    analysisModal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    initAnalysisWizard();
}

function closeAnalysisModalFunc() {
    analysisModal.style.display = 'none';
    document.body.style.overflow = 'auto';
    resetAnalysisWizard();
}

function resetAnalysisWizard() {
    analysisCurrentStep = 0;
    analysisWizardData = {};
    analysisWizardContainer.innerHTML = '';
    analysisProgressSteps.innerHTML = '';
    analysisWizardNavigation.style.display = 'none';
    analysisLoadingState.style.display = 'none';
    analysisResultState.style.display = 'none';
}

function initAnalysisWizard() {
    resetAnalysisWizard();
    analysisType = null;
    currentAnalysisQuestions = analysisTypeQuestions;
    renderAnalysisProgressSteps();
    renderAnalysisCurrentStep();
    updateAnalysisNavigation();
}

function renderAnalysisProgressSteps() {
    analysisProgressSteps.innerHTML = '';
    currentAnalysisQuestions.forEach((q, index) => {
        const step = document.createElement('div');
        step.className = `progress-step ${index === analysisCurrentStep ? 'active' : ''} ${analysisWizardData[q.id] ? 'completed' : ''}`;
        step.textContent = index + 1;
        analysisProgressSteps.appendChild(step);
    });
    updateAnalysisProgressBar();
}

function updateAnalysisProgressBar() {
    const progress = currentAnalysisQuestions.length > 0 ? ((analysisCurrentStep + 1) / currentAnalysisQuestions.length) * 100 : 0;
    analysisProgressBar.style.width = `${progress}%`;
}

function renderAnalysisCurrentStep() {
    const question = currentAnalysisQuestions[analysisCurrentStep];
    if (!question) return;

    if (question.type === 'choice') {
        analysisWizardContainer.innerHTML = `
            <div class="wizard-step">
                <h2 class="wizard-question-title">${question.title}</h2>
                ${question.description ? `<p class="wizard-question-desc">${question.description}</p>` : ''}
                <div class="wizard-choice-container">
                    ${question.options.map(opt => `
                        <div class="wizard-choice-option ${analysisWizardData[question.id] === opt.value ? 'selected' : ''}" data-value="${opt.value}">
                            <h4>${opt.label}</h4>
                            <p>${opt.description}</p>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        // Add click handlers for choice options
        analysisWizardContainer.querySelectorAll('.wizard-choice-option').forEach(option => {
            option.addEventListener('click', () => {
                analysisWizardContainer.querySelectorAll('.wizard-choice-option').forEach(opt => opt.classList.remove('selected'));
                option.classList.add('selected');
                analysisWizardData[question.id] = option.dataset.value;
            });
        });
    } else {
        analysisWizardContainer.innerHTML = `
            <div class="wizard-step">
                <h2 class="wizard-question-title">${question.title}</h2>
                ${question.description ? `<p class="wizard-question-desc">${question.description}</p>` : ''}
                <div class="wizard-input-container">
                    ${renderInput(question)}
                </div>
            </div>
        `;

        const input = analysisWizardContainer.querySelector(`#wizard-${question.id}`);
        const suggestionsContainer = document.getElementById(`suggestions-${question.id}`);
        
        // Aggiungi gestione suggerimenti per campi text e textarea
        if (input && suggestionsContainer && (question.type === 'text' || question.type === 'textarea')) {
            let suggestionTimeout;
            let isLoadingSuggestions = false;
            let lastLoadedValue = '';
            let hasSuggestions = false;
            
            // Funzione per mostrare loading senza nascondere i suggerimenti esistenti
            const showLoading = () => {
                const existingBox = suggestionsContainer.querySelector('.suggestions-box');
                if (existingBox) {
                    // Aggiungi indicatore di aggiornamento senza nascondere i suggerimenti
                    const loadingIndicator = document.createElement('div');
                    loadingIndicator.className = 'suggestions-loading';
                    loadingIndicator.style.cssText = 'padding: 8px; text-align: center; font-size: 13px; color: #64748b; border-top: 1px solid #e2e8f0; margin-top: 12px;';
                    loadingIndicator.textContent = 'Aggiornamento suggerimenti...';
                    existingBox.appendChild(loadingIndicator);
                } else {
                    suggestionsContainer.innerHTML = '<div class="suggestions-loading">Caricamento suggerimenti...</div>';
                }
            };
            
            // Funzione per rimuovere l'indicatore di loading
            const hideLoading = () => {
                const loadingIndicator = suggestionsContainer.querySelector('.suggestions-loading');
                if (loadingIndicator && loadingIndicator.parentElement) {
                    loadingIndicator.remove();
                }
            };
            
            // Funzione per caricare e mostrare suggerimenti
            const loadSuggestions = async () => {
                if (isLoadingSuggestions) return;
                
                const currentValue = input.value.trim();
                
                // Evita ricaricamenti se il valore non è cambiato significativamente
                if (currentValue === lastLoadedValue && hasSuggestions) {
                    return;
                }
                
                const contextData = { ...analysisWizardData }; // Dati già compilati
                
                isLoadingSuggestions = true;
                showLoading();
                
                try {
                    const suggestions = await getSuggestions(
                        question.id,
                        question.title,
                        question.description || '',
                        currentValue,
                        'market-analysis',
                        contextData
                    );
                    
                    hideLoading();
                    
                    if (suggestions && suggestions.length > 0) {
                        displaySuggestions(suggestions, suggestionsContainer, input);
                        lastLoadedValue = currentValue;
                        hasSuggestions = true;
                    } else {
                        // Nascondi solo se non ci sono suggerimenti e non c'erano prima
                        if (!hasSuggestions) {
                            suggestionsContainer.innerHTML = '';
                        }
                        hasSuggestions = false;
                    }
                } catch (error) {
                    console.error('Errore caricamento suggerimenti:', error);
                    hideLoading();
                    // Non nascondere i suggerimenti esistenti in caso di errore
                    if (!hasSuggestions) {
                        suggestionsContainer.innerHTML = '';
                    }
                } finally {
                    isLoadingSuggestions = false;
                }
            };
            
            // Carica suggerimenti al focus (solo se non ci sono già)
            input.addEventListener('focus', () => {
                if (!hasSuggestions) {
                    clearTimeout(suggestionTimeout);
                    suggestionTimeout = setTimeout(loadSuggestions, 500);
                }
            });
            
            // Carica suggerimenti dopo che l'utente smette di digitare (debounce più lungo)
            input.addEventListener('input', () => {
                clearTimeout(suggestionTimeout);
                // Aumenta il debounce a 2 secondi per evitare ricaricamenti troppo frequenti
                suggestionTimeout = setTimeout(loadSuggestions, 2000);
            });
            
            // Carica suggerimenti iniziali dopo un breve delay
            setTimeout(loadSuggestions, 800);
        }

        if (input) {
            setTimeout(() => input.focus(), 100);
            if (analysisWizardData[question.id]) {
                input.value = analysisWizardData[question.id];
            }
        }
    }
}

function updateAnalysisNavigation() {
    analysisWizardNavigation.style.display = 'flex';
    analysisPrevBtn.style.display = analysisCurrentStep > 0 ? 'block' : 'none';
    
    if (analysisCurrentStep === currentAnalysisQuestions.length - 1) {
        analysisNextBtn.textContent = 'Analizza Mercato';
        analysisNextBtn.classList.add('btn-large');
    } else {
        analysisNextBtn.textContent = 'Avanti';
        analysisNextBtn.classList.remove('btn-large');
    }
}

function validateAnalysisCurrentStep() {
    const question = currentAnalysisQuestions[analysisCurrentStep];
    if (!question) return true;

    if (question.type === 'choice') {
        if (question.required && !analysisWizardData[question.id]) {
            return false;
        }
        return true;
    }

    const input = document.getElementById(`wizard-${question.id}`);
    if (!input) return true;

    if (question.required && !input.value.trim()) {
        input.classList.add('error');
        input.focus();
        return false;
    }

    input.classList.remove('error');
    return true;
}

function saveAnalysisCurrentStep() {
    const question = currentAnalysisQuestions[analysisCurrentStep];
    if (!question) return;

    if (question.type === 'choice') {
        // Already saved in click handler
        return;
    }

    const input = document.getElementById(`wizard-${question.id}`);
    if (input) {
        analysisWizardData[question.id] = input.value.trim();
    }
}

function analysisNextStep() {
    if (!validateAnalysisCurrentStep()) {
        if (currentAnalysisQuestions[analysisCurrentStep].type === 'choice' && !analysisWizardData[currentAnalysisQuestions[analysisCurrentStep].id]) {
            alert('Seleziona un\'opzione per continuare');
        }
        return;
    }

    saveAnalysisCurrentStep();

    // Check if we need to switch to actual questions after type selection
    if (currentAnalysisQuestions === analysisTypeQuestions && analysisWizardData.analysisType) {
        analysisType = analysisWizardData.analysisType;
        if (analysisType === 'standard') {
            currentAnalysisQuestions = analysisQuestionsStandard;
        } else {
            currentAnalysisQuestions = analysisQuestionsDeep;
        }
        analysisCurrentStep = 0;
        analysisWizardData = { analysisType: analysisType }; // Keep only the type
        renderAnalysisProgressSteps();
        renderAnalysisCurrentStep();
        updateAnalysisNavigation();
        return;
    }

    if (analysisCurrentStep < currentAnalysisQuestions.length - 1) {
        analysisCurrentStep++;
        renderAnalysisCurrentStep();
        renderAnalysisProgressSteps();
        updateAnalysisNavigation();
    } else {
        generateMarketAnalysis();
    }
}

function analysisPrevStep() {
    if (analysisCurrentStep > 0) {
        saveAnalysisCurrentStep();
        analysisCurrentStep--;
        renderAnalysisCurrentStep();
        renderAnalysisProgressSteps();
        updateAnalysisNavigation();
    }
}

async function generateMarketAnalysis() {
    saveAnalysisCurrentStep();
    
    analysisWizardContainer.style.display = 'none';
    analysisWizardNavigation.style.display = 'none';
    
    // PRIMA: Richiedi il pagamento prima di generare il documento
    try {
        // Salva i dati del wizard in localStorage per recuperarli dopo il redirect
        try {
            const dataToSave = JSON.stringify(analysisWizardData);
            localStorage.setItem('pendingMarketAnalysisData', dataToSave);
            localStorage.setItem('pendingDocumentType', 'market-analysis');
            console.log('✅ Dati analisi salvati in localStorage');
            console.log('Dimensione dati salvati:', dataToSave.length, 'caratteri');
            
            // Verifica che siano stati salvati correttamente
            const verify = localStorage.getItem('pendingMarketAnalysisData');
            if (!verify) {
                throw new Error('Dati non salvati correttamente in localStorage');
            }
            console.log('✅ Verifica salvataggio: dati presenti in localStorage');
        } catch (e) {
            console.error('❌ ERRORE nel salvataggio localStorage:', e);
            console.warn('⚠️ Fallback: salva in memoria (i dati potrebbero andare persi dopo il redirect)');
            // Fallback: salva in memoria
            window.pendingMarketAnalysisData = analysisWizardData;
        }
        
        await handlePayment('market-analysis');
        // Se il pagamento è stato avviato, la funzione reindirizza a Stripe
        // Il codice qui sotto verrà eseguito solo se l'utente annulla
        return;
    } catch (error) {
        if (error.message !== 'Pagamento annullato') {
            alert('Errore nel pagamento: ' + error.message);
        }
        // Rimuovi i dati salvati se l'utente annulla
        try {
            localStorage.removeItem('pendingMarketAnalysisData');
            localStorage.removeItem('pendingDocumentType');
        } catch (e) {}
        // Ripristina il wizard se l'utente annulla
        analysisWizardContainer.style.display = 'block';
        analysisWizardNavigation.style.display = 'flex';
        return;
    }
}

// Funzione per generare l'analisi di mercato dopo il pagamento verificato
async function generateMarketAnalysisAfterPayment(analysisWizardData) {
    if (!analysisLoadingState) analysisLoadingState = document.getElementById('analysisLoadingState');
    if (!analysisContent) analysisContent = document.getElementById('analysisContent');
    if (!analysisResultState) analysisResultState = document.getElementById('analysisResultState');
    
    analysisLoadingState.style.display = 'block';

    try {
        const result = await generateAnalysisWithAI(analysisWizardData);
        
        // Gestisci sia il caso in cui viene restituito un oggetto {html, json} che una stringa
        let analysisHTML;
        let marketAnalysisJSON = null;
        
        if (typeof result === 'object' && result !== null && result.html) {
            analysisHTML = result.html;
            marketAnalysisJSON = result.json || null;
            console.log('Risultato in formato oggetto - HTML e JSON ricevuti');
        } else if (typeof result === 'string') {
            analysisHTML = result;
            marketAnalysisJSON = null;
            console.log('Risultato in formato stringa');
        } else {
            throw new Error('generateAnalysisWithAI ha restituito un formato non valido: ' + typeof result);
        }
        
        analysisContent.innerHTML = analysisHTML;
        analysisLoadingState.style.display = 'none';
        
        // Salva i dati
        window.currentAnalysisData = {
            ...analysisWizardData,
            content: analysisHTML
        };
        
        // Salva il JSON se disponibile
        if (marketAnalysisJSON) {
            window.lastMarketAnalysisJSON = marketAnalysisJSON;
            console.log('✅ JSON analisi salvato in window.lastMarketAnalysisJSON');
        }
        
        // Mostra offerta upsell prima del risultato
        showUpsellOffer('market-analysis', marketAnalysisJSON).then(accepted => {
            if (accepted) {
                // L'utente ha accettato l'upsell, genereremo anche il business plan
                console.log('✅ Upsell accettato, procederemo con entrambi i servizi');
            }
            // Mostra il risultato dopo l'upsell (accettato o rifiutato)
            if (analysisResultState) {
                analysisResultState.style.display = 'block';
            }
        });
    } catch (error) {
        console.error('Errore nell\'analisi:', error);
        alert('Si è verificato un errore durante l\'analisi. Riprova.');
        analysisWizardContainer.style.display = 'block';
        analysisWizardNavigation.style.display = 'flex';
        analysisLoadingState.style.display = 'none';
    }
}

async function generateAnalysisWithAI(data) {
    const isDeep = analysisType === 'deep';
    const analysisTypeStr = isDeep ? 'deep' : 'standard';
    
    console.log('=== INIZIO ANALISI DI MERCATO ===');
    console.log('Timestamp:', new Date().toISOString());
    console.log('FormData ricevuto:', data);
    console.log('Tipo analisi:', analysisTypeStr);
    console.log('API Base URL:', API_BASE_URL);
    
    try {
        console.log('Chiamata API backend Python per analisi di mercato...');
        console.log('URL:', `${API_BASE_URL}/api/generate-market-analysis`);
        console.log('⚠️ NOTA: L\'analisi di mercato approfondita può richiedere 5-7 minuti. Attendi...');
        console.log('⏱️ Timestamp inizio:', new Date().toISOString());
        
        // Crea un AbortController per timeout - 15 minuti per analisi approfondite
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 900000); // 15 minuti timeout
        const startTime = Date.now();
        
        let response;
        try {
            response = await fetch(`${API_BASE_URL}/api/generate-market-analysis`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    formData: data,
                    analysisType: analysisTypeStr
                }),
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            const fetchTime = ((Date.now() - startTime) / 1000).toFixed(2);
            console.log('✅ Fetch completata. Status:', response.status, response.statusText);
            console.log('⏱️ Tempo impiegato:', fetchTime, 'secondi');
        } catch (fetchError) {
            clearTimeout(timeoutId);
            console.error('❌ Errore nella chiamata fetch:', fetchError);
            
            let errorMessage = 'Errore sconosciuto nella chiamata API';
            if (fetchError.name === 'AbortError') {
                errorMessage = 'Timeout: la richiesta ha impiegato troppo tempo (oltre 15 minuti).';
            } else if (fetchError.name === 'TypeError') {
                if (fetchError.message.includes('Failed to fetch') || fetchError.message.includes('Load failed')) {
                    errorMessage = 'Errore di connessione: impossibile raggiungere il backend su Render. Verifica:\n' +
                        '- La connessione internet\n' +
                        '- Se il servizio era in pausa (cold start), riprova: la prima richiesta può richiedere 1-2 minuti\n' +
                        '- Eventuali problemi CORS';
                } else {
                    errorMessage = `Errore di tipo: ${fetchError.message}`;
                }
            } else {
                errorMessage = `Errore nella chiamata API: ${fetchError.message || 'Errore sconosciuto'}`;
            }
            
            throw new Error(errorMessage);
        }
        
        if (!response.ok) {
            let errorData;
            try {
                const text = await response.text();
                console.error('Risposta errore (raw):', text);
                errorData = JSON.parse(text);
            } catch (e) {
                errorData = { detail: `Errore HTTP ${response.status}: ${response.statusText}` };
            }
            console.error('Errore API - Status:', response.status);
            console.error('Dati errore:', errorData);
            const errorMessage = errorData.detail || errorData.message || errorData.error || 'Errore sconosciuto';
            throw new Error(`Errore API: ${response.status} - ${errorMessage}`);
        }
        
        const result = await response.json();
        console.log('✅ Risposta ricevuta dal backend');
        
        if (!result.success || !result.json) {
            throw new Error('Risposta API non valida - formato dati inatteso');
        }
        
        const marketAnalysisJSON = result.json;
        
        // LOG DETTAGLIATO DEL JSON PER DEBUG
        console.log('=== JSON ANALISI DI MERCATO RICEVUTO ===');
        console.log('Tipo dati ricevuti:', typeof marketAnalysisJSON);
        console.log('Chiavi disponibili:', Object.keys(marketAnalysisJSON || {}));
        console.log('--- JSON COMPLETO (formattato) ---');
        try {
            const jsonString = JSON.stringify(marketAnalysisJSON, null, 2);
            console.log(jsonString);
            console.log('--- FINE JSON ---');
        } catch (stringifyError) {
            console.error('Errore nella stringificazione JSON:', stringifyError);
            console.log('JSON raw:', marketAnalysisJSON);
        }
        console.log('=== FINE LOG JSON ===');
        
        // Salva il JSON in variabile globale e localStorage
        window.lastMarketAnalysisJSON = marketAnalysisJSON;
        console.log('✅ JSON salvato in window.lastMarketAnalysisJSON');
        
        try {
            localStorage.setItem('lastMarketAnalysisJSON', JSON.stringify(marketAnalysisJSON));
            console.log('✅ JSON salvato anche in localStorage');
        } catch (storageError) {
            console.warn('⚠️ Impossibile salvare in localStorage:', storageError);
        }
        
        // Converti il JSON in HTML per la visualizzazione
        console.log('Inizio conversione JSON -> HTML...');
        const analysisHTML = convertMarketAnalysisJSONToHTML(marketAnalysisJSON);
        console.log('Conversione completata. Lunghezza HTML:', analysisHTML.length);
        
        if (!analysisHTML || analysisHTML.trim() === '') {
            console.error('ERRORE: HTML generato è vuoto!');
            throw new Error('La conversione JSON->HTML ha prodotto un risultato vuoto');
        }
        
        console.log('=== generateAnalysisWithAI completata con successo ===');
        // Restituisci sia HTML che JSON
        return {
            html: analysisHTML,
            json: marketAnalysisJSON
        };
        
    } catch (error) {
        console.log('=== generateAnalysisWithAI terminata con errore ===');
        console.error('Errore nella chiamata API:', error);
        console.error('Stack trace:', error.stack);
        
        const errorMessage = error.message || 'Errore sconosciuto';
        console.warn(`Errore API: ${errorMessage}.`);
        
        // Mostra popup di errore
        if (errorMessage.includes('Errore di connessione') || errorMessage.includes('Failed to fetch')) {
            alert('❌ Errore di Connessione\n\n' + errorMessage + '\n\nSe il backend su Render era in pausa, riprova tra 1-2 minuti.');
        } else {
            alert('❌ Errore nell\'analisi di mercato\n\n' + errorMessage);
        }
        
        throw error; // Rilancia l'errore per gestirlo in generateMarketAnalysis
    }
}

// Converte il JSON dell'analisi di mercato in HTML per la visualizzazione
function convertMarketAnalysisJSONToHTML(analysisData) {
    let html = '<div class="analysis-output">';
    
    // Helper per escape HTML
    const escape = (str) => String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    const formatCurrency = (num, unit) => {
        if (!num) return 'N/A';
        if (unit === 'EUR' || unit === 'USD') {
            return new Intl.NumberFormat('it-IT', { style: 'currency', currency: unit === 'EUR' ? 'EUR' : 'USD' }).format(num);
        }
        return num.toLocaleString('it-IT') + ' ' + (unit || '');
    };
    
    // Meta info
    const meta = analysisData.meta || {};
    html += `<div class="analysis-header">`;
    html += `<h1>Analisi di Mercato ${meta.tipo_analisi === 'deep' ? 'Approfondita' : ''}</h1>`;
    if (meta.settore) {
        html += `<h2>${escape(meta.settore)}</h2>`;
    }
    if (meta.area_geografica || meta.data_generazione) {
        html += `<div class="meta-info">`;
        if (meta.area_geografica) {
            html += `<span>Area Geografica: ${escape(meta.area_geografica)}</span>`;
        }
        if (meta.data_generazione) {
            html += `<span>Generato il: ${escape(meta.data_generazione)}</span>`;
        }
        html += `</div>`;
    }
    html += `</div>`;
    
    // Executive Summary
    if (analysisData.executive_summary) {
        const exec = analysisData.executive_summary;
        html += `<div class="analysis-section">`;
        html += `<h3>Executive Summary</h3>`;
        
        if (exec.sintesi) {
            html += `<div class="analysis-card">${markdownToHTML(exec.sintesi)}</div>`;
        }
        
        if (exec.punti_chiave && exec.punti_chiave.length > 0) {
            html += `<h4>Punti Chiave</h4>`;
            html += `<ul>`;
            exec.punti_chiave.forEach(punto => {
                html += `<li>${escape(punto)}</li>`;
            });
            html += `</ul>`;
        }
        
        if (exec.raccomandazioni && exec.raccomandazioni.length > 0) {
            html += `<h4>Raccomandazioni Principali</h4>`;
            html += `<ol>`;
            exec.raccomandazioni.forEach(rec => {
                html += `<li>${escape(rec)}</li>`;
            });
            html += `</ol>`;
        }
        html += `</div>`;
    }
    
    // Market Size
    if (analysisData.market_size) {
        const ms = analysisData.market_size;
        html += `<div class="analysis-section">`;
        html += `<h3>Dimensioni del Mercato</h3>`;
        
        if (ms.tam) {
            html += `<div class="analysis-info-box">`;
            html += `<h4>TAM (Total Addressable Market)</h4>`;
            html += `<p><strong>Valore:</strong> ${formatCurrency(ms.tam.valore, ms.tam.unita)}</p>`;
            if (ms.tam.fonte) html += `<p><strong>Fonte:</strong> ${escape(ms.tam.fonte)} (${escape(ms.tam.anno || 'N/A')})</p>`;
            if (ms.tam.descrizione) html += `<div>${markdownToHTML(ms.tam.descrizione)}</div>`;
            html += `</div>`;
        }
        
        if (ms.sam) {
            html += `<div class="analysis-info-box">`;
            html += `<h4>SAM (Serviceable Addressable Market)</h4>`;
            html += `<p><strong>Valore:</strong> ${formatCurrency(ms.sam.valore, ms.sam.unita)}</p>`;
            if (ms.sam.fonte) html += `<p><strong>Fonte:</strong> ${escape(ms.sam.fonte)} (${escape(ms.sam.anno || 'N/A')})</p>`;
            if (ms.sam.descrizione) html += `<div>${markdownToHTML(ms.sam.descrizione)}</div>`;
            html += `</div>`;
        }
        
        if (ms.som) {
            html += `<div class="analysis-info-box">`;
            html += `<h4>SOM (Serviceable Obtainable Market)</h4>`;
            html += `<p><strong>Valore:</strong> ${formatCurrency(ms.som.valore, ms.som.unita)}</p>`;
            if (ms.som.fonte) html += `<p><strong>Fonte:</strong> ${escape(ms.som.fonte)} (${escape(ms.som.anno || 'N/A')})</p>`;
            if (ms.som.descrizione) html += `<div>${markdownToHTML(ms.som.descrizione)}</div>`;
            html += `</div>`;
        }
        
        if (ms.trend_crescita) {
            html += `<div class="analysis-card">`;
            html += `<h4>Trend di Crescita</h4>`;
            html += `<p><strong>Tasso di crescita annuale:</strong> ${ms.trend_crescita.tasso_crescita_annuale}%</p>`;
            html += `<p><strong>Periodo:</strong> ${escape(ms.trend_crescita.periodo || 'N/A')}</p>`;
            if (ms.trend_crescita.fonte) html += `<p><strong>Fonte:</strong> ${escape(ms.trend_crescita.fonte)}</p>`;
            if (ms.trend_crescita.descrizione) html += `<div>${markdownToHTML(ms.trend_crescita.descrizione)}</div>`;
            html += `</div>`;
        }
        html += `</div>`;
    }
    
    // Competitor Analysis
    if (analysisData.competitor_analysis) {
        const comp = analysisData.competitor_analysis;
        html += `<div class="analysis-section">`;
        html += `<h3>Analisi Competitor</h3>`;
        
        if (comp.competitor_principali && comp.competitor_principali.length > 0) {
            comp.competitor_principali.forEach((competitor) => {
                html += `<div class="competitor-card ${competitor.tipo}">`;
                html += `<h4>${escape(competitor.nome)} <span class="competitor-type">(${competitor.tipo === 'diretto' ? 'Competitor Diretto' : 'Competitor Indiretto'})</span></h4>`;
                if (competitor.fatturato_stimato) html += `<p><strong>Fatturato stimato:</strong> ${escape(competitor.fatturato_stimato)}</p>`;
                if (competitor.quote_mercato) html += `<p><strong>Quota di mercato:</strong> ${escape(competitor.quote_mercato)}</p>`;
                if (competitor.posizionamento) html += `<p><strong>Posizionamento:</strong> ${escape(competitor.posizionamento)}</p>`;
                
                if (competitor.punti_forza && competitor.punti_forza.length > 0) {
                    html += `<p><strong>Punti di Forza:</strong></p><ul>`;
                    competitor.punti_forza.forEach(pf => html += `<li>${escape(pf)}</li>`);
                    html += `</ul>`;
                }
                
                if (competitor.punti_debolezza && competitor.punti_debolezza.length > 0) {
                    html += `<p><strong>Punti di Debolezza:</strong></p><ul>`;
                    competitor.punti_debolezza.forEach(pd => html += `<li>${escape(pd)}</li>`);
                    html += `</ul>`;
                }
                html += `</div>`;
            });
        }
        html += `</div>`;
    }
    
    // Trends & Opportunities
    if (analysisData.trends_opportunities) {
        const to = analysisData.trends_opportunities;
        html += `<div class="analysis-section">`;
        html += `<h3>Trend e Opportunità</h3>`;
        
        if (to.trend_emergenti && to.trend_emergenti.length > 0) {
            html += `<h4>Trend Emergenti</h4>`;
            to.trend_emergenti.forEach(trend => {
                html += `<div class="trend-card">`;
                html += `<h5>${escape(trend.titolo)} <span class="trend-impact ${trend.impatto}">Impatto: ${trend.impatto}</span></h5>`;
                html += `<div>${markdownToHTML(trend.descrizione)}</div>`;
                if (trend.fonte) html += `<p class="trend-source">Fonte: ${escape(trend.fonte)}</p>`;
                html += `</div>`;
            });
        }
        
        if (to.opportunita && to.opportunita.length > 0) {
            html += `<h4>Opportunità di Mercato</h4>`;
            html += `<ul>`;
            to.opportunita.forEach(opp => {
                html += `<li><strong>${escape(opp.titolo)}</strong> (Potenziale: ${opp.potenziale})<br/>${markdownToHTML(opp.descrizione)}</li>`;
            });
            html += `</ul>`;
        }
        html += `</div>`;
    }
    
    // SWOT Analysis
    if (analysisData.swot_analysis) {
        const swot = analysisData.swot_analysis;
        html += `<div class="analysis-section">`;
        html += `<h3>Analisi SWOT</h3>`;
        html += `<div class="swot-grid">`;
        
        // Strengths
        html += `<div class="swot-box strengths">`;
        html += `<h4>Punti di Forza</h4><ul>`;
        if (swot.strengths) {
            swot.strengths.forEach(s => {
                html += `<li><strong>${escape(s.titolo)}</strong><br/>${markdownToHTML(s.descrizione)}</li>`;
            });
        }
        html += `</ul></div>`;
        
        // Weaknesses
        html += `<div class="swot-box weaknesses">`;
        html += `<h4>Debolezze</h4><ul>`;
        if (swot.weaknesses) {
            swot.weaknesses.forEach(w => {
                html += `<li><strong>${escape(w.titolo)}</strong> (Impatto: ${w.impatto})<br/>${markdownToHTML(w.descrizione)}</li>`;
            });
        }
        html += `</ul></div>`;
        
        // Opportunities
        html += `<div class="swot-box opportunities">`;
        html += `<h4>Opportunità</h4><ul>`;
        if (swot.opportunities) {
            swot.opportunities.forEach(o => {
                html += `<li><strong>${escape(o.titolo)}</strong> (Potenziale: ${o.potenziale})<br/>${markdownToHTML(o.descrizione)}</li>`;
            });
        }
        html += `</ul></div>`;
        
        // Threats
        html += `<div class="swot-box threats">`;
        html += `<h4>Minacce</h4><ul>`;
        if (swot.threats) {
            swot.threats.forEach(t => {
                html += `<li><strong>${escape(t.titolo)}</strong> (Probabilità: ${t.probabilita}, Impatto: ${t.impatto})<br/>${markdownToHTML(t.descrizione)}</li>`;
            });
        }
        html += `</ul></div>`;
        
        html += `</div>`;
        html += `</div>`;
    }
    
    // Positioning Strategy
    if (analysisData.positioning_strategy) {
        const pos = analysisData.positioning_strategy;
        html += `<div class="analysis-section">`;
        html += `<h3>Strategia di Posizionamento</h3>`;
        
        if (pos.posizionamento_raccomandato) {
            html += `<div class="analysis-card">`;
            html += `<h4>Posizionamento Raccomandato</h4>`;
            html += `<div>${markdownToHTML(pos.posizionamento_raccomandato)}</div>`;
            html += `</div>`;
        }
        
        if (pos.nicchie_mercato && pos.nicchie_mercato.length > 0) {
            html += `<h4>Nicchie di Mercato</h4>`;
            html += `<ul>`;
            pos.nicchie_mercato.forEach(nicchia => {
                html += `<li><strong>${escape(nicchia.nicchia)}</strong> (Potenziale: ${nicchia.potenziale})<br/>${markdownToHTML(nicchia.descrizione)}</li>`;
            });
            html += `</ul>`;
        }
        html += `</div>`;
    }
    
    // Sources
    if (analysisData.sources && analysisData.sources.length > 0) {
        html += `<div class="analysis-section">`;
        html += `<h3>Fonti</h3>`;
        html += `<ul class="sources-list">`;
        analysisData.sources.forEach(source => {
            html += `<li><strong>${escape(source.titolo)}</strong> (${source.tipo})`;
            if (source.url) html += ` - <a href="${escape(source.url)}" target="_blank" rel="noopener noreferrer">${escape(source.url)}</a>`;
            if (source.data_accesso) html += ` - Accesso: ${escape(source.data_accesso)}`;
            if (source.descrizione) html += `<br/><span style="color: var(--text-tertiary); font-size: 0.9rem;">${escape(source.descrizione)}</span>`;
            html += `</li>`;
        });
        html += `</ul>`;
        html += `</div>`;
    }
    
    // Charts (se presenti)
    if (analysisData.charts && analysisData.charts.length > 0) {
        html += `<div class="analysis-section">`;
        html += `<h3>Grafici</h3>`;
        html += `<div class="charts-container" id="analysis-charts-container"></div>`;
        // I grafici verranno renderizzati con Chart.js dopo il caricamento
        window.analysisChartsData = analysisData.charts;
        html += `</div>`;
    }
    
    html += '</div>'; // Close analysis-output
    return html;
}

// Initialize analysis modal elements and event listeners
function initializeAnalysisListeners() {
    analysisModal = document.getElementById('analysisModal');
    closeAnalysisModal = document.getElementById('closeAnalysisModal');
    analysisWizardContainer = document.getElementById('analysisWizardContainer');
    analysisWizardNavigation = document.getElementById('analysisWizardNavigation');
    analysisPrevBtn = document.getElementById('analysisPrevBtn');
    analysisNextBtn = document.getElementById('analysisNextBtn');
    analysisProgressBar = document.getElementById('analysisProgressBar');
    analysisProgressSteps = document.getElementById('analysisProgressSteps');
    analysisLoadingState = document.getElementById('analysisLoadingState');
    analysisResultState = document.getElementById('analysisResultState');
    analysisContent = document.getElementById('analysisContent');
    downloadAnalysisPdfBtn = document.getElementById('downloadAnalysisPdfBtn');

    if (closeAnalysisModal) closeAnalysisModal.addEventListener('click', closeAnalysisModalFunc);
    if (analysisNextBtn) analysisNextBtn.addEventListener('click', analysisNextStep);
    if (analysisPrevBtn) analysisPrevBtn.addEventListener('click', analysisPrevStep);
    if (downloadAnalysisPdfBtn) downloadAnalysisPdfBtn.addEventListener('click', async () => {
        if (window.lastMarketAnalysisJSON) {
            await generatePDFAnalysis(window.lastMarketAnalysisJSON);
        } else if (window.currentAnalysisData) {
            // Fallback al metodo vecchio se non c'è JSON
            generatePDFFromContent(window.currentAnalysisData, 'analisi-mercato');
        } else {
            alert('Nessuna analisi di mercato disponibile. Genera prima un\'analisi.');
        }
    });
}

// Helper function for PDF generation from any content
function generatePDFFromContent(data, filename) {
    const pdfContent = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { 
            font-family: 'Inter', Arial, sans-serif; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 40px 20px; 
            line-height: 1.8;
            color: #1e293b;
        }
        h1 { 
            color: #000000; 
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            text-align: center;
        }
        h2 {
            color: #6b7280;
            font-size: 1.5rem;
            text-align: center;
            margin-bottom: 2rem;
            font-weight: 400;
        }
        h4 { 
            color: #000000; 
            margin-top: 30px; 
            margin-bottom: 15px;
            font-size: 1.3rem;
            font-weight: 600;
        }
        p { 
            line-height: 1.8; 
            margin-bottom: 15px;
            color: #475569;
        }
        ul, ol {
            margin-bottom: 20px;
            padding-left: 30px;
        }
        li {
            margin-bottom: 10px;
            line-height: 1.7;
        }
        strong {
            color: #1e293b;
            font-weight: 600;
        }
        .header {
            border-bottom: 3px solid #000000;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
    </style>
</head>
<body>
    ${data.content}
</body>
</html>
    `;

    if (typeof html2pdf !== 'undefined') {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = pdfContent;
        tempDiv.style.position = 'absolute';
        tempDiv.style.left = '-9999px';
        tempDiv.style.width = '800px';
        document.body.appendChild(tempDiv);

        const opt = {
            margin: [20, 20, 20, 20],
            filename: `${filename}.pdf`,
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2, useCORS: true },
            jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
        };

        html2pdf().set(opt).from(tempDiv).save().then(() => {
            document.body.removeChild(tempDiv);
        });
    } else {
        const blob = new Blob([pdfContent], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${filename}.html`;
        a.click();
        URL.revokeObjectURL(url);
    }
}

// Close modals when clicking outside - this is handled in initializeEventListeners
// Additional handlers for analysis modal
document.addEventListener('click', (e) => {
    if (analysisModal && e.target === analysisModal) closeAnalysisModalFunc();
});
