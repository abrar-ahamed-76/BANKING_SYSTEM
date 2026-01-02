// JavaScript for banking system frontend interactions

// Function to validate form inputs
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required]');
    for (let input of inputs) {
        if (!input.value.trim()) {
            alert(`${input.name} is required`);
            return false;
        }
    }
    return true;
}

// Function to get URL parameter
function getUrlParameter(name) {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    const regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    const results = regex.exec(location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
}

// Function to set amount from URL parameter
function setAmountFromUrl() {
    const amount = getUrlParameter('amount');
    if (amount) {
        const amountInput = document.querySelector('input[name="amount"]');
        if (amountInput) {
            amountInput.value = amount;
        }
    }
}

// Function to handle quick amount buttons
function setupQuickAmountButtons() {
    const quickAmountButtons = document.querySelectorAll('.quick-amount[data-amount]');
    quickAmountButtons.forEach(button => {
        button.addEventListener('click', function() {
            const amount = this.getAttribute('data-amount');
            const amountInput = document.querySelector('input[name="amount"]');
            if (amountInput) {
                amountInput.value = amount;
            }
        });
    });
}

// Add event listeners to forms
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(form)) {
                e.preventDefault();
            }
        });
    });

    // Set amount from URL and setup quick amount buttons
    setAmountFromUrl();
    setupQuickAmountButtons();
});

// Function to show/hide password
function togglePassword() {
    const passwordField = document.getElementById('password');
    if (passwordField.type === 'password') {
        passwordField.type = 'text';
    } else {
        passwordField.type = 'password';
    }
}

// Function to confirm transaction
function confirmTransaction(type) {
    return confirm(`Are you sure you want to ${type}?`);
}

// Add confirmation to transaction forms
document.addEventListener('DOMContentLoaded', function() {
    const depositForm = document.querySelector('form[action*="deposit"]');
    const withdrawForm = document.querySelector('form[action*="withdraw"]');
    const transferForm = document.querySelector('form[action*="transfer"]');

    if (depositForm) {
        depositForm.addEventListener('submit', function(e) {
            if (!confirmTransaction('deposit')) {
                e.preventDefault();
            }
        });
    }

    if (withdrawForm) {
        withdrawForm.addEventListener('submit', function(e) {
            if (!confirmTransaction('withdraw')) {
                e.preventDefault();
            }
        });
    }

    if (transferForm) {
        transferForm.addEventListener('submit', function(e) {
            if (!confirmTransaction('transfer')) {
                e.preventDefault();
            }
        });
    }
});
