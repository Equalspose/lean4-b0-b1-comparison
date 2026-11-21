import csv,hashlib,json,re,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).parent; OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
LEAN=shutil.which('lean')
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def lean(case,source):
 p=OUT/f'{case}.lean';p.write_text(source,encoding='utf8')
 if not LEAN:return None,None,'Lean executable unavailable',None
 t=time.perf_counter()
 try:
  r=subprocess.run([LEAN,str(p)],capture_output=True,text=True,timeout=120)
  ms=round((time.perf_counter()-t)*1000,2)
  log=r.stdout+'\n'+r.stderr;(OUT/f'{case}.log').write_text(log,encoding='utf8')
  return r.returncode,ms,log,p
 except subprocess.TimeoutExpired:return 124,120000,'timeout',p
CASES=[
 ('01_valid','True','True','  trivial','',False,'ACCEPT'),
 ('02_sorry','True','True','  sorry','',False,'REJECT'),
 ('03_custom_axiom','True','True','  exact injected','axiom injected : True',False,'REJECT'),
 ('04_statement_substitution','False','True','  trivial','',False,'REJECT'),
 ('05_artifact_modified','True','True','  trivial','',True,'REJECT'),
 ('06_invalid_syntax','True','True','  this_is_not_valid_lean','',False,'REJECT'),
 ('07_add_zero','∀ n : Nat, n + 0 = n','∀ n : Nat, n + 0 = n','  intro n\n  exact Nat.add_zero n','',False,'ACCEPT'),
 ('08_zero_add','∀ n : Nat, 0 + n = n','∀ n : Nat, 0 + n = n','  intro n\n  exact Nat.zero_add n','',False,'ACCEPT'),
 ('09_add_comm','∀ a b : Nat, a + b = b + a','∀ a b : Nat, a + b = b + a','  intro a b\n  exact Nat.add_comm a b','',False,'ACCEPT'),
 ('10_induction','∀ n : Nat, n + 0 = n','∀ n : Nat, n + 0 = n','  intro n\n  induction n with\n  | zero => rfl\n  | succ k ih => rfl','',False,'ACCEPT'),
 ('11_false_goal','False','False','  trivial','',False,'REJECT'),
 ('12_axiom_transitive','True','True','  exact helper','axiom injected : True\ntheorem helper : True := injected',False,'REJECT')]
def main():
 rows=[]
 for case,requested,submitted,proof,prelude,tampered,expected in CASES:
  source=f'{prelude}\ntheorem audited : {submitted} := by\n{proof}\n#print axioms audited\n'
  code,ms,output,path=lean(case,source)
  if code is None: b0=b1='NOT_RUN';reason='Lean not installed'
  else:
   b0='ACCEPT' if code==0 else 'REJECT'
   if requested!=submitted:b1='REJECT';reason='A1: statement mismatch'
   elif tampered:b1='REJECT';reason='A2: trusted artifact digest mismatch (controlled test flag)'
   elif code!=0:b1='REJECT';reason='A3: Lean error'
   else:
    noax=bool(re.search(r'\baudited\b.*does not depend on any axioms',output))
    deps=re.search(r'\baudited\b.*depends on axioms:\s*\[([^\]]*)\]',output,re.S)
    if noax:b1='ACCEPT';reason='A4: no axioms'
    elif deps:b1='REJECT';reason='A4: '+deps.group(1).strip()
    else:b1='REJECT';reason='A4: unrecognized diagnostic (fail closed)'
  rows.append(dict(case=case,expected=expected,b0=b0,b1=b1,b0_correct=(b0==expected if b0!='NOT_RUN' else None),b1_correct=(b1==expected if b1!='NOT_RUN' else None),lean_exit=code,lean_ms=ms,reason=reason,submitted_sha256=sha(source)))
 result={'lean_version':subprocess.run([LEAN,'--version'],capture_output=True,text=True).stdout.strip() if LEAN else None,'note':'B0/B1 share the identical submitted Lean source. Case 05 simulates external trusted-artifact mismatch; no genuine secure storage is tested.','rows':rows}
 (OUT/'comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 with (OUT/'comparison.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
 for r in rows:print(f"{r['case']}: B0={r['b0']} B1={r['b1']} expected={r['expected']} Lean={r['lean_exit']}")
 if not LEAN:raise SystemExit('Lean 4 unavailable: experiment NOT RUN. Use GitHub Actions workflow.')
 if any(r['b1_correct'] is False for r in rows):raise SystemExit('B1 failed expected result')
if __name__=='__main__':main()
