#!/usr/bin/python3 -u

from datetime import datetime
import json
import os
from pathlib import Path
import requests
import sqlite3


# Path and filename of the script itself
absFilePath = os.path.abspath(__file__)
# Split the path and the filename of the script into single variables
ScriptPath, ScriptFilename = os.path.split(absFilePath)
# Path and name of the sqlite database file
# Name of the sqlite database file
DBName = 'mastoinfo.db'
DBPath = ScriptPath + '\{}'.format(DBName) 


def main():
    # Datenbank ggf. erstellen und erste Domain abfragen, sonst öffnen
    fileObj = Path(DBPath) 
    if fileObj.is_file():
        print("Datenbank öffnen...")
        con = sqlite3.connect(DBName)        
        cur = con.cursor()
    else:    
        print("Datenbank anlegen...")    
        con = sqlite3.connect(DBName)
        cur = con.cursor()
        cur.execute("CREATE TABLE instances(domain text NOT NULL UNIQUE, title text, version text, platform text, user_count integer, user_active integer, status_count integer, domain_count integer, updated integer)")
        
        InstanzRequest = "https://social.instance/api/v2/instance"
        req = requests.get(InstanzRequest)
        if req.status_code == 200:
            Instanz = json.loads(req.text)
            domain = Instanz['domain']
            title = Instanz['title']
            version = Instanz['version']
            source = Instanz['source_url']
            platform = source.rsplit("/", maxsplit=1)[1]
            user_active = Instanz['usage']['users']['active_month']
        else:
            print("Daten konnten nicht abgerufen werden.")
            return False

        InstanzRequest = "https://social.instance/api/v1/instance"
        req = requests.get(InstanzRequest)
        if req.status_code == 200:
            Instanz = json.loads(req.text)
            user_count = Instanz['stats']['user_count']
            status_count = Instanz['stats']['status_count']
            domain_count = Instanz['stats']['domain_count']
        else:
            print("Daten konnten nicht abgerufen werden.")
            return False       
        
        updated = datetime.now()
        cur.execute('INSERT INTO instances VALUES(?,?,?,?,?,?,?,?,?)', (domain, title, version, platform, user_count, user_active, status_count, domain_count, updated))
        con.commit()        
        cur.close()
        con.close()
        return True

    
    cur.execute('SELECT * FROM instances ORDER BY updated DESC LIMIT 100')
    rows = cur.fetchall()
    try:
        row = rows[0]        
    except:
        cur.close
        con.close
        print("Keine Daten in der Datenbank!")
        return False


    for row in rows:
        if update_instance(row[0], con) == True:
            InstanzRequest = "https://" + row[0] + "/api/v1/instance/peers"
            try:
                req = requests.get(InstanzRequest)            
                if req.status_code == 200:
                    Instanzen = json.loads(req.text)
                    vorhanden = 0
                    for x in Instanzen:                
                        try:
                            updated = datetime.now()
                            cur.execute('INSERT INTO instances VALUES(?,NULL,NULL,NULL,NULL,NULL,NULL,NULL,?)', (x, updated))
                            con.commit()
                        except:
                            vorhanden = vorhanden + 1
                    print("Bereits vorhandene Instanzen: " + str(vorhanden))
            except:
                print("Fehler bei Abfrage von " + row[0])
                continue
        else:
            cur.execute("DELETE FROM instances WHERE domain = '" + row[0] + "'")
            con.commit()
        

    cur.close() 
    con.close()


def update_instance(domain, con):
    InstanzRequest = "https://" + domain + "/api/v2/instance"
    try:
        req = requests.get(InstanzRequest)
    except:
        #cur = con.cursor()
        #cur.execute("DELETE FROM instances WHERE domain = '" + domain + "'")
        #con.commit()
        return False


    if req.status_code == 200:
        try:
            Instanz = json.loads(req.text)
            title = Instanz['title']
            version = Instanz['version']
            source = Instanz['source_url']
            platform = source.rsplit("/", maxsplit=1)[1]
            user_active = Instanz['usage']['users']['active_month']
        except:
            print(req.text)
            #cur = con.cursor()
            #cur.execute("DELETE FROM instances WHERE domain = '" + domain + "'")
            #con.commit()
            return False
    else:
        print("Daten konnten nicht abgerufen werden")
        return False


    InstanzRequest = "https://" + domain + "/api/v1/instance"
    try:
        req = requests.get(InstanzRequest)
        if req.status_code == 200:
            Instanz = json.loads(req.text)
            user_count = Instanz['stats']['user_count']
            status_count = Instanz['stats']['status_count']
            domain_count = Instanz['stats']['domain_count']
        else:
            return False    
    except:
        return False 

    cur = con.cursor()
    sql = ''' UPDATE instances
              SET title = ? ,
                  version = ? ,
                  platform = ? ,
                  user_count = ? ,
                  user_active = ? ,
                  status_count = ? ,
                  domain_count = ? ,
                  updated = ?
              WHERE domain = ?'''
    updated = datetime.now()
    cur.execute(sql, (title, version, platform, user_count, user_active, status_count, domain_count, domain, updated))
    con.commit()
    return True




if __name__ == "__main__":
    main()
