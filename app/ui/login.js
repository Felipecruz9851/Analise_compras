async function carregarAnalises() {
    const analises = await window.pywebview.api.listar_analises();
    const select = document.getElementById("analise");

    analises.forEach((value) => {
        const option = document.createElement("option");
        option.value = value;
        option.text = value;
        select.appendChild(option);
    });
}

async function executar() {
    const payload = {
        username: document.getElementById("user").value,
        password: document.getElementById("pass").value,
        analise: document.getElementById("analise").value
    };

    const resultado = await window.pywebview.api.rodar_analise(payload);

    document.getElementById("resultado").textContent =
        JSON.stringify(resultado, null, 2);
}

window.addEventListener("DOMContentLoaded", carregarAnalises);