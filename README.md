# LabAgenda

Sistema web para **reservar laboratórios e equipamentos** de uma instituição de ensino, com aprovação por um técnico,
registro de ocorrências e relatório de uso. Projeto Integrador Transdisciplinar II (Kaizen: melhoria contínua).

**Stack:** Python 3 · Flask · MySQL 8 (PyMySQL) · HTML/CSS · Git

**Solução em funcionamento:** https://projeto-integrador-interdisciplinar.onrender.com  
**Código aberto:** https://github.com/LeonardoCeccon/Projeto-Integrador-Interdisciplinar  
**Hospedagem:** Render (aplicação) + Aiven (MySQL 8)

| Quero… | Onde está |
|---|---|
| Entender o problema, requisitos e regras | [docs/01-escopo.md](docs/01-escopo.md) |
| Ver os diagramas UML | [docs/02-uml.md](docs/02-uml.md) |
| Ver telas, mensagens e acessibilidade | [docs/03-ihc.md](docs/03-ihc.md) |
| Modelo de dados e normalização | [docs/04-dados.md](docs/04-dados.md) |
| Script do banco e dicionário | [database/schema.sql](database/schema.sql), [database/dicionario_dados.md](database/dicionario_dados.md) |
| Testes e laudo | [docs/05-testes-e-laudo.md](docs/05-testes-e-laudo.md) |
| Feedback dos colegas e versão 2.0 | [docs/08-feedback-e-versao-2.md](docs/08-feedback-e-versao-2.md), [CHANGELOG.md](CHANGELOG.md) |
| Roteiros dos vídeos | [docs/09-roteiros-de-video.md](docs/09-roteiros-de-video.md) |
| Roteiros de teste para colegas | [docs/07-roteiros-de-teste.md](docs/07-roteiros-de-teste.md) |
| Rodar e hospedar o projeto (Render + MySQL na nuvem) | [docs/06-git-e-implantacao.md](docs/06-git-e-implantacao.md) |

```bash
python -m unittest discover -s tests -v   # 78 testes
```
