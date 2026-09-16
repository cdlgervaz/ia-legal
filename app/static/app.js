const MESES = ["jan.", "fev.", "mar.", "abr.", "maio", "jun.", "jul.", "ago.", "set.", "out.", "nov.", "dez."];

let TEMAS = {};
let TIPOS_DOC = [];
let ULTIMO_TERMO = "";

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

function rotuloTema(tema) {
  return TEMAS[tema] || tema;
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

function destacar(texto, termo) {
  let saida = escapeHtml(texto);
  if (!termo) return saida;
  termo
    .split(/\s+/)
    .filter((t) => t.length >= 3)
    .forEach((t) => {
      const re = new RegExp(`(${t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi");
      saida = saida.replace(re, "<mark>$1</mark>");
    });
  return saida;
}

function resultCard(hit) {
  const p = hit.proposicao;
  if (hit.origem === "documento") {
    const pagina = hit.pagina ? `<span class="tag">p. ${hit.pagina}</span>` : `<span class="tag">documento</span>`;
    const categoria = hit.categoria ? `<span class="tag tag-cat">${escapeHtml(hit.categoria)}</span>` : "";
    const vig = hit.vigente === true
      ? `<span class="badge vigente">Vigente</span>`
      : hit.vigente === false
        ? `<span class="badge nao-vigente">Substituído/Revogado</span>`
        : "";
    const situacaoTxt = [
      hit.situacao,
      hit.substituido_por ? `Substituído por: ${hit.substituido_por}` : "",
    ].filter(Boolean).join(" ");
    return `
      <article class="result doc-hit">
        <header>
          ${categoria || pagina}
          <span class="casa">${escapeHtml(p.tipo)}${p.ano ? " · " + p.ano : ""}</span>
          ${vig}
          <span class="score">${hit.score ? "relevância " + (hit.score * 100).toFixed(0) + "%" : "busca textual"}</span>
        </header>
        <p class="ementa"><strong>${escapeHtml(hit.titulo || p.ementa)}</strong></p>
        ${situacaoTxt ? `<p class="hint">${escapeHtml(situacaoTxt)}</p>` : ""}
        <p class="ementa">${escapeHtml(hit.trecho || "")}</p>
        <div class="temas">${(p.temas || []).map((t) => `<span>${escapeHtml(rotuloTema(t))}</span>`).join("")}</div>
        <div class="actions">
          ${p.url ? `<a class="btn ghost" href="${escapeHtml(p.url)}" target="_blank" rel="noopener">Abrir oficial</a>` : ""}
          <button class="btn ghost" data-doc="${escapeHtml(hit.documento_id)}" type="button">Buscar no documento</button>
          <button class="btn ghost" data-perguntar-doc="${escapeHtml(hit.documento_id)}" type="button">Perguntar sobre ele</button>
        </div>
      </article>`;
  }
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
      ${hit.trecho ? `<p class="ementa hint">${escapeHtml(hit.trecho)}</p>` : ""}
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
  container.querySelectorAll("[data-doc]").forEach((botao) => {
    botao.addEventListener("click", () => {
      mostrarAba("documentos");
      abrirDocumento(botao.dataset.doc);
    });
  });
  container.querySelectorAll("[data-perguntar-doc]").forEach((botao) => {
    botao.addEventListener("click", () => perguntarSobreDocumento(botao.dataset.perguntarDoc));
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
    const ativo = document.querySelector("#chips-categoria .chip.active");
    const categoria = ativo && ativo.dataset.cat ? ativo.dataset.cat : null;
    const body = { query, limit: 12, categoria };
    const data = await api("/api/search", { method: "POST", body: JSON.stringify(body) });
    guardar(data.resultados);
    modo.textContent = `${data.total} resultado(s) - busca ${data.modo}${categoria ? " · " + categoria : ""}.`;
    if (!data.resultados.length) {
      resultados.innerHTML = `<div class="alert info">Nenhum resultado. Importe os documentos na aba Documentos, sincronize a base nas Configurações ou reformule a consulta.</div>`;
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
      const rotulo =
        hit.origem === "documento"
          ? `${escapeHtml(hit.titulo || p.ementa)}${hit.pagina ? " (p. " + hit.pagina + ")" : ""}`
          : `${escapeHtml(p.tipo)} ${escapeHtml(p.numero)}/${p.ano}`;
      const marca = p.url ? `<a href="${escapeHtml(p.url)}" target="_blank" rel="noopener">${rotulo}</a>` : rotulo;
      return `<div>[${indice + 1}] ${marca} - ${escapeHtml(p.casa)}${p.situacao ? " - " + escapeHtml(p.situacao) : ""}</div>`;
    })
    .join("");
  const corpo = escapeHtml(texto).replace(/\[(\d+)\]/g, "<strong>[$1]</strong>");
  return `<div class="msg assistant">${corpo}${links ? `<div class="sources">${links}</div>` : ""}</div>`;
}

function atualizarFiltroChat() {
  return;
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
  aguardando.innerHTML = `<span class="spinner"></span>Consultando o acervo...`;
  janela.appendChild(aguardando);
  janela.scrollTop = janela.scrollHeight;
  $("#chat-send").disabled = true;
  try {
    const seletor = $("#c-categoria");
    const body = { query: pergunta, categoria: seletor ? seletor.value || null : null };
    const data = await api("/api/chat", { method: "POST", body: JSON.stringify(body) });
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

/* ---------- Documentos ---------- */

async function carregarTemas() {
  try {
    const data = await api("/api/temas");
    (data.temas || []).forEach((t) => {
      TEMAS[t.id] = t.rotulo;
    });
    const selects = ["#f-tema", "#c-tema", "#d-tema"];
    selects.forEach((sel) => {
      const alvo = $(sel);
      if (!alvo) return;
      (data.temas || []).forEach((t) => {
        const opcao = document.createElement("option");
        opcao.value = t.id;
        opcao.textContent = t.rotulo;
        alvo.appendChild(opcao);
      });
    });
  } catch (erro) {
    /* silencioso */
  }
}

async function carregarDocumentosFiltro() {
  try {
    const data = await api("/api/documentos");
    const importados = (data.itens || []).filter((d) => d.importado);
    ["#f-documento", "#c-documento"].forEach((sel) => {
      const alvo = $(sel);
      if (!alvo) return;
      const anterior = alvo.value;
      alvo.innerHTML = '<option value="">Todos</option>';
      importados.forEach((doc) => {
        const opcao = document.createElement("option");
        opcao.value = doc.id;
        opcao.textContent = doc.titulo;
        alvo.appendChild(opcao);
      });
      if (anterior) alvo.value = anterior;
    });
  } catch (erro) {
    /* silencioso */
  }
}

function docCard(doc) {
  const temas = (doc.temas || []).map((t) => `<span>${escapeHtml(rotuloTema(t))}</span>`).join("");
  const status = doc.importado
    ? `<span class="status ok">${doc.chunks} trechos</span>`
    : doc.importavel
      ? `<span class="status pendente">não importado</span>`
      : `<span class="status manual">importar manual</span>`;
  return `
    <article class="doc-card">
      <header>
        <div>
          <h3>${escapeHtml(doc.titulo)}</h3>
          <p class="hint">${escapeHtml(doc.tipo)}${doc.ano ? " · " + doc.ano : ""}${doc.orgao ? " · " + escapeHtml(doc.orgao) : ""}</p>
        </div>
        ${status}
      </header>
      <p class="doc-desc">${escapeHtml(doc.descricao || "")}</p>
      <div class="temas">${temas}</div>
      <div class="actions">
        ${doc.importado ? `<button class="btn ghost" data-doc="${escapeHtml(doc.id)}" type="button">Abrir e buscar no documento</button>` : ""}
        ${doc.url ? `<a class="btn ghost" href="${escapeHtml(doc.url)}" target="_blank" rel="noopener">Abrir oficial</a>` : ""}
        ${doc.importado ? `<button class="btn ghost" data-perguntar-doc="${escapeHtml(doc.id)}" type="button">Perguntar</button>` : ""}
      </div>
    </article>`;
}

async function carregarDocumentos() {
  const lista = $("#d-lista");
  lista.innerHTML = `<div class="loading"><span class="spinner"></span>Carregando documentos...</div>`;
  try {
    const params = new URLSearchParams();
    if ($("#d-tema").value) params.set("tema", $("#d-tema").value);
    if ($("#d-tipo").value) params.set("tipo", $("#d-tipo").value);
    if ($("#d-busca").value) params.set("q", $("#d-busca").value);
    const data = await api(`/api/documentos?${params.toString()}`);
    if (!TIPOS_DOC.length) {
      TIPOS_DOC = [...new Set((data.itens || []).map((d) => d.tipo))].sort();
      const select = $("#d-tipo");
      TIPOS_DOC.forEach((tipo) => {
        const opcao = document.createElement("option");
        opcao.value = tipo;
        opcao.textContent = tipo;
        select.appendChild(opcao);
      });
    }
    if (!data.itens.length) {
      lista.innerHTML = `<div class="alert info">Nenhum documento com esses filtros.</div>`;
      return;
    }
    const importados = data.itens.filter((d) => d.importado).length;
    lista.innerHTML = `<p class="hint">${data.total} documento(s), ${importados} já importado(s).</p>` + data.itens.map(docCard).join("");
    ligarAcoes(lista);
  } catch (erro) {
    lista.innerHTML = `<div class="alert error">Erro ao listar documentos: ${escapeHtml(erro.message)}</div>`;
  }
}

async function abrirDocumento(id) {
  const painel = $("#d-detalhe");
  painel.classList.remove("hidden");
  painel.innerHTML = `<div class="loading"><span class="spinner"></span>Carregando documento...</div>`;
  painel.scrollIntoView({ behavior: "smooth", block: "start" });
  try {
    const doc = await api(`/api/documentos/${encodeURIComponent(id)}`);
    const temas = (doc.temas || []).map((t) => `<span>${escapeHtml(rotuloTema(t))}</span>`).join("");
    painel.innerHTML = `
      <header class="doc-detail-header">
        <div>
          <h2>${escapeHtml(doc.titulo)}</h2>
          <p class="hint">${escapeHtml(doc.tipo)}${doc.ano ? " · " + doc.ano : ""}${doc.orgao ? " · " + escapeHtml(doc.orgao) : ""}${doc.importado ? " · " + doc.chunks + " trechos indexados" : " · não importado"}</p>
        </div>
        <button class="btn ghost" id="doc-fechar" type="button">Fechar</button>
      </header>
      <p>${escapeHtml(doc.descricao || "")}</p>
      <div class="temas">${temas}</div>
      ${doc.observacao ? `<p class="hint">${escapeHtml(doc.observacao)}</p>` : ""}
      <div class="actions" style="margin:10px 0">
        ${doc.url ? `<a class="btn secondary" href="${escapeHtml(doc.url)}" target="_blank" rel="noopener">Abrir oficial</a>` : ""}
        ${doc.importado ? `<button class="btn secondary" id="doc-resumo" type="button">Gerar resumo para aula (IA)</button>` : ""}
        ${doc.importado ? `<button class="btn secondary" id="doc-perguntar" type="button">Perguntar sobre este documento</button>` : ""}
      </div>
      <div id="doc-resumo-box"></div>
      ${
        doc.importado
          ? `<div class="doc-busca">
              <h3>Buscar dentro do documento</h3>
              <form id="doc-busca-form" class="search-bar">
                <input id="doc-busca-input" type="text" placeholder="Palavra-chave ou pergunta (ex.: carga horária, avaliação, competências)" autocomplete="off" />
                <select id="doc-busca-modo">
                  <option value="chave">Palavra-chave</option>
                  <option value="semantica">Semântica (IA)</option>
                </select>
                <button class="btn" type="submit">Buscar</button>
              </form>
              <div id="doc-busca-resultados" class="results"></div>
            </div>`
          : ""
      }`;
    $("#doc-fechar").addEventListener("click", () => painel.classList.add("hidden"));
    const botaoResumo = $("#doc-resumo");
    if (botaoResumo) {
      botaoResumo.addEventListener("click", () => resumirDocumento(id));
    }
    const botaoPerguntar = $("#doc-perguntar");
    if (botaoPerguntar) {
      botaoPerguntar.addEventListener("click", () => perguntarSobreDocumento(id));
    }
    const formBusca = $("#doc-busca-form");
    if (formBusca) {
      formBusca.addEventListener("submit", (evento) => {
        evento.preventDefault();
        buscarNoDocumento(id);
      });
    }
  } catch (erro) {
    painel.innerHTML = `<div class="alert error">Erro: ${escapeHtml(erro.message)}</div>`;
  }
}

async function resumirDocumento(id) {
  const box = $("#doc-resumo-box");
  box.innerHTML = `<div class="loading"><span class="spinner"></span>Gerando resumo com IA (pode levar um minuto)...</div>`;
  try {
    const data = await api(`/api/documentos/${encodeURIComponent(id)}/resumo`, { method: "POST" });
    box.innerHTML = `<div class="alert info" style="white-space:pre-wrap">${escapeHtml(data.resumo)}</div>`;
  } catch (erro) {
    box.innerHTML = `<div class="alert warn">${escapeHtml(erro.message)}</div>`;
  }
}

async function buscarNoDocumento(id) {
  const termo = $("#doc-busca-input").value.trim();
  if (!termo) return;
  ULTIMO_TERMO = termo;
  const modo = $("#doc-busca-modo").value;
  const resultados = $("#doc-busca-resultados");
  resultados.innerHTML = `<div class="loading"><span class="spinner"></span>Buscando...</div>`;
  try {
    const params = new URLSearchParams({ q: termo, modo, limit: "30" });
    const data = await api(`/api/documentos/${encodeURIComponent(id)}/busca?${params.toString()}`);
    if (!data.resultados.length) {
      resultados.innerHTML = `<div class="alert info">Nenhum trecho encontrado para "${escapeHtml(termo)}".</div>`;
      return;
    }
    resultados.innerHTML =
      `<p class="hint">${data.total} trecho(s) — busca ${data.modo === "semantica" ? "semântica" : "por palavra-chave"}.</p>` +
      data.resultados
        .map((hit) => {
          const pagina = hit.pagina ? `<span class="tag">p. ${hit.pagina}</span>` : `<span class="tag">trecho</span>`;
          return `
            <article class="result doc-trecho">
              <header>${pagina}<span class="score">${hit.score ? "relevância " + (hit.score * 100).toFixed(0) + "%" : ""}</span></header>
              <p class="ementa">${destacar(hit.trecho || "", termo)}</p>
              <div class="actions">
                <button class="btn ghost" data-copiar-trecho type="button">Copiar trecho</button>
              </div>
            </article>`;
        })
        .join("");
    resultados.querySelectorAll("[data-copiar-trecho]").forEach((botao) => {
      botao.addEventListener("click", () => {
        const trecho = botao.closest(".result").querySelector(".ementa").textContent;
        copiar(trecho, botao);
      });
    });
  } catch (erro) {
    resultados.innerHTML = `<div class="alert error">Erro na busca: ${escapeHtml(erro.message)}</div>`;
  }
}

function perguntarSobreDocumento(id) {
  const select = $("#c-documento");
  if (select) {
    select.value = id;
    if (select.value !== id) {
      const opcao = document.createElement("option");
      opcao.value = id;
      opcao.textContent = id;
      select.appendChild(opcao);
      select.value = id;
    }
  }
  atualizarFiltroChat();
  mostrarAba("perguntar");
  $("#chat-input").focus();
}

async function importarCatalogo() {
  const status = $("#d-status");
  status.innerHTML = `<div class="loading"><span class="spinner"></span>Iniciando importação do catálogo...</div>`;
  $("#d-importar").disabled = true;
  try {
    await api("/api/documentos/importar/background", {
      method: "POST",
      body: JSON.stringify({ ids: [], forcar: false, baixar: true }),
    });
    acompanharImportacao();
  } catch (erro) {
    status.innerHTML = `<div class="alert error">Erro: ${escapeHtml(erro.message)}</div>`;
    $("#d-importar").disabled = false;
  }
}

async function acompanharImportacao() {
  const status = $("#d-status");
  const progresso = $("#cfg-importar-progresso");
  try {
    const estado = await api("/api/documentos/importar/status");
    const alvo = progresso || status;
    if (estado.running) {
      alvo.innerHTML = `
        <div class="progress"><div></div></div>
        <p class="hint">${escapeHtml(estado.fase)} — ${estado.processados}/${estado.total} documentos, ${estado.chunks} trechos indexados.</p>`;
      setTimeout(acompanharImportacao, 2500);
    } else {
      const res = estado.resultado;
      if (res) {
        alvo.innerHTML = `<div class="alert info">Importação concluída: ${res.importados} documento(s), ${res.chunks} trecho(s) em ${res.duracao_segundos}s.
        ${res.erros && res.erros.length ? `<br><strong>Atenção:</strong> ${res.erros.map(escapeHtml).join("<br>")}` : ""}</div>`;
      } else {
        alvo.innerHTML = `<p class="hint">${escapeHtml(estado.fase || "ocioso")}</p>`;
      }
      $("#d-importar").disabled = false;
      $("#cfg-importar").disabled = false;
      carregarDocumentos();
      carregarDocumentosFiltro();
      atualizarStatus();
    }
  } catch (erro) {
    status.innerHTML = `<div class="alert error">Erro ao consultar status: ${escapeHtml(erro.message)}</div>`;
    $("#d-importar").disabled = false;
    $("#cfg-importar").disabled = false;
  }
}

/* ---------- Fim documentos ---------- */

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
    const docs = (info.stats && info.stats.documentos) || 0;
    $("#status-text").textContent = info.llm_configurado
      ? `IA ativa (${info.llm_provider}) · ${docs} documentos · ${info.indexados} itens`
      : `Busca ativa · ${docs} documentos · ${info.indexados} itens · LLM não configurado`;
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
    <p><strong>Documentos importados:</strong> ${stats.documentos || 0} (${stats.documentos_chunks || 0} trechos)</p>
    <p><strong>Proposições na base:</strong> ${stats.total || 0} (${porCasa})</p>
    <p><strong>Por ano:</strong> ${porAno}</p>
    <p><strong>Embeddings:</strong> ${escapeHtml(info.embeddings)}</p>
    <p><strong>Autenticação:</strong> ${info.autenticacao ? "ativada" : "desativada (defina APP_PASSWORD no .env para proteger o acesso)"}</p>
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

function mostrarAba(nome) {
  document.querySelectorAll("nav.tabs button").forEach((b) => {
    b.classList.toggle("active", b.dataset.tab === nome);
  });
  document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
  const painel = $(`#tab-${nome}`);
  if (painel) painel.classList.add("active");
  if (nome === "acompanhar") carregarAcompanhamento();
  if (nome === "config") atualizarConfigInfo();
  if (nome === "documentos") carregarDocumentos();
}

function abrirOnboarding() {
  const el = $("#onboarding");
  if (el) el.classList.remove("hidden");
}

function fecharOnboarding(marcar) {
  const el = $("#onboarding");
  if (!el) return;
  el.classList.add("hidden");
  if (marcar !== false) {
    try {
      localStorage.setItem("iagora_guia_v1", "1");
    } catch (erro) {
      /* armazenamento indisponível */
    }
  }
}

function ligarTabs() {
  document.querySelectorAll("nav.tabs button").forEach((botao) => {
    botao.addEventListener("click", () => mostrarAba(botao.dataset.tab));
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
  $("#d-atualizar").addEventListener("click", carregarDocumentos);
  $("#d-busca").addEventListener("keydown", (evento) => {
    if (evento.key === "Enter") {
      evento.preventDefault();
      carregarDocumentos();
    }
  });
  $("#d-importar").addEventListener("click", importarCatalogo);
  $("#cfg-importar").addEventListener("click", () => {
    mostrarAba("documentos");
    importarCatalogo();
  });
  $("#cfg-importar-status").addEventListener("click", acompanharImportacao);
  $("#modal-close").addEventListener("click", () => $("#modal").classList.add("hidden"));
  $("#modal").addEventListener("click", (evento) => {
    if (evento.target.id === "modal") $("#modal").classList.add("hidden");
  });
  const ajuda = $("#abrir-ajuda");
  if (ajuda) ajuda.addEventListener("click", () => abrirOnboarding());
  const fecharGuia = $("#onboarding-close");
  if (fecharGuia) fecharGuia.addEventListener("click", () => fecharOnboarding());
  const comecar = $("#onboarding-comecar");
  if (comecar) comecar.addEventListener("click", () => fecharOnboarding());
  const onboarding = $("#onboarding");
  if (onboarding) {
    onboarding.addEventListener("click", (evento) => {
      if (evento.target.id === "onboarding") fecharOnboarding();
    });
    onboarding.querySelectorAll(".chip[data-pergunta]").forEach((botao) => {
      botao.addEventListener("click", () => {
        fecharOnboarding();
        mostrarAba("perguntar");
        const campo = $("#chat-input");
        campo.value = botao.dataset.pergunta;
        enviarPergunta();
      });
    });
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  ligarTabs();
  ligarEventos();
  document.querySelectorAll(".chip[data-exemplo]").forEach((botao) => {
    botao.addEventListener("click", () => {
      const campo = $("#chat-input");
      campo.value = botao.dataset.exemplo;
      enviarPergunta();
    });
  });
  document.querySelectorAll("#chips-categoria .chip").forEach((botao) => {
    botao.addEventListener("click", () => {
      document.querySelectorAll("#chips-categoria .chip").forEach((b) => b.classList.remove("active"));
      botao.classList.add("active");
    });
  });
  const campoChat = $("#chat-input");
  if (campoChat) campoChat.focus();
  let jaViuGuia = false;
  try {
    jaViuGuia = localStorage.getItem("iagora_guia_v1") === "1";
  } catch (erro) {
    jaViuGuia = false;
  }
  if (!jaViuGuia) setTimeout(abrirOnboarding, 500);
  await carregarTemas();
  await carregarDocumentosFiltro();
  await carregarDocumentos();
  atualizarStatus();
  carregarAcompanhamento();
});
