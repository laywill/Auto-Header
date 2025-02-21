#requires -Version 7.0 -Modules Microsoft.PowerShell.Management
using namespace System.IO
using namespace System.Text

<#
.SYNOPSIS
A sample PowerShell script demonstrating key scripting elements
.DESCRIPTION
This script showcases various PowerShell scripting techniques including
parameter handling, custom functions, and system interactions.
#>

param (
    [Parameter(Mandatory=$true)]
    [string]$InputPath,

    [Parameter(Mandatory=$false)]
    [int]$MaxFiles = 10
)

# Custom function to process files
function Process-FileCollection {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Path,

        [Parameter(Mandatory=$false)]
        [int]$Limit = 5
    )

    begin {
        Write-Host "Starting file processing from $Path"
    }

    process {
        try {
            # Get files, limited by the specified max
            $files = Get-ChildItem -Path $Path -File | Select-Object -First $Limit

            foreach ($file in $files) {
                $fileInfo = [FileInfo]::new($file.FullName)

                # Use StringBuilder for efficient string manipulation
                $sb = [StringBuilder]::new()
                [void]$sb.AppendLine("File: $($file.Name)")
                [void]$sb.AppendLine("Size: $($fileInfo.Length) bytes")

                Write-Output $sb.ToString()
            }
        }
        catch {
            Write-Error "Error processing files: $_"
        }
    }

    end {
        Write-Host "File processing completed"
    }
}

# Main script execution
try {
    # Validate input path
    if (-not (Test-Path -Path $InputPath)) {
        throw "Invalid input path: $InputPath"
    }

    # Call the custom function
    $results = Process-FileCollection -Path $InputPath -Limit $MaxFiles

    # Use built-in cmdlet to display results
    $results | Format-Table -AutoSize

    # Additional built-in function example
    Get-Date | Select-Object DateTime, Day, DayOfWeek
}
catch {
    Write-Error "Script execution failed: $_"
    exit 1
}
