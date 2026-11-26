"""Scenario forecasts use the original trained model directly."""
from concurrent.futures import Future
from pathlib import Path
from .runtime import ROOT

def create(module,runtime):
 folder=runtime.data/'sections'/'scenario-hub';folder.mkdir(parents=True,exist_ok=True)
 rt=module.Runtime(data_dir=folder);rt.model=module.Runtime.__init__.__globals__['NeuralEngine'](rt.model_dir)
 def start():rt.set_state(phase='listening',address='Shared Neural App',model=rt.model.metadata,status={'services':[],'measured_hz':None,'pulse_count':0,'skipped_ticks':0})
 def infer(scenario):
  future=Future()
  try:
   result=rt.model.infer(scenario);result['receipt']=runtime.component_result('scenario-hub',scenario,result);rt.push('inference.result',result);future.set_result(result)
  except Exception as error:future.set_exception(error)
  return future
 rt.start=start;rt.infer=infer;start();return module.App(runtime=rt,autostart=False)
