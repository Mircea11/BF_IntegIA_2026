CREATE TABLE USER_GAMES	(
	userID int, 
	gameID int,
	hours_played int,
	purchase_date timestamp,
	CONSTRAINT FK_UserID FOREIGN KEY(userID)
		REFERENCES "USER"(id) ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT FK_gameID FOREIGN KEY(gameID)
		REFERENCES GAMES(id) ON DELETE CASCADE ON UPDATE CASCADE

--in case you need to change the type of the column
ALTER TABLE USER_GAMES ALTER COLUMN purchase_date TYPE date;


--section(section_id)
);
CREATE TABLE "USER" (
	id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	username varchar(50) NOT NULL UNIQUE,
	email varchar(50) NOT NULL UNIQUE,
	--email varchar(50) NOT NULL UNIQUE CHECK(email LIKE '%@%'),
	country varchar(50) DEFAULT 'Moldova', 
	created_at timestamp DEFUALT CURRENT_TIMESTAMP,
	CONSTRAINT chk_email CHECK (email LIKE '%@%'),
	CONSTRAINT chk_country_format CHECK (country ~ '^[A-Za-z][A-Za-z -]*$')
	
);

ALTER TABLE "USER"
ALTER COLUMN created_at
SET DEFAULT CURRENT_TIMESTAMP;

CREATE TABLE GAMES (
	id int  GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	title varchar(50) NOT NULL UNIQUE,
	price decimal (9,2 ),
	released_date timestamp,
	publisher_id int,
	CONSTRAINT FK_publisher_id FOREIGN KEY(publisher_id)
		REFERENCES PUBLISHER(id) ON DELETE CASCADE ON UPDATE CASCADE
);

/* in case you forgot qdding the GENERATED ALWAYS AS IDENTITY */
ALTER TABLE PUBLISHER ALTER COLUMN price add CHEC ;

CREATE TABLE PUBLISHER (
	id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	name varchar(50),
	country varchar(50) DEFAULT 'Moldova'
);
--- in caase you need to add more constraint
ALTER TABLE PUBLISHER ADD CONSTRAINT chk_country_format CHECK (country ~ '^[A-Za-z][A-Za-z -]*$')
	;
ALTER TABLE PUBLISHER 
ALTER COLUMN name TYPE varchar(150);


CREATE TABLE PROFIL (
	id int PRIMARY KEY GENERATED ALWAYS AS IDENTITY, 
	userID int,
	io varchar(50),
	avatar varchar(50),
	dob date,
	CONSTRAINT FK_UserID FOREIGN KEY(userID)
		REFERENCES "USER"(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- correction 
ALTER TABLE profil
RENAME COLUMN io TO bio;

ALTER TABLE profil
ALTER COLUMN avatar TYPE varchar(1000);


CREATE TABLE REVIEW (
	id int PRIMARY KEY GENERATED ALWAYS AS IDENTITY, 
	userID int,
	gameID int,
	rating int,
	comment varchar(50),
	creation_date timestamp,

	CONSTRAINT FK_UserID FOREIGN KEY(userID)
		REFERENCES "USER"(id) ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT FK_gameID FOREIGN KEY(gameID)
		REFERENCES GAMES(id) ON DELETE CASCADE ON UPDATE CASCADE
		)
