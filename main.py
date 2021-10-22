from telethon import TelegramClient, events, sync
from datetime import datetime, tzinfo
import pytz
import telethon
# 之后换成获取本地时区
utc = pytz.UTC

# 从配置文件中读取信息
api_id = 
api_hash = ''
client = TelegramClient('tgporter', api_id, api_hash)
recorded_grouped_id = None
recorded_caption = ""
message_list = []


async def send_files(target_id):
    print("发送文件集合")
    global message_list, recorded_grouped_id, recorded_caption
    await client.send_file(
        target_id,
        file=message_list,
        caption=recorded_caption
    )
    message_list = []
    recorded_grouped_id = None


async def main():
    global recorded_grouped_id, recorded_caption, message_list
    await client.start()
    source_id = input("请输入消息源频道id: ")
    target_id = input("请输入消息目标频道id: ")
    limit = int(input("采集数量上限(输入0不设限): "))
    if limit == 0:
        limit = None
    # interval = int(input("请求间隔"))
    time_select = input("是否指定时间范围\n1.是 2.否\n")
    messages = []
    if time_select == "1":
        start_date_str = input("请输入开始日期(UTC) eg: 2021-1-1\n")
        end_date_str = input("请输入结束时间 eg: 2021-10-22\n")
        start_date = datetime.strptime(
            start_date_str, "%Y-%m-%d").replace(tzinfo=utc)
        end_date = datetime.strptime(
            end_date_str, "%Y-%m-%d").replace(tzinfo=utc)
        print("采集", start_date, "至", end_date, "范围内的内容")
        messages = client.iter_messages(
            source_id, reverse=True, limit=limit, offset_date=start_date)
    else:
        messages = client.iter_messages(source_id, reverse=True, limit=limit)

    async for message in messages:
        # 循环中对消息时间进行判断
        if message.date.replace(tzinfo=utc) > end_date.replace(tzinfo=utc):
            print("时间超出，结束采集")
            break
        if isinstance(message, telethon.tl.patched.Message):
            # 针对合并发送的文件(如相册)要特殊处理
            if message.grouped_id == None:
                # 普通消息直接转发
                # 如果前面还有文件则先发送文件
                if len(message_list) != 0:
                    await send_files(target_id)
                print("普通消息转发 消息日期:", message.date)
                await client.send_message(target_id, message)
            else:
                # recorded_group_id 初始化
                if recorded_grouped_id == None:
                    print("发现文件集合 消息日期:", message.date)
                    recorded_grouped_id = message.grouped_id
                    recorded_caption = message.message

                if recorded_grouped_id == message.grouped_id:
                    # 记录到临时文件列表中，当grouped_id改变后一起发送
                    print("文件加入列表")
                    message_list.append(message)
                else:
                    # 分组发生变化，先发送文件
                    await send_files(target_id)
        # else:
            # print(message)
    if recorded_grouped_id != None:
        await send_files(target_id)


with client:
    client.loop.run_until_complete(main())
