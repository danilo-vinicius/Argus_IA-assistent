console.log("📂 [SYSTEM] script.js carregado.");

// ==========================================
// 1. VARIÁVEIS GLOBAIS
// ==========================================
var socket = io();
const synth = window.speechSynthesis;

// ==========================================
// 2. FUNÇÕES DE AÇÃO (Botões)
// ==========================================

// Enviar Mensagem
window.sendMessage = function() {
    const input = document.getElementById('userMsg');
    const msg = input.value;
    if (!msg.trim()) return;

    // Salva para feedback futuro
    const hiddenInput = document.getElementById('last-user-query');
    if(hiddenInput) hiddenInput.value = msg;

    // Adiciona na UI imediatamente (Feedback instantâneo)
    const chatBox = document.getElementById('chatHistory');
    chatBox.innerHTML += `
        <div class="msg user">${msg}</div>
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

// Toggle do Microfone (Placeholder para Fase 4)
window.toggleVoice = function() {
    const btn = document.getElementById('btnMic');
    btn.style.color = 'red';
    alert("Módulo de Voz Contínua será ativado na próxima atualização!");
};

// ==========================================
// 3. LISTENERS DO SOCKET (Reações do Sistema)
// ==========================================

socket.on('connect', () => {
    console.log("✅ [SOCKET] Conectado ao Argus Core.");
});

// --- O CORE DA MUDANÇA DE COR ---
socket.on('brain_change', (data) => {
    console.log("🔄 [SYSTEM] Modulação de Cérebro:", data);

    let rawColor = data.color;
    let colorHex = "#3b82f6"; // Valor padrão (Architect Blue)
    let colorInt = 0x3b82f6;

    // 1. Lógica Híbrida (Aceita String "#FF..." ou Número 1674...)
    if (typeof rawColor === 'string' && rawColor.startsWith('#')) {
        // Se veio como texto (Ex: "#FF0000")
        colorHex = rawColor;
        colorInt = parseInt(colorHex.replace('#', '0x'));
    } else if (typeof rawColor === 'number') {
        // Se veio como número (Ex: 16746496)
        colorInt = rawColor;
        // Converte número para hex string (Ex: "ff0000") e adiciona o #
        colorHex = "#" + rawColor.toString(16).padStart(6, '0');
    }

    console.log(`🎨 Cores Processadas -> Hex: ${colorHex} | Int: ${colorInt}`);

    // 2. Atualiza CSS (Neon e Brilhos)
    document.documentElement.style.setProperty('--accent', colorHex);
    document.documentElement.style.setProperty('--glow', `0 0 10px ${colorHex}4d`);

    // 3. Atualiza Vanta.js (Fundo)
    if (window.vantaEffect) {
        window.vantaEffect.setOptions({
            color: colorInt,
            backgroundColor: 0x050505
        });
    }

    // 4. Atualiza Textos na UI
    const title = document.getElementById('brain-title');
    const status = document.getElementById('status-line');
    
    if(title) {
        title.innerText = data.name;
        title.setAttribute('data-text', data.name);
    }
    if(status) status.innerText = "SYSTEM READY: " + data.name.toUpperCase();

    // 5. Atualiza Botões
    document.querySelectorAll('.brain-btn').forEach(btn => {
        btn.style.borderColor = '#333';
        btn.style.color = '#666';
        btn.style.boxShadow = 'none';
    });

    const mapping = { "Architect": "btn-architect", "Strategist": "btn-strategist", "Operator": "btn-operator", "Polymath": "btn-polymath" };
    const key = Object.keys(mapping).find(k => data.name.includes(k));
    
    if(key) {
        const activeBtn = document.getElementById(mapping[key]);
        if(activeBtn) {
            activeBtn.style.borderColor = colorHex;
            activeBtn.style.color = colorHex;
            activeBtn.style.boxShadow = `0 0 15px ${colorHex}66`;
        }
    }
});

// Streaming de Texto (Efeito Digitação)
socket.on('ai_stream_start', () => {
    const chatBox = document.getElementById('chatHistory');
    // Cria o balão vazio do bot
    chatBox.innerHTML += `<div class="msg bot"><span id="temp-msg" class="typing">...</span></div>`;
    chatBox.scrollTop = chatBox.scrollHeight;
});

socket.on('ai_stream', (data) => {
    const temp = document.getElementById('temp-msg');
    if (temp) {
        // Remove os três pontinhos iniciais na primeira letra
        if (temp.innerText === "...") {
            temp.innerText = "";
            temp.classList.remove("typing");
        }
        temp.innerText += data.chunk;
        
        // Auto-scroll suave
        const chatBox = document.getElementById('chatHistory');
        chatBox.scrollTop = chatBox.scrollHeight;
    }
});

socket.on('ai_stream_end', (data) => {
    const temp = document.getElementById('temp-msg');
    if (temp) {
        // Renderiza Markdown final
        if(typeof marked !== 'undefined') temp.innerHTML = marked.parse(temp.innerText);
        if(typeof hljs !== 'undefined') hljs.highlightAll();
        
        // Remove o ID para que a próxima mensagem crie um novo
        temp.removeAttribute('id');
    }
});

// Visão Computacional (Feedback na UI)
socket.on('status_update', (data) => {
    // Se for mensagem de visão, atualiza o widget lateral
    if (data.msg.includes("👁️")) {
        const gestureStatus = document.getElementById('gesture-status');
        if(gestureStatus) {
            // Extrai a mensagem limpa
            let cleanMsg = data.msg.replace('👁️', '').trim();
            gestureStatus.innerText = cleanMsg.toUpperCase();
            gestureStatus.style.color = 'var(--accent)';
            
            // Efeito de "piscada" no sensor
            const sensorDot = document.querySelector('.rec-dot');
            if(sensorDot) {
                sensorDot.style.backgroundColor = 'var(--accent)';
                setTimeout(() => sensorDot.style.backgroundColor = 'red', 500);
            }
        }
    }
});

// ==========================================
// 5. RECEPÇÃO DE DADOS EM TEMPO REAL
// ==========================================

// Atualiza Barras de CPU e RAM
socket.on('system_stats', (data) => {
    // Atualiza Textos
    const cpuVal = document.querySelector('.sys-stat:nth-child(1) .value');
    const ramVal = document.querySelector('.sys-stat:nth-child(2) .value');
    const cpuBar = document.querySelector('.sys-stat:nth-child(1) .bar-fill');
    const ramBar = document.querySelector('.sys-stat:nth-child(2) .bar-fill');

    if(cpuVal) cpuVal.innerText = data.cpu + "%";
    if(ramVal) ramVal.innerText = data.ram + "%";

    // Atualiza Largura das Barras
    if(cpuBar) cpuBar.style.width = data.cpu + "%";
    if(ramBar) ramBar.style.width = data.ram + "%";

    // Muda cor se estiver crítico (>80%)
    if(data.cpu > 80) cpuBar.style.backgroundColor = 'red';
    else cpuBar.style.backgroundColor = 'var(--accent)';
});

// Recebe o Streaming de Vídeo
socket.on('video_stream', (data) => {
    const imgElement = document.getElementById('live-vision');
    const placeholder = document.getElementById('camera-feed');
    const noSignalText = placeholder.querySelector('.overlay-text');
    const reticle = placeholder.querySelector('.reticle');

    if (imgElement) {
        // Mostra a imagem
        imgElement.style.display = 'block';
        imgElement.src = "data:image/jpeg;base64," + data.image;
        
        // Esconde o texto "NO SIGNAL"
        if(noSignalText) noSignalText.style.display = 'none';
        // Mantém a mira (reticle) por cima
        if(reticle) reticle.style.zIndex = "10";
    }
});

// ==========================================
// 4. EVENT LISTENERS GERAIS
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById('userMsg');
    if(input) {
        input.addEventListener("keyup", function(e) {
            if (e.key === "Enter") window.sendMessage();
        });
    }
});