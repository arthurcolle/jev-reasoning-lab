import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from jev_lab.advanced import active_fixture,candidates,best_test,oracle_active,revision_events,reduce_events,revision_gold,batch_fixtures

class AdvancedTests(unittest.TestCase):
    def test_active_world_and_budget_reference(self):
        for seed in range(4011,4043):
            f=active_fixture(seed)
            self.assertEqual(len({tuple(x) for x in f['matrix']}),8)
            r=oracle_active(f)
            self.assertLessEqual(r['spent'],f['budget'])
            self.assertIn(f['hidden'],r['remaining'])
            if r['identified']:self.assertEqual(r['remaining'],[f['hidden']])
    def test_versioned_memory_matches_separate_reference(self):
        for seed in range(8101,8113):
            events=revision_events(seed)
            for end in range(1,len(events)+1):
                memory=reduce_events(events[:end]);v=[x['value'] for x in memory.values()]
                status='block' if False in v else 'hold' if None in v else 'proceed'
                self.assertEqual(status,revision_gold(events[:end]))
            self.assertEqual(reduce_events(events[:5]),reduce_events(events[:4]))
    def test_new_batch_cases_have_independent_exact_oracles(self):
        f=batch_fixtures()
        self.assertEqual(len(f),24)
        self.assertEqual(len({x['id'] for x in f}),24)
        self.assertEqual(sum(x['gold']=='yes' for x in f),12)
    def test_exhausted_budget_has_no_permitted_probe(self):
        f=active_fixture(4011)
        self.assertIsNone(best_test(f['matrix'],list(range(8)),f['costs'],0,set()))
        self.assertIsNone(best_test(f['matrix'],list(range(8)),f['costs'],5,set(range(7))))

if __name__=='__main__':unittest.main()
