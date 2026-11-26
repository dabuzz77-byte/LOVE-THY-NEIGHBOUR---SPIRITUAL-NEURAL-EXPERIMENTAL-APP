$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$inputData = [Console]::In.ReadToEnd() | ConvertFrom-Json
switch ($inputData.action) {
 'status' {
  $userProfiles = @(Get-VpnConnection -ErrorAction SilentlyContinue)
  $sharedProfiles = @(Get-VpnConnection -AllUserConnection -ErrorAction SilentlyContinue)
  $profiles = @($userProfiles | ForEach-Object { @{name=$_.Name; server=$_.ServerAddress; tunnel=[string]$_.TunnelType; status=[string]$_.ConnectionStatus; all_users=$false; split_tunnel=[bool]$_.SplitTunneling} })
  $profiles += @($sharedProfiles | ForEach-Object { @{name=$_.Name; server=$_.ServerAddress; tunnel=[string]$_.TunnelType; status=[string]$_.ConnectionStatus; all_users=$true; split_tunnel=[bool]$_.SplitTunneling} })
  @{profiles=$profiles} | ConvertTo-Json -Depth 5 -Compress
 }
 'add' {
  if ($inputData.tunnel -notin @('Ikev2','Sstp')) { throw 'Choose IKEv2 or SSTP.' }
  if (Get-VpnConnection -Name $inputData.name -ErrorAction SilentlyContinue) { throw 'A Windows VPN with this name already exists.' }
  if (Get-VpnConnection -Name $inputData.name -AllUserConnection -ErrorAction SilentlyContinue) { throw 'A shared Windows VPN with this name already exists.' }
  $null = Add-VpnConnection -Name $inputData.name -ServerAddress $inputData.server -TunnelType $inputData.tunnel -EncryptionLevel Required -AuthenticationMethod Eap -RememberCredential:$false -SplitTunneling:$false -PassThru
  @{added=$inputData.name; status='Profile created. Connect in Windows to supply the provider credentials.'} | ConvertTo-Json -Compress
 }
 default { throw 'Unsupported VPN operation.' }
}
