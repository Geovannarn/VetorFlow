(function () {
  'use strict';

  const VERSAO = 'v9';
  const API_URL = '/api/clientes/';

  // Campos do cliente (o código é tratado à parte, só no cadastro).
  const CAMPOS = [
    { nome: 'razao_social', rotulo: 'Razão social', obrigatorio: true },
    { nome: 'cnpj', rotulo: 'CNPJ' },
    { nome: 'telefone', rotulo: 'Telefone' },
    { nome: 'email', rotulo: 'E-mail', tipo: 'email' },
    { nome: 'bairro', rotulo: 'Bairro' },
    { nome: 'cep', rotulo: 'CEP' },
    { nome: 'cidade', rotulo: 'Cidade' },
    { nome: 'uf', rotulo: 'UF', tamanhoMaximo: 2 },
    { nome: 'cadastro', rotulo: 'Data de cadastro', tipo: 'date' },
    { nome: 'responsavel', rotulo: 'Responsável' }
  ];

  const $ = seletor => document.querySelector(seletor);

  let clientes = [];     // lista vinda da API
  let editando = null;   // cliente em edição (null = novo cadastro)
  let excluindo = null;  // cliente que será excluído
  let ocupado = false;   // evita cliques duplos durante uma requisição


  // ---------- Utilitários ----------

  const soDigitos = valor => String(valor ?? '').replace(/\D/g, '');

  const nomeDe = cliente => cliente.razao_social || 'Cliente sem nome';

  const urlDoCliente = id => API_URL + encodeURIComponent(id) + '/';

  // Cria um elemento HTML. Usa textContent, então não há risco de injetar HTML.
  function criar(tag, atributos = {}, texto = '') {
    const elemento = document.createElement(tag);

    Object.entries(atributos).forEach(([chave, valor]) => {
      elemento.setAttribute(chave, valor);
    });

    elemento.textContent = texto;
    return elemento;
  }

  function lerCsrf() {
    const item = document.cookie
      .split('; ')
      .find(cookie => cookie.startsWith('csrftoken='));

    if (item) return decodeURIComponent(item.split('=')[1]);

    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta && meta.content) return meta.content;

    const campo = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return campo ? campo.value : '';
  }

  // Transforma o corpo de um erro da API em texto legível.
  function textoDoErro(dados, status) {
    if (typeof dados === 'string' && dados.trim() && !dados.trim().startsWith('<')) {
      return dados.trim();
    }

    if (dados && typeof dados === 'object') {
      if (typeof dados.erro === 'string') return dados.erro;
      if (typeof dados.detail === 'string') return dados.detail;

      const partes = Object.entries(dados).map(([campo, valor]) =>
        `${campo}: ${Array.isArray(valor) ? valor.join(' ') : valor}`
      );

      if (partes.length) return partes.join(' | ');
    }

    return `Erro HTTP ${status}`;
  }

  // Faz a chamada à API e devolve o JSON. Em caso de erro, lança uma exceção
  // com a mensagem enviada pelo servidor.
  async function requisitar(metodo, url, corpo = null) {
    const headers = { Accept: 'application/json' };

    if (corpo) headers['Content-Type'] = 'application/json';

    if (metodo !== 'GET') {
      const csrf = lerCsrf();
      if (csrf) headers['X-CSRFToken'] = csrf;
    }

    const resposta = await fetch(url, {
      method: metodo,
      headers,
      credentials: 'same-origin',
      body: corpo ? JSON.stringify(corpo) : undefined
    });

    const texto = await resposta.text();
    let dados = null;

    try {
      dados = texto ? JSON.parse(texto) : null;
    } catch {
      dados = texto;
    }

    if (!resposta.ok) {
      const erro = new Error(textoDoErro(dados, resposta.status));
      erro.status = resposta.status;
      throw erro;
    }

    return dados;
  }

  function mensagemDeErro(erro) {
    if (erro instanceof TypeError) {
      return 'Não foi possível conectar ao servidor. Verifique se ele está rodando.';
    }

    if (erro.status === 404) {
      return 'Cliente não encontrado. Atualize a lista e tente novamente.';
    }

    if (erro.status === 403) {
      return 'Requisição recusada (403). Recarregue a página com Ctrl+F5.';
    }

    // 400, 409 e 500: a API já manda a mensagem explicando o problema.
    return erro.message;
  }

  function definirAviso(texto, erro = false) {
    const aviso = $('#cli-status');
    aviso.textContent = texto;
    aviso.classList.toggle('aviso--erro', erro);
  }

  function mostrarErroForm(texto) {
    const aviso = $('#cli-erro-form');
    aviso.textContent = texto;
    aviso.hidden = !texto;
  }

  function mostrarErroExcluir(texto) {
    const aviso = $('#cli-erro-excluir');
    aviso.textContent = texto;
    aviso.hidden = !texto;
  }

  // Bloqueia o botão enquanto a tarefa roda e libera no final.
  async function comBloqueio(botao, tarefa) {
    if (ocupado) return;

    ocupado = true;
    botao.disabled = true;

    try {
      await tarefa();
    } finally {
      ocupado = false;
      botao.disabled = false;
    }
  }

  function abrirDialogo(dialogo) {
    if (!dialogo.open) dialogo.showModal();
  }

  function fecharDialogo(dialogo) {
    if (dialogo.open) dialogo.close();
  }


  // ---------- Formatação ----------

  function formatarValor(campo, valor) {
    if (valor === null || valor === undefined || valor === '') return '';

    const texto = String(valor);
    const digitos = soDigitos(texto);

    if (campo === 'cnpj' && digitos.length === 14) {
      return digitos.replace(
        /^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/,
        '$1.$2.$3/$4-$5'
      );
    }

    if (campo === 'cep' && digitos.length === 8) {
      return digitos.replace(/^(\d{5})(\d{3})$/, '$1-$2');
    }

    if (campo === 'cadastro' && /^\d{4}-\d{2}-\d{2}/.test(texto)) {
      const [ano, mes, dia] = texto.slice(0, 10).split('-');
      return `${dia}/${mes}/${ano}`;
    }

    return texto;
  }


  // ---------- Tabela ----------

  function criarBotao(texto, cliente, aoClicar) {
    const botao = criar(
      'button',
      {
        type: 'button',
        class: 'cli-acao',
        'aria-label': `${texto} ${nomeDe(cliente)}`
      },
      texto
    );

    botao.addEventListener('click', aoClicar);
    return botao;
  }

  function criarLinha(cliente) {
    const linha = criar('tr');

    linha.append(criar('td', { class: 'cli-mono' }, cliente.id_cliente ?? '—'));

    CAMPOS.forEach(campo => {
      const valor = formatarValor(campo.nome, cliente[campo.nome]);
      const celula = criar('td', {}, valor || '—');

      if (!valor) celula.classList.add('cli-nulo');

      linha.append(celula);
    });

    // O flex fica numa div: aplicado direto no <td>, quebraria a tabela.
    const acoes = criar('div', { class: 'cli-acoes' });

    acoes.append(
      criarBotao('Editar', cliente, () => abrirForm(cliente)),
      criarBotao('Excluir', cliente, () => abrirExcluir(cliente))
    );

    const celulaAcoes = criar('td', { class: 'cli-col-acoes' });
    celulaAcoes.append(acoes);

    linha.append(celulaAcoes);
    return linha;
  }

  // Junta todos os valores do cliente em um texto só, para a busca.
  function textoParaBusca(cliente) {
    return [
      cliente.id_cliente,
      ...CAMPOS.map(campo => formatarValor(campo.nome, cliente[campo.nome])),
      ...CAMPOS.map(campo => cliente[campo.nome])
    ].join(' | ').toLowerCase();
  }

  function renderizar() {
    const pesquisa = $('#cli-busca').value.trim().toLowerCase();

    const filtrados = clientes.filter(cliente =>
      textoParaBusca(cliente).includes(pesquisa)
    );

    $('#cli-contagem').textContent =
      `${filtrados.length} de ${clientes.length} clientes`;

    const titulos = ['Código', ...CAMPOS.map(campo => campo.rotulo), 'Ações'];

    const cabecalho = criar('tr');
    titulos.forEach(titulo => {
      cabecalho.append(criar('th', { scope: 'col' }, titulo));
    });

    const thead = criar('thead');
    thead.append(cabecalho);

    const tbody = criar('tbody');

    if (!filtrados.length) {
      const linha = criar('tr');
      linha.append(
        criar(
          'td',
          { colspan: titulos.length, class: 'cli-vazio' },
          'Nenhum cliente encontrado.'
        )
      );
      tbody.append(linha);
    }

    filtrados.forEach(cliente => tbody.append(criarLinha(cliente)));

    $('#cli-tabela').replaceChildren(thead, tbody);
  }

  async function carregar() {
    try {
      const resposta = await requisitar('GET', API_URL);

      clientes = Array.isArray(resposta) ? resposta : resposta?.results || [];

      renderizar();
      definirAviso('Clientes carregados com sucesso.');
      return true;

    } catch (erro) {
      console.error('Falha ao carregar clientes:', erro);
      definirAviso(mensagemDeErro(erro), true);
      return false;
    }
  }


  // ---------- Formulário (novo / editar) ----------

  function criarCampo(id, rotulo, atributos) {
    const grupo = criar('div', { class: 'cli-campo' });

    grupo.append(
      criar('label', { class: 'campo__rotulo', for: id }, rotulo),
      criar('input', { class: 'campo__entrada', id, ...atributos })
    );

    return grupo;
  }

  function montarFormulario(cliente) {
    const container = $('#cli-campos');
    container.replaceChildren();

    if (!cliente) {
      container.append(
        criarCampo('cli-c-id_cliente', 'Código do cliente', {
          name: 'id_cliente',
          type: 'text',
          required: 'required',
          autocomplete: 'off'
        })
      );
    }

    CAMPOS.forEach(campo => {
      const atributos = {
        name: campo.nome,
        type: campo.tipo || 'text',
        autocomplete: 'off'
      };

      if (campo.tamanhoMaximo) atributos.maxlength = campo.tamanhoMaximo;
      if (campo.obrigatorio) atributos.required = 'required';

      const grupo = criarCampo('cli-c-' + campo.nome, campo.rotulo, atributos);
      const valor = String(cliente?.[campo.nome] ?? '');

      grupo.querySelector('input').value =
        campo.tipo === 'date' ? valor.slice(0, 10) : valor;

      container.append(grupo);
    });
  }

  function abrirForm(cliente = null) {
    editando = cliente;

    $('#cli-dialogo-titulo').textContent =
      cliente ? 'Editar cliente' : 'Novo cliente';

    montarFormulario(cliente);
    mostrarErroForm('');

    abrirDialogo($('#cli-dialogo'));

    const primeiro = $('#cli-campos input');
    if (primeiro) primeiro.focus();
  }

  function coletarDados() {
    const dados = {};

    const campoId = $('#cli-c-id_cliente');
    if (campoId) dados.id_cliente = campoId.value.trim();

    CAMPOS.forEach(campo => {
      const texto = $('#cli-c-' + campo.nome).value.trim();

      dados[campo.nome] = texto === '' && !campo.obrigatorio ? null : texto;
    });

    if (dados.uf) dados.uf = dados.uf.toUpperCase();

    return dados;
  }

  function validar(dados, novo) {
    if (novo && !dados.id_cliente) {
      return 'Informe o código do cliente.';
    }

    if (!dados.razao_social) {
      return 'Informe a razão social do cliente.';
    }

    if (novo && clientes.some(c => String(c.id_cliente) === dados.id_cliente)) {
      return 'Já existe um cliente cadastrado com esse código.';
    }

    return '';
  }

  async function salvar(evento) {
    evento.preventDefault();

    const alvo = editando;
    const dados = coletarDados();

    const problema = validar(dados, !alvo);

    if (problema) {
      mostrarErroForm(problema);
      return;
    }

    await comBloqueio($('#cli-salvar'), async () => {
      try {
        if (alvo) {
          await requisitar('PUT', urlDoCliente(alvo.id_cliente), dados);
        } else {
          await requisitar('POST', API_URL, dados);
        }

        fecharDialogo($('#cli-dialogo'));

        if (await carregar()) {
          definirAviso(
            alvo
              ? 'Cliente atualizado com sucesso.'
              : 'Cliente cadastrado com sucesso.'
          );
        }

      } catch (erro) {
        console.error('Falha ao salvar cliente:', erro);
        mostrarErroForm(mensagemDeErro(erro));
      }
    });
  }


  // ---------- Exclusão ----------

  function abrirExcluir(cliente) {
    excluindo = cliente;

    $('#cli-confirmar-texto').textContent =
      `Deseja realmente excluir "${nomeDe(cliente)}" (código ${cliente.id_cliente})?`;

    mostrarErroExcluir('');
    abrirDialogo($('#cli-confirmar'));
  }

  async function excluir() {
    const alvo = excluindo;

    if (!alvo) return;

    await comBloqueio($('#cli-excluir'), async () => {
      try {
        await requisitar('DELETE', urlDoCliente(alvo.id_cliente));

        fecharDialogo($('#cli-confirmar'));

        if (await carregar()) {
          definirAviso('Cliente excluído com sucesso.');
        }

      } catch (erro) {
        console.error('Falha ao excluir cliente:', erro);
        mostrarErroExcluir(mensagemDeErro(erro));
      }
    });
  }


  // ---------- Início ----------

  function iniciar() {
    if (!$('#clientes')) return;

    console.info('clientes.js ' + VERSAO + ' carregado');

    $('#cli-novo').addEventListener('click', () => abrirForm());
    $('#cli-busca').addEventListener('input', renderizar);
    $('#cli-form').addEventListener('submit', salvar);
    $('#cli-cancelar').addEventListener('click', () => fecharDialogo($('#cli-dialogo')));
    $('#cli-dialogo').addEventListener('close', () => { editando = null; });
    $('#cli-excluir').addEventListener('click', excluir);
    $('#cli-cancelar-excluir').addEventListener('click', () => fecharDialogo($('#cli-confirmar')));
    $('#cli-confirmar').addEventListener('close', () => { excluindo = null; });

    carregar();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar);
  } else {
    iniciar();
  }

})();