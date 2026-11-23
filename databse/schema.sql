CREATE TABLE IF NOT EXISTS usuarios (
    id_cliente   VARCHAR(20)  PRIMARY KEY,
    razao_social VARCHAR(200) NOT NULL,
    cnpj         VARCHAR(18),
    telefone     VARCHAR(20),
    email        VARCHAR(150),
    bairro       VARCHAR(100),
    cep          VARCHAR(8),
    cidade       VARCHAR(100),
    uf           CHAR(2),
    cadastro     DATE,
    responsavel  VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS benchmark_clientes (
    id_cliente            TEXT,
    nome                  TEXT,
    documento             TEXT,
    cep                   TEXT,
    endereco              TEXT,
    regiao_administrativa TEXT
);