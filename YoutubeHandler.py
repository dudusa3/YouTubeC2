# -*- coding: utf-8 -*-

# Sample Python code for youtube.commentThreads.insert
# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/code-samples#python

import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

api_service_name = "youtube"
api_version = "v3"
client_secrets_file = "credentials.json"


class YouTubeHandler(object):
    def __init__(self):
        # Get credentials and create an API client
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()
        self.youtube = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

    def post_comment(self, video_id, comment):
        request = self.youtube.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": comment
                        }
                    },
                    "videoId": video_id
                }
            }
        )
        response = request.execute()

        # print(response)
        return response['id']

    def delete_comment(self, comment_id):
        request = self.youtube.comments().delete(
            id=comment_id
        )
        response = request.execute()
        # print(response)


def main():
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "credentials.json"

    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    credentials = flow.run_console()
    print("The API Client key is: ", credentials)
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    # request = youtube.commentThreads().insert(
    #     part="snippet",
    #     body={
    #       "snippet": {
    #         "topLevelComment": {
    #           "snippet": {
    #             "textOriginal": "This video is awesome!"
    #           }
    #         },
    #         "videoId": "681TWckKj9g"
    #       }
    #     }
    # )
    # response = request.execute()
    #
    # print(response)

if __name__ == "__main__":
    main()