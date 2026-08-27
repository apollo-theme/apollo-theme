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
if ($colors -isnot [hashtable]) { throw 'Get-ApolloPSReadLineColors must return a Hashtable.' }
Assert-Equal $colors.Count 19 'All PSReadLine semantic color tokens must be mapped.'
Assert-Equal $colors.Default '#cfbc97' 'Default text must use textPrimary.'
Assert-Equal $colors.Comment '#928374' 'Comments must use textInactive.'
Assert-Equal $colors.Error '#fb4934' 'Errors must use the error role.'
Assert-Equal $colors.Command '#fabd2f' 'Commands must use the focus role.'
if ($colors.Values -contains '#665c54') { throw '#665c54 is restricted to ANSI bright black.' }

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
foreach ($entry in $properties.GetEnumerator()) { $before[$entry.Key] = $options.($entry.Value) }
Enable-ApolloTheme
Assert-Equal (Get-PSReadLineOption).DefaultTokenColor "`e[38;2;207;188;151m" 'Enable must apply Apollo.'
Disable-ApolloTheme
$options = Get-PSReadLineOption
foreach ($entry in $properties.GetEnumerator()) {
    Assert-Equal $options.($entry.Value) $before[$entry.Key] "Disable must restore $($entry.Key)."
}
Disable-ApolloTheme
Write-Output 'PowerShell Apollo theme tests passed'
