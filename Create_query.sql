CREATE DATABASE IF NOT EXISTS tennis_db;
USE tennis_db;
CREATE TABLE Categories(
		category_id VARCHAR(50) PRIMARY KEY,
        category_name VARCHAR(100) NOT NULL);
        
CREATE TABLE Competitions(
	    competition_id VARCHAR(50) PRIMARY KEY,
        competition_name VARCHAR(255) NOT NULL,
        parent_id VARCHAR(50) NULL,
        `type` VARCHAR(20) NOT NULL,
        gender VARCHAR(10) NOT NULL,
        category_id VARCHAR(50),
        FOREIGN KEY(category_id) REFERENCES Categories(category_id));
        
CREATE TABLE Complexes(
		complex_id VARCHAR(50) PRIMARY KEY,
        complex_name VARCHAR(100) NOT NULL);
        
CREATE TABLE Venues(
    venue_id VARCHAR(50) PRIMARY KEY,
    venue_name VARCHAR(100) NOT NULL,
    city_id VARCHAR(50),
    city_name VARCHAR(100) NOT NULL,
    country_name VARCHAR(100) NOT NULL,
    country_code CHAR(3) NOT NULL,
    timezone VARCHAR(100) NOT NULL,
    complex_id VARCHAR(50),
    FOREIGN KEY (complex_id) REFERENCES Complexes(complex_id));

CREATE TABLE Competitors(
	   competitor_id VARCHAR(50) PRIMARY KEY,
       name VARCHAR(100) NOT NULL,
       country VARCHAR(50) NOT NULL,
       country_code CHAR(3) NOT NULL,
       abbreviation VARCHAR(10) NOT NULL);

CREATE TABLE Competitor_Rankings(
		rank_id INT PRIMARY KEY AUTO_INCREMENT,
        `rank` INT NOT NULL,
        movement INT NOT NULL,
        points INT NOT NULL,
        competitions_played INT NOT NULL,
        competitor_id VARCHAR(50),
        tour VARCHAR(20),
        gender VARCHAR(10),
        year INT,
		week INT,
        FOREIGN KEY(competitor_id) REFERENCES Competitors(competitor_id));

-- For check Table datatype and rows.  
USE tennis_db;
DESCRIBE categories;
DESCRIBE competitor_rankings;
SHOW CREATE TABLE competitor_rankings;


SELECT 'categories', COUNT(*) FROM categories
UNION ALL SELECT 'competitions', COUNT(*) FROM competitions
UNION ALL SELECT 'complexes', COUNT(*) FROM complexes
UNION ALL SELECT 'venues', COUNT(*) FROM venues
UNION ALL SELECT 'competitors', COUNT(*) FROM competitors
UNION ALL SELECT 'competitor_rankings', COUNT(*) FROM competitor_rankings;



        
        
        