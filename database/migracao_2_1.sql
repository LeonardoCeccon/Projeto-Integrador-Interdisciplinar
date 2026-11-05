-- Migração 2.0 -> 2.1: exclusão lógica de equipamentos e laboratórios.
-- Para bancos que JÁ existem (ex.: Aiven). Em banco novo, use schema.sql.
-- Execute UMA vez:  python database/aplicar_schema.py database/migracao_2_1.sql
-- Não apaga nem altera nenhum dado existente.
ALTER TABLE laboratorio
  ADD COLUMN excluido TINYINT(1) NOT NULL DEFAULT 0,
  ADD COLUMN excluido_em DATETIME NULL,
  ADD COLUMN excluido_por INT UNSIGNED NULL,
  ADD COLUMN motivo_exclusao VARCHAR(200) NULL,
  ADD CONSTRAINT ck_laboratorio_excl CHECK (excluido IN (0,1)),
  ADD CONSTRAINT fk_laboratorio_excl_por FOREIGN KEY (excluido_por)
    REFERENCES usuario (id_usuario) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE equipamento
  ADD COLUMN excluido TINYINT(1) NOT NULL DEFAULT 0,
  ADD COLUMN excluido_em DATETIME NULL,
  ADD COLUMN excluido_por INT UNSIGNED NULL,
  ADD COLUMN motivo_exclusao VARCHAR(200) NULL,
  ADD CONSTRAINT ck_equipamento_excl CHECK (excluido IN (0,1)),
  ADD CONSTRAINT fk_equipamento_excl_por FOREIGN KEY (excluido_por)
    REFERENCES usuario (id_usuario) ON UPDATE CASCADE ON DELETE SET NULL;
