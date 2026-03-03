async function carregarAnalises() {
    // Wait for pywebview to be ready
    if (typeof window.pywebview === 'undefined') {
        await new Promise(resolve => setTimeout(resolve, 500));
    }

    try {
        const analises = await window.pywebview.api.listar_analises();
        const select = document.getElementById("analise");

        analises.forEach((value) => {
            const option = document.createElement("option");
            option.value = value;
            option.text = value;
            select.appendChild(option);
        });
    } catch (error) {
        console.error("Erro ao carregar analises:", error);
        // Fallback: populate with default values
        const select = document.getElementById("analise");
        const defaultAnalises = ["Compra para estoque", "compra por necessidade", "rev", "lam"];
        defaultAnalises.forEach((value) => {
            const option = document.createElement("option");
            option.value = value;
            option.text = value;
            select.appendChild(option);
        });
    }
}

async function executar() {
    // Show loading overlay
    const loadingOverlay = document.createElement('div');
    loadingOverlay.id = 'loading-overlay';
    loadingOverlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);display:flex;flex-direction:column;justify-content:center;align-items:center;z-index:9999;';
    loadingOverlay.innerHTML = '<div style="width:50px;height:50px;border:5px solid rgba(255,255,255,0.3);border-top:5px solid #3cb371;border-radius:50%;animation:spin 1s linear infinite;"></div><p style="color:white;margin-top:20px;font-size:18px;">Executando análise...</p><style>@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}</style>';
    document.body.appendChild(loadingOverlay);

    try {
        const payload = {
            username: document.getElementById("user").value,
            password: document.getElementById("pass").value,
            analise: document.getElementById("analise").value
        };

        const resultado = await window.pywebview.api.rodar_analise(payload);

        const resultadoElem = document.getElementById("resultado");
        if (resultadoElem) {
            resultadoElem.textContent = JSON.stringify(resultado, null, 2);
        }

        // Wait 5 seconds before removing overlay
        await new Promise(resolve => setTimeout(resolve, 5000));

    } catch (error) {
        const resultadoElem = document.getElementById("resultado");
        if (resultadoElem) {
            resultadoElem.textContent = "Erro ao executar: " + error.message;
        }
    } finally {
        // Remove loading overlay
        loadingOverlay.remove();
    }
}

window.addEventListener("DOMContentLoaded", carregarAnalises);
