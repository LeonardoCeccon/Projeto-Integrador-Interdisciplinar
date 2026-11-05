-- =====================================================================
-- LabAgenda - Projeto físico (MySQL 8.0+, InnoDB, utf8mb4)
-- Execução:  mysql -u root -p < database/schema.sql
-- =====================================================================
DROP DATABASE IF EXISTS labagenda;
CREATE DATABASE labagenda
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE labagenda;

-- ---------------------------------------------------------- usuario
CREATE TABLE usuario (
  id_usuario  INT UNSIGNED NOT NULL AUTO_INCREMENT,
  nome        VARCHAR(100) NOT NULL,
  email       VARCHAR(120) NOT NULL,
  senha_hash  VARCHAR(255) NOT NULL,
  perfil      ENUM('ALUNO','PROFESSOR','TECNICO') NOT NULL DEFAULT 'ALUNO',
  ativo       TINYINT(1)   NOT NULL DEFAULT 1,
  criado_em   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT pk_usuario PRIMARY KEY (id_usuario),
  CONSTRAINT uq_usuario_email UNIQUE (email),
  CONSTRAINT ck_usuario_ativo CHECK (ativo IN (0,1))
) ENGINE=InnoDB;

-- ------------------------------------------------------ laboratorio
CREATE TABLE laboratorio (
  id_laboratorio INT UNSIGNED NOT NULL AUTO_INCREMENT,
  nome           VARCHAR(80)  NOT NULL,
  localizacao    VARCHAR(120) NOT NULL,
  capacidade     SMALLINT UNSIGNED NOT NULL,
  ativo          TINYINT(1)   NOT NULL DEFAULT 1,
  excluido       TINYINT(1)   NOT NULL DEFAULT 0,        -- exclusão lógica (v2.1)
  excluido_em    DATETIME     NULL,
  excluido_por   INT UNSIGNED NULL,
  motivo_exclusao VARCHAR(200) NULL,
  CONSTRAINT pk_laboratorio PRIMARY KEY (id_laboratorio),
  CONSTRAINT uq_laboratorio_nome UNIQUE (nome),
  CONSTRAINT ck_laboratorio_cap CHECK (capacidade > 0),
  CONSTRAINT ck_laboratorio_ativo CHECK (ativo IN (0,1)),
  CONSTRAINT ck_laboratorio_excl CHECK (excluido IN (0,1)),
  CONSTRAINT fk_laboratorio_excl_por FOREIGN KEY (excluido_por)
    REFERENCES usuario (id_usuario) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

-- ------------------------------------------------------ equipamento
CREATE TABLE equipamento (
  id_equipamento    INT UNSIGNED NOT NULL AUTO_INCREMENT,
  id_laboratorio    INT UNSIGNED NOT NULL,
  nome              VARCHAR(80) NOT NULL,
  numero_patrimonio VARCHAR(30) NOT NULL,
  status            ENUM('DISPONIVEL','MANUTENCAO','BAIXADO') NOT NULL DEFAULT 'DISPONIVEL',
  excluido          TINYINT(1)   NOT NULL DEFAULT 0,      -- exclusão lógica (v2.1)
  excluido_em       DATETIME     NULL,
  excluido_por      INT UNSIGNED NULL,
  motivo_exclusao   VARCHAR(200) NULL,
  CONSTRAINT pk_equipamento PRIMARY KEY (id_equipamento),
  CONSTRAINT uq_equipamento_patrimonio UNIQUE (numero_patrimonio),
  CONSTRAINT ck_equipamento_excl CHECK (excluido IN (0,1)),
  CONSTRAINT fk_equipamento_excl_por FOREIGN KEY (excluido_por)
    REFERENCES usuario (id_usuario) ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT fk_equipamento_lab FOREIGN KEY (id_laboratorio)
    REFERENCES laboratorio (id_laboratorio) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;
CREATE INDEX idx_equipamento_lab ON equipamento (id_laboratorio);

-- ---------------------------------------------------------- reserva
CREATE TABLE reserva (
  id_reserva     INT UNSIGNED NOT NULL AUTO_INCREMENT,
  id_usuario     INT UNSIGNED NOT NULL,
  id_laboratorio INT UNSIGNED NOT NULL,
  data_reserva   DATE NOT NULL,
  hora_inicio    TIME NOT NULL,
  hora_fim       TIME NOT NULL,
  finalidade     VARCHAR(200) NOT NULL,
  status         ENUM('PENDENTE','APROVADA','RECUSADA','CANCELADA') NOT NULL DEFAULT 'PENDENTE',
  id_avaliador   INT UNSIGNED NULL,
  motivo_recusa  VARCHAR(200) NULL,
  criada_em      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT pk_reserva PRIMARY KEY (id_reserva),
  CONSTRAINT fk_reserva_usuario FOREIGN KEY (id_usuario)
    REFERENCES usuario (id_usuario) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_reserva_lab FOREIGN KEY (id_laboratorio)
    REFERENCES laboratorio (id_laboratorio) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_reserva_avaliador FOREIGN KEY (id_avaliador)
    REFERENCES usuario (id_usuario) ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT ck_reserva_horas CHECK (hora_fim > hora_inicio)
) ENGINE=InnoDB;
-- acelera a verificação de conflito de horário (RN05)
CREATE INDEX idx_reserva_lab_data ON reserva (id_laboratorio, data_reserva, hora_inicio);
CREATE INDEX idx_reserva_usuario  ON reserva (id_usuario, data_reserva);
CREATE INDEX idx_reserva_status   ON reserva (status);

-- ------------------------------------------------ reserva_equipamento (N:N)
CREATE TABLE reserva_equipamento (
  id_reserva     INT UNSIGNED NOT NULL,
  id_equipamento INT UNSIGNED NOT NULL,
  CONSTRAINT pk_reserva_equipamento PRIMARY KEY (id_reserva, id_equipamento),
  CONSTRAINT fk_re_reserva FOREIGN KEY (id_reserva)
    REFERENCES reserva (id_reserva) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_re_equip FOREIGN KEY (id_equipamento)
    REFERENCES equipamento (id_equipamento) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;
CREATE INDEX idx_re_equip ON reserva_equipamento (id_equipamento);

-- -------------------------------------------------------- ocorrencia
CREATE TABLE ocorrencia (
  id_ocorrencia  INT UNSIGNED NOT NULL AUTO_INCREMENT,
  id_reserva     INT UNSIGNED NOT NULL,
  id_equipamento INT UNSIGNED NULL,
  descricao      VARCHAR(500) NOT NULL,
  registrada_em  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT pk_ocorrencia PRIMARY KEY (id_ocorrencia),
  CONSTRAINT fk_oc_reserva FOREIGN KEY (id_reserva)
    REFERENCES reserva (id_reserva) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_oc_equip FOREIGN KEY (id_equipamento)
    REFERENCES equipamento (id_equipamento) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;
CREATE INDEX idx_oc_reserva ON ocorrencia (id_reserva);

-- ----------------------------------------- historico_alteracao (v2.2)
-- Registro de quem alterou laboratórios e equipamentos, e o que mudou.
CREATE TABLE historico_alteracao (
  id_historico   INT UNSIGNED NOT NULL AUTO_INCREMENT,
  entidade       ENUM('LABORATORIO','EQUIPAMENTO') NOT NULL,
  id_entidade    INT UNSIGNED NOT NULL,
  referencia     VARCHAR(120) NOT NULL,          -- nome do item na época da alteração
  acao           VARCHAR(30)  NOT NULL,          -- CADASTRO, EDICAO, SITUACAO, EXCLUSAO, REATIVACAO, MANUTENCAO
  detalhe        VARCHAR(500) NULL,
  id_usuario     INT UNSIGNED NULL,
  registrado_em  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT pk_historico PRIMARY KEY (id_historico),
  CONSTRAINT fk_historico_usuario FOREIGN KEY (id_usuario)
    REFERENCES usuario (id_usuario) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;
CREATE INDEX idx_historico_entidade ON historico_alteracao (entidade, id_entidade);
CREATE INDEX idx_historico_data ON historico_alteracao (registrado_em);

-- ------------------------------------------------------------ visão
CREATE OR REPLACE VIEW vw_uso_laboratorio AS
SELECT l.id_laboratorio, l.nome AS laboratorio, r.data_reserva,
       COUNT(*) AS total_reservas,
       SUM(TIME_TO_SEC(TIMEDIFF(r.hora_fim, r.hora_inicio))) / 3600 AS horas_uso
FROM reserva r
JOIN laboratorio l ON l.id_laboratorio = r.id_laboratorio
WHERE r.status = 'APROVADA'
GROUP BY l.id_laboratorio, l.nome, r.data_reserva;

-- ------------------------------------------- usuário da aplicação (mínimo privilégio)
-- Troque a senha antes de executar em qualquer ambiente real.
CREATE USER IF NOT EXISTS 'labagenda_app'@'localhost' IDENTIFIED BY 'troque-esta-senha';
GRANT SELECT, INSERT, UPDATE ON labagenda.* TO 'labagenda_app'@'localhost';
FLUSH PRIVILEGES;
