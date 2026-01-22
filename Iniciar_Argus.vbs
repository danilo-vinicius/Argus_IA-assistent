Set WshShell = CreateObject("WScript.Shell") 
' O número 0 no final significa: ESCONDA A JANELA
WshShell.Run chr(34) & "run_silent.bat" & Chr(34), 0
Set WshShell = Nothing