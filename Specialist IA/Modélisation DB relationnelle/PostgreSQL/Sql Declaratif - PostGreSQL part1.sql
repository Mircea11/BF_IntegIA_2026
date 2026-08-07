-- DROP TABLE IF EXISTS reviews;
-- DROP TABLE IF EXISTS user_games;
-- DROP TABLE IF EXISTS profiles;
-- DROP TABLE IF EXISTS games;
-- DROP TABLE IF EXISTS publishers;
-- DROP TABLE IF EXISTS users;
 
-- CREATE TABLE users (
--     id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
--     username VARCHAR(50) NOT NULL UNIQUE CHECK (LENGTH(username) >= 3),
--     email VARCHAR(100) NOT NULL UNIQUE CHECK (email LIKE '%@%'),
--     country VARCHAR(50) NOT NULL,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );
 
-- CREATE TABLE profiles (
--     id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
--     user_id INT NOT NULL UNIQUE,
--     bio TEXT,
--     avatar_url TEXT,
--     birth_date DATE,
 
--     CONSTRAINT fk_profiles_users
--         FOREIGN KEY (user_id)
--         REFERENCES users(id)
--         ON DELETE CASCADE
-- );
 
-- CREATE TABLE publishers (
--     id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
--     name VARCHAR(100) NOT NULL UNIQUE,
--     country VARCHAR(50) NOT NULL
-- );
 
-- CREATE TABLE games (
--     id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
--     title VARCHAR(100) NOT NULL UNIQUE,
--     price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
--     release_date DATE,
--     publisher_id INT NOT NULL,
 
--     CONSTRAINT fk_games_publishers
--         FOREIGN KEY (publisher_id)
--         REFERENCES publishers(id)
-- );
 
-- CREATE TABLE user_games (
--     user_id INT NOT NULL,
--     game_id INT NOT NULL,
--     hours_played INT DEFAULT 0 CHECK (hours_played >= 0),
--     purchase_date DATE NOT NULL,
 
--     PRIMARY KEY (user_id, game_id),
 
--     CONSTRAINT fk_user_games_users
--         FOREIGN KEY (user_id)
--         REFERENCES users(id)
--         ON DELETE CASCADE,
 
--     CONSTRAINT fk_user_games_games
--         FOREIGN KEY (game_id)
--         REFERENCES games(id)
--         ON DELETE CASCADE
-- );
 
-- CREATE TABLE reviews (
--     id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
--     user_id INT NOT NULL,
--     game_id INT NOT NULL,
--     rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
--     comment TEXT CHECK (LENGTH(comment) >= 5),
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 
--     CONSTRAINT fk_reviews_users
--         FOREIGN KEY (user_id)
--         REFERENCES users(id)
--         ON DELETE CASCADE,
 
--     CONSTRAINT fk_reviews_games
--         FOREIGN KEY (game_id)
--         REFERENCES games(id)
--         ON DELETE CASCADE,
 
--     CONSTRAINT unique_user_game_review
--         UNIQUE (user_id, game_id)
-- );
 
-- INSERT INTO users (username, email, country) VALUES
-- ('Davit', 'davit@test.com', 'Belgium'),
-- ('Sarah', 'sarah@test.com', 'France'),
-- ('Lucas', 'lucas@test.com', 'Belgium'),
-- ('Emma', 'emma@test.com', 'Canada'),
-- ('Noah', 'noah@test.com', 'Germany'),
-- ('Lina', 'lina@test.com', 'Belgium'),
-- ('Tom', 'tom@test.com', 'USA'),
-- ('Julie', 'julie@test.com', 'France'),
-- ('Alex', 'alex@test.com', 'USA'),
-- ('Mike', 'mike@test.com', 'UK');
 
-- INSERT INTO profiles (user_id, bio, avatar_url, birth_date) VALUES
-- (1, 'Metalhead and Souls fan', 'avatar1.png', '2002-03-02'),
-- (2, 'Competitive FPS player', 'avatar2.png', '1998-07-10'),
-- (3, 'Indie games lover', 'avatar3.png', '2001-11-15'),
-- (4, 'Streamer and content creator', 'avatar4.png', '1999-01-20'),
-- (5, 'Hardcore RPG gamer', 'avatar5.png', '1995-05-05');
 
-- INSERT INTO publishers (name, country) VALUES
-- ('FromSoftware', 'Japan'),
-- ('CD Projekt', 'Poland'),
-- ('Valve', 'USA'),
-- ('Rockstar Games', 'USA'),
-- ('Riot Games', 'USA'),
-- ('Activision', 'USA'),
-- ('Naughty Dog', 'USA'),
-- ('Mojang', 'Sweden'),
-- ('Epic Games', 'USA');
 
-- INSERT INTO games (title, price, release_date, publisher_id) VALUES
-- ('Elden Ring', 59.99, '2022-02-25', 1),
-- ('Dark Souls 3', 39.99, '2016-04-12', 1),
-- ('Cyberpunk 2077', 49.99, '2020-12-10', 2),
-- ('Counter Strike 2', 0.00, '2023-09-27', 3),
-- ('GTA V', 29.99, '2013-09-17', 4),
-- ('League of Legends', 0.00, '2009-10-27', 5),
-- ('Call of Duty MW3', 79.99, '2023-11-10', 6),
-- ('The Last of Us', 69.99, '2022-09-02', 7),
-- ('Minecraft', 26.95, '2011-11-18', 8),
-- ('Fortnite', 0.00, '2017-07-21', 9),
-- ('Red Dead Redemption 2', 59.99, '2018-10-26', 4);
 
-- INSERT INTO user_games (user_id, game_id, hours_played, purchase_date) VALUES
-- (1, 1, 220, '2024-01-10'),
-- (1, 4, 450, '2023-11-01'),
-- (1, 5, 180, '2022-08-20'),
 
-- (2, 3, 95, '2024-03-15'),
-- (2, 6, 800, '2020-06-01'),
-- (2, 7, 120, '2024-01-20'),
 
-- (3, 2, 140, '2023-07-22'),
-- (3, 9, 300, '2022-12-05'),
 
-- (4, 8, 40, '2024-04-18'),
-- (4, 11, 110, '2024-01-03'),
 
-- (5, 1, 350, '2024-02-11'),
-- (5, 8, 70, '2024-03-10'),
 
-- (6, 10, 500, '2021-07-14'),
-- (6, 6, 1000, '2019-09-09'),
 
-- (7, 4, 1300, '2021-06-01'),
 
-- (8, 3, 35, '2024-05-02'),
 
-- (9, 5, 220, '2022-10-10'),
 
-- (10, 9, 600, '2020-05-05');
 
-- INSERT INTO reviews (user_id, game_id, rating, comment) VALUES
-- (1, 1, 5, 'Absolute masterpiece'),
-- (2, 6, 4, 'Still addictive after years'),
-- (3, 2, 5, 'Amazing boss fights'),
-- (4, 11, 5, 'Best story ever'),
-- (5, 1, 5, 'Fantastic exploration'),
-- (6, 10, 4, 'Very fun with friends'),
-- (7, 4, 5, 'Competitive and intense'),
-- (8, 3, 3, 'Good but buggy'),
-- (9, 5, 5, 'Classic game'),
-- (10, 9, 5, 'Infinite creativity');

-- INSERT INTO users (username, email, country) VALUES
-- ('Nina', 'nina@test.com', 'Belgium'),
-- ('Oscar', 'oscar@test.com', 'Spain'),
-- ('Yuki', 'yuki@test.com', 'Japan'),
-- ('Maya', 'maya@test.com', 'USA'),
-- ('Chris', 'chris@test.com', 'UK');

-- INSERT INTO profiles (user_id, bio, avatar_url, birth_date) VALUES
-- (11, NULL, NULL, '2000-06-12'),
-- (12, 'Casual gamer', NULL, '1997-09-30'),
-- (13, 'JRPG and Souls enjoyer', 'avatar13.png', '1996-02-14');

-- INSERT INTO publishers (name, country) VALUES
-- ('Ubisoft', 'France');

-- INSERT INTO games (title, price, release_date, publisher_id) VALUES
-- ('Bloodborne', 19.99, '2015-03-24', 1),
-- ('Sekiro', 59.99, '2019-03-22', 1),
-- ('Bully', 14.99, '2006-10-17', 4),
-- ('Valorant', 0.00, '2020-06-02', 5),
-- ('Warzone', 0.00, '2020-03-10', 6),
-- ('Uncharted 4', 39.99, '2016-05-10', 7),
-- ('Hades', 24.99, '2020-09-17', 3),
-- ('Portal 2', 9.99, '2011-04-19', 3);

-- INSERT INTO user_games (user_id, game_id, hours_played, purchase_date) VALUES

-- (1, 6, 120, '2020-01-12'),
-- (1, 7, 240, '2024-02-01'),
-- (1, 9, 90, '2021-04-10'),
-- (1, 12, 160, '2022-02-02'),
-- (1, 15, 80, '2023-04-04'),

-- (2, 4, 300, '2023-09-28'),
-- (2, 10, 900, '2018-08-08'),
-- (2, 15, 450, '2022-07-07'),
-- (2, 16, 700, '2021-02-02'),

-- (3, 4, 150, '2023-10-01'),
-- (3, 6, 500, '2020-03-03'),
-- (3, 10, 250, '2018-01-01'),
-- (3, 15, 200, '2021-01-01'),
-- (3, 16, 100, '2022-05-05'),

-- (4, 18, 60, '2020-11-11'),

-- (5, 12, 400, '2022-06-06'),
-- (5, 13, 180, '2023-03-03'),

-- (6, 4, 700, '2023-11-11'),
-- (6, 16, 350, '2022-10-10'),
-- (6, 17, 40, '2024-04-04'),

-- (7, 6, 1200, '2019-09-09'),
-- (7, 16, 850, '2020-04-04'),

-- (8, 11, 100, '2023-08-08'),
-- (8, 14, 40, '2023-01-01'),

-- (9, 1, 150, '2024-01-01'),
-- (9, 3, 90, '2024-02-02'),
-- (9, 4, 300, '2024-03-03'),
-- (9, 6, 600, '2024-04-04'),
-- (9, 7, 80, '2024-05-05'),

-- (12, 17, 25, '2024-06-06'),

-- (13, 1, 500, '2024-01-01'),
-- (13, 2, 350, '2024-01-02'),
-- (13, 12, 250, '2024-01-03'),
-- (13, 13, 300, '2024-01-04'),

-- (14, 5, 70, '2024-02-02'),
-- (14, 8, 30, '2024-03-03'),

-- (15, 18, 10, '2024-05-05');

-- INSERT INTO reviews (user_id, game_id, rating, comment) VALUES
-- (1, 7, 4, 'Fun but sweaty'),
-- (1, 9, 5, 'Blocky perfection'),
-- (2, 4, 5, 'Best competitive FPS'),
-- (2, 10, 4, 'Chaotic but fun'),
-- (3, 6, 4, 'Still toxic but addictive'),
-- (4, 18, 5, 'Beautiful adventure'),
-- (5, 12, 5, 'Gothic masterpiece'),
-- (5, 13, 5, 'Parry god simulator'),
-- (6, 17, 5, 'Insane roguelike'),
-- (7, 16, 4, 'Battle royale classic'),
-- (8, 14, 4, 'Old but gold'),
-- (9, 3, 4, 'Much better now'),
-- (9, 7, 2, 'Too expensive for what it is'),
-- (12, 17, 5, 'Perfect indie game'),
-- (13, 1, 5, 'Peak fantasy RPG'),
-- (14, 5, 5, 'Still iconic'),
-- (15, 6, 1, 'Not my thing');

-- SELECT * FROM games
-- SELECT titl

-- SELECT username, country
-- FROM users
-- WHERE country IN ( 'Belgium', 'France', 'UK')
-- -- is the same as WHERE country = 'Belgium', or country= 'France', or country = 'UK'

-- -- exercise1
-- -- exercise1

-- SQL Exercises — Gaming Platform

-- SELECT * FROM users

-- 1.Display all users.

-- SELECT username
-- FROM users

-- ---
-- 2.
-- Display only the usernames and countries of all users.

-- SELECT username, country
-- FROM users

-- ---
-- 3.
-- Display all games.

-- SELECT * FROM games

-- --or

-- SELECT title FROM games
-- 4.
-- Display only the title and price of all games.

-- SELECT title, price FROM games
-- ---
-- 5.
-- Display all games that cost more than 40€.

-- SELECT * FROM games
-- WHERE price > 40
-- ---
-- 6.
-- Display all games that cost less than 50€.

-- SELECT * FROM games
-- WHERE price < 50
-- ---
-- 7.
-- Display all free games.

-- SELECT title,price FROM games
-- WHERE price <= 0
-- ---
-- 8.
-- Display all users coming from Belgium.

-- SELECT username, country
-- FROM users
-- WHERE country = 'Belgium'
-- ---
-- 9.
-- Display all users who are not from Belgium.

-- SELECT username, country
-- FROM users
-- WHERE country != 'Belgium'
-- --WHERE country ILIKE 'belgium'

-- --or

-- SELECT username, country
-- FROM users
-- WHERE NOT country = 'Belgium'

-- --WHERE NOT country ILIKE 'belgium' 
-- --gere la case de mot
-- ---
-- 10.
-- Display all publishers from the USA.

-- SELECT * from publishers

-- SELECT name, country from publishers WHERE country = 'USA'
-- ---
-- 11.
-- Display all games released after 2020.

-- SELECT * from games WHERE release_date > '2020-12-31'
-- ---
-- 12.
-- Display all games released before 2020.


-- SELECT * from games WHERE release_date < '01/01/2020'

-- -- 01/01/2020 marche aussi
-- ---
-- 13.
-- Display all games ordered by price in descending order.

-- SELECT * from games ORDER BY price DESC
-- ---
-- 14.
-- Display all games ordered by release date from newest to oldest.

-- SELECT * from games ORDER BY release_date DESC

-- ---
-- 15.
-- Display all usernames ordered alphabetically.

-- SELECT * FROM users ORDER BY username ASC

-- 16.
-- Display all games whose title contains "Dark".

-- SELECT * FROM games WHERE title ILIKE '%Dark%'

-- ---
-- 17.
-- Display all games whose title starts with "C".

-- SELECT * FROM games WHERE title LIKE 'C%'
-- ---
-- 18.
-- Display all users whose username contains the letter "a".

-- SELECT * FROM users WHERE username LIKE '%a%'

-- ---
-- 19.
-- Display all reviews with a rating of 5.

-- SELECT * FROM reviews WHERE rating = 5
-- ---
-- 20.
-- Display all reviews created after `2024-01-01`.

-- SELECT * FROM reviews WHERE created_at > '2024-01-01'
-- ---
-- 21.
-- Display all games with a price between 20€ and 60€.

-- SELECT * FROM games WHERE price BETWEEN 20 AND 60

-- ---
-- 22.
-- Display all users coming from Belgium or France.

-- SELECT * FROM users WHERE country = 'Belgium' or country = 'France'

-- SELECT * FROM users WHERE country in ('Belgium', 'France')
-- cqse sensitive
-- SELECT *
-- FROM users
-- WHERE country ILIKE 'belgium' OR country ILIKE 'france';

-- ---
-- 23.
-- Display all games that are not free.

-- SELECT * FROM games WHERE price > 0

-- ---
-- 24.
-- Display all games ordered alphabetically by title.

-- SELECT * FROM games ODER by title ASC

-- ---
-- 25.
-- Display all publishers ordered alphabetically.

-- SELECT * FROM publishers ORDER BY name ASC
-- ---
-- 26.
-- Display all games where the title ends with "2".

-- SELECT * FROM games WHERE title LIKE '%2'
-- SELECT * FROM gams WHERE price::varchar(10) LIKE '%2'
-- ---
-- 27.
-- Display all users created after a specific date.


-- SELECT * from users 
-- WHERE created_at > '2026-07-17'
-- ---
-- 28.
-- Display all games released between 2015 and 2022.

-- SELECT * FROM games
-- WHERE release_date BETWEEN '2015-01-01' and '2022-12-31'
-- ---
-- 29.
-- Display all reviews where the comment contains the word "best".

-- SELECT * from reviews WHERE comment ILIKE '%best%'
-- ---
-- 30.
-- Display all games whose price is exactly 59.99€.

-- SELECT * FROM games
-- WHERE price = 59.99


-- Les fonction

-- DATE_PART(  )
-- EXTRACT(  )
-- SELECT CAST(10.0/3 as decimal(10.2));
-- FROM games

-- SELECT price::int
-- FROM games;


-- SELECT EXTRACT(YEAR FROM release_date)
-- from games

-- SELECT DATE_PART (day, release_date )
-- from games


-- --TO CHAR
-- SELECT TO_CHAR 5 release_date, (DD-MM-YY)

-- Format Description
-- YYYY Year as a numeric, 4-digit value
-- YY Year as a numeric, 2-digit value
-- MM Numeric month name (01 to 12)
-- MONTH Month name in full (January to December)
-- DD Day of the month as a numeric value (01 to 31)
-- D Day of the week as a numeric value (1 to 7 – Sunday to Saturday)
-- DI Day of the week as a numeric value (1 to 7 – Monday to Sunday)
-- HH Hour (00 to 12)
-- HH12 Hour (00 to 12)
-- HH24 Hour (00 to 23)
-- MI Minutes (00 to 59)
-- SS Seconds (00 to 59)

--date extraction
--SELECT NOW(),CURRENT_TIME,CURRENT_DATE,CURRENT_TIMESTAMP

-- SELECT SUBSTRING('Basinger' FROM 4 FOR 3)
-- AS "Caractères 4, 5 et 6";

-- SELECT title, LEFT (title,5)
-- FROM games
-- WHERE id =4;

-- SELECT UPPER(title)
-- from games;

-- SELECT title, REPLACE(title, 'a','!')
-- from games;

-- SELECT  LTRIM('     n    ')
-- SELECT  RTRIM('      n    ')
-- SELECT  TRIM('       n    ')



-- -- Les fonctions : Agrégations

-- SELECT * 
-- FROM
-- games

-- SELECT count(*)
-- from games;


-- Les valeurs « NULL » ne sont 
-- prises en compte que dans l’utilisation du « COUNT(*) 

-- SELECT MAX(price)
-- FROM games

-- SELECT *
-- FROM games

-- SELECT MIN(price) as "Le prix le plus bqs", COUNT(title)
-- FROM games
-- WHERE price >0


-- SELECT SUM(price) as "Somme du prix de tout les jeux",
-- 	COUNT(title) as "Le nombre total de jeux",
-- 	MAX(price) as "Le prix le plus haut",
-- 	AVG (price) as "La moyene du prix des jeux"
-- 	FROM games


--Les fonction: CASE

-- SELECT title,price,
-- 	CASE
-- 	WHEN price = 0 THEN 'FREE(pay to win)'
-- 	WHEN price BETWEEN 1 AND 20 THEN 'CA PASSE, pas chere'
-- 	WHEN price BETWEEN 21 AND 50 THEN 'CA commence a couter'
-- 	ELSE 'Cest grave chere'
-- END as "Comment"
-- FROM games;


-- SELECT username, country,
-- 	CASE country
-- 		WHEN 'Belgium' THEN 'BELGE'
-- 		WHEN 'France' THEN ' France'
-- 		ELSE 'AUTRE'
-- 	END as "Nationalite"
-- from users;

-- SELECT username, country,
-- 	CASE country
-- 		WHEN 'Belgium' THEN 'BELGE'
-- 		WHEN 'France' THEN ' France'
-- 		ELSE NULL
-- 	END as "Nationalite"
-- from users;

-- SELECT username, country, NULLIF(country, 'Belgium')
-- from users
		
------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- SQL Exercises — Gaming Platform
-- Functions, Aggregations, GROUP BY / HAVING
-- 1. Display all usernames in uppercase.
SELECT upper (username),username
FROM users

-- 2. Display each username with its length.

SELECT username, length(username)
FROM users

-- 3. Display each game with its release year.


--SELECT Title, YEAR(CAST(release_date as date))

SELECT title, EXTRACT(YEAR FROM (release_date))
FROM games
Limit 3

-- 4. Display profiles and replace NULL bio with 'No bio yet'.

-- SELECT *
-- FROM profiles
SEELCT COALESCE (bio, 'no bio yet'), id
from profiles


SELECT *,
       CASE
         WHEN bio IS NULL THEN 'No bio yet'
         ELSE bio
       END AS bio_display
FROM profiles;

-- SELECT title, REPLACE(title, 'a','!')
-- from games;


-- 5. Display each game with a price label: Free or Paid.

SELECT *,
		CASE
			WHEN PRICE = 0 THEN 'Free'
			ELSE 'Paid'
		END AS Label_Price	
FROM games

-- 6. Display the total number of users.
SELECT COUNT(*)

FROM USERS


-- 7. Display the total number of games.
SELECT count(title)
FROM games
-- 8. Display the average game price.

SELECT AVG(price)
FROM games
-- 9. Display the total number of hours played.

SELECT SUM(hours_played) 
from user_games

-- 10. Display the highest and lowest rating.

Select min(rating) as "lowest",max(rating) as "highest"
FROM reviews

-- 11. Display the number of users per country.

SELECT  count(users) as "Number_of_Users",country
FROM users
GROUP by country

-- 12. Display the number of games per publisher_id.

SELECT count(title) as "Number of games", publisher_id
FROM games
GROUP by publisher_id
-- Display the average game price per publisher_id.
-- Display the total hours played per user_id.
-- Display the average hours played per user_id.
-- Display the total hours played per game_id.
-- Display the average rating per game_id.
-- Display the number of purchases per year.

-- 19. Display the number of games released per year.
SELECT 


-- 20. Display the number of games per price category:
-- Free if price = 0
-- Cheap if price < 30
-- Standard if price between 30 and 60
-- Expensive if price > 60

SELECT 
	CASE 
		WHEN price = 0 then 'free'
		when price <30 then 'chep'
		--when price between 30 and 60 
		when price < 60 then 'Standard'
		else 'expensive'
	end as "Price category", count(*)
from games
group by 1



-- 21. Display the number of paid games per publisher_id.

SELECT count(price)::decimal(10,2), publisher_id
from games
group by publisher_id
having count(price) !=0
-- 22.Display the average price per publisher_id for games released after '2015-01-01'.

SELECT avg(price), publisher_id, release_date
from games

group by publisher_id, release_date
having release_date > '2015-01-01'


SELECT* 
from games
-- 23. Display only countries that have more than 1 user.

SELECT country, count(id)
from users
group by country
having count(id) > 2

SELECT count(country )
FROM users
--24. Display only user_id values with more than 300 total hours played.

SELECT user_id, sum(hours_played)
from user_games
Group by user_id
having sum(hours_played) > 300

-- 25. Display only game_id values with an average rating >= 4.5.
SELECT cast(AVG(rating), game_id
from reviews
group by game_id
having AVG(rating) >= 4.5


SELECT *
FROM reviews