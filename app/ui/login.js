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

        const resultado = await window.pywebview.api.call("rodar_analise", payload);

        localStorage.setItem("resultadoAnalise", JSON.stringify(resultado));
        window.location.href = "pagina_resultado.html";
        if (resultado && resultado.length > 0) {

            let html = "<table border='1' style='border-collapse:collapse;width:100%'>";

            // Cabeçalho
            html += "<thead><tr>";
            Object.keys(resultado[0]).forEach(coluna => {
                html += `<th style="padding:8px;background:#2f2f2f;color:white">${coluna}</th>`;
            });
            html += "</tr></thead>";

            // Corpo
            html += "<tbody>";
            resultado.forEach(linha => {
                html += "<tr>";
                Object.values(linha).forEach(valor => {
                    html += `<td style="padding:8px">${valor ?? ""}</td>`;
                });
                html += "</tr>";
            });
            html += "</tbody></table>";

            resultadoElem.innerHTML = html;

        } else {
            resultadoElem.textContent = "Nenhum dado retornado.";
        }
    } finally {
        // Remove loading overlay
        loadingOverlay.remove();
    }
}

function formatDateTime(d) {
    if (!d) return '';
    const pad = (n) => String(n).padStart(2, '0');
    const yyyy = d.getFullYear();
    const mm = pad(d.getMonth() + 1);
    const dd = pad(d.getDate());
    const hh = pad(d.getHours());
    const min = pad(d.getMinutes());
    const ss = pad(d.getSeconds());
    return `${yyyy}-${mm}-${dd} ${hh}:${min}:${ss}`;
}

function renderPickles(lista) {
    const container = document.getElementById('pickles-container');
    if (!container) return;

    if (!lista || lista.length === 0) {
        container.innerHTML = `<div id="pickles-empty" style="opacity:0.85; font-size:12px;">Nenhum arquivo <b>snapshot_*.pkl</b> encontrado.</div>`;
        return;
    }

    let html = `
        <div style="font-size:12px; margin-bottom:10px; color:#333;">Arquivos pickle encontrados: <b>${lista.length}</b></div>
        <div class="table-wrapper" style="max-height: 240px; overflow: auto; border: 1px solid #e0e0e0; border-radius: 12px;">
          <table style="width:100%; border-collapse: collapse; font-size: 12px;">
            <thead>
              <tr>
                <th style="position: sticky; top: 0; background: linear-gradient(135deg, #2e8b57 0%, #3cb371 100%); color: white; padding: 10px;">Nome</th>
                <th style="position: sticky; top: 0; background: linear-gradient(135deg, #2e8b57 0%, #3cb371 100%); color: white; padding: 10px;">Criação</th>
              </tr>
            </thead>
            <tbody>
    `;

    for (const item of lista) {
        html += `
          <tr>
            <td style="padding:10px; border-bottom: 1px solid #e0e0e0; word-break: break-word;">${item.nome || ''}</td>
            <td style="padding:10px; border-bottom: 1px solid #e0e0e0; font-family: Consolas, Monaco, monospace;">${item.data_criacao || ''}</td>
          </tr>
        `;
    }

    html += `
            </tbody>
          </table>
        </div>
    `;

    container.innerHTML = html;
}

async function listarPickles() {
    try {
        const lista = await window.pywebview.api.call('listar_pickles', {});
        if (lista && lista.erro) throw new Error(lista.erro);
        renderPickles(lista || []);
    } catch (e) {
        const container = document.getElementById('pickles-container');
        if (container) container.innerHTML = `<div style="color:#b00020; font-size:12px;">Erro ao listar pickles: ${e.message || e}</div>`;
    }
}

async function gerarPickles() {
    const loadingOverlay = document.createElement('div');
    loadingOverlay.id = 'loading-overlay';
    loadingOverlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);display:flex;flex-direction:column;justify-content:center;align-items:center;z-index:9999;';
    loadingOverlay.innerHTML = '<div style="width:50px;height:50px;border:5px solid rgba(255,255,255,0.3);border-top:5px solid #3cb371;border-radius:50%;animation:spin 1s linear infinite;"></div><p style="color:white;margin-top:20px;font-size:18px;">Gerando arquivos pickle...</p><style>@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}</style>';
    document.body.appendChild(loadingOverlay);

    try {
        const resp = await window.pywebview.api.call('gerar_pickles', {});
        if (resp && resp.erro) throw new Error(resp.erro);
        await listarPickles();
    } catch (e) {
        const container = document.getElementById('pickles-container');
        if (container) container.innerHTML = `<div style="color:#b00020; font-size:12px;">Erro ao gerar pickles: ${e.message || e}</div>`;
    } finally {
        loadingOverlay.remove();
    }
}

window.addEventListener("DOMContentLoaded", async () => {
    await carregarAnalises();
    await listarPickles();
});

