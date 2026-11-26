param([string]$RequestPath)
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.Encoding]::UTF8
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type @'
using System;
using System.Text;
using System.Runtime.InteropServices;
public class ObservatoryPointer {
 [StructLayout(LayoutKind.Sequential)] public struct Point { public int X; public int Y; public Point(int x, int y) { X=x;Y=y; } }
 [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
 [DllImport("user32.dll")] public static extern IntPtr WindowFromPoint(Point point);
 [DllImport("user32.dll")] public static extern IntPtr GetAncestor(IntPtr window, uint flags);
 [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr window, StringBuilder text, int maximum);
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr window, out uint process);
}
'@
[void][ObservatoryPointer]::SetProcessDPIAware()
$script:pickedPoint=$null
$veil=New-Object Windows.Forms.Form
$veil.FormBorderStyle='None';$veil.StartPosition='Manual'
$veil.Bounds=[Windows.Forms.SystemInformation]::VirtualScreen
$veil.BackColor=[Drawing.Color]::SlateGray;$veil.Opacity=0.16
$veil.TopMost=$true;$veil.ShowInTaskbar=$false;$veil.KeyPreview=$true
$veil.Cursor=[Windows.Forms.Cursors]::Cross
$veil.AccessibleName='Observatory source picker: click a window or tab; Escape cancels'
$veil.Add_MouseUp({param($sender,$event)
 if($event.Button -eq [Windows.Forms.MouseButtons]::Left) {
  $script:pickedPoint=[Windows.Forms.Cursor]::Position
  $sender.Close()
 }
})
$veil.Add_KeyDown({param($sender,$event) if($event.KeyCode -eq 'Escape') {$sender.Close()}})
$timer=New-Object Windows.Forms.Timer
$timer.Interval=20000;$timer.Add_Tick({$veil.Close()});$timer.Start()
try {[void]$veil.ShowDialog()} finally {$timer.Stop();$timer.Dispose();$veil.Dispose()}
if($null -eq $script:pickedPoint) {'{"cancelled":true}';exit}
# The overlay consumed the click. Resolve the underlying window after it has closed.
Start-Sleep -Milliseconds 120
$native=[ObservatoryPointer]::WindowFromPoint([ObservatoryPointer+Point]::new($script:pickedPoint.X,$script:pickedPoint.Y))
$handle=[ObservatoryPointer]::GetAncestor($native,2)
if($handle -eq [IntPtr]::Zero) {throw 'No application window was selected.'}
[uint32]$selectedProcess=0
[void][ObservatoryPointer]::GetWindowThreadProcessId($handle,[ref]$selectedProcess)
$title=New-Object Text.StringBuilder 1024
[void][ObservatoryPointer]::GetWindowText($handle,$title,1024)
$processName=(Get-Process -Id $selectedProcess -ErrorAction Stop).ProcessName
if(!$title.Length) {throw 'Choose a titled application window or a visible browser tab.'}
$tabId='';$tabTitle=''
try {
 $point=New-Object Windows.Point($script:pickedPoint.X,$script:pickedPoint.Y)
 $element=[Windows.Automation.AutomationElement]::FromPoint($point)
 $walker=[Windows.Automation.TreeWalker]::ControlViewWalker
 for($i=0;$i -lt 32 -and $element;$i++) {
  if($element.Current.ControlType -eq [Windows.Automation.ControlType]::TabItem) {
   $tabId=$element.GetRuntimeId() -join '.';$tabTitle=$element.Current.Name;break
  }
  if($element.Current.NativeWindowHandle -eq $handle.ToInt64()) {break}
  $element=$walker.GetParent($element)
 }
} catch {}
@{cancelled=$false;window=@{handle=$handle.ToInt64().ToString();pid=[int]$selectedProcess;title=$title.ToString();process=$processName};tab=$tabId;tab_title=$tabTitle} | ConvertTo-Json -Depth 5 -Compress
