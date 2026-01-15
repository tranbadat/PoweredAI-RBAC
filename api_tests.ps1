$BaseUrl = "http://localhost:8000"

function Invoke-ApiPost {
    param(
        [string]$Path,
        [hashtable]$Body
    )

    $url = "$BaseUrl$Path"
    $json = $Body | ConvertTo-Json -Depth 6

    try {
        $response = Invoke-RestMethod -Method Post -Uri $url -ContentType "application/json" -Body $json
        Write-Host "POST $Path => OK" -ForegroundColor Green
        $response | ConvertTo-Json -Depth 6
    } catch {
        Write-Host "POST $Path => FAILED" -ForegroundColor Red
        if ($_.Exception.Response -and $_.Exception.Response.GetResponseStream()) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $reader.ReadToEnd()
        } else {
            $_.Exception.Message
        }
    }
    Write-Host ""
}

# 1) Recommend new user (valid)
Invoke-ApiPost -Path "/recommend/new-user" -Body @{
    role = "Doctor"
    department = "Khoa_Noi"
    branch = "CN_HN"
    license = "Yes"
    seniority = "Senior"
}

# 2) Recommend new user (missing field)
Invoke-ApiPost -Path "/recommend/new-user" -Body @{
    role = "Nurse"
    department = "Khoa_Noi"
    branch = "CN_HN"
    license = "Yes"
}

# 3) Job transfer
Invoke-ApiPost -Path "/recommend/job-transfer" -Body @{
    old_profile = @{
        role = "Doctor"
        department = "Khoa_Noi"
        branch = "CN_HN"
        license = "Yes"
        seniority = "Senior"
    }
    new_profile = @{
        role = "HR"
        department = "Phong_NhanSu"
        branch = "CN_HN"
        license = "No"
        seniority = "Senior"
    }
}

# 4) Rightsizing default
Invoke-ApiPost -Path "/recommend/rightsizing" -Body @{
    lookback_days = 90
}

# 5) Rightsizing short lookback
Invoke-ApiPost -Path "/recommend/rightsizing" -Body @{
    lookback_days = 7
}

# 6) Anomaly default
Invoke-ApiPost -Path "/recommend/anomaly" -Body @{
    risk_threshold = 3
}

# 7) Anomaly high threshold
Invoke-ApiPost -Path "/recommend/anomaly" -Body @{
    risk_threshold = 6
}
