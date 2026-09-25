"""Run the frozen package in a fresh temporary copy with DB/network calls denied.

Uses the current Python interpreter and installed dependencies; no installation.
This is an executable reproducibility check, not an OS security sandbox.
"""
from __future__ import annotations
import argparse,importlib.util,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path

GUARD = '''import socket, sqlite3
def denied(*args, **kwargs):
    raise RuntimeError("ISOLATION CHECK: database/network access attempted")
socket.socket.connect = denied
socket.socket.connect_ex = denied
socket.create_connection = denied
socket.getaddrinfo = denied
sqlite3.connect = denied
'''

def verify(package,workspace):
    package=package.resolve();workspace=workspace.resolve()
    if workspace.exists() and any(workspace.iterdir()):raise FileExistsError('Verification directory must be new or empty')
    if workspace==package or workspace.is_relative_to(package):raise ValueError('Verification workspace must be outside package')
    workspace.mkdir(parents=True,exist_ok=True);copy=workspace/'submission_archive'
    shutil.copytree(package,copy,ignore=shutil.ignore_patterns('__pycache__','*.pyc','reproduced','.git'))
    guard=workspace/'guard';guard.mkdir();(guard/'sitecustomize.py').write_text(GUARD,encoding='utf-8')
    env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','TEMP','TMP','PATH','COMSPEC','PATHEXT'}}
    env.update(PYTHONPATH=str(guard),PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1',
               USERPROFILE=str(workspace/'empty_profile'))
    (workspace/'empty_profile').mkdir()
    command=[sys.executable,str(copy/'scripts/reproduce.py'),'--data',str(copy/'data'),'--out',str(workspace/'reproduced')]
    with (workspace/'isolation.log').open('w',encoding='utf8') as log:
        proc=subprocess.run(command,cwd=copy,env=env,stdout=log,stderr=subprocess.STDOUT)
    report={'returncode':proc.returncode,'workspace':str(workspace),'copied_package':str(copy),
            'database_or_raw_text_copied':any(p.suffix.lower() in {'.db','.sqlite','.sqlite3','.jsonl'} for p in copy.rglob('*') if p.is_file()),
            'guard':'sitecustomize blocks socket connects, DNS and sqlite3.connect in parent and subprocesses',
            'credentials':'environment allowlist; empty user profile; no personal model client in default chain'}
    result=workspace/'reproduced/reproduction_manifest.json'
    if result.exists():
        r=json.loads(result.read_text(encoding='utf8'))
        report.update(reproduction_status=r['status'],table_checks=len(r['table_checks']),latex_checks=len(r.get('latex_checks',[])),figure_check=r.get('figure_check'),png_matches=sum(x['same_sha256'] for x in r.get('png_checks',[])))
    # Meaningful failure-path tests against copies, without rerunning statistics.
    spec=importlib.util.spec_from_file_location('offline_reproduce',copy/'scripts/reproduce.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    manifest=json.loads((copy/'MANIFEST.json').read_text(encoding='utf8'))
    target=copy/'data/revision_data_manifest.json';saved=target.read_bytes();target.write_bytes(saved+b'\n')
    try:
        mod.validate_manifest(copy,manifest);report['tamper_rejected']=False
    except ValueError:report['tamper_rejected']=True
    finally:target.write_bytes(saved)
    existing=workspace/'existing_output';existing.mkdir();marker=existing/'keep.txt';marker.write_text('preserve',encoding='utf8')
    try:
        mod.reproduce(copy,copy/'data',existing);report['existing_output_rejected']=False
    except FileExistsError:report['existing_output_rejected']=marker.read_text(encoding='utf8')=='preserve'
    try:
        mod.reproduce(copy,copy/'data',copy/'data'/'nested_output');report['input_output_overlap_rejected']=False
    except ValueError:report['input_output_overlap_rejected']=True
    report['passed']=proc.returncode==0 and report.get('reproduction_status')=='passed' and not report['database_or_raw_text_copied'] and all(report[k] for k in ['tamper_rejected','existing_output_rejected','input_output_overlap_rejected'])
    (workspace/'isolation_verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report,indent=2));return report

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--package',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--workspace',type=Path)
    args=ap.parse_args();workspace=args.workspace or Path(tempfile.mkdtemp(prefix='nc_submission_isolation_'))
    result=verify(args.package,workspace);sys.exit(0 if result['passed'] else 1)
