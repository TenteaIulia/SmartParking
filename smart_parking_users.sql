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
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `full_name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` enum('user','admin') DEFAULT 'user',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `unique_email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'Ana Popescu','ana@email.com','scrypt:32768:8:1$AKL6Z8sZ71Ypu6RI$3b8f80f71955da59b0f2ed946c7afcaf05c91e699fe3f5ff606787e0298d7482faf24d47a2da3380186a0b20598f8c4ee59cb809a5bcdb82577562c75168e440','user','2026-03-12 15:13:46'),(2,'Iulia Tentea','tenteaiuliana@yahoo.com','scrypt:32768:8:1$clUZs6kONfzHgNXp$c47e58164b4913120cf4a82f1361d6e7d3f812d544ba2ffda428c16466b7b8fbbc48f911727271593e81ec4962eb02e37352734c5637e23b15160871dd741847','user','2026-03-14 08:04:49'),(3,'Bogdan Lupsa','lupsa.bogdan@gmail.com','scrypt:32768:8:1$TrfyD9lmYQc2qtQF$bc61fffe9da387632231e18deeb7cec613d9c501abcbbf90c5451bfe108bb05b77bdaf51076291cfbbae0dc2c8249acd8da3c626d051b84651e9c2acb05105ad','user','2026-03-14 08:13:33'),(4,'Ana','ana@yahoo.com','scrypt:32768:8:1$ZZlO71OPbu72y03A$a218901c8bfa26343404fe49152db821983ea679182440cf9985828774b849380694039bdeb729b725166ff5ef68c757d7360f3eda7f0970195cef95d29c6dce','user','2026-03-14 08:17:43'),(5,'ContAdmin','contAdmin@gmail.com','scrypt:32768:8:1$31hqiNQgLOqknM27$f4f1ae4a6a8c35a68b74f50b51f403a4a8f73aa54589cd72c48ded16ba37c7efb56157b852d9120410a0dcf0fa3da6f4187d30e0193e875a22705721377c1b8d','admin','2026-03-18 10:52:04'),(6,'Ioana','ioana@yahoo.com','scrypt:32768:8:1$IJmVZ96LXihyTltI$5894ec4ff97942ac44ec0f98fe6dc385c491ba1f90e99e25567d2c5812ed351d5f3e1d4307cc6524a2e5f6d3722f6b6f8ac13ce28767d664314a6bf2ae047005','user','2026-03-20 15:18:34'),(7,'Anca Ianos','anca@yahoo.com','scrypt:32768:8:1$NKatxmKdfNRsD0rf$c25f178bb30eb27cb0c57e3aced9cf7e2410d1182a438a5bd11fcb2b4433c75f022f43393ec9ee7d659e30d9f84fd57f1ca3e14b98e13b665335bcb1e6ae3dc3','user','2026-06-16 23:04:12');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-07-02 10:45:32
