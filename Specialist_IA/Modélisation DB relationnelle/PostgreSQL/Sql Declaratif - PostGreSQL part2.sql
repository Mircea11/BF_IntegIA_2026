-- -- SQL Exercises — Gaming Platform
-- -- Functions, Aggregations, GROUP BY / HAVING
-- -- Display all usernames in uppercase.
-- -- Display each username with its length.
-- -- Display each game with its release year.
-- -- Display profiles and replace NULL bio with 'No bio yet'.
-- -- Display each game with a price label: Free or Paid.
-- -- Display the total number of users.
-- -- Display the total number of games.
-- -- Display the average game price.
-- -- Display the total number of hours played.
-- -- Display the highest and lowest rating.
-- -- Display the number of users per country.
-- -- Display the number of games per publisher_id.
-- -- Display the average game price per publisher_id.
-- -- Display the total hours played per user_id.
-- -- Display the average hours played per user_id.
-- -- Display the total hours played per game_id.
-- -- Display the average rating per game_id.
-- -- Display the number of purchases per year.
-- -- Display the number of games released per year.
-- -- Display the number of games per price category:
-- -- Free if price = 0
-- -- Cheap if price < 30
-- -- Standard if price between 30 and 60
-- -- Expensive if price > 60
-- -- Display the number of paid games per publisher_id.
-- -- Display the average price per publisher_id for games released after '2015-01-01'.
-- -- Display only countries that have more than 1 user.
-- -- Display only user_id values with more than 300 total hours played.
-- -- Display only game_id values with an average rating >= 4.5.


-- SELECT u.username, p.bio, u.id, p.id
-- from users u, profiles p


-- --INNER (exclusive)
-- SELECT u.username, p.bio
-- FROM users as u
-- JOIN profiles as p on u.id = p.user_id;

-- SELECT u.username, p.bio
-- FROM users u
-- JOIN profiles p on u.id = p.user_id;

-- SELECT u.username, p.bio
-- FROM users u
-- JOIN profiles p on u.id = user_id;


-- SELECT g.title, p.name
-- FROM games g
-- JOIN publishers p ON g.publisher_id = p.id;

-- --alternative not using JOIN
-- SELECT u.username, p.bio
-- from users as u, profiles p
-- WHERE u.id = p.user_id

-- ---LEFT JOIN
-- SELECT u.username, p.bio, p.user_id
-- FROM users u
-- ----toujour from tqble principqle
-- LEFT JOIN profiles p ON u.id = p.user_id



-- SELECT u.username, p.bio, p.user_id
-- FROM users u
-- ----toujour from tqble principqle
-- RIGHT JOIN profiles p ON u.id = p.user_id


-- SELECT u.username, p.bio, p.user_id
-- FROM profiles p
-- LEFT join

-- -----SELF JOINT
-- SELECT g1.title, g2.title, g1.id, g2.id
-- FROM games g1
-- JOIN games g2 on g1.publisher_id = g2.publisher_id
-- WHERE g1.id < g2.id


-- --Jointures verticales
-- --no dublage
-- SELECT country from users
-- UNION 
-- SELECT country from publishers
-- --all
-- SELECT country from users
-- UNION ALL
-- SELECT country from publishers

-- SELECT country from users
-- INTERSECT
-- SELECT country from publishers


-- -- # SQL Exercises — Gaming Platform

-- -- ## JOINs and Advanced SELECT

-- -- ## Level 1 — Fundamentals

-- -- ### 1. Games and publishers

-- -- Display every game with its publisher.

-- -- Expected columns:

-- -- * `game_title`
-- -- * `publisher_name`


-- SELECT g.title as "game_title", p.name as "publisher_name"
-- from games g
-- JOIN publishers p on p.id = g.publisher_id

-- ---

-- -- ### 2. Owned games

-- -- Display every game owned by a user.

-- -- Expected columns:

-- -- * `username`
-- -- * `game_title`
-- -- * `hours_played`


-- SELECT u.username, g.title, p.hours_played 
-- from games g
-- join user_games p on p.game_id=g.id 
-- join users u on u.id = p.user_id 

-- SELECT g.title,
--        p.hours_played,
--        p.user_id,
--        u.username
-- FROM games AS g
-- JOIN user_games AS p ON p.game_id = g.id
-- JOIN users AS u ON u.id = p.user_id;

-- -- ---

-- -- ### 3. Users and profiles

-- -- Display all users with their profile information.

-- -- Users without a profile must still appear.

-- -- Expected columns:

-- -- * `username`
-- -- * `bio`
-- -- * `avatar_url`

-- -- ---


-- SELECT u.username, p.bio, p.avatar_url, u.id, p.user_id
-- from users u
-- left join profiles p on u.id =p.user_id
		


-- -- ### 4. Reviews

-- -- Display every review with the user and game information.

-- -- Expected columns:

-- -- * `username`
-- -- * `game_title`
-- -- * `rating`
-- -- * `comment`


-- SELECT u.username,
-- 		g.title,
-- 		r.rating,
-- 		r.comment
-- FROM reviews r
-- JOIN users u on r.user_id = u.id
-- JOIN games g on r.game_id = g.id
-- -- ---

-- -- ### 5. Publishers and games

-- -- Display all publishers with their games.

-- -- Publishers without games must still appear.

-- -- Expected columns:

-- -- * `publisher_name`
-- -- * `game_title`

-- -- ---

-- SELECT g.title, p.name
-- from publishers p
-- LEFT JOIN games g on p.id = g.publisher_id

-- -- ### 6. Users without games

-- -- Display all users who have never bought a game.

-- -- Expected columns:

-- -- * `username`

-- -- ---
-- SELECT u.username, count(u_g.game_id)
-- from users u
-- left join user_games u_g on u.id=u_g.user_id 
-- GROUP BY u.username
-- HAVING count(u_g.game_id) = 0

-- -- group by u.username, u_g.purchase_date
-- -- having u_g.purchase_date = NULL

-- -- SELECT * from user_games

-- -- ### 7. Game purchases

-- -- Display all users with the games they own and the corresponding purchase date.

-- -- Expected columns:

-- -- * `username`
-- -- * `game_title`
-- -- * `purchase_date`

-- SELECT u.username, g.title, p.purchase_date
-- from games g
-- join user_games p on p.game_id=g.id 
-- join users u on u.id = p.user_id 

-- -- ---

-- -- ### 8. Games without purchases

-- -- Display all games that have never been purchased.

-- SELECT g.title
-- from user_games u_g
-- right join games g on g.id=u_g.game_id 
-- GROUP BY g.title
-- HAVING count(u_g.game_id) = 0


-- -- -- Expected columns:

-- -- -- * `game_title`

-- -- -- ---

-- -- -- ### 9. Number of players per game

-- -- -- Display every game with its total number of players.

-- -- -- Games without players must still appear.

-- -- -- Expected columns:

-- -- -- * `game_title`
-- -- -- * `total_players`

-- -- ---

-- SELECT g.title as "game_title", 
-- 		count(ug.user_id)
-- FROM games g
-- LEFT JOIN user_games ug on ug.game_id = g.id
-- GROUP BY g.title

-- -- ### 10. Average rating per game

-- -- Display every reviewed game with its average rating.

-- -- Expected columns:

-- -- * `game_title`
-- -- * `average_rating`

-- SELECT g.title as "game_title",AVG(r.rating)::decimal(10,2)
-- FROM games as g
-- join reviews as r on g.id = r.game_id
-- Group by 
-- g.title

-- -- ---

-- ## Level 2 — Intermediate

-- ### 11. User activity summary

-- Display all users with the number of games they own and their total number of hours played.

-- Users without games must still appear.

-- Expected columns:

-- * `username`
-- * `games_owned`
-- * `total_hours_played`

-- ---

 -- SELECT u.username,
 -- 		count(g.title),
 --        coalesce(sum(p.hours_played),0)
             
 -- FROM games AS g
 -- JOIN user_games AS p ON p.game_id = g.id
 -- RIGHT JOIN users AS u ON u.id = p.user_id
 -- group by u.username
-- FROM users AS u
-- Left JOIN user_games as P on u.id = p.user_id
-- RIGHT JOIN games AS g ON p.game_id = g.id
-- GROUP BY u.username


-- ### 12. Publishers with several games

-- Display publishers that have published more than one game.

-- Expected columns:

-- * `publisher_name`
-- * `total_games`

-- ---

-- SELECT p.name, count(title)
-- FROM publishers as p
-- JOIN games as g on p.id = g.publisher_id
-- group by p.name
-- having count(title) > 1		

-- ### 13. Highly played games

-- Display games for which the total number of hours played exceeds 500.

-- Expected columns:

-- * `game_title`
-- * `total_hours_played`

-- ---

-- SELECT g.title, 
-- 	sum(ug.hours_played)
-- FROM games as g
-- join user_games as ug on g.id =ug.game_id
-- group by g.title 
-- having sum(ug.hours_played) > 500

-- ### 14. Active reviewers

-- Display users who have written more than one review.

-- Expected columns:

-- * `username`
-- * `reviews_written`

-- ---
-- SELECT u.username,
-- 		count(r.comment)
-- FROM users as u
-- join reviews as r on r.user_id = u.id
-- GROUP BY u.username
-- having count(r.comment) > 1

-- ### 15. Most-played games

-- Display the five games with the highest total number of hours played.

-- Expected columns:

-- * `game_title`
-- * `total_hours_played`

-- -- The most-played game must appear first.
-- SELECT g.title, 
-- sum(ug.hours_played)
-- FROM games as g
-- join user_games as ug on g.id =ug.game_id
-- group by g.title 
-- having sum(ug.hours_played) > 500
-- order by sum(ug.hours_played) desc
-- limit 5
-- -- ---

-- ## Level 3 — Advanced

-- ### 16. Detailed game review statistics

-- Display all games with their publisher and review statistics.

-- Games without reviews must still appear.

-- Expected columns:

-- * `game_title`
-- * `publisher_name`
-- * `total_reviews`
-- * `average_rating`

-- Order the result by average rating from highest to lowest.


-- SELECT g.title,
-- 		p.name,
-- 		count(r.rating),
-- 		avg(r.rating)::numeric(10,2)
-- FROM games as g
-- JOIN publishers as p on p.id=g.publisher_id
-- left JOIN reviews as r on g.id =r.game_id
-- group by g.title, p.name
-- order by avg(r.rating) desc
-- -- ---
-- SELECT 
--   g.title,
--   p.name,
--   COUNT(r.rating)            AS rating_count,
--   AVG(r.rating)::numeric(10,2) AS avg_rating
-- FROM games AS g
-- JOIN publishers AS p ON p.id = g.publisher_id
-- LEFT JOIN reviews AS r ON g.id = r.game_id
-- GROUP BY g.title, p.name
-- ORDER BY avg_rating DESC;

-- -- ### 17. Complete user activity

-- -- Display all users with the number of games they own and the number of reviews they have written.

-- Users without games or reviews must still appear.

-- Expected columns:

-- * `username`
-- * `games_owned`
-- * `reviews_written`

-- Be careful not to count the same game or review several times.

-- SELECT u.username, 
-- count  (distinct ug.game_id),
-- count (distinct r.id)
-- from users as u
-- LEFT JOIN user_games as ug on u.id = ug.user_id
-- LEFT JOIN reviews as r on u.id = r.user_id
-- GROUP BY u.username


-- ---

-- ### 18. Users loyal to a publisher

-- Display every user who owns at least two games from the same publisher.

-- Expected columns:

-- * `username`
-- * `publisher_name`
-- * `games_owned_from_publisher`

SELECT u.username, 
count  (distinct ug.game_id),
count (distinct p.id)
from users as u
LEFT JOIN user_games as ug on u.id = ug.user_id
LEFT JOIN reviews as r on u.id = p.user_id
GROUP BY u.username +
having 
-- ---



-- ### 19. Local publisher audiences

-- For each publisher, display the number of distinct players who come from the same country as the publisher.

-- Publishers without matching players must still appear.

-- Expected columns:

-- * `publisher_name`
-- * `publisher_country`
-- * `local_players`
-- SELECT p.name,
-- p.country,
-- count (distinct u.id)
-- FROM publishers p 
-- LEFT JOIN games g on g.publisher_id = p.id
-- Left JOIN user_games ug on ug.game_id = g.id
-- Left join users u on u.id = ug.user_id and p.country = u.country
-- WHERE 
-- GROUP BY p.name, p.country

-- ---

-- ### 20. Publishers ranked by playtime

-- Display all publishers with the total number of hours played across all their games.

-- Publishers whose games have never been played must still appear.

-- Expected columns:

-- * `publisher_name`
-- * `total_hours_played`

-- Order the result from the highest total playtime to the lowest.