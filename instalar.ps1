# Instala el monitor web y crea la tarea programada diaria a las 9:00.
# Uso: abre PowerShell en esta carpeta y ejecuta  .\instalar.ps1
# Si PowerShell no deja ejecutar scripts:
#   powershell -ExecutionPolicy Bypass -File .\instalar.ps1

$ErrorActionPreference = "Stop"

$carpeta = $PSScriptRoot
$python = Join-Path $carpeta ".venv\Scripts\python.exe"
$nombreTarea = "Monitor web"

# 1. Entorno virtual y dependencias
if (-not (Test-Path $python)) {
    Write-Host "Creando entorno virtual..."
    py -m venv (Join-Path $carpeta ".venv")
}
Write-Host "Instalando dependencias..."
& $python -m pip install --quiet -r (Join-Path $carpeta "requirements.txt")

# 2. Tarea programada: todos los días a las 9:00.
# StartWhenAvailable: si el equipo estaba apagado a las 9:00, se ejecuta al encenderlo.
$accion = New-ScheduledTaskAction -Execute $python -Argument "monitor.py" -WorkingDirectory $carpeta
$desencadenante = New-ScheduledTaskTrigger -Daily -At "09:00"
$ajustes = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Register-ScheduledTask -TaskName $nombreTarea -Action $accion -Trigger $desencadenante `
    -Settings $ajustes -Description "Comprueba las URLs de urls.txt y avisa por Telegram" -Force | Out-Null

Write-Host ""
Write-Host "Listo. Tarea '$nombreTarea' creada para las 9:00."
Write-Host "Siguiente paso: configura Telegram (README, apartado 4) y prueba con:"
Write-Host "  .venv\Scripts\python.exe monitor.py --probar-telegram"
