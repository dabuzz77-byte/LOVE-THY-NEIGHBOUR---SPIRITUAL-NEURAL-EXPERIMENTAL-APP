export function classifyRuntime(name = '') {
  const base = name.toLowerCase().replace(/\.exe$/, '');
  if (/^javaw?$/.test(base)) return 'java';
  if (/^(pythonw?(?:\d+(?:\.\d+)*)?|pypyw?3?)$/.test(base)) return 'python';
  return null;
}

const valid = value => typeof value === 'number' && Number.isFinite(value);
export function rate(current, previous, seconds) {
  return valid(current) && valid(previous) && seconds > 0 ? Math.max(0, (current - previous) / seconds) : null;
}

export function processMetrics(sample, previous, cores) {
  const seconds = previous ? (sample.timestamp - previous.timestamp) / 1000 : 0;
  const prior = new Map((previous?.processes || []).map(p => [p.pid, p]));
  return sample.processes.filter(p => classifyRuntime(p.name)).map(p => {
    const old = prior.get(p.pid);
    const same = old && old.started === p.started ? old : null;
    const cpuRate = rate(p.cpuSeconds, same?.cpuSeconds, seconds);
    const readRate = rate(p.readBytes, same?.readBytes, seconds);
    const writeRate = rate(p.writeBytes, same?.writeBytes, seconds);
    return {
      pid: p.pid, name: p.name, label: p.label, runtime: classifyRuntime(p.name), started: p.started,
      cpu: cpuRate === null ? null : Math.min(100, cpuRate / Math.max(1, cores) * 100),
      memoryBytes: p.memoryBytes, threads: p.threads,
      readRate, writeRate, ioRate: readRate === null || writeRate === null ? null : readRate + writeRate,
      ageSeconds: p.started ? Math.max(0, (sample.timestamp - Date.parse(p.started)) / 1000) : null
    };
  }).sort((a, b) => (b.cpu || 0) - (a.cpu || 0) || (b.memoryBytes || 0) - (a.memoryBytes || 0));
}
