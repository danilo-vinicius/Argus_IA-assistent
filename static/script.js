// Configuração do Lottie (Cérebro)
var animation = lottie.loadAnimation({
    container: document.getElementById('lottie-brain'),
    renderer: 'svg',
    loop: true,
    autoplay: true,
    path: 'static/brain.json' // Certifique-se de ter um JSON aqui
});

// --- CHAT LOGIC ---
const chatHistory = document.getElementById('chatHistory');
const userMsgInput = document.getElementById('userMsg');
const brainContainer = document.querySelector('.brain-container');

async function sendMessage() {
    let text = userMsgInput.value;
    if (!text) return;

    // UI: Adiciona msg do user
    addMessage(text, 'user');
    userMsgInput.value = '';

    // UI: Esconde o brain para focar no chat (opcional, ou mantém flutuando)
    // brainContainer.style.display = 'none'; 

    // API Call
    try {
        let response = await fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: text})
        });
        let data = await response.json();
        addMessage(data.reply, 'bot');
    } catch (e) {
        addMessage("Erro de conexão.", 'bot');
    }
}

// --- INICIALIZAÇÃO DO SOCKET ---
const socket = io();
let currentBotMessageDiv = null;

// Ao conectar
socket.on('connect', () => {
    console.log("Conectado ao Núcleo Neural.");
});

// Ao receber atualização de status (ex: Troca de Cérebro)
socket.on('status_update', (data) => {
    const statusLine = document.getElementById('status-line');
    if(statusLine) statusLine.innerText = "⚡ " + data.msg;
});

socket.on('ai_stream_start', () => {
    // Cria a div do bot vazia e guarda na variável global
    let chatHistory = document.getElementById('chatHistory');
    let div = document.createElement('div');
    div.className = 'msg bot';
    div.innerHTML = '<span class="typing-indicator">▋</span>'; // Cursor piscando
    chatHistory.appendChild(div);
    
    currentBotMessageDiv = div;
    
    // Scroll para baixo
    document.querySelector('.interaction-area').scrollTop = document.querySelector('.interaction-area').scrollHeight;
    
    // Anima o cérebro
    const brain = document.getElementById('lottie-brain');
    if(brain) brain.style.transform = "scale(1.2)";
});

// 2. Chegada de Pedaço de Texto (Token)
socket.on('ai_stream', (data) => {
    if (currentBotMessageDiv) {
        // Remove o cursor antigo
        let currentHtml = currentBotMessageDiv.innerHTML.replace('<span class="typing-indicator">▋</span>', '');
        
        // Adiciona o novo texto
        // Nota: Marcamos Markdown só no final para não quebrar a formatação no meio
        // Por enquanto, apenas concatenamos texto puro ou HTML simples
        currentBotMessageDiv.innerHTML = currentHtml + data.chunk + '<span class="typing-indicator">▋</span>';
        
        // Auto Scroll suave
        document.querySelector('.interaction-area').scrollTop = document.querySelector('.interaction-area').scrollHeight;
    }
});

// 3. Fim da Resposta (Formata Markdown e Fala)
socket.on('ai_stream_end', () => {
    if (currentBotMessageDiv) {
        // Remove cursor
        let rawText = currentBotMessageDiv.innerText.replace('▋', '');
        
        // Aplica Markdown final (Bonito)
        currentBotMessageDiv.innerHTML = marked.parse(rawText);
        
        // Colore códigos
        currentBotMessageDiv.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
        
        // Fala (Se estiver ativado)
        if (typeof speakText === "function") speakText(rawText);
        
        currentBotMessageDiv = null; // Reseta para a próxima
        
        // Para o cérebro
        const brain = document.getElementById('lottie-brain');
        if(brain) brain.style.transform = "scale(1)";
    }
});

// Ao receber resposta da IA
socket.on('ai_response', (data) => {
    addMessage(data.text, 'bot');
    // Se tiver a função de voz ativa, fala:
    if (typeof speakText === "function") speakText(data.text);
});

// --- FUNÇÕES DE ENVIO ---

function sendMessage() {
    const input = document.getElementById('userMsg');
    const text = input.value;
    if (!text) return;

    // UI: Adiciona mensagem do usuário
    addMessage(text, 'user');
    input.value = '';

    // SOCKET: Envia para o servidor
    socket.emit('user_message', { message: text });
}

function switchBrain(brainKey, btnElement) {
    // Visual: Atualiza botões
    document.querySelectorAll('.brain-btn').forEach(b => b.classList.remove('active'));
    btnElement.classList.add('active');

    // Socket: Avisa o servidor
    socket.emit('switch_brain', { brain: brainKey });
}


// --- MÓDULO DE VOZ (JARVIS VOICE V2) ---

const synth = window.speechSynthesis;
let voiceEnabled = false;

// Carrega as vozes assim que estiverem prontas (Chrome as vezes demora)
let voices = [];
synth.onvoiceschanged = () => {
    voices = synth.getVoices();
    // Debug: Mostra no console (F12) quais vozes você tem
    console.log("Vozes disponíveis:", voices.map(v => v.name));
};

function speakText(text) {
    if (!voiceEnabled || synth.speaking) return;

    // Limpa Markdown (*, #, links) para leitura fluida
    let cleanText = text.replace(/[*#`_]/g, '')
                        .replace(/\[.*?\]/g, '') // Remove links [text]
                        .replace(/\(.*?\)/g, ''); // Remove urls (url)

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = 'pt-BR';
    utterance.rate = 1.2; // Velocidade dinâmica (1.0 a 1.2 é bom)
    utterance.pitch = 1;

    // LÓGICA DE ESCOLHA DE VOZ (PRIORIDADE)
    // 1. Tenta voz do Google (Geralmente a melhor no Chrome)
    // 2. Tenta voz da Microsoft (Edge)
    // 3. Qualquer outra PT-BR
    const preferredVoice = voices.find(v => v.name.includes("Google Português")) || 
                           voices.find(v => v.name.includes("Microsoft")) ||
                           voices.find(v => v.lang.includes("pt-BR"));

    if (preferredVoice) {
        utterance.voice = preferredVoice;
        console.log("Falando com:", preferredVoice.name);
    }

    synth.speak(utterance);
    
    // Animação do cérebro
    const brain = document.getElementById('lottie-brain');
    if(brain) brain.style.transform = "scale(1.1)";
    
    utterance.onend = () => {
        if(brain) brain.style.transform = "scale(1)";
    };
}

// 2. Configuração de RECONHECIMENTO (AUDIÇÃO)
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.lang = 'pt-BR';
    recognition.continuous = false; // Para assim que você para de falar

    recognition.onstart = function() {
        document.getElementById('btnMic').style.color = '#ef4444'; // Fica vermelho gravando
        document.getElementById('userMsg').placeholder = "Ouvindo...";
    };

    recognition.onend = function() {
        document.getElementById('btnMic').style.color = 'var(--accent)';
        document.getElementById('userMsg').placeholder = "Converse com o Jarvis...";
    };

    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        document.getElementById('userMsg').value = transcript;
        sendMessage(); // Envia automaticamente
    };
} else {
    console.log("Seu navegador não suporta reconhecimento de voz nativo.");
    document.getElementById('btnMic').style.display = 'none';
}

// Função do Botão Mic
function toggleVoice() {
    // Se clicar, ativa a leitura de voz para o futuro
    voiceEnabled = true;
    
    if (recognition) {
        recognition.start();
    } else {
        alert("Navegador sem suporte a voz.");
    }
}

function addMessage(text, sender) {
    let div = document.createElement('div');
    div.className = `msg ${sender}`;

    if (sender === 'bot') {
        div.innerHTML = marked.parse(text);
        div.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });

        // --- LINHA NOVA: O JARVIS FALA AQUI ---
        speakText(text); 
        // --------------------------------------

    } else {
        div.innerHTML = text.replace(/\n/g, '<br>');
    }

    chatHistory.appendChild(div);
    // Scroll automático para o final
    document.querySelector('.interaction-area').scrollTop = document.querySelector('.interaction-area').scrollHeight;
}

// Enter para enviar
userMsgInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') sendMessage();
});

// --- MODAL LOGIC ---
const modal = document.getElementById('taskModal');

function openModal() {
    modal.classList.add('active');
    // Foca no input automaticamente
    setTimeout(() => document.getElementById('modalDesc').focus(), 100);
}

function closeModal() {
    modal.classList.remove('active');
}

// Fechar se clicar fora do box (no vidro)
modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
});

// Fechar com ESC
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('active')) closeModal();
});

// --- SALVAR TAREFA ---
async function saveTaskFromModal() {
    const desc = document.getElementById('modalDesc').value;
    const prio = document.getElementById('modalPrio').value;
    let grupo = document.getElementById('modalGrupo').value;
    const prazo = document.getElementById('modalDate').value; // Pegando a data

    if (!grupo.trim()) grupo = "Geral";

    if (!desc) {
        alert("A descrição é obrigatória.");
        return;
    }

    await fetch('/api/add_task', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            descricao: desc, 
            prioridade: prio,
            grupo: grupo,
            prazo: prazo // Enviando data
        })
    });
    
    closeModal();
    location.reload();
}

// Deletar Tarefa
async function deleteTask(id) {
    if(!confirm("Remover este protocolo permanentemente?")) return;

    await fetch('/api/delete_task', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: id})
    });
    location.reload();
}

// Concluir (Já existia, mas reforçando)
async function finishTask(id) {
    await fetch('/api/complete_task', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: id})
    });
    location.reload();
}

// --- SNIPPETS LOGIC ---

async function saveSnippet() {
    let title = document.getElementById('noteTitle').value;
    let code = document.getElementById('noteBody').value;
    let lang = document.getElementById('noteLang').value; // Pega a linguagem
    
    if(title && code) {
        // Reutilizamos a rota add_note, mas passando 'categoria' como a linguagem
        await fetch('/api/add_note', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                titulo: title, 
                conteudo: code,
                categoria: lang // Salva 'python', 'sql', etc na categoria
            })
        });
        location.reload();
    } else {
        alert("Preencha a descrição e o código!");
    }
}

// Função de Copiar
function copyToClipboard(text, btn) {
    navigator.clipboard.writeText(text).then(() => {
        // Feedback visual (Muda ícone rapidinho)
        let original = btn.innerHTML;
        btn.innerHTML = "✅";
        setTimeout(() => { btn.innerHTML = original; }, 1500);
    }).catch(err => {
        console.error('Erro ao copiar:', err);
    });
}

// Inicializar highlight.js nos snippets já carregados
document.addEventListener('DOMContentLoaded', (event) => {
    document.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
});