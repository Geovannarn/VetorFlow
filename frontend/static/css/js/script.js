'use strict';

const $ = (seletor, raiz = document) => raiz.querySelector(seletor);



function soDigitos(valor) {
  return String(valor == null ? '' : valor).replace(/\D/g, '');
}

function formatarCep(digitos) {
  return digitos.length > 5 ? digitos.slice(0, 5) + '-' + digitos.slice(5) : digitos;
}

function normalizar(texto) {
  return String(texto == null ? '' : texto)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '');
}

function esperar(ms) {
  return new Promise((ok) => setTimeout(ok, ms));
}

function criar(tag, atributos = {}, ...filhos) {
  const no = document.createElement(tag);
  for (const [chave, valor] of Object.entries(atributos)) {
    if (valor == null) continue;
    if (chave === 'class') no.className = valor;
    else if (chave === 'text') no.textContent = valor;
    else no.setAttribute(chave, valor);
  }
  for (const filho of filhos) if (filho != null) no.append(filho);
  return no;
}

function limparCnpj(texto) {
  const d = soDigitos(texto);
  if (d.length !== 14) return { erro: 'CNPJ precisa ter 14 dígitos' };
  if (/^(\d)\1{13}$/.test(d)) return { erro: 'Sequência repetida' };
  return { valor: d };
}

function limparTelefone(texto) {
  let d = soDigitos(texto);
  if (d.length > 11 && d.startsWith('55')) d = d.slice(2);
  if (d.length !== 10 && d.length !== 11) return { erro: 'Telefone precisa ter 10 ou 11 dígitos' };
  return { valor: '+55' + d };
}

function limparCep(texto) {
  const d = soDigitos(texto);
  if (d.length !== 8) return { erro: 'CEP precisa ter 8 dígitos' };
  return { valor: formatarCep(d) };
}

function dataValida(ano, mes, dia) {
  const d = new Date(Date.UTC(ano, mes - 1, dia));
  return d.getUTCFullYear() === ano && d.getUTCMonth() === mes - 1 && d.getUTCDate() === dia;
}

function limparData(texto) {
  const s = String(texto).trim();
  let m;
  let ano, mes, dia;

  if ((m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s))) {
    [ano, mes, dia] = [+m[1], +m[2], +m[3]];
  } else if ((m = /^(\d{2})([/-])(\d{2})\2(\d{4})$/.exec(s))) {
    [dia, mes, ano] = [+m[1], +m[3], +m[4]];
  } else {
    return { erro: 'Use AAAA-MM-DD, DD/MM/AAAA ou DD-MM-AAAA' };
  }

  if (!dataValida(ano, mes, dia)) return { erro: 'Data inexistente' };
  const dd = String(dia).padStart(2, '0');
  const mm = String(mes).padStart(2, '0');
  return { valor: String(ano).padStart(4, '0') + '-' + mm + '-' + dd };
}

const REGRAS = {
  cnpj:     { rotulo: 'CNPJ',     limpar: limparCnpj },
  telefone: { rotulo: 'Telefone', limpar: limparTelefone },
  cep:      { rotulo: 'CEP',      limpar: limparCep },
  data:     { rotulo: 'Data',     limpar: limparData },
};

function detectarTipo(nomeColuna) {
  const n = normalizar(nomeColuna);
  if (!n) return null;
  if (n.includes('cnpj')) return 'cnpj';
  if (/(^|_)cep(_|$)/.test(n)) return 'cep';
  if (/(^|_)(telefone|fone|celular|whatsapp|tel)(_|$)/.test(n)) return 'telefone';
  if (/(^|_)(data|dt)(_|$)/.test(n) || n.includes('nascimento')) return 'data';
  return null;
}

function limparValor(tipo, bruto) {
  const texto = String(bruto == null ? '' : bruto).trim();
  if (!texto) return { valor: '' };
  return REGRAS[tipo].limpar(texto);
}


function detectarDelimitador(texto) {
  const cont = { ',': 0, ';': 0, '\t': 0 };
  let aspas = false;
  for (let i = 0; i < texto.length; i++) {
    const c = texto[i];
    if (c === '"') aspas = !aspas;
    else if (!aspas) {
      if (c === '\n' || c === '\r') break;
      if (c in cont) cont[c]++;
    }
  }
  return [',', ';', '\t'].reduce((a, b) => (cont[b] > cont[a] ? b : a), ',');
}

function parseCsv(texto, delimitador) {
  const linhas = [];
  let linha = [];
  let campo = '';
  let aspas = false;

  for (let i = 0; i < texto.length; i++) {
    const c = texto[i];
    if (aspas) {
      if (c === '"') {
        if (texto[i + 1] === '"') { campo += '"'; i++; }
        else aspas = false;
      } else {
        campo += c;
      }
    } else if (c === '"') {
      aspas = true;
    } else if (c === delimitador) {
      linha.push(campo);
      campo = '';
    } else if (c === '\n' || c === '\r') {
      if (c === '\r' && texto[i + 1] === '\n') i++;
      linha.push(campo);
      linhas.push(linha);
      linha = [];
      campo = '';
    } else {
      campo += c;
    }
  }
  if (campo !== '' || linha.length) {
    linha.push(campo);
    linhas.push(linha);
  }
  return linhas.filter((l) => l.some((c) => c.trim() !== ''));
}

function escaparCsv(valor, delimitador) {
  const s = String(valor == null ? '' : valor);
  return s.includes(delimitador) || /["\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}

function paraCsv(linhas, delimitador) {
  return linhas.map((l) => l.map((c) => escaparCsv(c, delimitador)).join(delimitador)).join('\r\n');
}

/** Lê o arquivo como UTF-8 e, se não for válido, tenta Windows-1252 (Excel brasileiro). */
async function lerTexto(arquivo) {
  const buffer = await arquivo.arrayBuffer();
  let texto;
  try {
    texto = new TextDecoder('utf-8', { fatal: true }).decode(buffer);
  } catch (_) {
    texto = new TextDecoder('windows-1252').decode(buffer);
  }
  return texto.replace(/^\uFEFF/, '');
}

function processarCsv(texto) {
  const delimitador = detectarDelimitador(texto);
  const linhas = parseCsv(texto, delimitador);
  if (linhas.length < 2) return { vazio: true };

  const cabecalho = linhas[0].map((nome, i) => nome.trim() || 'coluna ' + (i + 1));
  const tipos = cabecalho.map(detectarTipo);

  const registros = linhas.slice(1).map((celulas, i) => {
    const campos = cabecalho.map((_, j) => {
      const bruto = celulas[j] == null ? '' : celulas[j];
      const tipo = tipos[j];
      if (!tipo) return { bruto, valor: bruto };
      const r = limparValor(tipo, bruto);
      if (r.erro) return { bruto, valor: bruto, erro: r.erro };
      return { bruto, valor: r.valor, alterado: r.valor !== bruto.trim() };
    });
    const erros = [];
    campos.forEach((c, j) => { if (c.erro) erros.push(cabecalho[j] + ': ' + c.erro); });
    return { linha: i + 2, campos, erros };
  });

  const rejeitadas = registros.filter((r) => r.erros.length).length;
  return {
    delimitador,
    cabecalho,
    tipos,
    registros,
    aceitas: registros.length - rejeitadas,
    rejeitadas,
  };
}

function gerarCsvLimpo(res) {
  const aceitas = res.registros.filter((r) => !r.erros.length);
  return paraCsv([res.cabecalho, ...aceitas.map((r) => r.campos.map((c) => c.valor))], res.delimitador);
}

function gerarCsvRejeitados(res) {
  const rejeitadas = res.registros.filter((r) => r.erros.length);
  return paraCsv(
    [
      [...res.cabecalho, 'erros'],
      ...rejeitadas.map((r) => [...r.campos.map((c) => c.bruto), r.erros.join(' | ')]),
    ],
    res.delimitador
  );
}

function baixar(nomeArquivo, conteudo) {
  const blob = new Blob(['\uFEFF' + conteudo], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = criar('a', { href: url, download: nomeArquivo });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}


const CHAVE_CACHE = 'primora:cep:';
const CHAVE_PREFERENCIA = 'primora:usar-cache';
const VALIDADE_CACHE_MS = 30 * 24 * 60 * 60 * 1000;
const TENTATIVAS_VIACEP = 3;
const TEMPO_LIMITE_MS = 6000;
const NOMES_FONTE = { viacep: 'ViaCEP', brasilapi: 'BrasilAPI' };

class ErroCep extends Error {
  constructor(codigo) {
    super(codigo);
    this.codigo = codigo;
  }
}

function lerCache(cep) {
  try {
    const bruto = localStorage.getItem(CHAVE_CACHE + cep);
    if (!bruto) return null;
    const item = JSON.parse(bruto);
    if (Date.now() - item.salvoEm > VALIDADE_CACHE_MS) {
      localStorage.removeItem(CHAVE_CACHE + cep);
      return null;
    }
    return item;
  } catch (_) {
    return null;
  }
}

function gravarCache(cep, endereco, fonte) {
  try {
    localStorage.setItem(CHAVE_CACHE + cep, JSON.stringify({ endereco, fonte, salvoEm: Date.now() }));
  } catch (_) { }
}

async function buscar(url) {
  const controle = new AbortController();
  const timer = setTimeout(() => controle.abort(), TEMPO_LIMITE_MS);
  try {
    return await fetch(url, { signal: controle.signal });
  } finally {
    clearTimeout(timer);
  }
}

async function consultarViaCep(cep) {
  const resposta = await buscar('https://viacep.com.br/ws/' + cep + '/json/');
  if (!resposta.ok) throw new Error('ViaCEP HTTP ' + resposta.status);
  const j = await resposta.json();
  if (j.erro) return null;
  return {
    cep,
    logradouro: j.logradouro || '',
    bairro: j.bairro || '',
    cidade: j.localidade || '',
    uf: j.uf || '',
    ddd: j.ddd || '',
    ibge: j.ibge || '',
  };
}

async function consultarBrasilApi(cep) {
  const resposta = await buscar('https://brasilapi.com.br/api/cep/v2/' + cep);
  if (resposta.status === 404) return null;
  if (!resposta.ok) throw new Error('BrasilAPI HTTP ' + resposta.status);
  const j = await resposta.json();
  return {
    cep,
    logradouro: j.street || '',
    bairro: j.neighborhood || '',
    cidade: j.city || '',
    uf: j.state || '',
    ddd: '',
    ibge: '',
  };
}

async function resolverCep(cep, { usarCache, aoTentar }) {
  if (usarCache) {
    const guardado = lerCache(cep);
    if (guardado) return { endereco: guardado.endereco, fonte: 'cache', origem: guardado.fonte };
  }

  let inexistente = false;

  for (let tentativa = 1; tentativa <= TENTATIVAS_VIACEP; tentativa++) {
    if (aoTentar) aoTentar('viacep', tentativa);
    try {
      const endereco = await consultarViaCep(cep);
      if (endereco) {
        if (usarCache) gravarCache(cep, endereco, 'viacep');
        return { endereco, fonte: 'viacep' };
      }
      inexistente = true;
      break;
    } catch (_) {
      if (tentativa < TENTATIVAS_VIACEP) await esperar(300 * tentativa);
    }
  }

  if (aoTentar) aoTentar('brasilapi', 1);
  try {
    const endereco = await consultarBrasilApi(cep);
    if (endereco) {
      if (usarCache) gravarCache(cep, endereco, 'brasilapi');
      return { endereco, fonte: 'brasilapi' };
    }
    inexistente = true;
  } catch (_) { /* cai no erro abaixo */ }

  throw new ErroCep(inexistente ? 'nao-encontrado' : 'indisponivel');
}


function criarGerador(semente) {
  let a = semente >>> 0;
  return function () {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function desenharBarras(svg, cep) {
  const LARGURA = 300;
  let hash = 2166136261;
  for (const c of soDigitos(cep)) hash = Math.imul(hash ^ c.charCodeAt(0), 16777619);
  const aleatorio = criarGerador(hash);

  const retangulos = [];
  let x = 0;
  const barra = (largura) => {
    retangulos.push('<rect x="' + x + '" y="0" width="' + largura + '" height="40"/>');
    x += largura;
  };

  barra(2); x += 1; barra(1); x += 2; // guarda inicial
  while (x < LARGURA - 10) {
    const r = aleatorio();
    barra(r < 0.5 ? 1 : r < 0.85 ? 2 : 3);
    x += aleatorio() < 0.65 ? 1 : 2;
  }
  x = LARGURA - 4; barra(1); x += 1; barra(2); // guarda final

  svg.innerHTML = '<g fill="currentColor" shape-rendering="crispEdges">' + retangulos.join('') + '</g>';
}


function iniciarCep() {
  const form = $('#form-cep');
  const entrada = $('#cep');
  const erroCampo = $('#cep-erro');
  const chkCache = $('#usar-cache');
  const botao = $('#btn-consultar');
  const cartao = $('#cartao');
  const dados = $('#dados');
  const mensagem = $('#mensagem');
  const fonte = $('#fonte');
  let consultaAtual = 0;

  try {
    const guardada = localStorage.getItem(CHAVE_PREFERENCIA);
    if (guardada !== null) chkCache.checked = guardada === '1';
  } catch (_) { /* segue com o padrão */ }

  chkCache.addEventListener('change', () => {
    try { localStorage.setItem(CHAVE_PREFERENCIA, chkCache.checked ? '1' : '0'); } catch (_) { /* ignora */ }
  });

  function mostrarErroCampo(texto) {
    erroCampo.textContent = texto;
    erroCampo.hidden = false;
    entrada.setAttribute('aria-invalid', 'true');
  }
  function limparErroCampo() {
    erroCampo.hidden = true;
    erroCampo.textContent = '';
    entrada.removeAttribute('aria-invalid');
  }

  entrada.addEventListener('input', () => {
    const formatado = formatarCep(soDigitos(entrada.value).slice(0, 8));
    if (formatado !== entrada.value) entrada.value = formatado;
    limparErroCampo();
  });

  function definirCarregando(sim) {
    cartao.classList.toggle('is-loading', sim);
    cartao.setAttribute('aria-busy', sim ? 'true' : 'false');
    botao.disabled = sim;
  }

  function mostrarEndereco(resultado, digitos) {
    const e = resultado.endereco;
    mensagem.hidden = true;
    dados.hidden = false;

    $('#cep-a').textContent = digitos.slice(0, 5);
    $('#cep-b').textContent = digitos.slice(5);

    const rua = $('#out-rua');
    rua.textContent = e.logradouro || 'Logradouro não informado';
    rua.classList.toggle('is-vazio', !e.logradouro);

    $('#out-bairro').textContent = e.bairro || '—';
    $('#out-cidade').textContent = e.cidade || '—';
    $('#out-uf').textContent = e.uf || '—';
    $('#out-ddd').textContent = e.ddd || '—';
    $('#out-ibge').textContent = e.ibge || '—';

    fonte.textContent = resultado.fonte === 'cache'
      ? 'Fonte: cache · ' + NOMES_FONTE[resultado.origem]
      : 'Fonte: ' + NOMES_FONTE[resultado.fonte];

    desenharBarras($('#barras'), digitos);
  }

  function mostrarMensagem(titulo, texto) {
    dados.hidden = true;
    mensagem.hidden = false;
    $('#msg-titulo').textContent = titulo;
    $('#msg-texto').textContent = texto;
    fonte.textContent = 'Sem resultado';
  }

  async function consultar() {
    const digitos = soDigitos(entrada.value);
    if (digitos.length !== 8) {
      mostrarErroCampo('Informe um CEP com 8 dígitos.');
      entrada.focus();
      return;
    }

    const minhaConsulta = ++consultaAtual;
    definirCarregando(true);
    fonte.textContent = chkCache.checked ? 'Consultando…' : 'Consultando ViaCEP…';

    try {
      const resultado = await resolverCep(digitos, {
        usarCache: chkCache.checked,
        aoTentar(servico, tentativa) {
          if (minhaConsulta !== consultaAtual) return;
          fonte.textContent = servico === 'viacep'
            ? (tentativa === 1 ? 'Consultando ViaCEP…' : 'ViaCEP · tentativa ' + tentativa + ' de ' + TENTATIVAS_VIACEP)
            : 'Consultando BrasilAPI…';
        },
      });
      if (minhaConsulta !== consultaAtual) return;
      mostrarEndereco(resultado, digitos);
    } catch (erro) {
      if (minhaConsulta !== consultaAtual) return;
      if (erro instanceof ErroCep && erro.codigo === 'nao-encontrado') {
        mostrarMensagem('CEP não encontrado', 'Confira os números e tente de novo. A BrasilAPI também foi consultada.');
      } else {
        mostrarMensagem('Serviços indisponíveis', 'ViaCEP e BrasilAPI não responderam. Verifique sua conexão e tente novamente.');
      }
    } finally {
      if (minhaConsulta === consultaAtual) definirCarregando(false);
    }
  }

  form.addEventListener('submit', (evento) => {
    evento.preventDefault();
    consultar();
  });

  consultar();
}


const TAMANHO_MAXIMO = 5 * 1024 * 1024;
const LINHAS_NA_PREVIA = 100;

function iniciarImportacao() {
  const zona = $('#dropzone');
  const campoArquivo = $('#arquivo');
  const aviso = $('#aviso-importacao');
  const secaoResultado = $('#resultado');
  const btnLimpo = $('#baixar-limpo');
  const btnRejeitados = $('#baixar-rejeitados');
  let atual = null; // { nome, res }

  function definirAviso(texto, erro) {
    aviso.textContent = texto;
    aviso.classList.toggle('aviso--erro', Boolean(erro));
  }

  function celula(campo) {
    const td = criar('td');
    if (campo.erro) {
      td.className = 'cel--erro';
      td.append(criar('span', { text: campo.bruto || '—' }), criar('small', { class: 'cel__nota', text: campo.erro }));
    } else if (campo.alterado) {
      td.className = 'cel--alterada';
      td.append(criar('span', { text: campo.valor }), criar('small', { class: 'cel__nota', text: 'antes: ' + campo.bruto }));
    } else {
      td.textContent = campo.valor;
    }
    return td;
  }

  function renderizar(nome, res) {
    $('#resultado-titulo').textContent = nome;
    $('#res-total').textContent = res.registros.length;
    $('#res-aceitas').textContent = res.aceitas;
    $('#res-rejeitadas').textContent = res.rejeitadas;

    const reconhecidas = res.tipos
      .map((tipo, j) => (tipo ? REGRAS[tipo].rotulo + ' (' + res.cabecalho[j] + ')' : null))
      .filter(Boolean);
    $('#res-colunas').textContent = reconhecidas.length
      ? 'Colunas limpas: ' + reconhecidas.join(', ') + '.'
      : 'Nenhuma coluna reconhecida. Use cabeçalhos como cnpj, telefone, cep ou data.';

    const tabela = $('#tabela-resultado');
    tabela.replaceChildren();

    const cabecalhoLinha = criar('tr', {}, criar('th', { scope: 'col', text: 'Linha' }), criar('th', { scope: 'col', text: 'Situação' }));
    res.cabecalho.forEach((nomeColuna, j) => {
      const th = criar('th', { scope: 'col' }, nomeColuna);
      if (res.tipos[j]) th.append(criar('small', { text: '→ ' + REGRAS[res.tipos[j]].rotulo }));
      cabecalhoLinha.append(th);
    });
    tabela.append(criar('thead', {}, cabecalhoLinha));

    const corpo = criar('tbody');
    res.registros.slice(0, LINHAS_NA_PREVIA).forEach((registro) => {
      const rejeitada = registro.erros.length > 0;
      const tr = criar('tr', { class: rejeitada ? 'is-rejeitada' : '' });
      tr.append(
        criar('td', { class: 'cel--linha', text: String(registro.linha) }),
        criar('td', {}, criar('span', { class: 'selo' + (rejeitada ? ' selo--erro' : ''), text: rejeitada ? 'Rejeitada' : 'Aceita' }))
      );
      registro.campos.forEach((campo) => tr.append(celula(campo)));
      corpo.append(tr);
    });
    tabela.append(corpo);

    $('#res-nota').textContent = res.registros.length > LINHAS_NA_PREVIA
      ? 'Mostrando as primeiras ' + LINHAS_NA_PREVIA + ' de ' + res.registros.length + ' linhas. Os downloads trazem o arquivo completo.'
      : '';

    btnLimpo.disabled = res.aceitas === 0;
    btnRejeitados.disabled = res.rejeitadas === 0;
    secaoResultado.hidden = false;
  }

  async function importar(arquivo) {
    definirAviso('', false);

    if (!/\.(csv|txt)$/i.test(arquivo.name) && !/csv|text/.test(arquivo.type)) {
      definirAviso('Envie um arquivo .csv.', true);
      return;
    }
    if (arquivo.size > TAMANHO_MAXIMO) {
      definirAviso('O arquivo passa de 5 MB.', true);
      return;
    }

    try {
      const texto = await lerTexto(arquivo);
      const res = processarCsv(texto);
      if (res.vazio) {
        definirAviso('O arquivo precisa ter um cabeçalho e ao menos uma linha de dados.', true);
        return;
      }
      atual = { nome: arquivo.name, res };
      renderizar(arquivo.name, res);
      definirAviso(res.aceitas + ' de ' + res.registros.length + ' linhas aceitas.', false);
      secaoResultado.scrollIntoView({ block: 'start' });
    } catch (_) {
      definirAviso('Não foi possível ler o arquivo.', true);
    }
  }

  $('#btn-arquivo').addEventListener('click', () => campoArquivo.click());
  campoArquivo.addEventListener('change', () => {
    const arquivo = campoArquivo.files[0];
    if (arquivo) importar(arquivo);
    campoArquivo.value = ''; // permite escolher o mesmo arquivo de novo
  });

  zona.addEventListener('dragover', (evento) => {
    evento.preventDefault();
    zona.classList.add('dropzone--ativa');
  });
  zona.addEventListener('dragleave', (evento) => {
    if (!zona.contains(evento.relatedTarget)) zona.classList.remove('dropzone--ativa');
  });
  zona.addEventListener('drop', (evento) => {
    evento.preventDefault();
    zona.classList.remove('dropzone--ativa');
    const arquivo = evento.dataTransfer && evento.dataTransfer.files[0];
    if (arquivo) importar(arquivo);
  });
  // Evita que soltar um arquivo fora da zona faça o navegador abri-lo.
  window.addEventListener('dragover', (evento) => evento.preventDefault());
  window.addEventListener('drop', (evento) => evento.preventDefault());

  function nomeBase() {
    return atual.nome.replace(/\.[^.]+$/, '');
  }
  btnLimpo.addEventListener('click', () => {
    if (atual) baixar(nomeBase() + '-limpo.csv', gerarCsvLimpo(atual.res));
  });
  btnRejeitados.addEventListener('click', () => {
    if (atual) baixar(nomeBase() + '-rejeitados.csv', gerarCsvRejeitados(atual.res));
  });
}


function iniciarMenu() {
  const links = Array.from(document.querySelectorAll('.menu a'));
  const secoes = ['inicio', 'consulta', 'clientes', 'importacao']
    .map((id) => document.getElementById(id))
    .filter(Boolean);
  let agendado = false;

  function marcar(alvo) {
    links.forEach((a) => {
      if (a.dataset.alvo === alvo) a.setAttribute('aria-current', 'true');
      else a.removeAttribute('aria-current');
    });
  }

  function atualizar() {
    agendado = false;
    const linhaDeLeitura = window.innerHeight * 0.35;
    let alvo = secoes.length ? secoes[0].id : '';
    for (const secao of secoes) {
      if (secao.getBoundingClientRect().top <= linhaDeLeitura) alvo = secao.id;
    }
    if (alvo === 'importacao' && location.hash === '#regras') alvo = 'regras';
    marcar(alvo);
  }

  function agendar() {
    if (agendado) return;
    agendado = true;
    requestAnimationFrame(atualizar);
  }

  window.addEventListener('scroll', agendar, { passive: true });
  window.addEventListener('hashchange', agendar);
  window.addEventListener('resize', agendar);
  atualizar();
}


function iniciarSplash() {
  const splash = $('#splash');
  if (!splash) return;

  const semMovimento = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (semMovimento) {
    splash.remove();
    return;
  }

  const TEMPO_TOTAL_MS = 3600; // animação de entrada + saída, com folga
  let encerrada = false;

  document.body.classList.add('splash-aberta');

  function encerrar() {
    if (encerrada) return;
    encerrada = true;
    document.body.classList.remove('splash-aberta');
    splash.remove();
  }

  function sair() {
    if (encerrada || splash.classList.contains('splash--saindo')) return;
    splash.classList.add('splash--saindo');
  }

  splash.addEventListener('animationend', (evento) => {
    if (evento.animationName === 'splash-saida') encerrar();
  });
  setTimeout(encerrar, TEMPO_TOTAL_MS); // garantia, caso o evento não dispare

  splash.addEventListener('click', sair);
  document.addEventListener('keydown', (evento) => {
    if (!encerrada && (evento.key === 'Escape' || evento.key === 'Enter' || evento.key === ' ')) {
      evento.preventDefault();
      sair();
    }
  });
}




document.addEventListener('DOMContentLoaded', () => {
  iniciarSplash();
  iniciarMenu();
  iniciarCep();
  iniciarImportacao();
});