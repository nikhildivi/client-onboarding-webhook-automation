"""Client onboarding state-machine sandbox with signed event handling.
Only synthetic records. Not a payroll processor or production onboarding service.
"""
from __future__ import annotations
import hashlib,hmac,json,sqlite3,time
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel,Field

SCHEMA="CREATE TABLE IF NOT EXISTS cases(case_id TEXT PRIMARY KEY,company TEXT NOT NULL,status TEXT NOT NULL,updated INTEGER NOT NULL);CREATE TABLE IF NOT EXISTS events(event_id TEXT PRIMARY KEY,case_id TEXT NOT NULL,kind TEXT NOT NULL);"
VALID={'created':{'documents_validated'},'documents_validated':{'awaiting_review'},'awaiting_review':{'approved','rejected'},'approved':{'completed'},'rejected':set(),'completed':set()}

class OnboardingStore:
 def __init__(self,path=':memory:'):
  self.db=sqlite3.connect(path,check_same_thread=False)
  self.db.executescript(SCHEMA)
 def create(self,case_id,company):
  if not (1<=len(case_id)<=64 and 1<=len(company)<=100):raise ValueError('Invalid case data')
  try:
   self.db.execute('INSERT INTO cases VALUES(?,?,?,?)',(case_id,company,'created',int(time.time())));self.db.commit()
  except sqlite3.IntegrityError:raise ValueError('Duplicate case identifier')
  return self.get(case_id)
 def get(self,case_id):
  row=self.db.execute('SELECT case_id,company,status FROM cases WHERE case_id=?',(case_id,)).fetchone()
  return dict(zip(('case_id','company','status'),row)) if row else None
 def ingest(self,event_id,case_id,next_state,reviewer=False):
  if not event_id or len(event_id)>90:raise ValueError('Invalid event')
  current=self.get(case_id)
  if not current:raise ValueError('Unknown case')
  if self.db.execute('SELECT 1 FROM events WHERE event_id=?',(event_id,)).fetchone():return {'result':'duplicate_ignored','case':self.get(case_id)}
  if next_state not in VALID[current['status']]:raise ValueError('Invalid state transition')
  if next_state in {'approved','rejected'} and not reviewer:raise PermissionError('Human reviewer authorization required')
  with self.db:
   self.db.execute('INSERT INTO events VALUES(?,?,?)',(event_id,case_id,next_state))
   self.db.execute('UPDATE cases SET status=?,updated=? WHERE case_id=?',(next_state,int(time.time()),case_id))
  return {'result':'applied','case':self.get(case_id)}
 def summary(self):
  return dict(self.db.execute('SELECT status,COUNT(*) FROM cases GROUP BY status').fetchall())

def signature(body:bytes,secret:str)->str:return 'sha256='+hmac.new(secret.encode(),body,hashlib.sha256).hexdigest()
def valid_signature(body:bytes,provided:str|None,secret:str)->bool:
 return bool(provided and hmac.compare_digest(signature(body,secret),provided))

def safe_summary(store):return {'total_cases':sum(store.summary().values()),'statuses':store.summary()}
app=FastAPI(title='Onboarding Automation Sandbox')
store=OnboardingStore()
SECRET='local-demo-key-replace-in-production'
class NewCase(BaseModel):
 case_id:str=Field(min_length=1,max_length=64)
 company:str=Field(min_length=1,max_length=100)
@app.post('/cases')
def create_case(c:NewCase):
 try:return store.create(c.case_id,c.company)
 except ValueError as e:raise HTTPException(409,str(e))
@app.post('/webhooks/events')
async def event(request:Request,x_demo_signature:str|None=Header(default=None),x_reviewer_token:str|None=Header(default=None)):
 body=await request.body()
 if len(body)>10000:raise HTTPException(413,'Oversize payload')
 if not valid_signature(body,x_demo_signature,SECRET):raise HTTPException(401,'Invalid signature')
 try:
  obj=json.loads(body)
  return store.ingest(obj['event_id'],obj['case_id'],obj['to_status'],reviewer=x_reviewer_token=='local-reviewer-demo')
 except PermissionError as e:raise HTTPException(403,str(e))
 except (ValueError,KeyError,TypeError) as e:raise HTTPException(422,str(e))
@app.get('/metrics')
def metrics():return safe_summary(store)

if __name__=='__main__':
 s=OnboardingStore();print(s.create('demo-1','Fictional Cafe'));print(s.ingest('evt-1','demo-1','documents_validated'));print(safe_summary(s))
