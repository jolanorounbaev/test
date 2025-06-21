document.addEventListener('DOMContentLoaded', function () {
    ['id_latitude', 'id_longitude'].forEach(id => {
        const field = document.getElementById(id);
        if (field) {
            const btn = document.createElement('button');
            btn.innerText = 'Clear';
            btn.type = 'button';
            btn.style.marginLeft = '8px';
            btn.onclick = () => field.value = '';
            field.parentElement.appendChild(btn);
        }
    });
});
