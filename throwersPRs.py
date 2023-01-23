import sqlite3
from urllib.request import urlopen
from bs4 import BeautifulSoup

def getAthletesNamesAndTffrsLinks(url):
    html = urlopen(url)
    soup=BeautifulSoup(html.read(), "html.parser")
    athleteLinks = soup.find('h3',text='ROSTER').find_parent().find('tbody').findAll('a')
    names=[]
    tffrsLink=[]
    for eachLink in athleteLinks:
        nameParts=eachLink.getText().split(', ')
        names.append(nameParts[1]+' '+nameParts[0])
        tffrsLink.append('https://www.tfrrs.org'+eachLink['href'])
    return(names,tffrsLink)

def getThrowersInDBCurrPRS():
    mensTrackURL = 'https://www.tfrrs.org/teams/tf/WI_college_m_Wis_Stevens_Point.html'
    html = urlopen(mensTrackURL)
    soup=BeautifulSoup(html.read(), "html.parser")
    womensTrackURL = 'https://www.tfrrs.org'+soup.find('a',text='Women\'s Track & Field')['href']
    men,menTffrsLink = getAthletesNamesAndTffrsLinks(mensTrackURL)
    women,womenTffrsLink = getAthletesNamesAndTffrsLinks(womensTrackURL)
    names=men+women
    tffrsLinks=menTffrsLink+womenTffrsLink
    res = cur.execute("select name from athletes").fetchall()
    throwers=[]
    for each in res:
        throwers.append(each[0])
    for eachThrower in throwers:
        #Go to their tffrs page and get all their current prs then update the db
        if(eachThrower in names):
            html = urlopen(tffrsLinks[names.index(eachThrower)])
            soup=BeautifulSoup(html.read(), "html.parser")
            bestsRows=soup.find('table',id='all_bests').findAll('td')
            events=[]
            marks=[]
            for index,each in enumerate(bestsRows):
                if index%2==0:
                    events.append(each)
                else:
                    marks.append(each)
            #cur.execute("select * from prs inner join athletes on prs.athleteID = athletes.id inner join events on events.id = prs.eventID where athletes.name = 'Austin Kopp'").fetchall()
            for eventIndex,eachEvent in enumerate(events):
                formatEvent=eachEvent.getText().strip()
                if formatEvent in ['SP','WT','DT','HT','JT']:
                    formatMark=marks[eventIndex].getText().strip()    
                    holdCharacters=[]
                    tempmark=''
                    #Need to go through mark and find m then only use what before m for the mark.
                    for eachLetter in formatMark:
                        if eachLetter=='m':
                            break
                        holdCharacters.append(eachLetter)
                    for each in holdCharacters:
                        tempmark=tempmark+each
                    formatMark=tempmark
                    event=''
                    if(formatEvent=='SP'):
                        event='Shot Put'
                    elif(formatEvent == 'WT'):
                        event='Weight Throw'
                    elif(formatEvent == 'DT'):
                        event='Discus'
                    elif(formatEvent == 'HT'):
                        event='Hammer'
                    elif(formatEvent == 'JT'):
                        event='Javelin'
                    #ADD TO DB OR UPDATE DB NOW
                    res = cur.execute("select count(*) from prs inner join athletes on prs.athleteID = athletes.id inner join events on events.id = prs.eventID where athletes.name = ? and events.name = ?",(eachThrower,event))
                    count = res.fetchone()[0]
                    if(count==1):
                        currPR = cur.execute("select prs.mark from prs inner join athletes on prs.athleteID = athletes.id inner join events on events.id = prs.eventID where athletes.name = ? and events.name = ?",(eachThrower,event)).fetchone()[0]
                        if(currPR<float(formatMark)):
                            print('Updating ' + eachThrower + ' event ' + event + ' new mark ' + formatMark)
                            prID = cur.execute("select prs.id from prs inner join athletes on prs.athleteID = athletes.id inner join events on events.id = prs.eventID where athletes.name = ? and events.name = ?",(eachThrower,event)).fetchone()[0]
                            cur.execute("update prs set mark = ? where id = ?",(formatMark,prID,))
                            con.commit()
                    else:
                        print('Adding pr for ' + eachThrower + ' event ' + event + ' new mark ' + formatMark)
                        athleteID = cur.execute("select id from athletes where name = ?",(eachThrower,)).fetchone()[0]
                        eventID = cur.execute("select id from events where name = ?",(event,)).fetchone()[0]
                        cur.execute("insert into prs (athleteID,eventID,mark)values (?,?,?)",(athleteID,eventID,formatMark,))
                        con.commit()
        else:
            print ('Old thrower ' + eachThrower + ' not on the roster :(')

def findEventURLS(listOfEventLinks):
    events=["Shot Put","Weight Throw","Discus","Hammer","Javelin"]
    throwsLinks = {"Shot Put":"","Weight Throw":"","Discus":"","Hammer":"","Javelin":"",}
    for each in listOfEventLinks:
        if each.text in events:
            throwsLinks[each.text]=each['href']
    return(throwsLinks)

def getMenAndWomenEventURLS(meetURL):
    html = urlopen(meetURL)
    soup=BeautifulSoup(html.read(), "html.parser")
    menEvents = soup.find('h3',text="MEN'S EVENTS").find_parent().findAll('a')
    womenEvents = soup.find('h3',text="WOMEN'S EVENTS").find_parent().findAll('a')
    menEventURLS=findEventURLS(menEvents)
    womenEventURLS=findEventURLS(womenEvents)
    return(menEventURLS,womenEventURLS)

def getEventsNamesAndMarks(eventURL):   
    html = urlopen(eventURL)
    soup=BeautifulSoup(html.read(), "html.parser")
    allAthletes = soup.find('tbody').findAll('tr')
    uwspNamesRowsIndex = []
    #Get all the name row index due to formatting of site
    for index,eachAthlete in enumerate(allAthletes):
        if (eachAthlete.find('a',text='Wis.-Stevens Point') != None):
            uwspNamesRowsIndex.append(index)
    #Grab all the names and marks for each person
    
    names=[]
    marks=[]
    for eachIndex in uwspNamesRowsIndex:
        names.append(allAthletes[eachIndex].find('a').text)
        unformattedMarks = allAthletes[eachIndex+1].findAll('li')
        formattedMarks=[]
        for eachMark in unformattedMarks:
            formattedMarks.append(eachMark.text.strip())
        marks.append(formattedMarks)
    return(names,marks)

#Now that I got the event urls I need to go through and query the DB to see if a person PR if so update the pr
#Also if the person does not exist they need to be added

def checkForPRS(eventURLS):
    instagram=""
    email=""
    for eachEventURL in eventURLS.items():
        if(eachEventURL[1]!=""):
            instagram +='\n\n'+eachEventURL[0]+'\n'
            email +='\n\n'+eachEventURL[0]+'\n'
            print(eachEventURL[0])
            names,marks=getEventsNamesAndMarks(eachEventURL[1])
            for index,eachName in enumerate(names):
                if(marks[index]!=[]):
                    res = cur.execute("select count(*) from athletes where name = ?",(eachName,))
                    count = res.fetchone()[0]
                    if(count==0):
                        cur.execute("insert into athletes (name) values(?)",(eachName,))
                        con.commit()
                    #Now that everyname is in need to check for prs
                    #If no pr add a pr
                    #First need to get highest mark out of the list of marks
                    #Need to remove 'FOUL' for the max function to work
                    athleteID = cur.execute("select id from athletes where name = ?",(eachName,)).fetchone()[0]
                    eventID = cur.execute("select id from events where name = ?",(eachEventURL[0],)).fetchone()[0]
                    markNoFoul = [mark.replace('FOUL', '0') for mark in marks[index]]
                    highestThrowAtMeet=max(markNoFoul)
                    throwNumber = markNoFoul.index(highestThrowAtMeet)+1
                    res = cur.execute("select count(*) from prs inner join athletes on prs.athleteID = athletes.id inner join events on events.id = prs.eventID where athletes.name = ? and events.name = ?",(eachName,eachEventURL[0]))
                    count = res.fetchone()[0]
                    if(count==0):
                        cur.execute("insert into prs (athleteID,eventID,mark)values (?,?,?)",(athleteID,eventID,highestThrowAtMeet,))
                        con.commit()
                    else:
                        currPR = cur.execute("select prs.mark from prs inner join athletes on prs.athleteID = athletes.id inner join events on events.id = prs.eventID where athletes.name = ? and events.name = ?",(eachName,eachEventURL[0])).fetchone()[0]
                        prID = cur.execute("select prs.id from prs inner join athletes on prs.athleteID = athletes.id inner join events on events.id = prs.eventID where athletes.name = ? and events.name = ?",(eachName,eachEventURL[0])).fetchone()[0]
                        if(currPR<float(highestThrowAtMeet)):
                            cur.execute("update prs set mark = ? where id = ?",(highestThrowAtMeet,prID,))
                            con.commit()
                            instagram +=eachName + ' - '+ highestThrowAtMeet+'\n'
                            email +=eachName +' throw number '+ str(throwNumber)+'\n'
        else:
            print (eachEventURL[0] + " was not thrown")
    email+=instagram
    return(email)

def user_input_is_valid(input,lowVal,highVal):
    try:
        # Convert it into integer
        val = int(input)
        if(val>=lowVal and val<=highVal):
            return (True)        
        print("Please input an acceptable choice")
        return (False)
    except ValueError:
        print("Please input an acceptable choice")
        return (False)


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
    cur.execute("insert into events values(Null,'Shot Put'),(Null,'Weight Throw'),(Null,'Discus'),(Null,'Hammer'),(Null,'Javelin')")
    con.commit()

mensTrackURL = 'https://www.tfrrs.org/teams/tf/WI_college_m_Wis_Stevens_Point.html'
html = urlopen(mensTrackURL)
soup=BeautifulSoup(html.read(), "html.parser")
#Get the latest meet result links
mostRecentMeets = soup.find('h3',text="LATEST RESULTS").find_parent().find_parent().find('table').findAll('a')
###
###ADD FUNCTIONALITY TO PRINT THE 10 MOST RECENT MEETS THEN CHOOSE ONE 0-9 TO GET THE RESULTS FOR
###

emailOn=False
def cli(emailOnPassed):
    emailOn=emailOnPassed
    print("Welcome to sauce's thrower pr tracker :)")
    print('Email on is set to ' + str(emailOn))
    print("What would you like to do?")
    print("1) Run the check for prs and 'print' the results to the console")
    print("2) Update all throwers prs that are in the 'system'")
    print("3) Turn on the auto email functionality?")
    print("4) Exit")

    choice = input()
    while not user_input_is_valid(choice,1,4):
        choice = input()
    choice = int(choice)
    if choice==1:
        print('Which meet would you like to check?')
        for x in range(0,10):
            print(str(x)+') '+mostRecentMeets[x].text)
        meetChoice=input()
        while not user_input_is_valid(meetChoice,0,9):
            meetChoice = input()
        meetChoice = int(meetChoice)
        menEventURLS,womenEventURLS=getMenAndWomenEventURLS('https://www.tfrrs.org'+mostRecentMeets[meetChoice]['href'])
        email='\nMEN\n'+checkForPRS(menEventURLS)
        email+='\nWOMEN\n'+checkForPRS(womenEventURLS)
        print(email)
        print('Done! NEXT')
        cli(emailOn)
    elif choice==2:
        print('updating app pr information')
        getThrowersInDBCurrPRS()
        print('Done! NEXT')
        cli(emailOn)
    elif choice==3:
        emailOn=not emailOn
        print('Email on is set to ' + str(emailOn))
        print('Done! NEXT')
        cli(emailOn)
    elif choice==4:
        print('Goodbye')
#This functon takes the input ur and finds the roster section on the page then grabs all the names and tffrs links and returns them as a dictionary as key value pairs name is the key
# menEventURLS,womenEventURLS = getMenAndWomenEventURLS(meetURL)

# email = checkForPRS(menEventURLS)
# email+= checkForPRS(womenEventURLS)

cli(emailOn)
# con.commit()
con.close()

# Trouble shooting commands
# import sqlite3
# con = sqlite3.connect("throwersprs.db")
# cur = con.cursor()
# cur.execute("insert into athletes (name) values('Lupe Corn')")
# con.commit()
#cur.execute("select * from prs inner join athletes on prs.athleteID = athletes.id inner join events on events.id = prs.eventID where athletes.name = ?",('Lupe Corn',)).fetchone()[0]
#cur.execute("select distinct * from athletes").fetchall()