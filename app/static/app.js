const MESES = ["jan.", "fev.", "mar.", "abr.", "maio", "jun.", "jul.", "ago.", "set.", "out.", "nov.", "dez."];

function $(sel) {
  return document.querySelector(sel);
}

function escapeHtml(text) {
  return (text || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function api(path, options = {}) {
  const resp = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) {
    let detalhe = resp.statusText;
    try {
      const body = await resp.json();
      detalhe = body.detail || JSON.stringify(body);
    } catch (e) {
      /* ignora */
    }
    throw new Error(detalhe);
  }
  return resp.json();
}

function dataAcesso() {
  const agora = new Date();
  return `${agora.getDate()} ${MESES[agora.getMonth()]} ${agora.getFullYear()}`;
}

function citacao(prop) {
  const casa = prop.casa === "Senado" ? "Senado Federal" : "Câmara dos Deputados";
  const local = "Brasília, DF";
  const ano = prop.ano || "";
  const ementa = prop.ementa ? `${prop.ementa} ` : "";
  const link = prop.url ? `Disponível em: <${prop.url}>. ` : "";
  return `BRASIL. ${casa}. ${prop.tipo} ${prop.numero}/${ano}. ${ementa}${local}: ${casa}, ${ano}. ${link}Acesso em: ${dataAcesso()}.`;
}

function copiar(texto, botao) {
  navigator.clipboard.writeText(texto).then(() => {
    const original = botao.textContent;
    botao.textContent = "Copiado!";
    setTimeout(() => (botao.textContent = original), 1500);
  });
}

function resultCard(hit) {
  const p = hit.proposicao;
  const temas = (p.temas || []).slice(0, 6).map((t) => `<span>${escapeHtml(t)}</span>`).join("");
  const score = hit.score && hit.score > 0 ? `<span class="score">relevância ${(hit.score * 100).toFixed(0)}%</span>` : "";
  return `
    <article class="result">
      <header>
        <span class="tag">${escapeHtml(p.tipo)} ${escapeHtml(p.numero)}/${p.ano}</span>
        <span class="casa">${escapeHtml(p.casa)}</span>
        ${score}
      </header>
      <p class="ementa">${escapeHtml(p.ementa)}</p>
      <div class="temas">${temas}</div>
      <div class="meta">
        ${p.situacao ? `<span>Situação: ${escapeHtml(p.situacao)}</span>` : ""}
        ${p.orgao ? `<span>Órgão: ${escapeHtml(p.orgao)}</span>` : ""}
        ${p.autor ? `<span>Autor: ${escapeHtml(p.autor)}</span>` : ""}
        ${p.data ? `<span>Data: ${escapeHtml(p.data)}</span>` : ""}
      </div>
      <div class="actions">
        ${p.url ? `<a class="btn ghost" href="${escapeHtml(p.url)}" target="_blank" rel="noopener">Abrir oficial</a>` : ""}
        <button class="btn ghost" data-detail="${escapeHtml(p.id)}" type="button">Ver tramitação</button>
        <button class="btn ghost" data-copy="${escapeHtml(p.id)}" type="button">Copiar citação</button>
      </div>
    </article>`;
}

const cache = {};

function ligarAcoes(container) {
  container.querySelectorAll("[data-copy]").forEach((botao) => {
    botao.addEventListener("click", () => {
      const p = cache[botao.dataset.copy];
      if (p) copiar(citacao(p), botao);
    });
  });
  container.querySelectorAll("[data-detail]").forEach((botao) => {
    botao.addEventListener("click", () => abrirDetalhe(botao.dataset.detail));
  });
}

function guardar(hits) {
  (hits || []).forEach((hit) => {
    cache[hit.proposicao.id] = hit.proposicao;
  });
}

async function executarBusca(evento) {
  if (evento) evento.preventDefault();
  const query = $("#search-input").value.trim();
  if (!query) return;
  const resultados = $("#search-results");
  const modo = $("#search-modo");
  resultados.innerHTML = `<div class="loading"><span class="spinner"></span>Buscando...</div>`;
  modo.textContent = "";
  try {
    const body = {
      query,
      limit: parseInt($("#f-limit").value, 10),
      casa: $("#f-casa").value || null,
      tipo: $("#f-tipo").value || null,
      ano_de: $("#f-ano-de").value ? parseInt($("#f-ano-de").value, 10) : null,
      ano_ate: $("#f-ano-ate").value ? parseInt($("#f-ano-ate").value, 10) : null,
    };
    const data = await api("/api/search", { method: "POST", body: JSON.stringify(body) });
    guardar(data.resultados);
    modo.textContent = `${data.total} resultado(s) - busca ${data.modo}.`;
    if (!data.resultados.length) {
      resultados.innerHTML = `<div class="alert info">Nenhum resultado. Sincronize a base na aba Configurações ou reformule a consulta.</div>`;
      return;
    }
    resultados.innerHTML = data.resultados.map(resultCard).join("");
    ligarAcoes(resultados);
  } catch (erro) {
    resultados.innerHTML = `<div class="alert error">Erro na busca: ${escapeHtml(erro.message)}</div>`;
  }
}

function bolhaUsuario(texto) {
  return `<div class="msg user">${escapeHtml(texto)}</div>`;
}

function bolhaAssistente(texto, fontes) {
  const links = (fontes || [])
    .map((hit, indice) => {
      const p = hit.proposicao;
      const marca = p.url ? `<a href="${escapeHtml(p.url)}" target="_blank" rel="noopener">${escapeHtml(p.tipo)} ${escapeHtml(p.numero)}/${p.ano}</a>` : `${escapeHtml(p.tipo)} ${escapeHtml(p.numero)}/${p.ano}`;
      return `<div>[${indice + 1}] ${marca} - ${escapeHtml(p.casa)}${p.situacao ? " - " + escapeHtml(p.situacao) : ""}</div>`;
    })
    .join("");
  const corpo = escapeHtml(texto).replace(/\[(\d+)\]/g, "<strong>[$1]</strong>");
  return `<div class="msg assistant">${corpo}${links ? `<div class="sources">${links}</div>` : ""}</div>`;
}

async function enviarPergunta(evento) {
  if (evento) evento.preventDefault();
  const campo = $("#chat-input");
  const pergunta = campo.value.trim();
  if (!pergunta) return;
  const janela = $("#chat-window");
  janela.insertAdjacentHTML("beforeend", bolhaUsuario(pergunta));
  campo.value = "";
  janela.scrollTop = janela.scrollHeight;
  const aguardando = document.createElement("div");
  aguardando.className = "msg assistant";
  aguardando.innerHTML = `<span class="spinner"></span>Consultando a base legislativa...`;
  janela.appendChild(aguardando);
  janela.scrollTop = janela.scrollHeight;
  $("#chat-send").disabled = true;
  try {
    const data = await api("/api/chat", { method: "POST", body: JSON.stringify({ query: pergunta }) });
    guardar(data.fontes);
    aguardando.outerHTML = bolhaAssistente(data.resposta, data.fontes);
  } catch (erro) {
    aguardando.outerHTML = `<div class="msg assistant"><span class="alert error">Erro: ${escapeHtml(erro.message)}</span></div>`;
  } finally {
    $("#chat-send").disabled = false;
    janela.scrollTop = janela.scrollHeight;
  }
}

async function abrirDetalhe(id) {
  const modal = $("#modal");
  const corpo = $("#modal-body");
  corpo.innerHTML = `<div class="loading"><span class="spinner"></span>Carregando detalhes...</div>`;
  modal.classList.remove("hidden");
  try {
    const prop = await api(`/api/proposicoes/${encodeURIComponent(id)}`);
    cache[id] = prop;
    const temas = (prop.temas || []).map((t) => `<span>${escapeHtml(t)}</span>`).join("");
    const linhaTempo = (prop.tramitacoes || [])
      .slice()
      .reverse()
      .map((t) => `<li><div class="when">${escapeHtml(t.data_hora || "")} ${t.orgao ? "- " + escapeHtml(t.orgao) : ""}</div>${escapeHtml(t.descricao || t.situacao || "")}</li>`)
      .join("");
    corpo.innerHTML = `
      <h2>${escapeHtml(prop.tipo)} ${escapeHtml(prop.numero)}/${prop.ano} - ${escapeHtml(prop.casa)}</h2>
      <p class="hint">${prop.situacao ? "Situação atual: " + escapeHtml(prop.situacao) : ""} ${prop.orgao ? "- " + escapeHtml(prop.orgao) : ""}</p>
      <p>${escapeHtml(prop.ementa)}</p>
      <div class="temas">${temas}</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:12px">
        ${prop.url ? `<a class="btn secondary" href="${escapeHtml(prop.url)}" target="_blank" rel="noopener">Abrir página oficial</a>` : ""}
        <button class="btn secondary" id="btn-resumo" type="button">Gerar resumo para aula (IA)</button>
      </div>
      <h3 style="margin-bottom:4px">Tramitação recente</h3>
      ${linhaTempo ? `<ul class="timeline">${linhaTempo}</ul>` : `<p class="hint">Sem tramitações registradas.</p>`}
      <div id="resumo-box"></div>`;
    const botaoResumo = $("#btn-resumo");
    if (botaoResumo) {
      botaoResumo.addEventListener("click", async () => {
        const box = $("#resumo-box");
        box.innerHTML = `<div class="loading"><span class="spinner"></span>Gerando resumo...</div>`;
        try {
          const data = await api(`/api/proposicoes/${encodeURIComponent(id)}/resumo`, { method: "POST" });
          box.innerHTML = `<div class="alert info" style="white-space:pre-wrap">${escapeHtml(data.resumo)}</div>`;
        } catch (erro) {
          box.innerHTML = `<div class="alert warn">${escapeHtml(erro.message)}</div>`;
        }
      });
    }
  } catch (erro) {
    corpo.innerHTML = `<div class="alert error">Erro: ${escapeHtml(erro.message)}</div>`;
  }
}

async function carregarAcompanhamento() {
  const tbody = $("#a-tbody");
  tbody.innerHTML = `<tr><td colspan="6"><span class="spinner"></span>Carregando...</td></tr>`;
  const params = new URLSearchParams();
  if ($("#a-casa").value) params.set("casa", $("#a-casa").value);
  if ($("#a-ano").value) params.set("ano_de", $("#a-ano").value);
  if ($("#a-busca").value) params.set("busca", $("#a-busca").value);
  params.set("limit", "100");
  try {
    const data = await api(`/api/proposicoes?${params.toString()}`);
    if (!data.itens.length) {
      tbody.innerHTML = `<tr><td colspan="6" class="hint">Nenhuma proposição. Sincronize na aba Configurações.</td></tr>`;
      return;
    }
    tbody.innerHTML = data.itens
      .map((p) => {
        cache[p.id] = p;
        return `<tr>
          <td><strong>${escapeHtml(p.tipo)} ${escapeHtml(p.numero)}/${p.ano}</strong></td>
          <td>${escapeHtml(p.casa)}</td>
          <td>${escapeHtml(p.ementa.slice(0, 160))}${p.ementa.length > 160 ? "..." : ""}</td>
          <td>${escapeHtml(p.situacao || "-")}</td>
          <td>${escapeHtml(p.orgao || "-")}</td>
          <td><button class="btn ghost" data-detail="${escapeHtml(p.id)}" type="button">Ver</button></td>
        </tr>`;
      })
      .join("");
    ligarAcoes(tbody);
  } catch (erro) {
    tbody.innerHTML = `<tr><td colspan="6"><div class="alert error">Erro: ${escapeHtml(erro.message)}</div></td></tr>`;
  }
}

async function atualizarStatus() {
  try {
    const info = await api("/api/health");
    $("#status-dot").className = `dot ${info.llm_configurado ? "on" : "off"}`;
    $("#status-text").textContent = info.llm_configurado
      ? `IA ativa (${info.llm_provider}) - ${info.indexados} itens`
      : `Busca ativa - ${info.indexados} itens - LLM não configurado`;
    return info;
  } catch (erro) {
    $("#status-dot").className = "dot off";
    $("#status-text").textContent = "Servidor indisponível";
    return null;
  }
}

async function atualizarConfigInfo() {
  const info = await atualizarStatus();
  if (!info) {
    $("#config-info").innerHTML = `<div class="alert error">Não foi possível contatar o servidor.</div>`;
    return;
  }
  const stats = info.stats || {};
  const porCasa = Object.entries(stats.por_casa || {}).map(([k, v]) => `${k}: ${v}`).join(" | ") || "-";
  const porAno = Object.entries(stats.por_ano || {}).slice(0, 8).map(([k, v]) => `${k}: ${v}`).join(" | ") || "-";
  $("#config-info").innerHTML = `
    <p><strong>Itens indexados:</strong> ${info.indexados}</p>
    <p><strong>Proposições na base:</strong> ${stats.total || 0} (${porCasa})</p>
    <p><strong>Por ano:</strong> ${porAno}</p>
    <p><strong>Embeddings:</strong> ${escapeHtml(info.embeddings)}</p>
    <p><strong>LLM:</strong> ${info.llm_configurado ? "configurado (" + escapeHtml(info.llm_provider) + ")" : "não configurado - defina LLM_API_KEY no arquivo .env"}</p>`;
}

async function sincronizar() {
  const anos = $("#s-anos").value
    .split(",")
    .map((a) => parseInt(a.trim(), 10))
    .filter((a) => !isNaN(a));
  const tipos = $("#s-tipos").value
    .split(",")
    .map((t) => t.trim().toUpperCase())
    .filter(Boolean);
  const body = {
    camara: $("#s-camara").checked,
    senado: $("#s-senado").checked,
    anos,
    tipos,
    max_itens_por_ano: parseInt($("#s-max").value, 10) || 60,
    buscar_tramitacoes: $("#s-tram").checked,
    incluir_comunicacoes: $("#s-com").checked,
  };
  $("#s-progress").innerHTML = `<div class="loading"><span class="spinner"></span>Iniciando sincronização...</div>`;
  $("#s-iniciar").disabled = true;
  try {
    await api("/api/sync/background", { method: "POST", body: JSON.stringify(body) });
    acompanharSync();
  } catch (erro) {
    $("#s-progress").innerHTML = `<div class="alert error">Erro: ${escapeHtml(erro.message)}</div>`;
    $("#s-iniciar").disabled = false;
  }
}

async function acompanharSync() {
  try {
    const estado = await api("/api/sync/status");
    if (estado.running) {
      $("#s-progress").innerHTML = `
        <div class="progress"><div></div></div>
        <p class="hint">${escapeHtml(estado.fase)} - ${estado.processados} processados, ${estado.indexados} indexados</p>`;
      setTimeout(acompanharSync, 2000);
    } else {
      const res = estado.resultado;
      if (res) {
        $("#s-progress").innerHTML = `<div class="alert info">Concluído: ${res.camara} da Câmara, ${res.senado} do Senado, ${res.indexados} indexados em ${res.duracao_segundos}s.</div>`;
        atualizarStatus();
        atualizarConfigInfo();
      } else {
        $("#s-progress").innerHTML = `<p class="hint">${escapeHtml(estado.fase || "ocioso")}</p>`;
      }
      $("#s-iniciar").disabled = false;
    }
  } catch (erro) {
    $("#s-progress").innerHTML = `<div class="alert error">Erro ao consultar status: ${escapeHtml(erro.message)}</div>`;
    $("#s-iniciar").disabled = false;
  }
}

function ligarTabs() {
  document.querySelectorAll("nav.tabs button").forEach((botao) => {
    botao.addEventListener("click", () => {
      document.querySelectorAll("nav.tabs button").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      botao.classList.add("active");
      $(`#tab-${botao.dataset.tab}`).classList.add("active");
      if (botao.dataset.tab === "acompanhar") carregarAcompanhamento();
      if (botao.dataset.tab === "config") atualizarConfigInfo();
    });
  });
}

function ligarEventos() {
  $("#search-form").addEventListener("submit", executarBusca);
  $("#chat-form").addEventListener("submit", enviarPergunta);
  $("#chat-input").addEventListener("keydown", (evento) => {
    if (evento.key === "Enter" && !evento.shiftKey) {
      evento.preventDefault();
      enviarPergunta(evento);
    }
  });
  $("#a-atualizar").addEventListener("click", carregarAcompanhamento);
  $("#s-iniciar").addEventListener("click", sincronizar);
  $("#s-status").addEventListener("click", acompanharSync);
  $("#modal-close").addEventListener("click", () => $("#modal").classList.add("hidden"));
  $("#modal").addEventListener("click", (evento) => {
    if (evento.target.id === "modal") $("#modal").classList.add("hidden");
  });
}

document.addEventListener("DOMContentLoaded", () => {
  ligarTabs();
  ligarEventos();
  atualizarStatus();
  carregarAcompanhamento();
});
