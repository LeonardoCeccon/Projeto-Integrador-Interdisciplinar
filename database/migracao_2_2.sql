-- Migração 2.1 -> 2.2: histórico de alterações de laboratórios e equipamentos.
-- Execute UMA vez:  python database/aplicar_schema.py database/migracao_2_2.sql
-- Cria uma tabela nova; não altera nenhum dado existente.

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
