"""Small, bounded numeric-state branching demo; not hidden-state recursion."""
import asyncio
import json
from .safety import require_live
from .lens_provider import validate_lens_decision

async def run_frontier(provider, seeds, lenses, *, max_depth=6, max_calls=24,
                       concurrency=2, frontier_width=4):
    require_live()
    if not (1 <= max_depth <= 64 and 1 <= max_calls <= 128 and
            1 <= concurrency <= 8 and 1 <= frontier_width <= 16):
        raise ValueError('Experiment limits outside supported bounds')
    if not seeds or len(seeds) > frontier_width or not lenses or len(lenses) > 32:
        raise ValueError('Supply a bounded nonempty seed set and lens catalogue')
    if any(not isinstance(s,str) or not s.strip() or len(s)>2048 for s in seeds.values()):
        raise ValueError('Seeds must be bounded nonempty strings')
    names=list(lenses)
    frontier=[{'root':name,'state':text,'parent':None,'depth':0,'pivot':-1}
              for name,text in seeds.items()]
    sem=asyncio.Semaphore(concurrency)
    rows=[];seen=set();merges=pruned=0;stop='frontier_exhausted'
    async def evaluate(job,ident):
        async with sem:
            try:
                d=await provider.select_lenses(job['state'],lenses,threshold=0.5,max_lenses=len(lenses))
                d=validate_lens_decision(d,lenses,max_lenses=len(lenses))
                if set(d.probabilities)!=set(names):
                    raise ValueError('Incomplete probability vector')
                vector=[d.probabilities[n] for n in names]
                return {'id':ident,**job,'status':'ok','vector':vector,'model':d.model}
            except Exception as error:
                # Do not expose provider objects, authorization headers or secrets.
                return {'id':ident,**job,'status':'error','error_type':type(error).__name__}
    while frontier:
        remaining=max_calls-len(rows)
        if remaining<=0:stop='call_cap';break
        batch=frontier[:min(frontier_width,remaining)]
        completed=await asyncio.gather(*(evaluate(job,len(rows)+i) for i,job in enumerate(batch)))
        rows.extend(completed)
        if any(row['status']!='ok' for row in completed):
            stop='error_no_retry';break
        next_frontier=[]
        for row in completed:
            if row['depth']+1>=max_depth:continue
            vector=row['vector']
            choices=sorted((i for i,v in enumerate(vector) if v>=.5),key=lambda i:(-vector[i],i))[:2]
            for pivot in choices:
                fingerprint=(tuple(round(v/.05) for v in vector),pivot)
                if fingerprint in seen:merges+=1;continue
                seen.add(fingerprint)
                next_frontier.append({'root':row['root'],'state':json.dumps(vector+[pivot]),
                                      'parent':row['id'],'depth':row['depth']+1,'pivot':pivot})
        pruned+=max(0,len(next_frontier)-frontier_width)
        frontier=next_frontier[:frontier_width]
        if not frontier and any(r['depth']+1>=max_depth for r in completed):stop='depth_cap'
    if len(rows)>=max_calls:stop='call_cap'
    return {'calls_attempted':len(rows),'max_depth_observed':max((r['depth'] for r in rows),default=0),
            'stop':stop,'merged_states':merges,'beam_pruned':pruned,'rows':rows,
            'token_cost_usd':None,'notes':'No generated prose between calls; numeric states still use the typed API. Quantized merges and caps are host rules, not proof of reasoning convergence. This smaller portable demo is not a replay of the historical run.'}
