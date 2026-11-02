-- Dados inteiramente ficticios. Executar uma vez apos o DDL em base vazia.
BEGIN;
INSERT INTO pessoa (id,nome,email) VALUES
(1,'Alice Exemplo','alice@example.invalid'), (2,'Bruno Exemplo','bruno@example.invalid'),
(3,'Carla Exemplo','carla@example.invalid'), (4,'Diego Exemplo','diego@example.invalid'),
(5,'Eva Exemplo','eva@example.invalid'), (6,'Fabio Exemplo','fabio@example.invalid'),
(7,'Giovana Exemplo','giovana@example.invalid'), (8,'Hugo Exemplo','hugo@example.invalid');
INSERT INTO promotor (id,pessoa_id,organizacao) VALUES
(1,1,NULL), (2,NULL,'Instituto Ficticio de Tecnologia'), (3,NULL,'Associacao Exemplo');
INSERT INTO evento (id,nome,edicao,inicio,fim) VALUES
(1,'Semana de Tecnologia',1,'2026-11-02 08:00','2026-11-04 20:00'),
(2,'Semana de Tecnologia',2,'2027-11-02 08:00','2027-11-04 20:00'),
(3,'Feira de Inovacao',1,'2026-11-05 08:00','2026-11-05 20:00'),
(4,'Encontro em Planejamento',1,'2026-12-01 08:00','2026-12-01 18:00');
INSERT INTO promove VALUES (1,1),(2,1),(2,2),(3,3);
INSERT INTO espaco (id,nome,capacidade,recursos) VALUES
(1,'Auditorio Central',100,'projetor, audio, internet'),
(2,'Laboratorio A',4,'computadores, projetor, internet'),
(3,'Sala B',30,'projetor'), (4,'Estudio de Demonstracao',2,'computadores');
INSERT INTO atividade (id,evento_id,titulo,descricao,tipo) VALUES
(1,1,'Abertura e tendencias','Programacao geral','palestra'),
(2,1,'Workshop PostgreSQL','Duas oportunidades independentes','workshop'),
(3,1,'Python para Dados','Pratica guiada','minicurso'),
(4,1,'Painel de Carreiras','Programacao geral','painel'),
(5,2,'Workshop PostgreSQL 2027','Nova edicao independente','workshop'),
(6,3,'Demonstracao de Produtos','Apresentacoes abertas','apresentacao'),
(7,1,'Demonstracao Individual','Grupo pequeno','workshop');
INSERT INTO sessao (id,atividade_id,espaco_id,inicio,fim,requer_inscricao,limite_vagas) VALUES
(1,1,1,'2026-11-02 09:00','2026-11-02 10:00',false,NULL),
(2,2,2,'2026-11-02 10:00','2026-11-02 12:00',true,2),
(3,2,2,'2026-11-02 14:00','2026-11-02 16:00',true,3),
(4,3,3,'2026-11-03 09:00','2026-11-03 12:00',true,NULL),
(5,4,1,'2026-11-03 14:00','2026-11-03 16:00',false,NULL),
(6,5,2,'2027-11-02 10:00','2027-11-02 12:00',true,4),
(7,6,1,'2026-11-05 09:00','2026-11-05 11:00',false,NULL),
(8,7,4,'2026-11-04 10:00','2026-11-04 11:00',true,NULL);
INSERT INTO inscricao_evento (pessoa_id,evento_id,status) VALUES
(1,1,'confirmada'),(2,1,'confirmada'),(3,1,'confirmada'),(4,1,'confirmada'),
(5,1,'confirmada'),(6,1,'cancelada'),(7,1,'espera'),(8,1,'confirmada'),
(1,2,'confirmada'),(2,2,'confirmada'),(4,3,'confirmada');
INSERT INTO inscricao_sessao (pessoa_id,sessao_id,status) VALUES
(1,2,'confirmada'),(2,2,'confirmada'),(3,2,'espera'),(6,2,'cancelada'),
(1,3,'confirmada'),(3,3,'confirmada'),(4,3,'espera'),
(1,4,'confirmada'),(2,4,'confirmada'),(5,4,'cancelada'),
(1,6,'confirmada'),(1,8,'confirmada'),(2,8,'confirmada'),(8,8,'espera');
INSERT INTO papel_evento VALUES (1,1,'organizador'),(1,1,'colaborador'),(4,1,'colaborador'),(1,2,'organizador');
INSERT INTO papel_sessao VALUES (1,2,'instrutor'),(1,3,'instrutor'),(5,1,'palestrante'),(4,5,'moderador'),(5,5,'palestrante');
-- Historico real produzido pelo trigger, nao INSERT manual de historico.
UPDATE sessao SET inicio='2026-11-03 10:00', fim='2026-11-03 13:00' WHERE id=4;
UPDATE sessao SET espaco_id=1 WHERE id=4;
-- Ajustar sequencias apos IDs explicitos para permitir novas insercoes automaticas.
SELECT setval(pg_get_serial_sequence('pessoa','id'), (SELECT max(id) FROM pessoa));
SELECT setval(pg_get_serial_sequence('promotor','id'), (SELECT max(id) FROM promotor));
SELECT setval(pg_get_serial_sequence('evento','id'), (SELECT max(id) FROM evento));
SELECT setval(pg_get_serial_sequence('espaco','id'), (SELECT max(id) FROM espaco));
SELECT setval(pg_get_serial_sequence('atividade','id'), (SELECT max(id) FROM atividade));
SELECT setval(pg_get_serial_sequence('sessao','id'), (SELECT max(id) FROM sessao));
COMMIT;
