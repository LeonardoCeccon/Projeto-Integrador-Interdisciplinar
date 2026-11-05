# 1. Escopo, requisitos e melhoria contínua (Kaizen)

## 1.1 Problema
Em muitas instituições de ensino, a agenda dos laboratórios é mantida em planilhas, grupos de mensagens ou
cadernos na secretaria. O resultado é previsível: duas turmas marcadas para a mesma sala no mesmo horário,
equipamentos pedidos que estão quebrados, nenhuma visão de quanto cada laboratório é realmente usado e pouca
rastreabilidade quando algo dá errado durante a aula.

## 1.2 Proposta
O **LabAgenda** é uma aplicação web para solicitar, aprovar e acompanhar reservas de laboratórios e de seus
equipamentos. Quem solicita enxerga os horários ocupados antes de pedir; o técnico responsável decide cada
pedido; o sistema impede conflitos por regra, não por boa vontade.

**Objetivo geral:** eliminar conflitos de agenda e dar visibilidade ao uso dos laboratórios.

**Objetivos específicos**
1. Permitir que alunos e professores consultem disponibilidade e solicitem reservas sem sair do navegador.
2. Garantir, no servidor e no banco, que dois pedidos ativos nunca ocupem o mesmo laboratório ao mesmo tempo.
3. Dar ao técnico um painel único para aprovar/recusar pedidos, manter laboratórios e equipamentos e registrar ocorrências.
4. Produzir um relatório de horas de uso por laboratório para apoiar decisões de manutenção e compra.

## 1.3 Escopo
| Dentro do escopo (versões 1.0 e 2.0) | Fora do escopo (backlog) |
|---|---|
| Cadastro e login de alunos/professores | Integração com o sistema acadêmico (SSO) |
| Consulta de horários ocupados por data | Reservas recorrentes (semanais) |
| Solicitação, cancelamento e acompanhamento de reservas | Notificações por e-mail/SMS |
| Aprovação/recusa com motivo pelo técnico | Aplicativo móvel nativo (a interface web já é responsiva) |
| Cadastro de laboratórios e equipamentos, com situação | Calendário visual semanal |
| Registro de ocorrências | Exportação do relatório em PDF (o CSV entrou na v2.0) |
| Relatório de uso por período | Recuperação de senha por e-mail |

## 1.4 Partes interessadas e perfis
| Perfil | Quem é | O que precisa fazer |
|---|---|---|
| Aluno | Estudante em atividade de monitoria, projeto ou estudo | Reservar, cancelar e acompanhar os próprios pedidos |
| Professor | Docente responsável por aulas práticas | O mesmo que o aluno |
| Técnico | Responsável pelos laboratórios | Decidir pedidos, manter cadastros, registrar ocorrências, ver relatório |

*Alunos e professores compartilham as mesmas permissões; o perfil existe para fins de relatório futuro e para
manter a separação clara em relação ao técnico.*

## 1.5 Requisitos funcionais
| ID | Requisito | Caso de uso |
|---|---|---|
| RF01 | Criar conta informando nome, e-mail, senha e perfil (aluno ou professor) | UC01 |
| RF02 | Autenticar com e-mail e senha | UC02 |
| RF03 | Consultar horários já ocupados de um laboratório em uma data | UC03 |
| RF04 | Solicitar reserva com laboratório, data, horário, finalidade e equipamentos opcionais | UC04 |
| RF05 | Cancelar a própria reserva antes do horário de início | UC05 |
| RF06 | Listar as próprias reservas com situação e motivo de recusa | UC06 |
| RF07 | Aprovar ou recusar reservas pendentes (recusa exige motivo) | UC07 |
| RF08 | Cadastrar, editar, ativar e desativar laboratórios | UC08 |
| RF09 | Cadastrar equipamentos e alterar sua situação | UC09 |
| RF10 | Registrar ocorrências ligadas a reservas aprovadas | UC10 |
| RF11 | Emitir relatório de reservas aprovadas e horas de uso por laboratório | UC11 |

## 1.6 Requisitos não funcionais
| ID | Requisito | Como é atendido |
|---|---|---|
| RNF01 | Senhas nunca guardadas em texto | Hash com `werkzeug.security` (scrypt) |
| RNF02 | Proteção contra CSRF e XSS | Token de formulário em todo POST; escape automático do Jinja2 |
| RNF03 | Mínimo privilégio no banco | Usuário `labagenda_app` sem `DELETE`/`DROP` |
| RNF04 | Interface utilizável em celular | CSS responsivo (tabelas viram cartões); ver `docs/img/tela12_mobile_reservas.png` |
| RNF05 | SGBD popular e de fácil manutenção | MySQL 8 com InnoDB |
| RNF06 | Consultas de conflito rápidas | Índice composto `(id_laboratorio, data_reserva, hora_inicio)` |
| RNF07 | Mensagens claras e consistentes | Catálogo único em `app/messages.py` |
| RNF08 | Disponível na internet com banco gerenciado | Render (aplicação) + MySQL 8 no Aiven, conexão SSL, deploy automático pelo GitHub |
| RNF09 | Configuração fora do código | Variáveis de ambiente (`DB_*`, `SECRET_KEY`, `SECURE_COOKIES`); credenciais nunca versionadas |

## 1.7 Regras de negócio
| ID | Regra | Onde é garantida |
|---|---|---|
| RN01 | Somente o técnico gerencia laboratórios, equipamentos, ocorrências, relatório e decisões | `login_required` nas rotas |
| RN02 | Não é possível reservar data/horário que já passou | `services.criar_reserva` |
| RN03 | Horário final maior que o inicial; duração máxima de 4 horas | serviço + `CHECK` no banco |
| RN04 | Reservas apenas entre 07:00 e 22:00 | serviço |
| RN05 | Dois pedidos PENDENTE/APROVADA não podem se sobrepor no mesmo laboratório (horários encostados são permitidos) | serviço, com `SELECT … FOR UPDATE` no laboratório |
| RN06 | Equipamento precisa pertencer ao laboratório, estar DISPONÍVEL e livre no horário | serviço |
| RN07 | Só reservas PENDENTES são decididas; recusar exige motivo de 5+ caracteres | serviço |
| RN08 | Só o dono cancela, e apenas antes do início | serviço + botão oculto na tela |
| RN09 | Ocorrência só em reserva APROVADA cujo horário já começou | serviço |
| RN10 | Relatório considera apenas reservas APROVADAS | serviço |
| RN11 (v2.1) | Equipamento ou laboratório é excluído só de forma lógica, com motivo de 5+ caracteres, data e responsável; o histórico (reservas, ocorrências, relatório) é preservado | serviço |
| RN13 (v2.2) | Cadastro, edição, mudança de situação, exclusão e reativação de laboratórios e equipamentos são registrados (quem, quando e o que mudou) | serviço |
| RN14 (v2.2) | Equipamento só muda de laboratório se não tiver reservas futuras pendentes/aprovadas; colocar em manutenção por ocorrência exige o equipamento da reserva | serviço |
| RN12 (v2.1) | Não se exclui laboratório ou equipamento com reservas futuras pendentes/aprovadas; item excluído pode ser reativado em Itens excluídos | serviço |

## 1.8 Critérios de aceite (resumo)
- Dado um laboratório com reserva das 08:00 às 10:00, um pedido das 09:00 às 11:00 é rejeitado com a mensagem E11, e um pedido das 10:00 às 11:00 é aceito.
- Dado um pedido recusado, o solicitante vê o motivo na própria lista.
- Dado um equipamento em manutenção, ele não aparece na lista de seleção da reserva e é rejeitado se enviado.
- Um aluno que acessa `/relatorio` é redirecionado com a mensagem E17.

## 1.9 Ciclo de melhoria contínua (Kaizen / PDCA)
> **Nota ao estudante:** como o PIT I não foi anexado, os achados abaixo descrevem falhas comuns de uma primeira modelagem, tratadas já nesta versão. Se o seu PIT I tinha outros pontos, substitua/complete a tabela com a sua realidade e os comentários dos colegas.

O projeto foi tratado como um ciclo PDCA. Cada achado abaixo foi **planejado, feito, verificado e ajustado**.

| # | Achado (Plan) | Ação (Do) | Verificação (Check) | Resultado (Act) |
|---|---|---|---|---|
| 1 | O diagrama de classes inicial ligava Reserva e Equipamento como 1:N, impedindo reservar vários equipamentos e reaproveitá-los em datas diferentes | Relação passou a N:N com tabela associativa `reserva_equipamento` | Teste `test_equipamentos` | Corrigido em classes, DER e banco |
| 2 | A situação da reserva era só um texto livre | Criada a máquina de estados (PENDENTE → APROVADA/RECUSADA/CANCELADA) e `ENUM` no banco | Diagrama de estados + testes de decisão e cancelamento | Transições inválidas rejeitadas (E15) |
| 3 | Conflito de horário só era checado na tela | Checagem no servidor, dentro de transação, com trava do laboratório | `test_conflito_de_horario` | Garantia independente da interface |
| 4 | O perfil "técnico" podia ser escolhido no cadastro público | Cadastro público aceita só aluno/professor | `test_cadastro_nao_permite_virar_tecnico` | Escalada de privilégio eliminada |
| 5 | Mensagem de erro de conflito remetia a "horários livres abaixo", mas o quadro de ocupados fica acima | Texto da E11 reescrito | Captura de tela `tela06_conflito_erro.png` | Mensagem coerente com a tela |
| 6 | Botão "Cancelar" aparecia em reservas já realizadas | Botão só aparece quando a regra RN08 permite | Captura `tela12_mobile_reservas.png` | Interface alinhada à regra |
| 7 | Falha ao gravar um equipamento deixava a reserva "pela metade" | Operação envolta em transação com `ROLLBACK` | `test_falha_em_equipamento_nao_deixa_reserva_pela_metade` | Gravação tudo-ou-nada |
| 8 | Mensagens espalhadas pelo código | Catálogo único `app/messages.py` com códigos E/S | Revisão das telas | Textos consistentes e reutilizáveis |

## 1.10 Riscos
| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Duas pessoas reservarem ao mesmo tempo | Média | Alto | Transação + `FOR UPDATE` + índice |
| Técnico demorar a decidir | Alta | Médio | Painel destaca pendentes; notificações no backlog |
| Dados de teste sendo usados em produção | Média | Alto | Senhas de demonstração documentadas como temporárias; `.env` fora do Git |
| Perda do banco | Baixa | Alto | Rotina de `mysqldump` descrita em `docs/04-dados.md` |
| Serviço gratuito "dormir" e demorar na primeira página | Alta | Baixo | Abrir a URL antes de apresentar; plano pago em uso real |
| Credenciais com erro de digitação ou espaços invisíveis | Média | Alto | `.strip()` no código e conferência pelo Traceback nos Logs (incidente D06) |
| Contas de demonstração públicas | Alta | Médio | Trocar ou remover após a apresentação |
