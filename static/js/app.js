const messagesEl = document.getElementById("messages");
const welcomeEl = document.getElementById("welcome");
const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const newChatBtn = document.getElementById("new-chat-btn");
const statusPill = document.getElementById("status-pill");
const modelLabel = document.getElementById("model-label");
const capabilitiesList = document.getElementById("capabilities-list");

const authModal = document.getElementById("auth-modal");
const paymentModal = document.getElementById("payment-modal");
const authForm = document.getElementById("auth-form");
const authModalTitle = document.getElementById("auth-modal-title");
const authModalSubtitle = document.getElementById("auth-modal-subtitle");
const authNameField = document.getElementById("name-field");
const authNameInput = document.getElementById("auth-name");
const authEmailInput = document.getElementById("auth-email");
const authPasswordInput = document.getElementById("auth-password");
const authSubmitBtn = document.getElementById("auth-submit-btn");
const authSwitchText = document.getElementById("auth-switch-text");
const authSwitchBtn = document.getElementById("auth-switch-btn");
const loginBtn = document.getElementById("login-btn");
const signupBtn = document.getElementById("signup-btn");
const logoutBtn = document.getElementById("logout-btn");
const subscribeBtn = document.getElementById("subscribe-btn");
const authButtons = document.getElementById("auth-buttons");
const userActions = document.getElementById("user-actions");
const userGreeting = document.getElementById("user-greeting");
const planStatus = document.getElementById("plan-status");

let conversation = [];
let isLoading = false;
let currentUser = null;
let authMode = "signup";

marked.setOptions({
  breaks: true,
  gfm: true,
});

function getToken() {
  return localStorage.getItem("access_token");
}

function setToken(token) {
  localStorage.setItem("access_token", token);
}

function clearToken() {
  localStorage.removeItem("access_token");
}

function authHeaders() {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

function renderMarkdown(content) {
  return marked.parse(content);
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function setLoading(loading) {
  isLoading = loading;
  const canChat = Boolean(currentUser?.can_chat);
  sendBtn.disabled = loading || !currentUser || !canChat;
  userInput.disabled = loading || !currentUser || !canChat;
  document.querySelectorAll(".capability-btn, .suggestion").forEach((btn) => {
    btn.disabled = loading || !currentUser || !canChat;
  });
}

function updateWelcomeVisibility() {
  welcomeEl.classList.toggle("hidden", conversation.length > 0);
}

function openModal(modal) {
  modal.classList.remove("hidden");
  modal.setAttribute("aria-hidden", "false");
}

function closeModal(modal) {
  modal.classList.add("hidden");
  modal.setAttribute("aria-hidden", "true");
}

function openAuthModal(mode = "signup") {
  authMode = mode;
  const isSignup = mode === "signup";
  authModalTitle.textContent = isSignup ? "Sign Up" : "Log In";
  authModalSubtitle.textContent = isSignup
    ? "Create an account to start chatting."
    : "Welcome back! Sign in to continue.";
  authNameField.classList.toggle("hidden", !isSignup);
  authSubmitBtn.textContent = isSignup ? "Create Account" : "Log In";
  authSwitchText.textContent = isSignup ? "Already have an account?" : "Don't have an account?";
  authSwitchBtn.textContent = isSignup ? "Log in" : "Sign up";
  authForm.reset();
  openModal(authModal);
  (isSignup ? authNameInput : authEmailInput).focus();
}

function updateAuthUI() {
  const loggedIn = Boolean(currentUser);

  authButtons.classList.toggle("hidden", loggedIn);
  userActions.classList.toggle("hidden", !loggedIn);
  userGreeting.classList.toggle("hidden", !loggedIn);

  if (loggedIn) {
    userGreeting.textContent = `Hi, ${currentUser.full_name}`;
    if (currentUser.is_premium && currentUser.can_chat) {
      planStatus.textContent = "Premium active — unlimited chat";
      planStatus.className = "plan-status premium";
      subscribeBtn.classList.add("hidden");
    } else if (currentUser.can_chat) {
      planStatus.textContent = `${currentUser.free_messages_remaining} free messages left`;
      planStatus.className = "plan-status free";
      subscribeBtn.classList.remove("hidden");
    } else {
      planStatus.textContent = "Free limit reached — subscribe to continue";
      planStatus.className = "plan-status expired";
      subscribeBtn.classList.remove("hidden");
    }
    userInput.placeholder = currentUser.can_chat
      ? "Message AI Assistant..."
      : "Subscribe to continue chatting...";
  } else {
    planStatus.textContent = "Sign up free — 5 messages included";
    planStatus.className = "plan-status";
    userInput.placeholder = "Sign in to start chatting...";
  }

  setLoading(isLoading);
}

async function fetchCurrentUser() {
  const token = getToken();
  if (!token) {
    currentUser = null;
    updateAuthUI();
    return;
  }

  try {
    const response = await fetch("/api/auth/me", { headers: authHeaders() });
    if (!response.ok) {
      clearToken();
      currentUser = null;
    } else {
      currentUser = await response.json();
    }
  } catch {
    currentUser = null;
  }
  updateAuthUI();
}

async function handleAuthSubmit(event) {
  event.preventDefault();
  const endpoint = authMode === "signup" ? "/api/auth/signup" : "/api/auth/login";
  const payload =
    authMode === "signup"
      ? {
          full_name: authNameInput.value.trim(),
          email: authEmailInput.value.trim(),
          password: authPasswordInput.value,
        }
      : {
          email: authEmailInput.value.trim(),
          password: authPasswordInput.value,
        };

  authSubmitBtn.disabled = true;
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.detail || "Authentication failed.");
    }
    setToken(data.access_token);
    currentUser = data.user;
    closeModal(authModal);
    clearError();
    updateAuthUI();
    userInput.focus();
  } catch (error) {
    showError(error.message);
  } finally {
    authSubmitBtn.disabled = false;
  }
}

function logout() {
  clearToken();
  currentUser = null;
  resetChat();
  updateAuthUI();
}

async function startPayment(method) {
  if (!currentUser) {
    openAuthModal("signup");
    return;
  }

  try {
    const response = await fetch("/api/payments/create-order", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ method }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.detail || "Could not start payment.");
    }

    if (typeof Razorpay === "undefined") {
      throw new Error("Payment gateway failed to load. Please refresh the page.");
    }

    const options = {
      key: data.key_id,
      amount: data.amount,
      currency: data.currency,
      name: "AI Chat Assistant",
      description: "Premium Monthly Plan",
      order_id: data.order_id,
      prefill: {
        name: data.user_name,
        email: data.user_email,
      },
      theme: { color: "#5b8cff" },
      method: {
        upi: method === "upi",
        netbanking: method === "netbanking",
        wallet: method === "google_pay",
        card: false,
      },
      handler: async (paymentResponse) => {
        try {
          const verifyRes = await fetch("/api/payments/verify", {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({
              razorpay_order_id: paymentResponse.razorpay_order_id,
              razorpay_payment_id: paymentResponse.razorpay_payment_id,
              razorpay_signature: paymentResponse.razorpay_signature,
            }),
          });
          const verifyData = await verifyRes.json().catch(() => ({}));
          if (!verifyRes.ok) {
            throw new Error(verifyData.detail || "Payment verification failed.");
          }
          closeModal(paymentModal);
          clearError();
          await fetchCurrentUser();
          showError("Payment successful! Premium is now active.");
          document.querySelector(".error-banner")?.classList.add("success-banner");
        } catch (error) {
          showError(error.message);
        }
      },
      modal: {
        ondismiss: () => {
          showError("Payment cancelled.");
        },
      },
    };

    const razorpay = new Razorpay(options);
    razorpay.on("payment.failed", (response) => {
      showError(response.error?.description || "Payment failed. Please try again.");
    });
    razorpay.open();
  } catch (error) {
    showError(error.message);
  }
}

function createMessageElement(role, content, isHtml = false) {
  const wrapper = document.createElement("article");
  wrapper.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "You" : "AI";

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  if (isHtml) {
    bubble.innerHTML = content;
  } else if (role === "assistant") {
    bubble.innerHTML = renderMarkdown(content);
  } else {
    bubble.textContent = content;
  }

  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  return wrapper;
}

function showTypingIndicator() {
  const indicator = createMessageElement(
    "assistant",
    '<div class="typing" aria-label="Assistant is typing"><span></span><span></span><span></span></div>',
    true
  );
  indicator.id = "typing-indicator";
  messagesEl.appendChild(indicator);
  scrollToBottom();
}

function removeTypingIndicator() {
  document.getElementById("typing-indicator")?.remove();
}

function showError(message) {
  document.querySelector(".error-banner, .success-banner")?.remove();
  const banner = document.createElement("div");
  banner.className = "error-banner";
  banner.textContent = message;
  chatForm.before(banner);
}

function clearError() {
  document.querySelector(".error-banner, .success-banner")?.remove();
}

function appendMessage(role, content) {
  conversation.push({ role, content });
  messagesEl.appendChild(createMessageElement(role, content));
  updateWelcomeVisibility();
  scrollToBottom();
}

async function sendMessage(text) {
  const trimmed = text.trim();
  if (!trimmed || isLoading) {
    return;
  }

  if (!currentUser) {
    openAuthModal("signup");
    return;
  }

  if (!currentUser.can_chat) {
    openModal(paymentModal);
    return;
  }

  clearError();
  appendMessage("user", trimmed);
  userInput.value = "";
  userInput.style.height = "auto";

  setLoading(true);
  showTypingIndicator();

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ messages: conversation }),
    });

    const data = await response.json().catch(() => ({}));

    if (response.status === 401) {
      clearToken();
      currentUser = null;
      updateAuthUI();
      openAuthModal("login");
      throw new Error("Session expired. Please sign in again.");
    }

    if (response.status === 402) {
      openModal(paymentModal);
      throw new Error(data.detail || "Subscribe to continue chatting.");
    }

    if (!response.ok) {
      throw new Error(data.detail || "Failed to get a response from the assistant.");
    }

    removeTypingIndicator();
    appendMessage("assistant", data.reply);
    await fetchCurrentUser();
  } catch (error) {
    removeTypingIndicator();
    conversation.pop();
    messagesEl.lastElementChild?.remove();
    updateWelcomeVisibility();
    showError(error.message);
  } finally {
    setLoading(false);
    if (currentUser?.can_chat) {
      userInput.focus();
    }
  }
}

function resetChat() {
  conversation = [];
  messagesEl.innerHTML = "";
  clearError();
  updateWelcomeVisibility();
  if (currentUser?.can_chat) {
    userInput.focus();
  }
}

async function loadAssistantInfo() {
  try {
    const response = await fetch("/api/info");
    const info = await response.json();

    capabilitiesList.innerHTML = info.capabilities
      .map(
        (item) => `
          <li>
            <button
              class="capability-btn"
              type="button"
              data-prompt="${item.prompt.replace(/"/g, "&quot;")}"
              title="Start a chat about ${item.label}"
            >${item.label}</button>
          </li>`
      )
      .join("");

    capabilitiesList.querySelectorAll(".capability-btn").forEach((button) => {
      button.addEventListener("click", () => sendMessage(button.dataset.prompt));
    });

    if (info.configured) {
      statusPill.textContent = "Ready";
      statusPill.className = "status-pill ready";
      modelLabel.textContent = `${info.provider_label} · ${info.model}`;
    } else {
      statusPill.textContent = "Not configured";
      statusPill.className = "status-pill error";
      modelLabel.textContent = `Configure ${info.provider_label} in .env`;
    }
  } catch {
    statusPill.textContent = "Offline";
    statusPill.className = "status-pill error";
    modelLabel.textContent = "Could not reach the backend";
  }
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(userInput.value);
});

userInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage(userInput.value);
  }
});

userInput.addEventListener("input", () => {
  userInput.style.height = "auto";
  userInput.style.height = `${Math.min(userInput.scrollHeight, 180)}px`;
});

newChatBtn.addEventListener("click", resetChat);
loginBtn.addEventListener("click", () => openAuthModal("login"));
signupBtn.addEventListener("click", () => openAuthModal("signup"));
logoutBtn.addEventListener("click", logout);
subscribeBtn.addEventListener("click", () => openModal(paymentModal));
authForm.addEventListener("submit", handleAuthSubmit);
authSwitchBtn.addEventListener("click", () => openAuthModal(authMode === "signup" ? "login" : "signup"));

document.querySelectorAll("[data-close-modal]").forEach((el) => {
  el.addEventListener("click", () => {
    closeModal(authModal);
    closeModal(paymentModal);
  });
});

document.querySelectorAll(".payment-method").forEach((button) => {
  button.addEventListener("click", () => startPayment(button.dataset.method));
});

document.querySelectorAll(".suggestion").forEach((button) => {
  button.addEventListener("click", () => sendMessage(button.dataset.prompt));
});

(async function init() {
  await fetchCurrentUser();
  await loadAssistantInfo();
})();
