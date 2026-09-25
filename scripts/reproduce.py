"""Offline reconstruction of frozen submission results; no database or model API."""
from __future__ import annotations
import argparse,hashlib,importlib.metadata,json,os,platform,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def validate_manifest(package,manifest):
    errors=[]
    for name,record in manifest['files'].items():
        p=(package/name).resolve()
        if not p.is_relative_to(package):errors.append(f'Unsafe manifest path: {name}');continue
        if not p.is_file():errors.append(f'Missing: {name}')
        elif digest(p)!=record['sha256']:errors.append(f'SHA-256 mismatch: {name}')
    if errors:raise ValueError('\n'.join(errors))

def compare_csv(actual,expected):
    import pandas as pd
    a=pd.read_csv(actual);b=pd.read_csv(expected)
    pd.testing.assert_frame_equal(a,b,check_dtype=False,check_exact=False,rtol=1e-10,atol=1e-10)

def reproduce(package,data,out):
    package=package.resolve();data=data.resolve();out=out.resolve()
    manifest=json.loads((package/'MANIFEST.json').read_text(encoding='utf-8'))
    if manifest['status']!='complete':raise RuntimeError('Package is not frozen complete: '+manifest['status'])
    validate_manifest(package,manifest)
    if out==data or out.is_relative_to(data) or data.is_relative_to(out):raise ValueError('Output and input data directories must not overlap')
    if out.exists() and any(out.iterdir()):raise FileExistsError('Output must be new or empty; select another --out directory')
    # A custom --data directory must contain exactly the frozen inputs, unchanged.
    for name in manifest['inputs']:
        src=data/name;expected=manifest['files']['data/'+name]['sha256']
        if not src.is_file() or digest(src)!=expected:raise ValueError('Frozen input mismatch: '+name)
    out.mkdir(parents=True,exist_ok=True);tables=out/'tables';figures=out/'figures';logs=out/'logs';latex=out/'latex'
    tables.mkdir();figures.mkdir();logs.mkdir();latex.mkdir()
    env=os.environ.copy();env['PYTHONIOENCODING']='utf-8';env['PYTHONDONTWRITEBYTECODE']='1'
    env['MPLCONFIGDIR']=str(out/'matplotlib_cache')
    result={'started_utc':datetime.now(timezone.utc).isoformat(),'status':'running',
            'package_manifest_sha256':digest(package/'MANIFEST.json'),'python':sys.version,
            'platform':platform.platform(),'dependencies':{},'steps':[],'table_checks':[],'latex_checks':[]}
    for name in ['numpy','pandas','scipy','matplotlib']:
        result['dependencies'][name]=importlib.metadata.version(name)
    try:
        for name in manifest['inputs']:shutil.copy2(data/name,tables/name)
        commands=[('analysis',[sys.executable,str(package/'scripts/submission_analysis.py'),'--data',str(data),'--out',str(tables)]),
                  ('plots',[sys.executable,str(package/'scripts/submission_plots.py'),'--data',str(tables),'--out',str(figures)]),
                  ('latex',[sys.executable,str(package/'scripts/submission_tables.py'),'--data',str(tables),'--out',str(latex)])]
        for step,command in commands:
            with (logs/(step+'.log')).open('w',encoding='utf-8') as log:
                proc=subprocess.run(command,cwd=package,env=env,stdout=log,stderr=subprocess.STDOUT)
            result['steps'].append({'name':step,'returncode':proc.returncode})
            if proc.returncode:raise RuntimeError(f'{step} failed; see logs/{step}.log')
        for name in manifest['expected_tables']:
            actual=tables/name;expected=data/name
            if not actual.is_file():raise FileNotFoundError('Missing reproduced table: '+name)
            if name.endswith('.csv'):compare_csv(actual,expected)
            else:
                if json.loads(actual.read_text(encoding='utf8'))!=json.loads(expected.read_text(encoding='utf8')):
                    raise AssertionError('JSON mismatch: '+name)
            result['table_checks'].append({'file':name,'match':True,'reproduced_sha256':digest(actual),'frozen_sha256':digest(expected)})
        for name in manifest['expected_latex']:
            actual=latex/name;expected=data/'latex'/name
            if not actual.is_file() or actual.read_bytes()!=expected.read_bytes():raise AssertionError('LaTeX/numeric-macro mismatch: '+name)
            result['latex_checks'].append({'file':name,'match':True,'sha256':digest(actual)})
        for name in manifest['expected_figures']:
            if not (figures/name).is_file() or (figures/name).stat().st_size==0:raise FileNotFoundError('Missing reproduced figure: '+name)
        figure_manifest=json.loads((figures/'figure_manifest.json').read_text(encoding='utf8'))
        expected_stems={Path(name).stem for name in manifest['expected_figures']}
        if set(figure_manifest['figures'])!=expected_stems:raise AssertionError('Figure manifest does not match expected stems')
        result['status']='passed';result['figure_check']='all expected PDF and PNG artifacts generated; PNG hashes compared below'
        result['png_checks']=[{'file':name,'same_sha256':digest(figures/name)==digest(package/'figures'/name)} for name in manifest['expected_figures'] if name.endswith('.png')]
        # Font/library differences can change rasterization; report them, never hide them.
        if not all(c['same_sha256'] for c in result['png_checks']):result['figure_check']='complete; rendering differs from frozen PNGs; inspect png_checks and environment versions'
    except Exception as exc:
        result['status']='failed';result['error']=str(exc);raise
    finally:
        result['finished_utc']=datetime.now(timezone.utc).isoformat()
        result['outputs']={p.relative_to(out).as_posix():{'bytes':p.stat().st_size,'sha256':digest(p)} for d in [tables,figures,logs,latex] for p in sorted(d.rglob('*')) if p.is_file()}
        (out/'reproduction_manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps({k:result[k] for k in ['status','started_utc','finished_utc']},indent=2))
    return result

if __name__=='__main__':
    package=Path(__file__).resolve().parents[1]
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--data',type=Path,default=package/'data');ap.add_argument('--out',type=Path,default=package/'reproduced')
    args=ap.parse_args();reproduce(package,args.data,args.out)
