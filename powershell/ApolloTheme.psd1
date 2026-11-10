@{
    RootModule = 'ApolloTheme.psm1'
    ModuleVersion = '0.2.0'
    GUID = '5c88f42f-5dbf-45f5-8514-6f99cb3b628e'
    Author = 'D0n9X1n'
    CompanyName = 'Apollo Theme'
    Copyright = '(c) 2026 D0n9X1n. MIT License.'
    Description = 'Apollo Dark and Light semantic token colors for PSReadLine with reversible activation.'
    PowerShellVersion = '7.2'
    FunctionsToExport = @('Get-ApolloPSReadLineColors', 'Enable-ApolloTheme', 'Disable-ApolloTheme')
    CmdletsToExport = @()
    VariablesToExport = @()
    AliasesToExport = @()
    PrivateData = @{
        PSData = @{
            ProjectUri = 'https://github.com/apollo-theme/powershell-apollo-theme'
            LicenseUri = 'https://github.com/apollo-theme/powershell-apollo-theme/blob/main/LICENSE'
            Tags = @('Apollo', 'Theme', 'PSReadLine')
        }
    }
}
