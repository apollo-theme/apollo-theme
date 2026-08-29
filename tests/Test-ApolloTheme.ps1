$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Assert-Equal {
    param([object]$Actual, [object]$Expected, [string]$Message)
    if ($Actual -cne $Expected) {
        throw "$Message`nExpected: $Expected`nActual: $Actual"
    }
}

$modulePath = Join-Path (Split-Path $PSScriptRoot -Parent) 'ApolloTheme.psd1'
Import-Module $modulePath -Force
$colors = Get-ApolloPSReadLineColors
$explicitDark = Get-ApolloPSReadLineColors -Variant Dark
$light = Get-ApolloPSReadLineColors -Variant Light
if ($colors -isnot [hashtable]) { throw 'Get-ApolloPSReadLineColors must return a Hashtable.' }
Assert-Equal $colors.Count 19 'All PSReadLine semantic color tokens must be mapped.'
Assert-Equal $colors.Default '#cfbc97' 'Default text must use dark textPrimary.'
Assert-Equal $colors.Comment '#928374' 'Comments must use dark textInactive.'
Assert-Equal $colors.Error '#fb4934' 'Errors must use the dark error role.'
Assert-Equal $colors.Command '#fabd2f' 'Commands must use the dark focus role.'
Assert-Equal $explicitDark.Default $colors.Default 'Dark must remain the default variant.'
Assert-Equal $light.Count 19 'Apollo Light must map all PSReadLine semantic tokens.'
Assert-Equal $light.Default '#3c3836' 'Light default text must use light textPrimary.'
Assert-Equal $light.Comment '#665c54' 'Light comments must use light textInactive.'
Assert-Equal $light.Error '#9d0006' 'Light errors must use the light error role.'
Assert-Equal $light.Command '#8a5200' 'Light commands must use the light focus role.'
if ($colors.Values -contains '#665c54') { throw '#665c54 remains restricted in Apollo Dark.' }
if ($light.Values -notcontains '#665c54') { throw '#665c54 is canonical light inactive text.' }

$before = @{}
$options = Get-PSReadLineOption
$properties = @{
    ContinuationPrompt = 'ContinuationPromptColor'; Emphasis = 'EmphasisColor'; Error = 'ErrorColor'
    Default = 'DefaultTokenColor'; Comment = 'CommentColor'; Keyword = 'KeywordColor'
    String = 'StringColor'; Operator = 'OperatorColor'; Variable = 'VariableColor'
    Command = 'CommandColor'; Parameter = 'ParameterColor'; Type = 'TypeColor'; Number = 'NumberColor'
    Member = 'MemberColor'; Selection = 'SelectionColor'; InlinePrediction = 'InlinePredictionColor'
    ListPrediction = 'ListPredictionColor'; ListPredictionSelected = 'ListPredictionSelectedColor'
    ListPredictionTooltip = 'ListPredictionTooltipColor'
}
$supportedProperties = @{}
foreach ($entry in $properties.GetEnumerator()) {
    if ($null -ne $options.PSObject.Properties[$entry.Value]) {
        $supportedProperties[$entry.Key] = $entry.Value
        $before[$entry.Key] = $options.($entry.Value)
    }
}

$legacyOptions = [pscustomobject]@{
    DefaultTokenColor = 'default'
    CommentColor = 'comment'
}
$legacyProperties = & (Get-Module ApolloTheme) {
    param($Options)
    Get-ApolloSupportedColorProperties -Options $Options
} $legacyOptions
Assert-Equal $legacyProperties.Count 2 'Legacy PSReadLine options must filter unsupported properties.'
Assert-Equal $legacyProperties.Default 'DefaultTokenColor' 'Legacy default color must remain supported.'
Assert-Equal $legacyProperties.Comment 'CommentColor' 'Legacy comment color must remain supported.'

Enable-ApolloTheme
Assert-Equal (Get-PSReadLineOption).DefaultTokenColor "`e[38;2;207;188;151m" 'Enable must apply Apollo Dark by default.'
Enable-ApolloTheme -Variant Light
Assert-Equal (Get-PSReadLineOption).DefaultTokenColor "`e[38;2;60;56;54m" 'Switching must apply Apollo Light.'
Enable-ApolloTheme -Variant Dark
Assert-Equal (Get-PSReadLineOption).DefaultTokenColor "`e[38;2;207;188;151m" 'Switching back must reapply Apollo Dark.'
Disable-ApolloTheme
$options = Get-PSReadLineOption
foreach ($entry in $supportedProperties.GetEnumerator()) {
    Assert-Equal $options.($entry.Value) $before[$entry.Key] "Disable must restore the pre-Apollo $($entry.Key)."
}
Disable-ApolloTheme
Write-Output 'PowerShell Apollo theme tests passed'
