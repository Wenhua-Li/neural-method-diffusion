"""Maintainer-only export of the current approved, text-free submission package.

Run from the project checkout: python release/scripts/export_current.py
This does not query the corpus or call models. It copies only the allowlist.
"""
from __future__ import annotations
import argparse, ast, csv, hashlib, json, shutil
from datetime import datetime, timezone
from pathlib import Path

INPUTS = ['analysis_papers.csv','sampling_m1.csv','calibration_m1.csv',
          'sampling_penetration.csv','calibration_penetration.csv',
          'recall_validation.csv','excluded_venue_provenance.csv',
          'revision_data_manifest.json','venue_key.csv','followup_role_labels.csv',
          'followup_m1_labels.csv','human_followup_provenance.json']
SCRIPTS = ['submission_analysis.py','submission_followup.py','submission_plots.py','submission_tables.py','style.py']
LATEX = ['table1.tex']+[f'si_table{i}.tex' for i in range(1,10)]+['numbers.tex','numbers.json']
FIGURES = ['fig1_true_penetration','fig2_domestication','fig3_method_dev',
           'fig4_penetrators','supp_fig1_coverage','supp_fig2_calibration',
           'supp_fig3_recall','supp_fig4_venues','supp_fig5_robustness',
           'supp_fig6_contributions','supp_fig7_validation','supp_fig8_missingness']
LEGACY_SCRIPTS=['db.py','deconfound.py','llm_client.py','make_extended.py',
                'make_figures.py','make_tables.py','run_full.py',
                'schema_m1_m2.md','verify_finding002.py']
LEGACY_DATA=['fig1_true_penetration.csv','fig2a_core_hit_composition.csv',
             'fig3_method_dev_yearly.csv','fig4_penetrator_topics.csv',
             'si_table_venue_penetration.csv','table1_penetration.csv']
# corpus_doi_list.csv is NOT legacy: it is the corpus-wide DOI inventory
# (paper/export_doi_list.py, user-approved 2026-09-17 scope) and is kept in
# the package; export_current neither regenerates nor deletes it.

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def descendant(p,base):
    p=p.resolve();base=base.resolve()
    if not p.is_relative_to(base) or p==base:raise ValueError(f'Unsafe target: {p}')
    return p
def literal(tree,name):
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets):
            return ast.literal_eval(node.value)
    raise KeyError(name)
def function_source(source,tree,name):
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    return ast.get_source_segment(source,node)
def export_prompts(root,package):
    dest=package/'instrument';dest.mkdir(exist_ok=True)
    paths={'m1':root/'exploration/001_semantic_pilot/run_pilot.py',
           'penetration':root/'exploration/005_fortress/deconfound.py'}
    provenance={}
    for task,path in paths.items():
        source=path.read_text(encoding='utf-8');tree=ast.parse(source)
        (dest/f'{task}_prompt.txt').write_text(literal(tree,'PROMPT_TEMPLATE')+'\n',encoding='utf-8')
        vocab='VOCAB' if task=='m1' else 'LABELS'
        parser='"""Frozen historical response parser; no model client or I/O on import."""\nimport json\nimport re\n\n'
        parser+=f'{vocab} = {literal(tree,vocab)!r}\n\n'
        parser+=function_source(source,tree,'_extract_json')+'\n\n'+function_source(source,tree,'_validate')+'\n'
        (dest/f'{task}_parser.py').write_text(parser,encoding='utf-8')
        provenance[task]={'source':path.relative_to(root).as_posix(),'source_sha256':digest(path),'extract':'AST literal PROMPT_TEMPLATE and exact _extract_json/_validate functions'}
    (dest/'prompt_provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    measurement_path=root/'scripts/submission_data.py'
    source=measurement_path.read_text(encoding='utf-8');tree=ast.parse(source)
    rules={'source_sha256':digest(measurement_path),'topic_order':'first matching application pattern; otherwise unclassified','TOPICS':literal(tree,'TOPICS')}
    for node in tree.body:
        if isinstance(node,ast.Assign) and isinstance(node.value,ast.Call):
            for target in node.targets:
                if isinstance(target,ast.Name) and target.id in {'DL','LLM','EXT'}:
                    rules[target.id]={'regex':ast.literal_eval(node.value.args[0]),'flags':'re.IGNORECASE'}
    (dest/'measurement_rules.json').write_text(json.dumps(rules,indent=2),encoding='utf-8')

def export(root,package,figure_dir,allow_missing_plots=False):
    root=root.resolve();package=package.resolve()
    if package!=root/'release':raise ValueError('This exporter is restricted to PROJECT_ROOT/release')
    required=[root/'results/tables'/f for f in INPUTS]+[root/'scripts'/f for f in SCRIPTS]+[root/'results/tables/latex'/f for f in LATEX]
    missing=[str(p) for p in required if not p.exists()]
    if missing and not (allow_missing_plots and missing==[str(root/'scripts/submission_plots.py')]):
        raise FileNotFoundError('Required current artifacts missing: '+', '.join(missing))
    # Old versions remain in the pre_revision archive, not the reviewer package.
    for name in LEGACY_SCRIPTS:
        p=descendant(package/'scripts'/name,package)
        if p.exists():p.unlink()
    for name in LEGACY_DATA:
        p=descendant(package/'data'/name,package)
        if p.exists():p.unlink()
    (package/'data').mkdir(exist_ok=True);(package/'figures').mkdir(exist_ok=True)
    (package/'figures/pdf').mkdir(exist_ok=True)
    sources=[root/'results/tables'/name for name in INPUTS]
    sources+=sorted((root/'results/tables').glob('revision_*.csv'))
    sources+=[root/'results/tables/revision_numbers.json']
    for src in sources:
        if not src.is_file():raise FileNotFoundError(src)
        if src.suffix=='.csv':
            with src.open(encoding='utf-8-sig',newline='') as f: fields=next(csv.reader(f))
            blocked={'title','abstract','raw','reason','text','api_key','token'}&set(fields)
            if blocked:raise ValueError(f'Unapproved raw/private columns in {src.name}: {blocked}')
        shutil.copy2(src,package/'data'/src.name)
    for name in SCRIPTS:
        src=root/'scripts'/name
        if src.exists():shutil.copy2(src,package/'scripts'/name)
    (package/'data/latex').mkdir(exist_ok=True)
    for name in LATEX:shutil.copy2(root/'results/tables/latex'/name,package/'data/latex'/name)
    export_prompts(root,package)
    # Fully regenerate the managed figure set; never leave stale legacy figures.
    for p in (package/'figures').rglob('*'):
        if p.is_file() and p.suffix in {'.pdf','.png'}:descendant(p,package).unlink()
    missing_figures=[]
    for stem in FIGURES:
        for ext in ['.pdf','.png']:
            rel=Path('pdf')/(stem+ext) if ext=='.pdf' else Path(stem+ext)
            src=figure_dir/rel
            if src.exists():shutil.copy2(src,package/'figures'/rel)
            else:missing_figures.append(rel.as_posix())
    if (figure_dir/'figure_manifest.json').exists():
        shutil.copy2(figure_dir/'figure_manifest.json',package/'figures/figure_manifest.json')
    manifest={'format_version':1,'generated_utc':datetime.now(timezone.utc).isoformat(),
              'status':'complete' if not missing and not missing_figures else 'awaiting_current_plots',
              'inputs':INPUTS,'expected_tables':[p.name for p in sources if p.name.startswith('revision_') and p.name!='revision_data_manifest.json'],
              'expected_figures':[(Path('pdf')/(s+ext)).as_posix() if ext=='.pdf' else s+ext for s in FIGURES for ext in ['.pdf','.png']],
              'expected_latex':LATEX,
              'missing_figures':missing_figures,'files':{}}
    excluded={'__pycache__','.pytest_cache','reproduced','.git'}
    for p in sorted(package.rglob('*')):
        if p.is_file() and p.name!='MANIFEST.json' and not any(x in excluded for x in p.relative_to(package).parts):
            manifest['files'][p.relative_to(package).as_posix()]={'bytes':p.stat().st_size,'sha256':digest(p)}
    (package/'MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({'status':manifest['status'],'files':len(manifest['files']),'missing_figures':missing_figures},indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[2])
    ap.add_argument('--figure-dir',type=Path);ap.add_argument('--allow-missing-plots',action='store_true')
    args=ap.parse_args();export(args.project,args.project/'release',args.figure_dir or args.project/'results/figures',args.allow_missing_plots)
