document.addEventListener('DOMContentLoaded', () => {
    // Handling File Upload Drag & Drop and Preview
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');
    
    const filePreview = document.getElementById('file-preview');
    const fileNameDisplay = document.getElementById('file-name');
    const fileSizeDisplay = document.getElementById('file-size');
    const removeFileBtn = document.getElementById('remove-file');
    
    const analyzeBtn = document.getElementById('analyze-btn');
    const loadingState = document.getElementById('loading-state');

    if (uploadZone && fileInput) {
        // Trigger file input click when browsing via button
        browseBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // prevent clicking uploadZone from firing twice
            fileInput.click();
        });

        // Trigger file input when clicking on upload zone
        uploadZone.addEventListener('click', () => {
            fileInput.click();
        });

        // Handle Drag Events
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadZone.addEventListener(eventName, () => {
                uploadZone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, () => {
                uploadZone.classList.remove('dragover');
            }, false);
        });

        uploadZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            handleFiles(files);
        });

        fileInput.addEventListener('change', function() {
            handleFiles(this.files);
        });

        function handleFiles(files) {
            if (files.length > 0) {
                const file = files[0];
                
                // Validate if it's a PDF (basic check)
                if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
                    displayFileInfo(file);
                } else {
                    alert('Please upload a valid PDF file.');
                }
            }
        }

        function displayFileInfo(file) {
            uploadZone.classList.add('d-none');
            filePreview.classList.remove('d-none');
            
            fileNameDisplay.textContent = file.name;
            
            // Format file size
            const sizeInMB = (file.size / (1024 * 1024)).toFixed(2);
            fileSizeDisplay.textContent = sizeInMB > 0 ? `${sizeInMB} MB` : `${(file.size / 1024).toFixed(2)} KB`;
        }
        
        // Remove File functionality
        if (removeFileBtn) {
            removeFileBtn.addEventListener('click', () => {
                fileInput.value = '';
                filePreview.classList.add('d-none');
                uploadZone.classList.remove('d-none');
            });
        }

        // Actual Analysis with File Upload
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => {
                const file = fileInput.files[0];
                if (!file) return;

                const nameInput = document.getElementById('candidate-name');
                const candidateName = nameInput ? nameInput.value.trim() : "";
                
                if (!candidateName) {
                    alert('Please enter your full name before proceeding.');
                    return;
                }

                filePreview.classList.add('d-none');
                loadingState.classList.remove('d-none');
                
                const formData = new FormData();
                formData.append('file', file);
                formData.append('candidate_name', candidateName);

                fetch('/upload', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.redirect) {
                        // Delay slightly for visual effect
                        setTimeout(() => {
                            window.location.href = data.redirect;
                        }, 1000);
                    } else if (data.error) {
                        alert('Error: ' + data.error);
                        loadingState.classList.add('d-none');
                        filePreview.classList.remove('d-none');
                    }
                })
                .catch(error => {
                    console.error('Error uploading file:', error);
                    alert('An error occurred during resume analysis.');
                    loadingState.classList.add('d-none');
                    filePreview.classList.remove('d-none');
                });
            });
        }
    }
});
