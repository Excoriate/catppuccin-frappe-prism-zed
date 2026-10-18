# Inert preview: defines a function; it does not invoke it.
function Get-ThemeRecord {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $Name,
        [int[]] $Values = @(21, 21),
        [switch] $Active
    )

    $total = 0
    foreach ($value in $Values) {
        $total += $value
    }

    [pscustomobject]@{
        Name = $Name
        Total = $total
        Active = $Active.IsPresent
        Label = "${Name}:$total"
    }
}
