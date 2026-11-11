"""Reproducible standard-library analysis of the user-pasted questionnaire.

Raw 1/2 = positive for five-point questions. All ranks below use 6-raw.
No selection by p-value; declared families appear explicitly in PAIRS.
"""
import csv
import json
import math
import random
import statistics as st
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results'
OUT.mkdir(exist_ok=True)
TEXT = {'Q15_text', 'Q16_text', 'Q21_text', 'Q24_text'}
PERMUTATIONS = 19999
BOOTSTRAPS = 2000
SEED = 20261026
PAIRS = [('Q1','interest')]
PAIRS += [(a,b) for a in ['Q1','Q2','Q3'] for b in ['Q14_1','Q14_2']]
PAIRS += [('interest','int_5'),('interest','int_6')]
PAIRS += [('Q14_10',b) for b in ['int_6','int_7','int_8']]
PAIRS += [('Q13','Q14_1'),('Q13','Q14_2')]
PAIRS += [('Q1','int_5'),('Q1','int_6')]

def read_data():
    with (ROOT/'raw_pasted.tsv').open(encoding='utf-8', newline='') as f:
        rr = list(csv.reader(f, delimiter='\t'))
    header = rr[0]
    assert len(header) == 83 and len(rr)-1 == 155
    assert all(len(r)==83 for r in rr[1:])
    rows = [{k:(v if k in TEXT else int(v) if v else None)
             for k,v in zip(header,r)} for r in rr[1:]]
    assert [r['RespondentID'] for r in rows] == list(range(1,156))
    binary = [k for k in header if k.startswith(('Q4_','Q15_','Q16_','aw_','Q24_')) and k not in TEXT]
    five = [f'Q{i}' for i in range(1,4)] + [f'Q{i}' for i in range(5,14)]
    five += [f'Q14_{i}' for i in range(1,11)] + ['interest'] + [f'int_{i}' for i in range(1,9)]
    ranges = {k:set(range(1,6)) for k in five}
    ranges.update({k:{0,1} for k in binary})
    ranges.update({f'part_{i}':{1,2,3} for i in range(1,8)})
    ranges.update({'Q19':{1,2,3},'Q20':set(range(1,7)), 'Q21':{1,2,3},'Q22':set(range(1,6)),'Q23':set(range(1,6))})
    invalid=[(r['RespondentID'],k,r[k]) for r in rows for k,valid in ranges.items() if r[k] is not None and r[k] not in valid]
    assert not invalid, invalid
    return header, rows, five, binary

def rank(x):
    order=sorted(range(len(x)), key=lambda i:x[i]); out=[0.0]*len(x)
    j=0
    while j<len(order):
        e=j+1
        while e<len(order) and x[order[e]]==x[order[j]]: e+=1
        avg=(j+1+e)/2
        for i in order[j:e]: out[i]=avg
        j=e
    return out

def pearson(x,y):
    mx=st.fmean(x); my=st.fmean(y)
    xx=[v-mx for v in x]; yy=[v-my for v in y]
    den=math.sqrt(sum(v*v for v in xx)*sum(v*v for v in yy))
    return sum(a*b for a,b in zip(xx,yy))/den if den else None

def rho(x,y): return pearson(rank(x), rank(y))

def quantile(x,q):
    z=sorted(x); pos=(len(z)-1)*q; i=int(pos); w=pos-i
    return z[i]*(1-w)+z[min(i+1,len(z)-1)]*w

def holm(results, pkey='p', outkey='p_holm'):
    ix=sorted(range(len(results)), key=lambda i: results[i][pkey]); prev=0
    for j,i in enumerate(ix):
        prev=max(prev, min(1.0,(len(ix)-j)*results[i][pkey]))
        results[i][outkey]=prev

def spearman(x,y, seed):
    n=len(x); observed=rho(x,y); rng=random.Random(seed)
    rx=rank(x); ry=rank(y); mean=(n+1)/2
    xx=[v-mean for v in rx]; yy=[v-mean for v in ry]
    denom=math.sqrt(sum(v*v for v in xx)*sum(v*v for v in yy))
    exceed=0
    for _ in range(PERMUTATIONS):
        rng.shuffle(yy)
        r=sum(a*b for a,b in zip(xx,yy))/denom
        exceed += abs(r)>=abs(observed)-1e-12
    p=(exceed+1)/(PERMUTATIONS+1)
    bs=[]
    for _ in range(BOOTSTRAPS):
        ix=[rng.randrange(n) for j in range(n)]
        val=rho([x[i] for i in ix],[y[i] for i in ix])
        if val is not None: bs.append(val)
    return {'n':n,'rho':observed,'p':p, 'ci_low':quantile(bs,.025), 'ci_high':quantile(bs,.975), 'perm_exceedances':exceed}

def binomial_two_sided_equal(b,c):
    n=b+c
    if n==0:return 1.0
    return min(1.0, 2*sum(math.comb(n,i) for i in range(min(b,c)+1))/2**n)

def paired(rows,a,b):
    complete=[r for r in rows if r[a] is not None and r[b] is not None]
    counts=Counter((r[a]<=2,r[b]<=2) for r in complete)
    aa=counts[(True,True)]; ab=counts[(True,False)]; ba=counts[(False,True)]; bb=counts[(False,False)]
    return {'a':a,'b':b,'n':len(complete),'both_positive':aa,'a_only':ab,'b_only':ba,'neither_positive':bb,
            'a_positive':aa+ab,'b_positive':aa+ba,'difference_pp':100*(ab-ba)/len(complete),
            'p':binomial_two_sided_equal(ab,ba),
            'table_5x5':[[sum(r[a]==i and r[b]==j for r in complete) for j in range(1,6)] for i in range(1,6)]}

def three_cat(v): return 0 if v<=2 else 1 if v==3 else 2

def mannwhitney(a,b,seed):
    na,nb=len(a),len(b); pooled=a+b; ranks=rank(pooled)
    ua=sum(ranks[:na])-na*(na+1)/2
    effect=2*ua/(na*nb)-1
    ties=Counter(pooled); N=na+nb
    variance=na*nb/12*((N+1)-sum(t**3-t for t in ties.values())/(N*(N-1)))
    z=(max(0,abs(ua-na*nb/2)-.5)/math.sqrt(variance)) if variance else 0
    rng=random.Random(seed); expected=na*(N+1)/2; obs=abs(sum(ranks[:na])-expected); exceed=0
    for _ in range(PERMUTATIONS):
        ids=rng.sample(range(N),na)
        exceed+=abs(sum(ranks[i] for i in ids)-expected)>=obs-1e-12
    return {'n1':na,'n0':nb,'U1':ua,'rank_biserial':effect,'median1':st.median(a),'median0':st.median(b),
            'positive1':sum(v>=4 for v in a),'positive0':sum(v>=4 for v in b),
            'p':(exceed+1)/(PERMUTATIONS+1),'p_asymptotic':math.erfc(z/math.sqrt(2))}

def gammaincc(a,x):
    if x==0:return 1.0
    gln=math.lgamma(a); eps=3e-14
    if x<a+1:
        ap=a; total=term=1/a
        for _ in range(10000):
            ap+=1; term*=x/ap; total+=term
            if abs(term)<abs(total)*eps: break
        return max(0,min(1,1-total*math.exp(-x+a*math.log(x)-gln)))
    b=x+1-a; c=1e300; d=1/b; h=d
    for i in range(1,10000):
        an=-i*(i-a); b+=2; d=an*d+b
        if abs(d)<1e-300:d=1e-300
        c=b+an/c
        if abs(c)<1e-300:c=1e-300
        d=1/d; delta=d*c; h*=delta
        if abs(delta-1)<eps:break
    return max(0,min(1,math.exp(-x+a*math.log(x)-gln)*h))

def kw(groups):
    sizes=[len(g) for g in groups]; allv=[v for g in groups for v in g]
    N=len(allv); rr=rank(allv); sums=[]; start=0
    for n in sizes:sums.append(sum(rr[start:start+n]));start+=n
    H=12/(N*(N+1))*sum(s*s/n for s,n in zip(sums,sizes))-3*(N+1)
    corr=1-sum(t**3-t for t in Counter(allv).values())/(N**3-N)
    H/=corr
    return {'H':H,'df':len(groups)-1,'p':gammaincc((len(groups)-1)/2,H/2),'epsilon2':max(0,(H-len(groups)+1)/(N-len(groups))), 'group_n':sizes}

def descriptive(rows, header, five, binary):
    d={}
    for k in header:
        if k in TEXT or k=='RespondentID': continue
        vals=[r[k] for r in rows if r[k] is not None]; c=Counter(vals)
        obj={'n':len(vals),'missing':len(rows)-len(vals),'counts':dict(sorted(c.items()))}
        if k in five:
            obj.update(positive=c[1]+c[2],positive_pct=100*(c[1]+c[2])/len(vals),median=st.median(vals),q1=quantile(vals,.25),q3=quantile(vals,.75))
        d[k]=obj
    return d

def run(label,rows,header,five,binary):
    out={'n':len(rows),'descriptive':descriptive(rows,header,five,binary)}
    out['paired']=[paired(rows,a,b) for a,b in [('Q13','Q14_1'),('Q14_10','int_6'),('Q14_2','Q14_1')]]
    for z in out['paired']:
        z['table_3x3']=[[sum(three_cat(r[z['a']])==i and three_cat(r[z['b']])==j for r in rows) for j in range(3)] for i in range(3)]
    holm(out['paired'])
    corrs=[]
    for i,(a,b) in enumerate(PAIRS):
        complete=[r for r in rows if r[a] is not None and r[b] is not None]
        z=spearman([6-r[a] for r in complete],[6-r[b] for r in complete],SEED+i)
        z.update(a=a,b=b); corrs.append(z)
    holm(corrs); out['correlations']=corrs
    out['experience']=[]
    for i,result in enumerate(['int_5','int_6']):
        g1=[6-r[result] for r in rows if r['part_1']>=2];g0=[6-r[result] for r in rows if r['part_1']==1]
        z=mannwhitney(g1,g0,SEED+100+i);z.update(group='part_1 ever',outcome=result);out['experience'].append(z)
    holm(out['experience'])
    exploratory=[]
    for k in ['Q20','Q22']:
        for y in ['Q1','Q14_1','int_6']:
            levels=sorted({r[k] for r in rows}); groups=[[6-r[y] for r in rows if r[k]==level] for level in levels]
            z=kw(groups);z.update(group=k,outcome=y,levels=levels);exploratory.append(z)
    holm(exploratory);out['attribute_kw']=exploratory
    for y in ['Q1','Q14_1','int_6']:
        for i,k in enumerate(['Q15_5','Q15_6']):
            g1=[6-r[y] for r in rows if r[k]==1];g0=[6-r[y] for r in rows if r[k]==0]
            z=mannwhitney(g1,g0,SEED+200+i);z.update(group=k,outcome=y);exploratory.append(z)
    holm(exploratory);out['exploratory']=exploratory
    out['sample_slices']={
        'Q13_positive_Q14_1_notpositive':[r['RespondentID'] for r in rows if r['Q13']<=2 and r['Q14_1']>=3],
        'Q14_10_positive_int6_notpositive':[r['RespondentID'] for r in rows if r['Q14_10']<=2 and r['int_6']>=3],
        'Q14_10_positive_int6_negative':[r['RespondentID'] for r in rows if r['Q14_10']<=2 and r['int_6']>=4],
        'part1_ever':[r['RespondentID'] for r in rows if r['part_1']>=2],
        'part1_current':[r['RespondentID'] for r in rows if r['part_1']==3],
    }
    (OUT/f'{label}.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    with (OUT/f'{label}_descriptive.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['variable','n','missing','category','count','percent_valid'])
        for k,obj in out['descriptive'].items():
            for val,count in obj['counts'].items():w.writerow([k,obj['n'],obj['missing'],val,count,100*count/obj['n']])
    with (OUT/f'{label}_correlations.csv').open('w',encoding='utf-8-sig',newline='') as f:
        cols=['a','b','n','rho','ci_low','ci_high','p','p_holm'];w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader();w.writerows(corrs)
    print(json.dumps({'label':label,'n':out['n'],'paired':out['paired'],'correlations':corrs,'experience':out['experience'],'attributes':out['exploratory']},ensure_ascii=False),flush=True)
    return out

if __name__=='__main__':
    # Small checks against hand-calculable distributions and identities.
    assert abs(rho([1,2,3],[3,2,1])+1)<1e-12
    assert rank([1,1,3])==[1.5,1.5,3.0]
    assert abs(binomial_two_sided_equal(10,0)-.001953125)<1e-12
    assert abs(gammaincc(1,2)-math.exp(-2))<1e-12
    header,rows,five,binary=read_data()
    keys=[k for k in header if k not in TEXT and k!='RespondentID']
    groups=defaultdict(list)
    for r in rows:groups[tuple(r[k] for k in keys)].append(r['RespondentID'])
    dup=[g for g in groups.values() if len(g)>1]
    keep={g[0] for g in groups.values()}; profiles=[r for r in rows if r['RespondentID'] in keep]
    audit={'rows':155,'columns':83,'duplicate_numeric_profiles':dup,'unique_profiles':len(profiles),
           'missing':{k:sum(r[k] is None for r in rows) for k in keys if any(r[k] is None for r in rows)},
           'parameters':{'permutations':PERMUTATIONS,'bootstraps':BOOTSTRAPS,'seed':SEED,'correlation_family':PAIRS},
           'sha256':hashlib.sha256((ROOT/'raw_pasted.tsv').read_bytes()).hexdigest()}
    (OUT/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    full=run('all155',rows,header,five,binary)
    unique=run('profile139',profiles,header,five,binary)
    # An anonymized numeric table for reproducibility, without residence text.
    with (OUT/'numeric155.csv').open('w',encoding='utf-8-sig',newline='') as f:
        cols=['RespondentID']+keys;w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader();w.writerows(rows)
