document.addEventListener("DOMContentLoaded", function () {
  const userInput = document.getElementById("userInput");
  const sendButton = document.getElementById("sendButton");
  const resetButton = document.getElementById("resetButton");
  const reloadKbButton = document.getElementById("reloadKbButton");
  const chatMessages = document.getElementById("chatMessages");
  const statusIndicator = document.getElementById("statusIndicator");
  const statusText = document.getElementById("statusText");

  // Function to add a message to the chat interface
  function addMessage(content, isUser = false, isSystem = false) {
    const messageDiv = document.createElement("div");

    if (isSystem) {
      messageDiv.className = "system-message";
      messageDiv.textContent = content;
    } else {
      messageDiv.className = `message ${
        isUser ? "user-message" : "bot-message"
      }`;
      const messageContent = document.createElement("div");
      messageContent.className = "message-content";
      messageContent.textContent = content;
      messageDiv.appendChild(messageContent);
    }

    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // Function to display loading indicator
  function showLoading() {
    const loadingDiv = document.createElement("div");
    loadingDiv.className = "message bot-message loading";
    loadingDiv.id = "loadingMessage";

    const loadingContent = document.createElement("div");
    loadingContent.className = "message-content";
    loadingContent.innerHTML = 'Thinking<span class="loading-dots"></span>';

    loadingDiv.appendChild(loadingContent);
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // Function to remove loading indicator
  function hideLoading() {
    const loadingMessage = document.getElementById("loadingMessage");
    if (loadingMessage) {
      loadingMessage.remove();
    }
  }

  // Function to send message to server
  async function sendMessage(message) {
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: message }),
      });

      const data = await response.json();

      hideLoading();

      if (data.error) {
        addMessage(`Error: ${data.error}`);
      } else {
        addMessage(data.response);
      }
    } catch (error) {
      hideLoading();
      addMessage(
        `An error occurred while connecting to the server. Please try again.`
      );
      console.error("Error:", error);
    }
  }

  // Handle send button click
  sendButton.addEventListener("click", function () {
    const message = userInput.value.trim();
    if (message) {
      // Add user message to chat
      addMessage(message, true);

      // Clear input
      userInput.value = "";

      // Show loading indicator
      showLoading();

      // Send message to server
      sendMessage(message);
    }
  });

  // Handle Enter key press
  userInput.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
      sendButton.click();
      e.preventDefault();
    }
  });

  // Handle reset button click
  resetButton.addEventListener("click", function () {
    fetch("/api/reset", { method: "POST" })
      .then((response) => response.json())
      .then((data) => {
        // Clear chat messages except the welcome message
        while (chatMessages.children.length > 1) {
          chatMessages.removeChild(chatMessages.lastChild);
        }
        // Add system message confirming reset
        addMessage("Conversation has been reset.", false, true);
      })
      .catch((error) => {
        console.error("Error resetting conversation:", error);
      });
  });

  // Handle reload KB button click
  reloadKbButton.addEventListener("click", function () {
    // Change button text to show loading
    reloadKbButton.textContent = "Reloading...";
    reloadKbButton.disabled = true;

    // Add system message
    addMessage("Reloading knowledge base...", false, true);

    fetch("/api/reload", { method: "POST" })
      .then((response) => response.json())
      .then((data) => {
        if (data.status) {
          addMessage(data.status, false, true);
          // Update KB status
          checkKbStatus();
        } else if (data.error) {
          addMessage(`Error: ${data.error}`, false, true);
        }

        // Reset button
        reloadKbButton.textContent = "Reload KB";
        reloadKbButton.disabled = false;
      })
      .catch((error) => {
        console.error("Error reloading knowledge base:", error);
        addMessage("Failed to reload knowledge base.", false, true);

        // Reset button
        reloadKbButton.textContent = "Reload KB";
        reloadKbButton.disabled = false;
      });
  });

  // Function to check knowledge base status
  function checkKbStatus() {
    fetch("/api/status")
      .then((response) => response.json())
      .then((data) => {
        if (data.vector_store_initialized) {
          statusIndicator.className = "status-indicator active";
          statusText.textContent = `${data.pdf_count} PDF${
            data.pdf_count !== 1 ? "s" : ""
          } loaded`;
        } else {
          statusIndicator.className = "status-indicator error";
          statusText.textContent = "Knowledge base not initialized";
        }
      })
      .catch((error) => {
        console.error("Error checking KB status:", error);
        statusIndicator.className = "status-indicator error";
        statusText.textContent = "Error checking status";
      });
  }

  // Check KB status on page load
  checkKbStatus();
});
