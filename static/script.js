document.addEventListener("DOMContentLoaded", () => {
  const chatMessages = document.getElementById("chatMessages");
  const userInput = document.getElementById("userInput");
  const sendButton = document.getElementById("sendButton");
  const resetButton = document.getElementById("resetButton");

  // Function to add a message to the chat
  function addMessage(content, isUser = false) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${isUser ? "user-message" : "bot-message"}`;

    const messageContent = document.createElement("div");
    messageContent.className = "message-content";
    messageContent.textContent = content;

    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);

    // Auto scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return messageDiv;
  }

  // Function to add a loading message - simplified
  function addLoadingMessage() {
    const messageDiv = document.createElement("div");
    messageDiv.className = "message bot-message";

    const messageContent = document.createElement("div");
    messageContent.className = "message-content";
    messageContent.textContent = "Thinking...";

    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);

    // Auto scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return messageDiv;
  }

  // Function to send a message to the API
  async function sendMessage(message) {
    // Add user message to chat
    addMessage(message, true);

    // Add loading message
    const loadingMessage = addLoadingMessage();

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: message }),
      });

      const data = await response.json();

      // Remove loading message
      chatMessages.removeChild(loadingMessage);

      if (response.ok) {
        // Add bot response to chat
        addMessage(data.response);
      } else {
        // Add error message
        const errorDiv = addMessage(
          `Error: ${data.error || "Something went wrong"}`
        );
        errorDiv.classList.add("error-message");
      }
    } catch (error) {
      // Remove loading message
      chatMessages.removeChild(loadingMessage);

      // Add error message
      const errorDiv = addMessage(`Error: Could not connect to the server`);
      errorDiv.classList.add("error-message");
    }
  }

  // Function to reset conversation
  async function resetConversation() {
    try {
      await fetch("/api/reset", { method: "POST" });

      // Clear chat messages
      chatMessages.innerHTML = "";

      // Add welcome message
      addMessage(
        "Welcome! Ask me questions about the documents in your data directory."
      );
    } catch (error) {
      const errorDiv = addMessage(`Error: Could not reset the conversation`);
      errorDiv.classList.add("error-message");
    }
  }

  // Event listeners
  sendButton.addEventListener("click", () => {
    const message = userInput.value.trim();
    if (message) {
      sendMessage(message);
      userInput.value = "";
    }
  });

  userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      const message = userInput.value.trim();
      if (message) {
        sendMessage(message);
        userInput.value = "";
      }
    }
  });

  resetButton.addEventListener("click", resetConversation);

  // Focus on input field when page loads
  userInput.focus();
});
