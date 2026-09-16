(function () {
  "use strict";

  var DADOS = window.LETRAS_DATA;
  if (!DADOS) { return; }

  var CORES = {
    "Norte": "#2a9d8f",
    "Nordeste": "#e76f51",
    "Centro-Oeste": "#e9a23b",
    "Sudeste": "#457b9d",
    "Sul": "#7b6cc4"
  };

  var estado = { regiao: null, uf: null, busca: "", hab: "todas", mod: "todas" };
  var univAberta = null;

  // índice plano
  var INDICE = [];
  var ESTADO_INFO = {};
  var REGIAO_INFO = {};

  Object.keys(DADOS.regioes).forEach(function (nomeRegiao) {
    var r = DADOS.regioes[nomeRegiao];
    REGIAO_INFO[nomeRegiao] = { nome: nomeRegiao, slug: r.slug, estados: Object.keys(r.estados) };
    Object.keys(r.estados).forEach(function (uf) {
      var e = r.estados[uf];
      ESTADO_INFO[uf] = { uf: uf, nome: e.nome, regiao: nomeRegiao, qtd: e.universidades.length };
      e.universidades.forEach(function (u) {
        INDICE.push({
          sigla: u.sigla, nome: u.nome, categoria: u.categoria, site: u.site,
          url_curso: u.url_curso, url_ppc: u.url_ppc, ppc_tipo: u.ppc_tipo,
          cursos: u.cursos, regiao: nomeRegiao, uf: uf, estadoNome: e.nome,
          cidade: u.cursos.length ? u.cursos[0].cidade : "",
          busca: [u.sigla, u.nome, e.nome, uf].concat(u.cursos.map(function (c) {
            return [c.cidade, c.campus, c.nome, c.habilitacao, c.modalidade].join(" ");
          })).join(" ").toLowerCase()
        });
      });
    });
  });

  function porExtenso(n) {
    return new Intl.NumberFormat("pt-BR").format(n);
  }

  function habGrupo(h) {
    if (h === "Espanhol") { return "Espanhol"; }
    if (h === "Português/Espanhol") { return "Português/Espanhol"; }
    return "outras";
  }

  function casaFiltros(u) {
    if (estado.regiao && u.regiao !== estado.regiao) { return false; }
    if (estado.uf && u.uf !== estado.uf) { return false; }
    if (estado.busca && u.busca.indexOf(estado.busca) === -1) { return false; }
    if (estado.hab !== "todas" && !u.cursos.some(function (c) { return habGrupo(c.habilitacao) === estado.hab; })) { return false; }
    if (estado.mod !== "todas" && !u.cursos.some(function (c) { return c.modalidade === estado.mod; })) { return false; }
    return true;
  }

  function filtradas() { return INDICE.filter(casaFiltros); }

  /* ---------------- resumo ---------------- */
  function renderResumo() {
    var s = DADOS.stats;
    var itens = [
      { num: porExtenso(s.universidades), rot: "universidades" },
      { num: porExtenso(s.cursos), rot: "cursos ofertados" },
      { num: s.estados_com_oferta + " de " + s.estados_total, rot: "estados" },
      { num: s.ppc_disponivel + "/" + s.universidades, rot: "PPC linkados" }
    ];
    document.getElementById("resumo").innerHTML = itens.map(function (i) {
      return '<div class="stat"><div class="stat__num">' + i.num + '</div><div class="stat__rot">' + i.rot + '</div></div>';
    }).join("");
  }

  /* ---------------- mapa ---------------- */
  function renderMapa() {
    var el = document.getElementById("mapa");
    el.innerHTML = window.MAPA_BRASIL || "";
    var tooltip = document.getElementById("tooltip");

    el.querySelectorAll(".uf").forEach(function (path) {
      var uf = path.getAttribute("data-uf");
      var info = ESTADO_INFO[uf] || { nome: uf, qtd: 0 };
      path.addEventListener("mousemove", function (ev) {
        var cai = info.qtd ? info.qtd + (info.qtd === 1 ? " universidade" : " universidades") : "sem oferta";
        tooltip.innerHTML = "<strong>" + info.nome + " (" + uf + ")</strong>" + cai;
        var caixa = el.getBoundingClientRect();
        tooltip.style.left = (ev.clientX - caixa.left) + "px";
        tooltip.style.top = (ev.clientY - caixa.top) + "px";
        tooltip.hidden = false;
      });
      path.addEventListener("mouseleave", function () { tooltip.hidden = true; });
      path.addEventListener("click", function () {
        estado.uf = (estado.uf === uf) ? null : uf;
        estado.regiao = estado.uf ? (ESTADO_INFO[uf] || {}).regiao || null : estado.regiao;
        if (!estado.uf) { estado.regiao = null; }
        render();
      });
    });
    atualizarMapa();
  }

  function atualizarMapa() {
    var el = document.getElementById("mapa");
    if (!el) { return; }
    el.querySelectorAll(".uf").forEach(function (path) {
      var uf = path.getAttribute("data-uf");
      var info = ESTADO_INFO[uf] || { regiao: null };
      var apagado = (estado.regiao && info.regiao !== estado.regiao) ||
        (estado.uf && uf !== estado.uf);
      path.classList.toggle("is-apagado", !!apagado);
      path.classList.toggle("is-selecionado", estado.uf === uf);
    });
  }

  /* ---------------- legenda ---------------- */
  function renderLegenda() {
    var box = document.getElementById("legenda");
    var html = ['<button data-regiao="" class="' + (!estado.regiao ? "is-ativo" : "") + '">Brasil <span class="qtd">(' + porExtenso(DADOS.stats.universidades) + ")</span></button>"];
    Object.keys(DADOS.regioes).forEach(function (nome) {
      var st = DADOS.stats.por_regiao[nome] || { universidades: 0 };
      html.push(
        '<button data-regiao="' + nome + '" class="' + (estado.regiao === nome ? "is-ativo" : "") + '">' +
        '<span class="ponto" style="background:' + CORES[nome] + '"></span>' + nome +
        ' <span class="qtd">(' + st.universidades + ")</span></button>"
      );
    });
    box.innerHTML = html.join("");
    box.querySelectorAll("button").forEach(function (b) {
      b.addEventListener("click", function () {
        var r = b.getAttribute("data-regiao");
        estado.regiao = r || null;
        estado.uf = null;
        render();
      });
    });
  }

  /* ---------------- trilha ---------------- */
  function renderTrilha() {
    var box = document.getElementById("trilha");
    var partes = ['<button data-nav="raiz">Brasil</button>'];
    if (estado.regiao) {
      partes.push('<span class="sep">/</span>');
      partes.push(estado.uf
        ? '<button data-nav="regiao">' + estado.regiao + "</button>"
        : '<span class="atual">' + estado.regiao + "</span>");
    }
    if (estado.uf) {
      partes.push('<span class="sep">/</span>');
      partes.push('<span class="atual">' + (ESTADO_INFO[estado.uf] || {}).nome + " (" + estado.uf + ")</span>");
    }
    box.innerHTML = partes.join("");
    box.querySelectorAll("[data-nav]").forEach(function (b) {
      b.addEventListener("click", function () {
        var n = b.getAttribute("data-nav");
        if (n === "raiz") { estado.regiao = null; estado.uf = null; }
        if (n === "regiao") { estado.uf = null; }
        render();
      });
    });
  }

  /* ---------------- filtros ---------------- */
  function renderFiltros() {
    document.querySelectorAll(".chip").forEach(function (chip) {
      var grupo = chip.getAttribute("data-filtro");
      var valor = chip.getAttribute("data-valor");
      var ativo = (grupo === "hab" ? estado.hab : estado.mod) === valor;
      chip.classList.toggle("is-ativo", ativo);
      chip.onclick = function () {
        if (grupo === "hab") { estado.hab = valor; } else { estado.mod = valor; }
        render();
      };
    });
  }

  /* ---------------- lista ---------------- */
  function renderLista() {
    var us = filtradas();
    var lista = document.getElementById("lista");
    var vazio = document.getElementById("vazio");
    document.getElementById("contagem").textContent =
      us.length + (us.length === 1 ? " universidade" : " universidades") + " listadas";

    if (!us.length) { lista.innerHTML = ""; vazio.hidden = false; return; }
    vazio.hidden = true;

    lista.innerHTML = us.map(function (u, i) {
      var habs = unicos(u.cursos.map(function (c) { return c.habilitacao; }));
      var ead = u.cursos.some(function (c) { return c.modalidade === "EAD"; });
      var tags = habs.map(function (h) { return '<span class="tag tag--hab">' + h + "</span>"; }).join("");
      tags += '<span class="tag">' + u.uf + "</span>";
      if (ead) { tags += '<span class="tag tag--ead">EAD</span>'; }
      return (
        '<article class="card" data-i="' + i + '" tabindex="0">' +
        '<div class="card__topo"><span class="card__sigla">' + u.sigla + "</span>" +
        '<span class="card__regiao" style="background:' + CORES[u.regiao] + '">' + u.regiao + "</span></div>" +
        '<div class="card__nome">' + u.nome + " · " + u.estadoNome + "</div>" +
        '<div class="card__tags">' + tags + "</div>" +
        "</article>"
      );
    }).join("");

    lista.querySelectorAll(".card").forEach(function (card) {
      var u = us[Number(card.getAttribute("data-i"))];
      card.addEventListener("click", function () { abrirDetalhe(u); });
      card.addEventListener("keydown", function (ev) {
        if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); abrirDetalhe(u); }
      });
    });
  }

  function unicos(arr) {
    return arr.filter(function (v, i) { return arr.indexOf(v) === i; });
  }

  /* ---------------- detalhe ---------------- */
  function abrirDetalhe(u) {
    var drawer = document.getElementById("drawer");
    var conteudo = document.getElementById("drawer-conteudo");
    var ppcTipo = { ppc: "Projeto Pedagógico do Curso (PPC)", matriz: "Matriz curricular", lista: "Página de PPC/projetos" };

    var cursos = u.cursos.map(function (c) {
      return (
        '<div class="curso">' +
        '<div class="curso__nome">' + c.nome + "</div>" +
        '<div class="curso__meta">' + c.cidade + " · " + c.campus + "<br>" +
        "Habilitação: " + c.habilitacao + " · " + c.modalidade + "</div></div>"
      );
    }).join("");

    var siteCurso = u.url_curso || u.site;
    var links = "";
    links += '<a class="link-btn link-btn--principal" href="' + siteCurso + '" target="_blank" rel="noopener">' +
      "<span>Página do curso<small>" + rotulo(siteCurso) + "</small></span><span class=\"seta\">↗</span></a>";

    if (u.url_ppc) {
      links += '<a class="link-btn" href="' + u.url_ppc + '" target="_blank" rel="noopener">' +
        "<span>" + (ppcTipo[u.ppc_tipo] || "PPC") + "<small>" + rotulo(u.url_ppc) + "</small></span><span class=\"seta\">↗</span></a>";
    } else {
      links += '<div class="aviso">PPC não localizado automaticamente. Procure em "Projeto Pedagógico" na página do curso ou no site da instituição.</div>';
    }
    if (u.site) {
      links += '<a class="link-btn" href="' + u.site + '" target="_blank" rel="noopener">' +
        '<span>Site da instituição<small>' + rotulo(u.site) + "</small></span><span class=\"seta\">↗</span></a>";
    }

    conteudo.innerHTML =
      '<div class="det">' +
      '<div class="det__regiao" style="color:' + CORES[u.regiao] + '">' + u.regiao + " · " + u.estadoNome + " · " + u.uf + "</div>" +
      "<h2>" + u.sigla + "</h2>" +
      '<p class="det__nome">' + u.nome + "</p>" +
      '<div class="det__secao"><h3>Cursos (' + u.cursos.length + ")</h3><div class=\"cursos\">" + cursos + "</div></div>" +
      '<div class="det__secao"><h3>Acesso e documentos</h3><div class="links">' + links + "</div></div>" +
      (u.obs ? '<p class="det__obs">' + u.obs + "</p>" : "") +
      "</div>";

    drawer.hidden = false;
    document.querySelector(".drawer__fechar").focus();
    univAberta = u.sigla;
    atualizarHash();
  }

  function rotulo(url) {
    try { return url.replace(/^https?:\/\//, "").split("/")[0]; }
    catch (e) { return url; }
  }

  function fecharDetalhe() {
    document.getElementById("drawer").hidden = true;
    univAberta = null;
    atualizarHash();
  }

  /* ---------------- link direto (hash) ---------------- */
  function atualizarHash() {
    var partes = [];
    if (estado.regiao) { partes.push(encodeURIComponent(estado.regiao)); }
    if (estado.regiao && estado.uf) { partes.push(estado.uf); }
    if (estado.regiao && estado.uf && univAberta) { partes.push(univAberta); }
    var alvo = partes.length ? "#/" + partes.join("/") : "";
    if (location.hash !== alvo) {
      history.replaceState(null, "", location.pathname + location.search + alvo);
    }
  }

  function aplicarHash() {
    var bruto = decodeURIComponent(location.hash.replace(/^#\/?/, ""));
    if (!bruto) { return null; }
    var p = bruto.split("/");
    var regiao = p[0] || null;
    if (regiao && !DADOS.regioes[regiao]) { return null; }
    estado.regiao = regiao;
    if (p[1] && ESTADO_INFO[p[1]] && ESTADO_INFO[p[1]].regiao === regiao) { estado.uf = p[1]; }
    if (p[2]) { return p[2]; }
    return null;
  }

  /* ---------------- render geral ---------------- */
  function render() {
    renderResumo();
    renderLegenda();
    renderTrilha();
    renderFiltros();
    renderLista();
    atualizarMapa();
    atualizarHash();
  }

  /* ---------------- eventos ---------------- */
  document.getElementById("campo-busca").addEventListener("input", function (ev) {
    estado.busca = ev.target.value.trim().toLowerCase();
    renderLista();
  });
  document.querySelectorAll("[data-fechar]").forEach(function (el) {
    el.addEventListener("click", fecharDetalhe);
  });
  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape") { fecharDetalhe(); }
  });
  window.addEventListener("hashchange", function () {
    univAberta = null;
    estado.regiao = null; estado.uf = null;
    var sigla = aplicarHash();
    render();
    if (sigla) {
      var u = INDICE.filter(function (x) { return x.sigla === sigla; })[0];
      if (u) { abrirDetalhe(u); }
    }
  });

  renderMapa();
  var siglaInicial = aplicarHash();
  render();
  if (siglaInicial) {
    var inicial = INDICE.filter(function (x) { return x.sigla === siglaInicial; })[0];
    if (inicial) { abrirDetalhe(inicial); }
  }
})();
