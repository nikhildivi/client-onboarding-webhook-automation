"""Synthetic onboarding operations metrics with human escalation recommendations."""
from dataclasses import dataclass
from collections import Counter

@dataclass(frozen=True)
class CaseSnapshot:
    case_id:str
    stage:str
    hours_in_stage:float
    blocked:bool=False
    def __post_init__(self):
        if self.hours_in_stage<0:raise ValueError('Hours cannot be negative')
        if not self.case_id:raise ValueError('case_id required')

def assess_queue(cases:list[CaseSnapshot],sla_hours:float=48.0)->dict:
    if sla_hours<=0:raise ValueError('SLA must be positive')
    flags=[]
    for c in cases:
        if c.stage in ('completed','rejected'):continue
        reasons=[]
        if c.hours_in_stage>sla_hours:reasons.append('sla_exceeded')
        if c.blocked:reasons.append('blocked')
        if reasons:flags.append({'case_id':c.case_id,'reasons':reasons,'recommended_action':'human_follow_up'})
    counts=Counter(c.stage for c in cases)
    return {'total_cases':len(cases),'completed':counts['completed'],
        'completion_rate':round(counts['completed']/len(cases),3) if cases else None,
        'escalations':flags,'mode':'synthetic_review_only'}
