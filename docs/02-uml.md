# 2. Modelagem UML revisada

Fontes dos diagramas em `docs/diagramas/*.mmd` (Mermaid). As imagens são geradas com `mmdc`.

## 2.1 Casos de uso
![Casos de uso](img/uml_casos_de_uso.png)

**Ajustes feitos:** "Aluno" e "Professor" passaram a herdar de um ator genérico **Solicitante**, já que têm as
mesmas permissões (menos setas, modelo mais fiel). A autenticação (UC02) ficou como `«include»` dos casos de uso
que exigem sessão. A recusa com motivo foi tratada como regra de UC07, não como extensão de UC04, pois não faz
parte do fluxo do solicitante.

### Descrição resumida dos casos de uso principais
| UC04 – Solicitar reserva | |
|---|---|
| Ator | Solicitante (aluno ou professor) |
| Pré-condição | Usuário autenticado; laboratório ativo |
| Fluxo principal | 1. Escolhe laboratório e data. 2. Sistema mostra horários ocupados. 3. Informa horário, finalidade e equipamentos. 4. Sistema valida regras RN02–RN06. 5. Sistema grava a reserva como PENDENTE e exibe S02. |
| Fluxos alternativos | A1. Data passada → E07. A2. Fim ≤ início → E08. A3. Mais de 4 h → E09. A4. Fora de 07–22 h → E10. A5. Conflito de laboratório → E11. A6. Equipamento indisponível → E12. |
| Pós-condição | Reserva PENDENTE visível ao solicitante e ao técnico |

| UC07 – Avaliar reserva | |
|---|---|
| Ator | Técnico |
| Pré-condição | Existe reserva PENDENTE |
| Fluxo principal | 1. Abre o painel. 2. Escolhe uma reserva. 3. Aprova (S03) ou recusa informando motivo (S04). |
| Alternativos | A1. Recusa sem motivo → E14. A2. Reserva já decidida por outra pessoa → E15. |
| Pós-condição | Status APROVADA ou RECUSADA e avaliador registrado |

## 2.2 Diagrama de classes
![Classes](img/uml_classes.png)

**Ajustes feitos:** (1) Reserva ↔ Equipamento passou a ser N:N; (2) criada a classe **Ocorrencia**, ligada à
reserva por composição (sem reserva, não existe ocorrência); (3) a associação "avaliada por" aparece
separada de "solicita" porque o avaliador é outro usuário (técnico); (4) situações viraram enumerações; (5) o
atributo `senhaHash` substitui `senha`, refletindo que o sistema nunca guarda a senha original; (6) operações de
negócio (`aprovar`, `recusar`, `cancelar`, `estaLivre`) foram acrescentadas às classes responsáveis.

## 2.3 Diagramas de sequência
### Solicitar reserva
![Sequência – solicitar](img/uml_sequencia_solicitar_reserva.png)

### Avaliar reserva
![Sequência – avaliar](img/uml_sequencia_avaliar_reserva.png)

## 2.4 Diagrama de atividades
![Atividades](img/uml_atividades_reserva.png)

## 2.5 Diagrama de estados da Reserva
![Estados](img/uml_estados_reserva.png)

## 2.6 Arquitetura de implantação
![Implantação](img/uml_implantacao.png)

O diagrama mostra a implantação real: navegador → **Render** (Gunicorn + Flask) → **MySQL 8 no Aiven** por SSL, com código no **GitHub** e deploy automático a cada `push`.
A aplicação segue três camadas simples: **rotas** (`app/routes.py`, controle e perfis), **serviços**
(`app/services.py`, regras de negócio) e **dados** (`app/db.py`, acesso ao MySQL).

## 2.7 Rastreabilidade
| Caso de uso | Rotas | Função de serviço | Tabelas |
|---|---|---|---|
| UC01 | `/cadastro` | `criar_usuario` | usuario |
| UC02 | `/login`, `/sair` | `autenticar` | usuario |
| UC03 | `/reservas/nova` (GET) | `horarios_ocupados` | reserva |
| UC04 | `/reservas/nova` (POST) | `criar_reserva` | reserva, reserva_equipamento |
| UC05 | `/reservas/<id>/cancelar` | `cancelar_reserva` | reserva |
| UC06 | `/painel` | `listar_reservas` | reserva |
| UC07 | `/reservas/<id>/decidir` | `decidir_reserva` | reserva |
| UC08 | `/laboratorios` | `salvar_laboratorio` | laboratorio |
| UC09 | `/equipamentos` | `salvar_equipamento`, `alterar_status_equipamento` | equipamento |
| UC10 | `/ocorrencias` | `registrar_ocorrencia` | ocorrencia |
| UC11 | `/relatorio` | `relatorio_uso` | reserva, laboratorio |
