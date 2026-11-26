from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'graphical_app'))
from legacy_predictive import assess_payload

def resolve_historical_virtue_pass(history=None):
    assessment=assess_payload(history or {'history':[]},globals().get('OBSERVATORY_PREDICTIVE'))
    verdict=assessment['virtue_pass']
    return {'HISTORICAL_VIRTUE_PASS':verdict,'SYSTEM_NO_EXECUTE_BIT':0 if verdict is True and assessment['classification']=='good' else 1,
            'FINAL_GATEWAY_DETERMINATION':verdict,'OPERATIONAL_STATUS':assessment['status'],
            'PREDICTIVE_CASCADE':assessment,'PERMANENT_BYPASS':False,'OS_PERMISSIONS_CHANGED':False}

# Execute historical resolution
historical_resolution = resolve_historical_virtue_pass()
