import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
let cached = null, pending = null;

export async function scanProcesses() {
  if (cached && Date.now() - cached.checkedAt < 4000) return cached;
  if (pending) return pending;
  pending = (async () => {
    try {
      if (process.platform !== 'win32') throw new Error('This process monitor is configured for Windows.');
      const script = `$ErrorActionPreference='Stop'; $items = @(Get-CimInstance Win32_Process -Filter "Name LIKE 'python%' OR Name LIKE 'java%' OR Name = 'py.exe' OR Name LIKE 'pypy%'" | ForEach-Object { $source = ''; if ($_.CommandLine -match '(?:"([^"\\r\\n]+\\.(?:py|pyw|java|jar))"|([^\\s"]+\\.(?:py|pyw|java|jar)))') { $source = [IO.Path]::GetFileName(($Matches[1] + $Matches[2])) }; [PSCustomObject]@{pid=[int]$_.ProcessId; name=$_.Name; source=$source; memoryMB=[math]::Round([double]$_.WorkingSetSize / 1MB, 1); language= $(if ($_.Name -like 'java*') {'java'} else {'python'})} }); ConvertTo-Json -InputObject $items -Compress`;
      let stdout;
      try { ({ stdout } = await exec('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', script], { windowsHide: true, timeout: 8000, maxBuffer: 2 * 1024 * 1024 })); }
      catch {
        const fallback = `$ErrorActionPreference='Stop'; $items = @(Get-Process | Where-Object { $_.ProcessName -match '^(python(?:w|[0-9.]+)?|javaw?|py|pypy[0-9.]*)$' } | ForEach-Object { [PSCustomObject]@{pid=$_.Id; name=$_.ProcessName; source=''; memoryMB=[math]::Round($_.WorkingSet64 / 1MB,1); language=$(if ($_.ProcessName -like 'java*') {'java'} else {'python'})} }); ConvertTo-Json -InputObject $items -Compress`;
        ({ stdout } = await exec('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', fallback], { windowsHide: true, timeout: 4000, maxBuffer: 2 * 1024 * 1024 }));
      }
      const parsed = JSON.parse(stdout.replace(/^\uFEFF/, '').trim() || '[]');
      cached = { checkedAt: Date.now(), processes: Array.isArray(parsed) ? parsed : [parsed], error: null };
    } catch (e) {
      cached = { checkedAt: Date.now(), processes: [], error: 'Windows process discovery is unavailable. Connected programs still appear below.' };
    } finally { pending = null; }
    return cached;
  })();
  return pending;
}
