# 5. Testes e laudo de qualidade

## 5.1 Testes automatizados
Arquivo: `tests/test_labagenda.py` · Execução: `python -m unittest discover -s tests -v`
Saída registrada em `docs/evidencias/execucao_testes.txt` — **78 testes, 0 falhas** (v2.2.1; 76 na v2.2, 60 na v2.1, 44 na v2.0 e 25 na v1.0).

| Grupo | O que cobre |
|---|---|
| Usuários | hash de senha, e-mail normalizado, bloqueio de perfil técnico no cadastro, validações E01–E06 |
| Reservas | data passada, fim ≤ início, 4 h exatas × 4 h + 1, bordas 07:00/22:00, sobreposição parcial/total, horários encostados, laboratório distinto, liberação por cancelamento/recusa, equipamento em manutenção, *rollback* de gravação parcial, decisão, cancelamento por não dono |
| Administração | validações de laboratório/equipamento, ocorrência, relatório de horas |
| Exclusão lógica (v2.1) | motivo obrigatório, bloqueio com reservas futuras, itens fora das listas e da reserva, histórico preservado, reativação, acesso só do técnico (`TestExclusaoV21`, 16 testes) |
| Histórico, edição, ocorrências e filtros (v2.2 e v2.2.1) | edição de equipamento, histórico de alterações, ocorrência ligada ao equipamento e à manutenção, ocorrência geral do laboratório, filtros de reservas e equipamentos (`TestV22` e 2 testes da v2.2.1) |
| HTTP | login inválido (401), POST sem CSRF, fluxo professor → técnico, mensagem de conflito (400), escape de HTML (XSS) |

> **Observação:** os testes automatizados rodam com SQLite (`database/schema_sqlite.sql`), que espelha as tabelas e regras.
> O mesmo código foi executado contra o **MySQL 8 do Aiven** em produção (seção 5.6).

## 5.2 Roteiro de teste manual para os colegas
| # | Passo | Resultado esperado |
|---|---|---|
| 1 | Criar conta com senha `abc` | Mensagem E04 |
| 2 | Criar conta válida e entrar | Painel "Minhas reservas" vazio |
| 3 | Nova reserva: lab de Redes, amanhã, 08:00–10:00, com um equipamento | Mensagem S02; situação "Pendente" |
| 4 | Repetir com 09:00–11:00 | Mensagem E11 e quadro amarelo com 08:00–10:00 |
| 5 | Pedir 10:00–15:00 | Mensagem E09 |
| 6 | Entrar como técnico, recusar sem motivo | Mensagem E14 |
| 7 | Recusar com motivo; voltar ao usuário | Motivo aparece na lista |
| 8 | Tentar abrir `/relatorio` como aluno | Mensagem E17 |
| 9 | Colocar equipamento em manutenção e tentar reservá-lo | Não aparece na lista |
| 10 | Abrir no celular (ou janela estreita) | Tabelas viram cartões |
| 11 | (v2.1) Como técnico, excluir um equipamento sem motivo e depois com motivo | Mensagem E26; depois S10 e o item some da lista |
| 12 | (v2.1) Abrir Itens excluídos e reativar | Mensagem S12; o item volta à lista |
| 13 | (v2.1) Excluir um laboratório que tem reserva futura | Mensagem E27 |
| 14 | (v2.2) Editar um equipamento com patrimônio já existente | Mensagem E21; com dado válido, S14 |
| 15 | (v2.2) Abrir Histórico | Linhas de cadastro, edição, exclusão e reativação |
| 16 | (v2.2.1) Registrar ocorrência escolhendo um equipamento e marcando manutenção; depois outra com "Problema geral do laboratório" | S15 e situação Em manutenção; no histórico, "Geral do laboratório" |

## 5.3 Registro de testes com colegas
As respostas dos 5 colegas foram transcritas, como recebidas, na tabela do documento Word de entrega e analisadas em [08-feedback-e-versao-2.md](08-feedback-e-versao-2.md).

## 5.4 Laudo de qualidade
**Sistema:** LabAgenda 1.0 (versão entregue aos colegas) · **Data da verificação:** 24/10/2026 · **Método:** testes automatizados, inspeção das telas em navegador (Chromium, desktop 1100 px e celular 390 px) e revisão de código.

### Defeitos encontrados e corrigidos
| ID | Gravidade | Descrição | Evidência | Correção | Reteste |
|---|---|---|---|---|---|
| D01 | Média | Botão "Cancelar" aparecia em reserva já realizada; ao clicar, o usuário recebia erro | Captura do celular (21/10, aprovada, com botão) | Rota calcula `pode_cancelar` (RN08) e o template só mostra o botão quando permitido | Nova captura `tela12_mobile_reservas.png` sem botão |
| D02 | Baixa | Mensagem E11 dizia "veja os horários livres abaixo", mas o quadro de ocupados aparece acima do formulário | `tela06_conflito_erro.png` | Texto alterado para "…no quadro amarelo acima" | Captura refeita |
| D03 | Baixa | Testes assumiam que o conflito de equipamento seria alcançado antes do conflito do laboratório | Falha inicial de `test_equipamentos` | Teste corrigido; a checagem de equipamento permanece como defesa em profundidade | 25/25 passando |
| D04 | Baixa | Teste de sobreposição usava 5 h, caindo na regra de 4 h (E09) em vez de E11 | Falha inicial de `test_conflito_de_horario` | Teste ajustado para 07:00–11:00 | 25/25 passando |

### Verificações de segurança
| Item | Resultado |
|---|---|
| Senhas em texto puro | Não: apenas hash scrypt |
| SQL com concatenação de entrada | Não: todas as consultas parametrizadas |
| CSRF | POST sem token é rejeitado (teste HTTP) |
| XSS | Entrada `<script>` é exibida escapada (teste HTTP) |
| Enumeração de usuários no login | Mesma mensagem E02 para e-mail inexistente e senha errada |
| Escalada de privilégio no cadastro | Perfil técnico não pode ser escolhido |
| Cookies | `HttpOnly` e `SameSite=Lax` |

### Pendências conhecidas
| ID | Descrição | Tratamento sugerido |
|---|---|---|
| P01 | Execução contra MySQL real ainda não registrada | **Resolvida** (seção 5.6): tabelas criadas e sistema publicado usando o MySQL 8 do Aiven |
| P02 | Cookie sem flag `Secure` em desenvolvimento | **Configurável na v2.0** (`SECURE_COOKIES=1`); ativar em produção com HTTPS |
| P03 | Sem limite de tentativas de login | **Resolvida na v2.0** (bloqueio após 5 falhas, E25) |
| P04 | Sem recuperação de senha | Backlog |
| P05 | Relatório sem exportação | **Resolvida na v2.0** (CSV) |

### Parecer
Dentro do escopo da versão 1.0, as regras RN01–RN10 estão implementadas e cobertas por testes, e os defeitos
D01–D04 foram corrigidos e retestados. **Aprovado condicionalmente**, pendente da pendência P01.

## 5.4-B Versão 2.1 – exclusão lógica
Sugestão do próprio autor durante os testes: equipamento quebrado ou laboratório que virou sala de aula não devia ficar para sempre como "indisponível". Verificado por 16 testes (classe `TestExclusaoV21`): motivo obrigatório; bloqueio com reservas futuras; sumiço das listas e da reserva; registro, data e responsável guardados; histórico de reservas, ocorrências e relatório preservado; reativação (com bloqueio se o laboratório continua excluído); acesso apenas do técnico.

## 5.4-C Versão 2.2 – histórico, edição, ocorrências e filtros
Melhorias definidas pelo autor, sem dependência de serviços externos. 16 testes (classe `TestV22`) cobrem: edição de equipamento (patrimônio único, mudança de laboratório bloqueada com reserva futura); histórico de cadastro, edição, situação, exclusão, reativação e manutenção; ocorrência ligada ao equipamento com envio para manutenção; filtros de reservas e de equipamentos; telas restritas ao técnico.

## 5.5 Reteste da versão 2.0
| ID | Origem | Verificação | Resultado |
|---|---|---|---|
| R01 | Colega 1 | Login e cadastro com campos vazios/e-mail inválido mostram erro junto do campo | Aprovado (testes + `tela13`) |
| R02 | Colega 2 | Reserva com campos vazios marca cada campo; conflito aparece no campo de horário | Aprovado (`tela14`) |
| R03 | Colega 3 | Recusa sem motivo mostra erro na linha da reserva e mantém pendente | Aprovado (`tela15`) |
| R04 | Colega 3 | Aluno barrado em `/relatorio`, `/relatorio.csv`, `/equipamentos`, `/ocorrencias` | Aprovado |
| R05 | Colega 4 | Ocorrência em reserva futura é recusada; em reserva iniciada é aceita | Aprovado |
| R06 | Colega 4 | Relatório na tela e em CSV com 2,5 h para uma reserva de 08:00–10:30 | Aprovado |
| R07 | Colega 5 | Link de salto, idioma, viewport, etapas e ajuda inicial presentes | Aprovado (`tela16`) |
| R08 | Segurança | Bloqueio após 5 falhas, mesmo com a senha certa; libera após a janela | Aprovado |



## 5.6 Verificação em produção (Render + MySQL 8 no Aiven)
**URL:** https://projeto-integrador-interdisciplinar.onrender.com · **Data:** 03/11/2026

| Verificação | Resultado |
|---|---|
| `aplicar_schema.py` executou os 13 comandos do `schema.sql` no MySQL do Aiven (6 tabelas, 6 índices, 1 visão) | Aprovado |
| Carga inicial (`app.seed`) executada contra o banco de nuvem | Aprovado |
| Conexão da aplicação ao MySQL com SSL a partir do Render | Aprovado |
| Login no site publicado com usuário de demonstração | Aprovado |
| Roteiro 5.2 completo no site publicado (reservas, conflito, painel do técnico, relatório, celular) | *Registrar aqui as capturas após executar* |

### Incidentes da implantação
| ID | Gravidade | Descrição | Evidência | Correção | Reteste |
|---|---|---|---|---|---|
| D05 | Alta | Site retornava *Internal Server Error*: variáveis de ambiente do Render vazias, o sistema tentava conectar em `127.0.0.1:3306` | Log: `ConnectionRefusedError: [Errno 111]` | Variáveis cadastradas em *Environment* e novo deploy | Log passou a mostrar a conexão chegando ao Aiven |
| D06 | Alta | Banco recusava a senha ao conectar pelo Render, embora funcionasse localmente | Log: `OperationalError 1045 Access denied` | `DB_PASSWORD` recriada e `.strip()` aplicado às credenciais (`app/__init__.py`) | Login funcionando no site publicado |

Lição registrada: erros de configuração são mais rápidos de diagnosticar pelo **final do Traceback nos Logs** do Render; a primeira linha (`Traceback (most recent call last):`) não traz a causa.

## 5.7 Verificação da versão 2.2.1 (execução do autor)
**Data:** 06/11/2026 · **Executor:** autor do projeto · **Ambientes:** local (SQLite) e site publicado (Render + MySQL 8 no Aiven)

| Etapa | Verificação | Resultado |
|---|---|---|
| 1 | `python -m unittest discover -s tests`: 78 testes | Aprovado |
| 2 | Checklist manual de 22 passos no ambiente local: erros junto do campo, bloqueio de login, reserva e conflito, recusa sem motivo, exclusão e reativação de equipamento e de laboratório, bloqueio por reserva futura, edição com patrimônio duplicado, histórico, filtros, ocorrência em reserva futura, ocorrência com equipamento e manutenção, ocorrência geral do laboratório, permissões do aluno | Aprovado (22/22) |
| 3 | Site publicado: rodapé v2.2.1, telas Itens excluídos, Histórico e Reservas abrindo sem erro (migrações 2.1 e 2.2 aplicadas no Aiven) | Aprovado |

Observação: este registro vem da execução do próprio autor. A validação com pessoas independentes continua sendo a dos colegas (seção 5.3 e 5.5).

### Parecer final
Regras RN01–RN14 implementadas e cobertas por 78 testes automatizados; defeitos F01–F04, D01–D04 (v1.0/v2.0) e D05–D06 (implantação) corrigidos e retestados; versões 2.1, 2.2 e 2.2.1 verificadas no ambiente local e no site publicado com MySQL real. **Aprovado.**
Itens que dependem de novo teste com pessoas (tempo da primeira reserva e nota de usabilidade) seguem para o próximo ciclo.
