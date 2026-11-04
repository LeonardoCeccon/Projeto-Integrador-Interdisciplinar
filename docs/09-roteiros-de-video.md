# 9. Roteiros dos vídeos

Os textos estão em primeira pessoa para você ler com suas palavras. Troque o que estiver entre `[colchetes]`.
Dica geral: grave a tela do navegador em 1080p, feche abas e notificações, use zoom de 110% e fale devagar.

## Preparação antes de gravar (vale para os dois vídeos)
1. Use o **site publicado** (https://projeto-integrador-interdisciplinar.onrender.com). Abra a URL alguns minutos antes: no plano gratuito o primeiro acesso demora cerca de um minuto. Banco com carga inicial feita (`aplicar_schema.py` e `python -m app.seed`).
2. Três janelas ou perfis de navegador já abertos: **professor**, **técnico** e **aluno** (ou entre e saia durante a gravação).
3. Tenha pronta uma reserva **aprovada** com data de ontem para demonstrar a ocorrência (ou use o relatório com dados antigos).
4. Abra também: repositório no GitHub, `docs/img/uml_classes.png`, `docs/img/uml_der.png`, terminal na pasta do projeto.
5. Faça um ensaio cronometrado. Se passar do tempo, corte a parte marcada como *opcional*.

---

# VÍDEO 1 – O projeto e como ele funciona (mínimo 5 min, meta: 7:30)

| Bloco | Tempo | Tela | 
|---|---|---|
| 1. Abertura | 0:00–0:30 | Tela de login |
| 2. O problema | 0:30–1:30 | README no GitHub |
| 3. Perfis e casos de uso | 1:30–2:30 | `uml_casos_de_uso.png` |
| 4. Demonstração | 2:30–5:50 | Sistema em funcionamento (professor, técnico e aluno) |
| 5. Banco de dados | 5:50–6:35 | `uml_der.png` e `schema.sql` |
| 6. Arquitetura, Git e testes | 6:35–7:10 | Estrutura do repositório e terminal |
| 7. Encerramento | 7:10–7:30 | Tela de login |

### 1. Abertura (0:30)
> "Olá, eu sou [seu nome], RGM [seu RGM]. Neste vídeo vou apresentar o **LabAgenda**, o meu Projeto Integrador: um sistema web para reservar laboratórios e equipamentos de uma instituição de ensino. Vou mostrar qual problema ele resolve, como funciona na prática e como foi construído."

### 2. O problema (1:00)
*Mostre o README e a seção 1.1 de `docs/01-escopo.md`.*
> "Em muitos lugares, a agenda dos laboratórios fica em planilha ou grupo de mensagens. Isso causa conflitos, como duas turmas marcadas na mesma sala, equipamentos pedidos que estão quebrados e nenhuma informação sobre quanto cada laboratório é usado.
> O LabAgenda resolve isso com regras automáticas: o sistema não deixa duas reservas ocuparem o mesmo laboratório ao mesmo tempo, e o técnico decide cada pedido num painel único.
> Foi feito em Python com Flask, o banco de dados é o MySQL 8 hospedado no Aiven e a aplicação está publicada no Render."

### 3. Perfis e casos de uso (1:00)
*Mostre `uml_casos_de_uso.png`.*
> "Existem dois grupos de usuários. O **solicitante**, que pode ser aluno ou professor, cria conta, consulta horários ocupados, pede reservas, cancela e acompanha os seus pedidos. E o **técnico**, que avalia as reservas, cadastra laboratórios e equipamentos, registra ocorrências e emite o relatório de uso.
> No diagrama, o caso de uso de solicitar reserva inclui a consulta de disponibilidade e a autenticação."

### 4. Demonstração (3:20)
*Siga esta ordem. Fale enquanto clica.*

**4.1 Conta e login (0:30)**
1. Clique em *Criar conta*, preencha nome, e-mail, senha e perfil *Professor*; crie e entre.
> "Aqui eu crio uma conta. A senha exige 8 caracteres com letras e números, e fica guardada só como hash."

**4.2 Reserva (1:00)**
2. *Nova reserva* → Laboratório de Redes, data de amanhã → *Ver horários ocupados*.
3. Peça 08:00–10:00 com um equipamento e envie.
> "Primeiro eu consulto os horários ocupados, depois faço o pedido. Ele entra como **pendente**, e a mensagem confirma laboratório, data e horário."
4. Faça um segundo pedido 09:00–11:00.
> "Se eu tentar um horário que se sobrepõe, o sistema recusa e mostra o erro junto do campo. Já um horário que começa exatamente quando o outro termina é aceito."

**4.3 Técnico (0:45)**
5. Saia, entre como técnico. Mostre os pendentes.
6. Clique em *Recusar* sem motivo → mostre o erro. Depois recuse com motivo em uma reserva e aprove outra.
> "O técnico só recusa informando o motivo. O solicitante vai ver esse motivo na própria lista."

**4.3-B Acesso do aluno (0:20)**
*Saia e entre como aluno: `aluno@labagenda.test` / `Aluno1234`.*
> "O aluno tem o mesmo acesso do professor para reservar: consulta horários, pede e cancela reservas. Mas repare que no menu ele não tem Equipamentos, Ocorrências nem Relatório."
*Digite `/relatorio` no final do endereço do site.*
> "Mesmo digitando o endereço na mão, o sistema barra e mostra que ele não tem permissão. Essa regra é validada no servidor, e não só escondida no menu."

**4.4 Cadastros, ocorrência e relatório (0:45)**
7. *Equipamentos*: coloque um em manutenção.
> "Equipamento em manutenção deixa de aparecer na hora de reservar."
8. *Ocorrências*: registre uma ocorrência numa reserva aprovada que já começou.
9. *Relatório*: escolha o período e mostre horas por laboratório.
> "O relatório soma as horas das reservas aprovadas por laboratório, e ajuda a decidir manutenção e compras."
10. *(Opcional)* Diminua a janela do navegador para mostrar a versão de celular.

### 5. Banco de dados (0:45)
*Mostre `uml_der.png` e depois trechos do `schema.sql`.*
> "O banco tem seis tabelas: usuário, laboratório, equipamento, reserva, reserva_equipamento e ocorrência. A relação entre reserva e equipamento é muitos para muitos, resolvida pela tabela associativa. Parti de uma tabela única e normalizei até a terceira forma normal.
> No script físico uso chaves estrangeiras, restrições de unicidade, `CHECK` para horário e capacidade, e um índice composto por laboratório, data e hora, que acelera a verificação de conflito. A aplicação conecta com um usuário de mínimo privilégio, sem permissão de apagar. Tem também um dicionário de dados completo."

### 6. Arquitetura, Git e testes (0:35)
*Mostre `docs/img/uml_implantacao.png`, o GitHub e rode os testes no terminal.*
> "Na implantação, o código vai para o GitHub e o Render publica automaticamente. A aplicação conecta ao MySQL do Aiven com SSL, usando variáveis de ambiente, e nenhuma senha fica no código."
> "O código tem três camadas: rotas, serviços com as regras de negócio e acesso a dados. Tudo está no GitHub: código, banco e documentação, com histórico de commits e versões marcadas.
> Os testes automatizados cobrem as regras principais. Vou rodá-los agora."
```bash
python -m unittest discover -s tests
```
> "Todos passaram."

### 7. Encerramento (0:20)
> "Esse foi o LabAgenda: um sistema que evita conflitos de agenda, dá autonomia ao solicitante e visibilidade ao técnico. No próximo vídeo mostro as melhorias que fiz depois do feedback dos meus colegas. Obrigado!"

---

# VÍDEO 2 – Implementações pós-feedback (máximo 5 min, meta: 4:30)

| Bloco | Tempo | Tela |
|---|---|---|
| 1. Abertura | 0:00–0:20 | Documento Word / tabela de testes |
| 2. Como coletei o feedback | 0:20–1:00 | Tabelas dos 5 colegas |
| 3. Mudança 1: erros ao lado do campo | 1:00–2:00 | v1.0 × v2.0 no login e reserva |
| 4. Mudanças 2 e 3: mensagens e recusa | 2:00–2:50 | Reserva e painel do técnico |
| 5. Mudanças 4 e 5: segurança e relatório | 2:50–3:40 | Login bloqueado e CSV |
| 6. Usabilidade e acessibilidade | 3:40–4:10 | Painel vazio, etapas, teclado |
| 7. Testes, Git e encerramento | 4:10–4:40 | Terminal e GitHub |

### 1. Abertura (0:20)
> "Olá, sou [seu nome]. Neste vídeo mostro o que mudei no LabAgenda depois que cinco colegas testaram a versão 1.0. Aplicando a ideia de melhoria contínua, o Kaizen, cada ponto virou uma ação, um teste e uma versão nova: a 2.0."

### 2. Como coletei o feedback (0:40)
*Mostre as 5 tabelas e o `docs/08-feedback-e-versao-2.md`.*
> "Cada colega recebeu um roteiro com foco diferente: acesso, reservas, painel do técnico, cadastros e usabilidade. Entre as respostas, [colega 1] apontou que as mensagens ao deixar campos vazios ou digitar e-mail inválido não estavam claras. Os outros colegas listaram pontos que precisavam ser verificados, como conflito de horário, recusa sem motivo, laboratório desativado e telas no celular.
> Então eu fiz duas coisas: corrigi o problema concreto e transformei **cada ponto em teste automatizado**, para garantir que ele continue funcionando."

### 3. Mudança 1 – Erros ao lado do campo (1:00)
*Abra a v1.0 (`git checkout v1.0` ou capturas antigas) e depois a v2.0.*
> "Na versão 1.0, quando o campo estava vazio, o aviso aparecia só no topo da página. Eu reproduzi isso e concordei com o feedback.
> Na 2.0, o erro aparece **ao lado do campo**, em vermelho, com ícone, a borda do campo é destacada e o cursor já vai para o primeiro campo com problema."
*Demonstre:* login vazio → cadastro com e-mail sem @ → reserva sem horário.
> "Para quem usa leitor de tela, o campo também é marcado como inválido e ligado à sua mensagem."

### 4. Mudanças 2 e 3 – Mensagens e recusa (0:50)
*Faça uma reserva e depois decida como técnico.*
> "A confirmação da reserva agora diz laboratório, data e horário. No painel do técnico, aprovar ou recusar informa o número da reserva e o nome do solicitante. E quando o técnico tenta recusar sem motivo, o erro aparece na própria linha da reserva, que continua pendente."
> "Também confirmei por teste que o solicitante vê o motivo da recusa e que o aluno não acessa relatório, equipamentos nem ocorrências."

### 5. Mudanças 4 e 5 – Segurança e relatório (0:50)
*Digite 5 senhas erradas; depois mostre o relatório e clique em Baixar CSV e abra no Excel.*
> "Depois de cinco senhas erradas, o acesso é bloqueado por dez minutos, mesmo que a senha certa seja digitada em seguida. Isso reduz o risco de adivinhação de senhas.
> No relatório de uso, agora é possível baixar um CSV, que abre direto no Excel e protege contra fórmulas maliciosas."

### 6. Usabilidade e acessibilidade (0:30)
*Mostre painel de um usuário novo, indicador de etapas, tecla Tab e a janela estreita.*
> "Para quem usa pela primeira vez, o painel vazio explica como reservar em três passos, e a tela de reserva mostra em que etapa a pessoa está. Adicionei um link 'Pular para o conteúdo' para quem navega só com o teclado. No celular, as tabelas viram cartões."

### 7. Testes, Git e encerramento (0:30)
*Rode os testes e mostre as tags no GitHub.*
> "A suíte de testes passou de 25 para 44 testes, todos passando. No Git, a versão testada pelos colegas está marcada como v1.0 e a nova como v2.0, e o histórico completo está no CHANGELOG.
> Ficam para o próximo ciclo as notificações por e-mail e a recuperação de senha, e repetir o teste com os colegas medindo o tempo da primeira reserva. Obrigado!"

---

## Checklist final dos vídeos
- [ ] Vídeo 1 com no mínimo 5 minutos, áudio claro, nome e RGM falados.
- [ ] Vídeo 2 com no máximo 5 minutos.
- [ ] Links no documento Word (o do vídeo 1 na tabela de codificação; o do vídeo 2 na tabela final).
- [ ] Visibilidade do vídeo configurada para quem tem o link (não privada).
- [ ] Repositório público com as tags `v1.0` e `v2.0`.
