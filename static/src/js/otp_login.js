(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        
        const step1 = document.getElementById('step1');
        const step2 = document.getElementById('step2');
        const phoneInput = document.getElementById('phone');
        const codeInput = document.getElementById('code');
        const phoneDisplay = document.getElementById('phoneDisplay');
        const sendBtn = document.getElementById('sendBtn');
        const verifyBtn = document.getElementById('verifyBtn');
        const resendBtn = document.getElementById('resendBtn');
        const backBtn = document.getElementById('backBtn');
        const phoneError = document.getElementById('phoneError');
        const otpError = document.getElementById('otpError');
        const countdownEl = document.getElementById('countdown');
        const timerBox = document.getElementById('timerBox');

        let currentUserId = null;
        let countdownInterval = null;
        let redirectUrl = '/web';
        let isSending = false;

        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('redirect')) {
            redirectUrl = urlParams.get('redirect');
        }

        function showError(element, message) {
            const span = element.querySelector('span');
            if (span) span.textContent = message;
            element.classList.remove('d-none');
        }

        function hideError(element) {
            element.classList.add('d-none');
        }

        function startCountdown(seconds) {
            let remaining = seconds;
            timerBox.classList.remove('d-none');
            resendBtn.classList.add('d-none');
            
            if (countdownInterval) clearInterval(countdownInterval);
            
            countdownInterval = setInterval(function() {
                remaining--;
                if (countdownEl) countdownEl.textContent = remaining;
                
                if (remaining <= 0) {
                    clearInterval(countdownInterval);
                    timerBox.classList.add('d-none');
                    resendBtn.classList.remove('d-none');
                }
            }, 1000);
        }

        async function rpcCall(url, params) {
            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        jsonrpc: '2.0',
                        method: 'call',
                        params: params,
                        id: new Date().getTime()
                    })
                });
                
                const data = await response.json();
                return data.result || data;
            } catch (error) {
                console.error('RPC Error:', error);
                throw error;
            }
        }

        sendBtn.addEventListener('click', async function() {
            if (isSending) return;
            
            const phone = phoneInput.value.trim();
            hideError(phoneError);

            if (!phone) {
                showError(phoneError,' Please enter your mobile number.');
                return;
            }

            if (!/^09[0-9]{9}$/.test(phone)) {
                showError(phoneError, 'The mobile number is invalid. Example: 09123456789');
                return;
            }

            isSending = true;
            sendBtn.disabled = true;
            sendBtn.innerHTML = '<span class="otp-spinner"></span> <span>Sending...</span>';

            try {
                const response = await rpcCall('/otp/send', {
                    phone_number: phone
                });

                if (response.error) {
                    showError(phoneError, response.error);
                    sendBtn.disabled = false;
                    sendBtn.innerHTML = '<i class="fa fa-paper-plane"></i> <span> Send verification code</span>';
                    isSending = false;
                } else {
                    currentUserId = response.user_id;
                    phoneDisplay.textContent = phone;
                    step1.classList.add('d-none');
                    step2.classList.remove('d-none');
                    codeInput.focus();
                    startCountdown(120);

                    if (response.test_otp) {
                        console.log("🔑 TEST OTP CODE:", response.test_otp);
                        setTimeout(() => {
                            alert(`🔔 Test mode is active!\n\nYour verification code: ${response.test_otp}\n\nPlease enter this code in the next step.`);
                        }, 500);
                    }
                    
                    sendBtn.disabled = false;
                    sendBtn.innerHTML = '<i class="fa fa-paper-plane"></i> <span> Send verification code </span>';
                    isSending = false;
                }
            } catch (error) {
                showError(phoneError, 'Error connecting to the server. Please try again.');
                sendBtn.disabled = false;
                sendBtn.innerHTML = '<i class="fa fa-paper-plane"></i> <span> Send verification code</span>';
                isSending = false;
            }
        });

        verifyBtn.addEventListener('click', async function() {
            const code = codeInput.value.trim();
            hideError(otpError);

            if (!code) {
                showError(otpError,' Please enter the verification code.');
                return;
            }

            if (!/^[0-9]{6}$/.test(code)) {
                showError(otpError, 'The verification code must be 6 digits.');
                return;
            }

            verifyBtn.disabled = true;
            verifyBtn.innerHTML = '<span class="otp-spinner"></span> <span>Logging in...</span>';

            try {
                const response = await rpcCall('/otp/verify', {
                    code: code,
                    user_id: currentUserId,
                    redirect: redirectUrl
                });

                if (response.error) {
                    showError(otpError, response.error);
                    verifyBtn.disabled = false;
                    verifyBtn.innerHTML = '<i class="fa fa-check-circle"></i> <span>Log in to account</span>';
                } else if (response.success) {
                    verifyBtn.innerHTML = '<i class="fa fa-check"></i> <span>Successful login!</span>';
                    window.location.href = response.redirect || '/web';
                }
            } catch (error) {
                showError(otpError, 'Error verifying the code. Please try again.');
                verifyBtn.disabled = false;
                verifyBtn.innerHTML = '<i class="fa fa-check-circle"></i> <span>Log in to account</span>';
            }
        });

        resendBtn.addEventListener('click', async function() {
            if (isSending) return;
            
            hideError(otpError);
            isSending = true;
            resendBtn.disabled = true;
            resendBtn.innerHTML = '<span class="otp-spinner"></span> Sending...';

            try {
                const phone = phoneInput.value.trim();
                const response = await rpcCall('/otp/send', {
                    phone_number: phone
                });

                if (response.error) {
                    showError(otpError, response.error);
                    resendBtn.disabled = false;
                    resendBtn.innerHTML = '<i class="fa fa-redo"></i>Resend verification code';
                    isSending = false;
                } else {
                    currentUserId = response.user_id;
                    codeInput.value = '';
                    codeInput.focus();
                    startCountdown(120);
                    resendBtn.disabled = false;
                    resendBtn.innerHTML = '<i class="fa fa-redo"></i> Resend verification code';
                    isSending = false;
                }
            } catch (error) {
                showError(otpError, 'Error resending');
                resendBtn.disabled = false;
                resendBtn.innerHTML = '<i class="fa fa-redo"></i>  Resend verification code';
                isSending = false;
            }
        });

        backBtn.addEventListener('click', function() {
            if (countdownInterval) {
                clearInterval(countdownInterval);
                countdownInterval = null;
            }
            
            step2.classList.add('d-none');
            step1.classList.remove('d-none');
            
            codeInput.value = '';
            hideError(otpError);
            hideError(phoneError);
            
            sendBtn.disabled = false;
            sendBtn.innerHTML = '<i class="fa fa-paper-plane"></i> <span>  Send verification code </span>';
            
            resendBtn.disabled = false;
            resendBtn.innerHTML = '<i class="fa fa-redo"></i>  Send verification code again';
            
            timerBox.classList.add('d-none');
            
            isSending = false;
            
            phoneInput.focus();
        });

        const odooLoginBtn = document.getElementById('odooLoginBtn');
        if (odooLoginBtn) {
            odooLoginBtn.addEventListener('click', function(e) {
                e.preventDefault();
                window.location.href = '/login/standard';
            });
        }

        phoneInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendBtn.click();
            }
        });

        codeInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                verifyBtn.click();
            }
        });

        codeInput.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^0-9]/g, '');
        });

        phoneInput.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^0-9]/g, '');
        });

        phoneInput.focus();
    });
})();