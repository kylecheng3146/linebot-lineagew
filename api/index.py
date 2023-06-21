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

    # 從事件中取得訊息文字
    message = event.message.text
    # 如果訊息中包含分號，則將其替換為全角分號
    if ";" in message or ":" in message:
        message = message.replace(";", "；")
        message = message.replace(":", "；")
        
    parts = message.split("；")
    keywords = parts[0]
    conn = connect_to_db()
    cursor = conn.cursor()
    if keywords == "功能":
        reply_msg = """
        【簽到】
        簽到；天堂W名稱；Line名稱；
        例-> 簽到；精靈鬼〻銀行；大正妹

        【查詢】
        找；line、天堂W名稱都行 (可模糊查詢)
        例-> 找；正妹

        【刪除】
        刪除；line、天堂W名稱都行 (需輸入詳細名稱)
        例-> 刪除；精靈鬼〻銀行
        """
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_msg))
        return
    # 如果關鍵字為 "簽到"
    if keywords == "簽到":

        # parts 包含 3 个非空元素
        if len(parts) != 3 or not all(parts):
            # 透過 Line Bot API 回覆訊息，告知用戶簽到失敗並提供正確的簽到格式
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="簽到失敗, 請填寫正確格式 -> 簽到；天堂W名稱；LINE名稱"))
            # 結束此次操作
            return

        # 從訊息中取得用戶的資訊
        lineagew_name = parts[1]
        line_name = parts[2]

        # 在插入之前先查詢是否已經有資料
        query = "SELECT * FROM member WHERE lineagew_name = %s AND line_name = %s"
        data = (lineagew_name, line_name)
        cursor.execute(query, data)
        result = cursor.fetchone()

        # 如果已經有資料
        if result:
            # 回覆line_bot_api已簽到的訊息
            reply_msg = lineagew_name + " 已經簽到過了, 想被精靈鬼飛噗你就繼續.😍"
        else:
            try:
                # 將用戶的資訊插入到資料庫中
                query = "INSERT INTO member (lineagew_name, line_name) VALUES (%s, %s)"
                data = (lineagew_name, line_name)
                cursor.execute(query, data)
                # 提交插入操作
                conn.commit()
                # 回覆簽到成功訊息
                reply_msg = lineagew_name + " 簽到成功"
            except (Exception, psycopg2.Error) as error:
                # 如果插入過程中出現錯誤，則回覆簽到失敗訊息
                reply_msg = lineagew_name + " 簽到失敗"
            finally:
                # 最後，關閉資料庫連接
                conn.close()
                
        # 透過 Line Bot API 回覆訊息
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_msg))
        return

    # 如果關鍵字為 "修改"
    if keywords == "修改":
        # 從訊息中取得舊的資訊
        old_line_name = parts[1]
        old_lineagew_name = parts[2]
        # 從訊息中取得新的資訊
        line_name = parts[3]
        lineagew_name = parts[4]
        try:
            # 更新資料庫中的資訊
            query = "UPDATE member SET lineagew_name = %s, line_name = %s, WHERE lineagew_name = %s OR line_name = %s"
            data = (lineagew_name, line_name, old_lineagew_name, old_line_name)
            cursor.execute(query, data)
            # 提交更新操作
            conn.commit()
            # 回覆更新成功訊息
            reply_msg = old_lineagew_name + " 修改為 " + lineagew_name + "成功"
        except (Exception, psycopg2.Error) as error:
            # 如果更新過程中出現錯誤，則回覆更新失敗訊息
            reply_msg = old_lineagew_name + " 修改為 " + lineagew_name + "失敗"
        finally:
            # 最後，關閉資料庫連接
            conn.close()
                
        # 透過 Line Bot API 回覆訊息
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_msg))
        return

    # 如果關鍵字為 "刪除"
    if keywords == "刪除":
        # 從訊息中取得要刪除的關鍵字
        keyword = parts[1]
        try:
            # 如果關鍵字為 "ALL"，則刪除所有成員
            if keyword == "ALL":
                query = "DELETE FROM member"
                cursor.execute(query)
            else:
                # 否則，根據關鍵字刪除特定成員
                query = "DELETE FROM member WHERE lineagew_name = %s OR line_name = %s"
                data = (keyword,keyword)
                cursor.execute(query, data)

            # 提交刪除操作
            conn.commit()
            # 回覆刪除成功訊息
            reply_msg = keyword + " 刪除成功"
        except (Exception, psycopg2.Error) as error:
            # 如果刪除過程中出現錯誤，則回覆刪除失敗訊息
            reply_msg = keyword + " 刪除失敗"
        finally:
            # 最後，關閉資料庫連接
            conn.close()
                
        # 透過 Line Bot API 回覆訊息
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_msg))
        return

    # 如果關鍵字為 "找"
    if keywords == "找":
        # 從訊息中取得查詢的關鍵字
        keyword = parts[1]
        # 連接到資料庫
        conn = connect_to_db()
        cursor = conn.cursor()
        try:
            # 如果關鍵字為空，則查詢所有成員
            if keyword == "":
                query = "SELECT * FROM member"
                cursor.execute(query)
            else:
                # 否則，根據關鍵字查詢成員
                query = "SELECT * FROM member WHERE lineagew_name LIKE %s OR line_name LIKE %s"
                cursor.execute(query, (f'%{keyword}%', f'%{keyword}%'))

            # 獲取查詢結果
            results = cursor.fetchall()
            # 格式化查询结果
            formatted_results = f"==== 查詢结果 {cursor.rowcount} 筆 ====\n"
            for row in results:
                formatted_row = " - ".join(str(item) for item in row[1:])  # 从第二列开始组合结果
                formatted_results += f"{formatted_row}\n"
            formatted_results += "===================="

            # 透過 Line Bot API 回覆訊息
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=formatted_results))
            return 
        except (Exception, psycopg2.Error) as error:
            # 如果查詢過程中出現錯誤，則輸出錯誤訊息
            print("查詢資料出錯:", error)
        finally:
            # 最後，關閉資料庫連接
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
