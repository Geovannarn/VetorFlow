(function () {
  'use strict';

  const VERSAO = 'v6';
  const API_URL = '/api/clientes/';
  const TEMPO_LIMITE_MS = 10000;

  const CAMPOS = [
    { nome: 'razao_social', rotulo: 'Razão social', obrigatorio: true },
    { nome: 'cnpj', rotulo: 'CNPJ' },
    { nome: 'telefone', rotulo: 'Telefone' },
    { nome: 'email', rotulo: 'E-mail', tipo: 'email' },
    { nome: 'bairro', rotulo: 'Bairro' },
    { nome: 'cep', rotulo: 'CEP' },
    { nome: 'cidade', rotulo: 'Cidade' },
    { nome: 'uf', rotulo: 'UF' },
    { nome: 'cadastro', rotulo: 'Data de cadastro', tipo: 'date' },
    { nome: 'responsavel', rotulo: 'Responsável' }
  ];

  const $ = (seletor, raiz = document) =>
    raiz.querySelector(seletor);

  let clientes = [];
  let excluindo = null;
  let ocupado = false;

  const soDigitos = valor =>
    String(valor ?? '').replace(/\D/g, '');

  function idValido(valor) {
    return valor !== null &&
      valor !== undefined &&
      String(valor).trim() !== '';
  }

  // Recupera o código do cliente. Aceita só variações de "id_cliente":
  // adivinhar outra coluna poderia excluir o cliente errado.
  function obterIdCliente(cliente) {
    if (!cliente || typeof cliente !== 'object') return null;

    const chave = Object.keys(cliente).find(
      nome => nome.toLowerCase().replace(/[^a-z]/g, '') === 'idcliente'
    );

    if (chave && idValido(cliente[chave])) return cliente[chave];

    console.warn('Cliente sem id_cliente. Chaves recebidas:', Object.keys(cliente), cliente);
    return null;
  }

  // Define por qual coluna o cliente será excluído.
  // Normal: id_cliente. Linhas importadas sem id_cliente usam a coluna "id".
  function obterAlvo(cliente) {
    const idCliente = obterIdCliente(cliente);

    if (idValido(idCliente)) {
      return { campo: 'id_cliente', valor: idCliente };
    }

    if (cliente && idValido(cliente.id)) {
      return { campo: 'id', valor: cliente.id };
    }

    return null;
  }

  function chavesDe(cliente) {
    return cliente && typeof cliente === 'object'
      ? Object.keys(cliente).join(', ')
      : '(registro inválido)';
  }

  function lerCookie(nome) {
    const cookie = document.cookie
      .split('; ')
      .find(item => item.startsWith(nome + '='));

    return cookie
      ? decodeURIComponent(cookie.slice(nome.length + 1))
      : '';
  }

  function urlDoCliente(valor, campo = 'id_cliente') {
    const url = API_URL + encodeURIComponent(valor) + '/';

    return campo === 'id' ? url + '?por=id' : url;
  }

  async function requisitar(metodo, url, corpo = null) {
    const headers = {
      Accept: 'application/json'
    };

    if (corpo) {
      headers['Content-Type'] = 'application/json';
    }

    if (!['GET', 'OPTIONS', 'HEAD'].includes(metodo)) {
      const csrf = lerCookie('csrftoken');

      if (csrf) {
        headers['X-CSRFToken'] = csrf;
      }
    }

    const controller = new AbortController();

    const timer = setTimeout(
      () => controller.abort(),
      TEMPO_LIMITE_MS
    );

    try {
      const resposta = await fetch(url, {
        method: metodo,
        headers,
        credentials: 'same-origin',
        body: corpo ? JSON.stringify(corpo) : undefined,
        signal: controller.signal
      });

      const texto = await resposta.text();

      let dados = null;

      if (texto) {
        try {
          dados = JSON.parse(texto);
        } catch {
          dados = texto;
        }
      }

      if (!resposta.ok) {
        const erro = new Error(
          dados?.erro ||
          dados?.detail ||
          `Erro HTTP ${resposta.status}`
        );

        erro.status = resposta.status;
        erro.dados = dados;

        throw erro;
      }

      return dados;

    } finally {
      clearTimeout(timer);
    }
  }

  function nomeDe(cliente) {
    return cliente.razao_social || 'Cliente sem nome';
  }

  function mensagemDeErro(erro) {
    if (erro.name === 'AbortError') {
      return 'A requisição demorou demais. Tente novamente.';
    }

    if (erro.status === 404) {
      return 'Cliente não encontrado. Atualize a lista e tente novamente.';
    }

    if (erro.status === 409) {
      return erro.dados?.erro ||
        'Já existe um cliente cadastrado com esse código.';
    }

    if (erro.status === 400) {
      if (erro.dados && typeof erro.dados === 'object') {
        return erro.dados.erro ||
          erro.dados.detail ||
          JSON.stringify(erro.dados);
      }

      return 'Os dados enviados não foram aceitos.';
    }

    if (erro.status === 403) {
      return 'Requisição recusada (403). Recarregue a página com Ctrl+F5 e tente novamente.';
    }

    if (erro.status >= 500) {
      if (erro.dados && erro.dados.erro) return erro.dados.erro;

      return `Erro interno do servidor (HTTP ${erro.status}). Veja o erro completo no terminal do Django.`;
    }

    return erro.message || 'Não foi possível concluir a operação.';
  }

  function definirAviso(texto, erro = false) {
    const aviso = $('#cli-status');

    aviso.textContent = texto;
    aviso.classList.toggle('aviso--erro', erro);
  }

  function formatarValor(campo, valor) {
    if (valor === null || valor === undefined || valor === '') {
      return '';
    }

    if (campo === 'cnpj') {
      const d = soDigitos(valor);

      if (d.length === 14) {
        return d.replace(
          /^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/,
          '$1.$2.$3/$4-$5'
        );
      }
    }

    if (campo === 'cep') {
      const d = soDigitos(valor);

      if (d.length === 8) {
        return d.replace(/^(\d{5})(\d{3})$/, '$1-$2');
      }
    }

    return String(valor);
  }

  function criarElemento(tag, atributos = {}, texto = null) {
    const elemento = document.createElement(tag);

    Object.entries(atributos).forEach(([chave, valor]) => {
      if (valor !== null && valor !== undefined) {
        elemento.setAttribute(chave, valor);
      }
    });

    if (texto !== null) {
      elemento.textContent = texto;
    }

    return elemento;
  }

  function renderizar() {
    const tabela = $('#cli-tabela');
    const busca = $('#cli-busca');
    const contagem = $('#cli-contagem');

    const pesquisa = busca.value
      .trim()
      .toLowerCase();

    const filtrados = clientes.filter(cliente => {
      const valores = [
        obterIdCliente(cliente),
        ...CAMPOS.map(campo => cliente[campo.nome])
      ];

      return valores.some(valor =>
        String(valor ?? '')
          .toLowerCase()
          .includes(pesquisa)
      );
    });

    contagem.textContent =
      `${filtrados.length} de ${clientes.length} clientes`;

    tabela.replaceChildren();

    const cabecalho = criarElemento('tr');

    CAMPOS.forEach(campo => {
      cabecalho.append(
        criarElemento('th', { scope: 'col' }, campo.rotulo)
      );
    });

    cabecalho.append(
      criarElemento('th', { scope: 'col' }, 'Ações')
    );

    const thead = criarElemento('thead');
    thead.append(cabecalho);

    tabela.append(thead);

    const corpo = criarElemento('tbody');

    if (!filtrados.length) {
      const linha = criarElemento('tr');

      const celula = criarElemento(
        'td',
        {
          colspan: CAMPOS.length + 1,
          class: 'cli-vazio'
        },
        'Nenhum cliente encontrado.'
      );

      linha.append(celula);
      corpo.append(linha);

    } else {
      filtrados.forEach(cliente => {
        const linha = criarElemento('tr');

        CAMPOS.forEach(campo => {
          const valor = formatarValor(
            campo.nome,
            cliente[campo.nome]
          );

          const celula = criarElemento(
            'td',
            {},
            valor || '—'
          );

          if (!valor) {
            celula.classList.add('cli-nulo');
          }

          linha.append(celula);
        });

        const acoes = criarElemento('td', {
          class: 'cli-acoes'
        });

        const excluir = criarElemento(
          'button',
          {
            type: 'button',
            class: 'cli-acao'
          },
          'Excluir'
        );

        excluir.addEventListener('click', () => {
          abrirExcluir(cliente);
        });

        acoes.append(excluir);
        linha.append(acoes);
        corpo.append(linha);
      });
    }

    tabela.append(corpo);
  }

  async function carregar() {
    try {
      const resposta = await requisitar('GET', API_URL);

      clientes = Array.isArray(resposta)
        ? resposta
        : resposta.results || [];

      renderizar();

      definirAviso('Clientes carregados com sucesso. (clientes.js ' + VERSAO + ')');

    } catch (erro) {
      console.error('Falha ao carregar clientes:', erro);
      definirAviso(mensagemDeErro(erro), true);
    }
  }

  function montarFormulario(cliente = null) {
    const container = $('#cli-campos');

    container.replaceChildren();

    // O código é solicitado somente no cadastro.
    if (!cliente) {
      const grupoId = criarElemento('div', {
        class: 'cli-campo'
      });

      const labelId = criarElemento(
        'label',
        {
          class: 'campo__rotulo',
          for: 'cli-c-id_cliente'
        },
        'Código do cliente'
      );

      const inputId = criarElemento('input', {
        class: 'campo__entrada',
        id: 'cli-c-id_cliente',
        name: 'id_cliente',
        type: 'text',
        required: 'required'
      });

      grupoId.append(labelId, inputId);
      container.append(grupoId);
    }

    CAMPOS.forEach(campo => {
      const grupo = criarElemento('div', {
        class: 'cli-campo'
      });

      const id = 'cli-c-' + campo.nome;

      const label = criarElemento(
        'label',
        {
          class: 'campo__rotulo',
          for: id
        },
        campo.rotulo
      );

      const input = criarElemento('input', {
        class: 'campo__entrada',
        id,
        name: campo.nome,
        type: campo.tipo || 'text'
      });

      if (campo.obrigatorio) {
        input.required = true;
      }

      const valor = cliente?.[campo.nome] ?? '';

      input.value = campo.tipo === 'date'
        ? String(valor).slice(0, 10)
        : String(valor);

      const erro = criarElemento('p', {
        class: 'campo__erro',
        id: id + '-erro',
        role: 'alert',
        hidden: ''
      });

      grupo.append(label, input, erro);
      container.append(grupo);
    });
  }

  function abrirForm(cliente = null) {
    $('#cli-dialogo-titulo').textContent =
      'Novo cliente';

    montarFormulario(cliente);

    $('#cli-erro-form').hidden = true;
    $('#cli-erro-form').textContent = '';

    $('#cli-dialogo').showModal();
  }

  function coletarDados() {
    const dados = {};

    {
      dados.id_cliente =
        $('#cli-c-id_cliente').value.trim();
    }

    CAMPOS.forEach(campo => {
      const entrada = $('#cli-c-' + campo.nome);

      dados[campo.nome] = entrada.value.trim();
    });

    return dados;
  }

  function mostrarErroForm(texto) {
    $('#cli-erro-form').textContent = texto;
    $('#cli-erro-form').hidden = false;
  }

  async function salvar(evento) {
    evento.preventDefault();

    if (ocupado) return;

    const dados = coletarDados();

    if (!idValido(dados.id_cliente)) {
      mostrarErroForm('Informe o código do cliente.');
      return;
    }

    if (!dados.razao_social) {
      mostrarErroForm('Informe a razão social do cliente.');
      return;
    }

    const codigoExiste = clientes.some(cliente =>
      String(obterIdCliente(cliente)) === String(dados.id_cliente)
    );

    if (codigoExiste) {
      mostrarErroForm('Já existe um cliente cadastrado com esse código.');
      return;
    }

    if (dados.cadastro === '') {
      dados.cadastro = null;
    }

    ocupado = true;
    $('#cli-salvar').disabled = true;

    try {
      await requisitar('POST', API_URL, dados);

      $('#cli-dialogo').close();

      await carregar();

      definirAviso('Cliente cadastrado com sucesso.');

    } catch (erro) {
      console.error('Falha ao salvar cliente:', erro, erro.dados);
      mostrarErroForm(mensagemDeErro(erro));

    } finally {
      ocupado = false;
      $('#cli-salvar').disabled = false;
    }
  }

  function descreverAlvo(cliente) {
    const alvo = obterAlvo(cliente);

    const rotulo = !alvo
      ? 'sem código'
      : alvo.campo === 'id_cliente'
        ? `código ${alvo.valor}`
        : `registro interno nº ${alvo.valor}, sem código de cliente`;

    return `Deseja realmente excluir "${nomeDe(cliente)}" (${rotulo})?`;
  }

  function abrirExcluir(cliente) {
    excluindo = cliente;

    $('#cli-confirmar-texto').textContent =
      descreverAlvo(cliente);

    $('#cli-erro-excluir').hidden = true;

    $('#cli-confirmar').showModal();
  }

  async function excluir() {
    if (ocupado || !excluindo) return;

    const alvo = obterAlvo(excluindo);

    if (!alvo) {
      $('#cli-erro-excluir').textContent =
        'Este registro não tem id_cliente nem id. Chaves recebidas da API: ' + chavesDe(excluindo);

      $('#cli-erro-excluir').hidden = false;
      return;
    }

    const url = urlDoCliente(alvo.valor, alvo.campo);

    ocupado = true;
    $('#cli-excluir').disabled = true;

    try {
      await requisitar('DELETE', url);

      $('#cli-confirmar').close();
      excluindo = null;

      await carregar();

      definirAviso('Cliente excluído com sucesso.');

    } catch (erro) {
      console.error('Falha ao excluir cliente:', url, erro, erro.dados);

      let texto = mensagemDeErro(erro);

      if (erro.status === 404) {
        texto = typeof erro.dados === 'string'
          ? `A rota não existe na API: DELETE ${url} (404). Confira api/routes.py.`
          : `A API não achou ${alvo.campo} = "${alvo.valor}" na tabela (DELETE ${url}).`;
      }

      $('#cli-erro-excluir').textContent = texto;
      $('#cli-erro-excluir').hidden = false;

    } finally {
      ocupado = false;
      $('#cli-excluir').disabled = false;
    }
  }

  function iniciar() {
    console.info('clientes.js ' + VERSAO + ' carregado');
    if (!$('#clientes')) return;

    $('#cli-novo').addEventListener('click', () => {
      abrirForm(null);
    });

    $('#cli-busca').addEventListener('input', renderizar);

    $('#cli-form').addEventListener('submit', salvar);

    $('#cli-cancelar').addEventListener('click', () => {
      $('#cli-dialogo').close();
    });

    $('#cli-excluir').addEventListener('click', excluir);

    $('#cli-cancelar-excluir').addEventListener('click', () => {
      $('#cli-confirmar').close();
      excluindo = null;
    });

    carregar();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar);
  } else {
    iniciar();
  }

})();