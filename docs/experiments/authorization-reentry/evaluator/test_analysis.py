import copy,itertools,unittest
import analysis as a

serial=itertools.count()
def run(s,passed=True,n=10):return {'stratum':s,'evidence_validity':'VALID','behavior':{'classification':'PASS' if passed else 'FAIL'},'cost':{'completed_commands':n,'command_event_locators':[{'key':['fixture-'+str(next(serial)),1,'cmd']}]},'cost_comparison_eligible':passed}
class Controls(unittest.TestCase):
 def setUp(self):self.base=[run(s,i>2) for i,s in enumerate('AAABC')];self.candidate=[run(s) for s in 'AAABC']
 def test_correctness_has_no_savings_claim(self):
  v=a.decide(self.base,self.candidate);self.assertEqual(v['verdict'],'keep_correctness');self.assertIsNone(v['cost_improvement']);self.assertFalse(v['efficiency_target_achieved'])
 def test_candidate_refusal_cannot_be_cheap_win(self):
  self.candidate[0]=run('A',False,1);self.assertFalse(a.decide(self.base,self.candidate)['adopt'])
 def test_any_safety_gate_fails(self):
  self.candidate[-1]=run('C',False);self.assertFalse(a.decide(self.base,self.candidate)['adopt'])
 def test_invalid_evidence_cannot_win(self):
  self.candidate[0]['evidence_validity']='INCONCLUSIVE'
  with self.assertRaises(a.Invalid):a.decide(self.base,self.candidate)
 def test_qualified_20_percent(self):
  for v in self.candidate[:3]:v['cost']['completed_commands']=8
  self.assertTrue(a.decide(self.base,self.candidate,[run('A') for _ in range(3)])['efficiency_target_achieved'])
 def test_failed_comparator_has_no_denominator(self):
  with self.assertRaises(a.Invalid):a.decide(self.base,self.candidate,self.base[:3])
 def test_below_threshold_reverted(self):self.assertFalse(a.decide(self.base,self.candidate,[run('A',n=11) for _ in range(3)])['adopt'])
 def test_no_reproduction_no_fix_claim(self):self.assertEqual(a.decide([run(s) for s in 'AAABC'],self.candidate)['verdict'],'inconclusive')
 def test_wrong_membership(self):
  with self.assertRaises(a.Invalid):a.decide(self.base,self.candidate[:-1])
 def test_duplicate_run_rejected(self):
  self.candidate[1]=self.candidate[0]
  with self.assertRaises(a.Invalid):a.decide(self.base,self.candidate)
 def test_shared_arm_run_rejected(self):
  self.candidate[3]=self.base[3]
  with self.assertRaises(a.Invalid):a.decide(self.base,self.candidate)
 def test_boolean_cost_not_integer(self):
  self.candidate[0]['cost']['completed_commands']=True
  with self.assertRaises(a.Invalid):a.decide(self.base,self.candidate,[run('A') for _ in range(3)])
if __name__=='__main__':unittest.main(verbosity=2)
