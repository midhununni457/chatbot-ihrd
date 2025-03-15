// Connect to WebSocket server
let socket;
const chatMessages = document.getElementById("chatMessages");
const userInput = document.getElementById("userInput");
const chatForm = document.getElementById("chatForm");
const connectionStatus = document.getElementById("connectionStatus");
const reconnectButton = document.getElementById("reconnectButton");

// Function to connect to WebSocket
function connectWebSocket() {
  // Close any existing connection
  if (socket) {
    socket.close();
  }

  // Update status
  connectionStatus.textContent = "Connecting...";
  connectionStatus.style.color = "#f0ad4e"; // Warning color

  // Get the current hostname for WebSocket connection
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.hostname}:8765`;

  // Create new WebSocket connection
  try {
    socket = new WebSocket(wsUrl);

    // WebSocket event listeners
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

// Initial connection
connectWebSocket();

// Reconnect button handler
if (reconnectButton) {
  reconnectButton.addEventListener("click", function () {
    connectWebSocket();
  });
}

// Form submission handler
chatForm.addEventListener("submit", function (e) {
  e.preventDefault();
  const message = userInput.value.trim();

  if (message) {
    displayUserMessage(message);

    // Check if socket is connected before sending
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(message);
    } else {
      displayBotMessage(
        "I'm currently disconnected from the server. Please wait while I reconnect..."
      );
      // Try to reconnect
      connectWebSocket();
    }

    userInput.value = "";
  }
});

// Display user message
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

// Display bot message
function displayBotMessage(message) {
  const messageDiv = document.createElement("div");
  messageDiv.className = "message bot-message";

  const contentDiv = document.createElement("div");
  contentDiv.className = "message-content";

  // Format the message to handle line breaks and lists
  const formattedMessage = message.replace(/\n-/g, "<br>-");

  const paragraph = document.createElement("p");
  paragraph.innerHTML = formattedMessage.replace(/\n/g, "<br>");

  contentDiv.appendChild(paragraph);
  messageDiv.appendChild(contentDiv);
  chatMessages.appendChild(messageDiv);

  scrollToBottom();
}

// Scroll chat to bottom
function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}
