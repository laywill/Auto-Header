<#PSScriptInfo
.VERSION 1.0.0
.GUID 123e4567-e89b-12d3-a456-426614174000
.AUTHOR Jane Doe
.COPYRIGHT Example Ltd, UK 2024
#>

<#
.SYNOPSIS
    Example script with help.
.DESCRIPTION
    This script demonstrates PowerShell help formatting.
.PARAMETER Path
    The path to process.
#>

[CmdletBinding()]
param(
    [string]$Path
)

Write-Host "Processing $Path"
