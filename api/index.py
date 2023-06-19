from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from os.path import join
import pandas as pd
import json
import psycopg2

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

    if event.message.text in "簽到":
        parts = event.message.text.split("；")
        sign = parts[0]
        line_name = parts[1]
        lineagew_name = parts[2]
        club = parts[3]

        conn = connect_to_db()
        cursor = conn.cursor()
        reply_msg = ""
        
        # 示例插入数据
        query = "INSERT INTO member (lineagew_name, line_name, club) VALUES (%s, %s, %s)"
        data = (lineagew_name, line_name, club)
        try:
            cursor.execute(query, data)
            conn.commit()
            reply_msg = lineagew_name + "簽到完成" 
            print("数据插入成功！")
        except (Exception, psycopg2.Error) as error:
            reply_msg = "簽到失敗:", error
            print("数据插入失敗！")
        finally:
            conn.close()
            
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_msg))
        return
    
    if event.message.text == "找":
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM member")
        results = cursor.fetchall()
        conn.close()

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=str(results)))
        return
    
def connect_to_db():
    conn = psycopg2.connect(
        host="ep-white-firefly-975577-pooler.us-east-1.postgres.vercel-storage.com",
        port="5432",
        database="verceldb",
        user="default",
        password="kyx8GQivump6"
    )
    return conn    

if __name__ == "__main__":
    app.run()
