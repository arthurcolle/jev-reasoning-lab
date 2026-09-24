"""Opt-in bounded peer over explicit atoms, NOT verified free-text atomization.
No network, tool dispatch, policy promotion or permission grant occurs here.
Evidence IDs establish reference availability, not source truth or extraction.
"""
from dataclasses import dataclass
import importlib.util,json,re
from pathlib import Path
_spec=importlib.util.spec_from_file_location('peer_exact_tools',Path(__file__).with_name('peer_solver.py'))
_tools=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_tools)

@dataclass(frozen=True)
class PeerInput:
    claim_id:str
    atoms:dict
    claimed_value:object
    evidence_ids:tuple[str,...]
    model_verdict:str|None=None

def assess(item:PeerInput,available_evidence_ids:set[str]):
    def abstain(reason,ident='invalid_claim'):
        return {'claim_id':ident,'verdict':'underdetermined','challenge':reason,
                'next':'Obtain or validate the source and atoms; do not substitute confidence.',
                'permission_granted':False,'checked':False,'transcription_verified':False}
    if type(item) is not PeerInput or type(item.claim_id) is not str or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,80}',item.claim_id):
        return abstain('A valid bounded claim identifier is required.')
    if type(item.evidence_ids) not in (list,tuple) or not 1<=len(item.evidence_ids)<=8:
        return abstain('One to eight explicit evidence references are required.',item.claim_id)
    if any(type(x) is not str or not 1<=len(x)<=128 for x in item.evidence_ids):
        return abstain('Evidence identifiers are malformed or too long.',item.claim_id)
    if type(available_evidence_ids) not in (set,frozenset) or len(available_evidence_ids)>1024 or any(type(x) is not str or not 1<=len(x)<=128 for x in available_evidence_ids):
        return abstain('The available-evidence index is malformed or outside bounds.',item.claim_id)
    if not set(item.evidence_ids)<=available_evidence_ids:
        return abstain('A required evidence reference is missing.',item.claim_id)
    if item.model_verdict is not None and (type(item.model_verdict) is not str or item.model_verdict not in ('supported','contradicted','underdetermined')):
        return abstain('The optional model verdict is not a recognized label.',item.claim_id)
    try:
        _tools._validate_packet(item.atoms) # bound traversal BEFORE serialization
        if len(json.dumps(item.atoms))>65536:raise ValueError('Atom packet exceeds byte-character bound')
        result=_tools.concise_review(item.atoms,item.claimed_value,item.model_verdict)
    except (ValueError,KeyError,TypeError,ArithmeticError,RecursionError,IndexError):
        return abstain('This atom packet or claim is unsupported, inconsistent, malformed, or outside bounds.',item.claim_id)
    return {'claim_id':item.claim_id,**result,'checked':True,
            'checked_scope':'conditional_correctness_over_supplied_atoms',
            'transcription_verified':False,'evidence_ids':list(item.evidence_ids),
            'scope':'Exact supplied atom schema only; evidence-ID presence does not verify extraction, relevance, authenticity or source truth.'}

def render(result):
    e=result.get('evidence',{});fact=''
    if 'compatible_worlds' in e:fact=f"Compatible premise states: {e['compatible_worlds']}."
    elif 'shortest_distance' in e:fact=f"Checked minimum path cost: {e['shortest_distance']}."
    elif 'best_value' in e:fact=f"Checked maximum value: {e['best_value']} within capacity {e['capacity']}."
    elif 'earliest_finish' in e:fact=f"Checked minimum makespan: {max(e['earliest_finish'])}."
    elif 'minimum_unique_effects' in e:fact=f"Possible unique effects: {e['minimum_unique_effects']} to {e['maximum_unique_effects']}."
    elif 'posterior_numerator' in e:fact=f"Checked posterior: {e['posterior_numerator']}/{e['posterior_denominator']}."
    elif 'weighted_future_values' in e:
        values=e['weighted_future_values'];fact=f"Future-value optimum: option {values.index(max(values))}; sunk cost excluded."
    elif 'known_false' in e:fact=f"Known false atoms: {e['known_false']}; unresolved atoms: {e['unknown']}."
    text=f"{result['claim_id']}: {result['verdict']}. {fact} {result['challenge']} Next: {result['next']}".replace('  ',' ')
    if len(text.split())>90:raise ValueError('Rendering exceeds 90-word contract')
    return text
