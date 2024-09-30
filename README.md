# MastoInfoBot
Mastodon Bot

Das Repository dient lediglich dazu die bisherige Arbeit vorzuhalten. Die notwendige Datenbank kann mit dem Skript [Instanzen.py](/Instanzen.py) erstellt werden, der eigentliche Bot steckt in [MastoInfoBot.py](/MastoInfoBot.py), welches ich als Simple Service mit systemd ausgeführt habe.

Der Bot nutzt [Mastodon.py](https://pypi.org/project/Mastodon.py/) um die Mastodon API anzusprechen und auf Benachrichtigungen zu reagieren.

Um den Bot nutzen zu können muss er mit einem Token versehen werden, das ihn an ein Mastodon Profil bindet. Der Token wird vor Ausführung in der Datei [usercred.secret](/usercred.secret) abgelegt. Ein Beispiel liegt bei.
