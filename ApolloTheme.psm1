# Generated from palette/apollo.json by scripts/generate.py; do not edit.
Set-StrictMode -Version Latest

$script:ApolloPreviousColors = $null
$script:ApolloColorProperties = @{
    ContinuationPrompt = 'ContinuationPromptColor'
    Emphasis = 'EmphasisColor'
    Error = 'ErrorColor'
    Default = 'DefaultTokenColor'
    Comment = 'CommentColor'
    Keyword = 'KeywordColor'
    String = 'StringColor'
    Operator = 'OperatorColor'
    Variable = 'VariableColor'
    Command = 'CommandColor'
    Parameter = 'ParameterColor'
    Type = 'TypeColor'
    Number = 'NumberColor'
    Member = 'MemberColor'
    Selection = 'SelectionColor'
    InlinePrediction = 'InlinePredictionColor'
    ListPrediction = 'ListPredictionColor'
    ListPredictionSelected = 'ListPredictionSelectedColor'
    ListPredictionTooltip = 'ListPredictionTooltipColor'
}

function Get-ApolloPSReadLineColors {
    [CmdletBinding()]
    param()

    return @{
        ContinuationPrompt = '#d5c4a1'
        Emphasis = '#fabd2f'
        Error = '#fb4934'
        Default = '#cfbc97'
        Comment = '#928374'
        Keyword = '#83a598'
        String = '#b8bb26'
        Operator = '#d5c4a1'
        Variable = '#8ec07c'
        Command = '#fabd2f'
        Parameter = '#d3869b'
        Type = '#83a598'
        Number = '#d3869b'
        Member = '#8ec07c'
        Selection = "`e[38;2;207;188;151;48;2;60;56;54m"
        InlinePrediction = '#928374'
        ListPrediction = '#d5c4a1'
        ListPredictionSelected = "`e[38;2;20;22;23;48;2;131;165;152m"
        ListPredictionTooltip = '#928374'
    }
}

function Enable-ApolloTheme {
    [CmdletBinding()]
    param()

    if (-not (Get-Module -Name PSReadLine)) {
        Import-Module PSReadLine -ErrorAction Stop
    }

    if ($null -eq $script:ApolloPreviousColors) {
        $options = Get-PSReadLineOption
        $script:ApolloPreviousColors = @{}
        foreach ($entry in $script:ApolloColorProperties.GetEnumerator()) {
            $script:ApolloPreviousColors[$entry.Key] = $options.($entry.Value)
        }
    }

    Set-PSReadLineOption -Colors (Get-ApolloPSReadLineColors)
}

function Disable-ApolloTheme {
    [CmdletBinding()]
    param()

    if ($null -eq $script:ApolloPreviousColors) {
        return
    }

    Set-PSReadLineOption -Colors $script:ApolloPreviousColors
    $script:ApolloPreviousColors = $null
}

Export-ModuleMember -Function Get-ApolloPSReadLineColors, Enable-ApolloTheme, Disable-ApolloTheme
