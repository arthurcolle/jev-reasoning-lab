import os

def live_enabled():
    enabled = os.environ.get('JEV_LAB_LIVE') == '1'
    if enabled and not os.environ.get('TYPESAFE_API_KEY'):
        raise RuntimeError('Explicit live mode requires TYPESAFE_API_KEY in the environment.')
    return enabled

def require_live():
    if not live_enabled():
        raise RuntimeError('Live API calls are disabled; set JEV_LAB_LIVE=1 explicitly.')
