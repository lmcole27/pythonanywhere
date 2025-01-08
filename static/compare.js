
    // JavaScript to update the file name display - Primary File
const fileInput1 = document.getElementById('fileInput1');
const fileName1 = document.getElementById('fileName1');

fileInput1.addEventListener('change', function() {
    if (fileInput1.files.length > 0) {
        fileName1.textContent = fileInput1.files[0].name;
    } else {
        fileName1.textContent = 'No file chosen';
    }
});

    // JavaScript to update the file name display - Secondary File
const fileInput2 = document.getElementById('fileInput2');
const fileName2 = document.getElementById('fileName2');

fileInput2.addEventListener('change', function() {
    if (fileInput2.files.length > 0) {
        fileName2.textContent = fileInput2.files[0].name;
    } else {
        fileName2.textContent = 'No file chosen';
    }
});