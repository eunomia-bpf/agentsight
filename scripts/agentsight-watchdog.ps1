[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Register', 'Unregister', 'Maintain')]
    [string]$Mode,
    [ValidateRange(1, 60)]
    [int]$IntervalMinutes = 5,
    [string]$WatchdogTaskName = 'AgentSight Health',
    [string]$MonitorTaskName = 'AgentSight Monitor',
    [string]$BindTaskName = 'AgentSight Bind'
)

$ErrorActionPreference = 'Stop'

$agentExeName = 'agentsight.exe'
$monitorKeyword = '\bmonitor\b'
$bindKeyword = '\bbind\b'

function Write-MaintainLog {
    param([string]$Message)

    $line = '{0:yyyy-MM-dd HH:mm:ss} {1}' -f (Get-Date), $Message
    Write-Output $line
    try {
        $logDir = Join-Path $env:LOCALAPPDATA 'AgentSight'
        New-Item -ItemType Directory -Path $logDir -Force `
            -ErrorAction Stop | Out-Null
        $logFile = Join-Path $logDir 'watchdog.log'
        $item = Get-Item $logFile -ErrorAction SilentlyContinue
        if ($item -and $item.Length -gt 262144) {
            # Keep the log bounded: keep only the most recent lines.
            Set-Content -Path $logFile -Value (Get-Content $logFile -Tail 512) `
                -ErrorAction Stop
        }
        Add-Content -Path $logFile -Value $line -ErrorAction Stop
    } catch {
        # Logging is best effort; never break a maintenance pass over it.
    }
}

function Get-RoleArgumentTail {
    param([string]$CommandLine, [string]$ExecutablePath)

    if (-not $CommandLine) { return '' }
    if ($CommandLine.StartsWith('"')) {
        $end = $CommandLine.IndexOf('"', 1)
        if ($end -ge 0) {
            return $CommandLine.Substring($end + 1).Trim()
        }
        return ''
    }
    if ($ExecutablePath -and
        $CommandLine.Length -gt $ExecutablePath.Length -and
        $CommandLine.StartsWith($ExecutablePath,
            [System.StringComparison]::OrdinalIgnoreCase)) {
        return $CommandLine.Substring($ExecutablePath.Length)
    }
    return $CommandLine
}

function Get-AgentSightInstance {
    param([string]$RoleKeyword)

    try {
        $processes = @(Get-CimInstance -ClassName Win32_Process `
            -Filter "Name = '$agentExeName'" -ErrorAction Stop)
        $blind = @($processes | Where-Object { -not $_.CommandLine })
        if ($blind.Count) {
            Write-Warning ('{0} agentsight.exe process(es) provide no command line; their role cannot be verified.' -f $blind.Count)
            # Be conservative when any AgentSight role is opaque. Starting a
            # second Monitor or Bind instance is worse than deferring recovery
            # until command-line visibility returns.
            return $processes
        }
        return @($processes | Where-Object {
            (Get-RoleArgumentTail -CommandLine $_.CommandLine `
                -ExecutablePath $_.ExecutablePath) -match $RoleKeyword })
    } catch {
        # Command-line visibility is not guaranteed for restricted callers;
        # a name-level match still suppresses an unnecessary restart when a
        # healthy manual instance exists, but roles can no longer be told apart.
        Write-Warning 'Cannot read agentsight.exe command lines; falling back to process-name matching.'
        return @(Get-Process -Name 'agentsight' `
            -ErrorAction SilentlyContinue)
    }
}

function Get-RegisteredTask {
    param([string]$TaskName)

    # Querying the complete task list lets an absent task produce an empty
    # result while service/CIM failures remain terminating, actionable errors.
    return @(Get-ScheduledTask -ErrorAction Stop | Where-Object {
        $_.TaskName -eq $TaskName -and $_.TaskPath -eq '\'
    }) | Select-Object -First 1
}

function Test-RoleAlive {
    param($Task, [string]$RoleKeyword)

    if ($Task.State -eq 'Running') { return $true }
    return (Get-AgentSightInstance -RoleKeyword $RoleKeyword).Count -gt 0
}

function Invoke-Maintain {
    foreach ($role in @(
        @{ TaskName = $MonitorTaskName; RoleKeyword = $monitorKeyword },
        @{ TaskName = $BindTaskName; RoleKeyword = $bindKeyword }
    )) {
        try {
            $task = Get-RegisteredTask -TaskName $role.TaskName
            if (-not $task) {
                Write-MaintainLog "Skipping '$($role.TaskName)': task is not registered."
                continue
            }
            if ($task.State -eq 'Disabled') { continue }
            if (-not (Test-RoleAlive -Task $task -RoleKeyword $role.RoleKeyword)) {
                Start-ScheduledTask -TaskName $role.TaskName
                Write-MaintainLog "Started '$($role.TaskName)'."
            }
        } catch {
            Write-MaintainLog "Failed to maintain '$($role.TaskName)': $($_.Exception.Message)"
        }
    }
}

function Register-Watchdog {
    foreach ($name in @($MonitorTaskName, $BindTaskName)) {
        if ($name -match '[`"]') {
            throw "Task name '$name' contains characters that cannot be embedded in the scheduled task command line."
        }
        if (-not (Get-RegisteredTask -TaskName $name)) {
            throw "Scheduled task '$name' is not registered. Register the AgentSight startup tasks first (see 'Start after sign-in' in docs/installation.md) before adding the watchdog."
        }
    }

    $interval = New-TimeSpan -Minutes $IntervalMinutes
    $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    $logonTrigger = New-ScheduledTaskTrigger -AtLogOn -User $currentUser

    $principal = New-ScheduledTaskPrincipal `
        -UserId $currentUser -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
        -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 15) `
        -MultipleInstances IgnoreNew
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' `
        -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$PSCommandPath`" -Mode Maintain -MonitorTaskName `"$MonitorTaskName`" -BindTaskName `"$BindTaskName`"" `
        -WorkingDirectory (Split-Path -Parent $PSCommandPath)

    try {
        $repetitionTrigger = New-ScheduledTaskTrigger -Once `
            -At (Get-Date).Add($interval) -RepetitionInterval $interval `
            -RepetitionDuration ([TimeSpan]::MaxValue)
        Register-ScheduledTask -TaskName $WatchdogTaskName -Action $action `
            -Trigger @($logonTrigger, $repetitionTrigger) `
            -Principal $principal -Settings $settings -Force | Out-Null
    } catch {
        # Old Task Scheduler builds reject an indefinite repetition, either
        # when the trigger object is built or when the task XML is registered;
        # fall back to a long, finite repetition window (about four years).
        Write-Warning ('Indefinite repetition rejected; using a finite window: {0}' -f $_.Exception.Message)
        $repetitionTrigger = New-ScheduledTaskTrigger -Once `
            -At (Get-Date).Add($interval) -RepetitionInterval $interval `
            -RepetitionDuration (New-TimeSpan -Days 1460)
        Register-ScheduledTask -TaskName $WatchdogTaskName -Action $action `
            -Trigger @($logonTrigger, $repetitionTrigger) `
            -Principal $principal -Settings $settings -Force | Out-Null
    }
    Write-Output "Registered '$WatchdogTaskName'. It runs at sign-in and every $IntervalMinutes minute(s)."
}

function Unregister-Watchdog {
    $task = Get-RegisteredTask -TaskName $WatchdogTaskName
    if (-not $task) {
        Write-Output "'$WatchdogTaskName' is not registered."
        return
    }
    Unregister-ScheduledTask -TaskName $WatchdogTaskName -Confirm:$false
    Write-Output "Removed '$WatchdogTaskName'."
}

switch ($Mode) {
    'Register' {
        Register-Watchdog
    }
    'Unregister' {
        Unregister-Watchdog
    }
    'Maintain' {
        Invoke-Maintain
    }
}
