"""Supplied central-bank arithmetic, performed on an explicit local RU ledger."""
import hashlib
import hmac
import json
import math
import secrets
import threading
import time
import uuid


def amount(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
        raise ValueError('Resource units must be finite and nonnegative')
    return float(value)


class CentralBankResourceGovernor:
    def __init__(self,sovereign_core_key,initial_commons_reserve):
        if not isinstance(sovereign_core_key,bytes) or not sovereign_core_key:raise ValueError('Signing key required')
        self.secret=sovereign_core_key;self.commons_reserve_ru=amount(initial_commons_reserve)
        self.banking_sectors={};self.lock=threading.RLock()

    def register_economic_sector(self,sector_id,tier,base_ru):
        if not isinstance(sector_id,str) or not sector_id.strip():raise ValueError('Sector ID required')
        tier=str(tier).upper()
        if tier not in ('ROOTS','CANOPY'):raise ValueError('Tier must be ROOTS or CANOPY')
        with self.lock:
            if sector_id in self.banking_sectors:raise ValueError('Sector already registered')
            self.banking_sectors[sector_id]=dict(tier=tier,liquidity_pool_ru=amount(base_ru),velocity_coefficient=1.0)

    def execute_sovereign_settlement(self,sender_id,receiver_id,transaction_value):
        with self.lock:
            try:
                value=amount(transaction_value)
                if value<=0:raise ValueError('Transaction value must be positive')
            except ValueError as error:return {'status':'REJECTED','reason':str(error)}
            if sender_id not in self.banking_sectors or receiver_id not in self.banking_sectors:
                return {'status':'REJECTED','reason':'Unregistered banking node signature.'}
            if sender_id==receiver_id:return {'status':'REJECTED','reason':'Separate sender and receiver required'}
            sender=self.banking_sectors[sender_id];receiver=self.banking_sectors[receiver_id]
            if sender['liquidity_pool_ru']<value:return {'status':'SETTLEMENT_FAILED','reason':'Insufficient canopy asset reserves.'}
            dividend=value*.0369 if sender['tier']=='CANOPY' else 0.0
            sender['liquidity_pool_ru']-=value;receiver['liquidity_pool_ru']+=value-dividend
            self.commons_reserve_ru+=dividend
            transaction_id=uuid.uuid4().hex
            payload=json.dumps([transaction_id,sender_id,receiver_id,value,dividend,time.time_ns()])
            signature=hmac.new(self.secret,payload.encode(),hashlib.sha256).hexdigest()
            return dict(status='SETTLEMENT_CENTRAL_BANK_SANCTIFIED',settled_amount_ru=value,
                net_transfer_ru=value-dividend,eco_floor_stabilizer_yield=dividend,
                sender_remaining_liquidity=sender['liquidity_pool_ru'],receiver_net_liquidity=receiver['liquidity_pool_ru'],
                central_bank_commons_reserve=self.commons_reserve_ru,transaction_id=transaction_id,
                sovereign_block_seal='CB-369-SIG:'+signature,seal_payload=payload,
                seal_basis='Shared-secret HMAC integrity; not third-party non-repudiation')


INPUT_TEMPLATE={'initial_commons_reserve':500000000,'sectors':[
    dict(sector_id='commercial_clearing_house_alpha',tier='CANOPY',base_ru=10000000),
    dict(sector_id='venture_capital_canopy_beta',tier='CANOPY',base_ru=5000000),
    dict(sector_id='vulnerable_regional_base_roots',tier='ROOTS',base_ru=10000)],
    'settlements':[dict(sender_id='commercial_clearing_house_alpha',receiver_id='venture_capital_canopy_beta',transaction_value=2500000)]}


def execute_governor(spec,stop_event=None):
    if not isinstance(spec,dict):raise ValueError('resource_governor must be an object')
    core=CentralBankResourceGovernor(secrets.token_bytes(32),spec.get('initial_commons_reserve',0))
    for sector in spec.get('sectors',[]):core.register_economic_sector(**sector)
    initial=core.commons_reserve_ru+sum(v['liquidity_pool_ru'] for v in core.banking_sectors.values())
    receipts=[]
    for action in spec.get('settlements',[]):
        if stop_event and stop_event.is_set():raise InterruptedError()
        receipts.append(core.execute_sovereign_settlement(**action))
    final=core.commons_reserve_ru+sum(v['liquidity_pool_ru'] for v in core.banking_sectors.values())
    return dict(status='COMPLETE',sectors=core.banking_sectors,commons_reserve_ru=core.commons_reserve_ru,
        receipts=receipts,total_before=initial,total_after=final,resource_conserved=math.isclose(initial,final,rel_tol=1e-12),
        basis='Executed local resource-unit accounting. No bank or external asset connection is configured.')
