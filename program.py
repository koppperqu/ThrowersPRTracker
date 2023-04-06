from urllib.request import urlopen
from bs4 import BeautifulSoup
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import URL

#This should run everyday at midnight to update current prs in the system
#this will prevent errors from mis entries in TFRRS so it will update prs
#before it runs though it will check if there was a new track meet that was competed in
#if there was it will make a note of all the people who pr'd in the meet then
#format an email to send out to coach matt and me and makenzie

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

# mensTrackURL="https://www.tfrrs.org/teams/tf/WI_college_m_Wis_Stevens_Point.html"
# html = urlopen(mensTrackURL)
# soup=BeautifulSoup(html.read(), "html.parser")
# womensTrackURL = 'https://www.tfrrs.org'+soup.find('a',text='Women\'s Track & Field')['href']

# men,menTffrsLink = getAthletesNamesAndTffrsLinks(mensTrackURL)
# women,womenTffrsLink = getAthletesNamesAndTffrsLinks(womensTrackURL)
# names=men+women
# tffrsLinks=menTffrsLink+womenTffrsLink
# throwers=[]
# throwersEvents=[]
# throwersMarks=[]
# for index,eachPerson in enumerate(names):
#     html = urlopen(tffrsLinks[index])
#     soup=BeautifulSoup(html.read(), "html.parser")
#     bestsRows=soup.find('table',id='all_bests').findAll('td')
#     events=[]
#     marks=[]
#     for index,each in enumerate(bestsRows):
#         if index%2==0:
#             events.append(each.getText().strip())
#         else:
#             marks.append(each.getText().strip())
#     isThrower=False
#     newMarks = []
#     newEvents = []
#     for eventIndex,eachEvent in enumerate(events):        
#         if eachEvent in ['SP','WT','DT','HT','JT']:
#             if(not isThrower):
#                 isThrower=True
#                 throwers.append(eachPerson)
#             holdCharacters=[]
#             tempmark=''
#             #Need to go through mark and find m then only use what before m for the mark.
#             for eachLetter in marks[eventIndex]:
#                 if eachLetter=='m':
#                     break
#                 holdCharacters.append(eachLetter)
#             for each in holdCharacters:
#                 tempmark=tempmark+each
#             newMarks.append(tempmark)
#             newEvents.append(eachEvent)
#     if(isThrower):
#         throwersEvents.append(newEvents)
#         throwersMarks.append(newMarks)

#Saving results from running the above code so I
#I can work on this offline if necessary and I no longer need to 
#grab all the html everytime I want to work on this.
#This can be remove when implementing the final version so it 
#gets most recent results
#forjson = zip(throwers,throwersEvents,throwersMarks)
with open('throwers.txt','r') as f:
    data = f.read().split('\n')

throwers=[]
throwersEvents=[]
throwersMarks=[]
<<<<<<< HEAD
for index,each in enumerate(data):
    if index%3==0:
        throwers.append(data[index].strip())
    if index%3==1:  
        throwersEvents.append(data[index].strip().split(' '))
    if index%3==2:
        throwersMarks.append(data[index].strip().split(' '))
for index,eachThrower in enumerate(throwers):
    print(eachThrower,throwersEvents[index],throwersMarks[index])

#At this point we only have people who have thrown a throwing event so we 
#can assume we have all throwers unless they have not thrown in an event.
#the above code should be ran every day at midnight

=======
for index,eachPerson in enumerate(names):
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
            newMarks.append(tempmark)
            newEvents.append(eachEvent)
    if(isThrower):
        throwersEvents.append(newEvents)
        throwersMarks.append(newMarks)

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import URL

url_object = URL.create(
    "sqlite",
    database="ThrowersPRTracker/appdb",
)
engine = create_engine(url_object)
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("select 'hello world'"))
    print(result.all())
#At this point we only have people who have thrown a throwing event so we 
#can assume we have all throwers unless they have not thrown in an event.
#the above code should be ran every day at midnight
for index,eachThrower in enumerate(throwers):
    print(eachThrower,throwersEvents[index],throwersMarks[index])
    
    
    https://docs.sqlalchemy.org/en/20/tutorial/metadata.html
>>>>>>> 454fa87c7f44304a4322df9a1c28115b8cf36760
