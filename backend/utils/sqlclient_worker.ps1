$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Data

$script:Conn = $null
$script:ConnStr = $null

function Add-Params($cmd, $params) {
  foreach ($p in $params) {
    $val = $p.value
    if ($null -eq $val) { $val = [DBNull]::Value }
    [void]$cmd.Parameters.AddWithValue([string]$p.name, $val)
  }
}

function Table-ToRows($table) {
  $rows = @()
  foreach ($row in $table.Rows) {
    $obj = [ordered]@{}
    foreach ($col in $table.Columns) {
      $v = $row[$col.ColumnName]
      if ($v -is [System.DBNull]) { $v = $null }
      $obj[$col.ColumnName] = $v
    }
    $rows += [pscustomobject]$obj
  }
  return ,$rows
}

function Get-DbConnection($connStr) {
  if ($script:Conn -and $script:Conn.State -eq [System.Data.ConnectionState]::Open -and $script:ConnStr -eq $connStr) {
    return $script:Conn
  }
  if ($script:Conn) {
    try { $script:Conn.Close() } catch {}
    try { $script:Conn.Dispose() } catch {}
  }
  $script:Conn = New-Object System.Data.SqlClient.SqlConnection ([string]$connStr)
  $script:Conn.Open()
  $script:ConnStr = $connStr
  return $script:Conn
}

function Invoke-Payload($payload) {
  $conn = Get-DbConnection ([string]$payload.connection_string)

  if ($payload.mode -eq 'query') {
    $cmd = $conn.CreateCommand()
    $cmd.CommandText = [string]$payload.sql
    Add-Params $cmd $payload.params
    $adapter = New-Object System.Data.SqlClient.SqlDataAdapter $cmd
    $table = New-Object System.Data.DataTable
    [void]$adapter.Fill($table)
    return [pscustomobject]@{ ok = $true; rows = (Table-ToRows $table) }
  }

  if ($payload.mode -eq 'execute') {
    $cmd = $conn.CreateCommand()
    $cmd.CommandText = [string]$payload.sql
    Add-Params $cmd $payload.params
    $count = $cmd.ExecuteNonQuery()
    return [pscustomobject]@{ ok = $true; rowcount = $count }
  }

  if ($payload.mode -eq 'transaction') {
    $tx = $conn.BeginTransaction()
    try {
      $counts = @()
      foreach ($stmt in $payload.statements) {
        $cmd = $conn.CreateCommand()
        $cmd.Transaction = $tx
        $cmd.CommandText = [string]$stmt.sql
        Add-Params $cmd $stmt.params
        $counts += $cmd.ExecuteNonQuery()
      }
      $tx.Commit()
      return [pscustomobject]@{ ok = $true; rowcounts = $counts }
    } catch {
      try { $tx.Rollback() } catch {}
      throw
    }
  }

  if ($payload.mode -eq 'batch_query') {
    $results = @()
    foreach ($stmt in $payload.statements) {
      $cmd = $conn.CreateCommand()
      $cmd.CommandText = [string]$stmt.sql
      Add-Params $cmd $stmt.params
      $adapter = New-Object System.Data.SqlClient.SqlDataAdapter $cmd
      $table = New-Object System.Data.DataTable
      [void]$adapter.Fill($table)
      $results += ,@(Table-ToRows $table)
    }
    return [pscustomobject]@{ ok = $true; results = $results }
  }

  throw "Unsupported mode: $($payload.mode)"
}

while (($line = [Console]::In.ReadLine()) -ne $null) {
  if ([string]::IsNullOrWhiteSpace($line)) { continue }
  try {
    $raw = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($line))
    $payload = $raw | ConvertFrom-Json
    $result = Invoke-Payload $payload
  } catch {
    $result = [pscustomobject]@{
      ok = $false
      error = $_.Exception.Message
      detail = ($_ | Out-String)
    }
  }
  $json = $result | ConvertTo-Json -Compress -Depth 20
  $outLine = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($json))
  [Console]::Out.WriteLine($outLine)
  [Console]::Out.Flush()
}
