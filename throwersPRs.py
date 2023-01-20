import sqlite3
from urllib.request import urlopen
from bs4 import BeautifulSoup

con = sqlite3.connect("throwersprs.db")
cur = con.cursor()
#Add the tables if they do not exists
cur.execute("CREATE TABLE IF NOT EXISTS athletes(id INTEGER NOT NULL, name NOT NULL, PRIMARY KEY (id))")
cur.execute("CREATE TABLE IF NOT EXISTS events(id INTEGER NOT NULL, name NOT NULL, PRIMARY KEY (id))")
cur.execute("CREATE TABLE IF NOT EXISTS prs(id INTEGER NOT NULL, athleteID INTEGER NOT NULL, eventID NOT NULL, mark DOUBLE, PRIMARY KEY (id) ,FOREIGN KEY (athleteID) REFERENCES athletes (athletes_id), FOREIGN KEY (eventID) REFERENCES events (events_id))")

checkEvents = cur.execute("select count(*) from events")
count = checkEvents.fetchone()[0]
#Add in events if there are none in the DB
if (count<1):
    cur.execute("insert into events values(Null,'SP'),(Null,'WT'),(Null,'DT'),(Null,'HT'),(Null,'JT')")

mensTrackURL = 'https://www.tfrrs.org/teams/tf/WI_college_m_Wis_Stevens_Point.html'
html = urlopen(mensTrackURL)
soup=BeautifulSoup(html.read(), "html.parser")
#Get the latest meet result links
mostRecentMeets = soup.find('h3',text="LATEST RESULTS").find_parent().find_parent().find('table').findAll('a')
###
###ADD FUNCTIONALITY TO PRINT THE 10 MOST RECENT MEETS THEN CHOOSE ONE 0-9 TO GET THE RESULTS FOR
###
###
###
###

meetURL = "https://www.tfrrs.org/results/75878/Pointer_Alumni_Open"
html = urlopen(meetURL)
soup=BeautifulSoup(html.read(), "html.parser")

#grabs the corresponding event urls for each gender.
#take the event name as a parameter must be as shown in TFFRS to work.
def GetGenderEventURLs(eventsRows, eventName):
    for eachEvent in eventsRows:
        if eventName in eachEvent.getText():
            return 'https:'+(eachEvent.find('a', href=True)['href'])
    return 'No event found for ' + eventName

menShotURL=GetGenderEventURLs(menANDwomenURL[0],'Shot Put')
menWeightURL=GetGenderEventURLs(menANDwomenURL[0],'Weight Throw')
menDiscusURL=GetGenderEventURLs(menANDwomenURL[0],'Discus')
menHammerURL=GetGenderEventURLs(menANDwomenURL[0],'Hammer')

womenShotURL=GetGenderEventURLs(menANDwomenURL[1],'Shot Put')
womenWeightURL=GetGenderEventURLs(menANDwomenURL[1],'Weight Throw')
womenDiscusURL=GetGenderEventURLs(menANDwomenURL[1],'Discus')
womenHammerURL=GetGenderEventURLs(menANDwomenURL[1],'Hammer')