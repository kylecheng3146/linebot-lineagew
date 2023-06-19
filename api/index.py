from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

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
        # 创建key-value字典
        data = {
            'Kyle': '煉獄',
        }

        # 将字典转换为DataFrame
        df = pd.DataFrame.from_dict(data, orient='index', columns=['value'])

        # 将DataFrame转换为JSON字符串
        json_str = df.to_json(orient='index')

        # 解析JSON字符串为Python对象
        json_data = json.loads(json_str)

        # 将Python对象写入JSON文件
        with open('sign.json', 'w') as file:
            json.dump(json_data, file)
        reply_msg = "test123"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_msg))
        return

    if event.message.text == "找":
        # 读取JSON文件
        with open('sign.json', 'r') as file:
            json_data = json.load(file)

        # 查询特定key的value
        key = 'Kyle'
        value = json_data.get(key)

        if value is not None:
            reply_msg = "這個 '{key}' 是: {value}"
        else:
            reply_msg = "找不到關於 '{key}' 的資料"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_msg))
        return

if __name__ == "__main__":
    app.run()
