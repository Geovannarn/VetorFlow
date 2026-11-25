(function () {
  'use strict';

  const URL_DADOS = '/api/benchmark/';

  const LINHAS_DAS_TABELAS = [
    { etapa: 'extracao', variante: 'chunks', rotulo: 'Extração (em partes)' },
    { etapa: 'extracao', variante: 'inteiro', rotulo: 'Extração (arquivo inteiro)' },
    { etapa: 'transformacao', variante: 'completa', rotulo: 'Transformação' },
    { etapa: 'carga', variante: 'lote', rotulo: 'Carga em lote' },
    { etapa: 'carga', variante: 'copy', rotulo: 'Carga com COPY' }
  ];

  const ETAPAS_PRINCIPAIS = ['extracao', 'transformacao', 'carga'];

  const TITULOS_GRAFICOS = {
    tempo_por_etapa: 'Tempo de execução por etapa',
    registros_por_segundo: 'Registros por segundo',
    memoria_por_etapa: 'Pico de memória',
    cpu_por_etapa: 'Uso de CPU',
    transformacao_operacoes: 'Onde a transformação gasta tempo',
    carga_estrategias: 'Estratégias de carga no PostgreSQL',
    qualidade: 'Problemas de qualidade encontrados',
    consultas_banco: 'Consultas no banco',
    api_latencias: 'Latência da API'
  };

  const $ = (seletor) => document.querySelector(seletor);

  function criar(tag, texto, classe) {
    const elemento = document.createElement(tag);

    if (texto !== undefined && texto !== null) {
      elemento.textContent = texto;
    }

    if (classe) {
      elemento.className = classe;
    }

    return elemento;
  }

  function ausente(valor) {
    return valor === null || valor === undefined || valor === '' || Number.isNaN(Number(valor));
  }

  function formatarNumero(valor, casas) {
    if (ausente(valor)) {
      return '—';
    }

    return Number(valor).toLocaleString('pt-BR', {
      minimumFractionDigits: casas,
      maximumFractionDigits: casas
    });
  }

  function rotuloVolume(volume) {
    if (volume === 0) return 'tabela atual';
    if (volume >= 1000000) return (volume / 1000000).toLocaleString('pt-BR') + ' mi';
    if (volume >= 1000) return (volume / 1000).toLocaleString('pt-BR') + ' mil';

    return String(volume);
  }

  function formatarData(valor) {
    if (ausente(valor) && typeof valor !== 'string') return null;

    const data = typeof valor === 'number' || /^\d+(\.\d+)?$/.test(String(valor))
      ? new Date(Number(valor) * 1000)
      : new Date(valor);

    if (Number.isNaN(data.getTime())) return null;

    return data.toLocaleString('pt-BR');
  }

  function volumesDe(resultados) {
    const volumes = [];

    for (const linha of resultados) {
      const principal = ETAPAS_PRINCIPAIS.includes(linha.etapa);

      if (principal && !linha.ignorado && !volumes.includes(linha.volume)) {
        volumes.push(linha.volume);
      }
    }

    volumes.sort((a, b) => a - b);

    return volumes;
  }

  function acharLinha(resultados, etapa, variante, volume) {
    let achada = null;

    for (const linha of resultados) {
      const igual = linha.etapa === etapa && linha.variante === variante && linha.volume === volume;

      if (igual && !linha.ignorado) {
        achada = linha;
      }
    }

    return achada;
  }

  function montarTabela(resultados, volumes, titulo, campo, casas) {
    const bloco = criar('div');
    bloco.append(criar('p', titulo, 'bm-subtitulo'));

    const caixa = criar('div', null, 'cli-tabela-wrap');
    caixa.tabIndex = 0;
    caixa.setAttribute('role', 'region');
    caixa.setAttribute('aria-label', titulo);

    const tabela = criar('table', null, 'cli-tabela');

    const cabecalho = criar('tr');
    const thEtapa = criar('th', 'Etapa');
    thEtapa.scope = 'col';
    cabecalho.append(thEtapa);

    for (const volume of volumes) {
      const th = criar('th', rotuloVolume(volume));
      th.scope = 'col';
      cabecalho.append(th);
    }

    const topo = criar('thead');
    topo.append(cabecalho);
    tabela.append(topo);

    const corpo = criar('tbody');

    for (const definicao of LINHAS_DAS_TABELAS) {
      const linhaTabela = criar('tr');
      const rotulo = criar('th', definicao.rotulo);
      rotulo.scope = 'row';
      linhaTabela.append(rotulo);

      let temValor = false;

      for (const volume of volumes) {
        const dados = acharLinha(resultados, definicao.etapa, definicao.variante, volume);
        const valor = dados ? dados[campo] : null;

        if (!ausente(valor)) temValor = true;

        linhaTabela.append(criar('td', formatarNumero(valor, casas), 'cli-mono'));
      }

      if (temValor) corpo.append(linhaTabela);
    }

    tabela.append(corpo);
    caixa.append(tabela);
    bloco.append(caixa);

    return bloco;
  }

  function adicionarResumo(lista, titulo, valor, classe) {
    const item = criar('div', null, classe);
    item.append(criar('dt', titulo));
    item.append(criar('dd', valor));
    lista.append(item);
  }

  function montarResumo(resultados, volumes) {
    const lista = $('#bm-resumo');
    lista.replaceChildren();

    if (volumes.length === 0) return;

    const maior = volumes[volumes.length - 1];
    const transformacao = acharLinha(resultados, 'transformacao', 'completa', maior);

    let picoMemoria = null;

    for (const linha of resultados) {
      const principal = ETAPAS_PRINCIPAIS.includes(linha.etapa);

      if (principal && linha.volume === maior && !linha.ignorado && !ausente(linha.ram_pico_mb)) {
        const valor = Number(linha.ram_pico_mb);

        if (picoMemoria === null || valor > picoMemoria) {
          picoMemoria = valor;
        }
      }
    }

    adicionarResumo(lista, 'Maior volume testado', rotuloVolume(maior));

    if (transformacao) {
      adicionarResumo(lista, 'Transformação', formatarNumero(transformacao.tempo_s, 1) + ' s');
      adicionarResumo(lista, 'Registros por segundo', formatarNumero(transformacao.registros_por_s, 0));
    }

    if (picoMemoria !== null) {
      adicionarResumo(lista, 'Pico de memória', formatarNumero(picoMemoria, 0) + ' MB');
    }

    if (transformacao) {
      adicionarResumo(
        lista,
        'Rejeitados',
        formatarNumero(transformacao.taxa_rejeicao_pct, 1) + '%',
        'resumo__rejeitadas'
      );
    }
  }

  function montarGraficos(graficos, geradoEm) {
    const area = $('#bm-graficos');
    area.replaceChildren();

    for (const grafico of graficos) {
      if (!grafico || !grafico.url) continue;

      const titulo = TITULOS_GRAFICOS[grafico.nome] || grafico.nome || 'Gráfico';
      const figura = criar('figure', null, 'bm-figura');
      const imagem = document.createElement('img');
      const separador = grafico.url.includes('?') ? '&' : '?';

      imagem.src = grafico.url + separador + 'v=' + encodeURIComponent(geradoEm ?? Date.now());
      imagem.alt = titulo;
      imagem.loading = 'lazy';

      figura.append(imagem);
      figura.append(criar('figcaption', titulo));
      area.append(figura);
    }
  }

  function limparTela() {
    $('#bm-resumo').replaceChildren();
    $('#bm-tabelas').replaceChildren();
    $('#bm-graficos').replaceChildren();
  }

  function mostrarAviso(texto, ehErro) {
    const aviso = $('#bm-status');

    aviso.textContent = texto;
    aviso.classList.toggle('aviso--erro', ehErro);
  }

  let carregando = false;

  async function carregar() {
    if (carregando) return;

    carregando = true;

    const botao = $('#bm-atualizar');
    if (botao) botao.disabled = true;

    mostrarAviso('Carregando resultados…', false);

    try {
      let dados;

      try {
        const resposta = await fetch(URL_DADOS, {
          headers: { Accept: 'application/json' },
          cache: 'no-store'
        });

        if (!resposta.ok) {
          throw new Error('Erro HTTP ' + resposta.status);
        }

        dados = await resposta.json();
      } catch (erro) {
        limparTela();
        $('#bm-relatorio').hidden = true;
        mostrarAviso('Não foi possível carregar o benchmark: ' + erro.message, true);
        return;
      }

      const resultados = Array.isArray(dados.resultados) ? dados.resultados : [];
      const graficos = Array.isArray(dados.graficos) ? dados.graficos : [];

      if (!dados.existe || resultados.length === 0) {
        limparTela();
        $('#bm-relatorio').hidden = true;
        mostrarAviso('Ainda não há resultados. No terminal, rode: python -m benchmark.executar', false);
        return;
      }

      const volumes = volumesDe(resultados);

      montarResumo(resultados, volumes);

      const tabelas = $('#bm-tabelas');
      tabelas.replaceChildren();
      tabelas.append(montarTabela(resultados, volumes, 'Tempo (segundos)', 'tempo_s', 2));
      tabelas.append(montarTabela(resultados, volumes, 'Registros por segundo', 'registros_por_s', 0));
      tabelas.append(montarTabela(resultados, volumes, 'Pico de memória (MB)', 'ram_pico_mb', 0));

      montarGraficos(graficos, dados.gerado_em);

      $('#bm-relatorio').hidden = false;

      const quando = formatarData(dados.gerado_em);
      mostrarAviso(quando ? 'Resultados gerados em ' + quando + '.' : 'Resultados carregados.', false);
    } finally {
      carregando = false;
      if (botao) botao.disabled = false;
    }
  }

  function iniciar() {
    if (!$('#benchmark')) return;

    $('#bm-atualizar').addEventListener('click', carregar);

    carregar();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar);
  } else {
    iniciar();
  }
})();