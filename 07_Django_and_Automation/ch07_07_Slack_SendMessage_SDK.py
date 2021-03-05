import os
# Import WebClient from Python SDK (github.com/slackapi/python-slack-sdk)
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging as logger

# WebClient insantiates a client that can call API methods
# When using Bolt, you can use either `app.client` or the `client` passed to listeners.
client = WebClient(token='xoxb-*****')

# ID of the channel you want to send the message to
channel_id = "#일반"
markdown_text = '''
This message is plain3.
*This message is bold3.*
'This message is code3.'
_This message is Italic3_'
~This message is strile3.~
'''

attach_dict = {
    'color': '#ff0000',
    'author_name': 'INVESTAR',
    'author_link': 'github.com/investar',
    'title': '오늘의 증시 KOSPI',
    'title_link': 'http://finance.naver.com/sise/sise_index.nhn?code=KOSPI',
    'text': '2,326.13 △11.89 (+0.51%)',
    'image_url': 'https://ssl.pstatic.net/imgstock/chart3/day/KOSPI.png'
}
attach_list = [attach_dict]
try:
    # Call the chat.postMessage method using the WebClient
    result = client.chat_postMessage(
        channel=channel_id,
        text=markdown_text,
        attachments=attach_list
    )
    logger.info(result)

except SlackApiError as e:
    logger.error(f"Error posting message: {e}")