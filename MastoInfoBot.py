#!/usr/bin/python3 -u

from bs4 import BeautifulSoup
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import json
import logging
import mastodon
from mastodon import Mastodon
import os
from pathlib import Path
import requests
import sqlite3
import sys

##### Variable definieren und initialisieren ##################################
# Path and filename of the script itself
absFilePath = os.path.abspath(__file__)
# Split the path and the filename of the script into single variables
ScriptPath, ScriptFilename = os.path.split(absFilePath)
# Path and name of the sqlite database file
# Name of the sqlite database file
DBName = 'mastoinfo.db'
DBPath = ScriptPath + '\{}'.format(DBName) 

version = "0.3.37"

##### systemd log initialisieren ##############################################
logger = logging.getLogger("mastoinfo")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(fmt="%(asctime)s %(name)s.%(levelname)s: %(message)s", datefmt="%Y.%m.%d %H:%M:%S")

handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)


logger.info("Starte MastoInfoBot")
m = Mastodon(access_token='home/myuser/python/mastoinfo/usercred.secret', api_base_url="https://social.instance")

class Listener(mastodon.StreamListener):
    global DBName
    global DBPath
    global version    

    #def on_update(self, status):
        #print(f"on_update: {status}")
        # on_update: {'id': 109371390226010302, 'content': '<p>Listening to Toots...</p>',
        #  'account': {'id': 109359234895957150, 'username': 'admin'}, ...}

    def on_notification(self, notification):        
        global DBName
        global DBPath
        global version
        if notification.type == "mention":
            logger.info("Benachrichtigung über 'mention' eingegangen.")
            sichtbarkeit = ""
            if notification.status.visibility == "public":
                sichtbarkeit = "unlisted"
            else:
                sichtbarkeit = notification.status.visibility
            Antwort = ""
            ### Text aus der Antwort extrahieren
            content = BeautifulSoup(notification.status.content, "html.parser").text

            ### Instanz: ##### Informationen über angefragte Instanz zurücksenden #################
            if "Instanz:" in content:
                logger.info("Mention ist eine Instanzabfrage.")
                x = content.split(":")
                if x[0].endswith("Instanz"):
                    InstanzRequest = "https://" + x[1] + "/api/v2/instance"
                    req = requests.get(InstanzRequest)
                    if req.status_code == 200:
                        Instanz = json.loads(req.text)
                        domain = Instanz['domain']
                        title = Instanz['title']
                        version = Instanz['version']
                        description = Instanz['description']
                        if len(description) >= 210:
                            description = description[:200] + "..."

                        active_users = Instanz['usage']['users']['active_month']
                        languagesx = Instanz['languages']
                        languages = ""
                        for x in languagesx:
                            if len(languages) == 0:
                                languages = x
                            else:
                                languages = languages + "\n" + x

                        toot_max_characters = Instanz['configuration']['statuses']['max_characters']
                        toot_max_media = Instanz['configuration']['statuses']['max_media_attachments']
                        if Instanz['configuration']['translation']['enabled'] == True:
                            translation_enabled = "Ja"
                        else:
                            translation_enabled = "Nein"

                        if Instanz['registrations']['enabled'] == True:
                            registrations_enabled = "geöffnet"
                        else:
                            registrations_enabled = "geschlossen"

                        if Instanz['registrations']['approval_required'] == True:
                            registrations_approval_required = "benötigt"
                        else:
                            registrations_approval_required = "ohne"
                        
                        contact_email = Instanz['contact']['email']
                        contact_username = Instanz['contact']['account']['username']
                        contact_url = Instanz['contact']['account']['url']

                        rulesx = Instanz['rules']
                        rules = "Regeln:\n"
                        for x in rulesx:
                            y = "\n" + str(x['id']) + ": " + x['text']
                            if len(y) > 120:
                                # Zeile auf 120 Zeichen kürzen, dann letztes Wort abschneiden...
                                z = y[:-(len(y)-120)].rsplit(" ", maxsplit=1)[0]
                                # ...den Rest in eine neue Zeile schreiben.
                                y = z + "\n    " + y[len(z):]
                            rules = rules + y
                        
                        with Image.open("bg.png").convert("RGBA") as base:
                            txt = Image.new("RGBA", base.size, (255, 255, 255, 0))
                            fnt = ImageFont.truetype("baskerville-700.ttf", 18)
                            d = ImageDraw.Draw(txt)
                            d.multiline_text((20, 25), rules, font=fnt, fill=(255, 255, 255, 255))
                            out = Image.alpha_composite(base, txt)
                            out.save("image.png")
                            
                        media = m.media_post("image.png", "image/png", rules[:1500])                        

                        Antwort = "\n\nDomain: " + domain + "\nTitel: " + title + "\nVersion: " + version + "\nAktive Nutzer: "  + str(active_users)
                        Antwort = Antwort + "\nRegistrierung: " + registrations_enabled + "\nGenehmigung: " + registrations_approval_required
                        Antwort = Antwort + "\n\nBeschreibung:\n" + description + "\n\nSprachen:\n" + languages + "\n\nZeichenzahl: " + str(toot_max_characters)
                        Antwort = Antwort + "\nMedienzahl: " + str(toot_max_media) + "\nÜbersetzung: " + translation_enabled + "\nAdmin Kontakt: " + contact_username + "\n" + contact_url
                        
                        m.status_reply(notification.status, Antwort, media_ids=media['id'], visibility=sichtbarkeit)
                        logger.info("Nachricht an " + notification.account.username + " über Instanz:" + domain + " versand.")
                    else:
                        Antwort = "Fehler '" + str(req.status_code) + "'\n\nHandelt es sich bei '" + x[1] + "' um eine Instanz im Fediverse?"
                        m.status_reply(notification.status, Antwort, visibility=sichtbarkeit)
                        logger.warning("Nachricht an " + notification.account.username + ", Fehler " + str(req.status_code) + " bei Abfrage von "+ x[1] + ".")
            
            ### WerBinIch: ##### Informationen über den Absender zurücksenden #####################
            elif "WerBinIch:" in content:
                logger.info("Mention ist eine WerBinIch-Abfrage.")
                                
                Antwort = "Hallo " + notification.account.display_name + ",\n\nDu hast mich gefragt wie Dein Profil sich darstellt:\n\n"
                Antwort = Antwort + "ID: " + str(notification.account.id) + "\nName: " + notification.account.acct + "\nBot: " 
                if notification.account.bot == True:
                    Antwort = Antwort + "Ja"
                else:
                    Antwort = Antwort + "Nein"

                Antwort = Antwort + "\nFolgt: " + str(notification.account.following_count) + "\nGefolgt: " + str(notification.account.followers_count)
                Antwort = Antwort + "\nKonto erstellt: " + str(notification.account.created_at.strftime("%d.%m.%Y")) + "\nNachrichten: " + str(notification.account.statuses_count)
                
                if notification.account.locked == False:
                    Antwort = Antwort + "\n- Es kann ohne Anfrage gefolgt werden\n"
                else:
                    Antwort = Antwort + "\n- Es braucht eine Anfrage um zu folgen\n"

                if notification.account.discoverable == True:
                    Antwort = Antwort + "- Profil wird auf der Entdecken Seite angezeigt und von Suchmaschinen gefunden\n\n"
                else:
                    Antwort = Antwort + "- Profil wird auf der Entdecken Seite nicht angezeigt und von Suchmaschinen nicht gefunden\n\n"
                
                Antwort = Antwort + notification.account.url
                
                fiAvatar = requests.get(notification.account.avatar, allow_redirects=True)
                open("Avatar", 'wb').write(fiAvatar.content)
                foAvatar = Image.open("Avatar").format
                Avatar = m.media_post("Avatar", "image/" + foAvatar, "Avatar")

                fiHeader = requests.get(notification.account.header, allow_redirects=True)
                open("Header", 'wb').write(fiHeader.content)
                foHeader = Image.open("Header").format
                Header = m.media_post("Header", "image/" + foHeader, "Header")    

                logger.info(len(Antwort))
                m.status_reply(notification.status, Antwort, media_ids=(Avatar['id'], Header['id']), visibility=sichtbarkeit) 
            
            ### Benutzer: ##### Informationen über angefragtes Profil zurücksenden ################
            elif "Benutzer:" in content:
                logger.info("Mention ist eine Benutzerabfrage.")
                x = content.split(":")
                Antwort = "Benutzer"
            
            ### Hilfe: ##### Link auf die Hilfeseite zurücksenden #################################
            elif "Hilfe:" in content:
                logger.info("Mention ist eine Hilfe-Abfrage.")
                Antwort = "\n\nHallo " + notification.account.display_name + ", Du hast mich um Hilfe gebeten.\n\nDie findest Du auf der folgeden Webseite:\nhttps://blog.jcs-net.de/startseite/mastodon-information-bot/"
                msg = m.status_reply(notification.status, Antwort, visibility=sichtbarkeit)
                logger.info("Nachricht an " + notification.account.username + " über Hilfe: versand.")

            ### Version: ##### Versionsnummer versenden ##########################################
            elif "Version:" in content:
                logger.info("Mention ist eine Version-Abfrage.")
                Antwort = "\n\nAktuell läuft mastoinfobot in Version: " + version
                msg = m.status_reply(notification.status, Antwort, visibility=sichtbarkeit)
                logger.info("Nachricht an " + notification.account.username + " über Version: versand.")

            ### Nichts tun !!! ###################################################################
            else:
                logger.warning("Mention wurde fehlerhaft erkannt: " + content)
            

        else:
            logger.warning("unbehandelter notification.type: " + notification.type)
            


        
logger.info("Mastodon Listener erstellen..")
m.stream_user(Listener())
