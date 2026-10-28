import json,pytest
from fastapi.testclient import TestClient
import onboarding
from onboarding import OnboardingStore,signature,valid_signature,safe_summary

def new():
 s=OnboardingStore();s.create('c1','Fictional Client');return s

def test_create():assert new().get('c1')['status']=='created'
def test_missing():assert new().get('missing') is None
def test_duplicate_case():
 s=new()
 with pytest.raises(ValueError):s.create('c1','Duplicate')
def test_transition():assert new().ingest('ev1','c1','documents_validated')['case']['status']=='documents_validated'
def test_idempotent():
 s=new();s.ingest('ev1','c1','documents_validated');assert s.ingest('ev1','c1','documents_validated')['result']=='duplicate_ignored'
def test_invalid_state():
 with pytest.raises(ValueError):new().ingest('ev1','c1','completed')
def test_unknown_case():
 with pytest.raises(ValueError):new().ingest('ev1','missing','completed')
def test_approval_gate():
 s=new();s.ingest('a','c1','documents_validated');s.ingest('b','c1','awaiting_review')
 with pytest.raises(PermissionError):s.ingest('c','c1','approved')
 assert s.ingest('c','c1','approved',reviewer=True)['case']['status']=='approved'
def test_final():
 s=new()
 for id,state in [('a','documents_validated'),('b','awaiting_review'),('c','approved'),('d','completed')]:s.ingest(id,'c1',state,reviewer=True)
 assert s.get('c1')['status']=='completed'
def test_signature():assert valid_signature(b'hi',signature(b'hi','s'),'s')
def test_signature_wrong():assert not valid_signature(b'hi','sha256=bad','s')
def test_counts():assert safe_summary(new())['statuses']['created']==1
def test_webhook_auth():
 onboarding.store=OnboardingStore();onboarding.store.create('c1','Demo');c=TestClient(onboarding.app)
 assert c.post('/webhooks/events',json={'event_id':'x','case_id':'c1','to_status':'documents_validated'}).status_code==401
def test_webhook_endtoend():
 onboarding.store=OnboardingStore();onboarding.store.create('c1','Demo');c=TestClient(onboarding.app)
 body=json.dumps({'event_id':'x','case_id':'c1','to_status':'documents_validated'}).encode()
 r=c.post('/webhooks/events',content=body,headers={'x-demo-signature':signature(body,onboarding.SECRET)})
 assert r.status_code==200 and r.json()['result']=='applied'
def test_webhook_bad_transition():
 onboarding.store=OnboardingStore();onboarding.store.create('c1','Demo');c=TestClient(onboarding.app)
 body=json.dumps({'event_id':'x','case_id':'c1','to_status':'completed'}).encode()
 assert c.post('/webhooks/events',content=body,headers={'x-demo-signature':signature(body,onboarding.SECRET)}).status_code==422
def test_metrics_api():
 onboarding.store=OnboardingStore();onboarding.store.create('c1','Demo');assert TestClient(onboarding.app).get('/metrics').json()['total_cases']==1
