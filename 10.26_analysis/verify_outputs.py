"""Final consistency audit of generated deliverables; no source-file discovery."""
import ast
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
for name in ['analyze.py','finalize.py','report.py']:
    ast.parse((ROOT/name).read_text(encoding='utf-8'))
for stem in ['all155','profile139']:
    d=json.loads((ROOT/'results'/f'{stem}.json').read_text(encoding='utf-8'))
    n=d['n']
    assert all(sum(x['counts'].values())==x['n'] and x['n']+x['missing']==n for x in d['descriptive'].values())
    for z in d['paired']:
        assert sum(map(sum,z['table_5x5']))==n
        assert sum(map(sum,z['table_3x3']))==n
        assert abs(z['difference_pp']-(z['a_positive']-z['b_positive'])*100/n)<1e-10
    assert len(d['correlations'])==16 and len(d['exploratory'])==12
    print(stem, 'frequency totals, paired totals and test counts checked')
files=['10.26要旨修改版 txt.txt','10.26教授13条意见修改对照.txt','10.26第三篇问卷分析步骤.txt','10.26第三篇155份问卷统计结果与分析说明.txt']
for name in files:
    t=(BASE/name).read_text(encoding='utf-8-sig')
    assert '\ufffd' not in t
    assert 'POLICY_TABLE' not in t and 'INTENTION_TABLE' not in t
    print(name, len(t), 'characters')
t=(BASE/files[0]).read_text(encoding='utf-8-sig')
assert len(re.findall(r'^第[1-7]章　',t,re.M))==7
assert all(f'（{i}）' in (BASE/files[1]).read_text(encoding='utf-8-sig') for i in range(1,14))
assert '分析は執筆中' not in t
assert '生物多様性の保全は、近年「自然を守る」段階から「自然を回復させる」段階へと移りつつある。' in t
assert '共同管理方針への賛成69.0％' in t
assert '139件' in t and '原票' in t
print('Seven chapters, all 13 comment mappings and actual result integration checked')
