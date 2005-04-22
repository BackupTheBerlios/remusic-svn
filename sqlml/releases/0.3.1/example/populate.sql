USE orderdb;

TRUNCATE TABLE items;
TRUNCATE TABLE orders;
TRUNCATE TABLE itemorders;

INSERT INTO items VALUES
	(NULL, 'spam', 6.75),
	(NULL, 'egg', 20);

INSERT INTO orders VALUES
	(NULL, 'John'),
	(NULL, 'Michael'),
	(NULL, 'Graham');

INSERT INTO itemorders VALUES
	(1, 1, 1),
	(1, 2, 1),
	(2, 1, 2),
	(2, 2, 1),
	(3, 1, 3),
	(3, 2, 1);
