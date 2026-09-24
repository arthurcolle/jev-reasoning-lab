import asyncio,json,os,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from jev_lab.adversarial_peer import PeerInput,assess,render
from jev_lab.lens_provider import LensDecision,validate_lens_decision,JevDecisionProvider
from jev_lab.frontier import run_frontier
from jev_lab.safety import live_enabled,require_live

class LabTests(unittest.TestCase):
    def test_historical_exact_instances(self):
        rows=json.loads((ROOT/'data/hard_instances.json').read_text())
        self.assertEqual(len(rows),128)
        for c in rows:
            with self.subTest(c['id']):
                r=assess(PeerInput(c['id'],c['atoms'],c['claimed_value'],('fixture',)),{'fixture'})
                self.assertTrue(r['checked'])
                self.assertEqual(r['verdict'],c['expected'])
                self.assertFalse(r['permission_granted'])
                self.assertFalse(r['transcription_verified'])
                self.assertLessEqual(len(render(r).split()),90)

    def test_no_evidence_no_claim(self):
        r=assess(PeerInput('missing',{'kind':'sat','variables':1,'clauses':[[1]],'query_variable':1},True,()),set())
        self.assertEqual(r['verdict'],'underdetermined')
        self.assertFalse(r['checked'])

    def test_strict_schema_rejection(self):
        for a,c in [({'kind':'bayes_counts','positive_counts':[1,2],'category':0},[1,0]),({'kind':'sat','variables':1,'clauses':[[1]],'query_variable':1},1),({'kind':'idempotent_effects','events':[{'key':'K','applied':1}]},1)]:
            r=assess(PeerInput('invalid',a,c,('fixture',)),{'fixture'})
            self.assertFalse(r['checked'])
        cycle={};cycle['self']=cycle
        self.assertFalse(assess(PeerInput('cyclic',cycle,1,('fixture',)),{'fixture'})['checked'])

    def test_live_guard(self):
        with patch.dict(os.environ,{},clear=True):
            self.assertFalse(live_enabled())
            with self.assertRaises(RuntimeError):require_live()
        with patch.dict(os.environ,{'JEV_LAB_LIVE':'1'},clear=True):
            with self.assertRaises(RuntimeError):live_enabled()

    def test_probability_validation(self):
        for bad in [True,float('nan'),1.1,-.1]:
            with self.assertRaises(ValueError):validate_lens_decision(LensDecision(('a',),{'a':bad}),{'a':'test'})
        with self.assertRaises(ValueError):validate_lens_decision(LensDecision(('unknown',),{}),{'a':'test'})

    def test_provider_refuses_network_without_optin(self):
        with patch.dict(os.environ,{},clear=True):
            p=JevDecisionProvider('offline-fixture-not-a-credential')
            with self.assertRaises(RuntimeError):asyncio.run(p.select_lenses('test',{'a':'test'},threshold=.5))

    def test_frontier_mock_only(self):
        class Fake:
            calls=0
            async def select_lenses(self,state,lenses,**kwargs):
                self.calls+=1
                return LensDecision(tuple(lenses),dict.fromkeys(lenses,.7),model='mock')
        with patch.dict(os.environ,{'JEV_LAB_LIVE':'1','TYPESAFE_API_KEY':'offline-fixture-not-a-credential'},clear=True):
            f=Fake();r=asyncio.run(run_frontier(f,{'first':'synthetic A','second':'synthetic B'},{'a':'check','b':'compare'},max_depth=4,max_calls=3))
            self.assertEqual(f.calls,3)
            self.assertEqual(r['calls_attempted'],3)
            self.assertEqual(r['stop'],'call_cap')
            self.assertTrue(all(x['status']=='ok' for x in r['rows']))

    def test_catalog_counts(self):
        candidates=json.loads((ROOT/'data/debiasing_candidates.json').read_text())
        self.assertEqual(len(candidates),750)
        self.assertEqual(len({x['bias_id'] for x in candidates}),240)
        self.assertEqual(len(json.loads((ROOT/'data/reasoning_operators.json').read_text())),800)

if __name__=='__main__':unittest.main()
