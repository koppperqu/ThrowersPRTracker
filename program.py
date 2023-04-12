from urllib.request import urlopen
from bs4 import BeautifulSoup

try:
    f = open("adminEmails.txt", "r")
except IOError:
    f = open("adminEmails.txt", 'w')
    f.close()
    f = open("adminEmails.txt", "r")

adminEmails=f.read().split(',')
f.close()

try:
    f = open("otherEmails.txt", "r")
except IOError:
    f = open("otherEmails.txt", 'w')
    f.close()
    f = open("otherEmails.txt", "r")

otherEmails=f.read().split(',')
f.close()

womensTrackURL="https://www.tfrrs.org/teams/tf/WI_college_f_Wis_Stevens_Point.html"
mensTrackURL="https://www.tfrrs.org/teams/tf/WI_college_m_Wis_Stevens_Point.html"
instagram = ""
newAddsToProgram=""
#Email should be layed out like the following
#1)Throw number for each persons pr (compare this list to the istagram list to ensure everyone has a throw number if they pr'd)
#2)Instagram post formatted (i.e each genders prs by event)
#3)"Debugging" Information like if someone new was added, new event was added, new pr was added

#Need 2 lists one for prs that happened by checking each persons page to see if th best changed
#and another one that checks the meet results to get what throw the pr happened on
#then the 2 lists need to be compared to see if anyone got missed.

tfrrsPRs=[]
#format for the if a pr happened by looking at page and checking for pr against db
#{'name':None, 'event':None, 'mark':None}
tfrrsMeetPagePRs=[]
#format for the if a pr happened by looking at meet page
#{'name':None, 'event':None, 'mark':None, 'thrownumber':None}
newPRsOrPeopleAdded=[]
#format for if a new person, pr, or event is added to DB
#{'name':None, 'event':None, 'mark':None}

#This should run everyday at midnight to update current prs in the system
#this will prevent errors from mis entries in TFRRS so it will update prs
#before it runs though it will check if there was a new track meet that was competed in
#if there was it will make a note of all the people who pr'd in the meet then
#format an email to send out to coach matt and me and makenzie

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import URL
from sqlalchemy import ForeignKey
from sqlalchemy import Table, Column, Integer, String
from sqlalchemy import MetaData

url_object = URL.create(
    "sqlite",
    database="appdb",
)

engine = create_engine(url_object)

metadata_obj = MetaData()

athlete_table = Table(
    "athlete",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("name", String(50), nullable=False),
)

event_table = Table(
    "event",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("name", String(20), nullable=False),
)

pr_table = Table(
    "pr",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("athlete_id", ForeignKey("athlete.id"), nullable=False),
    Column("event_id", ForeignKey("event.id"), nullable=False),
    Column("mark", Integer),
)

metadata_obj.create_all(engine)

from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    pass

from typing import List
from typing import Optional
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import relationship

class Athlete(Base):
    __tablename__ = "athlete"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    prs: Mapped[List["Pr"]] = relationship(back_populates="athlete")
    def __repr__(self) -> str:
        return f"Athlete(id={self.id!r}, name={self.name!r})"

class Event(Base):
    __tablename__ = "event"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(20))
    prs: Mapped[List["Pr"]] = relationship(back_populates="event")
    def __repr__(self) -> str:
        return f"Event(id={self.id!r}, name={self.name!r})"

class Pr(Base):
    __tablename__ = "pr"
    id: Mapped[int] = mapped_column(primary_key=True)
    athlete_id = mapped_column(ForeignKey("athlete.id"))
    event_id = mapped_column(ForeignKey("event.id"))    
    mark: Mapped[int]
    athlete: Mapped["Athlete"] = relationship(back_populates="prs")
    event: Mapped["Event"] = relationship(back_populates="prs")
    def __repr__(self) -> str:
        return f"Pr(id={self.id!r}, event_id={self.event_id!r}, event_id={self.athlete_id!r}, mark={self.mark!r})"

def getAthletesNamesAndTffrsLinks(url):
    html = urlopen(url)
    soup=BeautifulSoup(html.read(), "html.parser")
    athleteLinks = soup.find('h3',string='ROSTER').find_parent().find('tbody').findAll('a')
    names=[]
    tffrsLink=[]
    for eachLink in athleteLinks:
        nameParts=eachLink.getText().split(', ')
        names.append(nameParts[1]+' '+nameParts[0])
        tffrsLink.append('https://www.tfrrs.org'+eachLink['href'])
    return(names,tffrsLink)

def getCurrentAthletesAndPRS():
    html = urlopen(mensTrackURL)
    soup=BeautifulSoup(html.read(), "html.parser")
    womensTrackURL = 'https://www.tfrrs.org'+soup.find('a',string='Women\'s Track & Field')['href']
    men,menTffrsLink = getAthletesNamesAndTffrsLinks(mensTrackURL)
    women,womenTffrsLink = getAthletesNamesAndTffrsLinks(womensTrackURL)
    names=men+women
    tffrsLinks=menTffrsLink+womenTffrsLink
    throwers=[]
    throwersEvents=[]
    throwersMarks=[]
    for index,eachPerson in enumerate(names):
        print(f"Now on {eachPerson}")
        html = urlopen(tffrsLinks[index])
        soup=BeautifulSoup(html.read(), "html.parser")
        bestsRows=soup.find('table',id='all_bests').findAll('td')
        events=[]
        marks=[]
        for index,each in enumerate(bestsRows):
            if index%2==0:
                events.append(each.getText().strip())
            else:
                marks.append(each.getText().strip())
        isThrower=False
        newMarks = []
        newEvents = []
        for eventIndex,eachEvent in enumerate(events):        
            if eachEvent in ['SP','WT','DT','HT','JT']:
                if(not isThrower):
                    isThrower=True
                    throwers.append(eachPerson)
                holdCharacters=[]
                tempmark=''
                #Need to go through mark and find m then only use what before m for the mark.
                for eachLetter in marks[eventIndex]:
                    if eachLetter=='m':
                        break
                    holdCharacters.append(eachLetter)
                for each in holdCharacters:
                    tempmark=tempmark+each
                newMarks.append(float(tempmark))
                newEvents.append(eachEvent)
        if(isThrower):
            throwersEvents.append(newEvents)
            throwersMarks.append(newMarks)
    #Now we have all current athletes and prs we need to update DB
    session = Session(engine)
    for throwerNumber,eachThrower in enumerate(throwers):
        with Session(engine) as session:
            # query for athlete if they are in db
            statement = select(Athlete).filter_by(name=eachThrower)
            # get result
            res = session.execute(statement).fetchone()
            athleteID=None
            if res==None:
                #add to db
                print(f"Adding {eachThrower} to db")
                athlete=Athlete(name=eachThrower)
                session.add(athlete)
                session.commit()
                athleteID = athlete.id
                newPRsOrPeopleAdded.append({'name':eachThrower, 'event':None, 'mark':None})
            else:
                athleteID=res.Athlete.id
            for index,eachEvent in enumerate(throwersEvents[throwerNumber]):
                statement = select(Event).filter_by(name=eachEvent)
                # get result
                eventres = session.execute(statement).fetchone()
                eventID=None
                if eventres==None:
                    #add to db
                    print(f"Adding {eachEvent} to db")
                    event=Event(name=eachEvent)
                    session.add(event)
                    session.commit()
                    eventID = event.id
                    newPRsOrPeopleAdded.append({'name':None, 'event':eachEvent, 'mark':None})
                else:
                    eventID=eventres.Event.id
                statement = select(Pr).filter_by(athlete_id=athleteID, event_id = eventID)
                # get result
                prres = session.scalars(statement).one_or_none()
                if prres==None:
                    #add to db
                    print(f"Adding pr for {eachThrower} for {eachEvent} mark was {throwersMarks[throwerNumber][index]} to db")
                    pr=Pr(athlete_id=athleteID,event_id = eventID,mark=throwersMarks[throwerNumber][index])
                    session.add(pr)
                    session.commit()
                    newPRsOrPeopleAdded.append({'name':eachThrower, 'event':eachEvent, 'mark':throwersMarks[throwerNumber][index]})
                else:
                    if prres.mark!=throwersMarks[throwerNumber][index]:
                        #A NEW PR
                        print(f"{eachThrower}'s pr in {eachEvent} has been changed, old mark was {prres.mark} new mark is {throwersMarks[throwerNumber][index]}")
                        prres.mark=throwersMarks[throwerNumber][index]
                        session.commit()
                        tfrrsPRs.append({'name':eachThrower, 'event':eachEvent, 'mark':throwersMarks[throwerNumber][index]})
    session.close()

def getMenAndWomenEventURLS(meetURL):
    html = urlopen(meetURL)
    soup=BeautifulSoup(html.read(), "html.parser")
    menEvents = soup.find('h3',string="MEN'S EVENTS").find_parent().findAll('a')
    womenEvents = soup.find('h3',string="WOMEN'S EVENTS").find_parent().findAll('a')
    menEventURLS=findEventURLS(menEvents)
    womenEventURLS=findEventURLS(womenEvents)
    return(menEventURLS,womenEventURLS)

def getCurrentAthletesAndPRSOffline(fileName):
    throwers,throwersEvents,throwersMarks=readFromFileOffline(fileName)
    #Now we have all current athletes and prs we need to update DB
    session = Session(engine)
    for throwerNumber,eachThrower in enumerate(throwers):
        with Session(engine) as session:
            # query for athlete if they are in db
            statement = select(Athlete).filter_by(name=eachThrower)
            # get result
            res = session.execute(statement).fetchone()
            athleteID=None
            if res==None:
                #add to db
                print(f"Adding {eachThrower} to db")
                athlete=Athlete(name=eachThrower)
                session.add(athlete)
                session.commit()
                athleteID = athlete.id
                newPRsOrPeopleAdded.append({'name':eachThrower, 'event':None, 'mark':None})
            else:
                athleteID=res.Athlete.id
            for index,eachEvent in enumerate(throwersEvents[throwerNumber]):
                statement = select(Event).filter_by(name=eachEvent)
                # get result
                eventres = session.execute(statement).fetchone()
                eventID=None
                if eventres==None:
                    #add to db
                    print(f"Adding {eachEvent} to db")
                    event=Event(name=eachEvent)
                    session.add(event)
                    session.commit()
                    eventID = event.id
                    newPRsOrPeopleAdded.append({'name':None, 'event':eachEvent, 'mark':None})
                else:
                    eventID=eventres.Event.id
                statement = select(Pr).filter_by(athlete_id=athleteID, event_id = eventID)
                # get result
                prres = session.scalars(statement).one_or_none()
                if prres==None:
                    #add to db
                    print(f"Adding pr for {eachThrower} for {eachEvent} mark was {throwersMarks[throwerNumber][index]} to db")
                    pr=Pr(athlete_id=athleteID,event_id = eventID,mark=throwersMarks[throwerNumber][index])
                    session.add(pr)
                    session.commit()
                    newPRsOrPeopleAdded.append({'name':eachThrower, 'event':eachEvent, 'mark':throwersMarks[throwerNumber][index]})
                else:
                    if prres.mark!=throwersMarks[throwerNumber][index]:
                        #A NEW PR
                        print(f"{eachThrower} pr'd in {eachEvent} old mark was {prres.mark} new mark is {throwersMarks[throwerNumber][index]}")
                        prres.mark=throwersMarks[throwerNumber][index]
                        session.commit()
                        tfrrsPRs.append({'name':eachThrower, 'event':eachEvent, 'mark':throwersMarks[throwerNumber][index]})
    session.close()

import json

#SHOULD NOT NEED ANYMORE KEEPING JUST IN CASE
def storeOfflineToFile(throwers,throwersEvents,throwersMarks):
    data = dict(zip(['throwers','throwersEvents','throwersMarks'],[throwers,throwersEvents,throwersMarks]))
    jsondata = json.dumps(data,indent=2)
    with open('throwersofflinedata.json','w') as f:
        f.write(jsondata)
        f.close()

def readFromFileOffline(filename):
    f = open(filename,'r')
    data = json.load(f)
    returnThrowers=data['throwers']
    returnThrowersEvents=data["throwersEvents"]
    returnThrowersMarks=data['throwersMarks']
    return returnThrowers,returnThrowersEvents,returnThrowersMarks

def findEventURLS(listOfEventLinks):
    events=["Shot Put","Weight Throw","Discus","Hammer","Javelin"]
    throwsLinks = {"Shot Put":"","Weight Throw":"","Discus":"","Hammer":"","Javelin":"",}
    for each in listOfEventLinks:
        if each.text in events:
            throwsLinks[each.text]=each['href']
    return(throwsLinks)

def getEventsNamesAndMarks(eventURL):   
    html = urlopen(eventURL)
    soup=BeautifulSoup(html.read(), "html.parser")
    allAthletes = soup.find('tbody').findAll('tr')
    uwspNamesRowsIndex = []
    #Get all the name row index due to formatting of site
    for index,eachAthlete in enumerate(allAthletes):
        if (eachAthlete.find('a',string='Wis.-Stevens Point') != None):
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

#Format for checkForPRSByMeet dictionary
#{'event':event,'name':name,'mark':mark,'thrownumber':thrownumber}
def checkForPRSByMeetReturnThrowNumber(eventURLS):
    itemsToReturn=[]
    session = Session(engine)
    for eachEventURL in eventURLS.items():
        if(eachEventURL[1]!=""):
            eventname=eachEventURL[0]
            names,marks=getEventsNamesAndMarks(eachEventURL[1])
            for index,eachName in enumerate(names):
                if(marks[index]!=[]):
                    statement = select(Athlete).filter_by(name=eachName)
                    # get result
                    res = session.execute(statement).fetchone()
                    #If name is not in DB, its not a pr as they have no records
                    if res==None:
                        print(eachName)
                        continue
                    #Check if there was a pr
                    #First need to get highest mark out of the list of marks
                    #Need to remove 'FOUL' for the max function to work
                    athleteID = res.Athlete.id
                    dbEventID=0
                    if eventname=='Shot Put':
                        statement = select(Event).filter_by(name='SP')
                        # get result
                        res = session.execute(statement).fetchone()
                        dbEventID = res.Event.id
                    if eventname=='Weight':
                        statement = select(Event).filter_by(name='WT')
                        # get result
                        res = session.execute(statement).fetchone()
                        dbEventID = res.Event.id
                    if eventname=='Discus':
                        statement = select(Event).filter_by(name='DT')
                        # get result
                        res = session.execute(statement).fetchone()
                        dbEventID = res.Event.id
                    if eventname=='Javelin':
                        statement = select(Event).filter_by(name='JT')
                        # get result
                        res = session.execute(statement).fetchone()
                        dbEventID = res.Event.id
                    if eventname=='Hammer':
                        statement = select(Event).filter_by(name='HT')
                        # get result
                        res = session.execute(statement).fetchone()
                        dbEventID = res.Event.id
                    marksNoPass = [mark.replace('PASS', '0') for mark in marks[index]]
                    marksNoFoul = [mark.replace('FOUL', '0') for mark in marksNoPass]
                    marksToFloat= [float(mark) for mark in marksNoFoul]
                    highestThrowAtMeet=max(marksToFloat)
                    throwNumber = marksToFloat.index(highestThrowAtMeet)+1
                    statement = select(Pr).filter_by(athlete_id=athleteID, event_id = dbEventID)
                    res = session.scalars(statement).one_or_none()
                    if res==None:
                        #They have no pr so it doesnt count as a pr(for the instagram)
                        continue
                    else:
                        currPR = res.mark
                        prID = res.id
                        if(currPR<float(highestThrowAtMeet)):
                            res.mark=float(highestThrowAtMeet)
                            session.commit()
                            itemsToReturn.append({'event':eventname,'name':eachName,'mark':float(highestThrowAtMeet),'thrownumber':throwNumber})
    session.close()
    return(itemsToReturn)

def getMostRecentMeetsAndOrderThem():
    html = urlopen(mensTrackURL)
    soup=BeautifulSoup(html.read(), "html.parser")
    mostRecentMensMeets = soup.find('h3',string="LATEST RESULTS").find_parent().find_parent().find('tbody').findAll('tr')
    html = urlopen(womensTrackURL)
    soup=BeautifulSoup(html.read(), "html.parser")
    mostRecentWomensMeets = soup.find('h3',string="LATEST RESULTS").find_parent().find_parent().find('tbody').findAll('tr')
    mostRecentMeets = mostRecentMensMeets
    for eachMeet in mostRecentWomensMeets:
        if eachMeet not in mostRecentMeets:
            mostRecentMeets.append(eachMeet)
    #Now we have a combined list, now we need to sort them and remove XC meets
    meetsToRemove=[]
    for eachMeet in mostRecentMeets:
        if 'xc' in eachMeet.find('a')['href'].split('/'):
            meetsToRemove.append(eachMeet)
    for eachMeet in meetsToRemove:
        mostRecentMeets.remove(eachMeet)
    #Now we have a list of track meets, we need to make sure they are ordered by date.
    mostRecentMeetsByDate=[]
    #Format for mostRecentMeetsByDate {'date':date,'meet':meet}
    for eachMeet in mostRecentMeets:
        inputDate=eachMeet.findAll('td')[0].text
        if '-' in inputDate:
                    split = inputDate.split('-')
                    split2 = split[1].split(',')
                    inputDate = split[0] +','+split2[1]
        mostRecentMeetsByDate.append({'date':inputDate,'meet':eachMeet.find('a')})
    from datetime import datetime
    # Sort the list in ascending order of dates
    mostRecentMeetsByDate.sort(key = lambda date: datetime.strptime(date['date'], "%B %d, %Y"))
    return (mostRecentMeetsByDate)

def addToForMatt(sortedPrs):
    currEvent=sortedPrs[0]['event']
    textToReturn = currEvent +"\n\n"
    for each in sortedPrs:
        if each['event']==currEvent:
            #just add mark/number
            textToReturn += f"{each['name']} - throw number {each['thrownumber']} - mark was {each['mark']}\n"
        else:
            currEvent=each['event']
            #add new event and mark/number
            textToReturn += "\n" +currEvent +"\n\n"
            textToReturn += f"{each['name']} - throw number {each['thrownumber']} - mark was {each['mark']}\n"
    return(textToReturn)

def addToForInstagram(sortedPrs):
    currEvent=sortedPrs[0]['event']
    textToReturn = currEvent +"\n"
    for each in sortedPrs:
        if each['event']==currEvent:
            #just add mark/number
            textToReturn += f"{each['name']} - {each['mark']}\n"
        else:
            currEvent=each['event']
            #add new event and mark/number
            textToReturn += "\n" +currEvent +"\n"
            textToReturn += f"{each['name']} - {each['mark']}\n"
    return(textToReturn)

try:
    #MAIN PROGRAM LOOP STARTS HERE MAIN PROGRAM LOOP STARTS HERE MAIN PROGRAM LOOP STARTS HERE MAIN PROGRAM LOOP STARTS HERE MAIN PROGRAM LOOP STARTS HERE MAIN PROGRAM LOOP STARTS HERE MAIN PROGRAM LOOP STARTS HERE 

    #First get and order most recent meets

    mostRecentMeetsByDate=getMostRecentMeetsAndOrderThem()

    #After getting most recent meets the following code will run the check for prs
    #While also getting throws numbers for prs then update the DB
    #This will happend for every meet that the program has not ran on yet
    #Hopefully this implmentation works when more than one meet is done on a day
    #And when more than one meet is done in a week

    f = open("lastMeetProgramRanOn.txt", "r")
    mostRecentlyRanMeet=f.readline().strip()
    mostRecentlyRanMeetDate=f.readline().strip()
    f.close()
    mensPrs=[]
    womensPrs=[]
    for meetIndex,eachMeet in enumerate(mostRecentMeetsByDate):
        if eachMeet['meet'].text==mostRecentlyRanMeet and eachMeet['date']==mostRecentlyRanMeetDate:
            #We need to run program on the next meet, or if there is no next meet we are done
                if meetIndex!=len(mostRecentMeetsByDate)-1:
                    #we know the one we are on is not the last one in the list, so we can check the NEXT for prs
                    meetUrl="https://www.tfrrs.org"+ mostRecentMeetsByDate[meetIndex+1]['meet']['href']
                    menEventURLS,womenEventURLS=getMenAndWomenEventURLS(meetUrl)
                    mensPrs=checkForPRSByMeetReturnThrowNumber(menEventURLS)
                    womensPrs=checkForPRSByMeetReturnThrowNumber(womenEventURLS)
                    #Here is where the email is formatted then sent out
                    forEmail = f"{mostRecentMeetsByDate[meetIndex+1]['meet'].text} - {mostRecentMeetsByDate[meetIndex+1]['date']} \n"
                    sortedMensPrs=sorted(mensPrs,key=lambda x:(x['event'],-x['mark']))
                    sortedWomensPrs=sorted(womensPrs,key=lambda x:(x['event'],-x['mark']))
                    if len(sortedMensPrs)!=0:
                        forEmail += "MEN\n\n"
                        forEmail += addToForMatt(sortedMensPrs)
                        forEmail += "\nWOMEN\n\n"
                        forEmail += addToForMatt(sortedWomensPrs)
                        forEmail += "\n\nINSTAGRAM \n\nMen\n\n"
                        forEmail += addToForInstagram(sortedMensPrs)
                        forEmail += "\nWomen\n\n"
                        forEmail += addToForInstagram(sortedWomensPrs)
                    import ssl
                    import smtplib
                    import os
                    sender = os.environ.get("PYTHON_EMAIL")
                    password=os.environ.get("EMAIL_PASS")
                    receivers = otherEmails
                    message = f"From: {sender}\nTo: "
                    for each in receivers:
                        if receivers.index(each)==len(receivers)-1:
                            message += each.strip()
                            break
                        message += each + ','
                    
                    message += "\nSubject: Throws PRS This Week\n\n"
                    message += message+'\n\n'+forEmail
                    context = ssl.create_default_context()
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                        smtp.login(sender, password)
                        smtp.sendmail(sender,receivers,message)
                    #after checking the meet set the new most recently ran meet and date to the next one
                    mostRecentlyRanMeet = mostRecentMeetsByDate[meetIndex+1]['meet'].text
                    mostRecentlyRanMeetDate = mostRecentMeetsByDate[meetIndex+1]['date']
                else:
                    #Otherwise it is the most recently ran meet and is last in list to we save
                    f = open("lastMeetProgramRanOn.txt", "w")
                    f.writelines(eachMeet['meet'].text +"\n")
                    f.writelines(eachMeet['date'])
                    f.close()
                    
    #Run below code after getting what throw number was a pr and sending out email for throw number
    #Then after that the and all meets have been ran on the next code will send just me
    #An email to see if anything was missed or if new people are added
    #This will update the DB after checking for prs from the most recent meet, if it finds stuff
    #Someone was probably missed, unless they were just added to the DB, (No previous history i.e. freshman or new event)

    getCurrentAthletesAndPRS()

    #The code to format the email sent to me
    #VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV
    prAdded=""
    personAdded=""
    eventAdded=""
    for each in newPRsOrPeopleAdded:
        if each['mark']!=None:
            prAdded=prAdded+f"First record was added for {each['name']} in the {each['event']} mark was {each['mark']}\n"
        else:
            if each['name']!=None:
                personAdded=personAdded+f"{each['name']} was added to the DB, probably their first meet, if not somethings wrong\n"
            if each['event']!=None:
                eventAdded=eventAdded+f"{each['event']} was added to the DB, something is most likley drastically wrong CALL HELP\n"

    if(newPRsOrPeopleAdded!=[]):
        newAddsToProgram = 'Below contains new people added and new prs if any\n\n'
        newAddsToProgram=newAddsToProgram+personAdded+prAdded+eventAdded

    sorted_list = sorted(tfrrsPRs,key=lambda x:(x['event'],-x['mark']))
    if len(sorted_list)!=0:
        event=sorted_list[0]['event']
        instagram = 'PRS added or changed after most recent meet\n'
        instagram = instagram + (f"\n{event}\n")
        for index,each in enumerate(sorted_list):
            instagram = instagram + (f"{each['name']} - {each['mark']}\n")
            if index==len(sorted_list)-1:            
                break
            if event!=sorted_list[index+1]['event']:
                instagram = instagram + (f"\n{sorted_list[index+1]['event']}\n")
                event=sorted_list[index+1]['event']

    #If there is no new adds or changes to instagam dont send out an email
    if newAddsToProgram!='' or instagram!='':
        import ssl
        import smtplib
        import os
        sender = os.environ.get("PYTHON_EMAIL")
        password=os.environ.get("EMAIL_PASS")
        receivers = adminEmails
        message = f"From: {sender}\nTo: "
        for each in receivers:
            if receivers.index(each)==len(receivers)-1:
                message += each.strip()
                break
            message += each + ','
        
        message += "\nSubject: THROWS PROGRAM DEBUG STUFF\n\n"
        message += f"{instagram}\n\n{newAddsToProgram}"
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(sender, password)
            smtp.sendmail(sender,receivers,message)
except Exception as e:
    import ssl
    import smtplib
    import os
    sender = os.environ.get("PYTHON_EMAIL")
    password=os.environ.get("EMAIL_PASS")
    receivers = adminEmails
    message = f"From: {sender}\nTo: "
    for each in receivers:
        if receivers.index(each)==len(receivers)-1:
            message += each.strip()
            break
        message += each + ','
    
    message += "\nSubject: PROGRAM HAS THROWN AN EXCEPTION NEEDS ATTENTION\n\n"
    message += e
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(sender, password)
        smtp.sendmail(sender,receivers,message)