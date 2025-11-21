CREATE DATABASE  IF NOT EXISTS `lisney_files_info8` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `lisney_files_info8`;
-- MySQL dump 10.13  Distrib 8.0.36, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: lisney_files_info8
-- ------------------------------------------------------
-- Server version	8.0.36

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `app_log_file`
--

DROP TABLE IF EXISTS `app_log_file`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `app_log_file` (
  `app_log_file_pk` int NOT NULL AUTO_INCREMENT,
  `f_machine_files_summary_count_fk` int DEFAULT NULL,
  `ip_address` varchar(50) DEFAULT NULL,
  `hostname` varchar(100) DEFAULT NULL,
  `app_log` longtext,
  `row_creation_date_time` timestamp NULL DEFAULT NULL,
  `row_created_by` varchar(255) DEFAULT NULL,
  `row_modification_date_time` timestamp NULL DEFAULT NULL,
  `row_modification_by` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`app_log_file_pk`),
  KEY `app_log_file_ibfk_1` (`f_machine_files_summary_count_fk`),
  CONSTRAINT `app_log_file_ibfk_1` FOREIGN KEY (`f_machine_files_summary_count_fk`) REFERENCES `f_machine_files_summary_count` (`f_machine_files_summary_count_pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `audit_info`
--

DROP TABLE IF EXISTS `audit_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `audit_info` (
  `audit_info_pk` int NOT NULL AUTO_INCREMENT,
  `f_machine_files_summary_count_fk` int DEFAULT NULL,
  `pc_ip_address` varchar(255) DEFAULT NULL,
  `employee_username` varchar(255) DEFAULT NULL,
  `start_time` timestamp NULL DEFAULT NULL,
  `end_time` timestamp NULL DEFAULT NULL,
  `duration` text,
  `filefinder_activity` varchar(255) DEFAULT NULL,
  `activity_status` varchar(255) DEFAULT (_utf8mb4'error'),
  `row_creation_date_time` timestamp NULL DEFAULT NULL,
  `row_created_by` varchar(255) DEFAULT NULL,
  `row_modification_date_time` timestamp NULL DEFAULT NULL,
  `row_modification_by` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`audit_info_pk`),
  KEY `audit_info_ibfk_1` (`f_machine_files_summary_count_fk`),
  CONSTRAINT `audit_info_ibfk_1` FOREIGN KEY (`f_machine_files_summary_count_fk`) REFERENCES `f_machine_files_summary_count` (`f_machine_files_summary_count_pk`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `d_file_details`
--

DROP TABLE IF EXISTS `d_file_details`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `d_file_details` (
  `d_file_details_pk` int NOT NULL AUTO_INCREMENT,
  `f_machine_files_summary_count_fk` int DEFAULT NULL,
  `ip_address` varchar(25) DEFAULT NULL,
  `hostname` varchar(255) DEFAULT NULL,
  `file_path` varchar(760) DEFAULT NULL,
  `file_size_bytes` bigint DEFAULT NULL,
  `file_name` varchar(255) DEFAULT NULL,
  `file_extension` varchar(255) DEFAULT NULL,
  `file_owner` varchar(100) DEFAULT NULL,
  `file_creation_time` datetime DEFAULT NULL,
  `file_modification_time` datetime DEFAULT NULL,
  `file_last_access_time` datetime DEFAULT NULL,
  `classification_file_data` varchar(100) DEFAULT NULL,
  `file_data_domain` varchar(100) DEFAULT NULL,
  `file_is_sensitive_data` varchar(1) DEFAULT NULL,
  `file_lisney_isGPDR` varchar(1) DEFAULT NULL,
  `file_lisney_to_label` varchar(100) DEFAULT NULL,
  `file_lisney_to_describe` varchar(255) DEFAULT NULL,
  `file_lisney_to_classify` varchar(100) DEFAULT NULL,
  `row_creation_date_time` timestamp NULL DEFAULT NULL,
  `row_created_by` varchar(255) DEFAULT NULL,
  `row_modification_date_time` timestamp NULL DEFAULT NULL,
  `row_modification_by` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`d_file_details_pk`),
  UNIQUE KEY `file_path` (`f_machine_files_summary_count_fk`,`file_path`),
  CONSTRAINT `d_file_details_ibfk_1` FOREIGN KEY (`f_machine_files_summary_count_fk`) REFERENCES `f_machine_files_summary_count` (`f_machine_files_summary_count_pk`)
) ENGINE=InnoDB AUTO_INCREMENT=3736759 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `d_shared_folders`
--

DROP TABLE IF EXISTS `d_shared_folders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `d_shared_folders` (
  `d_shared_folders_pk` int NOT NULL AUTO_INCREMENT,
  `f_machine_files_summary_count_fk` int DEFAULT NULL,
  `hostname` varchar(100) DEFAULT NULL,
  `ip_address` varchar(50) DEFAULT NULL,
  `os_name` varchar(100) DEFAULT NULL,
  `os_version` varchar(100) DEFAULT NULL,
  `system_info` varchar(1000) DEFAULT NULL,
  `number_of_drives` int DEFAULT NULL,
  `name_of_drives` varchar(1000) DEFAULT NULL,
  `shared_folder_name` varchar(500) DEFAULT NULL,
  `shared_folder_path` varchar(3000) DEFAULT NULL,
  `shared_folder_description` varchar(500) DEFAULT NULL,
  `classification_fileshared_data` varchar(100) DEFAULT NULL,
  `fileshared_data_domain` varchar(100) DEFAULT NULL,
  `fileshared_is_sensitive_data` varchar(1) DEFAULT NULL,
  `fileshared_lisney_isGPDR` varchar(1) DEFAULT NULL,
  `fileshared_lisney_to_label` varchar(100) DEFAULT NULL,
  `fileshared_lisney_to_describe` varchar(255) DEFAULT NULL,
  `fileshared_lisney_to_classify` varchar(100) DEFAULT NULL,
  `row_creation_date_time` timestamp NULL DEFAULT NULL,
  `row_created_by` varchar(255) DEFAULT NULL,
  `row_modification_date_time` timestamp NULL DEFAULT NULL,
  `row_modification_by` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`d_shared_folders_pk`),
  UNIQUE KEY `share_folder_path` (`f_machine_files_summary_count_fk`,`shared_folder_name`),
  CONSTRAINT `d_shared_folders_ibfk_1` FOREIGN KEY (`f_machine_files_summary_count_fk`) REFERENCES `f_machine_files_summary_count` (`f_machine_files_summary_count_pk`)
) ENGINE=InnoDB AUTO_INCREMENT=81 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `env_info`
--

DROP TABLE IF EXISTS `env_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `env_info` (
  `env_info_pk` int NOT NULL AUTO_INCREMENT,
  `env_key` varchar(100) DEFAULT NULL,
  `env_value` varchar(1500) DEFAULT NULL,
  `row_creation_date_time` timestamp NULL DEFAULT NULL,
  `row_created_by` varchar(255) DEFAULT NULL,
  `row_modification_date_time` timestamp NULL DEFAULT NULL,
  `row_modification_by` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`env_info_pk`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `f_machine_files_count_sp`
--

DROP TABLE IF EXISTS `f_machine_files_count_sp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `f_machine_files_count_sp` (
  `f_machine_files_count_sp_pk` int NOT NULL AUTO_INCREMENT,
  `hostname` varchar(100) DEFAULT NULL,
  `ip_address` varchar(100) DEFAULT NULL,
  `file_extension` varchar(100) DEFAULT NULL,
  `file_count` varchar(100) DEFAULT NULL,
  `row_creation_date_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `row_created_by` varchar(255) DEFAULT 'arunkumar.nair@ie.gt.com',
  `row_modification_date_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `row_modification_by` varchar(100) DEFAULT 'arunkumar.nair@ie.gt.com',
  PRIMARY KEY (`f_machine_files_count_sp_pk`),
  UNIQUE KEY `hostname_file_extension` (`hostname`,`file_extension`)
) ENGINE=InnoDB AUTO_INCREMENT=1167 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `f_machine_files_summary_count`
--

DROP TABLE IF EXISTS `f_machine_files_summary_count`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `f_machine_files_summary_count` (
  `f_machine_files_summary_count_pk` int NOT NULL AUTO_INCREMENT,
  `hostname` varchar(100) DEFAULT NULL,
  `ip_address` varchar(50) DEFAULT NULL,
  `os_name` varchar(100) DEFAULT NULL,
  `os_version` varchar(100) DEFAULT NULL,
  `system_info` varchar(1000) DEFAULT NULL,
  `number_of_drives` int DEFAULT NULL,
  `name_of_drives` varchar(1000) DEFAULT NULL,
  `total_n_files` int DEFAULT NULL,
  `total_n_xls` int DEFAULT NULL,
  `total_n_xlsx` int DEFAULT NULL,
  `total_n_doc` int DEFAULT NULL,
  `total_n_docx` int DEFAULT NULL,
  `total_n_pdf` int DEFAULT NULL,
  `total_n_zip` int DEFAULT NULL,
  `total_n_sql` int DEFAULT NULL,
  `total_n_bak` int DEFAULT NULL,
  `total_n_csv` int DEFAULT NULL,
  `total_n_txt` int DEFAULT NULL,
  `total_n_jpg` int DEFAULT NULL,
  `total_n_psd` int DEFAULT NULL,
  `total_n_mp4` int DEFAULT NULL,
  `total_n_png` int DEFAULT NULL,
  `total_n_dll` int DEFAULT NULL,
  `total_n_exe` int DEFAULT NULL,
  `total_n_tif` int DEFAULT NULL,
  `total_n_avi` int DEFAULT NULL,
  `total_n_pst` int DEFAULT NULL,
  `total_n_log` int DEFAULT NULL,
  `row_creation_date_time` timestamp NULL DEFAULT NULL,
  `row_created_by` varchar(255) DEFAULT NULL,
  `row_modification_date_time` timestamp NULL DEFAULT NULL,
  `row_modification_by` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`f_machine_files_summary_count_pk`),
  UNIQUE KEY `host_key` (`hostname`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `machine_info_migration_center`
--

DROP TABLE IF EXISTS `machine_info_migration_center`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `machine_info_migration_center` (
  `machine_info_migration_centre_pk` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `create_time` date DEFAULT NULL,
  `ip` varchar(15) DEFAULT NULL,
  `model` varchar(255) DEFAULT NULL,
  `os_name` varchar(255) DEFAULT NULL,
  `total_processor` int DEFAULT NULL,
  `total_memory` int DEFAULT NULL,
  `free_memory` float DEFAULT NULL,
  `row_creation_date_time` timestamp NULL DEFAULT NULL,
  `row_created_by` varchar(255) DEFAULT NULL,
  `row_modification_date_time` timestamp NULL DEFAULT NULL,
  `row_modification_by` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`machine_info_migration_centre_pk`),
  UNIQUE KEY `idx_name` (`name`),
  KEY `idx_pc_data_pk` (`machine_info_migration_centre_pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `xls_file_sheet`
--

DROP TABLE IF EXISTS `xls_file_sheet`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `xls_file_sheet` (
  `xls_file_sheet_pk` int NOT NULL AUTO_INCREMENT,
  `d_file_details_fk` int DEFAULT NULL,
  `sheet_name` varchar(255) DEFAULT NULL,
  `total_cols` int DEFAULT NULL,
  `total_rows` int DEFAULT NULL,
  `row_creation_date_time` timestamp NULL DEFAULT NULL,
  `row_created_by` varchar(255) DEFAULT NULL,
  `row_modification_date_time` timestamp NULL DEFAULT NULL,
  `row_modification_by` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`xls_file_sheet_pk`),
  UNIQUE KEY `unique_file_sheet` (`d_file_details_fk`,`sheet_name`),
  CONSTRAINT `xls_file_sheet_ibfk_1` FOREIGN KEY (`d_file_details_fk`) REFERENCES `d_file_details` (`d_file_details_pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `xls_file_sheet_row`
--

DROP TABLE IF EXISTS `xls_file_sheet_row`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `xls_file_sheet_row` (
  `xls_file_sheet_row_pk` int NOT NULL AUTO_INCREMENT,
  `xls_file_sheet_fk` int DEFAULT NULL,
  `sheet_name` varchar(255) DEFAULT NULL,
  `col_no` int DEFAULT NULL,
  `row_no` int DEFAULT NULL,
  `is_row` varchar(3) DEFAULT NULL,
  `col_data_1` varchar(255) DEFAULT NULL,
  `col_data_2` varchar(255) DEFAULT NULL,
  `col_data_3` varchar(255) DEFAULT NULL,
  `col_data_4` varchar(255) DEFAULT NULL,
  `col_data_5` varchar(255) DEFAULT NULL,
  `col_data_6` varchar(255) DEFAULT NULL,
  `col_data_7` varchar(255) DEFAULT NULL,
  `col_data_8` varchar(255) DEFAULT NULL,
  `col_data_9` varchar(255) DEFAULT NULL,
  `col_data_10` varchar(255) DEFAULT NULL,
  `is_truncate` varchar(3) DEFAULT NULL,
  `row_creation_date_time` timestamp NULL DEFAULT NULL,
  `row_created_by` varchar(255) DEFAULT NULL,
  `row_modification_date_time` timestamp NULL DEFAULT NULL,
  `row_modification_by` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`xls_file_sheet_row_pk`),
  UNIQUE KEY `unique_file_sheet` (`xls_file_sheet_fk`,`sheet_name`,`row_no`),
  CONSTRAINT `xls_file_sheet_row_ibfk_1` FOREIGN KEY (`xls_file_sheet_fk`) REFERENCES `xls_file_sheet` (`xls_file_sheet_pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping routines for database 'lisney_files_info8'
--
/*!50003 DROP PROCEDURE IF EXISTS `GetFileCount_FileSize_Summary` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `GetFileCount_FileSize_Summary`()
BEGIN
    -- Select file details grouped by hostname
    SELECT
        hostname,
        COUNT(hostname) as total_file_count,
        SUM(file_size_bytes) as total_file_size_in_bytes,
        ROUND(SUM(file_size_bytes) / (1024 * 1024 * 1024), 2) as file_size_in_GB
    FROM
        lisney_files_info8.d_file_details
    GROUP BY
        hostname;

    -- Union with a row representing the grand total
    SELECT
        'Grand Total' as hostname,
        COUNT(hostname) as total_file_count,
        SUM(file_size_bytes) as total_file_size_in_bytes,
        ROUND(SUM(file_size_bytes) / (1024 * 1024 * 1024), 2) as file_size_in_GB
    FROM
        lisney_files_info8.d_file_details;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_InsertOrUpdateFileCounts` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_InsertOrUpdateFileCounts`()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE ip_address_value VARCHAR(255);
    DECLARE hostname_value VARCHAR(255);
    DECLARE file_extension_value VARCHAR(255);
    DECLARE file_count_value INT;
    DECLARE row_created_by_value VARCHAR(255) DEFAULT 'arun';
    
	
    
    -- Declare a cursor to select data
	DECLARE file_cursor CURSOR FOR
        SELECT 
			hostname,
			ip_address,
            file_extension,
            COUNT(*) AS file_count
        FROM 
            d_file_details
        GROUP BY 
			hostname, 
			ip_address,
            file_extension;

    -- Declare continue handler to exit loop
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    -- Open the cursor
    OPEN file_cursor;

    -- Loop through the data and insert into the table
    file_loop: LOOP
        FETCH file_cursor INTO hostname_value, ip_address_value,file_extension_value, file_count_value;
        IF done THEN
            LEAVE file_loop;
        END IF;

        -- Insert into your_table_name with retrieved values, using duplication updates
        
        INSERT INTO f_machine_files_count_sp ( hostname, ip_address, file_extension, file_count,
					row_creation_date_time,row_created_by,row_modification_date_time,row_modification_by
        )
		VALUES ( hostname_value, ip_address_value, file_extension_value, file_count_value,
				CURRENT_TIMESTAMP(),row_created_by_value, -- Assuming a default value for row_created_by
                CURRENT_TIMESTAMP(),row_created_by_value -- Assuming a default value for row_modification_by
        
        )
        #as new_f_machine_files_count_sp
		ON DUPLICATE KEY UPDATE
		file_count = VALUES(file_count);
        #file_count = new_f_machine_files_count_sp.file_count;
        
    END LOOP;

    -- Close the cursor
    CLOSE file_cursor;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-02-13 18:42:22
