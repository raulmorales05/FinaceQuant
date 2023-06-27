drop database BTC;
CREATE database BTC;
use BTC;
DROP TABLE IF EXISTS tradess;
FLUSH TABLES `tradess` ;
CREATE TABLE IF NOT EXISTS BTC.tradess (
  	`Date`			date,
  	`Open` 		DECIMAL(10,2),
	`High`		DECIMAL(10,2),
    `Low`			DECIMAL(10,2),
    `Close`		DECIMAL(10,2),
    `Volume`		DECIMAL(10,2),
    `Balance`		DECIMAL(10,2),
    `OBV`			DECIMAL(20,2),
    `cruce`		DECIMAL(10,2),
    `rsi`			DECIMAL(10,2),
    `sigma`		DECIMAL(10,2),
    `OBV_osc`		DECIMAL(10,2),
    `cruce_volumen`	DECIMAL(10,2),
    `cruce_precio` DECIMAL(10,2),
    `cruce_50_200`	DECIMAL(10,2),
    `cruce_20_100`	DECIMAL(10,2),
    `rsi_media`		DECIMAL(10,2),
    `OBV_media`		DECIMAL(10,2),
    `gatillo`			varchar(40)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;	
LOAD DATA INFILE 'C:\\ProgramData\\MySQL\\MySQL Server 8.0\\Uploads\\actionsBTC.csv' 
INTO TABLE BTC.tradess FIELDS TERMINATED BY ',' ENCLOSED BY ',' ESCAPED BY '' LINES TERMINATED BY '\n' IGNORE 1 LINES;


