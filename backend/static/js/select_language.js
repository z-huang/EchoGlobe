document.addEventListener('DOMContentLoaded', function () {
    // Map Django codes to transcript fields and display names
    const langMap = {
        'en': { key: 'en_transcription', label: 'English', dropdown: 'en-US' },
        'cn': { key: 'cn_transcription', label: '中文', dropdown: 'cmn-Hant-TW' },
        'jp': { key: 'jp_transcription', label: '日本語', dropdown: 'ja-JP' },
        'de': { key: 'de_transcription', label: 'Deutsch', dropdown: 'de-DE' }
    };

    // Map dropdown values to Django codes
    const dropdownToDjango = {
        'en-US': 'en',
        'cmn-Hant-TW': 'cn',
        'ja-JP': 'jp',
        'de-DE': 'de'
    };

    // Get transcript data from Django context (rendered as JS variables)
    const transcriptData = {
        en: "{{ content.en_transcription|escapejs }}",
        cn: "{{ content.cn_transcription|escapejs }}",
        jp: "{{ content.jp_transcription|escapejs }}",
        de: "{{ content.de_transcription|escapejs }}"
    };
    const srcLang = "{{ content.src_language }}";

    // Set initial target language (default to source)
    let targetLang = srcLang;

    function renderTranscripts() {
        // Source transcript
        const sourceDiv = document.getElementById('sourceTranscript');
        if (sourceDiv) {
            sourceDiv.textContent = transcriptData[srcLang] || 'No transcript available.';
        }

        // Target transcript (show only if different from source)
        const targetDiv = document.getElementById('targetTranscript');
        if (targetDiv) {
            if (targetLang !== srcLang) {
                targetDiv.textContent = transcriptData[targetLang] || 'No transcript available.';
            } else {
                targetDiv.textContent = '';
            }
        }
    }

    // Handle language dropdown selection
    document.querySelectorAll('.dropdown-content a[data-lang]').forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            // Remove active class from all
            document.querySelectorAll('.dropdown-content a[data-lang]').forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            // Set target language
            const selectedDropdown = this.getAttribute('data-lang');
            targetLang = dropdownToDjango[selectedDropdown] || srcLang;
            renderTranscripts();
        });
    });

    // Initial render
    renderTranscripts();
});