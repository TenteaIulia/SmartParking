-- MySQL dump 10.13  Distrib 8.0.40, for Win64 (x86_64)
--
-- Host: localhost    Database: smart_parking
-- ------------------------------------------------------
-- Server version	8.0.40

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
-- Table structure for table `parking_reservations`
--

DROP TABLE IF EXISTS `parking_reservations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `parking_reservations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `zone_id` int NOT NULL,
  `license_plate` varchar(20) NOT NULL,
  `reservation_start` datetime NOT NULL,
  `reservation_end` datetime NOT NULL,
  `status` enum('active','cancelled','completed','expired') NOT NULL DEFAULT 'active',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `reservation_cost` decimal(10,2) NOT NULL DEFAULT '0.00',
  `penalty_fee` decimal(10,2) NOT NULL DEFAULT '0.00',
  `notes` varchar(255) DEFAULT NULL,
  `payment_status` enum('unpaid','paid') DEFAULT 'unpaid',
  `payment_method` varchar(50) DEFAULT NULL,
  `paid_at` datetime DEFAULT NULL,
  `spot_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `zone_id` (`zone_id`),
  CONSTRAINT `parking_reservations_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `parking_reservations_ibfk_2` FOREIGN KEY (`zone_id`) REFERENCES `parking_zones` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `parking_reservations`
--

LOCK TABLES `parking_reservations` WRITE;
/*!40000 ALTER TABLE `parking_reservations` DISABLE KEYS */;
INSERT INTO `parking_reservations` VALUES (1,2,1,'CS03TNT','2026-03-20 18:55:00','2026-03-20 19:50:00','cancelled','2026-03-20 16:45:05',0.00,0.00,'Rezervare anulată la timp.','unpaid',NULL,NULL,NULL),(2,2,3,'CS11TCC','2026-03-20 18:47:00','2026-03-20 18:52:00','cancelled','2026-03-20 16:46:33',0.00,0.42,'Late cancellation: anulare după începerea intervalului rezervat.','unpaid',NULL,NULL,NULL),(3,2,2,'B123AAA','2026-03-20 20:15:00','2026-03-20 20:35:00','completed','2026-03-20 18:10:05',0.00,0.00,NULL,'unpaid',NULL,NULL,NULL),(4,2,2,'B123AAA','2026-03-20 21:30:00','2026-03-20 21:40:00','completed','2026-03-20 19:27:25',0.00,0.00,NULL,'unpaid',NULL,NULL,NULL),(5,2,1,'CS11TNT','2026-03-20 21:55:00','2026-03-20 21:57:00','completed','2026-03-20 19:54:20',0.00,0.00,'Ieșire după expirarea rezervării - tarif extra aplicat.','unpaid',NULL,NULL,NULL),(6,3,3,'CS11TCC','2026-03-23 18:30:00','2026-03-24 20:45:00','cancelled','2026-03-23 15:44:42',0.00,0.00,'Rezervare anulată la timp.','unpaid',NULL,NULL,NULL),(7,2,1,'CS01WWW','2026-05-06 11:15:00','2026-05-06 12:00:00','expired','2026-05-06 08:14:21',0.00,3.75,'No-show: rezervarea a expirat fără intrare în parcare.','unpaid',NULL,NULL,NULL),(8,5,2,'CS03TNT','2026-05-06 11:33:00','2026-05-06 11:35:00','cancelled','2026-05-06 08:31:13',0.00,0.12,'Late cancellation: anulare după începerea intervalului rezervat.','unpaid',NULL,NULL,NULL),(9,2,2,'CS03TNT','2026-05-09 16:00:00','2026-05-09 17:30:00','cancelled','2026-05-09 12:33:33',11.25,0.00,'Rezervare anulată la timp.','paid','revolut_test','2026-05-09 15:33:34',NULL),(10,2,2,'B123AAA','2026-05-09 17:35:00','2026-05-09 21:41:00','cancelled','2026-05-09 12:35:51',30.75,0.00,'Rezervare anulată la timp.','paid','cash_test','2026-05-09 15:35:51',NULL),(11,2,2,'CS11TCC','2026-05-09 16:40:00','2026-05-09 20:45:00','cancelled','2026-05-09 12:40:30',30.62,0.00,'Rezervare anulată la timp.','paid','card_test','2026-05-09 15:40:30',NULL),(12,2,1,'CS03TNT','2026-05-09 16:41:00','2026-05-09 18:41:00','cancelled','2026-05-09 12:41:29',10.00,0.00,'Rezervare anulată la timp.','paid','cash_test','2026-05-09 15:41:29',NULL),(13,2,1,'TM66FDG','2026-05-12 23:20:00','2026-05-13 04:10:00','completed','2026-05-12 20:06:46',24.17,0.00,NULL,'paid','card_test','2026-05-12 23:06:46',NULL),(14,2,1,'CS03TNT','2026-06-17 02:30:00','2026-06-17 05:33:00','expired','2026-06-16 22:29:49',15.25,15.25,'No-show: Rezervarea a expirat fără intrare în parcare.','paid','cash_test','2026-06-17 01:29:49',NULL),(15,2,1,'B99RRR','2026-06-18 04:15:00','2026-06-18 08:19:00','expired','2026-06-17 23:13:46',20.33,20.33,'No-show: Rezervarea a expirat fără intrare în parcare.','paid','card_test','2026-06-18 02:13:46',NULL),(18,5,1,'CS01WWW','2026-06-19 01:54:00','2026-06-19 04:54:00','expired','2026-06-18 22:51:06',15.00,15.00,'No-show: Rezervarea a expirat fără intrare în parcare.','paid','card_test','2026-06-19 01:51:07',NULL),(19,2,3,'B123AAA','2026-06-19 04:22:00','2026-06-19 08:26:00','cancelled','2026-06-18 23:20:25',40.67,0.00,'Rezervare anulată la timp.','paid','cash_test','2026-06-19 02:20:25',NULL),(20,2,1,'CS11TCC','2026-06-19 03:43:00','2026-06-19 04:43:00','cancelled','2026-06-18 23:42:26',5.00,0.00,'Rezervare anulată la timp.','paid','card_test','2026-06-19 02:42:26',NULL),(21,2,1,'B123AAA','2026-06-19 05:00:00','2026-06-19 05:30:00','cancelled','2026-06-19 01:37:50',2.50,0.00,'Rezervare anulată la timp.','paid','card_test','2026-06-19 04:37:50',NULL),(22,2,2,'TM66FDG','2026-06-20 22:00:00','2026-06-21 00:00:00','completed','2026-06-20 18:57:16',15.00,0.00,NULL,'paid','card_test','2026-06-20 21:57:16',NULL),(23,2,2,'TM66FDG','2026-06-24 13:50:00','2026-06-24 14:35:00','completed','2026-06-24 10:30:28',5.62,0.00,NULL,'paid','card_test','2026-06-24 13:30:28',NULL),(24,2,3,'TL89LEO','2026-06-27 16:25:00','2026-06-27 16:40:00','cancelled','2026-06-27 13:20:56',2.50,1.25,'Late cancellation: anulare după începerea intervalului rezervat.','paid','cash_test','2026-06-27 16:20:57',NULL),(25,2,3,'B123ABC','2026-06-27 16:35:00','2026-06-27 17:30:00','completed','2026-06-27 13:29:41',9.17,0.00,NULL,'paid','cash_test','2026-06-27 16:29:41',NULL),(26,2,2,'TM63RRR','2026-06-27 16:45:00','2026-06-27 16:50:00','completed','2026-06-27 13:40:32',0.62,0.00,NULL,'paid','card_test','2026-06-27 16:40:33',NULL),(27,2,2,'TM63RRR','2026-06-27 16:50:00','2026-06-27 17:00:00','cancelled','2026-06-27 13:48:16',1.25,0.00,'Rezervare anulată la timp.','paid','card_test','2026-06-27 16:48:16',NULL),(28,2,2,'TM63RRR','2026-06-27 16:55:00','2026-06-27 17:15:00','completed','2026-06-27 13:49:34',2.50,0.00,NULL,'paid','revolut_test','2026-06-27 16:49:34',NULL),(29,2,2,'TM63RRR','2026-06-27 17:10:00','2026-06-27 17:30:00','cancelled','2026-06-27 14:03:19',2.50,0.00,'Rezervare anulată la timp.','paid','card_test','2026-06-27 17:03:20',NULL),(30,4,1,'TM63RRR','2026-06-27 17:35:00','2026-06-27 17:50:00','expired','2026-06-27 14:29:29',1.25,1.25,'No-show: Rezervarea a expirat fără intrare în parcare.','paid','card_test','2026-06-27 17:29:29',NULL),(31,2,1,'TM63RRR','2026-06-27 18:10:00','2026-06-27 18:15:00','completed','2026-06-27 15:07:35',0.42,0.00,NULL,'paid','cash_test','2026-06-27 18:07:36',NULL),(32,4,1,'TM63RRR','2026-06-27 18:13:00','2026-06-27 18:16:00','completed','2026-06-27 15:11:29',0.25,0.00,NULL,'paid','card_test','2026-06-27 18:11:30',NULL),(33,4,1,'CT91ASK','2026-06-27 18:20:00','2026-06-27 18:26:00','cancelled','2026-06-27 15:17:50',0.50,0.25,'Late cancellation: anulare după începerea intervalului rezervat.','paid','card_test','2026-06-27 18:17:51',NULL),(34,4,1,'CS66FDG','2026-06-27 18:30:00','2026-06-27 18:35:00','completed','2026-06-27 15:25:27',0.42,0.00,'Ieșire după expirarea rezervării - tarif extra aplicat.','paid','card_test','2026-06-27 18:25:28',NULL),(35,4,1,'CS03TNT','2026-06-27 18:52:00','2026-06-27 18:56:00','cancelled','2026-06-27 15:50:36',0.33,0.17,'Late cancellation: anulare după începerea intervalului rezervat.','paid','card_test','2026-06-27 18:50:36',NULL),(36,4,1,'CS11TNT','2026-06-27 18:54:00','2026-06-27 23:27:00','cancelled','2026-06-27 15:51:16',22.75,11.38,'Late cancellation: anulare după începerea intervalului rezervat.','paid','card_test','2026-06-27 18:51:16',NULL),(37,4,1,'CS11TCC','2026-06-27 19:54:00','2026-06-27 22:55:00','cancelled','2026-06-27 15:51:36',15.08,0.00,'Rezervare anulată la timp.','paid','card_test','2026-06-27 18:51:37',NULL),(38,4,2,'TM66FDG','2026-06-27 20:56:00','2026-06-27 21:57:00','cancelled','2026-06-27 15:51:58',7.62,0.00,'Rezervare anulată la timp.','paid','card_test','2026-06-27 18:51:58',NULL),(39,4,2,'B123AAA','2026-06-27 20:54:00','2026-06-27 23:58:00','cancelled','2026-06-27 15:52:32',23.00,0.00,'Rezervare anulată la timp.','paid','card_test','2026-06-27 18:52:32',NULL),(40,4,2,'VL55AAJ','2026-06-27 20:53:00','2026-06-28 04:56:00','cancelled','2026-06-27 15:53:20',60.38,0.00,'Rezervare anulată la timp.','paid','card_test','2026-06-27 18:53:21',NULL),(41,4,3,'CS01WWW','2026-06-28 19:53:00','2026-06-28 23:59:00','cancelled','2026-06-27 15:53:39',41.00,0.00,'Rezervare anulată la timp.','paid','card_test','2026-06-27 18:53:40',NULL),(42,4,3,'CS98BGD','2026-06-28 07:54:00','2026-06-28 22:54:00','cancelled','2026-06-27 15:54:26',150.00,0.00,'Rezervare anulată la timp.','paid','card_test','2026-06-27 18:54:26',NULL),(43,4,3,'TM21MOP','2026-06-30 20:54:00','2026-07-01 15:54:00','cancelled','2026-06-27 15:55:01',190.00,0.00,'Rezervare anulată la timp.','paid','card_test','2026-06-27 18:55:02',NULL),(44,2,3,'B123ABC','2026-06-28 17:10:00','2026-06-28 18:00:00','expired','2026-06-28 14:02:08',8.33,8.33,'No-show: Rezervarea a expirat fără intrare în parcare.','paid','revolut_test','2026-06-28 17:02:08',7);
/*!40000 ALTER TABLE `parking_reservations` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-07-02 10:45:31
