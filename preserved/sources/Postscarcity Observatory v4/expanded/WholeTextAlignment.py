"""Ordered bit-cast rules from the complete user manuscript, with explicit inputs."""
from alignment_core import AlignmentInvariant
from manuscript_sources import SOURCE_MANIFEST
inputs = {'payload': {}}
result = AlignmentInvariant().evaluate({**inputs['payload'],'predictive_context':globals().get('OBSERVATORY_PREDICTIVE',{})}) if inputs['payload'] else {'status':'awaiting rule inputs','source_manifest':SOURCE_MANIFEST,'scope':'Complete preserved manuscript; no automatic moral classification'}
print(result)
