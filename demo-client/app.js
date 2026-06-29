const API_BASE_URL =
  window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://localhost:8000"
    : window.SCAMSHIELD_API_URL || "http://localhost:8000";

const sendForm = document.getElementById("sendForm");
const senderInput = document.getElementById("senderInput");
const sendBtn = document.getElementById("sendBtn");
const senderChat = document.getElementById("senderChat");
const recipientChat = document.getElementById("recipientChat");
const trainingModeToggle = document.getElementById("trainingModeToggle");

let trainingModeEnabled = true;

const ICONS = {
  thumbsUp: `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 10v12H3V10h4zm2-1V8a4 4 0 0 1 4-4h1.18C15.4 4 16 5.79 16 7.15V10h3.12c1.45 0 2.35 1.56 1.62 2.8L18 18H9.5c-.83 0-1.54-.5-1.85-1.22L7 10z" fill="currentColor"/></svg>`,
  shield: `<svg class="icon icon-shield" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2l8 3v6c0 5.25-3.5 9.74-8 11-4.5-1.26-8-5.75-8-11V5l8-3z" fill="currentColor"/></svg>`,
  flag: `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 2v20M5 4h10l-2 3 2 3H5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
};

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function linkify(text) {
  const escaped = escapeHtml(text);
  return escaped.replace(
    /(https?:\/\/[^\s]+|www\.[^\s]+)/gi,
    (url) => `<a href="#" tabindex="-1">${url}</a>`
  );
}

function classifyScanResult(data) {
  const action = data.delivery_action;

  if (action === "block") {
    return {
      level: "spam",
      label: "Spam blocked",
      blocked: true,
      shortNote: "Blocked by ScamShield",
    };
  }

  if (action === "warn") {
    return {
      level: "suspicious",
      label: "Suspicious — review carefully",
      blocked: false,
      shortNote: "",
    };
  }

  return {
    level: "safe",
    label: "Safe",
    blocked: false,
    shortNote: "",
  };
}

function appendBubble(
  container,
  { text, direction, state, statusLabel, blockedNote, feedbackData }
) {
  const row = document.createElement("div");
  row.className = `message-row ${direction}`;

  const wrap = document.createElement("div");
  wrap.className = "bubble-wrap";

  const bubble = document.createElement("div");
  bubble.className = `bubble ${direction} ${state || ""}`;
  if (blockedNote) {
    bubble.classList.add("blocked");
  }
  bubble.innerHTML = linkify(text);

  wrap.appendChild(bubble);

  if (statusLabel) {
    const badge = document.createElement("div");
    badge.className = `status-badge ${state || ""}`;
    badge.textContent = statusLabel;
    wrap.appendChild(badge);
  }

  if (blockedNote) {
    const overlay = document.createElement("div");
    overlay.className = "block-overlay";
    overlay.innerHTML = `${ICONS.shield}<span>${blockedNote}</span>`;
    wrap.appendChild(overlay);
  }

  if (feedbackData && trainingModeEnabled) {
    wrap.appendChild(createFlagLink(feedbackData));
  }

  row.appendChild(wrap);
  container.appendChild(row);
  container.scrollTop = container.scrollHeight;

  return { row, bubble, wrap };
}

function createFlagLink(feedbackData) {
  const link = document.createElement("button");
  link.type = "button";
  link.className = "feedback-flag";
  link.innerHTML = `${ICONS.flag}<span>Report incorrect</span>`;
  link.addEventListener("click", () => {
    if (link.dataset.open === "true") return;
    link.dataset.open = "true";
    link.replaceWith(createCorrectionPicker(feedbackData));
  });
  return link;
}

function createCorrectionPicker(feedbackData) {
  const bar = document.createElement("div");
  bar.className = "feedback-bar compact";

  const label = document.createElement("div");
  label.className = "feedback-label";
  label.innerHTML = `<span>Correct label for this message:</span>`;
  bar.appendChild(label);

  const picker = document.createElement("div");
  picker.className = "feedback-picker";
  picker.innerHTML = `
    <button type="button" data-label="safe">Safe</button>
    <button type="button" data-label="suspicious">Suspicious</button>
    <button type="button" data-label="scam">Scam</button>
  `;
  picker.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () =>
      sendFeedback(feedbackData, button.dataset.label, bar)
    );
  });
  bar.appendChild(picker);
  return bar;
}

async function sendFeedback(feedbackData, correctLabel, barEl) {
  try {
    const payload = {
      message: feedbackData.message,
      predicted_action: feedbackData.delivery_action,
      predicted_verdict: feedbackData.verdict,
      user_rating: "wrong",
      correct_label: correctLabel,
      source: "demo-client",
    };

    const response = await fetch(`${API_BASE_URL}/v1/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error("Could not save feedback.");
    }

    barEl.innerHTML =
      `<span class="feedback-thanks">${ICONS.thumbsUp}` +
      `<span>Correction saved as "${correctLabel}".</span></span>`;
  } catch (error) {
    barEl.innerHTML = `<span class="feedback-error">${error.message}</span>`;
  }
}

function clearRecipientEmptyState() {
  const empty = recipientChat.querySelector(".chat-empty");
  if (empty) {
    empty.remove();
  }
}

async function deliverMessage(text) {
  appendBubble(senderChat, { text, direction: "outgoing" });
  senderInput.value = "";

  clearRecipientEmptyState();

  const pending = appendBubble(recipientChat, {
    text,
    direction: "incoming",
    state: "scanning",
    statusLabel: "Scanning...",
  });

  sendBtn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/v1/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });

    const data = await response.json();

    if (!response.ok) {
      const detail =
        typeof data.detail === "string"
          ? data.detail
          : "Could not scan this message.";
      throw new Error(detail);
    }

    pending.row.remove();

    const result = classifyScanResult(data);
    const feedbackPayload = {
      message: text,
      delivery_action: data.delivery_action,
      verdict: data.verdict,
    };

    appendBubble(recipientChat, {
      text,
      direction: "incoming",
      state: result.level,
      statusLabel: result.label,
      blockedNote: result.blocked ? result.shortNote : "",
      feedbackData: trainingModeEnabled ? feedbackPayload : null,
    });
  } catch (error) {
    pending.row.remove();

    const hint =
      error instanceof TypeError
        ? "API offline — start with: ./scripts/run_api.sh"
        : error.message;

    appendBubble(recipientChat, {
      text: `Scan failed: ${hint}`,
      direction: "incoming",
      state: "spam",
      statusLabel: "Error",
    });
  } finally {
    sendBtn.disabled = false;
    senderInput.focus();
  }
}

sendForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = senderInput.value.trim();
  if (!text) return;
  deliverMessage(text);
});

if (trainingModeToggle) {
  trainingModeToggle.addEventListener("change", () => {
    trainingModeEnabled = trainingModeToggle.checked;
  });
}

senderInput.focus();
