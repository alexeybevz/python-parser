CREATE TABLE Users (
	  id integer identity(1,1) NOT NULL
	, userIdLog bigint
	, ipAddress nvarchar(15) NOT NULL
	, country nvarchar(50)
	, PRIMARY KEY (id)
)
GO

CREATE TABLE UserAction (
	  id integer identity(1,1) NOT NULL
	, userId integer NOT NULL FOREIGN KEY REFERENCES Users(id)
	, action nvarchar(200) NOT NULL
	, actionDate datetime NOT NULL
	, PRIMARY KEY (id)
)
GO

CREATE TABLE Cart (
	  id integer NOT NULL
	, userId integer NOT NULL FOREIGN KEY REFERENCES Users(id)
	, payDate datetime
	, PRIMARY KEY (id)
)
GO

CREATE TABLE Good (
	  id integer NOT NULL
	, name nvarchar(100) NOT NULL
	, category nvarchar(100) NOT NULL
	, PRIMARY KEY (id)
)
GO

CREATE TABLE CartItem (
	  cartId integer NOT NULL FOREIGN KEY REFERENCES Cart(id)
	, goodId integer NOT NULL FOREIGN KEY REFERENCES Good(id)
	, amount decimal(18,2) NOT NULL
)
GO

--delete from UserAction
--delete from Cart
--delete from Users
--delete from CartItem
--delete from Good

--select * from UserAction
--select * from Users
--select * from CartItem
--select * from Good
--select * from Cart