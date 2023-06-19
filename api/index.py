from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from os.path import join
import pandas as pd
import json

import os

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
working_status = os.getenv("DEFALUT_TALKING", default = "true").lower() == "true"

app = Flask(__name__)

# domain root
@app.route('/')
def home():
    return 'Hello, World!'

@app.route("/webhook", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global working_status
    if event.message.type != "text":
        return

    if event.message.text == "說話":
        reply_msg = "我可以說話囉，歡迎來跟我互動 ^_^ "
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_msg))
        return

    if event.message.text == "閉嘴":
        reply_msg = "好的，我乖乖閉嘴 > <，如果想要我繼續說話，請跟我說 「說話」 > <"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_msg))
        return

    if event.message.text == "簽到":
        data = {
            'Kyle': '煉獄'
        }
        df = pd.DataFrame.from_dict(data, orient='index', columns=['value'])
        json_str = df.to_json(orient='index')
        json_data = json.loads(json_str)
        with open(join('data', 'sign.json'), 'r') as file:
            for line in file:
                self.wfile.write(json_data)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="success"))
        return

if __name__ == "__main__":
    app.run()
