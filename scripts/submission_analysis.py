"""Offline revision analysis from released, text-free derived data.

No database, model client, credentials, network or raw abstracts are needed.
Usage: python submission_analysis.py --data DATA --out OUT
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import hypergeom

GROUPS=['Core EC conferences','Core EC journals','Mixed journals','SSCI (mixed conf.)']
DEV=['propose_new','improve','hybrid']
CLASSES=['propose_new','improve','hybrid','apply','theory','benchmark','review','other']
PEN=['dl_native','neuroevolution','hybrid','other']
WINDOWS=[(1996,2000),(2001,2005),(2006,2010),(2011,2015),(2016,2020),(2021,2025)]

def finite_bounds(N:int,m:int,k:int,alpha:float=.05):
    """Equal-tail hypergeometric inversion, including empty and census samples."""
    if not 0<=k<=m<=N:raise ValueError((N,m,k))
    if m==0:return 0,N
    if m==N:return k,k
    tail=alpha/2;left=k;right=N-m+k
    lo,hi=left,right
    while lo<hi:
        mid=(lo+hi)//2
        if hypergeom.sf(k-1,N,mid,m)>=tail:hi=mid
        else:lo=mid+1
    lower=lo;lo,hi=left,right
    while lo<hi:
        mid=(lo+hi+1)//2
        if hypergeom.cdf(k,N,mid,m)>=tail:lo=mid
        else:hi=mid-1
    return lower,lo

def kappa(a,b,weight=None):
    a=pd.Series(a).reset_index(drop=True);b=pd.Series(b).reset_index(drop=True)
    w=np.ones(len(a)) if weight is None else np.asarray(weight,dtype=float)
    w=w/w.sum();po=float(w[a.eq(b)].sum())
    classes=set(a)|set(b);pe=sum(w[a.eq(c)].sum()*w[b.eq(c)].sum() for c in classes)
    return (po-pe)/(1-pe) if pe<1 else np.nan

def two_phase_covariance(sample:pd.DataFrame,residual:np.ndarray):
    """Working independent-stratified-SRS variance, NOT a sparse-error exact CI.
    sample fields: era,N1,n1,pi1,sampling_label,N2,n2,pi2.
    The residual matrix keeps zero-valued units outside each domain.
    """
    s=sample.reset_index(drop=True);e=np.asarray(residual,float)
    size=e.shape[1];v1=np.zeros((size,size));v2=v1.copy()
    for _,part in s.groupby('era'):
        ii=part.index.to_numpy();Nh,nh=int(part.N1.iloc[0]),int(part.n1.iloc[0])
        if nh==Nh:continue
        if nh<2:raise ValueError('noncensus first-stage singleton')
        cov=np.zeros_like(v1)
        for a,i in enumerate(ii):
            for j in ii[a+1:]:
                ri,rj=s.iloc[i],s.iloc[j]
                if ri.sampling_label==rj.sampling_label:
                    M,q=int(ri.N2),int(ri.n2)
                    prob=q*(q-1)/(M*(M-1)) if M>1 else 1.
                else:prob=float(ri.pi2*rj.pi2)
                if prob<=0:raise ValueError('unestimable pair inclusion')
                diff=e[i]-e[j];cov+=np.outer(diff,diff)/prob
        v1+=Nh*Nh*(1-nh/Nh)/nh*cov/(nh*(nh-1))
    z=e/s.pi1.to_numpy()[:,None]
    for _,part in s.groupby('sampling_label'):
        M,q=int(part.N2.iloc[0]),int(part.n2.iloc[0])
        if q==M:continue
        if len(part)!=q or q<2:raise ValueError('incomplete second-stage covariance cell')
        zz=z[part.index];center=zz-zz.mean(axis=0)
        v2+=M*M*(1-q/M)/q*(center.T@center)/(q-1)
    return v1+v2

def analyze(data:Path,out:Path):
    out.mkdir(parents=True,exist_ok=True)
    def read(name):return pd.read_csv(data/name,keep_default_na=True,low_memory=False)
    def save(df,name):df.to_csv(out/('revision_'+name+'.csv'),index=False)
    p=read('analysis_papers.csv');m=read('calibration_m1.csv');g=read('calibration_penetration.csv')
    sv=read('sampling_penetration.csv');sm=read('sampling_m1.csv');rec=read('recall_validation.csv')
    assert p.corpus_id.is_unique and len(m)==300 and len(g)==300
    pen=p[p.penetration_eligible].copy();coded=p[p.m1_observed].copy()
    pen['hit']=pen.screen_hit;pen['dl']=pen.penetration_label.eq('dl_native')
    pen['neuro']=pen.penetration_label.eq('neuroevolution');pen['hybrid']=pen.penetration_label.eq('hybrid')
    pen['other']=pen.penetration_label.eq('other');coded['dev']=coded.m1_label.isin(DEV)
    assert pen.loc[pen.hit,'penetration_label'].notna().all()
    year=pen.groupby(['group','year']).agg(n=('corpus_id','size'),hits=('hit','sum'),dl=('dl','sum'),neuro=('neuro','sum'),hybrid=('hybrid','sum'),other=('other','sum')).reset_index()
    for c in ['hits','dl','neuro','hybrid','other']:year[c+'_pct']=100*year[c]/year.n
    save(year,'roles_yearly')
    windows=[];venues=[]
    for a,b in [(2016,2020),(2021,2023),(2021,2025)]:
        w=pen[pen.year.between(a,b)]
        for group,z in w.groupby('group'):
            row=dict(group=group,window=f'{a}-{b}',n=len(z))
            for c in ['hit','dl','neuro','hybrid','other']:row['n_'+c]=int(z[c].sum());row[c+'_pct']=100*z[c].mean()
            row['wide_pct']=100*(z.dl|z.hybrid).mean();row['integrated_pct']=100*(z.neuro|z.hybrid).mean()
            row['venue_equal_pct']=100*z.groupby('venue_abbr').dl.mean().mean();windows.append(row)
        for venue,z in w.groupby('venue_abbr'):
            venues.append(dict(window=f'{a}-{b}',venue=venue,group=z.group.iloc[0],n=len(z),hits=int(z.hit.sum()),dl=int(z.dl.sum()),dl_pct=100*z.dl.mean(),hit_pct=100*z.hit.mean()))
    win=pd.DataFrame(windows);venue=pd.DataFrame(venues);save(win,'roles_windows');save(venue,'roles_venues')
    ratios=[]
    for period,z in win.groupby('window'):
        z=z.set_index('group')
        for mix in GROUPS[2:]:
            for core in GROUPS[:2]:
                ratios.append(dict(window=period,numerator=mix,denominator=core,narrow_ratio=z.loc[mix,'dl_pct']/z.loc[core,'dl_pct'],wide_ratio=z.loc[mix,'wide_pct']/z.loc[core,'wide_pct'],keyword_ratio=z.loc[mix,'hit_pct']/z.loc[core,'hit_pct'],equal_venue_ratio=z.loc[mix,'venue_equal_pct']/z.loc[core,'venue_equal_pct']))
    save(pd.DataFrame(ratios),'role_ratios')
    loo=[]
    for group,z in venue[venue.window.eq('2021-2025')].groupby('group'):
        for v in z.venue:
            t=z[z.venue.ne(v)]
            if len(t):loo.append(dict(group=group,excluded=v,n=int(t.n.sum()),dl=int(t.dl.sum()),dl_pct=100*t.dl.sum()/t.n.sum()))
    save(pd.DataFrame(loo),'leave_one_out')
    # M1: full target set, core, EC-labelled; historical inclusion sensitivity explicit.
    mw=[];my=[]
    for scope in ['target_nonempty','core_nonempty','ec_nonempty','historical_notnull']:
        z=coded
        if scope=='core_nonempty':z=z[z.group.str.startswith('Core')]
        if scope=='ec_nonempty':z=z[z.ec_label.eq('ec')]
        if scope=='historical_notnull':z=p[p.year.between(1990,2025)&p.abstract_status.ne('null')&p.m1_label.notna()].copy();z['dev']=z.m1_label.isin(DEV)
        for yy,t in z.groupby('year'):
            row=dict(scope=scope,year=int(yy),n=len(t),method_dev=int(t.dev.sum()))
            for label in CLASSES:row[label]=int(t.m1_label.eq(label).sum())
            my.append(row)
        for a,b in WINDOWS:
            t=z[z.year.between(a,b)];row=dict(scope=scope,window=f'{a}-{b}',n=len(t),method_dev=int(t.dev.sum()),method_dev_pct=100*t.dev.mean())
            for label in CLASSES:row[label]=int(t.m1_label.eq(label).sum());row[label+'_pct']=100*t.m1_label.eq(label).mean()
            mw.append(row)
    save(pd.DataFrame(my),'contribution_yearly');save(pd.DataFrame(mw),'contribution_windows')
    # Exact missing-text partition for target venues; no overlap or assumed zero labels.
    bounds=[]
    for a,b in [(1996,2000),(2021,2025)]:
        z=p[p.target_venue&p.year.between(a,b)];obs=z[z.m1_observed];K=int(obs.m1_label.isin(DEV).sum());N=len(z);missing=N-len(obs)
        assert len(obs)+missing==N
        bounds.append(dict(window=f'{a}-{b}',N=N,observed=len(obs),missing=missing,method_dev=K,lower_pct=100*K/N,upper_pct=100*(K+missing)/N))
    save(pd.DataFrame(bounds),'missing_text_bounds')
    coverage=p[p.target_venue&p.year.le(2025)].groupby(['group','year']).agg(n=('corpus_id','size'),nonempty=('abstract_status',lambda s:int(s.eq('nonempty').sum()))).reset_index();coverage['coverage_pct']=100*coverage.nonempty/coverage.n;save(coverage,'abstract_coverage')
    # Sample agreement + design weighted calibration, distinct estimands.
    cal=[]
    for task,z,human,pred,coarse in [('m1',m,'human_label','production_label',DEV),('penetration',g,'human_label','label',['dl_native'])]:
        for weighting in ['unweighted','two_stage']:
            w=np.ones(len(z)) if weighting=='unweighted' else z.weight.to_numpy();hw=z[human];pw=z[pred]
            cal.append(dict(task=task,weighting=weighting,n=len(z),effective_n=w.sum()**2/(w*w).sum(),accuracy=np.average(hw.eq(pw),weights=w),kappa=kappa(hw,pw,w),binary_accuracy=np.average(hw.isin(coarse).eq(pw.isin(coarse)),weights=w),binary_net_bias_pp=100*np.average(pw.isin(coarse).astype(int)-hw.isin(coarse).astype(int),weights=w)))
        cm=pd.crosstab(z[human],z[pred]).reset_index();save(cm,'confusion_'+task)
    save(pd.DataFrame(cal),'calibration')
    # Human calibration of hits and model recall: one predeclared family of 24 strata.
    # Bounds are conditional-SRS working-design ranges; not human truth of nonhits.
    family=24;cells=[];combined=[]
    for group in GROUPS:
        domain=pen[pen.group.eq(group)&pen.year.between(2021,2025)];D=len(domain)
        hpoint=hlo=hhi=0.;rpoint=rlo=rhi=0.
        gg=g[g.group.eq(group)]
        difference=int(domain.dl.sum())+float((gg.weight*(gg.human_label.eq('dl_native').astype(int)-gg.label.eq('dl_native').astype(int))*gg.year.between(2021,2025)).sum())
        for label in PEN:
            pop=domain[domain.penetration_label.eq(label)];sample=gg[gg.year.between(2021,2025)&gg.label.eq(label)]
            N,n=len(pop),len(sample);k=int(sample.human_label.eq('dl_native').sum());lo,hi=finite_bounds(N,n,k,.05/family)
            est=N*k/n if n else np.nan;hpoint+=est;hlo+=lo;hhi+=hi
            cells.append(dict(component='human_hits',group=group,stratum=label,N=N,n=n,k=k,point_total=est,lower_total=lo,upper_total=hi,family_size=family))
        for enrich in [True,False]:
            pop=domain[~domain.hit&domain.extended_vocabulary.eq(enrich)]
            sample=rec[rec.group.eq(group)&rec.year.between(2021,2025)&rec.is_enriched.eq(enrich)]
            sample=sample[sample.part.eq('enriched' if enrich else 'random')]
            N,n=len(pop),len(sample);k=int(sample.label.eq('dl_native').sum());lo,hi=finite_bounds(N,n,k,.05/family)
            est=N*k/n if n else np.nan;rpoint+=est;rlo+=lo;rhi+=hi
            cells.append(dict(component='model_recall',group=group,stratum='enriched' if enrich else 'ordinary',N=N,n=n,k=k,point_total=est,lower_total=lo,upper_total=hi,family_size=family))
        combined.append(dict(group=group,n=D,machine_pct=100*domain.dl.mean(),human_hit_poststratified_pct=100*hpoint/D,human_hit_difference_raw_pct=100*difference/D,human_hit_lower_pct=100*hlo/D,human_hit_upper_pct=100*hhi/D,recall_model_pct=100*rpoint/D,combined_scenario_pct=100*(hpoint+rpoint)/D,combined_lower_pct=100*(hlo+rlo)/D,combined_upper_pct=100*(hhi+rhi)/D,interval_label='conditional SRS simultaneous working-design range; recall labels not human validated'))
    save(pd.DataFrame(cells),'calibration_cells');comb=pd.DataFrame(combined);save(comb,'calibrated_role_scenarios')
    cr=[];z=comb.set_index('group')
    for mix in GROUPS[2:]:
        for core in GROUPS[:2]:
            a,b=z.loc[mix],z.loc[core]
            cr.append(dict(numerator=mix,denominator=core,point=a.combined_scenario_pct/b.combined_scenario_pct,lower=a.combined_lower_pct/b.combined_upper_pct,upper=a.combined_upper_pct/b.combined_lower_pct if b.combined_lower_pct>0 else np.inf,assumptions='same predeclared 24-cell family; SRS working design; missed labels remain model-based'))
    save(pd.DataFrame(cr),'calibrated_ratios')
    # M1 two-stage difference point; endpoints do not contain noncandidate id89386.
    mc=[];residual_domains=[]
    meta=p.set_index('corpus_id')
    for scope in ['target_nonempty','core_nonempty','ec_nonempty']:
        for a,b in [(1996,2000),(2021,2025)]:
            d=p.m1_observed&p.year.between(a,b)
            if scope=='core_nonempty':d&=p.group.str.startswith('Core')
            if scope=='ec_nonempty':d&=p.ec_label.eq('ec')
            pop=p[d];wanted=set(pop.corpus_id);gm=m[m.corpus_id.isin(wanted)]
            base=int(pop.m1_label.isin(DEV).sum());res=gm.human_label.isin(DEV).astype(int)-gm.production_label.isin(DEV).astype(int)
            correction=float((gm.weight*res).sum());raw=100*(base+correction)/len(pop)
            residual_domains.append((m.human_label.isin(DEV).astype(int)-m.production_label.isin(DEV).astype(int)).to_numpy()*m.corpus_id.isin(wanted).to_numpy())
            mc.append(dict(scope=scope,window=f'{a}-{b}',n=len(pop),gold_in_domain=len(gm),machine_pct=100*base/len(pop),human_difference_raw_pct=raw,correction_count=correction,limitation='two-stage SRS working-design point; no zero-error bootstrap or nominal precision claim'))
    # One excluded pilot candidate (2003) has zero residual in all preset endpoint
    # domains; retain it in phase-1 pair sums rather than reducing n1.
    missing=sm[~sm.candidate].copy()
    assert missing.year.between(2001,2005).all()
    missing['sampling_label']='noncandidate_known_zero_domain';missing['N2']=1;missing['n2']=1;missing['pi2']=1.
    variance_sample=pd.concat([m,missing],ignore_index=True)
    residual=np.column_stack(residual_domains)
    residual=np.vstack([residual,np.zeros((len(missing),len(mc)))])
    covariance=two_phase_covariance(variance_sample,residual)
    assert np.allclose(covariance,covariance.T) and np.linalg.eigvalsh(covariance).min()>-1e-7
    for i,row in enumerate(mc):
        row['working_design_se_pp']=100*math.sqrt(covariance[i,i])/row['n']
        row['working_normal_diagnostic_lo']=row['human_difference_raw_pct']-1.96*row['working_design_se_pp']
        row['working_normal_diagnostic_hi']=row['human_difference_raw_pct']+1.96*row['working_design_se_pp']
    save(pd.DataFrame(mc),'m1_difference_points')
    labels=[x['scope']+'|'+x['window'] for x in mc]
    covdf=pd.DataFrame(covariance,index=labels,columns=labels).rename_axis('domain').reset_index();save(covdf,'m1_difference_covariance_counts')
    # Topic/year common support, journal comparisons only (same publication type).
    # Describes conditional composition, not venue policy or community causality.
    cs=[]
    for core in ['Core EC journals']:
        t=pen[pen.year.between(2021,2025)&pen.group.isin([core,'Mixed journals'])&~pen.topic.isin(['Missing controlled terms','Other/unclassified'])]
        agg=t.groupby(['year','topic','group']).agg(n=('corpus_id','size'),k=('dl','sum')).reset_index()
        nc=agg[agg.group.eq(core)].set_index(['year','topic']);nm=agg[agg.group.eq('Mixed journals')].set_index(['year','topic'])
        for key in nc.index.intersection(nm.index):
            a,b=nc.loc[key],nm.loc[key]
            if a.n<20 or b.n<20:continue
            cs.append(dict(year=key[0],topic=key[1],core_n=int(a.n),mixed_n=int(b.n),core_k=int(a.k),mixed_k=int(b.k),weight=int(a.n+b.n),core_pct=100*a.k/a.n,mixed_pct=100*b.k/b.n))
    cs=pd.DataFrame(cs);save(cs,'topic_common_support')
    if len(cs):
        support=dict(cells=len(cs),core_included=int(cs.core_n.sum()),mixed_included=int(cs.mixed_n.sum()),core_total=int(len(pen[pen.group.eq('Core EC journals')&pen.year.between(2021,2025)])),mixed_total=int(len(pen[pen.group.eq('Mixed journals')&pen.year.between(2021,2025)])),core_standardized_pct=float(np.average(cs.core_pct,weights=cs.weight)),mixed_standardized_pct=float(np.average(cs.mixed_pct,weights=cs.weight)))
    else:support={'cells':0,'status':'insufficient common support'}
    # Fixed lag prediction held out after 2020; fit only on fixed common support.
    lag=[]
    mixed=year[year.group.eq('Mixed journals')].set_index('year').dl_pct
    for core in GROUPS[:2]:
        c=year[year.group.eq(core)].set_index('year').dl_pct
        train=[y for y in range(2012,2021) if y in c.index and all(y-s in mixed.index for s in range(16))]
        test=[y for y in range(2021,2026) if y in c.index and all(y-s in mixed.index for s in range(16))]
        if len(train)<8 or len(test)<3:lag.append(dict(group=core,status='insufficient_support'));continue
        scores=[np.mean([(c[y]-mixed[y-s])**2 for y in train]) for s in range(16)];best=int(np.argmin(scores))
        for kind,preds in [('selected_lag',[mixed[y-best] for y in test]),('no_lag',[mixed[y] for y in test]),('last_core_level',[c[max(train)]]*len(test))]:
            mse=float(np.mean((c.loc[test].to_numpy()-np.asarray(preds))**2))
            lag.append(dict(group=core,status='heldout',model=kind,selected_shift=best,train_years=str(train),test_years=str(test),train_selected_mse=float(scores[best]),test_mse=mse,test_rmse_pp=math.sqrt(mse)))
    save(pd.DataFrame(lag),'lag_holdout')
    # Pilot direction with the revised target eligibility, not raw API row counts.
    pilot=[]
    for col in [c for c in sm if c.startswith('label_')]:
        row=dict(model=col[6:])
        for key,a,b in [('old',1996,2000),('new',2021,2025)]:
            z=sm[sm.year.between(a,b)&sm.corpus_id.isin(set(coded.corpus_id))&sm[col].notna()]
            row['n_'+key]=len(z);row[key+'_pct']=100*z[col].isin(DEV).mean()
        row['delta_pp']=row['new_pct']-row['old_pct'];pilot.append(row)
    save(pd.DataFrame(pilot),'pilot_deltas')
    # Core hit topics retain original controlled-term assignment, now derived per paper.
    topics=pen[pen.group.str.startswith('Core')&pen.dl].groupby(['year','topic']).size().unstack(fill_value=0).reset_index();save(topics,'core_dl_topics')
    save(pen[pen.group.str.startswith('Core')&pen.dl][['corpus_id','doi','year','venue_abbr','group','topic']], 'core_dl_papers')
    # New investigator-confirmed manual labels: keep them distinct from historical
    # model-recall scenarios and from the old gold sampling design.
    from submission_followup import role_estimates,m1_recent_estimates
    rh=read('followup_role_labels.csv');mh=read('followup_m1_labels.csv')
    human_provenance=json.loads((data/'human_followup_provenance.json').read_text(encoding='utf-8'))
    assert human_provenance['status']=='expert_manual_labels_complete'
    assert len(rh)==800 and len(mh)==200 and rh.case_id.is_unique and mh.case_id.is_unique
    assert rh.human_label.isin(PEN).all() and mh.human_label.isin(CLASSES).all()
    assert rh.uncertain.fillna('').eq('').all() and mh.uncertain.fillna('').eq('').all()
    designcols=['case_id','corpus_id','task','N','n']
    human_key=pd.concat([rh[designcols],mh[designcols]],ignore_index=True)
    hc,hr,hq=role_estimates(p,g,rh[['case_id','human_label']],human_key)
    wc,wr,wq=role_estimates(p,g,rh[['case_id','human_label']],human_key,positive_labels=('dl_native','hybrid'))
    hm,hpaired=m1_recent_estimates(p,m,mh[['case_id','human_label']],human_key)
    for name,df in [('human_role_cells',hc),('human_role_rates',hr),('human_role_ratios',hq),('human_m1_recent',hm)]:save(df,name)
    for name,df in [('human_wide_cells',wc),('human_wide_rates',wr),('human_wide_ratios',wq)]:
        df['definition']='DL-native plus substantive hybrid';df['inference_scope']='sensitivity definition; separate 24-cell family, not joint with narrow definition';save(df,name)
    fine_kappa=kappa(hpaired.human_label,hpaired.m1_label)
    binary_kappa=kappa(hpaired.human_label.isin(DEV),hpaired.m1_label.isin(DEV))
    hmetrics=pd.DataFrame([{'task':'m1_followup','n':len(hpaired),'accuracy':hpaired.human_label.eq(hpaired.m1_label).mean(),'fine_kappa':fine_kappa,'binary_accuracy':hpaired.human_label.isin(DEV).eq(hpaired.m1_label.isin(DEV)).mean(),'binary_kappa':binary_kappa,'scope':'unweighted recent-core validation sample, not corpus-wide accuracy'}])
    save(hmetrics,'followup_agreement')
    save(pd.crosstab(hpaired.human_label,hpaired.m1_label).rename_axis('human_label').reset_index(),'followup_confusion_m1')
    manifest=json.loads((data/'revision_data_manifest.json').read_text())
    numbers={'data':manifest,'topic_support':support,'primary_role_window':'2021-2025 (SSCI 2021-2023)','uncertainty_family':24,'uncertainty_method':'hypergeometric inversion and Bonferroni; conditional SRS working design, historical seed reuse disclosed','m1_method':'two-stage difference point diagnostic; no quality claim','nonempty_primary':True,'notes':'No API, raw texts or database used by this program.'}
    numbers['human_followup']={'role_annotations':len(rh),'m1_annotations':len(mh),'distinct_papers':int(pd.concat([rh.corpus_id,mh.corpus_id]).nunique()),'role_family':24,'recent_m1_family':2,'role_target':'expert-reference labels in both hit and non-hit populations; historical hit-stage working design retained','m1_target':'recent core endpoint; not a new temporal trend interval','fine_kappa_new_m1':float(fine_kappa),'all_role_ratio_lowers_above_one':bool(hq.lower.gt(1).all()),'all_role_ratio_lowers_above_three':bool(hq.lower.gt(3).all())}
    (out/'revision_numbers.json').write_text(json.dumps(numbers,indent=2),encoding='utf-8')
    print(json.dumps(numbers,indent=2));return numbers

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--data',type=Path,default=Path(__file__).resolve().parents[1]/'results/tables');ap.add_argument('--out',type=Path);a=ap.parse_args();analyze(a.data,a.out or a.data)
