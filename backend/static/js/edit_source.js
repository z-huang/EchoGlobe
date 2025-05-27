$(document).ready(function () {
    $('#editSourceBtn').on('click', function () {
        $('#sourceTranscript').hide();
        $('#editSourceForm').show();
        $('#editSourceTextarea').focus();
    });
    $('#cancelEditSourceBtn').on('click', function () {
        $('#editSourceForm').hide();
        $('#sourceTranscript').show();
    });
});