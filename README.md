C2 based on YouTube PoC
=========================================

This is a PoC of a possible C2 communication between controller and bots.
A demo of usage can be found at:
https://www.youtube.com/watch?v=Qim1Uw1furo

=========================================
Installation:

- We recommend using a virtual environment for python
- run the command: pip3 install -r requirements.txt
- You must obtain a json file containing the authorization credentials for YouTube Data API V3 - the file name must be credentials.json
- Please refer to https://developers.google.com/youtube/v3/getting-started
- Import the mysql database in the file BOTNET.sql, change in the controller.py file the database credentials! (search for "Change database credentials here!!")
- to run the controller: python controller.py
- to run the bot: python bot.py

=========================================
Usage:
- connect:
Used to connect to the API

- set_word <arg>:
The current word that will be used to search for videos and post them

- reset_word:
resets the posting word to the original hardcoded word

- send <arg>:
sends a command to the bots
the exec <arg> command will cause the bots to execute whatever comes after exec
the update_word <arg> command will cause the bots to search the videos by the word after update_word
in addition, you can send any message you like to the bots and it will be displayed while it runs and finds the messages

- show_comments:
shows all the currently posted comments and their id in the database

- del_comment <arg>:
deletes a comment by the id in arg
