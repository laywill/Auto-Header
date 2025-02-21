#Requires -Version 5.1
#Requires -Modules @{ ModuleName="Az"; ModuleVersion="9.3.0" }

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$ResourceGroup
)

Write-Host "Working with $ResourceGroup"
