' ============================================================
' run-hidden.vbs - Launch auto-sync.ps1 in a hidden window.
' Khong hien terminal den khi chay nen.
' ============================================================
Option Explicit

Dim objShell, objFSO, scriptDir, cmd

Set objShell = CreateObject("WScript.Shell")
Set objFSO   = CreateObject("Scripting.FileSystemObject")

scriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)
cmd = "powershell.exe -ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File """ & scriptDir & "\auto-sync.ps1"""

' 0 = hidden window, False = do not wait
objShell.Run cmd, 0, False
