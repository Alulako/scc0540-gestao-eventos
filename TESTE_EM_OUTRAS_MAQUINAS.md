# Homologação Windows - revisão de 02/11/2026

A entrega oficial BSI é em **03/11/2026**. Este roteiro e `apoio_homologacao/` são materiais internos de teste: **não entram em Entrega-BD.zip**. Cada integrante deve testar a mesma versão aprovada, usando seu próprio computador/base. A revisão coletiva não exige refazer módulos ou mudar o esquema.

Integrantes: Ana Luíza, Mônica, Gabriel, Larissa e Ana Araújo. O grupo informou não ter identificador; não preencher nomes completos, matrículas ou números de grupo inventados. Os campos de NUSP da avaliação individual pertencem a outro documento, não à instalação deste projeto.

## 0. Primeiro acesso: clonar o GitHub, mesmo sem conhecer Git

**Faça esta seção ANTES das seções 1 e 2.** O objetivo é baixar uma cópia do repositório e colocar os dois ZIPs na pasta Downloads para seguir os comandos de teste sem mudar nada.

1. **Instale o Git para Windows**, se ainda não tiver: https://git-scm.com/downloads/win . Aceite as opções padrão do instalador e feche/reabra o terminal ao terminar.
2. Abra **PowerShell** pelo menu Iniciar do Windows (pesquise `PowerShell`; não precisa executar como administrador).
3. Copie **uma linha de cada vez**, pressionando Enter. Na primeira vez, use este bloco:

   ```powershell
   git --version
   Set-Location (Join-Path $env:USERPROFILE 'Downloads')
   git clone https://github.com/Alulako/scc0540-gestao-eventos.git
   Set-Location .\scc0540-gestao-eventos
   git status -sb
   Get-Item .\Entrega-BD.zip, .\Apoio-Homologacao.zip, .\TESTE_EM_OUTRAS_MAQUINAS.md
   Copy-Item -LiteralPath .\Entrega-BD.zip, .\Apoio-Homologacao.zip -Destination ..
   Set-Location ..
   Get-Item .\Entrega-BD.zip, .\Apoio-Homologacao.zip
   ```

4. **Confira o resultado**:
   - `git --version` mostra a versão instalada. Se disser que `git` não é reconhecido, instale o Git e reabra o PowerShell antes de continuar.
   - `git clone` baixa a pasta `scc0540-gestao-eventos` para Downloads. Não é necessário criar branches, fazer commits ou configurar uma conta Git local.
   - `git status -sb` normalmente mostra `## main...origin/main`. Não deve apresentar arquivos modificados.
   - Os últimos comandos conferem os arquivos e **copiam** `Entrega-BD.zip` e `Apoio-Homologacao.zip` para a pasta Downloads, **sem mover ou alterar** os originais.
5. **Se já clonou anteriormente**, NÃO repita `git clone` na mesma pasta (isso causa o erro `destination path already exists`). Para atualizar a cópia, use:

   ```powershell
   Set-Location (Join-Path $env:USERPROFILE 'Downloads\scc0540-gestao-eventos')
   git pull --ff-only origin main
   git status -sb
   Copy-Item -LiteralPath .\Entrega-BD.zip, .\Apoio-Homologacao.zip -Destination (Join-Path $env:USERPROFILE 'Downloads') -Force
   ```

   Esse segundo bloco presume que ninguém editou os arquivos dentro do repositório. **Edite `config.json` somente na cópia extraída na seção 2**, nunca na pasta clonada; assim será possível atualizar a cópia sem conflitos.

**Problemas comuns:**
- `fatal: repository not found` ou pedido de permissão: confira o link e peça acesso ao repositório se for privado. Não compartilhe senha ou token no grupo.
- `destination path ... already exists`: use o bloco `git pull` acima, não apague a pasta.
- `Get-Item` diz que falta um dos dois ZIPs: a clonagem não terminou corretamente; não continue os testes até encontrar ambos.

**Pronto:** os dois ZIPs estão em Downloads. Siga as seções 1 (pré-requisitos) e 2 (extração em pasta limpa); as seções 3–10 ensinam os testes. **Não use `git push`, `git add` ou `git commit` para esta homologação.**

## 1. Preparar hoje, antes de ficar sem Internet

Levar `Entrega-BD.zip` e `Apoio-Homologacao.zip`. O segundo contém este roteiro, os dois scripts de apoio e o manifesto dos arquivos aprovados. Nunca enviar o segundo ZIP ao professor. Não levar `.venv`, `.local`, bases da Ana nem configurações pessoais como substitutos da instalação.

Requisitos:

1. Python **3.11+**, 64 bits; esta versão do projeto foi testada com Python 3.12.4. Se já houver versão compatível, reutilizá-la. Para instalar, usar [Python oficial para Windows](https://www.python.org/downloads/windows/). Com o Python Install Manager, `py install 3.12` instala um runtime da série usada nos testes; `py -3.12 --version` deve responder. Com o instalador tradicional, instalar o launcher e o pip. Não substituir uma instalação existente para seguir o roteiro. [Documentação oficial](https://docs.python.org/3/using/windows.html).
2. PostgreSQL: baseline testada na versão 18. Se não houver servidor, usar o [instalador indicado pelo PostgreSQL](https://www.postgresql.org/download/windows/), incluindo servidor e ferramentas de linha de comando; pgAdmin é opcional. Anotar porta e usuário locais. Guardar a senha localmente; não colocar senha em comando, print, captura ou mensagem do grupo. O usuário precisa de `CREATEDB` para a carga automatizada. Não alterar serviços ou bases preexistentes.
3. **Ollama + modelo Qwen (obrigatório para testar a IA):**
   1. Acesse **https://ollama.com/download/windows**, baixe o instalador para Windows e conclua a instalação. Abra o aplicativo Ollama pelo menu Iniciar. Ele funciona **localmente**; não é necessário criar conta em serviços de IA.
   2. **Feche e reabra o PowerShell** após a instalação. Verifique:
      
      ```powershell
      ollama --version
      ```

      Se aparecer que `ollama` não é reconhecido, confira a instalação, abra o Ollama pelo menu Iniciar e reabra o PowerShell. Não continue enquanto o comando não funcionar.
   3. **Baixe exatamente o modelo usado no projeto** (cerca de 1 GB de download; exige Internet):
      
      ```powershell
      ollama pull qwen2.5-coder:1.5b
      ```

      Aguarde a conclusão do download. **Não baixe somente `qwen2.5-coder` sem `:1.5b`**, pois isso seleciona outro tamanho de modelo.
   4. Confira se o modelo realmente foi instalado e faça uma pergunta curta:
      
      ```powershell
      ollama list
      ollama run qwen2.5-coder:1.5b "Responda apenas OK"
      ```

      `ollama list` deve mostrar `qwen2.5-coder:1.5b`; o segundo comando deve retornar uma resposta (o texto pode variar). Se entrar no modo de conversa, digite `/bye` para sair. Uma resposta aqui não substitui os testes do protótipo nas seções 7–8.
   5. **Verifique o servidor da API**, que o Python precisa acessar:
      
      ```powershell
      Invoke-RestMethod -Uri 'http://localhost:11434/api/tags' -Method Get | Select-Object -ExpandProperty models | Select-Object name
      ```

      O resultado deve conter o mesmo modelo. Se der erro de conexão, abra o Ollama pelo menu Iniciar e repita. Em instalações apenas de linha de comando, execute `ollama serve` em um **segundo PowerShell** e mantenha essa janela aberta; **não execute outro `ollama serve` se o Ollama já estiver funcionando**.

   Links oficiais: [instalação no Windows](https://docs.ollama.com/windows), [modelo específico qwen2.5-coder:1.5b](https://ollama.com/library/qwen2.5-coder:1.5b) e [API de modelos](https://docs.ollama.com/api/tags). O modelo permanece no computador; as perguntas dos testes devem ser processadas localmente.

Instalar dependências e baixar o modelo hoje. O desempenho de geração depende do hardware; a presença do modelo na lista não prova que ele consegue gerar SQL dentro do timeout de 180 segundos do protótipo. Não usar modelo de nuvem na demonstração.

## 2. Começar numa pasta limpa

Copiar os dois ZIPs para Downloads. Abrir **PowerShell** e executar o bloco abaixo. Os caminhos são derivados do perfil da pessoa; não há caminho da máquina da Ana. O nome com timestamp evita sobrescrever uma revisão anterior.

```powershell
Set-Location (Join-Path $env:USERPROFILE 'Downloads')
$pastaRevisao = 'Revisao-BD-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
New-Item -ItemType Directory -Path $pastaRevisao -ErrorAction Stop
Copy-Item -LiteralPath .\Entrega-BD.zip, .\Apoio-Homologacao.zip -Destination $pastaRevisao
Set-Location $pastaRevisao
Expand-Archive -LiteralPath .\Entrega-BD.zip -DestinationPath .\ProjetoBD
Expand-Archive -LiteralPath .\ProjetoBD\Prototipo.zip -DestinationPath .\ProjetoBD\Prototipo
Expand-Archive -LiteralPath .\Apoio-Homologacao.zip -DestinationPath .
Get-FileHash -LiteralPath .\Entrega-BD.zip -Algorithm SHA256
```

SHA256 aprovado do ZIP oficial:

```text
cfd7cc4a1a65684ca34d68a1e1cbeafc20bccc3045bc1e88d8a641ff68f9e9c1
```

Se divergir, parar a homologação e obter a versão correta. O oficial deve conter somente ER.pdf, ER.xml, Relacional.pdf, Relacional.mmd, Projeto.txt, DML.sql, Prototipo.zip e Instrucoes.txt. `Prototipo.zip` contém somente main.py, config.json e requirements.txt, sem pasta interna. A estrutura após extração é:

```text
Revisao-BD-.../
  Entrega-BD.zip
  Apoio-Homologacao.zip
  TESTE_EM_OUTRAS_MAQUINAS.md
  apoio_homologacao/
    pre_verificar_ambiente.py
    homologar.py
    manifesto-aprovado.json
  ProjetoBD/
    Projeto.txt  DML.sql  Instrucoes.txt  ER.pdf  ER.xml
    Relacional.pdf  Relacional.mmd  Prototipo.zip
    Prototipo/
      main.py  config.json  requirements.txt
```

## 3. Ambiente Python isolado

Ainda na pasta Revisao-BD, criar **um venv novo**, sem alterar instalações existentes:

```powershell
py -3.12 -m venv .venv
$env:Path = (Resolve-Path .\.venv\Scripts).Path + ';' + $env:Path
$env:PYTHONUTF8 = '1'
python --version
python -c "import sys; print('venv ativo:', sys.prefix != sys.base_prefix)"
python -m pip install -r .\ProjetoBD\Prototipo\requirements.txt
python -m pip show ollama psycopg psycopg-binary
```

Se a pessoa já usa 3.11 ou outra versão compatível, selecionar essa versão no primeiro comando, por exemplo `py -3.11 -m venv .venv`. `venv ativo: True` confirma que o processo está isolado. Não é necessário ativar scripts PowerShell nem mudar a política de execução. A alteração de PATH vale apenas neste terminal; reabrindo-o, repetir as duas linhas `$env:Path` e `$env:PYTHONUTF8` na pasta Revisao-BD.

Resultado esperado: instalação sem erro e importação das duas dependências exigidas. Se download/permissão/antivírus impedir a instalação, registrar o bloqueio e **NÃO TESTADO** nos testes dependentes; não marcar a execução como aprovada.

## 4. Configurar somente config.json

```powershell
notepad .\ProjetoBD\Prototipo\config.json
```

Alterar os valores do JSON para o servidor desta máquina. Manter as chaves e salvar em **UTF-8 sem BOM**. A porta é número inteiro, sem aspas. Usar um nome de base novo com prefixo `homologacao_`, apenas minúsculas, números e `_`, por exemplo `homologacao_monica_20261102_01`. Se já existir, usar `_02`; não apagar/reutilizar a base anterior.

```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "dbname": "homologacao_monica_20261102_01",
    "user": "postgres",
    "password": "SUBSTITUIR_SOMENTE_NESTA_COPIA_LOCAL"
  },
  "ollama": {
    "host": "http://localhost:11434",
    "model": "qwen2.5-coder:1.5b"
  }
}
```

Não editar `main.py`, SQL, Projeto.txt ou requirements.txt. Não recomprimir o config pessoal dentro dos ZIPs e não enviá-lo no grupo. Os scripts de apoio não imprimem valores do config nem mensagens completas de erro de conexão.

## 5. Pré-verificação automática, somente leitura

```powershell
python .\apoio_homologacao\pre_verificar_ambiente.py --projeto .\ProjetoBD --saida .\resultados\pre-antes.json
```

Verifica Python, dependências, integridade dos entregáveis, config, porta PostgreSQL, existência da base, conexão Python/PostgreSQL, API Ollama e presença do modelo. **Não instala, cria base, carrega DDL/DML, gera SQL ou imprime senha.** `psql` ausente do PATH é apenas informativo; a automação usa psycopg.

Antes da etapa seguinte, espera-se que a base nova ainda não exista: `Existencia da base: FALHOU`, com confirmação de inexistência pelo catálogo/servidor, é o bloqueio esperado nesse momento. A consulta de catálogo usa a base de manutenção `postgres` em READ ONLY quando a abertura da base alvo falha; se nem essa consulta for possível, a existência fica NÃO TESTADO. Python, arquivos, porta, API e modelo devem passar. Falha de autenticação, porta ou JSON precisa ser resolvida no config/serviço antes da carga. Se for impossível resolver uma dependência, registrar o bloqueio sem alegar sucesso.

## 6. Criar base vazia e executar DDL/DML, consultas e demonstração de triggers

```powershell
python .\apoio_homologacao\homologar.py --projeto .\ProjetoBD --criar-e-testar --saida .\resultados\carga-e-consultas.json
```

A automação usa os dados de conexão de config.json para acessar a base de manutenção `postgres`, confirma que o nome configurado é novo e começa com `homologacao_`, cria a base em UTF-8 a partir de template0 e comprova que está vazia. Em seguida importa o **main.py original**, extrai o DDL e as cinco consultas de **Projeto.txt**, executa DML.sql, confere resultados, demonstra cinco finalidades de triggers com transações revertidas e executa o CLI em processo separado.

Se o nome já existir, a operação é **recusada antes de carregar SQL**. Não há DROP, TRUNCATE, exclusão ou restauração de bases. Se uma etapa falhar depois da criação, a base fica disponível para diagnóstico: escolher outro nome no config para repetir do zero. Não tentar contornar a recusa. As demonstrações de triggers só fazem escritas na base criada pela própria chamada e terminam com ROLLBACK; sequências podem avançar, sem alterar os registros da carga.

Resultados esperados:

- Zero tabelas de usuário antes do DDL; DDL e DML integralmente executados.
- 8 pessoas, 4 eventos, 7 atividades, 8 sessões e 2 registros de histórico.
- Consultas 1–5 retornam, respectivamente, **8, 5, 2, 4 e 2 linhas**.
- Consulta 2: vagas livres por sessão `{2:0, 8:0, 3:1, 6:3, 4:98}`.
- Consulta 3: pares `(evento_id,pessoa_id)` iguais a `(1,1)` e `(2,1)`.
- Consulta 4: top 3 do evento 1 são sessões 2, 8 e 3, nessa ordem; evento 2 tem sessão 6.
- Regras de conflito, período, vagas e elegibilidade: um caso permitido e outro rejeitado com SQLSTATE 23514. Histórico: UPDATE real +1, no-op +0 e rollback.
- Coluna inexistente: SQLSTATE 42703 capturado; consulta seguinte retorna 8 pessoas. CLI apresenta menu e continua depois de opção inválida.

O script não repete as 54 verificações de integração/concorrência da auditoria anterior; esta é uma homologação portátil da versão já aprovada. Não modificar o projeto para se adequar ao esquema simplificado do PDF de treinamento.

Depois da carga, repetir:

```powershell
python .\apoio_homologacao\pre_verificar_ambiente.py --projeto .\ProjetoBD --saida .\resultados\pre-depois.json
```

Esperado: tudo PASSOU, incluindo base e SELECT 1 em conexão READ ONLY. Retorno dos scripts: 0 = todos os testes solicitados passaram; 1 = houve falha; 2 = há item NÃO TESTADO. A carga sem `--ia` retorna 2 por ainda não ter solicitado geração: isso não converte a IA em aprovação.

## 7. Três perguntas reais ao Ollama

```powershell
python .\apoio_homologacao\homologar.py --projeto .\ProjetoBD --somente-leitura --ia --saida .\resultados\ollama.json
```

Esse modo não faz carga nem demonstrações de escrita. Compara as respostas geradas pelo modelo com consultas SQL de referência. O Ollama não é determinístico em todas as máquinas: comparar a **semântica e os resultados**, não apenas a presença de SQL. Se retornar SQL inválido ou resultado incorreto, registrar **FALHOU**. Se não foi executado por falta de dependência, registrar **NÃO TESTADO**. Timeout durante tentativa é falha daquela tentativa, não aprovação.

| Caso | Pergunta | Resultado esperado |
|---|---|---|
| Simples | Liste o id e o nome de todos os eventos ordenados pelo id. | 4 linhas, IDs 1–4; Semana de Tecnologia (1 e 2), Feira de Inovacao (3), Encontro em Planejamento (4). |
| JOIN | Liste o id e o titulo de cada atividade e o nome de seu evento. Use JOIN entre atividade.evento_id e evento.id. Ordene pelo id da atividade. | 7 linhas, IDs de atividade 1–7; atividades 1–4 e 7 no evento Semana de Tecnologia, 5 na edição 2027, 6 em Feira de Inovacao. Consulta usa JOIN pela FK correta. |
| Agregação | Quantas pessoas existem cadastradas na tabela pessoa? Retorne somente a contagem total. | Uma linha, total 8, usando COUNT. |

Para conferir manualmente as referências, usar pgAdmin na **base de homologação**, ou o menu/geração do próprio CLI:

```sql
SELECT id,nome FROM evento ORDER BY id;
SELECT a.id,a.titulo,e.nome
FROM atividade a JOIN evento e ON a.evento_id=e.id ORDER BY a.id;
SELECT count(*) FROM pessoa;
```

## 8. Demonstração interativa obrigatória

No terminal com venv ativo, iniciar exatamente como o professor exige:

```powershell
Set-Location .\ProjetoBD\Prototipo
python main.py
```

Digitar `7`, depois `1`, `2`, `3`, `4`, `5`, e conferir as quantidades acima. Digitar `6` e cada uma das três perguntas (uma por vez). O programa deve exibir SQL e resultados. Digitar `9`: deve mostrar `Opcao invalida.` e voltar ao menu. Digitar `7` novamente, comprovar conexão e sair com `0`. Não iniciar por notebook, servidor web ou editando main.py.

Para demonstrar **erro de serviço tratado sem parar o serviço real**, sair do programa, guardar o host Ollama original e editar apenas o config: temporariamente usar `http://127.0.0.1:1` (confirmar que não há serviço nessa porta). Iniciar `python main.py`, escolher `6` e perguntar algo simples. Esperado: `Servico indisponivel ou timeout`, sem traceback; a opção `7` continua funcionando, pois PostgreSQL não mudou. Sair e restaurar imediatamente o host original no config. Nunca interromper os serviços de outra pessoa para provocar erro.

O erro de SQL inválido 42703 é reproduzido automaticamente na etapa 6. A IA pode inventar uma coluna em perguntas fora do domínio; não usar uma resposta errada como exemplo de sucesso. Já houve esse comportamento na baseline e ele continua documentado.

Ao terminar o CLI, `Set-Location ..\..` volta à pasta Revisao-BD. Para rever consultas sem recarregar DML: `python .\apoio_homologacao\homologar.py --projeto .\ProjetoBD --somente-leitura --ia`. A base deve continuar com os dados aprovados.

## 9. Diagramas e identificação

Abrir ER.pdf e Relacional.pdf. Em **página inteira**, verificar se o desenho cabe numa página e permite entender a estrutura; depois usar zoom para ler atributos, chaves e cardinalidades. Registrar se a tela da pessoa torna os detalhes ilegíveis em página inteira. Zoom é necessário em telas pequenas; não imprimir o formato amplo em A4 supondo que os atributos manterão o tamanho original.

Conferir ER.xml no draw.io e Relacional.mmd no mermaid.ai como fontes editáveis, sem reexportar ou sobrescrever a versão aprovada durante o teste. O MER usa retângulos/losangos/elipses de Chen, sete IDs sublinhados e seis participações totais em linha dupla; Crow's Foot pertence somente ao relacional. Há 7 entidades no MER e 12 tabelas no relacional por causa do mapeamento de relacionamentos.

Ressalva já constatada em 01/11: ao reduzir cada página para 700 pixels de altura, os menores textos ficam em torno de 5 pixels; não são confortáveis para leitura de todos os detalhes. Isso foi registrado na auditoria, sem substituir os diagramas aprovados. Se o grupo exigir leitura de todos os rótulos nesse modo, a proposta é gerar uma **candidata** com disposição mais próxima de paisagem e menor espaço em branco: Graphviz/DOT para o MER e layout compacto no mermaid.ai para o relacional, mantendo todos os elementos, cardinalidades e participações. Recomparar nós/conectores e reexportar XML/PDF pelo draw.io e PDF/fonte pelo mermaid.ai antes de aprovar qualquer substituição. Apenas diminuir o tamanho físico da página não melhora a leitura em tela.

Se for encontrada perda de notação, corte ou texto sobreposto, registrar o local e interromper a substituição dos artefatos. Uma eventual correção deve manter fontes editáveis e reexportação pelos sites exigidos. O roteiro de teste não altera PDFs.

Conferir os cinco nomes disponíveis em Projeto.txt e Instrucoes.txt; não inventar sobrenomes/NUSP/identificador. A submissão de 03/11 ainda exige conferir no Moodle a eventual regra de nome do ZIP, ausente no PDF.

## 10. Registro por integrante

Cada pessoa copia esta tabela para um arquivo próprio, por exemplo `RESULTADO_MONICA.md`, e preenche **PASSOU, FALHOU ou NÃO TESTADO**, evidência e motivo. Os JSONs em resultados não contêm config/senha. Revisar capturas antes de compartilhá-las: nunca fotografar o config. Não enviar ambiente virtual, config pessoal ou bancos.

Integrante: __________  Data: 02/11/2026  Windows: __________

Python: __________  PostgreSQL: __________  Ollama/modelo: __________

| ID | Teste e resultado esperado | Estado inicial | Evidência/motivo |
|---|---|---|---|
| T01 | SHA256 do ZIP igual e oito arquivos oficiais | NÃO TESTADO | |
| T02 | Extração limpa; main.py/requirements iguais aos aprovados | NÃO TESTADO | |
| T03 | Python 3.11+ e duas dependências importáveis em venv | NÃO TESTADO | |
| T04 | PostgreSQL acessível com autenticação local | NÃO TESTADO | |
| T05 | Base nova criada vazia, sem tocar em bases existentes | NÃO TESTADO | |
| T06 | DDL extraído diretamente de Projeto.txt executa | NÃO TESTADO | |
| T07 | DML inteiro e contagens 8/4/7/8/2 | NÃO TESTADO | |
| T08 | Cinco SELECTs: 8/5/2/4/2 linhas e valores conferidos | NÃO TESTADO | |
| T09 | Triggers: casos permitidos/proibidos e histórico | NÃO TESTADO | |
| T10 | Conexão Python/PostgreSQL, opção 7 | NÃO TESTADO | |
| T11 | CLI iniciado por python main.py e opções 1–5 | NÃO TESTADO | |
| T12 | API Ollama e modelo local presente | NÃO TESTADO | |
| T13 | Pergunta simples: 4 eventos e SQL correto | NÃO TESTADO | |
| T14 | JOIN: 7 atividades com evento correto | NÃO TESTADO | |
| T15 | Agregação: COUNT = 8 | NÃO TESTADO | |
| T16 | Erro SQL 42703 capturado; consulta seguinte funciona | NÃO TESTADO | |
| T17 | Erro Ollama tratado; menu/conexão continuam; config restaurado | NÃO TESTADO | |
| T18 | PDFs completos; estrutura em página inteira; detalhes com zoom | NÃO TESTADO | |
| T19 | XML/MMD editáveis e consistência conceitual/física | NÃO TESTADO | |
| T20 | Nomes corretos, sem identificações inventadas e ZIP sem apoio | NÃO TESTADO | |

Coordenação consolida uma linha por pessoa, sem presumir que o teste em outro PC passou:

| Integrante | Computador testado? | T01–T20 | Bloqueio/ação |
|---|---|---|---|
| Ana Luíza | NÃO TESTADO nesta rodada presencial | NÃO TESTADO | |
| Mônica | NÃO TESTADO | NÃO TESTADO | |
| Gabriel | NÃO TESTADO | NÃO TESTADO | |
| Larissa | NÃO TESTADO | NÃO TESTADO | |
| Ana Araújo | NÃO TESTADO | NÃO TESTADO | |

Na revisão de 02/11, cada pessoa deve demonstrar conexão, uma consulta, uma pergunta e um erro tratado, além de explicar uma regra que não implementou. Congelar mudanças até revisar qualquer falha real com o grupo. Em 03/11, enviar somente o ZIP oficial após confirmar seu conteúdo/nome. A avaliação individual BSI de 10/11 é sem IA; o PDF 04 é treino independente, não alteração deste sistema.
