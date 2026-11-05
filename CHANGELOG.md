# Histórico de versões

## 2.2 – histórico, edição, ocorrências com equipamento e filtros
- **Histórico de alterações** (tela nova, técnico): registra quem cadastrou, editou, mudou a situação, excluiu ou reativou laboratórios e equipamentos, com o que mudou (ex.: patrimônio 'PAT-0003' → 'PAT-0300'). Tabela nova `historico_alteracao`.
- **Edição de equipamentos**: nome, patrimônio e laboratório. O patrimônio continua único; mudar de laboratório é bloqueado se houver reservas futuras (E30). Laboratórios já eram editáveis na lista e agora também entram no histórico.
- **Ocorrência ligada ao equipamento**: o técnico escolhe o equipamento usado na reserva e pode colocá-lo em manutenção na hora (E31, S15).
- **Filtros e busca**: tela Reservas do técnico (laboratório, situação, período e solicitante/finalidade), filtros na lista de Equipamentos e busca no Histórico.
- Banco: tabela `historico_alteracao`. Para bancos já existentes: `database/migracao_2_2.sql` (depois da 2_1).
- 16 novos testes automatizados (total 76).

## 2.1 – exclusão de equipamentos e laboratórios
- Exclusão lógica de equipamentos e laboratórios com motivo obrigatório; data e responsável ficam registrados. O histórico de reservas, ocorrências e o relatório continuam completos.
- Nova tela **Itens excluídos** (técnico), com abas Equipamentos e Laboratórios, e botão **Reativar**.
- Ao excluir um laboratório, o técnico escolhe se os equipamentos saem junto ou ficam na lista.
- Bloqueios: laboratório ou equipamento com reservas futuras pendentes/aprovadas não pode ser excluído (E27, E28); equipamento cujo laboratório está excluído não pode ser reativado (E29).
- Número de patrimônio e nome de laboratório continuam únicos, inclusive entre os excluídos.
- Banco: colunas `excluido`, `excluido_em`, `excluido_por`, `motivo_exclusao` nas tabelas `laboratorio` e `equipamento`. Para bancos já existentes: `database/migracao_2_1.sql`.
- 16 novos testes automatizados (total 60).

## 2.0.1 – implantação em nuvem
- Aplicação publicada no Render, com banco MySQL 8 no Aiven.
- Conexão com SSL opcional (`DB_SSL_CA`); credenciais do banco sem espaços nas pontas (`.strip()`).
- `database/aplicar_schema.py`: cria as tabelas sem precisar do cliente `mysql` e ignora comandos não permitidos em nuvem.
- Documentação atualizada: implantação real, problemas encontrados (D05, D06), diagrama de implantação e roteiros de vídeo.

## 2.0 – após feedback dos colegas
- Erros de formulário exibidos junto de cada campo, com marcação de acessibilidade e foco automático.
- Mensagens de sucesso mais informativas (reserva, aprovação e recusa).
- Recusa sem motivo exibe o erro na linha da reserva.
- Bloqueio temporário após 5 tentativas de login incorretas (E25).
- Relatório de uso exportável em CSV.
- Indicador de etapas na tela de reserva; ajuda na primeira visita; link "Pular para o conteúdo".
- Cookie de sessão `Secure` configurável por variável de ambiente.
- 19 novos testes automatizados (total 44).

## 1.0 – primeira versão testada
- Cadastro, login, reservas com validação de conflito, painel do técnico, laboratórios, equipamentos, ocorrências e relatório.
- Banco MySQL 8 normalizado (3FN), UML e IHC documentados, 25 testes automatizados.
