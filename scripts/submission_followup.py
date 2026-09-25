"""Pure offline scoring of investigator-confirmed expert follow-up labels.
No file access, model calls or private adjudication text in this module.
"""
import pandas as pd
from submission_analysis import finite_bounds,DEV,GROUPS,PEN

def fraction_bounds(N,n,k,family):
    lo,hi=finite_bounds(int(N),int(n),int(k),.05/family)
    return {'N':int(N),'n':int(n),'k':int(k),'point':float(N*k/n) if n else None,'lower':lo,'upper':hi}

def role_estimates(papers,old_hit_gold,filled,key,positive_labels=('dl_native',)):
    recent=papers[papers.penetration_eligible & papers.year.between(2021,2025)].copy()
    new=filled.merge(key[key.task.eq('role')],on='case_id',validate='one_to_one')
    if len(new)!=len(filled):raise ValueError('Role case IDs absent from sampling key')
    new=new.merge(papers[['corpus_id','group','extended_vocabulary','penetration_eligible','screen_hit']],on='corpus_id',validate='one_to_one')
    if not (new.penetration_eligible & ~new.screen_hit).all():raise ValueError('Role sample no longer matches non-hit frame')
    cells=[];groups=[]
    for group in GROUPS:
        domain=recent[recent.group.eq(group)];total=lo=hi=0.
        for role in PEN:
            population=domain[domain.screen_hit&domain.penetration_label.eq(role)]
            sample=old_hit_gold[old_hit_gold.group.eq(group)&old_hit_gold.year.between(2021,2025)&old_hit_gold.label.eq(role)]
            r=fraction_bounds(len(population),len(sample),sample.human_label.isin(positive_labels).sum(),24)
            if r['point'] is None:raise ValueError('Old hit cell has no human reference: point not identified')
            cells.append({'group':group,'component':'historical_human_hits','stratum':role,**r});total+=r['point'];lo+=r['lower'];hi+=r['upper']
        for enriched in [True,False]:
            population=domain[~domain.screen_hit&domain.extended_vocabulary.eq(enriched)]
            sample=new[new.group.eq(group)&new.extended_vocabulary.eq(enriched)]
            if sample.empty:raise ValueError('Missing new recall cell')
            if not sample.N.eq(len(population)).all() or not sample.n.eq(len(sample)).all():raise ValueError('Saved non-hit N/n do not match population and complete sample')
            r=fraction_bounds(len(population),len(sample),sample.human_label.isin(positive_labels).sum(),24)
            cells.append({'group':group,'component':'new_human_nonhits','stratum':'enriched' if enriched else 'ordinary',**r});total+=r['point'];lo+=r['lower'];hi+=r['upper']
        groups.append({'group':group,'denominator':len(domain),'point_pct':100*total/len(domain),'lower_pct':100*lo/len(domain),'upper_pct':100*hi/len(domain),'target':'expert-labelled role under specified sampling design; old hit-stage working SRS assumptions retained','family_size':24})
    grouped=pd.DataFrame(groups);indexed=grouped.set_index('group');ratios=[]
    for numer in GROUPS[2:]:
        for denom in GROUPS[:2]:
            a,b=indexed.loc[numer],indexed.loc[denom]
            ratios.append({'numerator':numer,'denominator':denom,'point':a.point_pct/b.point_pct if b.point_pct else float('inf'),'lower':a.lower_pct/b.upper_pct if b.upper_pct else float('inf'),'upper':a.upper_pct/b.lower_pct if b.lower_pct else float('inf'),'family_size':24})
    return pd.DataFrame(cells),grouped,pd.DataFrame(ratios)

def m1_recent_estimates(papers,old_gold,filled,key):
    new=filled.merge(key[key.task.eq('m1')],on='case_id',validate='one_to_one')
    new=new.merge(papers[['corpus_id','group','m1_observed','m1_label']],on='corpus_id',validate='one_to_one')
    if len(new)!=len(filled) or not new.m1_observed.all():raise ValueError('M1 sample frame mismatch')
    if set(new.corpus_id)&set(old_gold.corpus_id):raise ValueError('New M1 sample overlaps excluded old-gold units')
    rows=[]
    for group in GROUPS[:2]:
        domain=papers[papers.m1_observed&papers.group.eq(group)&papers.year.between(2021,2025)]
        known=old_gold[old_gold.corpus_id.isin(domain.corpus_id)]
        remainder=domain[~domain.corpus_id.isin(known.corpus_id)]
        sample=new[new.group.eq(group)]
        if not sample.N.eq(len(remainder)).all() or not sample.n.eq(len(sample)).all():raise ValueError('New M1 complement N/n mismatch')
        r=fraction_bounds(len(remainder),len(sample),sample.human_label.isin(DEV).sum(),2)
        known_pos=int(known.human_label.isin(DEV).sum());D=len(domain)
        rows.append({'group':group,'denominator':D,'old_known_n':len(known),'old_known_positive':known_pos,'complement_N':len(remainder),'new_n':len(sample),'new_positive':r['k'],'machine_pct':100*domain.m1_label.isin(DEV).mean(),'human_recent_pct':100*(known_pos+r['point'])/D,'lower_pct':100*(known_pos+r['lower'])/D,'upper_pct':100*(known_pos+r['upper'])/D,'family_size':2,'interpretation':'recent endpoint only; not a new confidence interval for the old-to-new trend'})
    return pd.DataFrame(rows),new
