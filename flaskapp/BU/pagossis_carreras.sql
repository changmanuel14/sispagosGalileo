-- MySQL dump 10.13  Distrib 8.0.25, for Win64 (x86_64)
--
-- Host: localhost    Database: pagossis
-- ------------------------------------------------------
-- Server version	8.0.25

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
-- Table structure for table `carreras`
--

DROP TABLE IF EXISTS `carreras`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `carreras` (
  `idcarreras` int NOT NULL AUTO_INCREMENT,
  `codigo` varchar(8) NOT NULL,
  `carrera` varchar(100) NOT NULL,
  PRIMARY KEY (`idcarreras`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `carreras`
--

LOCK TABLES `carreras` WRITE;
/*!40000 ALTER TABLE `carreras` DISABLE KEYS */;
INSERT INTO `carreras` VALUES (1,'LBCQ','Licenciatura en Quimica Biologica'),(2,'LENQ','Licenciatura en Enfermeria'),(3,'LGSSQ','Licenciatura en Administracion y Gerencia de Servicios de Salud'),(4,'LOPTQ','Licenciatura en Optometria'),(5,'MGGQ','Maestria en Geriatria y Gerontologia'),(6,'MGSSQ','Maestria en Gestion de Sistemas de Salud'),(7,'MMFQ','Maestria en Medicina Familiar'),(8,'THDQ','Tecnico Universitario en Hemodialisis'),(9,'TLCQ','Tecnico Universitario en Laboratorio Clinico'),(10,'TOPTQ','Tecnico Universitario en Optometria'),(11,'TRADQ','Tecnico Universitario en Radiologia e Imagenes Diagnosticas'),(12,'TUEVQ','Tecnico Universitario en Enfermeria Veterinaria'),(13,'TVMMQ','Tecnico Universitario en Visita Medica y Mercadeo'),(14,'LADMOSQ','Licenciatura en Administración de Empresas');
/*!40000 ALTER TABLE `carreras` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2021-09-25 13:07:24
