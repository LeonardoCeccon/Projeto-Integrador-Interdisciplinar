# 3. Interface Humano-Computador (IHC)

## 3.1 Princípios adotados
Heurísticas de Nielsen aplicadas ao LabAgenda:

| Heurística | Aplicação |
|---|---|
| Visibilidade do estado do sistema | Situação da reserva em etiquetas coloridas **com texto**; mensagens de sucesso após cada ação |
| Correspondência com o mundo real | Vocabulário do dia a dia: "reserva", "laboratório", "aprovar" |
| Controle e liberdade | Botões "Cancelar" e "Voltar" em formulários; cancelamento de reserva |
| Consistência | Mesma barra de navegação, mesmos botões e catálogo único de mensagens (46 mensagens, E01–E31 e S01–S15) |
| Prevenção de erros | Campos `time`/`date` nativos, lista só com equipamentos disponíveis, quadro de horários ocupados antes do pedido |
| Reconhecimento em vez de memorização | O quadro amarelo mostra o que está ocupado; os rótulos ficam sempre visíveis (sem *placeholder* como rótulo) |
| Eficiência de uso | Consulta e pedido na mesma tela; painel do técnico decide sem abrir outra página |
| Design minimalista | Uma tarefa por tela, sem elementos decorativos |
| Ajuda a reconhecer e corrigir erros | Mensagens dizem o que houve **e** o que fazer (seção 3.4) |
| Ajuda e documentação | Dicas curtas junto aos campos (regras de senha, horário de funcionamento) |

**Acessibilidade:** contraste mínimo de 4,5:1 nos textos; foco visível com contorno amarelo de 3 px;
rótulos `<label>` associados a cada campo; `role="alert"` nas mensagens de erro; navegação por teclado;
situação nunca indicada apenas por cor; layout responsivo (tabelas viram cartões abaixo de 640 px).

## 3.2 Mapa conceitual
![Mapa conceitual](img/uml_mapa_conceitual.png)

## 3.3 Mapa de navegação
```
Login ──► Painel do solicitante ──► Nova reserva ──► (volta ao Painel)
  │              └──► Laboratórios (consulta)
  └─► Criar conta

Login ──► Painel do técnico (pendentes)
              ├──► Reservas (filtros)                         v2.2
              ├──► Laboratórios (edição, exclusão)            v2.1
              ├──► Equipamentos (filtros, edição, exclusão)   v2.1 e v2.2
              ├──► Itens excluídos (abas, reativação)         v2.1
              ├──► Histórico de alterações                    v2.2
              ├──► Ocorrências (equipamento ou problema geral) v2.2
              └──► Relatório de uso (tela e CSV)
```

## 3.4 Catálogo de mensagens
Definido em `app/messages.py`. Princípios: linguagem simples, sem culpar o usuário, sem jargão técnico, com o
próximo passo. Erros usam fundo vermelho-claro e `role="alert"`; sucessos, fundo verde-claro.

| Código | Quando aparece | Texto |
|---|---|---|
| E01 | Login com campo vazio | Informe o e-mail e a senha para entrar. |
| E02 | Credenciais erradas (não revela se o e-mail existe) | E-mail ou senha incorretos. Confira os dados e tente de novo. |
| E03 | E-mail já cadastrado | Já existe uma conta com este e-mail. Entre ou use outro endereço. |
| E04 | Senha fraca | A senha precisa ter pelo menos 8 caracteres, com letras e números. |
| E05 | Campo obrigatório vazio | Preencha todos os campos obrigatórios. |
| E06 | E-mail inválido | Informe um e-mail válido, como nome@instituicao.edu.br. |
| E07 | Data/hora no passado | Não é possível reservar uma data que já passou. |
| E08 | Fim ≤ início | O horário final deve ser depois do horário inicial. |
| E09 | Mais de 4 h | Cada reserva pode durar no máximo 4 horas. |
| E10 | Fora do expediente | O laboratório funciona das 07:00 às 22:00. Escolha um horário dentro desse período. |
| E11 | Conflito | Este laboratório já está reservado em parte desse horário. Consulte os horários já ocupados no quadro amarelo acima. |
| E12 | Equipamento indisponível | O equipamento '{nome}' não está livre nesse horário. |
| E13 | Laboratório desativado | Este laboratório está desativado e não aceita reservas. |
| E14 | Recusa sem motivo | Informe o motivo da recusa (mínimo de 5 caracteres). |
| E15 | Reserva já decidida | Esta reserva não pode mais ser alterada porque já foi {situação}. |
| E16 | Cancelamento não permitido | Você só pode cancelar as suas próprias reservas, antes do horário de início. |
| E17 | Sem permissão | Você não tem permissão para acessar esta página. |
| E18 | Registro inexistente | Registro não encontrado. |
| E19–E24 | Cadastros e datas | Ver arquivo (capacidade, nome duplicado, patrimônio duplicado, ocorrência, sessão expirada, data inválida) |
| E25 | Excesso de tentativas de login (v2.0) | Muitas tentativas de acesso. Aguarde 10 minutos e tente de novo. |
| E26 | Exclusão sem motivo (v2.1) | Informe o motivo da exclusão (mínimo de 5 caracteres). |
| E27 | Laboratório com reservas futuras (v2.1) | O laboratório tem {n} reserva(s) futura(s) pendente(s) ou aprovada(s). Cancele ou recuse essas reservas antes de excluir. |
| E28 | Equipamento com reservas futuras (v2.1) | O equipamento tem {n} reserva(s) futura(s) pendente(s) ou aprovada(s). Cancele ou recuse essas reservas antes de excluir. |
| E29 | Reativar equipamento de laboratório excluído (v2.1) | O laboratório deste equipamento está excluído. Reative o laboratório antes. |
| E30 | Trocar o laboratório de um equipamento com reservas futuras (v2.2) | O equipamento tem {n} reserva(s) futura(s) pendente(s) ou aprovada(s) e não pode mudar de laboratório agora. |
| E31 | Manutenção sem equipamento escolhido (v2.2) | Escolha o equipamento para colocá-lo em manutenção. |
| S01–S09 | Sucessos | Ex. (v2.0): "Reserva enviada! Laboratório de Redes, 25/10/2026 das 08:00 às 10:00. Ela aguarda a aprovação do técnico." |
| S10–S15 | Sucessos da v2.1 e v2.2 | Equipamento ou laboratório excluído (S10, S11) e reativado (S12, S13); equipamento atualizado (S14); "Ocorrência registrada. O equipamento '{nome}' foi colocado em manutenção." (S15) |

## 3.5 Protótipo implementado (capturas reais)
| Tela | Imagem | Observações de projeto |
|---|---|---|
| Login | ![](img/tela01_login.png) | Um objetivo, dois campos, link para criar conta |
| Login com erro | ![](img/tela02_login_erro.png) | Mensagem E02; e-mail digitado é preservado |
| Cadastro com erro | ![](img/tela03_cadastro_erro.png) | Mensagem E04; campos preenchidos são mantidos |
| Minhas reservas | ![](img/tela04_minhas_reservas.png) | Etiquetas de situação, motivo da recusa visível, "Cancelar" só quando permitido |
| Nova reserva | ![](img/tela05_nova_reserva.png) | Passo 1: consultar ocupação; passo 2: pedir |
| Conflito | ![](img/tela06_conflito_erro.png) | Mensagem E11 + quadro de horários ocupados |
| Laboratórios (solicitante) | ![](img/tela07_laboratorios_professor.png) | Somente leitura |
| Painel do técnico | ![](img/tela08_painel_tecnico.png) | Decisão na própria linha |
| Laboratórios (técnico) | ![](img/tela09_laboratorios_tecnico.png) | Edição em linha e cadastro |
| Equipamentos | ![](img/tela10_equipamentos.png) | Troca de situação por lista |
| Relatório | ![](img/tela11_relatorio.png) | Filtro por período |
| Celular | ![](img/tela12_mobile_reservas.png) | Tabela vira cartões |
| Excluir equipamento (v2.1) | ![](img/tela17_excluir_equipamento.png) | Motivo obrigatório antes de excluir |
| Itens excluídos (v2.1) | ![](img/tela18_itens_excluidos.png) | Abas Equipamentos e Laboratórios; motivo, data, responsável e botão Reativar |
| Editar equipamento (v2.2) | ![](img/tela19_editar_equipamento.png) | Nome, patrimônio e laboratório |
| Histórico (v2.2) | ![](img/tela20_historico.png) | Quem fez o quê, com busca e filtro por tipo |
| Reservas com filtros (v2.2) | ![](img/tela21_reservas_filtros.png) | Laboratório, situação, período e texto |
| Ocorrência com equipamento (v2.2) | ![](img/tela22_ocorrencia_equipamento.png) | Caixa "O que foi afetado?" e opção de manutenção |
| Ocorrências registradas (v2.2.1) | ![](img/tela23_ocorrencias_historico.png) | Equipamento citado ou "Geral do laboratório" |

## 3.6 Melhorias de IHC registradas no ciclo Kaizen
1. Mensagem E11 reescrita para apontar o quadro que realmente existe na tela.
2. Botão "Cancelar" ocultado para reservas já iniciadas ou encerradas.
3. Equipamentos em manutenção deixaram de aparecer na seleção.
4. Rótulos permanentes em vez de textos de exemplo dentro dos campos.
5. Layout adaptado a telas de 390 px de largura.

## 3.7 Melhorias de IHC da v2.0 (feedback dos colegas)
1. Erro **ao lado do campo**, com ícone, borda vermelha, `aria-invalid`, `aria-describedby` e foco automático.
2. Indicador de etapas na reserva e ajuda "Como reservar em 3 passos" para quem não tem reservas.
3. Mensagens de sucesso com detalhes (o que foi feito, com quem, quando).
4. Link "Pular para o conteúdo" para teclado e leitores de tela.
5. Exportação CSV do relatório.

Capturas: `tela13` a `tela16` em `docs/img/` (ver [08-feedback-e-versao-2.md](08-feedback-e-versao-2.md)).

## 3.8 Melhorias de IHC da v2.1 a v2.2.1 (definidas pelo autor)
1. **Controle e liberdade:** itens excluídos podem ser reativados; nada é apagado de verdade.
2. **Prevenção de erros:** exclusão exige motivo e é bloqueada quando há reservas futuras, com a quantidade na mensagem (E27, E28).
3. **Visibilidade do estado do sistema:** o histórico mostra quem fez o quê, com data e o valor antigo e o novo.
4. **Correspondência com o mundo real:** a ocorrência pergunta "O que foi afetado?", com a opção "Problema geral do laboratório" para fiação, ar-condicionado ou iluminação.
5. **Eficiência de uso:** filtros e busca nas listas do técnico (reservas, equipamentos, histórico).

Capturas: `tela17` a `tela23` em `docs/img/`.

## 3.9 Pontos a validar com colegas (roteiro de avaliação heurística)
- A pessoa consegue fazer uma reserva sem instrução? Quanto tempo leva?
- Entende por que o pedido foi recusado?
- O quadro de horários ocupados é percebido antes de errar o horário?
- Consegue usar o sistema só com o teclado?
