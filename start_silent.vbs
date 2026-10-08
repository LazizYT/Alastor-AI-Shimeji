Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptDir

exePath = scriptDir & "\Alastor.exe"
venvPythonw = "C:\Users\Laziko\AppData\Local\hermes\hermes-agent\venv\Scripts\pythonw.exe"

If fso.FileExists(exePath) Then
    WshShell.Run """" & exePath & """", 0, False
ElseIf fso.FileExists(venvPythonw) Then
    WshShell.Run """" & venvPythonw & """ """ & scriptDir & "\PinkChan.pyw""", 0, False
Else
    WshShell.Run "pythonw.exe """ & scriptDir & "\PinkChan.pyw""", 0, False
End If
