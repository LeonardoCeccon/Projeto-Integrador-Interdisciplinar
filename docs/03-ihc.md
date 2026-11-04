# 3. Interface Humano-Computador (IHC)

## 3.1 Princípios adotados
Heurísticas de Nielsen aplicadas ao LabAgenda:

| Heurística | Aplicação |
|---|---|
| Visibilidade do estado do sistema | Situação da reserva em etiquetas coloridas **com texto**; mensagens de sucesso após cada ação |
| Correspondência com o mundo real | Vocabulário do dia a dia: "reserva", "laboratório", "aprovar" |
| Controle e liberdade | Botões "Cancelar" e "Voltar" em formulários; cancelamento de reserva |
| Consistência | Mesma barra de navegação, mesmos botões e catálogo único de mensagens |
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
              ├──► Laboratórios (edição)
              ├──► Equipamentos
              ├──► Ocorrências
              └──► Relatório de uso
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
| E25 | Excesso de tentativas de login | Muitas tentativas de acesso. Aguarde 10 minutos e tente de novo. |
| E11 | Conflito | Este laboratório já está reservado em parte desse horário. Consulte os horários já ocupados no quadro amarelo acima. |
| E12 | Equipamento indisponível | O equipamento '{nome}' não está livre nesse horário. |
| E13 | Laboratório desativado | Este laboratório está desativado e não aceita reservas. |
| E14 | Recusa sem motivo | Informe o motivo da recusa (mínimo de 5 caracteres). |
| E15 | Reserva já decidida | Esta reserva não pode mais ser alterada porque já foi {situação}. |
| E16 | Cancelamento não permitido | Você só pode cancelar as suas próprias reservas, antes do horário de início. |
| E17 | Sem permissão | Você não tem permissão para acessar esta página. |
| E18 | Registro inexistente | Registro não encontrado. |
| E19–E24 | Cadastros e datas | Ver arquivo (capacidade, nome duplicado, patrimônio duplicado, ocorrência, sessão expirada, data inválida) |
| S01–S09 | Sucessos | Ex. (v2.0): "Reserva enviada! Laboratório de Redes, 25/10/2026 das 08:00 às 10:00. Ela aguarda a aprovação do técnico." |

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

## 3.8 Pontos a validar com colegas (roteiro de avaliação heurística)
- A pessoa consegue fazer uma reserva sem instrução? Quanto tempo leva?
- Entende por que o pedido foi recusado?
- O quadro de horários ocupados é percebido antes de errar o horário?
- Consegue usar o sistema só com o teclado?
