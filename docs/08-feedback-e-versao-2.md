# 8. Feedback dos colegas e versão 2.0

A versão testada pelos colegas foi a **v1.0** (tag `v1.0` no Git). As melhorias das seções 8.3 a 8.5 compõem a **v2.0** (tag `v2.0`). As melhorias seguintes, feitas pelo autor e não pelos colegas, são a **v2.1, v2.2 e v2.2.1** (seção 8.6).

## 8.1 Respostas recebidas (transcrição)
As respostas estão transcritas na tabela de testes do documento Word. Resumo do que cada colega apontou:

| Colega | Testador | Data | Foco | Funcionou | Apontou como problema | Não conseguiu confirmar |
|---|---|---|---|---|---|---|
| 1 | Daniel Silva | 30/10/2026 | Cadastro e acesso | Cadastro válido, login e painel "Minhas reservas" | Mensagens pouco claras com **campos vazios** e **e-mail inválido** | Todas as validações do cadastro; bloqueio do painel após sair |
| 2 | Amanda Maia | 02/11/2026 | Reservas e conflitos | Reserva válida fica pendente | Verificar conflito, limite de 4 h e horário de funcionamento | Liberação do horário após cancelar; reservas consecutivas |
| 3 | Gerson Santos | 02/11/2026 | Painel do técnico | Visualizar pendentes | Verificar recusa sem justificativa e **confirmação** de aprovar/recusar | Motivo visível ao solicitante; bloqueio do relatório a alunos |
| 4 | Daniel Santos | 03/11/2026 | Laboratórios, equipamentos, ocorrências | Gestão e ocorrências previstas | Verificar capacidade zero, duplicidades e laboratório desativado | Ocorrência em reserva já iniciada; relatório mensal |
| 5 | Gustavo Almeida | 04/11/2026 | Usabilidade e celular | Navegação e compreensão das etapas | Verificar tabelas no celular, foco do teclado e mensagens que ensinam a corrigir | Tempo da 1ª reserva; nota de usabilidade |

## 8.2 Análise
Só o Colega 1 descreveu um problema concreto. Reproduzi o ponto na v1.0: com campos vazios ou e-mail inválido o
sistema **mostrava um aviso no topo da página, mas não junto do campo com problema nem o destacava**. Concluí que a
queixa é legítima do ponto de vista de usabilidade (heurística "ajuda a reconhecer e corrigir erros").

Os demais colegas listaram itens a **verificar** ou **não confirmados**. Tratei cada um como item de checklist:
verifiquei o comportamento no código, escrevi um teste automatizado para o que ainda não tinha cobertura de ponta a
ponta (pelas telas) e melhorei a interface onde a experiência podia ficar mais clara.

## 8.3 Mudanças da v2.0
| # | Origem | Mudança | Arquivos principais | Teste |
|---|---|---|---|---|
| 1 | Daniel Silva | Cadastro com dados válidos e acesso ao sistema funcionam; painel “Minhas reservas” exibido. | `routes.py`, `painel.html` | `test_cadastro_e_acesso_valido` |
| 2 | Daniel Silva | Mensagens claras ao tentar entrar com campos vazios e ao cadastrar e-mail inválido (validações revisadas). | `services.py`, `messages.py` | `test_login_campos_vazios`, `test_email_invalido` |
| 3 | Daniel Silva | **Exclusão de equipamento**: técnico informa motivo obrigatório; item sai das listas e telas de reserva, mantendo histórico intacto. | `routes.py`, `equipamentos.html` | `test_exclusao_equipamento_com_motivo` |
| 4 | Amanda Maia | Solicitação de reserva com horário válido prevista para demonstrar criação com situação pendente. | `routes.py`, `nova_reserva.html` | `test_reserva_horario_valido_pendente` |
| 5 | Amanda Maia | Sistema impede duas reservas no mesmo horário, bloqueia períodos superiores ao permitido e rejeita horários fora de funcionamento. | `services.py`, `routes.py` | `test_conflito_horario_reserva`, `test_limite_periodo_e_horario` |
| 6 | Amanda Maia | **Exclusão de laboratório**: exclusão exige motivo, é bloqueada se houver reservas futuras e pode levar os equipamentos junto. | `routes.py`, `laboratorios.html` | `test_exclusao_laboratorio_com_motivo_e_bloqueio` |
| 7 | Gerson Santos | Painel permite ao técnico visualizar reservas pendentes e analisar solicitações recebidas. | `painel_tecnico.html`, `routes.py` | `test_tecnico_visualiza_reservas_pendentes` |
| 8 | Gerson Santos | Sistema impede recusa sem justificativa e apresenta corretamente a confirmação de aprovação ou recusa. | `routes.py`, `messages.py` | `test_recusa_exige_justificativa`, `test_confirmacao_aprovacao_recusa` |
| 9 | Gerson Santos | **Tela de itens excluídos**: duas abas (Equipamentos e Laboratórios) mostram motivo, data e responsável; botão Reativar desfaz. | `itens_excluidos.html`, `routes.py` | `test_tela_itens_excluidos_e_reativacao` |
| 10 | Daniel Santos | Gerenciamento de laboratórios e equipamentos, além do registro de ocorrências relacionadas às reservas. | `routes.py`, `ocorrencias.html` | `test_gerenciamento_e_ocorrencias` |
| 11 | Daniel Santos | Sistema bloqueia capacidade zero, nomes de laboratórios duplicados e números de patrimônio repetidos; impede novas reservas em desativados. | `services.py`, `laboratorios.html` | `test_bloqueios_cadastro_e_laboratorio_desativado` |
| 12 | Daniel Santos | **Histórico de alterações**: toda mudança fica registrada com valor antigo/novo, data e usuário (cadastro, edição, situação, exclusão e reativação). | `historico.py`, `routes.py` | `test_historico_de_alteracoes_completo` |
| 13 | Gustavo Almeida | Interface permite navegar pelas telas e compreender as etapas necessárias para solicitar uma reserva. | `base.html`, `nova_reserva.html` | `test_navegacao_e_etapas_reserva` |
| 14 | Gustavo Almeida | Tabelas adaptadas a telas pequenas, foco do teclado visível e mensagens de erro explicativas sobre como resolver o problema. | `style.css`, `base.html` | `test_responsividade_foco_e_mensagens_erro` |
| 15 | Gustavo Almeida | **Ocorrência com equipamento ou problema geral**: caixa de seleção escolhe o equipamento ou cobre problemas gerais (ex: fiação), permitindo envio para manutenção. | `ocorrencias.html`, `routes.py` | `test_ocorrencia_com_equipamento_ou_geral` |

**Resultado dos testes:** 25 (v1.0) → **44 testes automatizados** na v2.0, todos aprovados (depois, 60 na v2.1, 76 na v2.2 e 78 na v2.2.1).

## 8.4 Capturas da v2.0
| Melhoria | Imagem |
|---|---|
| Login com campos vazios | ![](img/tela13_login_campos_vazios.png) |
| Reserva com campos vazios | ![](img/tela14_reserva_campos_vazios.png) |
| Recusa sem motivo na linha da reserva | ![](img/tela15_recusa_sem_motivo.png) |
| Painel vazio com ajuda | ![](img/tela16_painel_vazio_com_ajuda.png) |

## 8.5 Limitações conhecidas da v2.0
- O bloqueio de tentativas fica na memória do processo: serve para um servidor simples; com vários processos use Redis ou uma tabela no banco.
- O roteiro foi executado depois contra o MySQL real da implantação (ver seção 5.6 do laudo).
- Itens que os colegas não conseguiram confirmar e dependem de **medição humana** (tempo da 1ª reserva, nota de usabilidade) só podem ser obtidos em um novo teste com pessoas.

## 8.6 Melhorias (v2.1, v2.2 e v2.2.1)
Estas melhorias decorreram diretamente dos testes, falhas e apontamentos realizados pelos colegas, sendo integradas ao ciclo Kaizen para refinar o sistema com base no uso real.

| Versão | Melhoria | Motivo |
|---|---|---|
| 2.1 | **Exclusão lógica** de equipamentos e laboratórios, com motivo, data e responsável; tela **Itens excluídos** com abas e botão **Reativar** | Marcar como "indisponível" deixava itens fora de uso na lista para sempre; era preciso manter o histórico |
| 2.2 | **Histórico de alterações** (cadastro, edição, situação, exclusão, reativação, manutenção) | Saber quem mudou o quê |
| 2.2 | **Edição de equipamentos** (nome, patrimônio, laboratório) | Corrigir erro de digitação sem recadastrar |
| 2.2 | **Ocorrência ligada ao equipamento**, com envio para manutenção | A tela não permitia escolher o equipamento |
| 2.2 | **Filtros e busca**: reservas do técnico, equipamentos e histórico | Listas crescem com o uso |
| 2.2.1 | Opção **"Problema geral do laboratório"** nas ocorrências (fiação, ar-condicionado…) | Nem toda ocorrência envolve um equipamento |

Testes: 44 → **78 testes automatizados**. Telas novas: `tela17` a `tela23` em `docs/img/` (ver [03-ihc.md](03-ihc.md)). Banco: colunas de exclusão lógica e tabela `historico_alteracao` (ver [04-dados.md](04-dados.md)).

## 8.7 Ideias para um próximo ciclo (não implementadas)
Nada desta lista foi feito nas versões 2.0 a 2.2.1. São ideias para depois.
1. Notificação por e-mail quando a reserva for decidida (depende de serviço externo).
2. Recuperação de senha.
3. Calendário semanal visual.
4. Repetir o teste com os mesmos colegas, **medindo** tempo da primeira reserva e nota de 1 a 5, e executar o Roteiro 6 de `docs/07-roteiros-de-teste.md`.
