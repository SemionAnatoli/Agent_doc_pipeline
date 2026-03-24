' Запуск веб-интерфейса без окна командной строки (pythonw + скрытый uvicorn).
Option Explicit

Dim fso, sh, webDir, root, pyw, cmdLine

Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")

webDir = fso.GetParentFolderName(WScript.ScriptFullName)
root = fso.GetParentFolderName(webDir)
pyw = root & "\.venv\Scripts\pythonw.exe"

If fso.FileExists(pyw) Then
  cmdLine = """" & pyw & """ """ & webDir & "\run_web.py"""
Else
  cmdLine = "pyw -3 """ & webDir & "\run_web.py"""
End If

sh.CurrentDirectory = root
' 0 = скрытое окно, False = не ждать завершения (скрипт сразу выходит, сервер работает в фоне).
sh.Run cmdLine, 0, False
