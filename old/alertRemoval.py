#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 17 15:51:01 2017

@author: tanner

This File Reads Email and then deletes alerts based on emails send to the email address

This File Comports FWAS with Zawinski's Law:
Every program attempts to expand until it can read mail. 
Those programs which cannot so expand are replaced by ones which can.

There are still some problems with this removal system which 
need to be worked on
Also most of the Platforms are not yet tested.
------------------
TESTED PLATFORMS:
ATT
VERIZON
EMAIL
T-MOBILE
------------------
UNTESTED PLATFORMS:
everything else
------------------
"""

import platform
import imaplib
import email
import datetime
import glob
import ConfigParser
import os
import base64
import sys
print '==========================='
print 'Alert Removal System     '
print datetime.datetime.now()
print platform.system(),platform.release()
print '===========================\n'
sys.path.insert(0,base64.b64decode('L2hvbWUvdWJ1bnR1L3NyYy90ZXN0Qm9uZFN0cmVldC8='))
import sys_codec
cZ=glob.glob('/srv/shiny-server/fwas/data/*.cfg')
#cZ=glob.glob('/home/tanner/src/breezy/cfgLoc/*.cfg')

def readHeaderFiles(cfgLoc):
    """
    reads first part of config file
    """
    cfg=ConfigParser.ConfigParser()
    cfg.read(cfgLoc)
    headerDict={}
#    thresholdDict={}
#    unitDict={}
    options=cfg.options(cfg.sections()[0])
    section=cfg.sections()[0]
    for i in range(len(options)):
        headerDict[options[i]]=cfg.get(section,options[i])
#    options=cfg.options(cfg.sections()[1])
#    section=cfg.sections()[1]
#    for i in range(len(options)):
#        thresholdDict[options[i]]=cfg.get(section,options[i])
#    options=cfg.options(cfg.sections()[2])
#    section=cfg.sections()[2]
#    for i in range(len(options)):
#        unitDict[options[i]]=cfg.get(section,options[i])
    return headerDict


M = imaplib.IMAP4_SSL('imap.gmail.com')
M.login(sys_codec.openAndDecode()[0], sys_codec.openAndDecode()[1])

#rv, mailboxes = M.list()

rv,data=M.select("INBOX")
rv,lData=M.search(None,"ALL")

datList=lData[0].split()
datList=[int(x) for x in datList]
rm_cZ=[]
rm_em=[] 

#j=1
for j in datList:
#    i=0
    for i in range(len(cZ)):
        problems=[]
        mStr=M.fetch(j,'(RFC822)')
        
        msg=email.message_from_string(mStr[1][0][1])
        sendFrom=msg['From']
        #sendBody=msg.get_payload(decode=True)
        #print sendFrom
        
        hList=readHeaderFiles(cZ[i])
        hList['phone']=hList['phone'].translate(None,'()[] -.{}/')
        
        hName=hList['alert_name']
#        print hName
        
        val='stop'
        
        tVal=val+' '+hName
        
        sendType=[0]    
        
        a=sendFrom.find(':') #????
        b=sendFrom.find('@') #Finds where the email is
        c=len(sendFrom)
        d=sendFrom.find('<') #These show up in Emails
        e=sendFrom.find('>') #But not text messages
        
        
#        print '--------------------------'
#        print 'Reading Message No: ',j
        if hList['carrier']=='tmobile' and d==-1 and e==-1:
            print 'Tmobile'
            #We Got a Runner...
            send_id=sendFrom[:b][2:]
            send_tmob=send_id[2:]
            msg_body=str(msg.get_payload(i=1))
            locLen=len('base64\n')
            b64Loc=str(msg_body.find('base64\n'))
            b64Part=msg_body[int(b64Loc)+locLen:]
            decode=base64.b64decode(b64Part)
            valLoc=decode.find((val+' '+hName))
            if valLoc==-1:
                valLoc=decode.find((val.capitalize()+' '+hName))
            sendType[0]=1
            
        if d==-1 and e==-1 and hList['carrier']!='tmobile':
            print '--Cell Phone based Alert--(or possibly nothing...)'
            send_id=sendFrom[:b]
            print 'try: get_payload(i=0)...'
            try:
                msg_body=msg.get_payload(i=0) #We Can't Decode Text messages without summoning demons... So instead we manually parse it!
            except:
                print 'get_payload(i=0) Failed... Try: get_payload(decode=True)...'
                pass
                try:
                    msg_body=msg.get_payload(decode=True)
                except:
                    print 'get_payload failed on both counts...'
                    print 'Servicing Required!'
                    raise
            
            print 'Soemthing Worked!, proceeding...'
            msg_body=str(msg_body)
#            print msg_body
            valLoc=msg_body.find((val+' '+hName))
            if valLoc==-1:
                msg_body=msg_body.lower()
                valLoc=msg_body.find(((val.lower()+' '+hName.lower())))
#                valLoc=msg_body.find((val.capitalize()+' '+hName))
            sendType[0]=1
                
        if d!=-1 and e!=-1:
            print '--Email Based Alert--'
            send_id=sendFrom[d+1:e]
            try:
#                msg_body=msg.get_payload(decode=True)
                msg_body=msg.get_payload(i=0)
                msg_body=msg_body.get_payload()
            except:
                print 'decode=True Failed...Try: i=0'
                pass
                try:
                    msg_body=msg.get_payload(decode=True)
                except:
                    print 'get_payload failed on both counts...'
                    print 'Servicing Required!'
                    raise
            
            print 'Something Worked!, proceeding...'
            valLoc=msg_body.find((val+' '+hName))
            if valLoc==-1:
                msg_body=msg_body.lower()
                valLoc=msg_body.find(((val.lower()+' '+hName.lower())))
#                valLoc=msg_body.find((val.capitalize()+' '+hName))
            sendType[0]=0
        
        localContact=''
        send_id=send_id.lower()
        if sendType[0]==0:
            if send_id==hList['email']:
                localContact=hList['email']
#                rm_cZ.append(cZ[i])
#                rm_em.append(j)
        if sendType[0]==1:
            if send_id==hList['phone']:
                localContact=hList['phone']
#                rm_cZ.append(cZ[i])
#                rm_em.append(j)
          
        if localContact!=send_id:
            problems.append('localContact!=send_id') #This prevents one users from deleting another users Alert         
       
        if valLoc!=-1 and not any(problems):
            print '---------------------------'
            print 'Reading Message No.',j
            print 'cfg File No.',i
            print sendType
            print 'sender:',send_id
            print 'cfg_contact:',localContact
            print 'stop loc:',valLoc
            print 'message:',msg_body[valLoc:valLoc+len(tVal)]
            print 'alert_name:',hList['alert_name']
            print cZ[i]
            print '---------------------------'

            
            rm_cZ.append(cZ[i])
            rm_em.append(j)
        localContact=''


#print '--------------------------'
print '==========================='

print '-=-=-=-=-=-=-=-=-=-=-=-=-=-'
print 'Emails & Alerts Slated for Removal'
print '-=-=-=-=-=-=-=-=-=-=-=-=-=-'
print rm_cZ
print rm_em
print '-=-=-=-=-=-=-=-=-=--=-=-=-=-'

check=len(rm_cZ)==len(rm_em)

if check==True:
    print 'Removal Lengths are equal'
    print check
    print 'rm_cZ,rm_em'
    print len(rm_cZ),len(rm_em)
if check==False:
    print 'Error, something has gone wrong with the removal system...'
    exit
    
if not any(rm_cZ) and not any(rm_em):
    print 'No Alerts Slated For Removal...'
    print 'Exiting'
    exit

#
for i in range(len(rm_cZ)):
    print 'Removing Alert:',rm_cZ[i]
    os.remove(rm_cZ[i])
    M.store(rm_em[i],'+X-GM-LABELS','\\Trash')



#set_em=list(set(rm_em))