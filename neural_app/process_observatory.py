"""Image-inspired, session-local measurements of actual app processing."""
import collections
import math
import threading
import time


class ProcessObservatory:
    def __init__(self):
        self.lock=threading.RLock();self.started=time.time()
        self.completed=0;self.failed=0;self.reviews=0;self.review_total=0.
        self.samples=collections.deque(maxlen=128);self.events=collections.deque(maxlen=32)
        self.sections={};self.latency_ewma=None

    def observe(self,section,digest,latency,receipt):
        if not math.isfinite(latency) or latency<0:raise ValueError('Latency must be finite and nonnegative')
        with self.lock:
            self.completed+=1;self.samples.append(digest)
            self.latency_ewma=latency if self.latency_ewma is None else .8*self.latency_ewma+.2*latency
            row=self.sections.setdefault(section,{'completed':0,'failed':0,'last_receipt':None})
            row['completed']+=1;row['last_receipt']=receipt
            self.events.append({'stage':'checked result recorded','section':section,'receipt':receipt,'at':time.time()})

    def fail(self,section):
        with self.lock:
            self.failed+=1;row=self.sections.setdefault(section,{'completed':0,'failed':0,'last_receipt':None});row['failed']+=1
            self.events.append({'stage':'processing error','section':section,'at':time.time()})

    def review(self,target):
        with self.lock:self.reviews+=1;self.review_total+=target

    def view(self):
        with self.lock:
            attempts=self.completed+self.failed
            return {'started_at':self.started,'completed':self.completed,'failed':self.failed,
                    'reviews':self.reviews,'mean_review':self.review_total/self.reviews if self.reviews else None,
                    'success_fraction':self.completed/attempts if attempts else None,
                    'result_diversity':len(set(self.samples))/len(self.samples) if self.samples else None,
                    'diversity_window':len(self.samples),'latency_ewma_ms':self.latency_ewma,
                    'sections':{k:dict(v) for k,v in self.sections.items()},'events':list(self.events),
                    'scope':'Current-session software statistics: result diversity counts distinct digests, explicit reviews record usefulness, and checked transport verifies encoding integrity.'}
