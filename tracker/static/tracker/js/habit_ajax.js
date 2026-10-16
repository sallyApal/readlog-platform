document.addEventListener('DOMContentLoaded', function() {
    const habitButtons = document.querySelectorAll('.toggle-habit-btn');

    habitButtons.forEach(button => {
        button.addEventListener('click', function() {
            const habitId = this.getAttribute('data-habit-id');
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            this.disabled = true; // منع التكرار أثناء المعالجة

            fetch('/habits/toggle-ajax/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ habit_id: habitId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    if (data.completed) {
                        this.classList.remove('btn-outline-success');
                        this.classList.add('btn-success');
                        this.innerText = '✓ مكتملة';
                    } else {
                        this.classList.remove('btn-success');
                        this.classList.add('btn-outline-success');
                        this.innerText = 'إنجاز العادة';
                    }
                    // تحديث شريط الإنجاز إن وجد
                    const progressBar = document.getElementById('today-progress');
                    if (progressBar) {
                        progressBar.style.width = data.progress + '%';
                        progressBar.innerText = data.progress + '%';
                    }
                } else {
                    alert('حدث خطأ: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('فشل الاتصال بالخادم!');
            })
            .finally(() => {
                this.disabled = false;
            });
        });
    });
});