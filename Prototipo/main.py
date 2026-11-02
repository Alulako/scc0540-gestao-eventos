"""CLI SCC0540. Configuracao portavel e SQL extraido da entrega oficial."""
from __future__ import annotations

import json
import re
from pathlib import Path

import psycopg
from ollama import Client, ResponseError
from httpx import HTTPError

BASE_DIR = Path(__file__).resolve().parent


def carregar_config():
    with open(BASE_DIR / "config.json", encoding="utf-8") as f:
        config = json.load(f)
    db = config["database"]
    for chave in ("host", "port", "dbname", "user", "password"):
        if chave not in db:
            raise ValueError(f"database.{chave} ausente em config.json")
    if not isinstance(db["port"], int) or not 1 <= db["port"] <= 65535:
        raise ValueError("database.port deve ser inteiro entre 1 e 65535")
    for chave in ("host", "model"):
        if not config["ollama"].get(chave):
            raise ValueError(f"ollama.{chave} ausente em config.json")
    return config


def carregar_projeto():
    projeto_path = BASE_DIR.parent / "Projeto.txt"
    if not projeto_path.exists():
        raise ValueError("Projeto.txt nao encontrado na raiz do projeto.")
    projeto = projeto_path.read_text(encoding="utf-8")
    try:
        ddl = projeto.split("3. DDL COMPLETO", 1)[1]
        ddl = ddl.split("4. CONSULTAS", 1)[0]
        ddl = "\n".join(linha for linha in ddl.splitlines()
                        if not re.fullmatch(r"\s*=+\s*", linha)).strip()
        secao = projeto.split("4. CONSULTAS", 1)[1].split("FIM DO ARQUIVO", 1)[0]
    except IndexError as exc:
        raise ValueError("Projeto.txt sem secoes oficiais de DDL/consultas") from exc
    if "CREATE TABLE" not in ddl.upper():
        raise ValueError("DDL nao encontrado em Projeto.txt")
    consultas = []
    for numero in range(1, 6):
        padrao = rf"CONSULTA {numero}\s+OBJETIVO:\s*(.*?)\s+SQL:\s*(.*?)(?=\nCONSULTA |\n=+|\Z)"
        bloco = re.search(padrao, secao, re.S)
        if not bloco:
            raise ValueError(f"Consulta {numero} nao encontrada em Projeto.txt")
        consultas.append((bloco[1].strip(), bloco[2].strip()))
    return ddl, consultas


def conectar(config):
    db = config["database"]
    return psycopg.connect(
        host=db["host"], port=db["port"], dbname=db["dbname"],
        user=db["user"], password=db["password"], connect_timeout=5,
        options="-c statement_timeout=10000 -c lock_timeout=3000",
    )


def validar_sql(sql):
    """Filtro conservador; transacao READ ONLY e a barreira de escrita no BD."""
    sql = sql.strip()
    if sql.startswith("```"):
        bloco = re.fullmatch(r"```(?:sql|postgresql)?\s*\n(.*?)\n```", sql, re.S | re.I)
        if not bloco:
            raise ValueError("Resposta do modelo nao contem um unico bloco SQL.")
        sql = bloco[1].strip()
    # Preserva literais para resultado, mas remove-os da verificacao de palavras.
    # Comentarios, dollar quoting e multiplos comandos sao rejeitados deliberadamente.
    if any(m in sql for m in ("--", "/*", "*/", "$$")) or re.search(r"\$\w*\$", sql):
        raise ValueError("SQL com comentarios ou dollar quoting nao permitido.")
    sem_literais = re.sub(r"'(?:''|[^'])*'", "''", sql)
    sem_literais = sem_literais.rstrip().removesuffix(";")
    if ";" in sem_literais or not re.match(r"^(SELECT|WITH)\b", sem_literais, re.I):
        raise ValueError("Permitida somente uma consulta SELECT ou WITH SELECT.")
    proibidas = r"\b(INSERT|UPDATE|DELETE|MERGE|DROP|ALTER|CREATE|TRUNCATE|COPY|CALL|DO|GRANT|REVOKE|INTO|SET|RESET|LOCK)\b"
    if re.search(proibidas, sem_literais, re.I):
        raise ValueError("Resposta contem operacao fora do modo de consulta.")
    # Funcoes administrativas podem ter efeitos mesmo dentro de SELECT.
    if re.search(r"\b(pg_\w+|set_config|lo_\w+|dblink\w*|nextval|setval)\s*\(", sem_literais, re.I):
        raise ValueError("Funcoes administrativas nao permitidas.")
    return sql


def executar_consulta(config, sql):
    sql = validar_sql(sql)
    with conectar(config) as conn:
        conn.read_only = True
        with conn.cursor() as cur:
            cur.execute(sql, prepare=True)
            colunas = [c.name for c in cur.description]
            linhas = cur.fetchmany(201)
    return colunas, linhas[:200], len(linhas) > 200


def mostrar_resultado(resultado):
    colunas, linhas, truncado = resultado
    print(" | ".join(colunas))
    print("-" * min(120, sum(len(c) + 3 for c in colunas)))
    for linha in linhas:
        print(" | ".join("NULL" if v is None else str(v) for v in linha))
    print(f"{len(linhas)} linha(s).")
    if truncado:
        print("Exibicao limitada a 200 linhas.")


def gerar_sql(config, ddl, pergunta):
    if not pergunta.strip():
        raise ValueError("Digite uma pergunta.")
    ollama_config = config["ollama"]
    client = Client(host=ollama_config["host"], timeout=180)
    relacoes = []
    for tabela, corpo in re.findall(r"CREATE TABLE (\w+) \((.*?)\n\);", ddl, re.S | re.I):
        for coluna, pai, chave in re.findall(r"^\s*(\w+)\s+[^\n]*?REFERENCES\s+(\w+)\((\w+)\)", corpo, re.M | re.I):
            relacoes.append(f"{tabela}.{coluna} = {pai}.{chave}")
    prompt = (
        "Converta a pergunta em exatamente uma consulta PostgreSQL SELECT ou WITH SELECT. "
        "Retorne apenas SQL, sem comentarios ou explicacoes. Use somente tabelas e colunas "
        "do DDL abaixo. Nao invente atributos. Nao execute comandos de escrita ou funcoes "
        "administrativas. Se impossivel, responda IMPOSSIVEL. Horarios sao locais de Sao Paulo.\n"
        f"<DDL_COMPLETO>\n{ddl}\n</DDL_COMPLETO>\n"
        "CHAVES ESTRANGEIRAS EXTRAIDAS DO DDL (use estas colunas nas juncoes):\n"
        + "\n".join(relacoes) + "\n"
        "O id da sessao identifica a realizacao; atividade_id identifica seu conteudo. "
        "Somente status='confirmada' ocupa vaga. Nao confunda FK com a PK da propria tabela.\n"
        f"PERGUNTA EM PORTUGUES: {pergunta}"
    )
    response = client.chat(
        model=ollama_config["model"], messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0, "num_ctx": 16384, "num_predict": 512},
    )
    resposta = response["message"]["content"]
    return validar_sql(resposta)


def main():
    try:
        config = carregar_config()
        ddl, consultas = carregar_projeto()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Erro de configuracao/projeto: {exc}")
        return 1
    print("Gestao de Eventos e Espacos")
    print("Parametros de conexao e modelo: config.json")
    while True:
        try:
            print("\n1-5: consultas | 6: pergunta em portugues | 7: testar conexao | 0: sair")
            opcao = input("Opcao: ").strip()
            if opcao == "0":
                return 0
            if opcao in {"1", "2", "3", "4", "5"}:
                objetivo, sql = consultas[int(opcao) - 1]
                print(objetivo)
                mostrar_resultado(executar_consulta(config, sql))
            elif opcao == "6":
                pergunta = input("Pergunta: ")
                sql = gerar_sql(config, ddl, pergunta)
                print(f"SQL gerado:\n{sql}")
                mostrar_resultado(executar_consulta(config, sql))
            elif opcao == "7":
                mostrar_resultado(executar_consulta(config, "SELECT current_database() AS banco;"))
            else:
                print("Opcao invalida.")
        except psycopg.Error as exc:
            print(f"Erro PostgreSQL [{exc.sqlstate or 'conexao'}]: {str(exc).strip()}")
        except ResponseError as exc:
            print(f"Erro Ollama: {exc.error}. Confira servico e modelo em config.json.")
        except (ConnectionError, TimeoutError, OSError, HTTPError) as exc:
            print(f"Servico indisponivel ou timeout: {exc}")
        except (ValueError, KeyError, TypeError) as exc:
            print(f"Consulta/resposta invalida: {exc}")
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrado.")
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
