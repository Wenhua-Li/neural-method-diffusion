"""Offline main and supplementary figures from text-free revision tables."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from style import apply_style,PALETTE
GROUPS=['Core EC conferences','Core EC journals','Mixed journals','SSCI (mixed conf.)']
SHORT=['Core conferences','Core journals','Mixed journals','SSCI (through 2023)']
COLORS=[PALETTE['ec'],'#56B4E9',PALETTE['accent'],PALETTE['purple']]
LABELS=['dl_native','neuroevolution','hybrid','other']
ROLE_LABEL=['DL-native','Neuroevolution','Substantive hybrid','Other']
ROLE_COLORS=[PALETTE['accent'],PALETTE['ec'],PALETTE['green'],'#BBBBBB']
NAMES=['fig1_true_penetration','fig2_domestication','fig3_method_dev','fig4_penetrators','supp_fig1_coverage','supp_fig2_calibration','supp_fig3_recall','supp_fig4_venues','supp_fig5_robustness','supp_fig6_contributions','supp_fig7_validation','supp_fig8_missingness']

def produce(data:Path,out:Path):
    out.mkdir(parents=True,exist_ok=True);(out/'pdf').mkdir(exist_ok=True)
    apply_style();plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],'font.size':8,'axes.labelsize':8,'axes.titlesize':8,'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,'pdf.fonttype':42,'axes.grid':False,'savefig.bbox':'tight'})
    def read(n):return pd.read_csv(data/('revision_'+n+'.csv'))
    def save(fig,name):
        fig.savefig(out/(name+'.png'),dpi=220);fig.savefig(out/'pdf'/(name+'.pdf'));plt.close(fig)
    def letter(ax,s):ax.text(-0.12,1.04,s,transform=ax.transAxes,fontweight='bold',fontsize=9,va='bottom')
    y=read('roles_yearly');w=read('roles_windows');latest=w[w.window.eq('2021-2025')].set_index('group').loc[GROUPS]
    previous=w[w.window.eq('2016-2020')].set_index('group').loc[GROUPS]

    # Main Fig. 1: annual series, recent snapshot and definitional comparison of the frozen screen.
    fig,axes=plt.subplots(1,3,figsize=(6.4,2.5),layout='constrained')
    ax=axes[0];handles=[]
    for i,g in enumerate(GROUPS):
        z=y[y.group.eq(g)&y.year.ge(2000)];ls='--' if i in [1,3] else '-'
        ax.plot(z.year,z.dl_pct,color=COLORS[i],ls=ls);ax.plot(z.year,z.hits_pct,color=COLORS[i],ls=ls,alpha=.4,lw=.9)
        handles+=[plt.Line2D([],[],color=COLORS[i],ls=ls,label=['Core conf.','Core journ.','Mixed journ.','SSCI'][i]+', DL-native'),plt.Line2D([],[],color=COLORS[i],ls=ls,alpha=.45,lw=.9,label=['Core conf.','Core journ.','Mixed journ.','SSCI'][i]+', keyword hit')]
    ax.legend(handles=handles,loc='upper left',frameon=False,fontsize=5.2,ncol=1,handlelength=1.1,columnspacing=.6,labelspacing=.22,borderaxespad=0)
    ax.set(xlabel='Publication year',ylabel='Share of eligible papers (%)',xlim=(2010,2025.5),ylim=(0,33));letter(ax,'a')
    ax=axes[1];x=np.arange(4);ax.bar(x-.18,latest.dl_pct,.34,color=PALETTE['ec'],label='DL-native');ax.bar(x+.18,latest.wide_pct,.34,color=PALETTE['accent'],label='DL-native + hybrid')
    for i,r in enumerate(latest.itertuples()):ax.text(i,r.wide_pct+.8,f'n={r.n:,}',ha='center',fontsize=6)
    ax.set_xticks(x,['Core\nconf.','Core\njourn.','Mixed\njourn.','SSCI\n(to 2023)']);ax.tick_params(axis='x',labelsize=6);ax.set(ylabel='Share in 2021–2025 (%)',ylim=(0,30));ax.legend(loc='upper left',frameon=False,fontsize=6);letter(ax,'b')
    ax=axes[2];vals=latest[['hit_pct','dl_pct','wide_pct']].to_numpy()
    for j,(label,color) in enumerate([('Keyword hit','#999999'),('DL-native',PALETTE['ec']),('DL-native + hybrid',PALETTE['accent'])]):ax.barh(x+(j-1)*.22,vals[:,j],.19,color=color,label=label)
    ax.set_yticks(x,['Core\nconf.','Core\njourn.','Mixed\njourn.','SSCI\n(to 2023)']);ax.tick_params(axis='y',labelsize=6);ax.invert_yaxis();ax.set_ylim(3.5,-0.6);ax.set_xlabel('Share of eligible papers (%)');ax.legend(loc='upper right',bbox_to_anchor=(1.08,0.8),frameon=False,fontsize=6);letter(ax,'c');save(fig,NAMES[0])

    # Main Fig. 2: composition, integration and change (venue-level panel lives in Supp. Fig. S4).
    fig,axes=plt.subplots(1,3,figsize=(6.4,2.5),layout='constrained');ax=axes[0];bottom=np.zeros(4)
    for col,label,color in zip(['n_dl','n_neuro','n_hybrid','n_other'],ROLE_LABEL,ROLE_COLORS):
        values=100*latest[col].to_numpy()/latest.n_hit.to_numpy();ax.barh(np.arange(4),values,left=bottom,color=color,label=label);bottom+=values
    ax.set_yticks(np.arange(4),['Core\nconf.','Core\njourn.','Mixed\njourn.','SSCI\n(to 2023)']);ax.tick_params(axis='y',labelsize=6);ax.invert_yaxis();ax.set_xlabel('Composition of\nkeyword-hit papers (%)');letter(ax,'a')
    h,l=ax.get_legend_handles_labels();fig.legend(h,l,ncol=4,loc='lower center',bbox_to_anchor=(0.5,-0.07),fontsize=6,frameon=False)
    ax=axes[1];core=y[y.group.str.startswith('Core')&y.year.ge(2000)].groupby('year')[['n','neuro','hybrid']].sum()
    for col,label,color in [('neuro','Neuroevolution',PALETTE['ec']),('hybrid','Substantive hybrid',PALETTE['green'])]:ax.plot(core.index,100*core[col]/core.n,label=label,color=color)
    ax.set(xlabel='Publication year',ylabel='Share of core-venue papers (%)');ax.legend(frameon=False,fontsize=6,loc='upper left');letter(ax,'b')
    ax=axes[2];core_groups=['Core EC conferences','Core EC journals'];xpos=np.arange(2)
    for j,(label,field,color) in enumerate([('2016–20 neuro','neuro_pct',PALETTE['ec']),('2021–25 neuro','neuro_pct','#56B4E9'),('2016–20 hybrid','hybrid_pct',PALETTE['green']),('2021–25 hybrid','hybrid_pct','#66C2A5')]):
        frame=previous if '2016' in label else latest;ax.bar(xpos+(j-1.5)*.18,frame.loc[core_groups,field],.16,color=color,label=label)
    ax.set_xticks(xpos,['Core\nconf.','Core\njourn.']);ax.set_ylabel('Share of eligible papers (%)');ax.legend(fontsize=5.6,frameon=False,ncol=2,loc='upper right',handlelength=1.2,columnspacing=.6,labelspacing=.3);letter(ax,'c');save(fig,NAMES[1])

    # Main Fig. 3: human-calibrated role estimates are the primary evidence.
    rates=read('human_role_rates').set_index('group').loc[GROUPS];wide=read('human_wide_rates').set_index('group').loc[GROUPS];ratios=read('human_role_ratios');wide_ratios=read('human_wide_ratios');old=read('calibrated_role_scenarios').set_index('group').loc[GROUPS]
    fig,axes=plt.subplots(1,3,figsize=(6.4,2.5),layout='constrained')
    ax=axes[0]
    for i,g in enumerate(GROUPS):
        r=rates.loc[g];rw=wide.loc[g]
        ax.plot([r.lower_pct,r.upper_pct],[i-.17,i-.17],color=COLORS[i],lw=1.8);ax.scatter(r.point_pct,i-.17,color=COLORS[i],s=20,zorder=3);ax.scatter(latest.loc[g,'dl_pct'],i-.17,marker='x',color='black',s=20,zorder=3)
        ax.plot([rw.lower_pct,rw.upper_pct],[i+.17,i+.17],color=COLORS[i],lw=1.8,alpha=.55);ax.scatter(rw.point_pct,i+.17,facecolors='none',edgecolors=COLORS[i],s=20,zorder=3);ax.scatter(latest.loc[g,'wide_pct'],i+.17,marker='x',color='black',s=20,zorder=3,alpha=.55)
    ax.set_yticks(range(4),['Core conf.','Core journ.','Mixed journ.','SSCI (to 2023)']);ax.tick_params(axis='y',labelsize=6);ax.set_ylim(3.55,-1.45);ax.set_xlabel('Share of eligible papers (%)')
    ax.plot([],[],color='grey',marker='o',ms=4,lw=1.8,label='Narrow (DL-native)');ax.plot([],[],color='grey',marker='o',ms=4,mfc='none',lw=1.8,alpha=.55,label='Wide (+ hybrid)');ax.plot([],[],color='black',marker='x',ms=4,ls='',label='Frozen screened share');ax.legend(frameon=False,fontsize=5.6,loc='upper right',handlelength=1.3,labelspacing=.3,borderaxespad=.1);letter(ax,'a')
    ax=axes[1];pairs=[('Mixed/Core\nconferences','Mixed journals','Core EC conferences'),('Mixed/Core\njournals','Mixed journals','Core EC journals')]
    for j,(label,numerator,denominator) in enumerate(pairs):
        r=ratios[(ratios.numerator==numerator)&(ratios.denominator==denominator)].iloc[0];rw=wide_ratios[(wide_ratios.numerator==numerator)&(wide_ratios.denominator==denominator)].iloc[0];ax.errorbar(r.point,j-.11,xerr=[[r.point-r.lower],[r.upper-r.point]],fmt='o',ms=4,color=PALETTE['ec'],capsize=2,label='Narrow' if j==0 else None);ax.errorbar(rw.point,j+.11,xerr=[[rw.point-rw.lower],[rw.upper-rw.point]],fmt='o',ms=4,color=PALETTE['accent'],capsize=2,label='Wide' if j==0 else None)
    ax.axvline(1,color='#999999',ls='--',lw=.8);ax.set_yticks(np.arange(2),[p[0] for p in pairs]);ax.tick_params(axis='y',labelsize=6);ax.set_xscale('log');ax.set_xlabel('Mixed/core share ratio\n(log scale)');ax.legend(frameon=False,fontsize=6);letter(ax,'b')
    ax=axes[2]
    for i,g in enumerate(GROUPS):
        r=old.loc[g];ax.plot([r.combined_lower_pct,r.combined_upper_pct],[i,i],color='#AAAAAA',lw=1.7);ax.scatter(r.combined_scenario_pct,i,marker='^',color='#777777',s=22);ax.scatter(rates.loc[g,'point_pct'],i,color=COLORS[i],s=22)
    ax.set_yticks(range(4),['Core conf.','Core journ.','Mixed journ.','SSCI (to 2023)']);ax.tick_params(axis='y',labelsize=6);ax.invert_yaxis();ax.set_xlabel('DL-native share (%)');ax.plot([],[],color='#777777',marker='^',ls='',label='Earlier model-recall scenario');ax.plot([],[],color='grey',marker='o',ls='',label='Human-calibrated point');ax.legend(frameon=False,fontsize=6,loc='center right');letter(ax,'c');save(fig,NAMES[3])

    # Main Fig. 4: secondary M1 result and its validation boundaries.
    c=read('contribution_yearly');cw=read('contribution_windows');fig,axes=plt.subplots(1,3,figsize=(6.4,2.5),layout='constrained');z=c[c.scope.eq('target_nonempty')&c.year.ge(1996)]
    ax=axes[0]
    for col,label,color in [('method_dev','Method development',PALETTE['ec']),('apply','Application',PALETTE['accent']),('theory','Theory','#777777')]:ax.plot(z.year,100*z[col]/z.n,label=label,color=color)
    ax.set(xlabel='Publication year',ylabel='Share of coded papers (%)');ax.legend(frameon=False);letter(ax,'a')
    ax=axes[1]
    for scope,label,color in [('target_nonempty','All target venues',PALETTE['all']),('core_nonempty','Core venues',PALETTE['ec']),('ec_nonempty','EC-labelled subset',PALETTE['green'])]:
        zz=cw[cw.scope.eq(scope)];ax.plot(np.arange(len(zz)),zz.method_dev_pct,'o-',color=color,label=label)
    bounds=read('missing_text_bounds').set_index('window')
    for xi,wn in [(0,'1996-2000'),(5,'2021-2025')]:
        r=bounds.loc[wn];ax.plot([xi,xi],[r.lower_pct,r.upper_pct],color='#555555',lw=2,solid_capstyle='butt',zorder=1)
    ax.plot([],[],color='#555555',lw=2,label='Missing-text bounds')
    ax.set_xticks(np.arange(6),['1996–00','2001–05','2006–10','2011–15','2016–20','2021–25'],rotation=25,ha='right');ax.set_ylabel('Method-development share (%)');ax.legend(frameon=False,fontsize=6.5);letter(ax,'b')
    ax=axes[2];recent=read('human_m1_recent').set_index('group').loc[GROUPS[:2]];xpos=np.arange(2);ax.bar(xpos-.17,recent.machine_pct,.32,color=PALETTE['ec'],label='Frozen share');ax.errorbar(xpos+.17,recent.human_recent_pct,yerr=np.vstack([recent.human_recent_pct-recent.lower_pct,recent.upper_pct-recent.human_recent_pct]),fmt='o',color=PALETTE['accent'],capsize=2,label='Human-calibrated endpoint');ax.set_xticks(xpos,['Core conferences','Core journals']);ax.set_ylabel('Method-development share, 2021–2025 (%)');ax.legend(frameon=False,fontsize=6.5);letter(ax,'c');save(fig,NAMES[2])
    cov=read('abstract_coverage');fig,ax=plt.subplots(figsize=(6.4,4.3),layout='constrained')
    for i,g in enumerate(GROUPS):
        z=cov[cov.group.eq(g)&cov.year.ge(1990)];ax.plot(z.year,z.coverage_pct,label=SHORT[i],color=COLORS[i])
    ax.set(xlabel='Publication year',ylabel='Nonempty-abstract coverage (%)',ylim=(0,105));ax.legend(ncol=2);save(fig,NAMES[4])
    def heat(ax,cm,xlabel):
        ax.imshow(cm.to_numpy(),cmap='Blues',aspect='auto')
        for i in range(len(cm)):
            for j in range(len(cm.columns)):ax.text(j,i,str(int(cm.iloc[i,j])),ha='center',va='center',fontsize=10,color='white' if cm.iloc[i,j]>cm.to_numpy().max()/2 else 'black')
        ax.set_xticks(range(len(cm.columns)),[x.replace('_',' ') for x in cm.columns],rotation=30,ha='right');ax.set_yticks(range(len(cm)),[x.replace('_',' ') for x in cm.index]);ax.set(xlabel=xlabel,ylabel='Reference label')
    fig,axes=plt.subplots(2,1,figsize=(6.4,8),layout='constrained')
    for ax,task in zip(axes,['m1','penetration']):heat(ax,read('confusion_'+task).set_index('human_label'),'Frozen production label');letter(ax,'a' if task=='m1' else 'b')
    save(fig,NAMES[5]);sc=read('human_role_rates').set_index('group').loc[GROUPS];oldsc=read('calibrated_role_scenarios').set_index('group').loc[GROUPS];fig,ax=plt.subplots(figsize=(6.4,4.8),layout='constrained')
    for i,g in enumerate(GROUPS):
        r=sc.loc[g];old=oldsc.loc[g];ax.plot([r.lower_pct,r.upper_pct],[i-.12,i-.12],color=COLORS[i],lw=2);ax.scatter(r.point_pct,i-.12,color=COLORS[i],s=48);ax.plot([old.combined_lower_pct,old.combined_upper_pct],[i+.12,i+.12],color='#AAAAAA',lw=1);ax.scatter(old.combined_scenario_pct,i+.12,marker='x',color='#888888',s=40)
    ax.plot([],[],color='grey',marker='o',label='Expert-calibrated hits and non-hits');ax.plot([],[],color='#AAAAAA',marker='x',label='Earlier model-recall scenario');ax.set_yticks(range(4),SHORT);ax.invert_yaxis();ax.set_xlabel('DL-native share of eligible papers (%)');ax.legend(loc='upper center',bbox_to_anchor=(.5,1.2));save(fig,NAMES[6])
    v=read('roles_venues');v=v[v.window.eq('2021-2025')].sort_values('dl_pct');fig,ax=plt.subplots(figsize=(6.4,8),layout='constrained');ax.barh(v.venue,v.dl_pct,color=[COLORS[GROUPS.index(g)] for g in v.group]);ax.set_xlabel('Frozen DL-native share, 2021–2025 (%)');save(fig,NAMES[7])
    hold=read('lag_holdout');fig,axes=plt.subplots(2,1,figsize=(6.4,7),layout='constrained')
    for i,g in enumerate(GROUPS[:2]):
        z=hold[hold.group.eq(g)];axes[0].bar(np.arange(3)+i*.35,z.test_rmse_pp,.35,color=COLORS[i],label=SHORT[i])
    axes[0].set_xticks(np.arange(3)+.175,['Training-selected lag','No lag','Last core level'],rotation=15,ha='right');axes[0].set_ylabel('Held-out RMSE (percentage points)');axes[0].legend();letter(axes[0],'a')
    topics=read('topic_common_support');axes[1].scatter(topics.core_pct,topics.mixed_pct,s=np.sqrt(topics.weight)*3,alpha=.7,color=PALETTE['green']);axes[1].plot([0,60],[0,60],'--',color='#999999');axes[1].set(xlabel='Core journals: DL-native share (%)',ylabel='Mixed journals: DL-native share (%)');letter(axes[1],'b');save(fig,NAMES[8])
    fig,axes=plt.subplots(2,1,figsize=(6.4,7),layout='constrained');z=c[c.scope.eq('target_nonempty')&c.year.ge(1996)]
    for col,label,color in [('propose_new','Propose new',PALETTE['ec']),('improve','Improve',PALETTE['accent']),('hybrid','Hybrid',PALETTE['green'])]:axes[0].plot(z.year,100*z[col]/z.n,label=label,color=color)
    axes[0].set(xlabel='Publication year',ylabel='Share of coded papers (%)');axes[0].legend();letter(axes[0],'a')
    d=read('human_m1_recent').set_index('group').loc[GROUPS[:2]];x=np.arange(2);axes[1].bar(x-.18,d.machine_pct,.34,color=PALETTE['ec'],label='Frozen share');axes[1].errorbar(x+.18,d.human_recent_pct,yerr=np.vstack([d.human_recent_pct-d.lower_pct,d.upper_pct-d.human_recent_pct]),fmt='o',color=PALETTE['accent'],label='Expert-calibrated recent endpoint');axes[1].set_xticks(x,SHORT[:2]);axes[1].set_ylabel('Method-development share, 2021–2025 (%)');axes[1].legend(loc='upper center',bbox_to_anchor=(.5,-.14));letter(axes[1],'b');save(fig,NAMES[9])
    val=pd.read_csv(data/'sampling_penetration.csv');fig,axes=plt.subplots(2,1,figsize=(6.4,7),layout='constrained')
    for j,col in enumerate(['second_label','masked_label']):
        cm=pd.crosstab(val.label,val[col]).reindex(index=LABELS,columns=LABELS,fill_value=0);heat(axes[j],cm,'Second model' if j==0 else 'Venue-masked model');axes[j].set_ylabel('Frozen role label');letter(axes[j],'a' if j==0 else 'b')
    save(fig,NAMES[10]);b=read('missing_text_bounds');fig,axes=plt.subplots(2,1,figsize=(6.4,6.6),layout='constrained')
    for i,r in enumerate(b.itertuples()):axes[0].plot([r.lower_pct,r.upper_pct],[i,i],lw=4,color=PALETTE['ec'])
    axes[0].set_yticks(range(len(b)),b.window);axes[0].set_xlabel('Method-development share bounds (%)');letter(axes[0],'a')
    pilot=read('pilot_deltas');axes[1].barh(pilot.model,pilot.delta_pp,color=PALETTE['all']);axes[1].set_xlabel('Pilot change, 1996–2000 to 2021–2025 (pp)');letter(axes[1],'b');save(fig,NAMES[11])
    (out/'figure_manifest.json').write_text(json.dumps({'figures':NAMES,'minimum_requested_font_pt':8,'output_width_inches':6.4,'claim':'visual QA must inspect final embedded size'},indent=2),encoding='utf-8');print('generated',len(NAMES),'figures')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();produce(a.data,a.out)
