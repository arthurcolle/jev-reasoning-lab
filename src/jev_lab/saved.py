"""Replay captured outputs without invoking a model or a fleet."""
import json,sys
from pathlib import Path

def replay(key):
    root=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'data/saved_outputs.json').exists())
    record=json.loads((root/'data/saved_outputs.json').read_text())[key]
    print('[Historical replay] '+record['description'])
    for output in record['outputs']:
        kind=output['output_type']
        if kind=='stream':
            text=output.get('text','')
            if isinstance(text,list):text=''.join(text)
            print(text,end='',file=sys.stderr if output.get('name')=='stderr' else sys.stdout)
        elif kind in ('display_data','execute_result'):
            from IPython.display import display
            display(output['data'],raw=True)
        elif kind=='error':
            print('Saved error: '+output.get('ename','')+': '+output.get('evalue',''))
