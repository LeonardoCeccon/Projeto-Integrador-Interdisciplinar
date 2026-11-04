# Histórico de versões

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
