import sqlite3

con = sqlite3.connect("throwersprs.db")
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS athletes(id INTEGER NOT NULL, name NOT NULL, PRIMARY KEY (id))")
cur.execute("CREATE TABLE IF NOT EXISTS events(id INTEGER NOT NULL, name NOT NULL, PRIMARY KEY (id))")
cur.execute("CREATE TABLE IF NOT EXISTS prs(id INTEGER NOT NULL, athleteID INTEGER NOT NULL, eventID NOT NULL, mark DOUBLE, PRIMARY KEY (id) ,FOREIGN KEY (athleteID) REFERENCES athletes (athletes_id), FOREIGN KEY (eventID) REFERENCES events (events_id))")

cur.execute("insert into events values(Null,'SP'),(Null,'WT'),(Null,'DT'),(Null,'HT'),(Null,'JT')")