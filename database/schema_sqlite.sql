-- Espelho SIMPLIFICADO do schema.sql, usado apenas em testes automatizados
-- e em desenvolvimento sem servidor MySQL. A fonte de verdade é schema.sql.
  CREATE TABLE usuario (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL, email TEXT NOT NULL UNIQUE, senha_hash TEXT NOT NULL,
    perfil TEXT NOT NULL DEFAULT 'ALUNO' CHECK (perfil IN ('ALUNO','PROFESSOR','TECNICO')),
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
  CREATE TABLE laboratorio (
    id_laboratorio INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE, localizacao TEXT NOT NULL,
    capacidade INTEGER NOT NULL CHECK (capacidade > 0),
    ativo INTEGER NOT NULL DEFAULT 1);
  CREATE TABLE equipamento (
    id_equipamento INTEGER PRIMARY KEY AUTOINCREMENT,
    id_laboratorio INTEGER NOT NULL REFERENCES laboratorio(id_laboratorio),
    nome TEXT NOT NULL, numero_patrimonio TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'DISPONIVEL' CHECK (status IN ('DISPONIVEL','MANUTENCAO','BAIXADO')));
  CREATE TABLE reserva (
    id_reserva INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL REFERENCES usuario(id_usuario),
    id_laboratorio INTEGER NOT NULL REFERENCES laboratorio(id_laboratorio),
    data_reserva TEXT NOT NULL, hora_inicio TEXT NOT NULL, hora_fim TEXT NOT NULL,
    finalidade TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDENTE' CHECK (status IN ('PENDENTE','APROVADA','RECUSADA','CANCELADA')),
    id_avaliador INTEGER REFERENCES usuario(id_usuario), motivo_recusa TEXT,
    criada_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (hora_fim > hora_inicio));
  CREATE TABLE reserva_equipamento (
    id_reserva INTEGER NOT NULL REFERENCES reserva(id_reserva) ON DELETE CASCADE,
    id_equipamento INTEGER NOT NULL REFERENCES equipamento(id_equipamento),
    PRIMARY KEY (id_reserva, id_equipamento));
  CREATE TABLE ocorrencia (
    id_ocorrencia INTEGER PRIMARY KEY AUTOINCREMENT,
    id_reserva INTEGER NOT NULL REFERENCES reserva(id_reserva) ON DELETE CASCADE,
    id_equipamento INTEGER REFERENCES equipamento(id_equipamento),
    descricao TEXT NOT NULL,
    registrada_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
