# Dicionário de dados – LabAgenda (MySQL 8)

Legenda: **PK** chave primária · **FK** chave estrangeira · **UK** valor único · **NN** não nulo · **AI** auto incremento.

## usuario
Pessoas que acessam o sistema.
| Coluna | Tipo | Restrições | Descrição |
|---|---|---|---|
| id_usuario | INT UNSIGNED | PK, AI | Identificador |
| nome | VARCHAR(100) | NN | Nome completo |
| email | VARCHAR(120) | NN, UK | Login; gravado em minúsculas |
| senha_hash | VARCHAR(255) | NN | Hash da senha (nunca a senha) |
| perfil | ENUM('ALUNO','PROFESSOR','TECNICO') | NN, padrão ALUNO | Papel de acesso |
| ativo | TINYINT(1) | NN, padrão 1, CHECK 0/1 | Conta ativa |
| criado_em | DATETIME | NN, padrão agora | Data de criação |

## laboratorio
| Coluna | Tipo | Restrições | Descrição |
|---|---|---|---|
| id_laboratorio | INT UNSIGNED | PK, AI | Identificador |
| nome | VARCHAR(80) | NN, UK | Nome exibido |
| localizacao | VARCHAR(120) | NN | Bloco/sala |
| capacidade | SMALLINT UNSIGNED | NN, CHECK > 0 | Lugares disponíveis |
| ativo | TINYINT(1) | NN, padrão 1 | Aceita reservas? |

## equipamento
| Coluna | Tipo | Restrições | Descrição |
|---|---|---|---|
| id_equipamento | INT UNSIGNED | PK, AI | Identificador |
| id_laboratorio | INT UNSIGNED | FK → laboratorio, NN | Laboratório onde fica |
| nome | VARCHAR(80) | NN | Descrição do equipamento |
| numero_patrimonio | VARCHAR(30) | NN, UK | Número de patrimônio |
| status | ENUM('DISPONIVEL','MANUTENCAO','BAIXADO') | NN, padrão DISPONIVEL | Situação |

## reserva
| Coluna | Tipo | Restrições | Descrição |
|---|---|---|---|
| id_reserva | INT UNSIGNED | PK, AI | Identificador |
| id_usuario | INT UNSIGNED | FK → usuario, NN | Solicitante |
| id_laboratorio | INT UNSIGNED | FK → laboratorio, NN | Laboratório reservado |
| data_reserva | DATE | NN | Dia da reserva |
| hora_inicio | TIME | NN | Início |
| hora_fim | TIME | NN, CHECK > hora_inicio | Término |
| finalidade | VARCHAR(200) | NN | Motivo/atividade |
| status | ENUM('PENDENTE','APROVADA','RECUSADA','CANCELADA') | NN, padrão PENDENTE | Situação |
| id_avaliador | INT UNSIGNED | FK → usuario, NULL | Técnico que decidiu |
| motivo_recusa | VARCHAR(200) | NULL | Preenchido em recusas |
| criada_em | DATETIME | NN, padrão agora | Data do pedido |

Índices: `idx_reserva_lab_data (id_laboratorio, data_reserva, hora_inicio)`, `idx_reserva_usuario`, `idx_reserva_status`.

## reserva_equipamento
Associativa N:N entre reserva e equipamento.
| Coluna | Tipo | Restrições | Descrição |
|---|---|---|---|
| id_reserva | INT UNSIGNED | PK, FK → reserva (CASCADE) | Reserva |
| id_equipamento | INT UNSIGNED | PK, FK → equipamento | Equipamento solicitado |

## ocorrencia
| Coluna | Tipo | Restrições | Descrição |
|---|---|---|---|
| id_ocorrencia | INT UNSIGNED | PK, AI | Identificador |
| id_reserva | INT UNSIGNED | FK → reserva (CASCADE), NN | Reserva de origem |
| id_equipamento | INT UNSIGNED | FK → equipamento, NULL | Equipamento envolvido |
| descricao | VARCHAR(500) | NN | O que aconteceu |
| registrada_em | DATETIME | NN, padrão agora | Momento do registro |

## vw_uso_laboratorio (visão)
`id_laboratorio`, `laboratorio`, `data_reserva`, `total_reservas`, `horas_uso` – somente reservas APROVADAS.
