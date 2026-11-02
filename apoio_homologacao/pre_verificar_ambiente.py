"""Diagnostico somente leitura. Nenhuma instalacao, carga ou senha em log.

python apoio_homologacao/pre_verificar_ambiente.py --projeto ProjetoBD
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import socket
import sys
from urllib.parse import urlsplit
from urllib.request import urlopen

BASE = Path(__file__).resolve().parent


class Registro:
    def __init__(self):
        self.itens = []

    def add(self, teste, resultado, evidencia):
        self.itens.append(dict(teste=teste, resultado=resultado, evidencia=evidencia))
        print(f'{resultado}: {teste}: {evidencia}', flush=True)

    def terminar(self, saida=None):
        if saida:
            path = Path(saida)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(self.itens, ensure_ascii=False, indent=2), encoding='utf-8')
        return 1 if any(i['resultado']=='FALHOU' for i in self.itens) else (2 if any(i['resultado']=='NÃO TESTADO' for i in self.itens) else 0)


def config(projeto):
    # Nao reproduzir JSON/exception: erros podem conter senhas ou URLs privadas.
    cfg = json.loads((projeto/'Prototipo/config.json').read_text(encoding='utf-8'))
    db, ia = cfg['database'], cfg['ollama']
    if not all(k in db for k in ('host','port','dbname','user','password')):
        raise ValueError('database incompleto')
    if type(db['port']) is not int or not 1<=db['port']<=65535:
        raise ValueError('database.port invalida')
    if not all(isinstance(db[k],str) and db[k] for k in ('host','dbname','user')) or not isinstance(db['password'],str):
        raise ValueError('database invalido')
    u=urlsplit(ia['host'])
    if u.scheme not in ('http','https') or not u.hostname or u.username or u.password or u.query or u.fragment:
        raise ValueError('URL Ollama invalida')
    if not isinstance(ia['model'],str) or not ia['model'].strip():
        raise ValueError('modelo ausente')
    return cfg


def verificar_arquivos(projeto):
    expected=json.loads((BASE/'manifesto-aprovado.json').read_text(encoding='utf-8'))
    for item in expected['arquivos']:
        p=projeto/item['nome']
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('Entregavel ausente/diferente: '+item['nome'])
    # A unica edicao permitida no prototipo extraido e config.json.
    import zipfile
    with zipfile.ZipFile(projeto/'Prototipo.zip') as z:
        if set(z.namelist())!={'main.py','config.json','requirements.txt'} or z.testzip():
            raise ValueError('Prototipo.zip invalido')
        for name in ('main.py','requirements.txt'):
            if (projeto/'Prototipo'/name).read_bytes()!=z.read(name):
                raise ValueError('Prototipo extraido diferente: '+name)
    return True


def parametros(cfg, dbname=None):
    db=cfg['database']
    return dict(host=db['host'],port=db['port'],user=db['user'],password=db['password'],
                dbname=dbname or db['dbname'],connect_timeout=5,
                options='-c statement_timeout=10000 -c lock_timeout=3000')


def modelos(cfg):
    with urlopen(cfg['ollama']['host'].rstrip('/')+'/api/tags',timeout=5) as response:
        data=json.load(response)
    names={m.get('name',m.get('model','')) for m in data['models']}
    model=cfg['ollama']['model']
    return model in names or (':' not in model.rsplit('/',1)[-1] and model+':latest' in names)


def executar(projeto, registro):
    registro.add('Python 3.11+', 'PASSOU' if sys.version_info>=(3,11) else 'FALHOU',platform.python_version())
    registro.add('Sistema', 'PASSOU',platform.system()+' '+platform.machine())
    for module in ('psycopg','ollama'):
        try:
            version=importlib.metadata.version(module)
            __import__(module)
            registro.add('Dependencia '+module,'PASSOU','versao '+version)
        except Exception:
            registro.add('Dependencia '+module,'FALHOU','instalar requirements.txt no ambiente ativo')
    try:
        verificar_arquivos(projeto)
        registro.add('Arquivos aprovados','PASSOU','8 entregaveis e main.py/requirements.txt extraidos iguais; config.json pode variar')
    except (OSError,ValueError,KeyError):
        registro.add('Arquivos aprovados','FALHOU','extracao incompleta ou arquivos diferentes do manifesto aprovado')
    try:
        cfg=config(projeto)
        registro.add('Config JSON','PASSOU','formato valido; valores e senha omitidos')
    except (OSError,ValueError,KeyError,TypeError):
        registro.add('Config JSON','FALHOU','revisar config.json; UTF-8 sem BOM, porta inteira e chaves exigidas')
        for name in ('PostgreSQL acessivel','Existencia da base','Conexao Python/PostgreSQL','Ollama acessivel','Modelo configurado'):
            registro.add(name,'NÃO TESTADO','depende de config.json valido')
        return
    try:
        with socket.create_connection((cfg['database']['host'],cfg['database']['port']),timeout=3):
            pass
        registro.add('PostgreSQL acessivel','PASSOU','porta TCP responde; autenticacao verificada separadamente')
    except OSError:
        registro.add('PostgreSQL acessivel','FALHOU','porta configurada nao responde; conferir servico/porta/rede')
    try:
        import psycopg
    except ImportError:
        for name in ('Existencia da base','Conexao Python/PostgreSQL'):
            registro.add(name,'NÃO TESTADO','psycopg indisponivel')
    else:
        try:
            with psycopg.connect(**parametros(cfg)) as conn:
                conn.read_only=True
                version=conn.execute('SHOW server_version_num').fetchone()[0]
                assert conn.execute('SELECT 1').fetchone()==(1,)
            registro.add('Existencia da base','PASSOU','base configurada existe e permite conexao')
            registro.add('Conexao Python/PostgreSQL','PASSOU','SELECT 1 em READ ONLY; server_version_num='+str(version))
        except psycopg.Error as exc:
            state=exc.sqlstate or 'conexao'
            exists=False if state=='3D000' else None
            # libpq pode nao disponibilizar SQLSTATE em erro de abertura.
            # Consultar catalogo em READ ONLY, sem depender do texto do erro.
            if exists is None:
                try:
                    with psycopg.connect(**parametros(cfg,'postgres')) as check:
                        check.read_only=True
                        exists=bool(check.execute('SELECT 1 FROM pg_database WHERE datname=%s',(cfg['database']['dbname'],)).fetchone())
                except psycopg.Error:
                    pass
            registro.add('Existencia da base','NÃO TESTADO' if exists is None else ('PASSOU' if exists else 'FALHOU'),
                         'sem confirmacao; conferir autenticacao/acesso' if exists is None else
                         ('base existe no catalogo; conexao alvo falhou' if exists else 'base inexistente, confirmado pelo catalogo/servidor'))
            registro.add('Conexao Python/PostgreSQL','FALHOU','SQLSTATE='+state+'; conferir servico, autenticacao, porta e base')
    try:
        found=modelos(cfg)
        registro.add('Ollama acessivel','PASSOU','GET /api/tags respondeu; nenhuma geracao executada')
        registro.add('Modelo configurado','PASSOU' if found else 'FALHOU',
                     'modelo presente no servidor' if found else 'modelo ausente; executar ollama pull para o modelo de config.json')
    except Exception:
        registro.add('Ollama acessivel','FALHOU','API indisponivel/invalida; conferir aplicativo, host e porta')
        registro.add('Modelo configurado','NÃO TESTADO','depende da API Ollama')
    print('Informativo: psql no PATH='+str(bool(shutil.which('psql')))+'; nao e obrigatorio para este roteiro.',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--projeto',type=Path,default=Path.cwd(),help='diretorio que contem Projeto.txt')
    parser.add_argument('--saida',help='JSON de resultados, sem configuracao/senhas')
    args=parser.parse_args()
    registro=Registro()
    executar(args.projeto.resolve(),registro)
    return registro.terminar(args.saida)


if __name__=='__main__':
    raise SystemExit(main())
