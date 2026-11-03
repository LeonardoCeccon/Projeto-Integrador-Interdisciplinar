# LabAgenda

Sistema web para **reservar laboratórios e equipamentos** de uma instituição de ensino, com aprovação por um técnico,
registro de ocorrências e relatório de uso. Projeto Integrador Transdisciplinar II (Kaizen: melhoria contínua).

**Stack:** Python 3 · Flask · MySQL 8 (PyMySQL) · HTML/CSS · Git

| Quero… | Onde está |
|---|---|
| Entender o problema, requisitos e regras | [docs/01-escopo.md](docs/01-escopo.md) |
| Ver os diagramas UML | [docs/02-uml.md](docs/02-uml.md) |
| Ver telas, mensagens e acessibilidade | [docs/03-ihc.md](docs/03-ihc.md) |
| Modelo de dados e normalização | [docs/04-dados.md](docs/04-dados.md) |
| Script do banco e dicionário | [database/schema.sql](database/schema.sql), [database/dicionario_dados.md](database/dicionario_dados.md) |
| Testes e laudo | [docs/05-testes-e-laudo.md](docs/05-testes-e-laudo.md) |
| Roteiros de teste para colegas | [docs/07-roteiros-de-teste.md](docs/07-roteiros-de-teste.md) |
| Rodar o projeto | [docs/06-git-e-implantacao.md](docs/06-git-e-implantacao.md) |

```bash
python -m unittest discover -s tests -v   # 25 testes
```
