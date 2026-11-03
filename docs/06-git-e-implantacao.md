# 6. Git e implantação

## 6.1 Estrutura do repositório
```
labagenda/
├── README.md
├── requirements.txt
├── .env.example
├── app/                 código Flask (rotas, serviços, acesso a dados, templates, CSS)
├── database/            schema.sql, seed.sql, schema_sqlite.sql (testes), dicionario_dados.md
├── docs/                escopo, UML, IHC, dados, testes/laudo, imagens e fontes dos diagramas
└── tests/               testes automatizados
```

## 6.2 Fluxo de trabalho
- Ramo `main` sempre estável; trabalho em ramos `feature/…` ou `fix/…`.
- Commits pequenos, no imperativo: `Corrige botão cancelar em reserva encerrada`.
- Documentação e código mudam **no mesmo commit** quando a regra muda (ex.: RN05 → `01-escopo.md` + `services.py` + teste).
- Cada comentário de colega vira uma *issue* ou item do quadro Kaizen em `01-escopo.md`.

## 6.3 Publicar no GitHub
```bash
git remote add origin https://github.com/<seu-usuario>/labagenda.git
git push -u origin main
```
Deixe o repositório **público** (o enunciado pede código aberto). Nunca envie o arquivo `.env`.

## 6.4 Execução local
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # edite as senhas
mysql -u root -p < database/schema.sql
mysql -u root -p < database/seed.sql
export $(grep -v '^#' .env | xargs)
python -m app.seed
flask --app app run             # http://127.0.0.1:5000
```
Sem MySQL (apenas para testar): `DB_ENGINE=sqlite` e `python -c "from app import db; db.init_sqlite('labagenda_dev.sqlite3','database/schema_sqlite.sql')"`.

Usuários de demonstração (**trocar fora de ambiente de estudo**):
| Perfil | E-mail | Senha |
|---|---|---|
| Técnico | tecnico@labagenda.test | Tecnico123 |
| Professor | professor@labagenda.test | Professor123 |
| Aluno | aluno@labagenda.test | Aluno1234 |

## 6.5 Hospedagem
Opções gratuitas ou baratas que aceitam Python + MySQL: PythonAnywhere (MySQL incluído), Railway, Render com banco
gerenciado. Comando de produção: `gunicorn "app:create_app()"`. Defina `SECRET_KEY`, `DB_*` e HTTPS no painel do provedor.
