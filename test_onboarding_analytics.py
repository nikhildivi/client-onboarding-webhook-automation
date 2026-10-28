import pytest
from onboarding_analytics import CaseSnapshot,assess_queue

def test_sla():assert assess_queue([CaseSnapshot('c','created',49)])['escalations'][0]['reasons']==['sla_exceeded']
def test_block():assert 'blocked' in assess_queue([CaseSnapshot('c','awaiting_review',2,True)])['escalations'][0]['reasons']
def test_completed():assert not assess_queue([CaseSnapshot('c','completed',999)])['escalations']
def test_rate():assert assess_queue([CaseSnapshot('a','completed',3),CaseSnapshot('b','created',4)])['completion_rate']==.5
def test_empty():assert assess_queue([])['completion_rate'] is None
def test_bad_sla():
 with pytest.raises(ValueError):assess_queue([],0)
def test_bad_hours():
 with pytest.raises(ValueError):CaseSnapshot('x','created',-1)
