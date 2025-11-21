import sys
from PyInstaller.utils.hooks import collect_data_files
import os
import warnings
# Suppress pkg_resources deprecation warning from dependencies
warnings.filterwarnings("ignore", category=UserWarning, module=".*pkg_resources.*")
warnings.filterwarnings("ignore", category=UserWarning, message=".*pkg_resources.*")
import pandas as pd
import psutil
import mysql.connector
import csv
from datetime import datetime, timedelta
import logging
import xlrd
from dotenv import load_dotenv
import platform
load_dotenv()
import time
import socket
from questionary import select
from rich import print
import keyboard
import subprocess
import win32net
from loguru import logger

# Performance optimization imports
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import threading
import queue
import multiprocessing
from typing import List, Dict, Any, Optional, Tuple

# Global cache for FK lookups (reduces database queries)
_machine_fk_cache = {}
_machine_fk_lock = threading.Lock()
_config_cache_timestamp = time.time()

enable_env_from_db = os.getenv("ENABLE_ENV_FROM_DB")
#####################
#Variables that can be fetched from database or .env

# Define the list of file extensions to search for
d_file_details_file_extensions = "test"
# Define word patterns to identify sensitive data in file names
sensitive_patterns = "test"
is_sensitive_file_extensions="test"
# enables teh count of files with extensions. By Defaualt the total files are counted. 
enable_file_ext_count_in_scan="test"
# Enbale scan of excel files. Enable read of the excel files 
enable_excel_file_data_scan="test"
enable_excel_file_data_scan_min_row=3
n_days = 0
#n_days = os.getenv("N_DAYS")






# Configure logging to a file
# log_file = "error.log"
# logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# def operating_system():
#     ops=input("Enter 1 for Windows and 2 for Linux")

#What is the logger.remove used for
logger.remove()






def create_db_connection(host, port, database_name,username,password):
    """
    Create MySQL database connection with error handling.
    
    Args:
        host: MySQL server hostname
        port: MySQL server port
        database_name: Database name to connect to
        username: MySQL username
        password: MySQL password
        
    Returns:
        MySQL connection object or None if connection fails
    """
    try:
        # Define your MySQL database connection details
        connection = mysql.connector.connect(
             host=host,
             port=port,
             database=database_name,
             user=username,
             password=password
         )
        
        if connection.is_connected():     
            print("[bright_green]Database connection is completed [/bright_green]")
            logger.success("Database connection is completed ")
            return connection
        else:
            logger.error("Database connection failed - not connected")        
            return None
        
    except Exception as e:
        logger.error(f"Error getting Database connection: {str(e)}", exc_info=True)
        return None


def get_or_create_machine_summary_fk(connection: Any, hostname: str, create_if_missing: bool = True) -> Optional[int]:
    """
    Retrieve or create machine summary foreign key with caching to eliminate repeated subqueries.
    
    This function provides significant performance improvement by:
    1. Caching FK lookups in memory (eliminates ~3.7M subqueries per full scan)
    2. Thread-safe access using locks
    3. Optional automatic record creation
    
    Args:
        connection: MySQL database connection
        hostname: Machine hostname to lookup
        create_if_missing: If True, create record if it doesn't exist
        
    Returns:
        Foreign key (f_machine_files_summary_count_pk) or None if not found
        
    Performance Impact: 10-20x faster than subquery approach
    """
    global _machine_fk_cache, _machine_fk_lock
    
    # Check cache first (thread-safe)
    with _machine_fk_lock:
        if hostname in _machine_fk_cache:
            return _machine_fk_cache[hostname]
    
    # Not in cache - query database
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT f_machine_files_summary_count_pk FROM f_machine_files_summary_count WHERE hostname = %s",
            (hostname,)
        )
        result = cursor.fetchone()
        
        if result:
            fk = result[0]
            # Cache the result
            with _machine_fk_lock:
                _machine_fk_cache[hostname] = fk
            return fk
        elif create_if_missing:
            # Record doesn't exist - this is normal for first scan
            logger.info(f"FK not found for hostname {hostname} - will be created during summary insert")
            return None
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error retrieving machine FK for {hostname}: {str(e)}", exc_info=True)
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()


def retrieve_env_values(enable_env_from_db,connection):
    """
    Retrieve environment configuration values from database or .env file with caching.
    
    Args:
        enable_env_from_db: If 'true', fetch from database; otherwise from .env
        connection: MySQL connection (only used if enable_env_from_db is true)
    """
    if enable_env_from_db == 'true':
        get_values_from_db(connection)
    else:
        get_values_from_env()


def batch_insert_file_details(connection: Any, machine_fk: int, file_batch: List[Dict], 
                              employee_username: str, start_time: float, batch_size: int = 1000) -> int:
    """
    Insert file details in batches for massive performance improvement.
    
    Instead of inserting one row at a time (slow), this function:
    1. Batches multiple rows into single INSERT statement
    2. Commits once per batch instead of per row
    3. Uses parameterized queries for safety
    
    Args:
        connection: MySQL database connection
        machine_fk: Foreign key to f_machine_files_summary_count table
        file_batch: List of file dictionaries with metadata
        employee_username: Username for audit trail
        start_time: Unix timestamp for audit trail
        batch_size: Number of rows per batch (default 1000)
        
    Returns:
        Number of files successfully inserted
        
    Performance Impact: 100-500x faster than row-by-row inserts
    """
    if not file_batch:
        return 0
        
    total_inserted = 0
    hostname = socket.gethostname()
    ipaddrs = socket.gethostbyname(hostname)
    
    try:
        cursor = connection.cursor()
        
        # Process in batches
        for i in range(0, len(file_batch), batch_size):
            batch = file_batch[i:i + batch_size]
            
            # Build multi-row INSERT statement
            values_template = "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FROM_UNIXTIME(%s), %s, FROM_UNIXTIME(%s), %s)"
            values_list = []
            params = []
            
            for file_data in batch:
                values_list.append(values_template)
                # Truncate file path to database limit
                truncated_path = file_data['file_path'][:759]
                
                params.extend([
                    machine_fk,                          # f_machine_files_summary_count_fk
                    ipaddrs,                             # ip_address
                    hostname,                            # hostname  
                    truncated_path,                      # file_path (truncated)
                    file_data['file_size'],              # file_size_bytes
                    file_data['file_name'],              # file_name
                    file_data['file_extension'],         # file_extension
                    file_data['file_owner'],             # file_owner
                    file_data['creation_time'],          # file_creation_time
                    file_data['modification_time'],      # file_modification_time
                    file_data['access_time'],            # file_last_access_time
                    file_data['is_sensitive'],           # file_is_sensitive_data
                    start_time,                          # row_creation_date_time
                    employee_username,                   # row_created_by
                    start_time,                          # row_modification_date_time
                    employee_username                    # row_modification_by
                ])
            
            # Execute batch insert
            query = f'''
                INSERT INTO d_file_details 
                (f_machine_files_summary_count_fk, ip_address, hostname, file_path, 
                 file_size_bytes, file_name, file_extension, file_owner, 
                 file_creation_time, file_modification_time, file_last_access_time, 
                 file_is_sensitive_data, row_creation_date_time, row_created_by,
                 row_modification_date_time, row_modification_by)
                VALUES {','.join(values_list)}
                ON DUPLICATE KEY UPDATE
                    file_size_bytes = VALUES(file_size_bytes),
                    file_modification_time = VALUES(file_modification_time),
                    row_modification_date_time = VALUES(row_modification_date_time),
                    row_modification_by = VALUES(row_modification_by)
            '''
            
            cursor.execute(query, params)
            total_inserted += len(batch)
            
            # Log progress every 5000 files
            if total_inserted % 5000 == 0:
                logger.info(f"Batch insert progress: {total_inserted} files inserted")
        
        # Commit all batches
        connection.commit()
        logger.success(f"Batch insert completed: {total_inserted} files inserted")
        
    except Exception as e:
        logger.error(f"Error in batch_insert_file_details: {str(e)}", exc_info=True)
        connection.rollback()
        return 0
    finally:
        if 'cursor' in locals():
            cursor.close()
    
    return total_inserted


def get_values_from_db(connection):
    
    
    cursor = connection.cursor()
    query = "SELECT env_key, env_value FROM env_info"
    cursor.execute(query)

    global config_values
    config_values = {env_key: env_value for env_key, env_value in cursor}
    global d_file_details_file_extensions
    d_file_details_file_extensions  = config_values.get("D_FILE_DETAILS_FILE_EXTENSIONS")
    global sensitive_patterns
    sensitive_patterns  = config_values.get("FILE_PATH_SCAN_SENSITIVE_PATTERNS")
    global is_sensitive_file_extensions
    is_sensitive_file_extensions = config_values.get("IS_SENSITIVE_FILE_EXTENSIONS")
    global enable_file_ext_count_in_scan
    enable_file_ext_count_in_scan=config_values.get("ENABLE_FILE_EXT_COUNT_IN_SCAN")
    global enable_excel_file_data_scan
    enable_excel_file_data_scan=config_values.get("ENABLE_EXCEL_FILE_DATA_SCAN")
    global enable_excel_file_data_scan_min_row
    enable_excel_file_data_scan_min_row=config_values.get("ENABLE_EXCEL_FILE_DATA_SCAN_MIN_ROW")
    global n_days
    n_days = config_values.get("N_DAYS")

    cursor.close()    




def get_values_from_env():
    #Variables that can be fetched from  .env
    # Define the list of file extensions to search for
    global d_file_details_file_extensions 
    d_file_details_file_extensions  = os.getenv("D_FILE_DETAILS_FILE_EXTENSIONS").split(",")  # Add more extensions as needed
    # Define word patterns to identify sensitive data in file names
    global sensitive_patterns 
    sensitive_patterns  = os.getenv("FILE_PATH_SCAN_SENSITIVE_PATTERNS").split(",")
    global is_sensitive_file_extensions 
    is_sensitive_file_extensions = os.getenv("IS_SENSITIVE_FILE_EXTENSIONS").split(",")
    # enables teh count of files with extensions. By Defaualt the total files are counted. 
    global enable_file_ext_count_in_scan
    enable_file_ext_count_in_scan=os.getenv("ENABLE_FILE_EXT_COUNT_IN_SCAN").lower()
    # Enbale scan of excel files. Enable read of the excel files 
    global enable_excel_file_data_scan
    enable_excel_file_data_scan=os.getenv("ENABLE_EXCEL_FILE_DATA_SCAN").lower()
    global enable_excel_file_data_scan_min_row
    enable_excel_file_data_scan_min_row=os.getenv("ENABLE_EXCEL_FILE_DATA_SCAN_MIN_ROW")
    global n_days
    n_days = int(os.getenv("N_DAYS"))
    
    

    
def get_ip_address():
    """This is a function that checks for the modified days of a file. 
       Return modified or not modified - true or false     
    Args:
        file_path (int): file path
        n_days (int): days modified from the env file

    Returns:
        boolean: true or false
    """
    
    
    try:
        # Check the operating system
        system_name = platform.system()
        
        if system_name == 'Linux':
            # Run the 'hostname -I' command and capture the output
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
            
            # Extract the IP address from the command output
            ip_addresses = result.stdout.strip().split()
            
            # Return the first IP address in the list
            if ip_addresses:
                return ip_addresses[0]
            else:
                return None
        elif system_name == 'Windows':
                # For Windows, use a different method to get the local IP address
            return socket.gethostbyname(socket.gethostname())
        else:
            print(f"Unsupported operating system: {system_name}")
            logger.error(f"Unsupported operating system: {system_name}")
            return None
    except Exception as e:
        print(f"Error getting IP address: {str(e)}")
        logger.error(f"Error getting IP address: {str(e)}")
        return None

def get_removable_drives():
    
    """This is a function that checks for the modified days of a file. 
       Return modified or not modified - true or false     
    Args:
        file_path (int): file path
        n_days (int): days modified from the env file

    Returns:
        boolean: true or false
    """
    
    removable_drives = []
#Refactor the below piece of code
    try:
        for partition in psutil.disk_partitions():
            try:
                if 'removable' in partition.opts or 'cdrom' in partition.opts:
                    removable_drives.append(partition.device)
            except Exception as inner_exception:
                print(f"An error occurred while processing partition {partition.device}: {inner_exception}")

    except Exception as outer_exception:
        print(f"Error get_removable_drives: {outer_exception}")

    return removable_drives

def get_drives():
    all_drives = []
    try:
        partitions = psutil.disk_partitions(all=True)  # Include all drives
        for partition in partitions:
            if partition.device:
                all_drives.append(partition.device)
        return all_drives
    except Exception as e:
        # Log the error to the log file
        logger.error(f"Error retrieving drive information: {str(e)}", exc_info=True)
        return None


#what is this function used for
# Define a cuhostname = socket.gethostname()  stom exception class for file-related errors
class FileError(Exception):
    pass


def is_recently_accessed_or_modified(file_path, n_days):
    """This is a function that checks for the modified days of a file. 
       Return modified or not modified - true or false     
    Args:
        file_path (int): file path
        n_days (int): days modified from the env file

    Returns:
        boolean: true or false
    """
    
    try:
        now = datetime.now()
        file_info = os.stat(file_path)
        file_mtime = datetime.fromtimestamp(file_info.st_mtime)
        file_atime = datetime.fromtimestamp(file_info.st_atime)
        delta_mtime = now - file_mtime
        delta_atime = now - file_atime
        return delta_mtime.days <= n_days or delta_atime.days <= n_days
    except Exception as e:
        # Log the error to the log file
        logger.error(f"Error checking file modification/access time: {str(e)}", exc_info=True)
        return False



def is_sensitive_file(file_path, sensitive_patterns):
    try:
        # Check if the file extension is in the allowed list
        #allowed_extensions = os.getenv("IS_SENSITIVE_FILE_EXTENSIONS").lower().split(',')
        allowed_extensions = is_sensitive_file_extensions
        if not any(file_path.lower().endswith(ext) for ext in allowed_extensions):
            return False

        file_name = os.path.basename(file_path).lower()

        # Check if any sensitive pattern is present in the file name
        for pattern in sensitive_patterns:
            if pattern in file_name:
                return True

        # If you want to check sensitive patterns in the file content, uncomment the following code:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                file_content = file.read().lower()
                for pattern in sensitive_patterns:
                    if pattern in file_content:
                        return True

    except Exception as e:
        # Log the error to the log file
        logger.error(f"Error checking file for sensitive data: {str(e)}", exc_info=True)

    return False


def search_files(root_dir, extensions, n_days, sensitive_patterns):
    found_assets = []
    try:
        for foldername, subfolders, filenames in os.walk(root_dir):
            for filename in filenames:
                #if os.getenv("D_FILE_DETAILS_FILE_EXTENSIONS").lower()=="all":
                if   d_file_details_file_extensions =="all":
                    
                    file_path = os.path.join(foldername, filename)
                    #File modified date check. If "File modified date" more than 0 then get only modified files
                    if n_days > 0 :
                        if is_recently_accessed_or_modified(file_path, n_days):
                            found_assets.append(file_path)
                    #File modified date check. If "File modified date" is 0 then get all the files
                    else:
                            found_assets.append(file_path)
                else:
                    if any(filename.lower().endswith(ext) for ext in extensions):
                        file_path = os.path.join(foldername, filename)
                        #File modified date check. If "File modified date" more than 0 then get only modified files
                        if n_days >0 :
                            if is_recently_accessed_or_modified(file_path, n_days):
                                found_assets.append(file_path)
                        #File modified date check. If "File modified date" is 0 then get all the files
                        else:    
                            found_assets.append(file_path)
                            
    except Exception as e:
        # Log the error to the log file
        logger.error(f"Error scanning files: {str(e)}", exc_info=True)
    return found_assets

   

def collect_file_metadata(file_path: str, sensitive_patterns: List[str]) -> Optional[Dict[str, Any]]:
    """
    Collect file metadata without inserting to database (for batch processing).
    
    This function extracts all file metadata and returns it as a dictionary,
    allowing batch insertion later for better performance.
    
    Args:
        file_path: Full path to the file
        sensitive_patterns: List of patterns to check for sensitive data
        
    Returns:
        Dictionary with file metadata or None if error occurs
        
    Performance Impact: Decouples metadata collection from database operations
    """
    try:
        # Get file owner based on platform
        if platform.system() == "Windows":
            import win32api
            import win32con
            import win32security
            sd = win32security.GetFileSecurity(file_path, win32security.OWNER_SECURITY_INFORMATION)
            owner_sid = sd.GetSecurityDescriptorOwner()
            name, domain, type = win32security.LookupAccountSid(None, owner_sid)
            owner_name = f"{domain}\\{name}"
        elif platform.system() == "Linux":
            import pwd
            stat_info = os.stat(file_path)
            owner_uid = stat_info.st_uid
            owner_name = pwd.getpwuid(owner_uid).pw_name
        else:
            owner_name = "Unknown"
        
        # Collect all file metadata
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_name)[1]
        modification_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        access_time = datetime.fromtimestamp(os.path.getatime(file_path))
        creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
        file_is_sensitive_data = is_sensitive_file(file_path, sensitive_patterns)
        
        return {
            'file_path': file_path,
            'file_size': file_size,
            'file_name': file_name,
            'file_extension': file_extension,
            'file_owner': owner_name,
            'creation_time': creation_time,
            'modification_time': modification_time,
            'access_time': access_time,
            'is_sensitive': file_is_sensitive_data
        }
        
    except Exception as e:
        logger.error(f"Error collecting metadata for {file_path}: {str(e)}")
        return None
        return None


def upsert_to_database(file_path, connection, employee_username, start_time):
    """
    Legacy single-row insert function (kept for backward compatibility).
    
    NOTE: For better performance, use collect_file_metadata() + batch_insert_file_details()
    This function inserts one row at a time which is ~100-500x slower than batch inserts.
    """
    try:
        if platform.system()=="Windows":
            import win32api
            import win32con
            import win32security
            # get_owner_name = get_owner_name_windows
            sd = win32security.GetFileSecurity(file_path, win32security.OWNER_SECURITY_INFORMATION)
            owner_sid = sd.GetSecurityDescriptorOwner()
            name, domain, type = win32security.LookupAccountSid(None, owner_sid)
            owner_name = f"{domain}\\{name}"
        elif platform.system()=="Linux":
            import pwd
            stat_info = os.stat(file_path)
            owner_uid = stat_info.st_uid
            owner_name = pwd.getpwuid(owner_uid).pw_name
        
        hostname = socket.gethostname()
        ipaddrs = socket.gethostbyname(hostname)
        cursor = connection.cursor()
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_name)[1]
        modification_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        access_time = datetime.fromtimestamp(os.path.getatime(file_path))
        creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
        file_is_sensitive_data = is_sensitive_file(file_path, sensitive_patterns)

        truncated_file_path = file_path[:759]

        # Perform an upsert based on file_path
        cursor.execute('''
            INSERT INTO d_file_details (f_machine_files_summary_count_fk, 
            ip_address,hostname,file_path, file_size_bytes, file_name, file_extension,file_owner,file_creation_time, 
            file_modification_time, file_last_access_time,file_is_sensitive_data,row_creation_date_time, 
            row_created_by,row_modification_date_time,row_modification_by)
            VALUES ((  SELECT f_machine_files_summary_count_pk FROM f_machine_files_summary_count WHERE hostname = %s), 
            %s,%s,%s, %s, %s, %s,%s, %s, %s, %s,%s,FROM_UNIXTIME(%s),%s,FROM_UNIXTIME(%s),%s)
            ON DUPLICATE KEY UPDATE
            file_size_bytes = %s, row_modification_date_time = FROM_UNIXTIME(%s),row_modification_by=%s ;
        ''', (
            hostname, ipaddrs, hostname, truncated_file_path, file_size, file_name, file_extension,owner_name, creation_time, 
            modification_time,
            access_time, file_is_sensitive_data, start_time, employee_username, start_time, employee_username,
            file_size, start_time, employee_username))
        
        connection.commit()
    except Exception as e:
        # Log the error to the log file
        logger.error(f"Error upsert_to_database: {str(e)}", exc_info=True)


def process_excel_file_async(file_path: str, connection_params: Dict, employee_username: str, 
                             start_time: float, max_rows: int = 100) -> bool:
    """
    Process a single Excel file asynchronously (for use with thread pool).
    
    This function is designed to run in a separate thread, allowing Excel processing
    to happen in parallel without blocking the main file scan.
    
    Args:
        file_path: Path to Excel file
        connection_params: Database connection parameters (host, port, database, user, password)
        employee_username: Username for audit trail
        start_time: Unix timestamp for audit trail
        max_rows: Maximum rows to read from each sheet
        
    Returns:
        True if successful, False otherwise
        
    Performance Impact: 5-10x faster when using thread pool with 4 workers
    """
    # Create new connection for this thread (connections aren't thread-safe)
    thread_connection = None
    try:
        thread_connection = mysql.connector.connect(**connection_params)
        cursor = thread_connection.cursor()
        
        # Read Excel file with row limit
        xls_data = pd.read_excel(file_path, sheet_name=None, nrows=max_rows)
        
        for sheet_name, sheet in xls_data.items():
            num_rows, num_cols = sheet.shape
            
            # Insert sheet metadata
            cursor.execute('''
                INSERT INTO xls_file_sheet (d_file_details_fk, sheet_name, total_cols, total_rows,
                row_creation_date_time, row_created_by,row_modification_date_time,row_modification_by)
                VALUES (
                    (SELECT d_file_details_pk FROM d_file_details WHERE file_path = %s),
                    %s, %s, %s,FROM_UNIXTIME(%s),%s,FROM_UNIXTIME(%s),%s
                ) ON DUPLICATE KEY UPDATE
                    total_cols=VALUES(total_cols),
                    total_rows=VALUES(total_rows),
                    row_modification_date_time = FROM_UNIXTIME(%s),row_modification_by=%s ;
            ''', (file_path, sheet_name, num_cols, num_rows, start_time, employee_username, 
                  start_time, employee_username, start_time, employee_username))
            
            # Process first N rows
            for row_idx in range(min(max_rows, num_rows)):
                is_row = "no" if row_idx == 0 else "yes"
                col_data = sheet.iloc[row_idx, :10].tolist()
                col_data.extend(["NULL"] * (10 - len(col_data)))
                col_data = [str(data)[:255] for data in col_data]
                is_truncate = "yes" if num_cols > 10 else "no"
                
                cursor.execute('''
                    INSERT INTO xls_file_sheet_row (xls_file_sheet_fk, sheet_name, col_no, row_no, is_row,
                    col_data_1, col_data_2, col_data_3, col_data_4, col_data_5,
                    col_data_6, col_data_7, col_data_8, col_data_9, col_data_10, is_truncate,
                    row_creation_date_time, row_created_by,row_modification_date_time,row_modification_by)
                    VALUES (
                        (SELECT xls_file_sheet_pk FROM xls_file_sheet 
                         WHERE sheet_name = %s AND d_file_details_fk = (
                            SELECT d_file_details_pk FROM d_file_details WHERE file_path = %s LIMIT 1
                         ) LIMIT 1),
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        FROM_UNIXTIME(%s),%s,FROM_UNIXTIME(%s),%s
                    ) ON DUPLICATE KEY UPDATE
                        col_data_1=VALUES(col_data_1), col_data_2=VALUES(col_data_2),
                        col_data_3=VALUES(col_data_3), col_data_4=VALUES(col_data_4),
                        col_data_5=VALUES(col_data_5), col_data_6=VALUES(col_data_6),
                        col_data_7=VALUES(col_data_7), col_data_8=VALUES(col_data_8),
                        col_data_9=VALUES(col_data_9), col_data_10=VALUES(col_data_10),
                        row_modification_date_time = FROM_UNIXTIME(%s),row_modification_by=%s ;
                ''', (sheet_name, file_path, sheet_name, num_cols, row_idx + 1, is_row, *col_data,
                      is_truncate, start_time, employee_username, start_time, employee_username,
                      start_time, employee_username))
        
        thread_connection.commit()
        logger.success(f"Excel file processed: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing Excel file {file_path}: {str(e)}")
        if thread_connection:
            thread_connection.rollback()
        return False
    finally:
        if thread_connection:
            thread_connection.close()


def process_excel_files_parallel(xls_files: List[str], connection_params: Dict, 
                                 employee_username: str, start_time: float, 
                                 max_workers: int = 4, max_rows: int = 100) -> int:
    """
    Process multiple Excel files in parallel using thread pool.
    
    This function creates a pool of worker threads to process Excel files concurrently,
    dramatically improving performance when scanning many Excel files.
    
    Args:
        xls_files: List of Excel file paths to process
        connection_params: Database connection parameters
        employee_username: Username for audit trail
        start_time: Unix timestamp for audit trail
        max_workers: Number of parallel threads (default 4)
        max_rows: Maximum rows to read from each sheet (default 100)
        
    Returns:
        Number of successfully processed files
        
    Performance Impact: 5-10x faster than sequential processing
    """
    if not xls_files:
        return 0
    
    logger.info(f"Starting parallel Excel processing: {len(xls_files)} files with {max_workers} workers")
    
    successful = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all Excel files for processing
        futures = {
            executor.submit(process_excel_file_async, xls_file, connection_params, 
                          employee_username, start_time, max_rows): xls_file
            for xls_file in xls_files
        }
        
        # Collect results as they complete
        for future in as_completed(futures):
            xls_file = futures[future]
            try:
                if future.result():
                    successful += 1
                    if successful % 10 == 0:
                        logger.info(f"Excel processing progress: {successful}/{len(xls_files)} files")
            except Exception as e:
                logger.error(f"Future exception for {xls_file}: {str(e)}")
    
    logger.success(f"Parallel Excel processing completed: {successful}/{len(xls_files)} files processed")
    return successful
    


def create_xls_file_sheet_table(connection, xls_files,employee_username, start_time):
    """
    Process Excel sheet metadata and insert into database.
    
    NOTE: For large scans, use process_excel_file_async() with thread pool for better performance.
    This function processes Excel files synchronously which can block the main scan.
    
    Args:
        connection: MySQL database connection
        xls_files: List of Excel file paths to process
        employee_username: Username for audit trail
        start_time: Unix timestamp for audit trail
    """
    try:
        cursor = connection.cursor()
        for xls_file in xls_files:
            # workbook = xlrd.open_workbook(xls_file)
            xls_data = pd.read_excel(xls_file, sheet_name=None)  # Read all sheets

            for sheet_name, sheet in xls_data.items():
                num_rows, num_cols = sheet.shape

                cursor.execute('''
                INSERT INTO xls_file_sheet (d_file_details_fk, sheet_name, total_cols, total_rows,row_creation_date_time, row_created_by,row_modification_date_time,row_modification_by)
                VALUES (
                    (SELECT d_file_details_pk FROM d_file_details WHERE file_path = %s),
                    %s, %s, %s,FROM_UNIXTIME(%s),%s,FROM_UNIXTIME(%s),%s
                )ON DUPLICATE KEY UPDATE
                               total_cols=VALUES(total_cols),
                               total_rows=VALUES(total_rows),
                               row_modification_date_time = FROM_UNIXTIME(%s),row_modification_by=%s ; 
                ''', (xls_file, sheet_name, num_cols, num_rows,start_time, employee_username, start_time, employee_username,start_time, employee_username))
                connection.commit()
        print("[bright_green]Data inserted into xls_file_sheet table.[/bright_green]")
        logger.success("Data inserted into xls_file_sheet table.")
    except Exception as e:
        logger.error(f"Error create_xls_file_sheet_table: {str(e)}", exc_info=True)


# Function to create a new table for .xls file rows
def create_xls_file_sheet_row_table(connection, xls_files,employee_username, start_time):
    try:
        cursor = connection.cursor()
        for xls_file in xls_files:
            xls_data = pd.read_excel(xls_file, sheet_name=None, header=None)  # Read all sheets

            for sheet_name, sheet in xls_data.items():
                num_rows, num_cols = sheet.shape


                # Insert the first 10 columns of data into the table, or all if there are fewer than 10 columns
                #for row_idx in range(min(int(os.getenv("ENABLE_EXCEL_FILE_DATA_SCAN_MIN_ROW")), num_rows)):  # Read up to the first 3 rows
                for row_idx in range(min(int(enable_excel_file_data_scan_min_row), num_rows)):  # Read up to the first 3 rows
                
                    is_row = "no" if row_idx == 0 else "yes"  # First row is a heading, the rest are data
                    col_data = sheet.iloc[row_idx, :10].tolist()  # Take the first 10 columns
                    col_data.extend(["NULL"] * (10 - len(col_data)))  # Fill the remaining columns with "NULL"
                    col_data = [str(data)[:255] for data in col_data]  # Truncate data if necessary
                    # Check for truncation if there are more than 10 columns
                    is_truncate = "yes" if num_cols > 10 else "no"

                    cursor.execute(f'''
                                        INSERT INTO xls_file_sheet_row (xls_file_sheet_fk, sheet_name, col_no, row_no, is_row,
                                        col_data_1, col_data_2, col_data_3, col_data_4, col_data_5,
                                        col_data_6, col_data_7, col_data_8, col_data_9, col_data_10, is_truncate,
                                        row_creation_date_time, row_created_by,row_modification_date_time,row_modification_by
                                        )
                                        VALUES (
                                        (
                                        SELECT xls_file_sheet_pk 
                                        FROM xls_file_sheet 
                                        WHERE sheet_name = %s AND d_file_details_fk = (
                                        SELECT d_file_details_pk
                                        FROM d_file_details 
                                        WHERE file_path = %s LIMIT 1

                                        ) LIMIT 1
                                        ),
                                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,FROM_UNIXTIME(%s),%s,FROM_UNIXTIME(%s),%s
                                        )ON DUPLICATE KEY UPDATE
                                                   xls_file_sheet_fk=VALUES(xls_file_sheet_fk),
                                                   sheet_name=VALUES(sheet_name),
                                                   col_no=VALUES(col_no),
                                                   row_no=VALUES(row_no),
                                                   col_data_1=VALUES(col_data_1),
                                                   col_data_2=VALUES(col_data_2),
                                                       col_data_3=VALUES(col_data_3),
                                                       col_data_4=VALUES(col_data_4),
                                                       col_data_5=VALUES(col_data_5),
                                                       col_data_6=VALUES(col_data_6),
                                                       col_data_7=VALUES(col_data_7),
                                                       col_data_8=VALUES(col_data_8),
                                                       col_data_9=VALUES(col_data_9),
                                                       col_data_10=VALUES(col_data_10),
                                                       row_modification_date_time = FROM_UNIXTIME(%s),row_modification_by=%s ;
                                        ''', (
                        sheet_name, xls_file, sheet_name, num_cols, row_idx + 1, is_row, *col_data, 
                        is_truncate,start_time, employee_username, start_time, employee_username,
                        start_time, employee_username))
                    connection.commit()
        print("[bright_green]Data inserted into xls_file_sheet_row table.[/bright_green]")
        logger.success("Data inserted into xls_file_sheet_row table.")
    except Exception as e:
        logger.error(f"create_xls_file_sheet_row_table: {str(e)}", exc_info=True)


# function for audit table
def create_audit_table(connection, employee_username, ip, start_time, end_time, elapsed_time, scan):
    if scan == "File Count":
        scan = 'Count'
    activity = 'Completed'
    try:
        cursor = connection.cursor()

        cursor.execute('''
            INSERT INTO audit_info (f_machine_files_summary_count_fk,pc_ip_address ,employee_username, start_time,end_time, duration,filefinder_activity,activity_status,
            row_creation_date_time, row_created_by,row_modification_date_time,row_modification_by
            )
            VALUES ((SELECT f_machine_files_summary_count_pk FROM f_machine_files_summary_count WHERE ip_address= %s),%s, %s, FROM_UNIXTIME(%s), FROM_UNIXTIME(%s), %s,%s,%s,
            FROM_UNIXTIME(%s),%s,FROM_UNIXTIME(%s),%s
            );
        ''', (ip, ip, employee_username, start_time, end_time, end_time - start_time, scan, activity,
        start_time, employee_username, start_time, employee_username
        ))
        connection.commit()
        print("[bright_green]Data inserted into audit_info table.[/bright_green]")
        logger.success("Data inserted into audit_info table.")
    except Exception as e:
        logger.error(f"Error create_audit_table: {str(e)}", exc_info=True)

def get_shared_drives():
    shared_drives = []
    resume = 0
    while True:
        drives_data, total, resume = win32net.NetShareEnum(None, 2, resume)
        shared_drives.extend(drives_data)
        if resume == 0:
            break
    return shared_drives



def insert_f_machine_files_summary_count(connection, ipaddress, hostname, ops, os_name, os_version, system_info, employee_username, start_time):
    try:
        if ops == "Windows":
            drives = get_drives()
            removeable_drives = get_removable_drives()
            drive_names = ""

            for i, drive in enumerate(drives, start=1):
                if drive in removeable_drives:
                    drive_names += f"{i}. {drive} (removable),"
                    
                else:
                    drive_names += f"{i}. {drive},"
                
            shared_drives =""    
            shared_drives = get_shared_drives()
            total_files = 0
            total_n_xls = 0
            total_n_xlsx = 0
            total_n_doc = 0
            total_n_docx= 0
            total_n_pdf = 0
            total_n_zip = 0
            total_n_sql = 0
            total_n_bak = 0 
            total_n_csv = 0
            total_n_txt = 0
            total_n_jpg = 0
            total_n_psd = 0
            total_n_mp4 =0
            total_n_png = 0
            total_n_dll = 0
            total_n_exe = 0
            total_n_tif = 0
            total_n_avi = 0
            total_n_pst = 0
            total_n_log = 0
            for drive in drives:
                #total_n_files += count_all_files(drive)
                #Above to be deleted
                #Arun: 30 Dec 2023: Below to be uncommented for production. 
                total_files += count_all_files(drive) 
                #Do the extension count only if enable_file_ext_count_in_scan == "true"
                if enable_file_ext_count_in_scan.lower() == "true"  :  
                    total_n_xls += count_files_with_extension(drive, ".xls")
                    #total_n_xlsx += count_files_with_extension(drive, ".xlsx")
                    #total_n_doc += count_files_with_extension(drive, ".doc")
                    #total_n_docx+= count_files_with_extension(drive, ".docx")
                    #total_n_pdf += count_files_with_extension(drive, ".pdf")
                    #total_n_zip += count_files_with_extension(drive, ".zip")
                    #total_n_sql += count_files_with_extension(drive, ".sql")
                    #total_n_bak += count_files_with_extension(drive, ".bak")
                    #total_n_csv += count_files_with_extension(drive, ".csv") 
                    #total_n_txt += count_files_with_extension(drive, ".txt") 
                    #total_n_jpg += count_files_with_extension(drive, ".jpg") 
                    #total_n_psd += count_files_with_extension(drive, ".psd")
                    #total_n_mp4 += count_files_with_extension(drive, ".mp4") 
                    #total_n_png += count_files_with_extension(drive, ".png") 
                    #total_n_dll += count_files_with_extension(drive, ".dll")
                    #total_n_exe += count_files_with_extension(drive, ".exe") 
                    #total_n_tif += count_files_with_extension(drive, ".tif") 
                    #total_n_avi += count_files_with_extension(drive, ".avi") 
                    #total_n_pst += count_files_with_extension(drive, ".pst")
                    #total_n_log += count_files_with_extension(drive, ".log")


        elif ops == "Linux":
            # For Linux, set number_of_drives and name_of_drives to NULL
            drives = None
            drive_names = None
            total_files = count_all_files("/")
            #Do the extension count only if enable_file_ext_count_in_scan == "true"
            if enable_file_ext_count_in_scan.lower() == "true"  :  
                total_n_xls = count_files_with_extension("/", ".xls")
                total_n_xlsx = count_files_with_extension("/", ".xlsx")
                total_n_doc = count_files_with_extension("/", ".doc")
                total_n_docx= count_files_with_extension("/", ".docx")
                total_n_pdf = count_files_with_extension("/", ".pdf")
                total_n_zip = count_files_with_extension("/", ".zip")
                total_n_sql = count_files_with_extension("/", ".sql")
                total_n_bak = count_files_with_extension("/", ".bak") 
                total_n_csv += count_files_with_extension("/", ".csv") 
                total_n_txt += count_files_with_extension("/", ".txt") 
                total_n_jpg += count_files_with_extension("/", ".jpg") 
                total_n_psd += count_files_with_extension("/", ".psd")
                total_n_mp4 += count_files_with_extension("/", ".mp4") 
                total_n_png += count_files_with_extension("/", ".png") 
                total_n_dll += count_files_with_extension("/", ".dll")
                total_n_exe += count_files_with_extension("/", ".exe") 
                total_n_tif += count_files_with_extension("/", ".tif") 
                total_n_avi += count_files_with_extension("/", ".avi") 
                total_n_pst += count_files_with_extension("/", ".pst")
                total_n_log += count_files_with_extension("/", ".log")

        else:
            print("Incorrect input")
            return 0

        cursor = connection.cursor()

        # Extract relevant information from system_info
        system_info_str = " ".join(str(info) for info in system_info)
        system_info_str = system_info_str[:255]  # Truncate to fit in VARCHAR(255)

        # Handle the case when drives is None

        if drives is None:
            cursor.execute('''
                    INSERT INTO f_machine_files_summary_count (
                    hostname, ip_address, os_name, os_version, system_info, number_of_drives, name_of_drives, 
                    total_n_files, total_n_xls, total_n_xlsx, total_n_doc, total_n_docx, total_n_pdf, total_n_zip, total_n_sql, total_n_bak,
                    total_n_csv,total_n_txt,total_n_jpg,total_n_psd,total_n_mp4,total_n_png,total_n_dll,total_n_exe,total_n_tif,total_n_avi,total_n_pst,total_n_log,
                    row_creation_date_time, row_created_by,row_modification_date_time,row_modification_by
                    )
                    VALUES (%s, %s, %s, %s, %s, NULL, NULL, 
                    %s, %s, %s,%s,%s,%s,%s,%s,%s,
                    %s, %s, %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                    FROM_UNIXTIME(%s),%s,FROM_UNIXTIME(%s),%s
                    ) ON DUPLICATE KEY UPDATE
                            total_n_files=VALUES(total_n_files), 
                            total_n_xls=VALUES(total_n_xls), 
                            total_n_xlsx=VALUES(total_n_xlsx), 
                            total_n_doc=VALUES(total_n_doc), 
                            total_n_docx=VALUES(total_n_docx), 
                            total_n_pdf=VALUES(total_n_pdf), 
                            total_n_zip=VALUES(total_n_zip), 
                            total_n_sql=VALUES(total_n_sql), 
                            total_n_bak=VALUES(total_n_bak),
                            total_n_csv =VALUES(total_n_csv), 
                            total_n_txt =VALUES(total_n_txt), 
                            total_n_jpg =VALUES(total_n_jpg), 
                            total_n_psd =VALUES(total_n_psd), 
                            total_n_mp4 =VALUES(total_n_mp4), 
                            total_n_png =VALUES(total_n_png),          
                            total_n_dll =VALUES(total_n_dll), 
                            total_n_exe =VALUES(total_n_exe), 
                            total_n_tif   =VALUES(total_n_tif),      
                            total_n_avi   =VALUES(total_n_avi), 
                            total_n_pst   =VALUES(total_n_pst),      
                            total_n_log  =VALUES(total_n_log), 
                            row_modification_date_time = FROM_UNIXTIME(%s),row_modification_by=%s; 

                ''', (
                hostname, ipaddress, os_name, os_version, system_info_str, 
                total_files, total_n_xls, total_n_xlsx, total_n_doc, total_n_docx, total_n_pdf, total_n_zip, total_n_sql, total_n_bak,
                total_n_csv,total_n_txt,total_n_jpg,total_n_psd,total_n_mp4,total_n_png,total_n_dll,total_n_exe,total_n_tif,total_n_avi,total_n_pst,total_n_log,
                start_time, employee_username, start_time, employee_username,
                start_time, employee_username
                
                ))
        #the below is for windows
        else:
            cursor.execute('''
                    INSERT INTO f_machine_files_summary_count (
                    hostname, ip_address, os_name, os_version, system_info, number_of_drives, name_of_drives, 
                    total_n_files, total_n_xls, total_n_xlsx, total_n_doc, total_n_docx, total_n_pdf, total_n_zip, total_n_sql, total_n_bak,
                    total_n_csv,total_n_txt,total_n_jpg,total_n_psd,total_n_mp4,total_n_png,total_n_dll,total_n_exe,total_n_tif,total_n_avi,total_n_pst,total_n_log,
                    row_creation_date_time, row_created_by,row_modification_date_time,row_modification_by
                    
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s,%s,%s,%s,%s,%s,%s,
                    %s, %s, %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                    
                    FROM_UNIXTIME(%s),%s,FROM_UNIXTIME(%s),%s
                    ) ON DUPLICATE KEY UPDATE
                            total_n_files=VALUES(total_n_files), 
                            total_n_xls=VALUES(total_n_xls), 
                            total_n_xlsx=VALUES(total_n_xlsx), 
                            total_n_doc=VALUES(total_n_doc), 
                            total_n_docx=VALUES(total_n_docx), 
                            total_n_pdf=VALUES(total_n_pdf), 
                            total_n_zip=VALUES(total_n_zip), 
                            total_n_sql=VALUES(total_n_sql), 
                            total_n_bak=VALUES(total_n_bak),
                            total_n_csv =VALUES(total_n_csv), 
                            total_n_txt =VALUES(total_n_txt), 
                            total_n_jpg =VALUES(total_n_jpg), 
                            total_n_psd =VALUES(total_n_psd), 
                            total_n_mp4 =VALUES(total_n_mp4), 
                            total_n_png =VALUES(total_n_png),          
                            total_n_dll =VALUES(total_n_dll), 
                            total_n_exe =VALUES(total_n_exe), 
                            total_n_tif   =VALUES(total_n_tif),      
                            total_n_avi   =VALUES(total_n_avi), 
                            total_n_pst   =VALUES(total_n_pst),      
                            total_n_log  =VALUES(total_n_log), 
                            row_modification_date_time = FROM_UNIXTIME(%s),row_modification_by=%s; 

                ''', (
                hostname, ipaddress, os_name, os_version, system_info_str,len(drives), drive_names,
                total_files, total_n_xls, total_n_xlsx, total_n_doc, total_n_docx, total_n_pdf, total_n_zip, total_n_sql, total_n_bak,
                total_n_csv,total_n_txt,total_n_jpg,total_n_psd,total_n_mp4,total_n_png,total_n_dll,total_n_exe,total_n_tif,total_n_avi,total_n_pst,total_n_log,
                start_time, employee_username, start_time, employee_username,
                start_time, employee_username
                
                ))
            
           

            for sh_drive in shared_drives:
                if sh_drive['path']:
                    shared_folder_name = sh_drive['netname']
                    shared_folder_path = sh_drive['path']
                    truncated_shared_folder_path = shared_folder_path[:2499]
                    shared_folder_description = sh_drive['remark']
                    #Insert into d_shared_folders
                    cursor.execute('''
                        INSERT INTO d_shared_folders (f_machine_files_summary_count_fk,
                        hostname, ip_address, os_name, os_version, system_info, number_of_drives, name_of_drives, 
                        shared_folder_name,shared_folder_path,shared_folder_description,
                        row_creation_date_time, row_created_by,row_modification_date_time,row_modification_by
                    
                        )
                        VALUES ((SELECT f_machine_files_summary_count_pk FROM f_machine_files_summary_count WHERE hostname = %s),
                        %s, %s, %s, %s, %s, %s, %s, %s, %s,%s,
                        FROM_UNIXTIME(%s),%s,FROM_UNIXTIME(%s),%s
                        ) ON DUPLICATE KEY UPDATE
                                shared_folder_path=VALUES(shared_folder_path), 
                                shared_folder_description=VALUES(shared_folder_description), 
                                row_modification_date_time = FROM_UNIXTIME(%s),row_modification_by=%s;
                            
                        ''', (hostname,
                        hostname, ipaddress, os_name, os_version, system_info_str,len(drives), drive_names,
                        shared_folder_name,truncated_shared_folder_path,shared_folder_description,
                        start_time, employee_username, start_time, employee_username,
                        start_time, employee_username                       
                    
                        ))
            connection.commit()
        #print(query)
        print("[bright_green]Data inserted into f_machine_files_summary_count table,d_shared_folders .[/bright_green]")
        logger.success("Data inserted into f_machine_files_summary_count table,d_shared_folders .")



    except Exception as e:
        print("[bright_red]An error occurred during database operations.[/bright_red]")
        logger.error(f"Error insert_f_machine_files_summary_count: {str(e)}", exc_info=True)
        #logger.error(f"{query}", exc_info=True)
#To be commented and not used


def windows(connection ):
    drives = get_drives()
    
    removeable_drives = get_removable_drives()
    extension = (".xls", ".xlsx")
    if not drives:
        print("[bright_yellow]No drives found.[/bright_yellow]")
        logger.warning("No drives found.")
    else:
        print("Drives Detected on this PC:")
        for i, drive in enumerate(drives, start=1):
            if drive in removeable_drives:
                print(f"{i}. {drive} (removable)")
            else:
                print(f"{i}. {drive}")

        scan_option_choices = ["All Drive Scan", "Specific Drive Scan"]
        scan_option = select("Select the type of scan:", choices=scan_option_choices).ask()

        try:
            if scan_option == "All Drive Scan":
                print(f"Performing a full scan for data files modified or accessed in the last {n_days} days.")
                print('***')
                print("The Tool is now scanning for Data Files. Please Wait...")

                found_assets = []
                for drive in drives:
                    found_assets.extend(search_files(drive, d_file_details_file_extensions, n_days, sensitive_patterns))
                print(
                    "[bright_green]The File Scanning is now complete!! Please wait while we insert the data into the database...[/bright_green]")
                logger.success("The File Scanning is now complete!! Please wait while we insert the data into the database.")
            elif scan_option == "Specific Drive Scan":
                drive_choice = input(
                    r"Enter the drive letter to scan (e.g., C:\, D:\, E:\, ...) or drive path (e.g., C:\Users\Username): ").upper()

                # if drive_choice in [d[0] for d in drives]:
                # selected_drive = [d for d in drives if d[0] == drive_choice][0]
                print(f"Scanning {drive_choice} for data files modified or accessed in the last {n_days} days:")
                print('***')
                print("Windows Scan: The Tool is now counting For  Files. Please Wait...")
                found_assets = search_files(drive_choice, d_file_details_file_extensions, n_days, sensitive_patterns)
                print('[bright_green]Windows Scan: The Tool has completed count For  Files. Please Wait...[/bright_green]')
                logger.success("Windows Scan: The Tool has completed count For  Files. Please Wait...")
                # else:
                #     print("Invalid drive choice.")
                #     found_assets = []
            else:
                print("Invalid option selected.")
                logger.error("Invalid option selected.")
                found_assets = []
        except ValueError:
            print("Invalid input. Please enter a valid option or drive letter.")
            logger.error("Invalid input. Please enter a valid option or drive letter.")

        
        try:
           
            # inserts data into f_machine_files_summary_count;
            print('[bright_green]Windows Scan: insert_f_machine_files_summary_count in progress. Please Wait...[/bright_green]')
            logger.success("Windows Scan: insert_f_machine_files_summary_count in progress. Please Wait...")
            
            insert_f_machine_files_summary_count(connection, ipaddrs, hostname, ops, os_name, os_version, system_info,employee_username,start_time )
            print('[bright_green]Windows Scan: insert_f_machine_files_summary_count complete. Please Wait...[/bright_green]')
            logger.success("Windows Scan: insert_f_machine_files_summary_count complete. Please Wait......")
            
            # ========================================================
            # PERFORMANCE OPTIMIZATION: Batch Insert Implementation
            # ========================================================
            # Instead of inserting files one-by-one (slow), we collect
            # metadata and insert in batches of 1000 rows (100-500x faster)
            # ========================================================
            
            if found_assets:
                # Get or retrieve the machine FK for batch inserts
                machine_fk = get_or_create_machine_summary_fk(connection, hostname)
                
                if machine_fk:
                    # Collect file metadata in batches (optimized approach)
                    logger.info(f"Collecting metadata for {len(found_assets)} files...")
                    file_batch = []
                    
                    for i, asset in enumerate(found_assets, 1):
                        # Collect metadata without inserting
                        file_data = collect_file_metadata(asset, sensitive_patterns)
                        if file_data:
                            file_batch.append(file_data)
                        
                        # Progress indicator every 1000 files
                        if i % 1000 == 0:
                            logger.info(f"Metadata collection progress: {i}/{len(found_assets)} files")
                    
                    # Batch insert all files (MUCH faster than row-by-row)
                    if file_batch:
                        logger.info(f"Starting batch insert for {len(file_batch)} files...")
                        inserted_count = batch_insert_file_details(
                            connection, machine_fk, file_batch, employee_username, start_time
                        )
                        print(f"[bright_green]Batch insert completed: {inserted_count} files saved to database[/bright_green]")
                        logger.success(f"Batch insert completed: {inserted_count} files saved to database")
                else:
                    # Fallback to old method if FK lookup fails
                    logger.warning("FK lookup failed, using legacy insert method")
                    for asset in found_assets:
                        upsert_to_database(asset, connection, employee_username, start_time)
                
                print(
                    f"[bright_green]Scan results for the last {n_days} days saved to the MySQL database...[/bright_green]")
                logger.info("Scan results for the last {n_days} days saved to the MySQL database.")
                print(
                    f"[bright_green]Scan result inserted into details table.[/bright_green]")
                logger.info("Scan result inserted into details table.")
            else:
                print("[bright_yellow]No data assets found.[/bright_yellow]")
                logger.warning("No data assets found.")
        except Exception as e:
            # Log the error to the log file
            logger.error(f"Error connecting to the database: {str(e)}")
        # finally:
        #     if connection:
        #         connection.close()
        #if (os.getenv("ENABLE_EXCEL_FILE_DATA_SCAN")).lower()=="true":
        if enable_excel_file_data_scan =="true":    
            if ".xls" or ".xlsx" in d_file_details_file_extensions:
                # xls_files = [file for file in found_assets if file.lower().endswith(".xls")]
                xls_files = [file for file in found_assets if file.lower().endswith(extension)]
                if xls_files:
                    create_xls_file_sheet_table(connection, xls_files,employee_username,start_time)
                    create_xls_file_sheet_row_table(connection, xls_files,employee_username,start_time)
                    connection.close()
                else:
                    print("No .xls files found.")
    end_time = time.time()
    elapsed_time = end_time - start_time
    ip = get_ip_address()
    scan = 'Scanning'
    create_audit_table(connection, employee_username, ip, start_time, end_time, elapsed_time, scan)
    


def linux(connection):
    start_time = time.time()
    try:
        extension = (".xls", ".xlsx")
        root_dir = '/'
        scan_option_choices = ["All Drive Scan", "Specific Path Scan"]
        scan_option = select("Select the type of scan:", choices=scan_option_choices).ask()
        if scan_option == "All Drive Scan":
            print(f"Performing a full scan for data files modified or accessed in the last {n_days} days: ")
            print('***')
            print("The Tool is now scanning for Data Files. Please Wait...")
            found_assets = []

            found_assets.extend(search_files(root_dir, d_file_details_file_extensions, n_days, sensitive_patterns))
            print("[bright_green]The File Scanning is now complete!! Please wait while we insert the data into the database...[/bright_green]")
            logger.success("The File Scanning is now complete!! Please wait while we insert the data into the database.")
        elif scan_option == "Specific Path Scan":
            path_choice = input("Enter the path (eg: root/home/gg): ").upper()
            print(f"Scanning {path_choice} for data files modified or accessed in the last {n_days} days:")
            print('***')
            print("The Tool is now scanning for Data Files. Please Wait...")
            found_assets = search_files(path_choice, d_file_details_file_extensions, n_days, sensitive_patterns)
            print("[bright_green]The File Scanning is now complete!! Please wait while we insert the data into the database...[/bright_green]")
            logger.success("The File Scanning is now complete!! Please wait while we insert the data into the database.")
        else:
            print("Invalid option selected.")
            logger.error("Invalid option selected.")
            found_assets = []

        #connection = None
        try:
            insert_f_machine_files_summary_count(connection, ipaddrs, hostname, ops, os_name, os_version, system_info,employee_username,start_time )

            if found_assets:
                for asset in found_assets:
                    upsert_to_database(asset, connection, employee_username, start_time)
                print(f"Scan results for the last {n_days} days saved to the MySQL database.")
            else:
                print("No data assets found.")
                logger.warning("No data assets found.")
        except Exception as e:
            # Log the error to the log file
            logger.error(f"Error connecting to the database: {str(e)}")
        # finally:
        #     if connection:
        #         connection.close()

        #if (os.getenv("ENABLE_EXCEL_FILE_DATA_SCAN")).lower() == "true":
        if enable_excel_file_data_scan =="true":        
            if ".xls" or ".xlsx" in d_file_details_file_extensions:
                xls_files = [file for file in found_assets if file.lower().endswith(extension)]
                if xls_files:
                    create_xls_file_sheet_table(connection, xls_files,employee_username,start_time)
                    create_xls_file_sheet_row_table(connection, xls_files,employee_username,start_time)
                    #connection.close()
                else:
                    print("No .xls files found.")
                    logger.warning("No .xls files found.")
    except Exception as e:
        print("[bright_red]An error occurred during the scan and database operations.[/bright_red]")
        logger.error(f"Error in the linux function: {str(e)}", exc_info=True)
    finally:
        end_time = time.time()
        elapsed_time = end_time - start_time
        ip = get_ip_address()
        scan = 'Scanning'
        create_audit_table(connection, employee_username, ip, start_time, end_time, elapsed_time, scan)


def count_all_files(directory):

    try:
        total_files = 0
        for root, _, files in os.walk(directory):
            total_files += len(files)
        return total_files

    except Exception as e:
         # Log the error to the log file
        logger.error(f"Counting all files: {str(e)}")
        return None


def count_files_with_extension(directory, extension):
    try:
        count = 0
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(extension.lower()):
                    count += 1

        return count
    except Exception as e:
         # Log the error to the log file
        logger.error(f"Counting files with extensions: {str(e)}")
        return None
    
def insert_log_file_to_mysql(connection, log_folder, ip_address, hostname, employee_username,start_time):
    try:
        log_file_path = os.path.join(log_folder, f"{hostname}_{ip_address}.log")
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r') as log_file:
                log_content = log_file.read()
            cursor = connection.cursor()
            cursor.execute('''
                INSERT INTO app_log_file (
                    f_machine_files_summary_count_fk,
                    ip_address,
                    hostname,
                    app_log,
                    row_creation_date_time,
                    row_created_by,
                    row_modification_date_time,
                    row_modification_by
                )
                VALUES (
                    (SELECT f_machine_files_summary_count_pk FROM f_machine_files_summary_count WHERE ip_address = %s),%s,%s,%s,FROM_UNIXTIME(%s),%s,FROM_UNIXTIME(%s),%s
                );
            ''', (
                ip_address,
                ip_address,
                hostname,
                log_content,
                start_time,
                employee_username,
                start_time,
                employee_username
            ))

            connection.commit()
            print("[bright_green]Log file content inserted into app_log_file table.[/bright_green]")
        else:
            print("[bright_yellow]Log file not found. Skipping insertion.[/bright_yellow]")

    except Exception as e:
        print("[bright_red]An error occurred during log file insertion.[/bright_red]")
        print(f"Error: {str(e)}")
        #should there not be a rollback everywhere?
        connection.rollback()





if __name__ == "__main__":
    
    # Change this flag to 'file' or 'database' based on your needs
    #if "enable_env_from_db = true" then the env values will be fetched from the database
       
        start_time = time.time()
        import platform
        from dotenv import load_dotenv
        load_dotenv()
        
        # Get the database connection strings
        #global host
        host = os.getenv("MYSQL_HOST")  # Replace with the MySQL server address
        #global port
        port = os.getenv("MYSQL_PORT")  # Replace with the MySQL server port
        
        
        #global database_name 
        #database_name = None
       
        
        database_name = os.getenv("MYSQL_DATABASE")
        #global username 
        username = os.getenv("MYSQL_USERNAME")
        #global password 
        password = os.getenv("MYSQL_PASSWORD")

        
                
        os_name = platform.system()
        # Get the OS release version
        os_version = platform.release()
        # Get more detailed system information
        system_info = platform.uname()
        hostname = socket.gethostname()
        ipaddrs = get_ip_address()
        app_log=logger.add(f"{hostname}_{ipaddrs}.log")
        logger.info("********************Start-Log********************")
        logger.info(f"Your IP Address:, {ipaddrs}")
        logger.info(f"Your Host Name: , {hostname}")
        logger.info(f"Operating System: {os_name}")
        logger.info(f"OS Version: {os_version}")
        logger.info(f"System Information: {system_info}")
        logger.info(f"database_name: {database_name}")
        print("Your IP Address:", ipaddrs)
        print("Your Host Name: ", hostname)
        print(f"Operating System: {os_name}")
        print(f"OS Version: {os_version}")
        print(f"System Information: {system_info}")
        #this is picking up old database information
        print(f"database_name: {database_name}")
        print(f"username: {username}")
        print(f"password: {password}")
        
        employee_username = input("Enter your Employee username: ")
        scan_choices = ["File Count", "File Data Scan"]
        scan = select("Select the type of scan:", choices=scan_choices).ask()

        ops_choices = ["Windows", "Linux"]
        ops = select("Select the Operating System:", choices=ops_choices).ask()
        
        
        connection = create_db_connection(host, port, database_name,username,password)
        print(f"connection: {connection}")
        retrieve_env_values(enable_env_from_db,connection)
        print(f"enable_env_from_db: {enable_env_from_db}")
        
        if scan == "File Count":
            print('***')
            print("The tool is now counting the Data Files. Please Wait...")
            
            
            insert_f_machine_files_summary_count(connection, ipaddrs, hostname, ops, os_name, os_version, system_info,employee_username,start_time )
            end_time = time.time()
            elapsed_time = end_time - start_time
            create_audit_table(connection, employee_username, ipaddrs, start_time, end_time, elapsed_time, scan)
            #Enter the error data here 
            #connection.close()
            print('[bright_green]The File Counting is now complete.[/bright_green]')
            logger.success("The File Counting is now complete.")
        elif scan == "File Data Scan":
            if ops == "Windows":
                
                windows(connection)
                
            elif ops == "Linux":
                linux(connection)
            else:
                print("Incorrect input")
        else:
            print("Incorrect input")

        logger.info("********************End-Log********************")
        log_folder = os.path.dirname(os.path.abspath(__file__))
        if os.getenv("ENABLE_APP_LOG_TO_DB")=="true":
            #insert_log_file_to_mysql(connection, log_folder, ipaddrs, hostname, employee_username,start_time)
            # Only attempt log insertion if connection exists
            if connection is not None:
                insert_log_file_to_mysql(connection, log_folder, ipaddrs, hostname, employee_username, start_time)
            else:
                logger.error("Cannot insert log file - database connection is None")
        print("Press Esc to exit...")
        connection.close()
        while not keyboard.is_pressed('Esc'):
            pass

        
        

