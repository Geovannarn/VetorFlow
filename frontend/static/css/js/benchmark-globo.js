/* Globo interativo do benchmark (VetorFlow / primora.)
 * Depende de globe.gl (carregado por CDN antes deste arquivo).
 * Os estilos estão neste arquivo (não precisa de CSS separado).
 *
 * Dados reais: BenchmarkGlobo.carregar({ volumes: [...], etapas: [
 *   { id, nome, porVolume: [{ tempo_s, ram_mb, cpu_pct, registros_por_s, erros }, ...] } ] })
 */
(() => {
  'use strict';

  const raiz = document.getElementById('bm-globo');
  if (!raiz) return;

  /* ---------- Estilos ---------- */
  const CSS = `
.bmg{--bmg-linha:color-mix(in srgb,currentColor 18%,transparent);display:grid;gap:1rem;margin-top:1.5rem}
.bmg .bmg__palco-wrap{position:relative;border:1px solid var(--bmg-linha);border-radius:12px;overflow:hidden}
.bmg .bmg__palco{width:100%;height:clamp(380px,66vh,680px);cursor:grab}
.bmg .bmg__palco:active{cursor:grabbing}
.bmg .bmg__painel{position:absolute;top:1rem;right:1rem;width:min(300px,calc(100% - 2rem));max-height:calc(100% - 2rem);overflow:auto;margin:0}
.bmg .bmg__titulo{margin:0 0 .5rem;font-weight:600}
.bmg .bmg__dica{margin:0}
.bmg .bmg__selo-gargalo{color:var(--bmg-perigo,inherit);font-weight:600}
.bmg .bmg__controles{display:flex;align-items:center;gap:.75rem;flex-wrap:wrap}
.bmg .bmg__slider{flex:1 1 220px;min-width:160px}
.bmg .bmg__volume{min-width:7ch;font-variant-numeric:tabular-nums;font-weight:600}
.bmg .bmg__etapas{display:flex;flex-wrap:wrap;gap:.5rem}
.bmg .bmg__etapas .btn[aria-pressed="true"]{outline:2px solid currentColor;outline-offset:2px}
.bmg .bmg__legenda{display:flex;flex-wrap:wrap;gap:.5rem 1.25rem;margin:0}
.bmg__rotulo{position:absolute;left:12px;top:-10px;white-space:nowrap;pointer-events:none;font-size:12px;font-weight:500;line-height:1.3;padding:1px 6px;border-radius:4px;color:var(--bmg-texto,#000);background:color-mix(in srgb,var(--bmg-fundo,#fff) 82%,transparent)}
.bmg__rotulo--sel{font-weight:700;outline:1px solid var(--bmg-texto,#000)}
@media (max-width:640px){.bmg .bmg__painel{position:static;width:auto;max-height:none;border-radius:0}}
`;
  const estilo = document.createElement('style');
  estilo.textContent = CSS;
  document.head.appendChild(estilo);

  const palco = raiz.querySelector('.bmg__palco');
  const painel = raiz.querySelector('#bmg-painel');
  const slider = raiz.querySelector('#bmg-slider');
  const rotuloVolume = raiz.querySelector('#bmg-volume');
  const btnPlay = raiz.querySelector('#bmg-play');
  const navEtapas = raiz.querySelector('#bmg-etapas');
  const aviso = raiz.querySelector('#bmg-origem');

  if (typeof Globe !== 'function') {
    palco.innerHTML = '<p class="aviso" style="padding:1rem">Não foi possível carregar o globo (biblioteca globe.gl indisponível).</p>';
    return;
  }

  /* ---------- Cores: lidas do próprio site ---------- */
  function lerCor(seletor, prop, reserva) {
    const el = document.querySelector(seletor);
    if (!el) return reserva;
    const v = getComputedStyle(el)[prop];
    if (!v || v === 'transparent' || /,\s*0\)$/.test(v)) return reserva;
    return v;
  }
  function rgb(c) {
    const m = String(c).match(/[\d.]+/g);
    return m && m.length >= 3 ? m.slice(0, 3).map(Number) : [128, 128, 128];
  }
  function misturar(a, b, t) {
    const A = rgb(a), B = rgb(b);
    return `rgb(${A.map((x, i) => Math.round(x + (B[i] - x) * t)).join(',')})`;
  }
  function comAlfa(c, a) {
    const [r, g, b] = rgb(c);
    return `rgba(${r},${g},${b},${a})`;
  }
  function tema() {
    return {
      fundo: lerCor('body', 'backgroundColor', 'rgb(255,255,255)'),
      texto: lerCor('body', 'color', 'rgb(10,10,10)'),
      destaque: lerCor('.btn:not(.btn--contorno)', 'backgroundColor', 'rgb(10,10,10)'),
      perigo: lerCor('.resumo__rejeitadas dd', 'color', lerCor('.cli-perigo', 'backgroundColor', 'rgb(200,40,20)')),
    };
  }
  let T = tema();

  /* ---------- Mapa: Brasil (contorno aproximado, funciona offline) ---------- */
  const BRASIL = {
    __brasil: true,
    type: 'Feature',
    properties: { name: 'Brasil' },
    geometry: {
      type: 'Polygon',
      coordinates: [[
        [-60.2, 5.2], [-59.8, 4.5], [-57.9, 1.9], [-55.9, 2.0], [-54.6, 2.3], [-52.9, 2.2], [-51.7, 4.0],
        [-50.4, 1.8], [-50.0, 0.0], [-49.0, -0.2], [-48.5, -1.4], [-47.0, -0.8], [-44.9, -1.9], [-42.0, -2.8],
        [-39.0, -3.0], [-37.2, -4.8], [-35.2, -5.4], [-34.8, -7.0], [-34.9, -8.2], [-35.5, -9.5], [-37.0, -11.0],
        [-38.5, -13.0], [-39.0, -15.5], [-39.2, -17.8], [-40.0, -20.0], [-41.0, -22.0], [-43.0, -23.0],
        [-45.5, -23.8], [-48.0, -25.5], [-48.6, -26.5], [-48.8, -28.3], [-50.0, -30.0], [-52.0, -32.0],
        [-53.4, -33.7], [-53.1, -32.7], [-55.5, -30.9], [-57.6, -30.2], [-56.0, -28.2], [-54.0, -27.2],
        [-53.7, -26.2], [-54.6, -25.6], [-54.3, -24.0], [-55.4, -23.8], [-55.7, -22.2], [-57.9, -22.1],
        [-57.6, -20.0], [-58.2, -17.9], [-60.0, -16.3], [-60.5, -13.8], [-62.0, -12.5], [-65.0, -11.7],
        [-65.4, -10.4], [-68.0, -11.0], [-70.5, -11.0], [-72.5, -9.5], [-73.2, -7.3], [-70.8, -4.2],
        [-69.9, -4.2], [-69.4, -1.0], [-69.5, 1.0], [-67.0, 1.8], [-66.9, 1.2], [-65.5, 0.7], [-64.0, 1.5],
        [-63.4, 2.2], [-64.0, 4.0], [-62.5, 4.0], [-60.7, 5.2], [-60.2, 5.2],
      ]],
    },
  };

  const FONTES_PAISES = [
    'https://cdn.jsdelivr.net/npm/globe.gl/example/datasets/ne_110m_admin_0_countries.geojson',
    'https://raw.githubusercontent.com/vasturiano/globe.gl/master/example/datasets/ne_110m_admin_0_countries.geojson',
    'https://unpkg.com/three-globe/example/datasets/ne_110m_admin_0_countries.geojson',
  ];

  async function buscarPaises() {
    for (const url of FONTES_PAISES) {
      try {
        const r = await fetch(url);
        if (!r.ok) continue;
        const geo = await r.json();
        if (geo && Array.isArray(geo.features)) return geo.features;
      } catch (e) { /* tenta a próxima */ }
    }
    return [];
  }

  function graticula() {
    const linhas = [];
    for (let lat = -60; lat <= 60; lat += 30) {
      const l = [];
      for (let lng = -180; lng <= 180; lng += 10) l.push([lat, lng]);
      linhas.push(l);
    }
    for (let lng = -180; lng < 180; lng += 30) {
      const l = [];
      for (let lat = -90; lat <= 90; lat += 10) l.push([lat, lng]);
      linhas.push(l);
    }
    return linhas;
  }

  /* ---------- Dados ---------- */
  // Posições só para desenhar (as etapas não são lugares reais), espalhadas pelo Brasil.
  const POSICOES = [
    { lat: -3.12, lng: -60.02 },  // Manaus
    { lat: -15.79, lng: -47.88 }, // Brasília
    { lat: -30.03, lng: -51.23 }, // Porto Alegre
    { lat: -8.05, lng: -34.88 },  // Recife
  ];
  const VISTA_INICIAL = { lat: -15, lng: -52, altitude: 1.5 };

  function dadosExemplo() {
    const volumes = [10000, 100000, 500000, 1000000, 5000000];
    const base = [
      { id: 'extracao', nome: 'Extração', rps: 90000, ram: 0.00005, cpu: 28, erro: 0.001 },
      { id: 'transformacao', nome: 'Transformação', rps: 32000, ram: 0.00014, cpu: 62, erro: 0.02 },
      { id: 'carga', nome: 'Carga no PostgreSQL', rps: 14000, ram: 0.00008, cpu: 48, erro: 0.004 },
    ];
    return {
      volumes,
      etapas: base.map((b) => ({
        id: b.id,
        nome: b.nome,
        porVolume: volumes.map((v, i) => {
          const rps = Math.round(b.rps * (1 - i * 0.07));
          return {
            tempo_s: v / rps,
            ram_mb: 90 + v * b.ram * 1024 / 8,
            cpu_pct: Math.min(98, b.cpu + i * 4),
            registros_por_s: rps,
            erros: Math.round(v * b.erro),
          };
        }),
      })),
    };
  }

  let dados = null;
  let iVol = 0;
  let selecionada = null;
  let limites = null;
  let mundo = null;
  let timer = null;
  let paisesCarregados = false;

  const fmtNum = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 });
  const fmtCompacto = new Intl.NumberFormat('pt-BR', { notation: 'compact', maximumFractionDigits: 1 });
  const fmtOpc = (x, suf) => (x === null || x === undefined || Number.isNaN(Number(x)) ? '—' : fmtNum.format(x) + suf);
  const fmtTempo = (s) => (s >= 120 ? `${fmtNum.format(s / 60)} min` : `${fmtNum.format(s)} s`);

  function calcularLimites() {
    const todos = dados.etapas.flatMap((e) => e.porVolume);
    const rps = todos.map((m) => m.registros_por_s);
    limites = { rpsMin: Math.min(...rps), rpsMax: Math.max(...rps) };
  }
  const normalizarRps = (r) => {
    const a = Math.log(limites.rpsMin), b = Math.log(limites.rpsMax);
    return b === a ? 0.5 : (Math.log(r) - a) / (b - a);
  };

  const metrica = (etapa) => etapa.porVolume[iVol];
  const gargalo = () => dados.etapas.reduce((a, b) => (metrica(b).tempo_s > metrica(a).tempo_s ? b : a));

  /* ---------- Desenho ---------- */
  function pontos() {
    return dados.etapas.map((e, i) => ({ ...e, ...POSICOES[i % POSICOES.length] }));
  }

  function arcos() {
    const p = pontos();
    const v = dados.volumes[iVol];
    return p.slice(0, -1).map((a, i) => {
      const b = p[i + 1];
      const ma = metrica(a), mb = metrica(b);
      const rps = Math.min(ma.registros_por_s, mb.registros_por_s);
      const taxaErro = mb.erros ? mb.erros / v : 0;
      return {
        startLat: a.lat, startLng: a.lng, endLat: b.lat, endLng: b.lng,
        rps, taxaErro, forca: normalizarRps(rps),
      };
    });
  }

  function aplicarTemaAoMundo() {
    raiz.style.setProperty('--bmg-texto', T.texto);
    raiz.style.setProperty('--bmg-fundo', T.fundo);
    raiz.style.setProperty('--bmg-perigo', T.perigo);

    const tomGlobo = misturar(T.fundo, T.texto, 0.07);
    const m = mundo.globeMaterial();
    m.color.set('rgb(0,0,0)');
    m.emissive.set(tomGlobo);
    m.specular.set('rgb(0,0,0)');
    m.shininess = 0;

    mundo
      .atmosphereColor(misturar(T.fundo, T.texto, 0.3))
      .pathColor(() => comAlfa(T.texto, 0.16))
      .hexPolygonColor((d) => (d.__brasil ? misturar(T.fundo, T.texto, 0.9) : misturar(T.fundo, T.texto, 0.32)));
  }

  function iniciarGlobo() {
    mundo = Globe()(palco)
      .backgroundColor('rgba(0,0,0,0)')
      .showAtmosphere(true)
      .atmosphereAltitude(0.12)
      .pointOfView(VISTA_INICIAL, 0)
      // linhas de latitude/longitude (sem depender de internet)
      .pathsData(graticula())
      .pathPointLat((p) => p[0]).pathPointLng((p) => p[1])
      .pathTransitionDuration(0)
      // Brasil em hexágonos, sempre disponível
      .hexPolygonsData([BRASIL])
      .hexPolygonResolution(3).hexPolygonMargin(0.45)
      // pontos = etapas
      .pointLat('lat').pointLng('lng').pointAltitude(0.02)
      .pointLabel((d) => `<b>${d.nome}</b>`)
      .onPointClick((d) => selecionar(d.id))
      // nomes das etapas em HTML (aceita acentos)
      .htmlLat('lat').htmlLng('lng').htmlAltitude(0.03)
      .htmlElement((d) => {
        const el = document.createElement('div');
        el.style.cssText = 'width:0;height:0;pointer-events:none;';
        const s = document.createElement('span');
        s.className = 'bmg__rotulo' + (d.id === selecionada ? ' bmg__rotulo--sel' : '');
        s.textContent = d.nome;
        el.appendChild(s);
        return el;
      })
      // arcos = vazão entre etapas
      .arcStartLat('startLat').arcStartLng('startLng')
      .arcEndLat('endLat').arcEndLng('endLng')
      .arcAltitudeAutoScale(0.35)
      .arcDashLength(0.4).arcDashGap(0.2)
      // anel pulsante no gargalo
      .ringLat('lat').ringLng('lng')
      .ringMaxRadius(4).ringPropagationSpeed(1.6).ringRepeatPeriod(1400);

    aplicarTemaAoMundo();
    mundo.controls().autoRotate = false;

    buscarPaises().then((features) => {
      if (!features.length) return;
      paisesCarregados = true;
      mundo.hexPolygonsData([BRASIL, ...features]);
      aplicarTemaAoMundo();
    });

    new ResizeObserver(() => {
      mundo.width(palco.clientWidth).height(palco.clientHeight);
    }).observe(palco);
  }

  function desenhar() {
    const g = gargalo();
    const maxT = Math.max(...dados.etapas.map((e) => metrica(e).tempo_s)) || 1;
    const pts = pontos();

    mundo
      .pointsData(pts)
      .pointRadius((d) => 0.35 + 0.7 * (metrica(d).tempo_s / maxT))
      .pointColor((d) => (d.id === g.id ? T.perigo : T.destaque))
      .htmlElementsData(pts)
      .arcsData(arcos())
      .arcStroke((d) => 0.3 + 1.7 * d.forca)
      .arcColor((d) => {
        const c = misturar(T.destaque, T.perigo, Math.min(1, d.taxaErro / 0.08));
        return [c, c];
      })
      .arcDashAnimateTime((d) => 900 + 4200 * (1 - d.forca))
      .ringsData(pts.filter((p) => p.id === g.id))
      .ringColor(() => {
        const [r, gg, b] = rgb(T.perigo);
        return (t) => `rgba(${r},${gg},${b},${1 - t})`;
      });

    rotuloVolume.textContent = fmtCompacto.format(dados.volumes[iVol]);
    slider.setAttribute('aria-valuetext', `${fmtCompacto.format(dados.volumes[iVol])} registros`);
    atualizarPainel();
    atualizarChips();
  }

  /* ---------- Painel e seleção ---------- */
  function atualizarPainel() {
    const g = gargalo();
    if (!selecionada) {
      painel.innerHTML = `
        <header class="cartao__topo"><span>Visão geral</span><span>${fmtCompacto.format(dados.volumes[iVol])} registros</span></header>
        <div class="cartao__corpo">
          <p class="bmg__titulo">Gargalo: <span class="bmg__selo-gargalo">${g.nome}</span></p>
          <p class="bmg__dica aviso">Clique em um ponto do globo (ou num botão abaixo) para ver CPU, memória e rejeitados da etapa.</p>
        </div>`;
      return;
    }
    const e = dados.etapas.find((x) => x.id === selecionada);
    const m = metrica(e);
    const total = dados.etapas.reduce((s, x) => s + metrica(x).tempo_s, 0) || 1;
    painel.innerHTML = `
      <header class="cartao__topo"><span>${e.nome}</span><span>${fmtCompacto.format(dados.volumes[iVol])} registros</span></header>
      <div class="cartao__corpo">
        <dl class="meta">
          <div><dt>Tempo</dt><dd>${fmtTempo(m.tempo_s)} (${fmtNum.format((m.tempo_s / total) * 100)}% do total)</dd></div>
          <div><dt>Registros/s</dt><dd>${fmtNum.format(m.registros_por_s)}</dd></div>
          <div><dt>CPU</dt><dd>${fmtOpc(m.cpu_pct, '%')}</dd></div>
          <div><dt>Memória</dt><dd>${fmtOpc(m.ram_mb, ' MB')}</dd></div>
          <div><dt>Rejeitados</dt><dd>${fmtOpc(m.erros, '')}</dd></div>
        </dl>
        ${e.id === g.id ? '<p class="bmg__selo-gargalo">Maior tempo neste volume</p>' : ''}
      </div>`;
  }

  function selecionar(id) {
    selecionada = selecionada === id ? null : id;
    if (selecionada) {
      const p = pontos().find((x) => x.id === id);
      mundo.pointOfView({ lat: p.lat, lng: p.lng, altitude: 0.9 }, 900);
    } else {
      mundo.pointOfView(VISTA_INICIAL, 900);
    }
    desenhar();
  }

  function montarChips() {
    navEtapas.innerHTML = '';
    dados.etapas.forEach((e) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'btn btn--contorno';
      b.dataset.id = e.id;
      b.textContent = e.nome;
      b.addEventListener('click', () => selecionar(e.id));
      navEtapas.appendChild(b);
    });
  }
  function atualizarChips() {
    navEtapas.querySelectorAll('button').forEach((b) => {
      b.setAttribute('aria-pressed', String(b.dataset.id === selecionada));
    });
  }

  /* ---------- Controles ---------- */
  slider.addEventListener('input', () => {
    iVol = Number(slider.value);
    desenhar();
  });

  btnPlay.addEventListener('click', () => {
    if (timer) { parar(); return; }
    if (iVol >= dados.volumes.length - 1) iVol = 0;
    btnPlay.textContent = 'Pausar';
    btnPlay.setAttribute('aria-pressed', 'true');
    slider.value = iVol;
    desenhar();
    timer = setInterval(() => {
      if (iVol >= dados.volumes.length - 1) { parar(); return; }
      iVol += 1;
      slider.value = iVol;
      desenhar();
    }, 1800);
  });
  function parar() {
    clearInterval(timer);
    timer = null;
    btnPlay.textContent = 'Reproduzir';
    btnPlay.setAttribute('aria-pressed', 'false');
  }

  /* ---------- API pública ---------- */
  function carregar(novos, { exemplo = false } = {}) {
    parar();
    dados = novos;
    iVol = 0;
    selecionada = null;
    T = tema();
    calcularLimites();
    slider.max = String(Math.max(0, dados.volumes.length - 1));
    slider.value = '0';
    montarChips();
    aviso.textContent = exemplo
      ? 'Dados de exemplo. Rode o benchmark para ver os resultados reais.'
      : '';
    if (!mundo) iniciarGlobo(); else aplicarTemaAoMundo();
    desenhar();
  }

  window.BenchmarkGlobo = { carregar };
  document.addEventListener('benchmark:dados', (ev) => carregar(ev.detail));

  if (window.__bmGloboDados) {
    carregar(window.__bmGloboDados);
  } else {
    carregar(dadosExemplo(), { exemplo: true });
  }
})();