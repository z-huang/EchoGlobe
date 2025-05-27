document.addEventListener("DOMContentLoaded", function () {
    const languageDropdown = document.querySelector(".dropdown-content");
    const languageButtons = languageDropdown.querySelectorAll("a");
    const transcriptBlocks = document.querySelectorAll(".transcript-block");

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

            // Update visible transcripts
            updateVisibleTranscripts(selectedLang);

            // Update active class for the dropdown
            languageButtons.forEach(btn => btn.classList.remove("active"));
            this.classList.add("active");
        });
    });

    // Initialize: Show source transcript and default language transcript
    const defaultLang = languageDropdown.querySelector(".active").getAttribute("data-lang");
    updateVisibleTranscripts(defaultLang);
});