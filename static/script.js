console.log("📂 Carregando script.js externo...");

// ==========================================
// 1. INICIALIZAÇÃO DE VARIÁVEIS GLOBAIS
// ==========================================
const socket = io();
let vantaEffect = null;
const synth = window.speechSynthesis; // Acesso direto, sem redeclarar conflitos

// ==========================================
// 2. FUNÇÕES DE AÇÃO (Botões)
// ==========================================

// Enviar Mensagem
window.sendMessage = function() {
    const input = document.getElementById('userMsg');
    const msg = input.value;
    if (!msg.trim()) return;

    // Salva para feedback
    const hiddenInput = document.getElementById('last-user-query');
    if(hiddenInput) hiddenInput.value = msg;

    // UI Imediata
    const chatBox = document.getElementById('chatHistory');
    chatBox.innerHTML += `
        <div class="msg-row user-row">
            <div class="msg user">${msg}</div>
        </div>
    `;
    
    // Envia Socket
    socket.emit('user_message', { 'message': msg });
    
    // Limpeza
    input.value = "";
    chatBox.scrollTop = chatBox.scrollHeight;
};

// Troca Manual de Cérebro
window.manualSwitch = function(brainKey) {
    console.log("🔘 Troca manual solicitada para:", brainKey);
    socket.emit('manual_brain_switch', { 'brain_key': brainKey });
};

// Enviar Feedback (Like/Dislike)
window.sendFeedback = function(score, btn) {
    const parent = btn.parentElement.parentElement;
    const response = parent.dataset.response;
    const query = parent.dataset.query;
    
    // Tenta pegar o nome do cérebro de forma segura
    let brainName = "System";
    const titleEl = document.getElementById('brain-title');
    if(titleEl) brainName = titleEl.innerText.split(' ')[0];

    // Estilo do botão
    if (score === 1) btn.classList.add('clicked');
    else btn.classList.add('clicked-down');

    // Desabilita botões vizinhos
    const siblings = btn.parentElement.querySelectorAll('button');
    siblings.forEach(b => b.disabled = true);

    // Envia API
    fetch('/api/reward', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            brain: brainName,
            query: query,
            response: response,
            score: score
        })
    }).then(() => console.log("Feedback registrado!"));
};

// ==========================================
// 3. LISTENERS DO SOCKET (Reações)
// ==========================================

socket.on('connect', () => {
    console.log("✅ Socket Conectado via script.js");
});

// Troca de Cérebro (Visual)
socket.on('brain_change', (data) => {
    // Atualiza Vanta (se existir)
    if(vantaEffect) vantaEffect.setOptions({ color: data.color });
    
    // Atualiza Textos
    const title = document.getElementById('brain-title');
    const status = document.getElementById('status-line');
    if(title) title.innerText = data.name + " Ativo";
    if(status) status.innerText = "Cérebro: " + data.name;

    // Atualiza CSS Global
    let hexColor = "#" + data.color.toString(16).padStart(6, '0'); // Fix para garantir 6 digitos
    document.documentElement.style.setProperty('--brain-color', hexColor);

    // Atualiza Botões
    document.querySelectorAll('.brain-btn').forEach(btn => {
        btn.style.borderColor = 'rgba(255,255,255,0.2)';
        btn.style.boxShadow = 'none';
    });

    const mapping = { "Architect": "btn-architect", "Strategist": "btn-strategist", "Operator": "btn-operator", "Polymath": "btn-polymath" };
    // Lógica para achar a chave parcial no nome
    const key = Object.keys(mapping).find(k => data.name.includes(k));
    if(key) {
        const btn = document.getElementById(mapping[key]);
        if(btn) {
            btn.style.borderColor = hexColor;
            btn.style.boxShadow = `0 0 15px ${hexColor}`;
        }
    }
});

// Streaming de Texto
socket.on('ai_stream_start', () => {
    const chatBox = document.getElementById('chatHistory');
    chatBox.innerHTML += `<div class="msg-row ai-row"><div class="msg ai" id="temp-msg">...</div></div>`;
    chatBox.scrollTop = chatBox.scrollHeight;
});

socket.on('ai_stream', (data) => {
    const temp = document.getElementById('temp-msg');
    if (temp) {
        if (temp.innerText === "...") temp.innerText = "";
        temp.innerText += data.chunk;
        // Scroll contínuo
        const chatBox = document.getElementById('chatHistory');
        chatBox.scrollTop = chatBox.scrollHeight;
    }
});

socket.on('ai_stream_end', (data) => {
    const temp = document.getElementById('temp-msg');
    if (temp) {
        // Renderiza Markdown (checa se a lib existe)
        if(typeof marked !== 'undefined') temp.innerHTML = marked.parse(temp.innerText);
        if(typeof hljs !== 'undefined') hljs.highlightAll();

        // Adiciona Botões de Feedback
        const feedbackDiv = document.createElement("div");
        feedbackDiv.className = "feedback-actions";
        
        // Proteção contra aspas no HTML
        const queryVal = document.getElementById('last-user-query') ? document.getElementById('last-user-query').value : "";
        
        // Armazena dados no dataset do pai (mais seguro que onclick string)
        temp.parentElement.dataset.response = data.full_text;
        temp.parentElement.dataset.query = queryVal;

        feedbackDiv.innerHTML = `
            <button class="feedback-btn" onclick="sendFeedback(1, this)">👍 Útil</button>
            <button class="feedback-btn" onclick="sendFeedback(-1, this)">👎 Ruim</button>
        `;
        
        temp.parentElement.appendChild(feedbackDiv);
        temp.removeAttribute('id');
    }
});

// Visão Computacional
socket.on('vision_feedback', (data) => {
    const chatBox = document.getElementById('chatHistory');
    chatBox.innerHTML += `
        <div class="msg-row ai-row" style="text-align: center; opacity: 0.8;">
            <div class="msg ai" style="display:inline-block; border: 1px solid yellow; color: yellow;">
                👁️ ${data.msg}
            </div>
        </div>
    `;
    chatBox.scrollTop = chatBox.scrollHeight;
});

// ==========================================
// 4. EVENT LISTENER DO ENTER
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById('userMsg');
    if(input) {
        input.addEventListener("keyup", function(e) {
            if (e.key === "Enter") window.sendMessage();
        });
    }
});