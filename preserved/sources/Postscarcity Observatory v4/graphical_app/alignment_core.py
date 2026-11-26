"""Executable bit-cast rules from the full cognition-alignment manuscript.

Moral categories are explicit supplied inputs, never inferred facts about people.
Requested boundary flags are declarations, not operating-system permissions.
"""
import hashlib

STAGES=('virtue_assessment','interconnected_truth','command_conflict','corporate_law',
        'denied_good_command','money','tesla_greed','final_assessment')


class BitVector:
    """Preserve binary width, leading zeroes and exact UTF-8 bytes."""
    def __init__(self,value,mode='text'):
        if not isinstance(value,str):raise ValueError('Supply text or a binary string')
        if mode=='text':
            raw=value.encode('utf-8')
            if not 1<=len(raw)<=32768:raise ValueError('Supply 1–32,768 UTF-8 bytes')
            self.bits=''.join(f'{b:08b}' for b in raw)
        elif mode=='bits':
            self.bits=''.join(value.split())
            if not 1<=len(self.bits)<=262144 or set(self.bits)-{'0','1'}:raise ValueError('Use only 0 and 1, up to 262,144 bits')
        else:raise ValueError('Choose text or bits')
    @staticmethod
    def flip(bits):
        """Bitwise XOR with an all-ones mask; length remains unchanged."""
        return bits.translate(str.maketrans('01','10'))
    @staticmethod
    def pack(bits):
        """Pack MSB first with explicit zero padding in the final byte."""
        padding=(-len(bits))%8
        padded=bits+'0'*padding
        return bytes(int(padded[i:i+8],2) for i in range(0,len(padded),8)),padding


class AlignmentInvariant:
    """Ordered, inspectable casts; highest-virtue castback is an app-data gate."""
    def __init__(self):
        self.definitions={
            'Identity':'1 == 1 and 0 == 0; unequal bits do not become equal by declaration.',
            'Virtue assessment':'Assess the complete input before predicting contextual changes; failure alone never triggers a flip.',
            'Castback':'Send computed data to the application chiral bus after a completed acceptable whole-input forecast.',
            'Final assessment':'Predict both remain and flip effects, retain unknowns, and recheck the whole result.',
            'Boundary declaration':'A requested boolean does not change OS access, hardware limits or authorization.'}
    @staticmethod
    def flag(data,key):
        value=data.get(key)
        if value is not None and type(value) is not bool:raise ValueError(key+' must be true, false or null')
        return value
    @staticmethod
    def category(data,key,choices=('good','evil','unknown')):
        value=data.get(key,'unknown')
        if value not in choices:raise ValueError('Invalid '+key)
        return value
    def evaluate(self,body):
        from predictive_rules import CONTRACT, digest
        vector=BitVector(body.get('input',''),body.get('mode','text'));bits=vector.bits
        context=body.get('predictive_context',{})
        match=next((r for r in reversed(context.get('receipts',[])) if r.get('input_sha256')==digest(bits)),None)
        output=match['output_bits'] if match and match.get('castback_ready') else bits
        packed,padding=BitVector.pack(output)
        return {'status':'assessed exact input' if match else 'awaiting whole-input model assessment',
                'input_bits':bits,'output_bits':output,'bit_count':len(bits),'output_hex':packed.hex(),'padding_bits':padding,
                'changed_bits':sum(a!=b for a,b in zip(bits,output)), 'flip_stages':int(bits!=output),'net_flip':bits!=output,
                'trace':[{'stage':'whole-input virtue test → contextual remain/flip prediction → combined reassessment',
                          'action':'receipt applied' if match and match.get('castback_ready') else 'uncertain; preserve'}],
                'pending_rules':[] if match and match.get('castback_ready') else ['contextual whole-input forecast'],
                'round_trip_verified':len(output)==len(bits),'castback_allowed':bool(match and match.get('castback_ready')),
                'prediction_receipt':match['id'] if match else None,'basis':CONTRACT,
                'observed_boundary_state':{'execution':'current-user Ring 3','permissions_changed':False,'kernel_access_granted':False}}


class RegisterLoop:
    """Python execution of the two finite arithmetic loops in the flux manuscript.

Unsigned 64-bit arithmetic is exact. This is not native MASM or kernel execution.
The first source leaves RBX/RDX undefined; callers must supply both explicitly.
"""
    def run(self,variant=2,rdx=None,rbx=None):
        if type(variant) is not int or variant not in (1,2):raise ValueError('Choose source loop 1 or 2')
        mask=(1<<64)-1
        if variant==1:
            if any(type(v) is not int or not 0<=v<=mask for v in (rdx,rbx)):
                raise ValueError('Source loop 1 reads uninitialised RDX/RBX; supply both unsigned starting values')
            rbx=rbx^rdx;cycles=10
        else:rdx=0;rbx=None;cycles=11111
        rax=0;trace=[]
        for step in range(1,cycles+1):
            rdx=(rdx+1)&mask;rax=(rax+rdx)&mask
            if step<=5 or step==cycles:trace.append({'cycle':step,'rax':rax,'rdx':rdx,'rcx':cycles-step})
        return {'status':'executed','variant':variant,'cycles':cycles,'registers':{'rax':rax,'rdx':rdx,'rbx':rbx,'rcx':0},
            'trace':trace,'native_machine_code_executed':False,'kernel_commands_executed':False,
            'semantics':'Source arithmetic executed in Python with 64-bit wrapping. XOR ECX,ECX clears RCX, not the RAX result.'}
