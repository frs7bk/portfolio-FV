/**
 * نظام طلب الخدمة
 * 
 * يتعامل مع نموذج طلب الخدمة ويرسله باستخدام AJAX
 * ويعرض رسائل النجاح أو الخطأ
 */

$(document).ready(function() {
    // تفعيل حقول الإدخال المخصصة عندما يختار المستخدم الخيار "مخصص"
    $('#budget_select').on('change', function() {
        if ($(this).val() === 'custom') {
            $('#budget').removeClass('hidden').addClass('bg-gray-800/70 backdrop-blur-sm').focus();
            $('#budget').val(''); // تفريغ الحقل
        } else {
            $('#budget').addClass('hidden').removeClass('bg-gray-800/70 backdrop-blur-sm');
            $('#budget').val($(this).val()); // نقل القيمة المحددة إلى حقل الإدخال المخفي
        }
    });
    
    $('#timeline_select').on('change', function() {
        if ($(this).val() === 'custom') {
            $('#timeline').removeClass('hidden').addClass('bg-gray-800/70 backdrop-blur-sm').focus();
            $('#timeline').val(''); // تفريغ الحقل
        } else {
            $('#timeline').addClass('hidden').removeClass('bg-gray-800/70 backdrop-blur-sm');
            $('#timeline').val($(this).val()); // نقل القيمة المحددة إلى حقل الإدخال المخفي
        }
    });
    
    // التعامل مع إرسال نموذج طلب الخدمة
    $('#service-request-form').on('submit', function(e) {
        e.preventDefault();
        
        // إظهار مؤشر التحميل
        const submitBtn = $(this).find('button[type="submit"]');
        const originalBtnText = submitBtn.html();
        submitBtn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> جاري الإرسال...');
        
        // التحقق من القيم المخصصة قبل الإرسال
        if ($('#budget_select').val() === 'custom' && $('#budget').val().trim() === '') {
            showMessage('danger', 'يرجى إدخال الميزانية المتوقعة.');
            submitBtn.prop('disabled', false).html(originalBtnText);
            return;
        }
        
        if ($('#timeline_select').val() === 'custom' && $('#timeline').val().trim() === '') {
            showMessage('danger', 'يرجى إدخال الموعد النهائي المتوقع.');
            submitBtn.prop('disabled', false).html(originalBtnText);
            return;
        }
        
        // جمع البيانات من النموذج
        const formData = new FormData(this);
        
        // إرسال البيانات باستخدام AJAX
        $.ajax({
            url: '/messaging/submit-service-request',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                // إعادة تعيين النموذج وعرض رسالة النجاح
                $('#service-request-form')[0].reset();
                $('#budget').addClass('hidden').removeClass('bg-gray-800/70 backdrop-blur-sm');
                $('#timeline').addClass('hidden').removeClass('bg-gray-800/70 backdrop-blur-sm');
                
                // إظهار رسالة النجاح
                showMessage('success', response.message);
                
                // إعادة زر الإرسال إلى حالته الأصلية
                submitBtn.prop('disabled', false).html(originalBtnText);
                
                // تمرير مكان الرسالة إلى المستخدم
                $('html, body').animate({
                    scrollTop: $('.message-container').offset().top - 100
                }, 500);
            },
            error: function(xhr) {
                // إظهار رسالة الخطأ
                let errorMessage = 'حدث خطأ أثناء إرسال الطلب. يرجى المحاولة مرة أخرى لاحقاً.';
                
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMessage = xhr.responseJSON.error;
                }
                
                showMessage('danger', errorMessage);
                
                // إعادة زر الإرسال إلى حالته الأصلية
                submitBtn.prop('disabled', false).html(originalBtnText);
                
                // تمرير مكان الرسالة إلى المستخدم
                $('html, body').animate({
                    scrollTop: $('.message-container').offset().top - 100
                }, 500);
            }
        });
    });
    
    /**
     * عرض رسالة للمستخدم
     * 
     * @param {string} type نوع الرسالة (success, danger, warning, info)
     * @param {string} message نص الرسالة
     */
    function showMessage(type, message) {
        // إنشاء رسالة بتنسيق مخصص بدلاً من استخدام alert البوتستراب
        const messageHtml = `
            <div class="bg-${type === 'success' ? 'green-500' : 'red-500'} text-white p-4 rounded-lg shadow-md">
                <div class="flex items-center">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} mr-2"></i>
                    <div>${message}</div>
                </div>
            </div>
        `;
        
        // إضافة الرسالة إلى الصفحة
        $('.message-container').html(messageHtml);
        
        // إخفاء الرسالة بعد 5 ثوانٍ
        setTimeout(function() {
            $('.message-container').empty();
        }, 5000);
    }
});