// Admin Dashboard functionality
document.addEventListener('DOMContentLoaded', function() {
    // Rich text editor initialization
    if (document.querySelectorAll('.rich-editor').length > 0) {
        document.querySelectorAll('.rich-editor').forEach(function(editor) {
            ClassicEditor
                .create(editor, {
                    toolbar: ['heading', '|', 'bold', 'italic', 'link', 'bulletedList', 'numberedList', 'blockQuote'],
                    direction: 'rtl',
                    language: 'ar'
                })
                .catch(error => {
                    console.error('Rich text editor error:', error);
                });
        });
    }

    // Image upload handling with progress
    const imageInputs = document.querySelectorAll('.image-upload');
    imageInputs.forEach(input => {
        input.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const validExtensions = ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'];
                const fileExtension = file.name.split('.').pop().toLowerCase();

                if (!validExtensions.includes(fileExtension)) {
                    showAlert('صيغة الملف غير صالحة. الصيغ المدعومة: ' + validExtensions.join(', '), 'danger');
                    this.value = '';
                    return;
                }

                const maxSize = 5 * 1024 * 1024;
                if (file.size > maxSize) {
                    showAlert('حجم الملف كبير جداً. الحد الأقصى هو 5 ميجابايت', 'danger');
                    this.value = '';
                    return;
                }

                const formData = new FormData();
                formData.append('image', file);
                formData.append('section', input.dataset.section || '');
                formData.append('key', input.dataset.key || '');

                const xhr = new XMLHttpRequest();
                xhr.open('POST', '/api/upload-image', true);

                // Show progress
                const progressContainer = document.createElement('div');
                progressContainer.className = 'progress mt-2';
                progressContainer.innerHTML = '<div class="progress-bar" role="progressbar"></div>';
                input.parentElement.appendChild(progressContainer);
                const progressBar = progressContainer.querySelector('.progress-bar');

                xhr.upload.onprogress = function(e) {
                    if (e.lengthComputable) {
                        const percentComplete = (e.loaded / e.total) * 100;
                        progressBar.style.width = percentComplete + '%';
                        progressBar.textContent = Math.round(percentComplete) + '%';
                    }
                };

                xhr.onload = function() {
                    progressContainer.remove();
                    if (xhr.status === 200) {
                        const response = JSON.parse(xhr.responseText);
                        if (response.success) {
                            showAlert('تم رفع الصورة بنجاح', 'success');
                            // Update preview if exists
                            const previewElement = input.parentElement.querySelector('img');
                            if (previewElement && response.path) {
                                previewElement.src = response.path;
                            }
                        } else {
                            showAlert('حدث خطأ أثناء رفع الصورة: ' + response.error, 'danger');
                        }
                    } else {
                        showAlert('حدث خطأ أثناء رفع الصورة', 'danger');
                    }
                };

                xhr.onerror = function() {
                    progressContainer.remove();
                    showAlert('حدث خطأ أثناء الاتصال بالخادم', 'danger');
                };

                xhr.send(formData);
            }
        });
    });

    // AJAX form submissions
    const ajaxForms = document.querySelectorAll('form[data-ajax="true"]');
    ajaxForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;
            const actionUrl = this.getAttribute('action');

            // Disable button and show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> جارٍ المعالجة...';

            fetch(actionUrl, {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                // Show alert based on response
                const alertDiv = document.createElement('div');
                alertDiv.className = data.success 
                    ? 'alert alert-success' 
                    : 'alert alert-danger';
                alertDiv.textContent = data.message;

                const alertContainer = document.querySelector('.alert-container');
                alertContainer.innerHTML = '';
                alertContainer.appendChild(alertDiv);

                // Reset form if successful
                if (data.success) {
                    form.reset();

                    // If there's a redirect URL, navigate after delay
                    if (data.redirect) {
                        setTimeout(() => {
                            window.location.href = data.redirect;
                        }, 1000);
                    }
                }

                // Reset button state
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;

                // Auto-hide alert after 4 seconds
                setTimeout(() => {
                    alertDiv.classList.add('fade');
                    setTimeout(() => alertDiv.remove(), 500);
                }, 4000);
            })
            .catch(error => {
                console.error('Error submitting form:', error);

                // Show error alert
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-danger';
                alertDiv.textContent = 'حدث خطأ في النظام. يرجى المحاولة مرة أخرى.';

                const alertContainer = document.querySelector('.alert-container');
                alertContainer.innerHTML = '';
                alertContainer.appendChild(alertDiv);

                // Reset button state
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            });
        });
    });

    // Live content editing
    const liveEditElements = document.querySelectorAll('[data-live-edit="true"]');
    liveEditElements.forEach(element => {
        element.addEventListener('click', function() {
            if (this.getAttribute('data-editing') === 'true') return;

            const originalContent = this.innerHTML;
            const sectionId = this.getAttribute('data-section-id');
            const contentKey = this.getAttribute('data-key');

            // Create and configure edit field
            const editField = document.createElement('textarea');
            editField.className = 'form-control text-right';
            editField.style.direction = 'rtl';
            editField.value = this.textContent.trim();
            editField.rows = 3;

            // Replace element with edit field
            this.innerHTML = '';
            this.appendChild(editField);
            this.setAttribute('data-editing', 'true');

            // Focus the textarea
            editField.focus();

            // Create save/cancel buttons
            const buttonContainer = document.createElement('div');
            buttonContainer.className = 'mt-2 text-left';

            const saveButton = document.createElement('button');
            saveButton.className = 'btn btn-sm btn-success ml-2';
            saveButton.textContent = 'حفظ';

            const cancelButton = document.createElement('button');
            cancelButton.className = 'btn btn-sm btn-secondary';
            cancelButton.textContent = 'إلغاء';

            buttonContainer.appendChild(saveButton);
            buttonContainer.appendChild(cancelButton);
            this.appendChild(buttonContainer);

            // Cancel button handler
            cancelButton.addEventListener('click', function() {
                element.innerHTML = originalContent;
                element.removeAttribute('data-editing');
            });

            // Save button handler
            saveButton.addEventListener('click', function() {
                const newValue = editField.value.trim();

                // Show loading spinner
                buttonContainer.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"><span class="sr-only">جارٍ الحفظ...</span></div>';

                // Send AJAX request to update content
                fetch('/api/content/update', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        section_id: sectionId,
                        key: contentKey,
                        value: newValue
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Update the element with new content
                        element.innerHTML = newValue;
                        element.removeAttribute('data-editing');

                        // Show success notification
                        const notification = document.createElement('div');
                        notification.className = 'alert alert-success alert-dismissible fade show position-fixed';
                        notification.style.top = '20px';
                        notification.style.right = '20px';
                        notification.style.zIndex = '9999';
                        notification.innerHTML = `
                            <strong>نجاح!</strong> ${data.message}
                            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                            </button>
                        `;

                        document.body.appendChild(notification);

                        // Auto-remove notification after 3 seconds
                        setTimeout(() => {
                            notification.remove();
                        }, 3000);
                    } else {
                        // Restore original content on error
                        element.innerHTML = originalContent;
                        element.removeAttribute('data-editing');

                        // Show error alert
                        alert('خطأ: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error updating content:', error);
                    element.innerHTML = originalContent;
                    element.removeAttribute('data-editing');
                    alert('حدث خطأ في النظام. يرجى المحاولة مرة أخرى.');
                });
            });
        });
    });

    // Handle image upload via base64
    const profileImageElement = document.getElementById('profileImageUpload');
    if (profileImageElement) {
        profileImageElement.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const base64Data = e.target.result;

                    // Send base64 image to server
                    fetch('/api/image/upload_base64', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            image: base64Data,
                            section: 'about',
                            key: 'profile_image'
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Update profile image
                            const previewElement = document.getElementById('profileImagePreview');
                            if (previewElement) {
                                previewElement.src = data.url;
                                previewElement.classList.remove('hidden');
                            }

                            // Show success message
                            alert(data.message);
                        } else {
                            alert('خطأ: ' + data.message);
                        }
                    })
                    .catch(error => {
                        console.error('Error uploading image:', error);
                        alert('حدث خطأ في النظام. يرجى المحاولة مرة أخرى.');
                    });
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Add portfolio item form handling
    function initializePortfolioForm() {
        const addPortfolioForm = document.getElementById('addPortfolioForm');
        if (addPortfolioForm) {
            addPortfolioForm.addEventListener('submit', function(e) {
                e.preventDefault();

                // Basic validation
                const title = this.querySelector('[name="title"]').value;
                const description = this.querySelector('[name="description"]').value;
                const image = this.querySelector('[name="image"]').files[0];
                const category = this.querySelector('[name="category"]').value;

                if (!title || !description || !image || !category) {
                    showAlert('يرجى ملء جميع الحقول المطلوبة', 'danger');
                    return;
                }

                const submitButton = this.querySelector('button[type="submit"]');
                submitButton.disabled = true;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> جارٍ الإضافة...';

                const formData = new FormData(this);

                fetch('/admin/portfolio/add', {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.text();
                })
                .then(() => {
                    showAlert('تم إضافة المشروع بنجاح', 'success');
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                })
                .catch(error => {
                    console.error('Error:', error);
                    showAlert(error.message || 'حدث خطأ أثناء إضافة المشروع', 'danger');
                    submitButton.disabled = false;
                    submitButton.innerHTML = '<i class="fas fa-plus-circle me-1"></i> إضافة المشروع';
                });
            });
        }
    }

    // Initialize form and editors when document is ready
    document.addEventListener('DOMContentLoaded', function() {
        if (document.getElementById('description')) {
            ClassicEditor
                .create(document.getElementById('description'))
                .then(editor => {
                    console.log('Editor initialized');
                })
                .catch(error => {
                    console.error('Editor error:', error);
                });
        }

        initializePortfolioForm();
    });

    // CKEditor for description fields
    if (document.getElementById('description')) {
        ClassicEditor
            .create(document.getElementById('description'))
            .catch(error => {
                console.error(error);
            });
    }

    // Comment management functionality
    // Handle approve comment buttons
    const approveButtons = document.querySelectorAll('.approve-comment-btn');
    approveButtons.forEach(button => {
        button.addEventListener('click', function() {
            const commentId = this.getAttribute('data-id');
            fetch(`/admin/portfolio-comments/${commentId}/approve`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if(data.success) {
                    location.reload();
                }
            });
        });
    });

    // Handle delete comment buttons
    const deleteButtons = document.querySelectorAll('.delete-comment-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            if(confirm('هل أنت متأكد من حذف هذا التعليق؟')) {
                const commentId = this.getAttribute('data-id');
                fetch(`/admin/portfolio-comments/${commentId}/delete`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if(data.success) {
                        location.reload();
                    }
                });
            }
        });
    });


    // Contact Form Handling (added)
    document.addEventListener('DOMContentLoaded', function() {
        // التحقق من وجود jQuery وعناصر نموذج الاتصال قبل استخدامها
        if (typeof $ !== 'undefined' && $('#contactForm').length > 0) {
            $('#contactForm').submit(function(e) {
                e.preventDefault();

                const alert = $('#contactFormAlert');
                const submitBtn = $(this).find('button[type="submit"]');
                const originalBtnText = submitBtn.html();

                // Show loading state
                submitBtn.html('<i class="fas fa-spinner fa-spin"></i> جاري الإرسال...');
                submitBtn.prop('disabled', true);
                alert.removeClass('bg-red-100 text-red-700 bg-green-100 text-green-700').addClass('hidden');

                const formData = {
                    name: $('#contactForm input[name="name"]').val(),
                    email: $('#contactForm input[name="email"]').val(),
                    message: $('#contactForm textarea[name="message"]').val()
                };
                
                $.ajax({
                    url: '/api/contact',
                    type: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify(formData),
                    success: function(response) {
                        if (response.success) {
                            alert.removeClass('hidden bg-red-100 text-red-700')
                                 .addClass('bg-green-100 text-green-700')
                                 .html('<i class="fas fa-check-circle"></i> ' + response.message);
                            $('#contactForm')[0].reset();
                        } else {
                            alert.removeClass('hidden bg-green-100 text-green-700')
                                 .addClass('bg-red-100 text-red-700')
                                 .html('<i class="fas fa-exclamation-circle"></i> ' + response.error);
                        }
                    },
                    error: function(xhr, status, error) {
                        const errorMessage = xhr.responseJSON?.error || 'حدث خطأ أثناء إرسال الرسالة';
                        alert.removeClass('hidden bg-green-100 text-green-700')
                             .addClass('bg-red-100 text-red-700')
                             .html('<i class="fas fa-exclamation-circle"></i> ' + errorMessage);
                    },
                    complete: function() {
                        // Reset button state
                        submitBtn.html(originalBtnText);
                        submitBtn.prop('disabled', false);
                    }
                });
            });
        }
    });

// Admin button shortcut (Ctrl+Alt+A)
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.altKey && e.key.toLowerCase() === 'a') {
        e.preventDefault();
        const adminBtn = document.querySelector('.admin-link');
        if (adminBtn) {
            adminBtn.style.display = adminBtn.style.display === 'none' ? 'block' : 'none';

            if (adminBtn.style.display === 'block') {
                // Flash effect
                let flashCount = 0;
                const flashInterval = setInterval(() => {
                    adminBtn.style.backgroundColor = flashCount % 2 === 0 ? '#fbbf24' : '#transparent';
                    flashCount++;
                    if (flashCount >= 6) {
                        clearInterval(flashInterval);
                        adminBtn.style.backgroundColor = '#fbbf24';
                    }
                }, 300);
            }

            // Save state
            localStorage.setItem('adminAccess', adminBtn.style.display === 'block');
        }
    }
});

// Restore admin button state on page load
document.addEventListener('DOMContentLoaded', function() {
    const adminBtn = document.querySelector('.admin-link');
    if (adminBtn && localStorage.getItem('adminAccess') === 'true') {
        adminBtn.style.display = 'block';
    }
});

// Restore admin button state on page load
document.addEventListener('DOMContentLoaded', function() {
    // تحقق من وجود زر الادمن قبل محاولة الوصول إليه
    const adminBtn = document.getElementById('adminControlBtn');
    // فقط إذا كان الزر موجودا وكان وضع الإدارة مفعل، قم بإظهار الزر
    if (adminBtn && localStorage.getItem('adminAccess') === 'true') {
        adminBtn.classList.remove('hidden');
    }
});

// نظام التنبيهات المتقدم
const showAlert = (message, type = 'info', duration = 5000) => {
    const alertContainer = document.querySelector('.alert-container');
    if (!alertContainer) return;

    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    alertContainer.appendChild(alert);

    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => alert.remove(), 150);
    }, duration);
};

// تحسين معالجة الأخطاء في الطلبات
const handleApiError = (error) => {
    console.error('API Error:', error);
    showAlert(error.message || 'حدث خطأ في النظام. يرجى المحاولة مرة أخرى.', 'danger');
};

// تأكيد الإجراءات الخطرة
const confirmAction = (message) => {
    return new Promise((resolve) => {
        if (confirm(message)) {
            resolve(true);
        } else {
            resolve(false);
        }
    });
};

// إغلاق القوس المفقود - إصلاح خطأ "Unexpected end of input"
});