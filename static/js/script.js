let socket;
const chatMessages = document.getElementById("chatMessages");
const userInput = document.getElementById("userInput");
const chatForm = document.getElementById("chatForm");
const connectionStatus = document.getElementById("connectionStatus");
const reconnectButton = document.getElementById("reconnectButton");

function connectWebSocket() {
  if (socket) {
    socket.close();
  }

  connectionStatus.textContent = "Connecting...";
  connectionStatus.style.color = "#f0ad4e";

  const isSecure = window.location.protocol === "https:";
  const wsProtocol = isSecure ? "wss:" : "ws:";

  let wsUrl;

  if (
    window.location.hostname.includes("herokuapp.com") ||
    window.location.hostname.includes("onrender.com")
  ) {
    wsUrl = `${wsProtocol}//${window.location.host}`;
  } else {
    const wsPort = window.location.port || (isSecure ? "443" : "80");
    wsUrl = `${wsProtocol}//${window.location.hostname}:${wsPort}`;
  }

  try {
    socket = new WebSocket(wsUrl);

    socket.onopen = function (event) {
      connectionStatus.textContent = "Connected";
      connectionStatus.style.color = "#28a745";
      reconnectButton.style.display = "none";
    };

    socket.onclose = function (event) {
      connectionStatus.textContent = "Disconnected";
      connectionStatus.style.color = "#dc3545";
      reconnectButton.style.display = "inline-block";
    };

    socket.onerror = function (error) {
      connectionStatus.textContent = "Error connecting to server";
      connectionStatus.style.color = "#dc3545";
      reconnectButton.style.display = "inline-block";
    };

    socket.onmessage = function (event) {
      try {
        const response = JSON.parse(event.data);
        displayBotMessage(response.response);
      } catch (error) {
        displayBotMessage(
          "Sorry, I encountered an error processing your request."
        );
      }
    };
  } catch (error) {
    connectionStatus.textContent = "Error connecting to server";
    connectionStatus.style.color = "#dc3545";
    reconnectButton.style.display = "inline-block";
  }
}

connectWebSocket();

if (reconnectButton) {
  reconnectButton.addEventListener("click", function () {
    connectWebSocket();
  });
}

chatForm.addEventListener("submit", function (e) {
  e.preventDefault();
  const message = userInput.value.trim();

  if (message) {
    displayUserMessage(message);

    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(message);
    } else {
      displayBotMessage(
        "I'm currently disconnected from the server. Please wait while I reconnect..."
      );
      connectWebSocket();
    }

    userInput.value = "";
  }
});

function displayUserMessage(message) {
  const messageDiv = document.createElement("div");
  messageDiv.className = "message user-message";

  const contentDiv = document.createElement("div");
  contentDiv.className = "message-content";

  const paragraph = document.createElement("p");
  paragraph.textContent = message;

  contentDiv.appendChild(paragraph);
  messageDiv.appendChild(contentDiv);
  chatMessages.appendChild(messageDiv);

  scrollToBottom();
}

function displayBotMessage(message) {
  const messageDiv = document.createElement("div");
  messageDiv.className = "message bot-message";

  const contentDiv = document.createElement("div");
  contentDiv.className = "message-content";

  const formattedMessage = message.replace(/\n-/g, "<br>-");

  const paragraph = document.createElement("p");
  paragraph.innerHTML = formattedMessage.replace(/\n/g, "<br>");

  contentDiv.appendChild(paragraph);
  messageDiv.appendChild(contentDiv);
  chatMessages.appendChild(messageDiv);

  scrollToBottom();
}

function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}
