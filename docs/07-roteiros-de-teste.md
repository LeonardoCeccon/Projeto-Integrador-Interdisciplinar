# 7. Roteiros de teste para colegas

Cada colega recebe um roteiro. Preencha **Resultado obtido** com o que realmente aconteceu e transcreva para as tabelas do Word. Não preencha por antecipação.


## Roteiro 1 – Cadastro e acesso

**Nome do colega:** ____________  **Data do teste:** ____/____/______

| # | Passo | Resultado esperado | Resultado obtido (OK / Falhou / Não testei) | Observações |
|---|---|---|---|---|
| 1 | Abrir a tela de login e tentar entrar com e-mail e senha em branco | Mensagem E01 |  |  |
| 2 | Tentar entrar com senha errada | Mensagem E02, e-mail digitado preservado |  |  |
| 3 | Criar conta com senha 'abc' | Mensagem E04, campos mantidos |  |  |
| 4 | Criar conta com e-mail sem @ | Mensagem E06 |  |  |
| 5 | Criar conta válida e entrar | Painel 'Minhas reservas' vazio |  |  |
| 6 | Criar outra conta com o mesmo e-mail | Mensagem E03 |  |  |
| 7 | Clicar em Sair e tentar abrir /painel | Volta para o login |  |  |

## Roteiro 2 – Reservas e conflitos

**Nome do colega:** ____________  **Data do teste:** ____/____/______

| # | Passo | Resultado esperado | Resultado obtido (OK / Falhou / Não testei) | Observações |
|---|---|---|---|---|
| 1 | Entrar como professor, consultar um laboratório numa data futura | Quadro com horários ocupados ou 'tudo livre' |  |  |
| 2 | Pedir reserva válida de 2 horas com um equipamento | Mensagem S02, situação Pendente |  |  |
| 3 | Repetir no mesmo horário | Mensagem E11 |  |  |
| 4 | Pedir 10:00 às 15:00 | Mensagem E09 |  |  |
| 5 | Pedir 06:00 às 08:00 | Mensagem E10 |  |  |
| 6 | Pedir horário que começa exatamente quando outra reserva termina | Aceita |  |  |
| 7 | Cancelar a reserva criada | Mensagem S05, horário liberado |  |  |

## Roteiro 3 – Painel do técnico

**Nome do colega:** ____________  **Data do teste:** ____/____/______

| # | Passo | Resultado esperado | Resultado obtido (OK / Falhou / Não testei) | Observações |
|---|---|---|---|---|
| 1 | Entrar como técnico | Lista de reservas pendentes |  |  |
| 2 | Clicar em Recusar sem motivo | Mensagem E14 |  |  |
| 3 | Recusar com motivo | Mensagem S04 |  |  |
| 4 | Entrar como solicitante | Motivo da recusa visível na lista |  |  |
| 5 | Aprovar outra reserva | Mensagem S03 |  |  |
| 6 | Como aluno, abrir /relatorio | Mensagem E17 |  |  |

## Roteiro 4 – Laboratórios, equipamentos e ocorrências

**Nome do colega:** ____________  **Data do teste:** ____/____/______

| # | Passo | Resultado esperado | Resultado obtido (OK / Falhou / Não testei) | Observações |
|---|---|---|---|---|
| 1 | Cadastrar laboratório com capacidade 0 | Mensagem E19 |  |  |
| 2 | Cadastrar laboratório com nome repetido | Mensagem E20 |  |  |
| 3 | Cadastrar equipamento com patrimônio repetido | Mensagem E21 |  |  |
| 4 | Colocar equipamento em manutenção | Some da lista de reserva |  |  |
| 5 | Desativar um laboratório | Não aceita novas reservas (E13) |  |  |
| 6 | Registrar ocorrência em reserva aprovada que já começou | Mensagem S08 |  |  |
| 7 | Gerar relatório de uso do mês | Horas e reservas por laboratório |  |  |

## Roteiro 5 – Usabilidade e celular

**Nome do colega:** ____________  **Data do teste:** ____/____/______

| # | Passo | Resultado esperado | Resultado obtido (OK / Falhou / Não testei) | Observações |
|---|---|---|---|---|
| 1 | Abrir no celular ou janela estreita | Tabelas viram cartões, sem rolagem lateral |  |  |
| 2 | Fazer uma reserva usando só o teclado | Foco visível em todos os campos |  |  |
| 3 | Ler as mensagens de erro | Dizem o que houve e o que fazer |  |  |
| 4 | Cronometrar uma primeira reserva sem ajuda | Registrar o tempo |  |  |
| 5 | Dar nota de 1 a 5 para clareza das telas | Registrar nota e comentário |  |  |

## Mensagem para enviar aos colegas
> Oi! Estou finalizando meu Projeto Integrador (sistema de reserva de laboratórios). Você pode testar por uns 10 minutos?
> Link: [colar link da aplicação]. Usuários de teste e roteiro: [colar roteiro]. Anote o que funcionou, o que quebrou e o que ficou confuso. Vou citar seu nome e seu feedback no trabalho, tudo bem?

## Como classificar as respostas
- **Defeito:** algo que deveria funcionar e não funcionou. Entra no laudo com evidência e correção.
- **Melhoria:** funciona, mas confunde. Entra no quadro Kaizen.
- **Não testado:** funcionalidade que o colega não alcançou ou que falta. Vai para a coluna correspondente da tabela.
