import test from 'node:test';
import assert from 'node:assert/strict';
import {classifyRuntime, rate, processMetrics} from '../metrics.mjs';
test('recognizes interpreters, excluding unrelated names and the py launcher',()=>{
  for(const name of ['python','python.exe','pythonw.exe','python3.13.exe','pypy3.exe'])assert.equal(classifyRuntime(name),'python');
  for(const name of ['java.exe','javaw','JAVA.EXE'])assert.equal(classifyRuntime(name),'java');
  for(const name of ['javascript.exe','javac.exe','py.exe','python-editor.exe','node.exe'])assert.equal(classifyRuntime(name),null);
});
test('rates are unknown at baseline, handle reset counters, and preserve zero',()=>{
  assert.equal(rate(10,undefined,1),null);assert.equal(rate(null,10,1),null);assert.equal(rate(1,10,1),0);assert.equal(rate(10,10,1),0);assert.equal(rate(100,50,2),25);assert.equal(rate(100,50,0),null);
});
const p={pid:42,name:'python',label:'worker.py',runtime:'python',started:'2026-10-07T10:00:00Z',cpuSeconds:10,memoryBytes:10485760,threads:2,readBytes:200,writeBytes:100};
test('simultaneous Python and Java are measured with CPU normalized across all cores',()=>{
  const before={timestamp:2000,processes:[p,{...p,pid:43,name:'java',runtime:'java',label:'Worker.java'}]};
  const after={timestamp:4000,processes:before.processes.map(p=>({...p,cpuSeconds:14,readBytes:1200,writeBytes:600}))};
  const result=processMetrics(after,before,8);assert.equal(result.length,2);assert.deepEqual(new Set(result.map(p=>p.runtime)),new Set(['python','java']));assert.equal(result[0].cpu,25);assert.equal(result[0].ioRate,750);
});
test('PID reuse never inherits old CPU and IO counters',()=>{
  const result=processMetrics({timestamp:4000,processes:[{...p,started:'2026-10-07T11:00:00Z'}]},{timestamp:2000,processes:[p]},8);assert.equal(result[0].cpu,null);assert.equal(result[0].ioRate,null);
});
test('inaccessible counters stay unknown and new/removed processes are handled',()=>{
  const result=processMetrics({timestamp:4000,processes:[{...p,pid:50,cpuSeconds:null,readBytes:null}]},{timestamp:2000,processes:[p]},8);assert.equal(result.length,1);assert.equal(result[0].pid,50);assert.equal(result[0].cpu,null);assert.equal(result[0].ioRate,null);
});
