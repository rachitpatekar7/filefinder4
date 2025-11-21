<#
Script: FileDetailsScanner.ps1
Purpose: Scan specified drives for non-system files, extract information, and export results to a CSV file.
Usage:   Modify the list of drives in the $drives array and run the script.
#>

# Change the following values 
$f_machine_files_summary_count_fk=18
$ip_address = "10.36.30.26"
$hostname = "LSG-uniFLOW"

# Define the list of drives to be scanned
$drives = @("H:\")  # Modify this list based on your network drives
##Filename below
##
$classification_file_data= "ServerIssue"
$row_created_by = "arunkumar.nair@canspirit.ai"
# Get the run date outside the loop, for the ouput of csv file
$runDate = Get-Date -Format "yyyy-MM-dd"
#$runDate = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
# Define the list of allowed file extensions (case-insensitive)
$allowedExtensions = @(".pdf", ".xls", ".xlsx", ".doc", ".docx", ".ppt", ".pptx", ".txt", ".rtf", ".csv", ".tsv", ".pst", ".sql", ".db", ".dbf", ".mdb", ".bak", ".zip", ".gz", ".tar", ".rar", ".7z", ".jpg", ".png", ".gif", ".mp3", ".mp4", ".xml", ".html", ".htm", ".log", ".odt", ".ods", ".odp", ".odg", ".odf", ".od", ".exe", ".dll", ".avi", ".bat", ".reg", ".css", ".js", ".lnk", ".sys", ".ini", ".wav", ".bmp", ".tif", ".iso", ".dat", ".psd", ".ai", ".eps")






#Define the list of drives to be scanned
#$drives = @("C:\")  # Modify this list based on your network drives
#$drives = @("C:\", "D:\", "E:\")  # Modify this list based on your network drives
#$drives = @("C:\GT_FileFInder_Arun\PS\")  # Modify this list based on your network drives

#$drives = @("C:\Users\arun_\Downloads\CanProjects\Grant_ThortonVendorRegisteration\")  # Modify this list based on your network drives

# Create an empty array to store results
$results = @()


#'YYYY-MM-DD HH:MM:SS'
foreach ($drive in $drives) {
    # Get non-system files
    #$files = Get-ChildItem -Path $drive -Recurse -File -Attributes !System -ErrorAction SilentlyContinue
    #$files = Get-ChildItem -Path $drive -Recurse -Attributes !Directory,!System,!Hidden | Where-Object { -not $_.PSIsContainer }
    # Get non-system files, with specific Extenions:
    $files = Get-ChildItem -Path $drive -Recurse -File -Attributes !System -ErrorAction SilentlyContinue |
             Where-Object { $allowedExtensions -contains $_.Extension.ToLower() }

    # Get non-system files, with specific Extenions:
    
    
    foreach ($file in $files) {
        # Extract file information
        $filePath = $file.FullName
        $fileName = $file.Name
        #$fileExtension = $file.Extension.TrimStart('.')
        $fileExtension = $file.Extension
        $owner = (Get-Acl $filePath).Owner

        # Create a custom object for each file and add it to the results array
        $results += New-Object PSObject -Property @{
            f_machine_files_summary_count_fk = $f_machine_files_summary_count_fk
            ip_address = $ip_address
            hostname = $hostname
            file_path = $filePath
            file_size_bytes = $file.Length
            file_name = $fileName.Replace("'", "''")
            file_extension = $fileExtension
            file_owner = $owner.Replace("'", "''")
            file_creation_time = $file.CreationTime.ToString('yyyy-MM-dd HH:mm:ss')
            file_modification_time = $file.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')
            file_last_access_time = $file.LastAccessTime.ToString('yyyy-MM-dd HH:mm:ss')
            classification_file_data = $classification_file_data
            row_creation_date_time = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
            row_created_by = $row_created_by
            row_modification_date_time = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
            row_modification_by = $row_created_by


        }
    }
}

# Specify the location to save the CSV file
#$csvFile = "C:\Users\FileDetails_$runDate.csv"  # Update with your path


$csvFile = "C:\GT_FileFInder_Arun\PS\18H_LSG-uniFLOW_TMS2_FileDetails_$runDate.csv"  # Update with your path
#$csvFile = "C:\Users\arun_\Downloads\PowerSh_ArunV3\FileDetails\FileDetails_$runDate.csv"  # Update with your path


# Export the results to CSV
#$results | Export-Csv -Path $csvFile -NoTypeInformation
#to append the file if you are running the cde multiple times
$results | Export-Csv -Path $csvFile -NoTypeInformation -Append

# Output the location of the CSV file
Write-Host "CSV file saved at: $csvFile"
