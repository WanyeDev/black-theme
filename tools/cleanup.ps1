Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" |
  Where-Object { $_.CommandLine -like '*ms-playwright*' } |
  ForEach-Object { Write-Host ("kill " + $_.ProcessId); Stop-Process -Id $_.ProcessId -Force }
