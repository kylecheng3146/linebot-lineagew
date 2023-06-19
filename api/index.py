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

    parts = event.message.text.split("；")
    keywords = parts[0]
    conn = connect_to_db()
    cursor = conn.cursor()

    if keywords == "簽到":
        line_name = parts[1]
        lineagew_name = parts[2]
        club = parts[3]
        try:
            query = "INSERT INTO member (lineagew_name, line_name, club) VALUES (%s, %s, %s)"
            data = (lineagew_name, line_name, club)
            cursor.execute(query, data)
            conn.commit()
            reply_msg = lineagew_name + " 簽到成功"
        except (Exception, psycopg2.Error) as error:
            reply_msg = lineagew_name + " 簽到失敗"
        finally:
            conn.close()
                
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_msg))
        return

    if keywords == "刪除":
        keyword = parts[1]
        try:
            query = "DELETE FROM member WHERE lineagew_name = %s OR line_name = %s"
            data = (keyword,keyword)
            cursor.execute(query, data)
            conn.commit()
            reply_msg = "恭喜你 " + keyword + " 刪除成功"
        except (Exception, psycopg2.Error) as error:
            reply_msg = "很遺憾 " + keyword + " 刪除失敗"
        finally:
            conn.close()
                
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_msg))
        return

    if keywords == "找":
        keyword = parts[1]
        conn = connect_to_db()
        cursor = conn.cursor()
        try:
            query = "SELECT * FROM member WHERE lineagew_name LIKE %s OR line_name LIKE %s OR club LIKE %s"
            cursor.execute(query, (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
            results = cursor.fetchall()

            formatted_results = "=============查詢結果=============\n"
            for row in results:
                formatted_row = " - ".join(str(item) for item in row)
                formatted_results += f"{formatted_row}\n"
            formatted_results += "================================="
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=formatted_results))
            return 
        except (Exception, psycopg2.Error) as error:
            print("查询資料出錯:", error)
        finally:
            conn.close()
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
