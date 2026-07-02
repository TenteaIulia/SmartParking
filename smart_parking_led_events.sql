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
-- Table structure for table `led_events`
--

DROP TABLE IF EXISTS `led_events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `led_events` (
  `id` int NOT NULL AUTO_INCREMENT,
  `zone_id` int NOT NULL,
  `spot_number` int NOT NULL,
  `duration_seconds` int DEFAULT '15',
  `status` enum('pending','done') DEFAULT 'pending',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=52 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `led_events`
--

LOCK TABLES `led_events` WRITE;
/*!40000 ALTER TABLE `led_events` DISABLE KEYS */;
INSERT INTO `led_events` VALUES (1,1,2,15,'done','2026-06-20 20:44:25'),(2,1,2,15,'done','2026-06-20 21:49:02'),(3,2,2,15,'done','2026-06-20 21:59:00'),(4,2,1,15,'done','2026-06-20 22:12:41'),(5,1,1,15,'done','2026-06-20 22:25:54'),(6,1,1,15,'done','2026-06-20 22:34:24'),(7,3,1,15,'done','2026-06-20 22:35:14'),(8,1,1,15,'done','2026-06-23 19:37:12'),(9,2,1,15,'done','2026-06-23 21:35:53'),(10,1,2,15,'done','2026-06-23 21:50:38'),(11,1,3,15,'done','2026-06-23 21:51:40'),(12,1,2,15,'done','2026-06-23 22:37:24'),(13,2,1,15,'done','2026-06-23 22:42:01'),(14,2,2,15,'done','2026-06-23 22:45:36'),(15,1,1,15,'done','2026-06-23 23:28:12'),(16,1,1,15,'done','2026-06-24 00:46:59'),(17,1,2,15,'done','2026-06-24 00:56:09'),(18,1,1,15,'done','2026-06-24 01:10:54'),(19,1,2,15,'done','2026-06-24 01:12:29'),(20,2,1,15,'done','2026-06-24 01:13:15'),(21,2,2,15,'done','2026-06-24 01:13:34'),(22,2,1,15,'done','2026-06-24 12:04:57'),(23,2,2,15,'done','2026-06-24 13:36:22'),(24,3,1,15,'done','2026-06-24 14:10:30'),(25,2,1,15,'done','2026-06-25 21:18:14'),(26,3,1,15,'done','2026-06-25 21:21:52'),(27,1,1,15,'done','2026-06-26 18:17:00'),(28,2,1,15,'done','2026-06-26 19:24:22'),(29,2,1,15,'done','2026-06-26 19:26:12'),(30,2,1,15,'done','2026-06-26 19:28:03'),(31,1,1,15,'done','2026-06-26 19:33:49'),(32,1,1,15,'done','2026-06-26 19:37:01'),(33,1,1,15,'done','2026-06-26 19:38:41'),(34,1,1,15,'done','2026-06-26 19:44:19'),(35,1,1,15,'done','2026-06-26 19:46:25'),(36,1,2,15,'done','2026-06-26 19:49:52'),(37,2,1,15,'done','2026-06-27 15:19:30'),(38,2,1,15,'done','2026-06-27 15:23:36'),(39,2,1,15,'done','2026-06-27 15:33:31'),(40,3,1,15,'done','2026-06-27 16:30:39'),(41,2,3,15,'done','2026-06-27 16:45:40'),(42,2,3,15,'done','2026-06-27 16:51:03'),(43,3,2,15,'done','2026-06-27 17:03:36'),(44,3,1,15,'done','2026-06-27 17:30:49'),(45,3,1,15,'done','2026-06-27 17:33:24'),(46,1,2,15,'done','2026-06-27 17:33:26'),(47,1,2,15,'done','2026-06-27 18:08:46'),(48,1,2,15,'done','2026-06-27 18:12:39'),(49,3,1,15,'done','2026-06-27 18:21:14'),(50,3,1,15,'done','2026-06-27 18:26:24'),(51,1,2,15,'done','2026-06-27 18:27:58');
/*!40000 ALTER TABLE `led_events` ENABLE KEYS */;
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
