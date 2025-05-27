document.addEventListener("DOMContentLoaded", function () {
    const languageDropdown = document.querySelector(".dropdown-content");
    const languageButtons = languageDropdown.querySelectorAll("a");
    const transcriptBlocks = document.querySelectorAll(".transcript-block");
    const languageButton = document.querySelector(".language-btn"); // The button with the 🌐 icon

    // Function to show only the source transcript and the selected target transcript
    function updateVisibleTranscripts(selectedLang) {
        transcriptBlocks.forEach(block => {
            const blockLang = block.getAttribute("data-lang");
            if (blockLang === "source" || blockLang === selectedLang) {
                block.style.display = "block";
            } else {
                block.style.display = "none";
            }
        });
    }

    // Add click event listeners to language buttons
    languageButtons.forEach(button => {
        button.addEventListener("click", function (e) {
            e.preventDefault();
            const selectedLang = this.getAttribute("data-lang");
            const selectedLangText = this.textContent.trim(); // Get the text of the selected language

            // Update visible transcripts
            updateVisibleTranscripts(selectedLang);

            // Update active class for the dropdown
            languageButtons.forEach(btn => btn.classList.remove("active"));
            this.classList.add("active");

            // Update the text next to the 🌐 icon
            languageButton.innerHTML = `<span class="btn-icon">🌐</span> ${selectedLangText}`;
        });
    });

    // Initialize: Show source transcript and Chinese transcript by default
    const defaultLang = "cn"; // Set default language to Chinese
    const defaultButton = languageDropdown.querySelector(`[data-lang="${defaultLang}"]`);
    if (defaultButton) {
        defaultButton.classList.add("active");
        const defaultLangText = defaultButton.textContent.trim(); // Get the default language text
        languageButton.innerHTML = `<span class="btn-icon">🌐</span> ${defaultLangText}`;
    }
    updateVisibleTranscripts(defaultLang);
});