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

    // --- COMANDO SECRETO DO NOTION ---
    if (msg.toLowerCase() === '/notion' || msg.toLowerCase().includes('verificar tarefas')) {
        // Mostra no chat que você pediu
        const chatBox = document.getElementById('chatHistory');
        chatBox.innerHTML += `<div class="msg user">${msg}</div>`;
        
        // Dispara o evento Python direto
        console.log("🧠 Disparando Check de Tarefas...");
        socket.emit('check_tasks', {});
    };

        
        input.value = "";
        return; // Para aqui, não manda pro LLM normal

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

    // 1. Lógica Híbrida (Aceita "#FF...", "0xFF..." ou Número)
    if (typeof rawColor === 'string') {
        if (rawColor.startsWith('#')) {
            // Veio como CSS "#ff0000"
            colorHex = rawColor;
            colorInt = parseInt(colorHex.replace('#', '0x'));
        } 
        else if (rawColor.startsWith('0x')) {
            // --- AQUI ESTAVA O PROBLEMA ---
            // Veio como JSON "0xff0000"
            colorHex = rawColor.replace('0x', '#'); // Transforma em #ff0000 para o CSS
            colorInt = parseInt(rawColor);          // O parseInt entende string "0x..." nativamente
        }
    } 
    else if (typeof rawColor === 'number') {
        // Veio como número (Ex: 16746496)
        colorInt = rawColor;
        // Converte número para hex string e adiciona o #
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
// 6. CONTROLE DO MÓDULO DE VISÃO
// ==========================================

function toggleVisionModule() {
    const checkbox = document.getElementById('vision-toggle');
    const action = checkbox.checked ? 'start' : 'stop';
    
    console.log(`🔌 Enviando comando de visão: ${action.toUpperCase()}`);
    socket.emit('toggle_vision', { 'action': action });
    
    // Se desligou, limpa a tela imediatamente
    if (action === 'stop') {
        const img = document.getElementById('live-vision');
        const text = document.querySelector('.overlay-text');
        if(img) img.style.display = 'none';
        if(text) {
            text.style.display = 'block';
            text.innerText = "SYSTEM OFFLINE";
        }
    }
}

// Confirmação do Servidor (Para garantir que ligou mesmo)
socket.on('vision_status', (data) => {
    const checkbox = document.getElementById('vision-toggle');
    const text = document.querySelector('.overlay-text');
    const img = document.getElementById('live-vision'); // <--- Pegamos o elemento da imagem

    if (data.status === 'online') {
        checkbox.checked = true;
        if(text) {
            text.style.display = 'block';
            text.innerText = "INITIALIZING...";
        }
    } else {
        // --- LÓGICA DE DESLIGAMENTO ---
        checkbox.checked = false;
        
        // 1. Mostra o texto "SYSTEM OFFLINE"
        if(text) {
            text.style.display = 'block'; 
            text.innerText = "SYSTEM OFFLINE";
            text.style.color = "#666"; // Volta cor cinza original
        }

        // 2. Esconde a imagem congelada
        if(img) {
            img.style.display = 'none';
            img.src = ""; // Limpa o buffer da imagem
        }
    }
});

// ==========================================
// 7. CONTROLE DE ÁUDIO (Ouvidos e Voz)
// ==========================================

// --- OUVIDOS (Microfone) ---
function toggleEars() {
    const checkbox = document.getElementById('ears-toggle');
    const action = checkbox.checked ? 'start' : 'stop';
    console.log(`👂 Enviando comando ouvidos: ${action}`);
    socket.emit('toggle_ears', { 'action': action });
}

socket.on('ears_status', (data) => {
    const checkbox = document.getElementById('ears-toggle');
    const statusText = document.getElementById('mic-status');
    
    if (data.status === 'online') {
        checkbox.checked = true;
        statusText.innerText = "MIC: LISTENING";
        statusText.style.color = "var(--accent)";
    } else {
        checkbox.checked = false;
        statusText.innerText = "MIC: OFFLINE";
        statusText.style.color = "#666";
    }
});

// --- VOZ (Sintetizador) ---
function toggleVoice() {
    const checkbox = document.getElementById('voice-toggle');
    const action = checkbox.checked ? 'start' : 'stop';
    console.log(`🗣️ Enviando comando voz: ${action}`);
    socket.emit('toggle_voice', { 'action': action });
}

socket.on('voice_status', (data) => {
    const checkbox = document.getElementById('voice-toggle');
    const statusText = document.getElementById('voice-status');
    
    if (data.status === 'online') {
        checkbox.checked = true;
        statusText.innerText = "VOICE: ACTIVE";
        statusText.style.color = "var(--accent)";
    } else {
        checkbox.checked = false;
        statusText.innerText = "VOICE: MUTED";
        statusText.style.color = "#666";
    }
});

// ==========================================
// 8. SINCRONIA DE CHAT (Espelho de Voz)
// ==========================================

socket.on('mirror_user_message', (data) => {
    const chatBox = document.getElementById('chatHistory');
    
    // Cria o balão do usuário (igual quando você digita)
    chatBox.innerHTML += `
        <div class="msg user">${data.message} <span style="font-size:0.7em">🎤</span></div>
    `;
    
    // Rola para baixo
    chatBox.scrollTop = chatBox.scrollHeight;
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