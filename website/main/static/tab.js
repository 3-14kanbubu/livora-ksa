// tabs.js

function initializeMedicalHistoryForm() {
    const editAllBtn = document.getElementById("editAllBtn");
    const form = document.getElementById("medicalForm");
    console.log("editAllBtn:", editAllBtn);
    console.log("form:", form);
    if (!editAllBtn || !form) {
        console.error("form or edit undetected");
        return;
    }

    let formEditing = false;

    toggleFormInputs(false);
    editAllBtn.textContent = "Edit";
    editAllBtn.classList.remove("bg-blue-500", "text-white");
    editAllBtn.classList.add("bg-gray-300", "text-black");

    editAllBtn.onclick = async () => {
        formEditing = !formEditing;

        if (formEditing) {
            toggleFormInputs(true);
            editAllBtn.textContent = "Save";
            editAllBtn.classList.remove("bg-gray-300", "text-black");
            editAllBtn.classList.add("bg-blue-500", "text-white");
        } else {
            toggleFormInputs(true);
            await submitMedicalHistoryForm(form);
            toggleFormInputs(false);
            editAllBtn.textContent = "Edit";
            editAllBtn.classList.remove("bg-blue-500", "text-white");
            editAllBtn.classList.add("bg-gray-300", "text-black");
        }
    };

    function toggleFormInputs(enable) {
        const elements = form.querySelectorAll("input, textarea, select");
        elements.forEach(el => {
            el.disabled = !enable;
        });
    }

    async function submitMedicalHistoryForm(form) {
        const formData = new FormData(form);
        for (let [key, value] of formData.entries()) {
            console.log(`${key}: ${value}`);
        }

        try {
            const response = await fetch(form.action, {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: formData
            });

            if (!response.ok) {
                console.error("Server returned an error status:", response.status);
                alert("Error");
                return;
            }

            const data = await response.json();
            console.log("✅ Success:", data);
            alert("Saved");
        } catch (err) {
            console.error("Submission error:", err);
            alert("submission error");
        }
    }
}

window.initializeMedicalHistoryForm = initializeMedicalHistoryForm;

function changeTab(tab) {
    const tabMap = {
        'main': 'main_std',
        'medical': 'med_his_std',
        'history': 'rqst_his_std'
    };

    const component = tabMap[tab];
    if (!component) return;

    document.querySelectorAll('.tab-menu a').forEach(link => {
        link.classList.remove('active');
    });
    document.getElementById(`${tab}-tab`).classList.add('active');

    fetch(`/ruser-comp/${component}`)
        .then(response => response.text())
        .then(html => {
            const container = document.getElementById('main-area');
            container.innerHTML = html;
            const scripts = container.getElementsByTagName('script');
            Array.from(scripts).forEach(oldScript => {
                const newScript = document.createElement('script');
                Array.from(oldScript.attributes).forEach(attr => {
                    newScript.setAttribute(attr.name, attr.value);
                });
                newScript.textContent = oldScript.textContent;
                oldScript.parentNode.replaceChild(newScript, oldScript);
            });

            if (component === 'med_his_std') {
                setTimeout(() => {
                    initializeMedicalHistoryForm();
                }, 0);
            }
            localStorage.setItem('selectedTab', tab);
        });
}
document.addEventListener('DOMContentLoaded', () => {
    loadSymptomComponent(); 
    const savedTab = localStorage.getItem('selectedTab') || 'main';
    changeTab(savedTab);
});
