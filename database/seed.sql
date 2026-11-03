-- Dados iniciais de laboratórios e equipamentos (MySQL).
-- Usuários (com senha criptografada) são criados por:  python -m app.seed
USE labagenda;
INSERT INTO laboratorio (nome, localizacao, capacidade) VALUES
 ('Laboratório de Redes', 'Bloco B - Sala 12', 30),
 ('Laboratório de Programação', 'Bloco A - Sala 03', 40),
 ('Laboratório de Eletrônica', 'Bloco C - Sala 01', 20);
INSERT INTO equipamento (id_laboratorio, nome, numero_patrimonio) VALUES
 (1, 'Switch gerenciável 24p', 'PAT-0001'),
 (1, 'Roteador Cisco 2901', 'PAT-0002'),
 (2, 'Projetor Epson', 'PAT-0003'),
 (2, 'Kit de 10 notebooks', 'PAT-0004'),
 (3, 'Osciloscópio digital', 'PAT-0005'),
 (3, 'Fonte de bancada', 'PAT-0006');
