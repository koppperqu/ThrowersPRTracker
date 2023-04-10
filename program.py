from urllib.request import urlopen
from bs4 import BeautifulSoup

womensTrackURL="https://www.tfrrs.org/teams/tf/WI_college_f_Wis_Stevens_Point.html"
mensTrackURL="https://www.tfrrs.org/teams/tf/WI_college_m_Wis_Stevens_Point.html"
email="PR's have been updated due to a new track meet(s)"
instagram = "Instagram post\n"
forMatt = "ForMATTed for Matt to get the correct throw for each PR"
newAddsToProgram="Below contains new people added and new prs if any\n\n"
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
    athleteLinks = soup.find('h3',text='ROSTER').find_parent().find('tbody').findAll('a')
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
    womensTrackURL = 'https://www.tfrrs.org'+soup.find('a',text='Women\'s Track & Field')['href']
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
                    if prres.mark<throwersMarks[throwerNumber][index]:
                        #A NEW PR
                        print(f"{eachThrower} pr'd in {eachEvent} old mark was {prres.mark} new mark is {throwersMarks[throwerNumber][index]}")
                        print(f"{prres.athlete_id}")
                        prres.mark=throwersMarks[throwerNumber][index]
                        session.commit()
                        tfrrsPRs.append({'name':eachThrower, 'event':eachEvent, 'mark':throwersMarks[throwerNumber][index]})

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
                    if prres.mark<throwersMarks[throwerNumber][index]:
                        #A NEW PR
                        print(f"{eachThrower} pr'd in {eachEvent} old mark was {prres.mark} new mark is {throwersMarks[throwerNumber][index]}")
                        prres.mark=throwersMarks[throwerNumber][index]
                        session.commit()
                        tfrrsPRs.append({'name':eachThrower, 'event':eachEvent, 'mark':throwersMarks[throwerNumber][index]})

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
#At this point we only have people who have thrown a throwing event so we 
#can assume we have all throwers unless they have not thrown in an event.
#the above code should be ran every day at midnight


#the above code should be ran every day at midnight
#Saving results from running the above code so I
#I can work on this offline if necessary
#This can be remove when implementing the final version so it 

#For when deploying
#getCurrentAthletesAndPRS()

#missing people and prs and events
#getCurrentAthletesAndPRSOffline('throwersofflinedataOriginalMissingPeople4-6-23.json')
#old data
#getCurrentAthletesAndPRSOffline('throwersofflinedataOriginal4-6-23.json')
#updated "new" data
getCurrentAthletesAndPRSOffline('throwersofflinedataModifedPRS4-6-23.json')

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

newAddsToProgram=newAddsToProgram+personAdded+prAdded+eventAdded


sorted_list = sorted(tfrrsPRs,key=lambda x:(x['event'],-x['mark']))
if len(sorted_list)!=0:
    event=sorted_list[0]['event']
    instagram = instagram + (f"\n{event}\n")
    for index,each in enumerate(sorted_list):
        instagram = instagram + (f"{each['name']} - {each['mark']}\n")
        if index==len(sorted_list)-1:            
            break
        if event!=sorted_list[index+1]['event']:
            instagram = instagram + (f"\n{sorted_list[index+1]['event']}\n")
            event=sorted_list[index+1]['event']

print(f"{instagram}\n\n{newAddsToProgram}")

html = urlopen(mensTrackURL)
soup=BeautifulSoup(html.read(), "html.parser")
mostRecentMensMeets = soup.find('h3',text="LATEST RESULTS").find_parent().find_parent().find('table').findAll('a')

html = urlopen(womensTrackURL)
soup=BeautifulSoup(html.read(), "html.parser")
mostRecentWomensMeets = soup.find('h3',text="LATEST RESULTS").find_parent().find_parent().find('table').findAll('a')
mostRecentMeetsHRefArrays=[]
mostRecentThrowsMeets=[]
hrefNumbers=[]
for eachMeet in mostRecentMensMeets:
    if 'xc' not in eachMeet['href'].split('/'):
        for index,eachPart in enumerate(eachMeet['href'].split('/')):
            if eachPart=='results':
                hrefNumbers.append(eachMeet['href'].split('/')[index+1])
                mostRecentThrowsMeets.append(eachMeet)


for eachMeet in mostRecentWomensMeets:
    if 'xc' not in eachMeet['href'].split('/'):
        for index,eachPart in enumerate(eachMeet['href'].split('/')):
            if eachPart=='results':
                if eachMeet['href'].split('/')[index+1] not in hrefNumbers:
                    for numberIndex,eachNumber in enumerate(hrefNumbers):
                        if int(eachNumber)>int(eachMeet['href'].split('/')[index+1]):
                            if int(hrefNumbers[numberIndex])<int(eachMeet['href'].split('/')[index+1]):
                                hrefNumbers.insert(eachMeet['href'].split('/')[index+1],numberIndex)
                            else:
                                hrefNumbers.insert(eachMeet['href'].split('/')[index+1],int(numberIndex+1))

                    hrefNumbers.append(eachMeet['href'].split('/')[index+1])
                    mostRecentThrowsMeets.append(eachMeet)