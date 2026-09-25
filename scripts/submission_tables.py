"""Offline LaTeX table fragments and numeric macros from revision outputs."""
from pathlib import Path
import argparse,json
import pandas as pd
GROUPS=['Core EC conferences','Core EC journals','Mixed journals','SSCI (mixed conf.)']
SHORT={'Core EC conferences':'Core conferences','Core EC journals':'Core journals','Mixed journals':'Mixed journals','SSCI (mixed conf.)':'SSCI'}
def esc(s):
    return str(s).replace('&',r'\&').replace('_',r'\_').replace('%',r'\%').replace('≥',r'$\geq$')
def table(columns,rows):
    n=len(columns);out=[r'\begin{tabular}{@{}'+('l'+'r'*(n-1))+r'@{}}',r'\toprule',' & '.join(map(esc,columns))+r' \\',r'\midrule']
    for row in rows:out.append(' & '.join(map(esc,row))+r' \\')
    return '\n'.join(out+[r'\bottomrule',r'\end{tabular}'])+'\n'
def produce(data,out):
    out.mkdir(parents=True,exist_ok=True)
    def read(name):return pd.read_csv(data/('revision_'+name+'.csv'))
    def write(name,cols,rows):(out/name).write_text(table(cols,rows),encoding='utf-8')
    w=read('roles_windows');rows=[]
    for g in GROUPS:
        for period in ['2016-2020','2021-2025']:
            r=w[(w.group==g)&(w.window==period)].iloc[0]
            rows.append([SHORT[g],period,f'{r.n:,}',f'{r.hit_pct:.2f}',f'{r.dl_pct:.2f}',f'{r.neuro_pct:.2f}',f'{r.hybrid_pct:.2f}'])
    write('table1.tex',['Venue group','Window','n','Hit (%)','DL-native (%)','Neuro (%)','Hybrid (%)'],rows)
    v=read('roles_venues');v=v[v.window.eq('2021-2025')].sort_values(['group','venue'])
    write('si_table1.tex',['Venue','n','Hits','DL-native','DL-native (%)'],[[r.venue,f'{r.n:,}',r.hits,r.dl,f'{r.dl_pct:.2f}'] for r in v.itertuples()])
    c=read('contribution_windows');z=c[c.scope.eq('target_nonempty')]
    write('si_table2.tex',['Window','n','Method dev. (%)','Apply (%)','Theory (%)'],[[r.window,f'{r.n:,}',f'{r.method_dev_pct:.2f}',f'{r.apply_pct:.2f}',f'{r.theory_pct:.2f}'] for r in z.itertuples()])
    cal=read('calibration')
    calrows=[[r.task,r.weighting.replace('_',' '),r.n,f'{r.effective_n:.1f}',f'{r.accuracy:.3f}',f'{r.kappa:.3f}'] for r in cal.itertuples()]
    follow=read('followup_agreement').iloc[0];calrows.append(['M1 recent','unweighted',int(follow.n),str(int(follow.n)),f'{follow.accuracy:.3f}',f'{follow.fine_kappa:.3f}'])
    write('si_table3.tex',['Task','Weights','n','Effective n','Agreement','Kappa'],calrows)
    cells=read('human_role_cells');z=cells[cells.component.eq('new_human_nonhits')]
    write('si_table4.tex',['Group','Stratum','N','n','Positive','Lower total','Upper total'],[[SHORT[r.group],r.stratum,r.N,r.n,r.k,r.lower,r.upper] for r in z.itertuples()])
    scen=read('human_role_rates');wide=read('human_wide_rates').set_index('group')
    write('si_table5.tex',['Group','DL-native (%)','Lower (%)','Upper (%)','With hybrid (%)'],[[SHORT[r.group],f'{r.point_pct:.2f}',f'{r.lower_pct:.2f}',f'{r.upper_pct:.2f}',f'{wide.loc[r.group,"point_pct"]:.2f}'] for r in scen.itertuples()])
    cr=read('human_role_ratios');wide_rat=read('human_wide_ratios').set_index(['numerator','denominator'])
    write('si_table6.tex',['Numerator','Denominator','DL ratio','Lower','Upper','Wide ratio'],[[SHORT[r.numerator],SHORT[r.denominator],f'{r.point:.2f}',f'{r.lower:.2f}',f'{r.upper:.2f}',f'{wide_rat.loc[(r.numerator,r.denominator),"point"]:.2f}'] for r in cr.itertuples()])
    b=read('missing_text_bounds');write('si_table7.tex',['Window','N','Observed','Unknown','Lower (%)','Upper (%)'],[[r.window,f'{r.N:,}',f'{r.observed:,}',f'{r.missing:,}',f'{r.lower_pct:.2f}',f'{r.upper_pct:.2f}'] for r in b.itertuples()])
    d=read('human_m1_recent');write('si_table8.tex',['Group','Old known','New n','Frozen (%)','Human (%)','Lower (%)','Upper (%)'],[[SHORT[r.group],r.old_known_n,r.new_n,f'{r.machine_pct:.2f}',f'{r.human_recent_pct:.2f}',f'{r.lower_pct:.2f}',f'{r.upper_pct:.2f}'] for r in d.itertuples()])
    lag=read('lag_holdout');write('si_table9.tex',['Group','Model','Lag','Held-out RMSE (pp)'],[[SHORT[r.group],r.model.replace('_',' '),r.selected_shift,f'{r.test_rmse_pp:.2f}'] for r in lag.itertuples()])
    meta=json.loads((data/'revision_data_manifest.json').read_text());nums=json.loads((data/'revision_numbers.json').read_text())
    macros={'CorpusN':f"{meta['canonical_records']:,}",'StandardN':f"{meta['standard_records']:,}",'TargetN':f"{meta['target_standard_records']:,}",'EligibleN':f"{meta['m1_primary_eligible']:,}",'MOneN':f"{meta['m1_primary_observed']:,}",'HitN':f"{meta['penetration_hits']:,}",'OtherN':str(meta['unmapped_standard_records']),'EmptyN':str(meta['m1_empty_coded']),'MTruncated':f"{meta['m1_primary_truncated']:,}",'PTruncated':str(meta['pen_hit_truncated'])}
    for task,prefix in [('m1','M'),('penetration','P')]:
        r=cal[(cal.task==task)&cal.weighting.eq('unweighted')].iloc[0];macros[prefix+'Kappa']=f'{r.kappa:.3f}';macros[prefix+'Agreement']=f'{100*r.accuracy:.1f}'
    for g,prefix in zip(GROUPS,['CoreC','CoreJ','MixedJ','SSCI']):
        r=w[(w.group==g)&w.window.eq('2021-2025')].iloc[0]
        for name,col in [('Rate','dl_pct'),('Wide','wide_pct'),('Neuro','neuro_pct'),('Hybrid','hybrid_pct'),('Integrated','integrated_pct')]:macros[prefix+name]=f'{r[col]:.2f}'
    for scope,prefix in [('target_nonempty','All'),('core_nonempty','Core'),('ec_nonempty','EC')]:
        t=c[c.scope.eq(scope)];macros[prefix+'Old']=f"{t[t.window.eq('1996-2000')].method_dev_pct.iloc[0]:.2f}";macros[prefix+'New']=f"{t[t.window.eq('2021-2025')].method_dev_pct.iloc[0]:.2f}"
    ts=nums['topic_support'];macros.update({'TopicCells':str(ts['cells']),'TopicCoreN':f"{ts['core_included']:,}",'TopicMixedN':f"{ts['mixed_included']:,}",'TopicCoreRate':f"{ts['core_standardized_pct']:.2f}",'TopicMixedRate':f"{ts['mixed_standardized_pct']:.2f}"})
    hr=read('human_role_rates').set_index('group');hm=read('human_m1_recent').set_index('group');fm=read('followup_agreement').iloc[0]
    for group,prefix in zip(GROUPS,['CoreC','CoreJ','MixedJ','SSCI']):
        for suffix,col in [('HumanRate','point_pct'),('HumanLo','lower_pct'),('HumanHi','upper_pct')]:macros[prefix+suffix]=f'{hr.loc[group,col]:.2f}'
        macros[prefix+'HumanWide']=f'{wide.loc[group,"point_pct"]:.2f}'
    for group,prefix in zip(GROUPS[:2],['CoreC','CoreJ']):
        for suffix,col in [('HumanM','human_recent_pct'),('HumanMLo','lower_pct'),('HumanMHi','upper_pct')]:macros[prefix+suffix]=f'{hm.loc[group,col]:.2f}'
    for denom,prefix in zip(GROUPS[:2],['C','J']):
        row=cr[cr.numerator.eq('Mixed journals')&cr.denominator.eq(denom)].iloc[0]
        for suffix,col in [('Point','point'),('Lo','lower'),('Hi','upper')]:macros['HumanRatio'+prefix+suffix]=f'{row[col]:.2f}'
    macros.update({'FollowupRoleN':str(nums['human_followup']['role_annotations']),'FollowupMOneN':str(nums['human_followup']['m1_annotations']),'FollowupDistinct':str(nums['human_followup']['distinct_papers']),'FollowupMAccuracy':f'{100*fm.accuracy:.1f}','FollowupMKappa':f'{fm.fine_kappa:.3f}','FollowupMBinaryAccuracy':f'{100*fm.binary_accuracy:.1f}','FollowupMBinaryKappa':f'{fm.binary_kappa:.3f}'})
    (out/'numbers.tex').write_text('\n'.join('\\newcommand{\\'+k+'}{'+v+'}' for k,v in macros.items())+'\n',encoding='utf-8')
    (out/'numbers.json').write_text(json.dumps(macros,indent=2),encoding='utf-8')
    print('generated 10 tables and numeric macros')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--data',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();produce(a.data,a.out)
