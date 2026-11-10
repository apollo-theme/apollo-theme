$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Schema = Join-Path $Root "schemas/vstheme.xsd"
$Themes = @(
    @{ Path = "themes/Apollo.vstheme"; Name = "Apollo"; Guid = "{895D123B-BC2C-58B5-B006-149BC8F1B5E7}" },
    @{ Path = "themes/Apollo Light.vstheme"; Name = "Apollo Light"; Guid = "{28E5D943-7F6B-5B87-B6F0-9AEF73CD4F34}" }
)
$requiredCategories = @("Environment", "Text Editor", "Command Window", "Output Window")

foreach ($definition in $Themes) {
    $themePath = Join-Path $Root $definition.Path
    $settings = [System.Xml.XmlReaderSettings]::new()
    $null = $settings.Schemas.Add($null, $Schema)
    $settings.ValidationType = [System.Xml.ValidationType]::Schema
    $settings.ValidationFlags = [System.Xml.Schema.XmlSchemaValidationFlags]::ReportValidationWarnings
    $errors = [System.Collections.Generic.List[string]]::new()
    $handler = [System.Xml.Schema.ValidationEventHandler] {
        param($sender, $eventArgs)
        $errors.Add($eventArgs.Message)
    }
    $settings.add_ValidationEventHandler($handler)

    $reader = [System.Xml.XmlReader]::Create($themePath, $settings)
    try {
        while ($reader.Read()) { }
    }
    finally {
        $reader.Dispose()
    }
    if ($errors.Count -gt 0) {
        throw "$($definition.Path) XML schema validation failed:`n$($errors -join "`n")"
    }

    $document = [System.Xml.XmlDocument]::new()
    $document.Load($themePath)
    $themeNode = $document.SelectSingleNode("/Themes/Theme")
    if ($null -eq $themeNode -or $themeNode.GetAttribute("Name") -ne $definition.Name -or $themeNode.GetAttribute("GUID") -ne $definition.Guid -or $themeNode.GetAttribute("MinVSVersion") -ne "17.0") {
        throw "$($definition.Path) metadata is invalid."
    }
    foreach ($category in $requiredCategories) {
        $node = $document.SelectSingleNode("/Themes/Theme/Category[@Name='$category']")
        if ($null -eq $node) {
            throw "$($definition.Path) required category '$category' is missing."
        }
    }
    Write-Host "Validated $($definition.Path) against schemas/vstheme.xsd on Windows."
}
