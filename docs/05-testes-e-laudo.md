# 5. Testes e laudo de qualidade

## 5.1 Testes automatizados
Arquivo: `tests/test_labagenda.py` · Execução: `python -m unittest discover -s tests -v`
Saída registrada em `docs/evidencias/execucao_testes.txt` — **25 testes, 0 falhas**.

| Grupo | O que cobre |
|---|---|
| Usuários | hash de senha, e-mail normalizado, bloqueio de perfil técnico no cadastro, validações E01–E06 |
| Reservas | data passada, fim ≤ início, 4 h exatas × 4 h + 1, bordas 07:00/22:00, sobreposição parcial/total, horários encostados, laboratório distinto, liberação por cancelamento/recusa, equipamento em manutenção, *rollback* de gravação parcial, decisão, cancelamento por não dono |
| Administração | validações de laboratório/equipamento, ocorrência, relatório de horas |
| HTTP | login inválido (401), POST sem CSRF, fluxo professor → técnico, mensagem de conflito (400), escape de HTML (XSS) |

> **Limite do ambiente:** os testes rodam com SQLite (`database/schema_sqlite.sql`), que espelha as tabelas e
> regras. O script MySQL (`schema.sql`) e o driver PyMySQL **não puderam ser executados** no ambiente em que este
> material foi produzido. Antes de entregar, rode `schema.sql` num MySQL 8 e repita o roteiro da seção 5.2 com
> `DB_ENGINE=mysql`.

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

## 5.3 Registro de testes com colegas
O documento Word de entrega traz 5 registros de teste elaborados como simulação a partir do comportamento real do sistema. Confirme cada um com o colega correspondente e ajuste ao que ele realmente observar.

## 5.4 Laudo de qualidade
**Sistema:** LabAgenda 2.0 · **Data da verificação:** 24/10/2026 · **Método:** testes automatizados, inspeção das telas em navegador (Chromium, desktop 1100 px e celular 390 px) e revisão de código.

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
| P01 | Execução contra MySQL real ainda não registrada | Rodar `schema.sql` + roteiro 5.2 e anexar capturas |
| P02 | Cookie sem flag `Secure` em desenvolvimento | Ativar `SESSION_COOKIE_SECURE=True` em produção com HTTPS |
| P03 | Sem limite de tentativas de login | Backlog: bloqueio temporário após falhas |
| P04 | Sem recuperação de senha | Backlog |
| P05 | Relatório sem exportação | Backlog |

### Parecer
Dentro do escopo da versão 2.0, as regras RN01–RN10 estão implementadas e cobertas por testes, e os defeitos
D01–D04 foram corrigidos e retestados. **Aprovado condicionalmente**, pendente da pendência P01.
