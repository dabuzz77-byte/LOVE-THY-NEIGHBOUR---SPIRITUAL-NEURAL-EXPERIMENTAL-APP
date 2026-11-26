"""World-grid variant of the supplied local resource accounting engine."""
import math
import secrets
from central_bank_mesh import CentralBankMeshController


class WorldGridCentralBankingCore:
    def __init__(self,core_vortex_key,absolute_commons_pool):
        self.secret=core_vortex_key
        self.controller=CentralBankMeshController(core_vortex_key,absolute_commons_pool)
        self.world_grid_matrix=self.controller.mesh_nodes
        self.passthrough_status='WORLD_GRID_PASSTHROUGH = TRUE'

    @property
    def global_commons_pool_ru(self):return self.controller.global_commons_pool

    @property
    def quarantine_blacklist(self):return self.controller.quarantine_zone

    def onboarding_regional_node(self,sector_id,layer,vram_gb,latency_ms,deception_ratio,initial_ru):
        self.controller.onboard_central_bank_node(sector_id,layer,vram_gb,latency_ms,deception_ratio,initial_ru)
        self.world_grid_matrix[sector_id]['status']='SANCTIFIED_GRID_MEMBER'

    def execute_global_settlement_stream(self,sender_id,receiver_id,payload_value_ru):
        try:signature=self.controller.sign_settlement(sender_id,receiver_id,payload_value_ru)
        except ValueError as error:return {'status':'SETTLEMENT_DENIED','reason':str(error)}
        result=self.controller.process_mesh_settlement(sender_id,receiver_id,payload_value_ru,signature)
        if result['status']=='EVICTED_AND_REBALANCED':
            return {**result,'status':'NODE_QUARANTINED_AND_ASSETS_SHUNTED','evicted_node':result['target']}
        if result['status']=='BLOCKED':return {**result,'status':'SETTLEMENT_DENIED'}
        if result['status']=='SETTLEMENT_MESH_SANCTIFIED':
            result.update(status='GLOBAL_GRID_SETTLEMENT_SANCTIFIED',passthrough_configuration=self.passthrough_status,
                passthrough_basis='Supplied local register declaration',net_transferred_units=result['net_transfer_units'],
                sender_canopy_remainder=result['sender_balance_ru'],receiver_floor_new_total=result['receiver_balance_ru'],
                cryptographic_seal_block=result['cryptographic_seal'].replace('CB-MESH-369:','WORLD-GRID-369:'))
        return result

    def _trigger_world_grid_eviction(self,sector_id,reason):self.controller._evict_node_to_quarantine(sector_id,reason)


INPUT_TEMPLATE={'absolute_commons_pool':1000000000,'nodes':[
    dict(sector_id='london_central_repo_house',layer='CANOPY',vram_gb=144,latency_ms=15,deception_ratio=.1,initial_ru=5000000),
    dict(sector_id='african_child_educational_grid',layer='ROOTS',vram_gb=48,latency_ms=5,deception_ratio=0,initial_ru=10000),
    dict(sector_id='deceptive_speculative_arbitrage_bank',layer='CANOPY',vram_gb=24,latency_ms=180,deception_ratio=15.2,initial_ru=1200000)],
    'settlements':[
        dict(sender_id='deceptive_speculative_arbitrage_bank',receiver_id='london_central_repo_house',payload_value_ru=200000),
        dict(sender_id='london_central_repo_house',receiver_id='african_child_educational_grid',payload_value_ru=1000000)]}


def execute_world_banking(spec,stop_event=None):
    if not isinstance(spec,dict):raise ValueError('world_banking must be an object')
    core=WorldGridCentralBankingCore(secrets.token_bytes(32),spec.get('absolute_commons_pool',0))
    for node in spec.get('nodes',[]):core.onboarding_regional_node(**node)
    before=core.controller.core.snapshot();receipts=[]
    for action in spec.get('settlements',[]):
        if stop_event and stop_event.is_set():raise InterruptedError()
        receipts.append(core.execute_global_settlement_stream(**action))
    after=core.controller.core.snapshot()
    return dict(status='COMPLETE',before=before,after=after,receipts=receipts,
        resource_conserved=math.isclose(before['total_ru'],after['total_ru'],rel_tol=1e-12),
        basis='Local signed resource-unit ledger; node names and world-grid declarations are supplied labels')
