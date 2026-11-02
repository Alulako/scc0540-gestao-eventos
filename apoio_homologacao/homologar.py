"""Instalacao de teste somente em base NOVA homologacao_*. Nunca DROP/TRUNCATE.

Carga: --criar-e-testar. Repeticao de consultas/IA: --somente-leitura [--ia].
Utiliza o main.py original por importacao; nao o edita.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import time

from pre_verificar_ambiente import Registro, config, modelos, parametros, verificar_arquivos


class RecusaSegura(ValueError):
    pass


def carregar_app(projeto):
    spec=importlib.util.spec_from_file_location('prototipo_homologacao',projeto/'Prototipo/main.py')
    app=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    return app


def consultas(app,cfg,qs,registro):
    for i,(_,query) in enumerate(qs,1):
        try:
            _,rows,truncated=app.executar_consulta(cfg,query)
            assert len(rows)==[8,5,2,4,2][i-1] and not truncated
            if i==2: assert {r[0]:r[-1] for r in rows}=={2:0,8:0,3:1,6:3,4:98}
            if i==3: assert {(r[0],r[2]) for r in rows}=={(1,1),(2,1)}
            if i==4: assert [(r[0],r[1],r[-1]) for r in rows]==[(1,2,1),(1,8,2),(1,3,3),(2,6,1)]
            registro.add('Consulta '+str(i),'PASSOU',str(len(rows))+' linhas; SQL literal de Projeto.txt')
        except Exception:
            registro.add('Consulta '+str(i),'FALHOU','erro SQL ou resultado diferente do DML aprovado')


def triggers(conn,registro):
    # Executado SO na conexao da base recem-criada nesta chamada. Sempre ROLLBACK.
    cases=[
        ('Conflito permitido',"INSERT INTO sessao (atividade_id,espaco_id,inicio,fim) VALUES (1,1,'2026-11-02 10:00','2026-11-02 11:00')",None),
        ('Conflito proibido',"INSERT INTO sessao (atividade_id,espaco_id,inicio,fim) VALUES (1,1,'2026-11-02 09:30','2026-11-02 11:00')",'23514'),
        ('Periodo permitido',"UPDATE evento SET fim='2026-11-04 21:00' WHERE id=1",None),
        ('Periodo proibido',"UPDATE evento SET inicio='2026-11-02 11:00' WHERE id=1",'23514'),
        ('Vagas permitidas',"INSERT INTO inscricao_sessao (pessoa_id,sessao_id) VALUES (5,3)",None),
        ('Vagas proibidas',"UPDATE inscricao_sessao SET status='confirmada' WHERE pessoa_id=3 AND sessao_id=2",'23514'),
        ('Elegibilidade permitida',"INSERT INTO inscricao_sessao (pessoa_id,sessao_id) VALUES (3,4)",None),
        ('Elegibilidade proibida',"INSERT INTO inscricao_sessao (pessoa_id,sessao_id) VALUES (6,4)",'23514')]
    import psycopg
    for name,query,expected in cases:
        conn.execute('BEGIN')
        state=None
        try:
            conn.execute(query)
        except psycopg.Error as exc:
            state=exc.sqlstate
        finally:
            conn.execute('ROLLBACK')
        registro.add('Trigger '+name,'PASSOU' if state==expected else 'FALHOU',
                     'aceito e revertido' if state is None else 'rejeitado; SQLSTATE='+str(state))
    conn.execute('BEGIN')
    try:
        before=conn.execute('SELECT count(*) FROM historico_sessao').fetchone()[0]
        conn.execute("UPDATE sessao SET inicio='2026-11-03 11:00' WHERE id=4")
        after=conn.execute('SELECT count(*) FROM historico_sessao').fetchone()[0]
        conn.execute('UPDATE sessao SET inicio=inicio WHERE id=4')
        noop=conn.execute('SELECT count(*) FROM historico_sessao').fetchone()[0]
        assert (before,after,noop)==(2,3,3)
        registro.add('Trigger historico','PASSOU','UPDATE efetivo +1; no-op +0; ROLLBACK')
    except Exception:
        registro.add('Trigger historico','FALHOU','resultado divergente')
    finally:
        conn.execute('ROLLBACK')


def testar_cli(projeto,registro):
    try:
        run=subprocess.run([sys.executable,'-X','utf8','main.py'],cwd=projeto/'Prototipo',
                           input='7\n1\n2\n3\n4\n5\n9\n7\n0\n',text=True,encoding='utf-8',
                           capture_output=True,timeout=90)
        assert run.returncode==0 and 'Traceback' not in run.stderr
        for text in ('8 linha(s).','5 linha(s).','2 linha(s).','4 linha(s).','Opcao invalida.'):
            assert text in run.stdout
        assert 'Erro PostgreSQL' not in run.stdout
        registro.add('CLI real e erro de opcao','PASSOU','python main.py: conexao, opcoes 1-5, opcao 9 tratada, conexao continua')
    except Exception:
        registro.add('CLI real e erro de opcao','FALHOU','processo CLI falhou, retornou erro ou excedeu 90s; conferir manualmente')


def testar_ia(app,cfg,ddl,registro):
    cases=[('simples','Liste o id e o nome de todos os eventos ordenados pelo id.',
            'SELECT id,nome FROM evento ORDER BY id',False),
           ('JOIN','Liste o id e o titulo de cada atividade e o nome de seu evento. Use JOIN entre atividade.evento_id e evento.id. Ordene pelo id da atividade.',
            'SELECT a.id,a.titulo,e.nome FROM atividade a JOIN evento e ON a.evento_id=e.id ORDER BY a.id',True),
           ('agregacao','Quantas pessoas existem cadastradas na tabela pessoa? Retorne somente a contagem total.',
            'SELECT count(*) FROM pessoa',False)]
    try:
        assert modelos(cfg)
    except Exception:
        for name,*_ in cases: registro.add('Ollama '+name,'NÃO TESTADO','API ou modelo configurado indisponivel')
        return
    for name,prompt,oracle,require_join in cases:
        start=time.monotonic()
        try:
            generated=app.gerar_sql(cfg,ddl,prompt)
            _,actual,truncated=app.executar_consulta(cfg,generated)
            _,expected,_=app.executar_consulta(cfg,oracle)
            assert not truncated and actual==expected
            if require_join: assert re.search(r'\bJOIN\b',generated,re.I)
            if name=='agregacao': assert re.search(r'\bCOUNT\s*\(',generated,re.I)
            registro.add('Ollama '+name,'PASSOU',{'segundos':round(time.monotonic()-start,2),'sql':generated,'linhas':len(actual)})
        except Exception as exc:
            # Apenas classe/SQLSTATE; nunca str(exc) que pode revelar configuracao.
            registro.add('Ollama '+name,'FALHOU',{'segundos':round(time.monotonic()-start,2),
                'tipo':type(exc).__name__,'sqlstate':getattr(exc,'sqlstate',None),
                'orientacao':'conferir servico/modelo e semantica; timeout do prototipo 180s por chamada'})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--projeto',type=Path,default=Path.cwd())
    action=parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--criar-e-testar',action='store_true')
    action.add_argument('--somente-leitura',action='store_true')
    parser.add_argument('--ia',action='store_true',help='3 geracoes reais pelo modelo configurado')
    parser.add_argument('--saida',help='JSON de resultados sem senha')
    args=parser.parse_args()
    registro=Registro()
    projeto=args.projeto.resolve()
    try:
        verificar_arquivos(projeto)
        cfg=config(projeto)
        app=carregar_app(projeto)
        ddl,qs=app.carregar_projeto()
        import psycopg
        from psycopg import sql
        if args.criar_e_testar:
            name=cfg['database']['dbname']
            if not re.fullmatch(r'homologacao_[a-z0-9_]{1,45}',name):
                raise RecusaSegura('usar dbname novo com prefixo homologacao_ e letras minusculas/numeros/_')
            with psycopg.connect(**parametros(cfg,'postgres'),autocommit=True) as admin:
                if admin.execute('SELECT 1 FROM pg_database WHERE datname=%s',(name,)).fetchone():
                    raise RecusaSegura('base ja existe: recusado; escolher novo dbname, sem apagar/recarregar')
                admin.execute(sql.SQL('CREATE DATABASE {} TEMPLATE template0 ENCODING {}').format(sql.Identifier(name),sql.Literal('UTF8')))
            registro.add('Base nova','PASSOU',name+' criada; nenhuma base anterior foi alterada')
            with psycopg.connect(**parametros(cfg),autocommit=True) as conn:
                assert conn.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema')").fetchone()[0]==0
                registro.add('Base vazia','PASSOU','zero tabelas de usuario antes do DDL')
                conn.execute(ddl)
                registro.add('DDL extraido de Projeto.txt','PASSOU','DDL literal executado, sem sql/ auxiliar')
                conn.execute((projeto/'DML.sql').read_text(encoding='utf-8'))
                registro.add('DML.sql','PASSOU','carga integral na base recem-criada')
                counts=conn.execute('SELECT (SELECT count(*) FROM pessoa),(SELECT count(*) FROM evento),(SELECT count(*) FROM atividade),(SELECT count(*) FROM sessao),(SELECT count(*) FROM historico_sessao)').fetchone()
                assert counts==(8,4,7,8,2),counts
                registro.add('Quantidades DML','PASSOU','8 pessoas; 4 eventos; 7 atividades; 8 sessoes; 2 historicos')
                triggers(conn,registro)
        consultas(app,cfg,qs,registro)
        try:
            app.executar_consulta(cfg,'SELECT coluna_inexistente FROM pessoa;')
            registro.add('Erro SQL e recuperacao','FALHOU','coluna inexistente nao foi rejeitada')
        except psycopg.errors.UndefinedColumn:
            assert app.executar_consulta(cfg,'SELECT count(*) FROM pessoa;')[1]==[(8,)]
            registro.add('Erro SQL e recuperacao','PASSOU','UndefinedColumn 42703; consulta seguinte retorna 8')
        testar_cli(projeto,registro)
        if args.ia:
            testar_ia(app,cfg,ddl,registro)
        else:
            registro.add('Ollama: 3 perguntas','NÃO TESTADO','geracao nao solicitada; repetir com --somente-leitura --ia')
    except Exception as exc:
        # Somente recusas controladas podem ter mensagem; erros externos nunca.
        detail=str(exc) if isinstance(exc,RecusaSegura) else type(exc).__name__+'; SQLSTATE='+str(getattr(exc,'sqlstate',None))
        registro.add('Execucao de homologacao','FALHOU',detail)
    return registro.terminar(args.saida)


if __name__=='__main__':
    raise SystemExit(main())
