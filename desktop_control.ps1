param()
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class NexusWindow {
 [StructLayout(LayoutKind.Sequential)] public struct Point { public int X; public int Y; public Point(int x,int y){X=x;Y=y;} }
 public delegate bool EnumProc(IntPtr h,IntPtr l);
 [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc callback,IntPtr l);
 [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h,System.Text.StringBuilder text,int count);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr h,System.Text.StringBuilder text,int count);
 [DllImport("user32.dll")] public static extern bool IsWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern IntPtr WindowFromPoint(Point p);
 [DllImport("user32.dll")] public static extern IntPtr GetAncestor(IntPtr h,uint flags);
 [DllImport("user32.dll")] public static extern void mouse_event(uint flags,uint x,uint y,uint data,UIntPtr extra);
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
}
"@
function Output($v){ConvertTo-Json -InputObject $v -Depth 8 -Compress | Write-Output}
try {
 $request=[Console]::In.ReadToEnd() | ConvertFrom-Json
 if($request.op -eq 'windows'){
  $windowList=New-Object System.Collections.Generic.List[object]
  $callback=[NexusWindow+EnumProc]{param($h,$l)
   if([NexusWindow]::IsWindowVisible($h)){
    $title=New-Object System.Text.StringBuilder 1024;[void][NexusWindow]::GetWindowText($h,$title,1024)
    $class=New-Object System.Text.StringBuilder 256;[void][NexusWindow]::GetClassName($h,$class,256)
    [uint32]$pidValue=0;[void][NexusWindow]::GetWindowThreadProcessId($h,[ref]$pidValue)
    $name='Windows app';try{$name=(Get-Process -Id $pidValue -ErrorAction Stop).ProcessName}catch{}
    if($title.Length -gt 0 -and $title.ToString() -notlike '*Neural Nexus*' -and $class.ToString() -notmatch 'ConsoleWindowClass|CASCADIA_HOSTING_WINDOW_CLASS|Credential|Consent' -and $name -notmatch '^(cmd|powershell|pwsh|WindowsTerminal|Taskmgr|regedit|consent|CredentialUIBroker|mmc|SystemSettings)$'){$windowList.Add(@{handle=$h.ToInt64();pid=$pidValue;title=$title.ToString();process=$name})}
   };return $true
  }
  [void][NexusWindow]::EnumWindows($callback,[IntPtr]::Zero);$rows=@($windowList.ToArray())
  Output @{windows=$rows};exit
 }
 $handle=[IntPtr][long]$request.handle
 if(-not [NexusWindow]::IsWindow($handle)){throw 'Selected window is no longer available'}
 [uint32]$owner=0;[void][NexusWindow]::GetWindowThreadProcessId($handle,[ref]$owner)
 if($owner -ne [uint32]$request.pid){throw 'Selected window changed owner; select it again'}
 $windowTitle=New-Object System.Text.StringBuilder 1024;[void][NexusWindow]::GetWindowText($handle,$windowTitle,1024)
 $processName='Windows app';try{$processName=(Get-Process -Id $owner -ErrorAction Stop).ProcessName}catch{}
 $process=@{ProcessName=$processName;MainWindowTitle=$windowTitle.ToString()}
 if($process.ProcessName -match '^(cmd|powershell|pwsh|WindowsTerminal|Taskmgr|regedit|consent|CredentialUIBroker|mmc|SystemSettings)$' -or $process.MainWindowTitle -like '*Neural Nexus*'){throw 'This application is excluded from desktop automation'}
 $root=[System.Windows.Automation.AutomationElement]::FromHandle($handle)
 $walker=[System.Windows.Automation.TreeWalker]::ControlViewWalker
 $queue=New-Object 'System.Collections.Generic.Queue[System.Windows.Automation.AutomationElement]';$queue.Enqueue($root)
 $elements=@{};$rows=New-Object System.Collections.Generic.List[object]
 while($queue.Count -gt 0 -and $rows.Count -lt 250){
  $element=$queue.Dequeue()
  try {
   $current=$element.Current
   if($current.IsPassword){continue}
   $id=$element.GetRuntimeId() -join '.';$elements[$id]=$element
   $rows.Add(@{id=$id;name=$current.Name;role=$current.ControlType.ProgrammaticName;enabled=$current.IsEnabled;offscreen=$current.IsOffscreen})
   $child=$walker.GetFirstChild($element);$count=0
   while($null -ne $child -and $count -lt 100){$queue.Enqueue($child);$child=$walker.GetNextSibling($child);$count++}
  } catch {}
 }
 if($request.op -eq 'read'){Output @{title=$process.MainWindowTitle;process=$process.ProcessName;controls=@($rows.ToArray());note='Accessible names and controls only. Password fields excluded; no screenshot vision.'};exit}
 if(-not $request.reviewed){throw 'Desktop actions require review in Nexus'}
 $element=$elements[[string]$request.control]
 if($null -eq $element){throw 'Control is no longer in the current window; read the window again'}
 if($element.Current.IsPassword){throw 'Password input is excluded'}
 if(-not $element.Current.IsEnabled){throw 'Control is disabled'}
 switch($request.op){
  'click' {
   if($element.Current.IsOffscreen){throw 'Selected control is offscreen; scroll it into view first'}
   $bounds=$element.Current.BoundingRectangle
   if($bounds.Width -le 0 -or $bounds.Height -le 0){throw 'Selected control has no clickable bounds'}
   $x=[int]($bounds.Left+$bounds.Width/2);$y=[int]($bounds.Top+$bounds.Height/2)
   [void][NexusWindow]::SetForegroundWindow($handle)
   if([NexusWindow]::GetForegroundWindow() -ne $handle){throw 'Target window did not receive focus'}
   $under=[NexusWindow]::WindowFromPoint([NexusWindow+Point]::new($x,$y))
   if($under -ne $handle -and [NexusWindow]::GetAncestor($under,2) -ne $handle){throw 'Another window covers the target; reselect the control'}
   if(-not [NexusWindow]::SetCursorPos($x,$y)){throw 'Mouse could not reach the selected control'}
   try{[NexusWindow]::mouse_event(2,0,0,0,[UIntPtr]::Zero)}finally{[NexusWindow]::mouse_event(4,0,0,0,[UIntPtr]::Zero)}
  }
  'invoke' {$pattern=$element.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern);$pattern.Invoke()}
  'set_text' {
   $value=[string]$request.text
   if($value.Length -gt 12000){throw 'Text limit is 12,000 characters'}
   $pattern=$null
   if($element.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern,[ref]$pattern)){$pattern.SetValue($value)}
   else {
    [void][NexusWindow]::SetForegroundWindow($handle);$element.SetFocus()
    if([NexusWindow]::GetForegroundWindow() -ne $handle){throw 'Target window did not receive focus'}
    foreach($character in $value.ToCharArray()){
     $key=[string]$character
     if($key -eq "`r"){continue};if($key -eq "`n"){$key='{ENTER}'}elseif($key -match '[+^%~(){}\[\]]'){$key='{'+$key+'}'}
     [System.Windows.Forms.SendKeys]::SendWait($key)
    }
   }
  }
  'scroll' {$pattern=$element.GetCurrentPattern([System.Windows.Automation.ScrollPattern]::Pattern);$amount=if($request.direction -eq 'up'){[System.Windows.Automation.ScrollAmount]::LargeDecrement}else{[System.Windows.Automation.ScrollAmount]::LargeIncrement};$pattern.Scroll([System.Windows.Automation.ScrollAmount]::NoAmount,$amount)}
  'focus' {[void][NexusWindow]::SetForegroundWindow($handle);$element.SetFocus()}
  default {throw 'Action must be click, invoke, set_text, scroll or focus'}
 }
 Output @{ok=$true;action=$request.op;control=$request.control;title=$process.MainWindowTitle}
} catch {Output @{ok=$false;error=$_.Exception.Message};exit 1}
