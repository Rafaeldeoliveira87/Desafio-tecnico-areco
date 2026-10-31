const form = document.querySelector("#chat-form");
const input = document.querySelector("#question");
const conversation = document.querySelector("#conversation");
const sendButton = document.querySelector("#send-button");
const charCount = document.querySelector("#char-count");
const localHistory = [];
const sessionId = globalThis.crypto?.randomUUID?.() ?? null;
const labels = {
  financeiro: "Financeiro",
  informacoes_internas: "Informações internas",
  ouvidoria: "Ouvidoria",
  fora_do_escopo: "Fora do escopo",
};
const agentLabels = {
  FinancialAgent: "Agente Financeiro",
  InternalInformationAgent: "Agente de Informações Internas",
  OmbudsmanAgent: "Agente de Ouvidoria",
  orchestrator: "Orquestrador",
};

function appendUser(question) {
  const article = document.createElement("article");
  article.className = "message user-message";
  article.setAttribute("aria-label", "Sua pergunta");
  const bubble = document.createElement("div");
  bubble.className = "user-bubble";
  bubble.textContent = question;
  article.append(bubble);
  conversation.append(article);
  return article;
}

function appendLoading() {
  const article = document.createElement("article");
  article.className = "message assistant-message";
  article.setAttribute("role", "status");
  article.setAttribute("aria-label", "Consultando as fontes");
  article.innerHTML = '<div class="avatar" aria-hidden="true">A</div><div class="message-body"><span class="message-label">ASSISTENTE</span><p>Consultando as fontes <span class="loading-dots" aria-hidden="true"><i></i><i></i><i></i></span></p></div>';
  conversation.append(article);
  return article;
}

function addPill(container, text) {
  const pill = document.createElement("span");
  pill.className = "meta-pill";
  pill.textContent = text;
  container.append(pill);
}

function renderResponse(data) {
  const article = document.createElement("article");
  article.className = "message assistant-message";
  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = "A";
  const body = document.createElement("div");
  body.className = "message-body";
  const label = document.createElement("span");
  label.className = "message-label";
  label.textContent = "ASSISTENTE";
  const card = document.createElement("div");
  card.className = "answer-card";
  const answer = document.createElement("p");
  answer.className = "answer-text";
  answer.textContent = data.answer;
  card.append(answer);

  const metadata = document.createElement("div");
  metadata.className = "metadata";
  addPill(metadata, `Categoria: ${labels[data.category] ?? data.category}`);
  addPill(metadata, `Confiança: ${Math.round(data.confidence * 100)}%`);
  addPill(metadata, agentLabels[data.agent] ?? data.agent);
  addPill(metadata, `${Number(data.processing_time_ms).toFixed(1)} ms`);
  card.append(metadata);

  if (data.sources?.length) {
    const sources = document.createElement("section");
    sources.className = "sources";
    sources.setAttribute("aria-label", "Fontes consultadas");
    const title = document.createElement("p");
    title.className = "sources-title";
    title.textContent = `Fontes consultadas (${data.sources.length})`;
    sources.append(title);
    for (const source of data.sources) {
      const details = document.createElement("details");
      details.className = "source-item";
      const summary = document.createElement("summary");
      summary.textContent = `${source.file} · ${source.location}`;
      const excerpt = document.createElement("p");
      excerpt.textContent = source.excerpt;
      details.append(summary, excerpt);
      sources.append(details);
    }
    card.append(sources);
  }

  const trace = document.createElement("div");
  trace.className = "trace";
  trace.textContent = "ID da execução: ";
  const id = document.createElement("code");
  id.textContent = data.execution_id;
  trace.append(id);
  card.append(trace);
  body.append(label, card);
  article.append(avatar, body);
  conversation.append(article);
  localHistory.push({ question: data.question, answer: data.answer, executionId: data.execution_id });
  conversation.scrollTop = conversation.scrollHeight;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question || question.length > 1500) return;
  appendUser(question);
  input.value = "";
  charCount.textContent = "0 / 1500";
  sendButton.disabled = true;
  sendButton.setAttribute("aria-busy", "true");
  const loading = appendLoading();
  conversation.scrollTop = conversation.scrollHeight;
  try {
    const response = await fetch("/api/v1/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, session_id: sessionId }),
    });
    if (!response.ok) {
      const message = response.status === 422
        ? "A pergunta não passou pela validação. Confira o limite de caracteres."
        : "O servidor não conseguiu processar a pergunta.";
      throw new Error(message);
    }
    const data = await response.json();
    loading.remove();
    renderResponse(data);
  } catch (error) {
    loading.remove();
    const article = document.createElement("article");
    article.className = "message assistant-message";
    article.setAttribute("role", "alert");
    const body = document.createElement("div");
    body.className = "answer-card";
    const message = document.createElement("p");
    message.className = "answer-text";
    message.textContent = error instanceof TypeError
      ? "Não foi possível conectar ao servidor. Verifique se a aplicação está em execução e tente novamente."
      : error.message;
    body.append(message);
    article.append(body);
    conversation.append(article);
  } finally {
    sendButton.disabled = false;
    sendButton.removeAttribute("aria-busy");
    input.focus();
    conversation.scrollTop = conversation.scrollHeight;
  }
});

input.addEventListener("input", () => {
  charCount.textContent = `${input.value.length} / 1500`;
});

document.querySelectorAll(".example-chip").forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.textContent.trim();
    charCount.textContent = `${input.value.length} / 1500`;
    input.focus();
  });
});
