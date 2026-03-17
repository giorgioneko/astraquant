Set WshShell = CreateObject("WScript.Shell")
' Run the batch file completely hidden (0)
WshShell.Run chr(34) & "c:\Sources\Investing\Launch_AstraQuant.bat" & Chr(34), 0
Set WshShell = Nothing
