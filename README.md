# Sistema de Gestão de Eventos e Espaços

Projeto da disciplina **SCC0540 — Bases de Dados** (ICMC-USP, 2026/2).

Sistema para organizar eventos, edições, promotores, atividades, sessões, espaços e inscrições. Inclui controle de vagas, restrições de agendamento, papéis dos participantes e histórico de mudanças na programação.

## Tecnologias

- **PostgreSQL 18** — modelo relacional, consultas e regras de integridade com funções e triggers.
- **Python 3.11+** — aplicação de linha de comando e acesso ao PostgreSQL com `psycopg`.
- **Ollama** — execução local do modelo `qwen2.5-coder:1.5b` para consultas em linguagem natural.
- **Graphviz (DOT), draw.io e Mermaid** — documentação e diagramas do banco.

## Estrutura do projeto

| Arquivo / diretório | Conteúdo |
| --- | --- |
| `Projeto.txt` | Descrição do sistema, decisões de projeto, DDL completo e cinco consultas SQL |
| `DML.sql` | Dados fictícios para demonstração |
| `Instrucoes.txt` | Instalação, configuração, execução e limitações |
| `Prototipo/` | Aplicação Python, dependências e configuração de exemplo |
| `Prototipo.zip` | Pacote do protótipo conforme o formato solicitado |
| `ER.pdf` e `ER.xml` | Modelo conceitual E/R, em notação Chen |
| `Relacional.pdf` e `Relacional.mmd` | Modelo relacional em notação Crow's Foot |
| `diagramas/` | Fontes DOT, SVG e diagramas editáveis |
| `sql/` | Arquivos auxiliares do DDL e das consultas |
| `Entrega-BD.zip` | Conjunto dos oito artefatos de entrega |

## Execução

Consulte **`Instrucoes.txt`** para criar a base, carregar o DML e executar o protótipo. A estrutura esperada é:

```text
Projeto/
├── Projeto.txt
└── Prototipo/
    ├── main.py
    ├── config.json
    └── requirements.txt
```

Com PostgreSQL e Ollama configurados, dentro de `Prototipo/`:

```bash
python -m pip install -r requirements.txt
python main.py
```

Ajuste somente o `config.json` para as informações do seu ambiente. Os valores versionados são exemplos e não devem ser substituídos por credenciais reais no repositório.

## Funcionalidades

- Cadastro e programação de eventos, atividades, sessões e espaços.
- Inscrição geral no evento e inscrição específica em sessões com vagas limitadas.
- Promoção conjunta, papéis acumuláveis e edições independentes.
- Restrições de capacidade e de conflitos de horário, com triggers PostgreSQL.
- Registro do histórico de reagendamentos.
- Cinco consultas SQL e geração de consultas a partir de linguagem natural.

O modelo local pode produzir SQL incorreto; o aplicativo apresenta a consulta gerada e o resultado ou erro correspondente. Para requisitos e limitações detalhados, consulte `Projeto.txt` e `Instrucoes.txt`.

## Homologação de 02/11/2026

O roteiro Windows está em `TESTE_EM_OUTRAS_MAQUINAS.md`, com scripts em `apoio_homologacao/` e distribuição separada em `Apoio-Homologacao.zip`. Relatórios e evidências de execução ficam na pasta de auditoria local, fora do repositório. O ZIP oficial e os componentes aprovados permanecem idênticos; o apoio não entra na submissão de 03/11. Testes nos PCs dos integrantes e o aceite da legibilidade em página inteira ainda dependem da revisão presencial.

## Integrantes

Ana Luíza, Mônica, Gabriel, Larissa e Ana Araújo.

**Disciplina:** SCC0540 — Bases de Dados | **Semestre:** 2026/2
