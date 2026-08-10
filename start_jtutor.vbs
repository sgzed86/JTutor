' Launch Jtutor as a normal Windows app — no command prompt, no Vite, no DevTools.

Option Explicit
Dim sh, fso, root, nodeExe, launcher, cmd, rc

Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = root

launcher = root & "\scripts\launch-desktop.cjs"
If Not fso.FileExists(launcher) Then
  MsgBox "Missing launcher script:" & vbCrLf & launcher, vbCritical, "Jtutor"
  WScript.Quit 1
End If

' Prefer node on PATH; fall back to common install locations.
nodeExe = "node"
On Error Resume Next
rc = sh.Run("cmd /c where node >nul 2>nul", 0, True)
On Error GoTo 0
If rc <> 0 Then
  If fso.FileExists("C:\Program Files\nodejs\node.exe") Then
    nodeExe = """C:\Program Files\nodejs\node.exe"""
  ElseIf fso.FileExists("C:\Program Files (x86)\nodejs\node.exe") Then
    nodeExe = """C:\Program Files (x86)\nodejs\node.exe"""
  Else
    MsgBox "Node.js was not found." & vbCrLf & vbCrLf & _
           "Install Node.js LTS, then try again.", vbCritical, "Jtutor"
    WScript.Quit 1
  End If
End If

' Window style 0 = hidden — rebuild (if needed) + Electron start with no console.
cmd = nodeExe & " """ & launcher & """"
rc = sh.Run(cmd, 0, False)
