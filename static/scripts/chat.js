let conversationHistory = []; // Armazena todo o histórico
const footer = document.querySelector('footer');

document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('userInput');
    input.focus();
});

async function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    displayMessage('user', message);
    input.value = '';
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                history: conversationHistory
            })
        });
        
        const data = await response.json();
        
        // 1. Mostra primeiro a resposta textual da IA
        displayMessage('ai', data.response);
        
        // 2. Se houver propriedades, mostra como mensagem separada
        if (data.properties && data.properties.length > 0) {
            // Cria um container de mensagem para os imóveis
            const chatBox = document.getElementById('chat-messages');
            const msgDiv = document.createElement('div');
            msgDiv.className = 'ai-message';
            
            // Cria o grid dentro da mensagem
            const grid = document.createElement('div');
            grid.className = 'properties-grid';
            
            // Preenche o grid com os imóveis
            data.properties.forEach(property => {
                const details = property.details.split('\n').filter(item => item.trim() !== '');
                const formattedDetails = details.map(item => {
                    if (item.includes(':')) {
                        const [label, value] = item.split(':');
                        return `<strong>${label.trim()}:</strong> ${value.trim()}`;
                    }
                    return item;
                }).join('<br>');
                
                grid.innerHTML += `
                    <div class="property-card">
                        ${property.image_url ? `<img src="${property.image_url}" class="property-image">` : ''}
                        <div class="property-details">${formattedDetails}</div>
                        <div class="card-buttons">
                        <button onclick="scheduleVisit()">Agendar Visita</button>
                        <button onclick="knowMore()">Ver Detalhes</button>
                        </div>
                    </div>
                `;
            });
            
            msgDiv.appendChild(grid);
            chatBox.appendChild(msgDiv);
        }
        
        conversationHistory = data.history || [];
        
    } catch (error) {
        console.error('Erro:', error);
        displayMessage('ai', 'Desculpe, não entendi muito bem. Pode digitar novamente? 😁');
    } finally {
        // Foca no input novamente após todo o processamento
        input.focus();
    }
}
        

async function fetchImoveis(query) {
    try {
        const response = await fetch(`/api/imoveis?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            data.data.forEach(imovel => {
                displayPropertyCard(imovel);
            });
        }
    } catch (error) {
        console.error('Error fetching properties:', error);
    }
}

function displayMessage(sender, text) {
    const chatBox = document.getElementById('chat-messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = sender === 'user' ? 'user-message' : 'ai-message';
    
    // Substitui \n por <br> e mantém emojis/formatos
    const formattedText = text
        .replace(/\n/g, '<br>')
        .replace(/\*(.*?)\*/g, '<strong>$1</strong>'); // Opcional: transforma *texto* em negrito    
    
    msgDiv.innerHTML = formattedText;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll
    window.scrollTo(0, footer.scrollHeight - 120);
}

function displayPropertyCard(imovel) {
    const chatBox = document.getElementById('chat-messages');
    const card = document.createElement('div');
    card.className = 'property-card';
    card.innerHTML = `
        <h3>${imovel.titulo || 'Imóvel sem título'}</h3>
        <p>${imovel.descricao || ''}</p>
        <p><strong>Preço:</strong> R$ ${imovel.preco || 'N/A'}</p>
        <button onclick="scheduleVisit('${imovel.id}')">Agendar Visita</button>
    `;
    chatBox.appendChild(card);
}

//começa
function scheduleVisit(propertyId) {
  document.getElementById("modalPropertyId").value = propertyId;
  document.getElementById("visitModal").style.display = "flex";
}

function closeModal() {
  document.getElementById("visitModal").style.display = "none";
}

async function submitVisit() {
  const data = {
    propertyId: document.getElementById("modalPropertyId").value,
    name: document.getElementById("visitName").value,
    email: document.getElementById("visitEmail").value,
    phone: document.getElementById("visitPhone").value,
    date: document.getElementById("visitDate").value,
    comment: document.getElementById("visitComment").value,
  };
  console.log(data);

  const res = await fetch("/api/schedule_visit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });

  if (res.ok) {
    alert("Visita agendada com sucesso!");
    closeModal();
  } else {
    alert("Erro ao agendar visita.");
  }
}
//final

// Configura o listener para o evento de tecla no input
document.getElementById('userInput').addEventListener('keydown', function(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault(); // Evita quebra de linha se for Shift+Enter
        sendMessage(); // Chama a função de enviar mensagem
    }
});

// document.getElementById('userInput').addEventListener('focus', function() {
//     const chatMessages = document.getElementById('chat-messages');
//     const containerHeight = document.querySelector('.chat-container').clientHeight;
    
//     if (chatMessages.scrollHeight > containerHeight / 2) {
//         chatMessages.scrollTop = chatMessages.scrollHeight;
//     }
// });

// function displayProperty(property) {
//     const chatBox = document.getElementById('chat-messages');
    
//     // Verifica se já existe um grid ou cria um novo
//     let grid = chatBox.querySelector('.properties-grid');
//     if (!grid) {
//         grid = document.createElement('div');
//         grid.className = 'properties-grid';
//         chatBox.appendChild(grid);
//     }
    
//     const propDiv = document.createElement('div');
//     propDiv.className = 'property-card';
    
//     // Extrai os detalhes formatados
//     const details = property.details.split('\n').filter(item => item.trim() !== '');
//     const formattedDetails = details.map(item => {
//         if (item.includes(':')) {
//             const [label, value] = item.split(':');
//             return `<strong>${label.trim()}:</strong> ${value.trim()}`;
//         }
//         return item;
//     }).join('<br>');
    
//     propDiv.innerHTML = `
//         ${property.image_url ? `<img src="${property.image_url}" class="property-image">` : ''}
//         <div class="property-details">${formattedDetails}</div>
//     `;
    
//     grid.appendChild(propDiv);
//     chatBox.scrollTop = chatBox.scrollHeight;
// }

