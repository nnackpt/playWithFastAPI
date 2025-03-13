let secondsLeft = 5;
        const countdownElement = document.getElementById('countdown');
        
        const timer = setInterval(() => {
            secondsLeft--;
            countdownElement.textContent = secondsLeft;
            
            if (secondsLeft <= 0) {
                clearInterval(timer);
                window.location.href = '/';
            }
        }, 1000);