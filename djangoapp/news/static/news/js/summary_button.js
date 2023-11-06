const toggleButtons = document.querySelectorAll(".toggle-button");

toggleButtons.forEach((button) => {
    button.addEventListener("click", function() {
        const icon = this.querySelector("i");
        if (icon.classList.contains("fa-chevron-down")) {
            icon.classList.remove("fa-chevron-down");
            icon.classList.add("fa-chevron-up");
            this.classList.add("active");
            this.setAttribute("aria-pressed", "true");
        } else {
            icon.classList.remove("fa-chevron-up");
            icon.classList.add("fa-chevron-down");
            this.classList.remove("active");
            this.setAttribute("aria-pressed", "false");
        }
    });
});