// Main JavaScript file for Azure AI-900 Quiz Platform

document.addEventListener('DOMContentLoaded', function() {
    
    // Enable quiz option selection styling
    const quizOptions = document.querySelectorAll('.quiz-option');
    if (quizOptions.length > 0) {
        quizOptions.forEach(option => {
            option.addEventListener('click', function() {
                // Find the radio input within this option
                const radio = this.querySelector('input[type="radio"]');
                if (radio) {
                    radio.checked = true;
                    
                    // Remove selected class from all options
                    quizOptions.forEach(opt => {
                        opt.classList.remove('selected');
                    });
                    
                    // Add selected class to the clicked option
                    this.classList.add('selected');
                }
            });
        });
    }
    
    // Quiz timer functionality
    const timerElement = document.getElementById('quiz-timer');
    if (timerElement) {
        let timeRemaining = parseInt(timerElement.dataset.seconds || 0);
        
        if (timeRemaining > 0) {
            const timerInterval = setInterval(function() {
                timeRemaining -= 1;
                
                if (timeRemaining <= 0) {
                    clearInterval(timerInterval);
                    // Auto-submit form when time is up
                    document.getElementById('quiz-form').submit();
                }
                
                // Update the timer display
                const minutes = Math.floor(timeRemaining / 60);
                const seconds = timeRemaining % 60;
                timerElement.textContent = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
                
                // Change color when time is running low
                if (timeRemaining < 60) {
                    timerElement.classList.add('text-danger');
                } else if (timeRemaining < 180) {
                    timerElement.classList.add('text-warning');
                }
                
            }, 1000);
        }
    }
    
    // Auto-dismiss flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert:not(.alert-danger)');
    if (flashMessages.length > 0) {
        flashMessages.forEach(message => {
            setTimeout(function() {
                const closeButton = message.querySelector('.btn-close');
                if (closeButton) {
                    closeButton.click();
                }
            }, 5000);
        });
    }
    
    // Admin interface: form validation for quiz and question forms
    const quizForm = document.getElementById('quiz-form');
    if (quizForm) {
        quizForm.addEventListener('submit', function(event) {
            const titleInput = document.getElementById('title');
            const timeLimitInput = document.getElementById('time_limit');
            const passPercentageInput = document.getElementById('pass_percentage');
            
            if (titleInput && titleInput.value.trim() === '') {
                event.preventDefault();
                titleInput.classList.add('is-invalid');
                showFormError(titleInput, 'Title is required');
            }
            
            if (timeLimitInput && (isNaN(timeLimitInput.value) || parseInt(timeLimitInput.value) <= 0)) {
                event.preventDefault();
                timeLimitInput.classList.add('is-invalid');
                showFormError(timeLimitInput, 'Time limit must be a positive number');
            }
            
            if (passPercentageInput && (isNaN(passPercentageInput.value) || parseInt(passPercentageInput.value) < 0 || parseInt(passPercentageInput.value) > 100)) {
                event.preventDefault();
                passPercentageInput.classList.add('is-invalid');
                showFormError(passPercentageInput, 'Pass percentage must be between 0 and 100');
            }
        });
    }
    
    // Question form validation
    const questionForm = document.getElementById('question-form');
    if (questionForm) {
        questionForm.addEventListener('submit', function(event) {
            const questionText = document.getElementById('text');
            const optionInputs = document.querySelectorAll('input[name="option_text"]');
            const correctOption = document.querySelector('input[name="correct_option"]:checked');
            
            if (questionText && questionText.value.trim() === '') {
                event.preventDefault();
                questionText.classList.add('is-invalid');
                showFormError(questionText, 'Question text is required');
            }
            
            // Check if at least 2 options are provided
            let filledOptions = 0;
            optionInputs.forEach(input => {
                if (input.value.trim() !== '') {
                    filledOptions++;
                }
            });
            
            if (filledOptions < 2) {
                event.preventDefault();
                showFormError(optionInputs[0], 'At least 2 options are required');
            }
            
            // Check if a correct option is selected
            if (!correctOption) {
                event.preventDefault();
                showFormError(optionInputs[0], 'Please select the correct answer');
            }
        });
    }
    
    function showFormError(element, message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        
        // Remove any existing error messages
        const existingError = element.nextElementSibling;
        if (existingError && existingError.className === 'invalid-feedback') {
            existingError.remove();
        }
        
        element.parentNode.appendChild(errorDiv);
    }
    
    // Form input validation reset
    const formInputs = document.querySelectorAll('.form-control');
    formInputs.forEach(input => {
        input.addEventListener('input', function() {
            this.classList.remove('is-invalid');
            const errorMessage = this.nextElementSibling;
            if (errorMessage && errorMessage.className === 'invalid-feedback') {
                errorMessage.remove();
            }
        });
    });
    
});