async function carregarAnalises() {
    // Wait for pywebview to be ready
    if (typeof window.pywebview === 'undefined') {
        console.log("Aguardando pywebview...");
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

        console.log("Analises carregadas:", analises);
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
    try {
        const payload = {
            username: document.getElementById("user").value,
            password: document.getElementById("pass").value,
            analise: document.getElementById("analise").value
        };

        const resultado = await window.pywebview.api.rodar_analise(payload);

        document.getElementById("resultado").textContent =
            JSON.stringify(resultado, null, 2);
    } catch (error) {
        document.getElementById("resultado").textContent =
            "Erro ao executar: " + error.message;
    }
}

window.addEventListener("DOMContentLoaded", carregarAnalises);