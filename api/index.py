from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from os.path import join
import pandas as pd
import json
import psycopg2
import os
import requests
from db_operations import connect_to_db, select_member, insert_member, close_connection


line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
working_status = os.getenv("DEFALUT_TALKING", default = "true").lower() == "true"

app = Flask(__name__)

# domain root
@app.route('/')
def home():
    return 'Hello, World!'

@app.route("/webhook", methods=['POST'])
def webhook():
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

        【報名出征】
        報名出征；天堂W名稱
        例-> 報名出征；精靈鬼〻銀行；咩系RRRRRRRR

        【找出征名單】
        找出征；天堂W名稱
        例-> 找出征；精靈鬼〻銀行

        【查詢】
        找；line、天堂W名稱都行 (可模糊查詢)
        例-> 找；正妹

        【刪除】
        刪除；line、天堂W名稱都行 (需輸入詳細名稱)
        例-> 刪除；精靈鬼〻銀行
        """
        reply_message(event, reply_msg)
        return
    # 如果關鍵字為 "簽到"
    if keywords == "簽到":
        if len(parts) != 3 or not all(parts):
            reply_message(event, "簽到失敗, 請填寫正確格式 -> 簽到；天堂W名稱；LINE名稱")
            return
        lineagew_name = parts[1]
        line_name = parts[2]
        result = select_member(cursor, lineagew_name, line_name)
        if result:
            reply_msg = lineagew_name + "還在皮?你已經簽到過了,想被精靈鬼飛噗你就繼續 😍"
        else:
            try:
                insert_member(cursor, conn, lineagew_name, line_name)
                reply_msg = lineagew_name + "簽到成功囉, 請跟紫變精靈鬼領取一次飛噗 👍"
            except (Exception, psycopg2.Error) as error:
                logging.error(f"Error occurred: {error}")
                reply_msg = lineagew_name + " 簽到失敗了, "
            finally:
                close_connection(conn)
        reply_message(event, reply_msg)
        return

    if keywords == "報名出征":
        if len(parts) != 3 or not all(parts):
            reply_message(event, "報名出征失敗, 請填寫正確格式 -> 出征；天堂W名稱；遺言")
            return
        lineagew_name = parts[1]
        excitation = parts[2]
        result = select_combat_team(cursor, lineagew_name)
        if result:
            reply_msg = lineagew_name + "還在皮?你已經報名過了,想留在本服被紫變精靈鬼飛噗嗎 😍"
        else:
            try:
                insert_combat_team(cursor, conn, lineagew_name, excitation)
                reply_msg = lineagew_name + "報名成功囉, 為榮耀爭光, 紫變精靈鬼給你一百次飛撲 👍"
            except (Exception, psycopg2.Error) as error:
                logging.error(f"Error occurred: {error}")
                reply_msg = lineagew_name + " 報名失敗了 "
            finally:
                close_connection(conn)
        reply_message(event, reply_msg)
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
            update_member(cursor, conn, lineagew_name, line_name, old_lineagew_name, old_line_name)
            reply_msg = old_lineagew_name + " 修改為 " + lineagew_name + "成功"
        except (Exception, psycopg2.Error) as error:
            logging.error(f"Error occurred: {error}")
            reply_msg = old_lineagew_name + " 修改為 " + lineagew_name + "失敗"
        finally:
            close_connection(conn)
        # 透過 Line Bot API 回覆訊息
        reply_message(event, reply_msg)
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
        reply_message(event, reply_msg)
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
            reply_message(event, formatted_results)
            return 
        except (Exception, psycopg2.Error) as error:
            # 如果查詢過程中出現錯誤，則輸出錯誤訊息
            print("查詢資料出錯:", error)
        finally:
            # 最後，關閉資料庫連接
            conn.close()
        return

    # 如果關鍵字為 "找出征"
    if keywords == "找出征":
        # 從訊息中取得查詢的關鍵字
        keyword = parts[1]
        # 連接到資料庫
        conn = connect_to_db()
        cursor = conn.cursor()
        try:
            # 如果關鍵字為空，則查詢所有出征成員
            if keyword == "":
                query = "SELECT * FROM combat_team"
                cursor.execute(query)
            else:
                # 否則，根據關鍵字查詢出征成員
                query = "SELECT * FROM combat_team WHERE lineagew_name LIKE %s"
                cursor.execute(query, (f'%{keyword}%'))

            # 獲取查詢結果
            results = cursor.fetchall()
            # 格式化查询结果
            formatted_results = f"==== 查詢结果 {cursor.rowcount} 筆 ====\n"
            for row in results:
                formatted_row = " - ".join(str(item) for item in row[1:])  # 从第二列开始组合结果
                formatted_results += f"{formatted_row}\n"
            formatted_results += "===================="

            # 透過 Line Bot API 回覆訊息
            reply_message(event, formatted_results)
            return 
        except (Exception, psycopg2.Error) as error:
            # 如果查詢過程中出現錯誤，則輸出錯誤訊息
            print("查詢資料出錯:", error)
        finally:
            # 最後，關閉資料庫連接
            conn.close()
        return


def reply_message(event, reply_msg):
    # 透過 Line Bot API 回覆訊息
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_msg))

if __name__ == "__main__":
    app.run()
