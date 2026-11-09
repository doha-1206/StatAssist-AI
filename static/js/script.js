
document.addEventListener('DOMContentLoaded', () => {

    // =====================================
    // DOM Elements
    // =====================================

    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');
    const uploadError = document.getElementById('upload-error');
    const errorMessage = document.getElementById('error-message');
    const uploadPanel = document.getElementById('upload-panel');
    const successPanel = document.getElementById('success-panel');
    const displayFileName = document.getElementById('display-file-name');
    const btnReset = document.getElementById('btn-reset');

    const tableHead = document.getElementById('cleaned-table-head');
    const tableBody = document.getElementById('cleaned-table-body');
    const rowCount = document.getElementById('cleaned-row-count');
    const columnCount = document.getElementById('cleaned-column-count');

    const researchSection = document.getElementById(
        'research-question-section'
    );

    const questionInput = document.getElementById('research-question');

    const nextQuestionButton = document.getElementById(
        'btn-next-question'
    );

    const dependencySection = document.getElementById(
        'dependency-question-section'
    );

    const interpretationSection = document.getElementById(
        'interpretation-section'
    );

    const interpretationLoading = document.getElementById(
        'interpretation-loading'
    );

    const interpretationContent = document.getElementById(
        'interpretation-content'
    );

    const interpretationError = document.getElementById(
        'interpretation-error'
    );

    const visualizationSection = document.getElementById(
        'visualization-section'
    );

    const visualizationLoading = document.getElementById(
        'visualization-loading'
    );

    const visualizationContent = document.getElementById(
        'visualization-content'
    );

    const visualizationError = document.getElementById(
        'visualization-error'
    );


    // =====================================
    // Save Interpretation Mode
    // =====================================


    const modeOptions = document.querySelectorAll(
        'input[name="interpretation-mode"]'
    );

    async function saveInterpretationMode(mode) {

        try {

            const response = await fetch('/set-mode', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    mode: mode
                })
            });

            const result = await response.json();

            if (!response.ok || !result.success) {
                console.error('Could not save mode:', result);
                return false;
            }

            console.log('Interpretation mode saved:', result.mode);

            return true;

        } catch (error) {

            console.error('Mode saving error:', error);

            return false;
        }
    }


        // Save mode whenever the user changes it

        modeOptions.forEach(option => {

        option.addEventListener('change', () => {
            saveInterpretationMode(option.value);
        });

        });


        // Synchronize the initially selected mode with Flask

        const initialMode = document.querySelector(
        'input[name="interpretation-mode"]:checked'
        );

        if (initialMode) {
        saveInterpretationMode(initialMode.value);
        }


    // =====================================
    // Detect Research Question Language
    // =====================================

    function detectLanguage(text) {

        const arabicPattern = /[\u0600-\u06FF]/;

        return arabicPattern.test(text) ? 'ar' : 'en';

    }


    // =====================================
    // Update Dependency Question Language
    // =====================================

    function updateDependencyLanguage(language) {

        const title = document.getElementById('dependency-title');

        const questionText = document.getElementById(
            'dependency-question-text'
        );

        const yesButton = document.getElementById('dependency-yes');

        const noButton = document.getElementById('dependency-no');


        if (!title || !questionText || !yesButton || !noButton) {

            throw new Error(
                'Dependency question elements were not found.'
            );

        }


        if (language === 'ar') {

            title.textContent = 'تأكيد نوع العلاقة';

            questionText.textContent =
                'هل البيانات في هذين المتغيرين مأخوذة من نفس الأشخاص؟';

            yesButton.textContent = 'نعم';
            noButton.textContent = 'لا';

            title.dir = 'rtl';
            questionText.dir = 'rtl';

        } else {

            title.textContent = 'Dependency Confirmation';

            questionText.textContent =
                'Are these two variables measured from the same participants?';

            yesButton.textContent = 'Yes';
            noButton.textContent = 'No';

            title.dir = 'ltr';
            questionText.dir = 'ltr';

        }

    }


    // =====================================
    // Progress Stepper
    // =====================================

    function setStepper(currentStep) {

        for (let number = 1; number <= 6; number++) {

            const step = document.getElementById(`step-${number}`);

            const stepNum = document.getElementById(
                `step-num-${number}`
            );

            const title = document.querySelector(
                `#step-${number} .step-title`
            );

            if (!step) continue;


            step.classList.remove('active', 'completed');
            step.removeAttribute('aria-current');


            if (number < currentStep) {

                step.classList.add('completed');

                if (stepNum) {
                    stepNum.innerHTML =
                        '<i class="bi bi-check-lg"></i>';
                }

            } else {

                if (stepNum) {
                    stepNum.textContent = number;
                }

            }


            if (number === currentStep) {

                step.classList.add('active');

                step.setAttribute('aria-current', 'step');

            }


            if (title) {

                title.classList.remove('text-muted', 'text-navy');

                if (number <= currentStep) {
                    title.classList.add('text-navy');
                } else {
                    title.classList.add('text-muted');
                }

            }

        }


        // Update connecting lines

        for (let number = 1; number <= 5; number++) {

            const line = document.getElementById(`line-${number}`);

            if (!line) continue;

            if (number < currentStep) {
                line.classList.add('completed');
            } else {
                line.classList.remove('completed');
            }

        }

    }


    // =====================================
    // Display Section Errors
    // =====================================

    function showSectionError(element, message) {

        if (!element) return;

        element.textContent = message;

        element.classList.remove('d-none');

    }


    // =====================================
    // Run Statistical Analysis
    // =====================================

    async function startAnalysis(dependencyType) {

        if (!['dependent', 'independent'].includes(dependencyType)) {

            alert('Invalid dependency type.');

            return;

        }


        window.dependencyType = dependencyType;


        // Hide dependency question

        dependencySection?.classList.add('d-none');


        // Hide previous results

        interpretationSection?.classList.add('d-none');

        visualizationSection?.classList.add('d-none');


        if (interpretationContent) {
            interpretationContent.textContent = '';
        }

        if (visualizationContent) {
            visualizationContent.innerHTML = '';
        }


        interpretationError?.classList.add('d-none');

        visualizationError?.classList.add('d-none');


        // Move to Analysis

        setStepper(4);


        if (nextQuestionButton) {

            nextQuestionButton.disabled = true;

            nextQuestionButton.textContent = 'Running Analysis...';

        }


        try {

            // Send dependency type to Flask

            const response = await fetch('/run-analysis', {

                method: 'POST',

                headers: {
                    'Content-Type': 'application/json'
                },

                body: JSON.stringify({
                    dependency_type: dependencyType
                })

            });


            const data = await response.json();


            if (!response.ok || !data.success) {

                throw new Error(
                    data.message || 'Could not complete the analysis.'
                );

            }


            // Save returned results

            window.lastAnalysisResult = data.result;

            window.lastInterpretation = data.interpretation;

            window.lastVisualization = data.visualization;


            // Display Interpretation

            await displayInterpretation(data);


            // Display Visualization automatically

            await displayVisualization(data);


        } catch (error) {

            console.error('Analysis Error:', error);

            alert(error.message);

            setStepper(3);


        } finally {

            if (nextQuestionButton) {

                nextQuestionButton.disabled = false;

                nextQuestionButton.textContent = 'Analyze';

            }

        }

    }


    
    // =====================================
    // Display Interpretation
    // =====================================

    async function displayInterpretation(data) {

        // Move to Interpretation

        setStepper(5);

        if (!interpretationSection) {

            throw new Error(
                'Interpretation section was not found.'
            );

        }

        interpretationSection.classList.remove('d-none');

        interpretationLoading?.classList.add('d-none');

        interpretationError?.classList.add('d-none');

        // Display Interpretation

        if (interpretationContent) {

            const interpretation =
                data.interpretation || '';

            if (
                typeof marked !== 'undefined' &&
                typeof DOMPurify !== 'undefined'
            ) {

                // Convert Markdown to HTML

                const html = marked.parse(interpretation);

                // Sanitize HTML before displaying

                interpretationContent.innerHTML =
                    DOMPurify.sanitize(html);

            } else {

                // Safe fallback if libraries are unavailable

                interpretationContent.textContent =
                    interpretation;

                interpretationContent.style.whiteSpace =
                    'pre-wrap';

                console.error(
                    'Marked.js or DOMPurify could not be loaded.'
                );

            }

        }

        interpretationSection.scrollIntoView({

            behavior: 'smooth',

            block: 'start'

        });

        // Give the user time to see the interpretation stage

        await new Promise(resolve => setTimeout(resolve, 700));

    }



    
    // =====================================
    // Display Visualization
    // =====================================

    async function displayVisualization(data) {

        // Move to Visualization
        setStepper(6);

        if (!visualizationSection) {
            throw new Error(
                'Visualization section was not found.'
            );
        }

        visualizationSection.classList.remove('d-none');

        visualizationLoading?.classList.remove('d-none');
        visualizationError?.classList.add('d-none');

        // Check if visualization was generated
        if (!data.visualization) {

            visualizationLoading?.classList.add('d-none');

            showSectionError(
                visualizationError,
                data.visualization_error ||
                'No visualization is available for this analysis.'
            );

            visualizationSection.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });

            return;
        }

        // Check Plotly availability
        if (typeof Plotly === 'undefined') {

            visualizationLoading?.classList.add('d-none');

            showSectionError(
                visualizationError,
                'Plotly library could not be loaded.'
            );

            return;
        }

        try {

            // Clear previous chart
            visualizationContent.innerHTML = '';

            const figure = data.visualization;

            // Create chart container
            const chartContainer = document.createElement('div');

            chartContainer.className = 'visualization-chart';

            visualizationContent.appendChild(chartContainer);

            // Make chart responsive
            const layout = {
                ...figure.layout,
                autosize: true
            };

            delete layout.width;

            // Render Plotly chart
            await Plotly.react(
                chartContainer,
                figure.data,
                layout,
                {
                    responsive: true,
                    displaylogo: false
                }
            );

            // Show chart name in Learning Mode only
            if (data.mode === 'learning') {

                const traces = figure.data || [];

                const hasHistogram = traces.some(
                    trace => trace.type === 'histogram'
                );

                const hasBox = traces.some(
                    trace => trace.type === 'box'
                );

                const hasScatter = traces.some(
                    trace => trace.type === 'scatter'
                );

                const hasBar = traces.some(
                    trace => trace.type === 'bar'
                );

                // Get Plotly figure title
                const figureTitle =
                    typeof figure.layout?.title === 'string'
                        ? figure.layout.title
                        : figure.layout?.title?.text || '';

                let chartName = '';
                let chartDescription = '';

                // Scatter with Marginal Distributions
                if (
                    hasScatter &&
                    (hasHistogram || hasBox)
                ) {

                    chartName =
                        'Scatter Plot with Marginal Distributions';

                    chartDescription =
                        'Includes a marginal Histogram and Box Plot.';

                }

                // Stacked Bar Chart
                else if (
                    hasBar &&
                    figure.layout?.barmode === 'stack'
                ) {

                    chartName = 'Stacked Bar Chart';

                }

                // Grouped Bar Chart
                else if (
                    hasBar &&
                    figure.layout?.barmode === 'group'
                ) {

                    chartName = 'Grouped Bar Chart';

                }

                // Ordinary Bar Chart
                else if (hasBar) {

                    chartName = 'Bar Chart';

                }

                // Dependent Wide Format
                else if (
                    hasHistogram &&
                    figureTitle.includes('Paired Differences')
                ) {

                    chartName =
                        'paired Histogram Plot';

                }

                // Dependent Long Format
                else if (
                    hasBox &&
                    figureTitle.includes('Before vs After')
                ) {

                    chartName = 'Paired Box Plot';

                }

                // Ordinary Histogram
                else if (hasHistogram) {

                    chartName = 'Histogram';

                }

                // Ordinary Box Plot
                else if (hasBox) {

                    chartName = 'Box Plot';

                }

                // Ordinary Scatter Plot
                else if (hasScatter) {

                    chartName = 'Scatter Plot';

                }

                // Fallback
                else {

                    chartName = 'Statistical Visualization';

                }

                // Create chart information below the plot
                const chartInfo = document.createElement('div');

                chartInfo.className =
                    'text-center mt-3 mb-2';

                const title = document.createElement('h5');

                title.className =
                    'fw-bold text-navy mb-2';

                title.textContent = chartName;

                chartInfo.appendChild(title);

                // Add description only for composite Scatter Plot
                if (chartDescription) {

                    const description = document.createElement('p');

                    description.className =
                        'text-muted small mb-0';

                    description.textContent = chartDescription;

                    chartInfo.appendChild(description);

                }

                visualizationContent.appendChild(chartInfo);

            }

            visualizationLoading?.classList.add('d-none');

            // Mark Visualization as completed
            setStepper(7);

        } catch (error) {

            console.error(
                'Plotly Rendering Error:',
                error
            );

            visualizationLoading?.classList.add('d-none');

            showSectionError(
                visualizationError,
                'Could not display the visualization.'
            );

        }

        visualizationSection.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });

    }



    
    // =====================================
    // Analyze Research Question
    // =====================================

    // Show Error Modal
    function showQuestionErrorModal(message, question) {

        const isArabic = /[\u0600-\u06FF]/.test(question);

        const modalElement = document.getElementById(
            'questionErrorModal'
        );

        const titleElement = document.getElementById(
            'questionErrorTitle'
        );

        const messageElement = document.getElementById(
            'questionErrorMessage'
        );

        if (!modalElement || !titleElement || !messageElement) {
            alert(message);
            return;
        }

        titleElement.textContent = isArabic
            ? 'سؤال البحث غير مدعوم'
            : 'Unsupported Research Question';

        messageElement.textContent = message;

        messageElement.dir = isArabic ? 'rtl' : 'ltr';
        titleElement.dir = isArabic ? 'rtl' : 'ltr';

        const errorModal = bootstrap.Modal.getOrCreateInstance(
            modalElement
        );

        errorModal.show();
    }

    // =====================================
    // Dataset Limit Error Modal
    // =====================================

    function showDatasetLimitModal(message) {

        const modalElement = document.getElementById(
            'questionErrorModal'
        );

        const titleElement = document.getElementById(
            'questionErrorTitle'
        );

        const messageElement = document.getElementById(
            'questionErrorMessage'
        );

        if (!modalElement || !titleElement || !messageElement) {
            alert(message);
            return;
        }

        titleElement.textContent = 'Dataset Limit Exceeded';

        messageElement.textContent = message;

        titleElement.dir = 'ltr';
        messageElement.dir = 'ltr';

        const errorModal = bootstrap.Modal.getOrCreateInstance(
            modalElement
        );

        errorModal.show();
    }


    if (nextQuestionButton && questionInput) {

        nextQuestionButton.addEventListener('click', async () => {

            const question = questionInput.value.trim();

            if (!question) {

                alert('Please enter your research question.');

                questionInput.focus();

                return;
            }

            nextQuestionButton.disabled = true;

            nextQuestionButton.textContent = 'Analyzing...';

            try {

                const response = await fetch('/analyze-question', {

                    method: 'POST',

                    headers: {
                        'Content-Type': 'application/json'
                    },

                    body: JSON.stringify({
                        question: question
                    })

                });

                const data = await response.json();

                if (!response.ok || !data.success) {

                    throw new Error(
                        data.message || 'Could not analyze the question.'
                    );

                }

                // Save research question information

                window.questionAnalysis = data.analysis;

                window.dependencyEvidence = data.dependency;

                const dependency = data.dependency;

                if (!dependency) {

                    throw new Error(
                        'Dependency information was not returned.'
                    );

                }

                // Detect question language

                const language = detectLanguage(question);

                // Reset previous dependency selection

                window.dependencyType = null;

                // Hide dependency section initially

                dependencySection?.classList.add('d-none');

                const yesButton = document.getElementById(
                    'dependency-yes'
                );

                const noButton = document.getElementById(
                    'dependency-no'
                );

                // Reset buttons

                if (yesButton) yesButton.disabled = false;

                if (noButton) noButton.disabled = false;

                // No dependency evidence:
                // Automatically use Independent

                if (!dependency.ask_user) {

                    console.log(
                        'Dependency Type: Independent'
                    );

                    await startAnalysis('independent');

                } else {

                    // Check dependency elements

                    if (
                        !dependencySection ||
                        !yesButton ||
                        !noButton
                    ) {

                        throw new Error(
                            'Dependency question elements were not found.'
                        );

                    }

                    // Display question in the user's language

                    updateDependencyLanguage(language);

                    // Show dependency question

                    dependencySection.classList.remove('d-none');

                    dependencySection.scrollIntoView({

                        behavior: 'smooth',

                        block: 'center'

                    });

                    // Yes = Dependent

                    yesButton.onclick = async () => {

                        yesButton.disabled = true;

                        noButton.disabled = true;

                        console.log(
                            'Dependency Type: Dependent'
                        );

                        await startAnalysis('dependent');

                    };

                    // No = Independent

                    noButton.onclick = async () => {

                        yesButton.disabled = true;

                        noButton.disabled = true;

                        console.log(
                            'Dependency Type: Independent'
                        );

                        await startAnalysis('independent');

                    };

                }

            } catch (error) {

                showQuestionErrorModal(
                    error.message,
                    question
                );

                console.error(
                    'Question Analysis Error:',
                    error
                );

            } finally {

                nextQuestionButton.disabled = false;

                nextQuestionButton.textContent = 'Analyze';

            }

        });

    }


    // =====================================
    // File Upload Elements
    // =====================================

    if (!dropzone || !fileInput) return;


    dropzone.addEventListener('click', (e) => {

        if (!e.target.closest('button')) {

            fileInput.click();

        }

    });


    dropzone.addEventListener('keydown', (e) => {

        if (e.key === ' ' || e.key === 'Enter') {

            e.preventDefault();

            fileInput.click();

        }

    });


    ['dragenter', 'dragover'].forEach(event => {

        dropzone.addEventListener(event, (e) => {

            e.preventDefault();

            dropzone.classList.add('dragover');

        });

    });


    ['dragleave', 'dragend', 'drop'].forEach(event => {

        dropzone.addEventListener(event, (e) => {

            e.preventDefault();

            dropzone.classList.remove('dragover');

        });

    });


    dropzone.addEventListener('drop', (e) => {

        if (e.dataTransfer.files.length) {

            handleFileSelection(e.dataTransfer.files[0]);

        }

    });


    fileInput.addEventListener('change', (e) => {

        if (e.target.files.length) {

            handleFileSelection(e.target.files[0]);

        }

    });



    // =====================================
    // Handle File Selection
    // =====================================

    async function handleFileSelection(file) {

        const extension = file.name.split('.').pop().toLowerCase();


        if (!['csv', 'xlsx'].includes(extension)) {

            showError(
                `Invalid file format: "${file.name}". Please upload CSV or XLSX.`
            );

            fileInput.value = '';

            return;

        }


        const formData = new FormData();

        formData.append('file', file);


        try {

            const response = await fetch('/upload', {

                method: 'POST',

                body: formData

            });

            const data = await response.json();


            // Check dataset limits

            if (data.error_type === 'dataset_limit') {

                showDatasetLimitModal(
                    data.message ||
                    'Dataset exceeds the allowed limits.'
                );

                fileInput.value = '';

                return;

            }


            // Check other upload errors

            if (!response.ok || !data.success) {

                throw new Error(
                    data.message || 'Could not process file.'
                );

            }


            if (!data.success) {

                throw new Error(
                    data.message || 'Could not process file.'
                );

            }


            displayCleanedData(data);


            uploadError?.classList.add('d-none');

            displayFileName.textContent = file.name;

            uploadPanel.classList.add('d-none');

            successPanel.classList.remove('d-none');


            // Move to Research Question

            setStepper(3);


            if (researchSection) {

                researchSection.classList.remove('d-none');

                researchSection.scrollIntoView({

                    behavior: 'smooth',

                    block: 'start'

                });

            }


        } catch (error) {

            showError(error.message);

            console.error(error);

        }

    }

    // =====================================
    // Display Cleaned Dataset
    // =====================================

    function displayCleanedData(data) {

        if (!tableHead || !tableBody) return;


        tableHead.innerHTML = '';

        tableBody.innerHTML = '';


        rowCount.textContent = data.row_count;

        columnCount.textContent = data.column_count;


        data.columns.forEach(column => {

            const th = document.createElement('th');

            th.textContent = column;

            tableHead.appendChild(th);

        });


        data.preview.slice(0, 5).forEach(row => {

            const tr = document.createElement('tr');


            data.columns.forEach(column => {

                const td = document.createElement('td');

                td.textContent = row[column] ?? '';

                tr.appendChild(td);

            });


            tableBody.appendChild(tr);

        });

    }



    // =====================================
    // Display Upload Errors
    // =====================================

    function showError(message) {

        if (errorMessage) {

            errorMessage.textContent = message;

        }

        uploadError?.classList.remove('d-none');

        uploadError?.setAttribute('aria-live', 'assertive');

    }



    // =====================================
    // Reset Upload and Workflow
    // =====================================

    if (btnReset) {

        btnReset.addEventListener('click', () => {

            // Reset file input

            fileInput.value = '';


            // Reset upload panels

            successPanel?.classList.add('d-none');

            uploadPanel?.classList.remove('d-none');

            uploadError?.classList.add('d-none');


            // Clear dataset preview

            if (tableHead) tableHead.innerHTML = '';

            if (tableBody) tableBody.innerHTML = '';


            if (rowCount) rowCount.textContent = '0';

            if (columnCount) columnCount.textContent = '0';


            // Hide workflow sections

            researchSection?.classList.add('d-none');

            dependencySection?.classList.add('d-none');

            interpretationSection?.classList.add('d-none');

            visualizationSection?.classList.add('d-none');


            // Clear research question

            if (questionInput) {
                questionInput.value = '';
            }


            // Clear interpretation

            if (interpretationContent) {
                interpretationContent.textContent = '';
            }

            interpretationLoading?.classList.add('d-none');

            interpretationError?.classList.add('d-none');


            // Clear visualization

            if (visualizationContent) {

                if (typeof Plotly !== 'undefined') {
                    Plotly.purge(visualizationContent);
                }

                visualizationContent.innerHTML = '';

            }

            visualizationLoading?.classList.add('d-none');

            visualizationError?.classList.add('d-none');


            // Reset dependency buttons

            const yesButton = document.getElementById(
                'dependency-yes'
            );

            const noButton = document.getElementById(
                'dependency-no'
            );

            if (yesButton) yesButton.disabled = false;

            if (noButton) noButton.disabled = false;


            // Reset application state

            window.dependencyType = null;

            window.dependencyEvidence = null;

            window.questionAnalysis = null;

            window.lastAnalysisResult = null;

            window.lastInterpretation = null;

            window.lastVisualization = null;


            // Reset progress stepper

            setStepper(1);


            // Reset Analyze button

            if (nextQuestionButton) {

                nextQuestionButton.disabled = false;

                nextQuestionButton.textContent = 'Analyze';

            }

            dropzone.focus();

        });

    }

    // =====================================
    // Initial State
    // =====================================

    setStepper(1);

});

