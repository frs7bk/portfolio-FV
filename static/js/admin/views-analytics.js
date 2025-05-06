/**
 * محلل المشاهدات المتقدم
 * تفاعلات وتحليلات للمستخدم على لوحة تحكم المشاهدات المتطورة
 */

document.addEventListener('DOMContentLoaded', function() {
    // تهيئة التبديل بين الرسوم البيانية
    setupTabSwitching();
    
    // تهيئة فلترة التقارير
    setupReportFilters();
    
    // تهيئة إظهار تفاصيل المشروع عند النقر
    setupProjectDetails();
    
    // تنفيذ تحديثات متزامنة للإحصائيات
    setupLiveUpdates();
});

/**
 * تهيئة التبديل بين علامات التبويب للرسوم البيانية المختلفة
 */
function setupTabSwitching() {
    const tabs = document.querySelectorAll('.analytics-tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // إزالة الفئة النشطة من جميع علامات التبويب
            tabs.forEach(t => t.classList.remove('active'));
            
            // إخفاء جميع محتويات علامات التبويب
            tabContents.forEach(content => content.classList.remove('active'));
            
            // إضافة الفئة النشطة للعلامة المحددة
            this.classList.add('active');
            
            // عرض المحتوى المقابل
            const target = this.getAttribute('data-target');
            document.getElementById(target).classList.add('active');
        });
    });
}

/**
 * تهيئة فلاتر التقارير للمدة والمشروع
 */
function setupReportFilters() {
    const dateRangeSelect = document.getElementById('date-range');
    const portfolioSelect = document.getElementById('portfolio-filter');
    
    if (dateRangeSelect && portfolioSelect) {
        // استدعاء التحديث عند تغيير الفلتر
        dateRangeSelect.addEventListener('change', updateAnalytics);
        portfolioSelect.addEventListener('change', updateAnalytics);
    }
    
    // إضافة زر لتحديث البيانات يدويًا
    const refreshButton = document.getElementById('refresh-data');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            showLoadingSpinner();
            updateAnalytics(true);
        });
    }
}

/**
 * تحديث إحصائيات التحليل بناءً على الفلاتر المحددة
 * @param {boolean} forceUpdate - تحديث قسري للبيانات
 */
function updateAnalytics(forceUpdate = false) {
    const days = document.getElementById('date-range').value;
    const portfolioId = document.getElementById('portfolio-filter').value;
    
    // إعداد عنوان URL
    let url = `/admin/analytics/views?days=${days}`;
    if (portfolioId && portfolioId !== 'all') {
        url += `&portfolio_id=${portfolioId}`;
    }
    
    // إضافة معلمة التحديث القسري
    if (forceUpdate) {
        url += `&force_update=true`;
    }
    
    // الانتقال إلى عنوان URL الجديد
    window.location.href = url;
}

/**
 * تهيئة عرض تفاصيل المشروع عند النقر على صف في الجدول
 */
function setupProjectDetails() {
    const tableRows = document.querySelectorAll('.views-details-table tbody tr');
    
    tableRows.forEach(row => {
        row.addEventListener('click', function() {
            const projectId = this.getAttribute('data-id');
            if (projectId) {
                showProjectDetails(projectId);
            }
        });
    });
}

/**
 * عرض تفاصيل المشروع في نافذة منبثقة
 * @param {string} projectId - معرف المشروع
 */
function showProjectDetails(projectId) {
    // طلب بيانات المشروع من الخادم
    fetch(`/admin/analytics/project/${projectId}/details`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // عرض البيانات في مودال
                showProjectModal(data.project);
            } else {
                showNotification('خطأ في الحصول على بيانات المشروع', 'error');
            }
        })
        .catch(error => {
            console.error('خطأ في طلب بيانات المشروع:', error);
            showNotification('خطأ في الاتصال بالخادم', 'error');
        });
}

/**
 * عرض نافذة منبثقة بتفاصيل المشروع والإحصائيات المتقدمة
 * @param {Object} project - بيانات المشروع
 */
function showProjectModal(project) {
    // إنشاء المودال وتعبئته بالبيانات
    const modal = document.createElement('div');
    modal.className = 'project-details-modal';
    
    modal.innerHTML = `
        <div class="modal-content">
            <span class="close-modal">&times;</span>
            <h2>${project.title}</h2>
            
            <div class="project-stats">
                <div class="stat-item">
                    <span class="stat-value">${project.total_views}</span>
                    <span class="stat-label">إجمالي المشاهدات</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${project.unique_visitors}</span>
                    <span class="stat-label">زوار فريدون</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${project.avg_duration}ث</span>
                    <span class="stat-label">متوسط مدة المشاهدة</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${project.engagement_score}%</span>
                    <span class="stat-label">نسبة التفاعل</span>
                </div>
            </div>
            
            <div class="project-details-charts">
                <canvas id="projectViewsChart"></canvas>
                <canvas id="projectDevicesChart"></canvas>
            </div>
            
            <div class="project-interactions">
                <h3>تفاعلات المستخدمين</h3>
                <table class="interaction-table">
                    <thead>
                        <tr>
                            <th>التاريخ</th>
                            <th>المدة</th>
                            <th>الجهاز</th>
                            <th>الموقع</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${project.interactions.map(interaction => `
                            <tr>
                                <td>${formatDate(interaction.date)}</td>
                                <td>${interaction.duration}ث</td>
                                <td>${interaction.device}</td>
                                <td>${interaction.location || 'غير معروف'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    // إضافة المودال إلى الصفحة
    document.body.appendChild(modal);
    
    // إضافة حدث الإغلاق للمودال
    const closeButton = modal.querySelector('.close-modal');
    closeButton.addEventListener('click', function() {
        document.body.removeChild(modal);
    });
    
    // رسم مخططات المشروع
    drawProjectCharts(project);
}

/**
 * رسم المخططات البيانية لتفاصيل المشروع
 * @param {Object} project - بيانات المشروع
 */
function drawProjectCharts(project) {
    // مخطط المشاهدات حسب اليوم
    const viewsCtx = document.getElementById('projectViewsChart').getContext('2d');
    new Chart(viewsCtx, {
        type: 'line',
        data: {
            labels: project.daily_views.map(item => item.date),
            datasets: [{
                label: 'المشاهدات اليومية',
                data: project.daily_views.map(item => item.count),
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 2,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
    
    // مخطط توزيع الأجهزة
    const devicesCtx = document.getElementById('projectDevicesChart').getContext('2d');
    new Chart(devicesCtx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(project.devices),
            datasets: [{
                data: Object.values(project.devices),
                backgroundColor: [
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(255, 206, 86, 0.8)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true
        }
    });
}

/**
 * تنسيق التاريخ بشكل مناسب للعرض
 * @param {string} dateString - سلسلة التاريخ
 * @returns {string} - التاريخ المنسق
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
}

/**
 * عرض إشعار للمستخدم
 * @param {string} message - رسالة الإشعار
 * @param {string} type - نوع الإشعار (success, error, warning)
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // إظهار الإشعار
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // إخفاء الإشعار بعد 3 ثوانٍ
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

/**
 * إظهار مؤشر التحميل أثناء تحديث البيانات
 */
function showLoadingSpinner() {
    const spinner = document.createElement('div');
    spinner.className = 'loading-spinner';
    spinner.innerHTML = `
        <div class="spinner-container">
            <div class="spinner"></div>
            <p>جاري تحديث البيانات...</p>
        </div>
    `;
    
    document.body.appendChild(spinner);
}

/**
 * تهيئة التحديثات الحية للإحصائيات
 */
function setupLiveUpdates() {
    // تحديث البيانات كل 5 دقائق
    setInterval(() => {
        // تحديث الإحصائيات دون إعادة تحميل الصفحة كاملة
        fetchLiveStats();
    }, 5 * 60 * 1000);
}

/**
 * جلب الإحصائيات المحدثة من الخادم
 */
function fetchLiveStats() {
    const days = document.getElementById('date-range').value;
    const portfolioId = document.getElementById('portfolio-filter').value;
    
    fetch(`/admin/analytics/views/live-update?days=${days}&portfolio_id=${portfolioId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // تحديث الإحصائيات على الصفحة
                updateStatsDisplay(data.stats);
            }
        })
        .catch(error => {
            console.error('خطأ في تحديث الإحصائيات الحية:', error);
        });
}

/**
 * تحديث عرض الإحصائيات على الصفحة
 * @param {Object} stats - البيانات الإحصائية الجديدة
 */
function updateStatsDisplay(stats) {
    // تحديث الإحصائيات الرئيسية
    document.getElementById('total-views').textContent = stats.total_views;
    document.getElementById('unique-views').textContent = stats.unique_views;
    document.getElementById('returning-views').textContent = stats.returning_views;
    document.getElementById('avg-duration').textContent = `${stats.avg_duration}ث`;
    document.getElementById('bounce-rate').textContent = `${stats.bounce_rate}%`;
    
    // تحديث آخر وقت تحديث
    document.getElementById('last-update-time').textContent = new Date().toLocaleTimeString();
}