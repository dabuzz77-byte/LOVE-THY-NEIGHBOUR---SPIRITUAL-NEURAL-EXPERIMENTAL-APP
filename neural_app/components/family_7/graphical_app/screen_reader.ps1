param([Parameter(Mandatory=$true)][string]$RequestPath)
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.Encoding]::UTF8
$captureRequest=Get-Content -LiteralPath $RequestPath -Raw -Encoding UTF8 | ConvertFrom-Json
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type @'
using System;
using System.Text;
using System.Runtime.InteropServices;
public class ObservatoryWindows {
 public delegate bool Visitor(IntPtr window, IntPtr parameter);
 [DllImport("user32.dll")] public static extern bool EnumWindows(Visitor callback, IntPtr parameter);
 [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr window);
 [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr window, StringBuilder text, int maximum);
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr window, out uint process);
}
'@
if($captureRequest.mode -eq 'windows') {
 $windows=New-Object 'System.Collections.Generic.List[object]'
 $visitor=[ObservatoryWindows+Visitor]{param($window,$parameter)
  if([ObservatoryWindows]::IsWindowVisible($window)) {
   $title=New-Object Text.StringBuilder 1024
   [void][ObservatoryWindows]::GetWindowText($window,$title,1024)
   if($title.Length -gt 0) {
    [uint32]$windowProcess=0
    [void][ObservatoryWindows]::GetWindowThreadProcessId($window,[ref]$windowProcess)
    $processName=''
    try {$processName=(Get-Process -Id $windowProcess -ErrorAction Stop).ProcessName} catch {}
    $windows.Add(@{handle=$window.ToInt64().ToString();pid=[int]$windowProcess;title=$title.ToString();process=$processName})
   }
  }
  return $true
 }
 [void][ObservatoryWindows]::EnumWindows($visitor,[IntPtr]::Zero)
 ConvertTo-Json -InputObject @($windows.ToArray()) -Depth 5 -Compress
 exit
}
$handle=[IntPtr]::new([long]$captureRequest.handle)
[uint32]$actualProcess=0
[void][ObservatoryWindows]::GetWindowThreadProcessId($handle,[ref]$actualProcess)
if($actualProcess -ne [uint32]$captureRequest.pid -or $actualProcess -eq 0) {throw 'The selected window closed or changed. Refresh the window list.'}
$root=[System.Windows.Automation.AutomationElement]::FromHandle($handle)
if(!$root) {throw 'This window does not expose readable accessibility information.'}
function ElementKey($element) {return ($element.GetRuntimeId() -join '.')}
function WalkControls($element,$limit=1400) {
 $items=New-Object 'System.Collections.Generic.List[object]'
 $queue=New-Object 'System.Collections.Generic.Queue[object]'
 $queue.Enqueue($element)
 $timer=[Diagnostics.Stopwatch]::StartNew()
 $walker=[System.Windows.Automation.TreeWalker]::ControlViewWalker
 while($queue.Count -gt 0 -and $items.Count -lt $limit -and $timer.ElapsedMilliseconds -lt 5000) {
  $current=$queue.Dequeue();$items.Add($current)
  try {
   $child=$walker.GetFirstChild($current)
   while($child -and $queue.Count -lt $limit -and $timer.ElapsedMilliseconds -lt 5000) {
    $queue.Enqueue($child);$child=$walker.GetNextSibling($child)
   }
  } catch {}
 }
 return ,$items.ToArray()
}
$controls=WalkControls $root
if($captureRequest.tab) {
 $tab=$controls | Where-Object { (ElementKey $_) -eq $captureRequest.tab } | Select-Object -First 1
 if(!$tab) {throw 'The selected browser tab is no longer available. Refresh tabs.'}
 $expectedTabName=$tab.Current.Name
 $selection=$tab.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)
 if(!$selection.Current.IsSelected) {
  if(!$captureRequest.activate) {throw 'The chosen tab is not active. Capture it again to select it, or switch back to it.'}
  $selection.Select();Start-Sleep -Milliseconds 500
 }
 # A browser can expose its previous document briefly after changing the tab.
 # Wait for a matching document; never ingest a different tab under this label.
 if($captureRequest.browser -and $captureRequest.mode -ne 'tabs') {
  $matchingDocument=$null
  for($waitIndex=0;$waitIndex -lt 6;$waitIndex++) {
   $root=[System.Windows.Automation.AutomationElement]::FromHandle($handle)
   $controls=WalkControls $root
   $matchingDocument=$controls | Where-Object {
    $_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Document -and !$_.Current.IsOffscreen -and
    $_.Current.Name -and ($_.Current.Name -eq $expectedTabName -or $expectedTabName.StartsWith($_.Current.Name+' '))
   } | Select-Object -First 1
   if($matchingDocument) {break}
   Start-Sleep -Milliseconds 300
  }
  if(!$matchingDocument) {throw 'The selected tab has not exposed its matching document yet. Activate that tab, wait for it to load, then capture again.'}
 }
} elseif($captureRequest.browser -and $captureRequest.mode -eq 'read') {throw 'Select an individual browser tab before capturing its content.'}
if($captureRequest.mode -eq 'tabs') {
 $tabs=@(foreach($element in $controls) {try {
  if($element.Current.ControlType -eq [System.Windows.Automation.ControlType]::TabItem) {
   $selected=$false
   try {$selected=$element.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Current.IsSelected} catch {}
   @{id=(ElementKey $element);title=$element.Current.Name;selected=$selected}
  }
 } catch {}})
 ConvertTo-Json -InputObject $tabs -Depth 5 -Compress;exit
}
if($captureRequest.mode -eq 'elements') {
 $elements=@(foreach($element in $controls) {try {
  if(!$element.Current.IsPassword -and $element.Current.Name -and !$element.Current.IsOffscreen) {
   @{id=(ElementKey $element);title=$element.Current.Name.Substring(0,[Math]::Min(120,$element.Current.Name.Length));type=$element.Current.ControlType.ProgrammaticName}
  }
 } catch {}})
 ConvertTo-Json -InputObject $elements -Depth 5 -Compress;exit
}
if($captureRequest.element) {
 $selected=$controls | Where-Object { (ElementKey $_) -eq $captureRequest.element } | Select-Object -First 1
 if(!$selected) {throw 'The selected element changed. Refresh elements.'}
 if($selected.Current.IsPassword) {throw 'Password fields are excluded from ingestion.'}
 $controls=WalkControls $selected 500
} elseif($captureRequest.browser) {
 # Browser toolbar, other tab titles, and address fields are outside page ingestion.
 $document=$matchingDocument
 if(!$document) {throw 'This tab does not expose a readable document. Use Website & text or paste its text.'}
 $controls=WalkControls $document
}
$pieces=New-Object 'System.Collections.Generic.List[string]'
$seen=New-Object 'System.Collections.Generic.HashSet[string]'
$characters=0
foreach($element in $controls) {
 if($characters -ge 30000) {break}
 try {
  if($element.Current.IsPassword -or $element.Current.IsOffscreen) {continue}
  $value=''
  try {$value=$element.GetCurrentPattern([System.Windows.Automation.TextPattern]::Pattern).DocumentRange.GetText(30000)} catch {}
  if(!$value) {try {$value=$element.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value} catch {}}
  if(!$value) {$value=$element.Current.Name}
  if($value -and $seen.Add($value)) {$pieces.Add($value);$characters+=$value.Length}
 } catch {}
}
$text=$pieces -join "`n"
if([string]::IsNullOrWhiteSpace($text)) {throw 'No readable text is exposed by this window or element.'}
$result=@{title=$root.Current.Name;text=$text.Substring(0,[Math]::Min(30000,$text.Length));truncated=($text.Length -gt 30000);kind='screen';pid=$actualProcess;handle=$captureRequest.handle;tab=$captureRequest.tab;element=$captureRequest.element}
ConvertTo-Json -InputObject $result -Depth 5 -Compress
