CREATE TABLE `equivalencia` (
  `idequivalencia` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(200) DEFAULT NULL,
  `carnet` varchar(45) DEFAULT NULL,
  `idcarrera` int DEFAULT NULL,
  `curso` varchar(200) DEFAULT NULL,
  `semestre` varchar(45) DEFAULT NULL,
  `seccion` varchar(45) DEFAULT NULL,
  `catedratico` varchar(200) DEFAULT NULL,
  `idestado` int DEFAULT NULL,
  `notificacion1` int DEFAULT NULL,
  `notificacion2` int DEFAULT NULL,
  `notificacion3` int DEFAULT NULL,
  `terminado` int DEFAULT NULL,
  PRIMARY KEY (`idequivalencia`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `estado` (
  `idestado` int NOT NULL AUTO_INCREMENT,
  `estado` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`idestado`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;