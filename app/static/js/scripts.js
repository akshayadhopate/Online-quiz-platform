document.addEventListener("DOMContentLoaded", function() {
    const timeElement = document.getElementById("time");
    if (timeElement) {
        let timeLeft = 30; // 30 seconds per question
        const timer = setInterval(function() {
            timeLeft--;
            timeElement.textContent = timeLeft;
            if (timeLeft <= 0) {
                clearInterval(timer);
                document.querySelector("form").submit(); // Auto-submit on timeout
            }
        }, 1000);
    }
});