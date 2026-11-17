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

  function formatarNumero(valor, casas) {
    if (valor === null || valor === undefined || Number.isNaN(Number(valor))) {
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
    const tabela = criar('table', null, 'cli-tabela');

    const cabecalho = criar('tr');
    cabecalho.append(criar('th', 'Etapa'));

    for (const volume of volumes) {
      cabecalho.append(criar('th', rotuloVolume(volume)));
    }

    const topo = criar('thead');
    topo.append(cabecalho);
    tabela.append(topo);

    const corpo = criar('tbody');

    for (const definicao of LINHAS_DAS_TABELAS) {
      const linhaTabela = criar('tr');
      linhaTabela.append(criar('th', definicao.rotulo));

      let temValor = false;

      for (const volume of volumes) {
        const dados = acharLinha(resultados, definicao.etapa, definicao.variante, volume);
        const valor = dados ? dados[campo] : null;

        if (valor !== null && valor !== undefined) temValor = true;

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

      if (principal && linha.volume === maior && !linha.ignorado && linha.ram_pico_mb !== null) {
        if (picoMemoria === null || linha.ram_pico_mb > picoMemoria) {
          picoMemoria = linha.ram_pico_mb;
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
      adicionarResumo(lista, 'Rejeitados', formatarNumero(transformacao.taxa_rejeicao_pct, 1) + '%', 'resumo__rejeitadas');
    }
  }

  function montarGraficos(graficos, geradoEm) {
    const area = $('#bm-graficos');
    area.replaceChildren();

    for (const grafico of graficos) {
      const figura = criar('figure', null, 'bm-figura');
      const imagem = document.createElement('img');

      imagem.src = grafico.url + '?v=' + geradoEm;
      imagem.alt = TITULOS_GRAFICOS[grafico.nome] || grafico.nome;
      imagem.loading = 'lazy';

      figura.append(imagem);
      figura.append(criar('figcaption', TITULOS_GRAFICOS[grafico.nome] || grafico.nome));
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

  async function carregar() {
    mostrarAviso('Carregando resultados…', false);

    let dados;

    try {
      const resposta = await fetch(URL_DADOS, { headers: { Accept: 'application/json' } });

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

    if (!dados.existe) {
      limparTela();
      $('#bm-relatorio').hidden = true;
      mostrarAviso('Ainda não há resultados. No terminal, rode: python -m benchmark.executar', false);
      return;
    }

    const volumes = volumesDe(dados.resultados);

    montarResumo(dados.resultados, volumes);

    const tabelas = $('#bm-tabelas');
    tabelas.replaceChildren();
    tabelas.append(montarTabela(dados.resultados, volumes, 'Tempo (segundos)', 'tempo_s', 2));
    tabelas.append(montarTabela(dados.resultados, volumes, 'Registros por segundo', 'registros_por_s', 0));
    tabelas.append(montarTabela(dados.resultados, volumes, 'Pico de memória (MB)', 'ram_pico_mb', 0));

    montarGraficos(dados.graficos, dados.gerado_em);

    $('#bm-relatorio').hidden = false;
    mostrarAviso('Resultados gerados em ' + new Date(dados.gerado_em * 1000).toLocaleString('pt-BR') + '.', false);
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