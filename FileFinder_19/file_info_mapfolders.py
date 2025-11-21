import os

import csv

from datetime import datetime

from collections import defaultdict
 
# Define the list of drives to be scanned

#drives = ["C:/"]  # Modify this list based on your network drives
drives = ["I:/"]  # Modify this list based on your network drives

 
# Create a dictionary to store results

results = []
 
# Get the run date

run_date = datetime.now().strftime("%Y-%m-%d")
 
# Function to get file extension

def get_extension(file_name):

    return file_name.split('.')[-1] if '.' in file_name else 'No Extension'
 
for drive in drives:

    for root, dirs, files in os.walk(drive, topdown=True):

        for name in files:

            file_path = os.path.join(root, name)

            if not os.path.islink(file_path):  # Skip symbolic links

                try:

                    file_ext = get_extension(name)

                    results.append({

                        "FileType": file_ext,

                        "Extension": '.' + file_ext if file_ext != 'No Extension' else '',

                        "Count": 1,

                        "RunDate": run_date,

                        "ServerName": os.environ['COMPUTERNAME'],

                        "Drive": drive

                    })

                except OSError:

                    pass  # Handle errors such as file access issues
 
# Aggregate results

aggregated_results = defaultdict(int)

for result in results:

    key = (result['FileType'], result['Extension'], result['RunDate'], result['ServerName'], result['Drive'])

    aggregated_results[key] += 1
 
# Convert aggregated results to list of dictionaries

final_results = []

for key, count in aggregated_results.items():

    final_results.append({

        "FileType": key[0],

        "Extension": key[1],

        "Count": count,

        "RunDate": key[2],

        "ServerName": key[3],

        "Drive": key[4]

    })
 
# Specify the location to save the CSV file

#csv_file = f"C:/GT/FileTypeCounts_{run_date}.csv"  # Update with your path
#csv_file = f"C:/GT/FileTypeCounts_{run_date}.csv"  # Update with your path
 
# Export the results to CSV

with open(csv_file, mode='w', newline='', encoding='utf-8') as file:

    writer = csv.DictWriter(file, fieldnames=final_results[0].keys())
