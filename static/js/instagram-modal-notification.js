/**
 * عرض إشعار للمستخدم
 */
function showNotification(message) {
  // التحقق من وجود العنصر أو إنشاءه
  let notification = document.getElementById('instagram-modal-notification');
  
  if (!notification) {
    notification = document.createElement('div');
    notification.id = 'instagram-modal-notification';
    notification.style.position = 'fixed';
    notification.style.bottom = '20px';
    notification.style.left = '50%';
    notification.style.transform = 'translateX(-50%)';
    notification.style.backgroundColor = '#4caf50';
    notification.style.color = 'white';
    notification.style.padding = '10px 20px';
    notification.style.borderRadius = '4px';
    notification.style.boxShadow = '0 2px 10px rgba(0,0,0,0.3)';
    notification.style.zIndex = '10000';
    notification.style.transition = 'opacity 0.3s, bottom 0.3s';
    notification.style.opacity = '0';
    notification.style.textAlign = 'center';
    notification.style.fontWeight = 'bold';
    notification.style.fontSize = '14px';
    notification.style.direction = 'rtl';
    document.body.appendChild(notification);
  }
  
  // إضافة الرسالة
  notification.textContent = message;
  
  // إذا كانت رسالة إزالة الإعجاب، نغير اللون
  if (message.includes('إزالة')) {
    notification.style.backgroundColor = '#f44336';
  } else {
    notification.style.backgroundColor = '#4caf50';
  }
  
  // عرض الإشعار
  setTimeout(function() {
    notification.style.opacity = '1';
    notification.style.bottom = '20px';
  }, 10);
  
  // إخفاء الإشعار بعد فترة
  setTimeout(function() {
    notification.style.opacity = '0';
    notification.style.bottom = '10px';
  }, 3000);
}