// Polyfill to replace window.pywebview.api and redirect to FastAPI backend

window.pywebview = {
    api: {
        listar_analises: async function() {
            const res = await fetch(`/api/listar_analises`);
            return res.json();
        },
        call: async function(method, payload) {
            const res = await fetch(`/api/call/${method}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ method: method, payload: payload || {} })
            });
            return res.json();
        }
    }
};

// Dispatch the pywebviewready event when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
    // A small timeout ensures all other script parsing is completely finished
    setTimeout(() => {
        window.dispatchEvent(new Event('pywebviewready'));
    }, 100);
});
