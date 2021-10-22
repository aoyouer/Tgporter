from telethon import TelegramClient, events, sync
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.errors import UserAlreadyParticipantError
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

# 从会话列表中进行选择
async def select_dialog():
    channels = []
    async for d in client.iter_dialogs():
        if d.is_channel:
            channels.append(d)
    print("------频道列表-----")
    for index in range(len(channels)):
        print(str(index)+"."+channels[index].name)
    select_index = int(input("请输入频道的索引: "))
    # print(channels[select_index])
    return channels[select_index].entity

async def main():
    global recorded_grouped_id, recorded_caption, message_list
    await client.start()
    source_select_mode = input("请输入源频道选择方式:\n1.输入id 2.从已加入的频道中选择\n")
    if source_select_mode == "2":
        input_channel = await select_dialog()
    else:
        source_type = input("请输入源频道类型\n1.公共 2.私有\n")
        input_channel = input("请输入源频道id: ")
        if source_type == "2":
            try:
                s_updates = await client(ImportChatInviteRequest(input_channel))
            except UserAlreadyParticipantError:
                print("已加入私有频道")
            print(s_updates)
            input_channel = s_updates.chats[0]

    input("请从列表中选择目的频道 回车继续")
    output_channel = await select_dialog()


    limit = int(input("搬运数量上限(输入0不设限): "))
    if limit == 0 or limit == None:
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
        messages = client.iter_messages(input_channel, reverse=True, limit=limit, offset_date=start_date)

    else:
        messages = client.iter_messages(input_channel, reverse=True, limit=limit)


    async for message in messages:
        # 循环中对消息时间进行判断
        if time_select == "1":
            if message.date > end_date:
                print("时间超出，结束采集")
                break

        if isinstance(message, telethon.tl.patched.Message):
            # 针对合并发送的文件(如相册)要特殊处理
            if message.grouped_id == None:
                # 普通消息直接转发
                # 如果前面还有文件则先发送文件
                if len(message_list) != 0:
                    await send_files(output_channel)
                print("普通消息转发 消息日期:", message.date)
                await client.send_message(output_channel, message)
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
                    await send_files(output_channel)
        # else:
            # print(message)
    if recorded_grouped_id != None:
        await send_files(output_channel)
    # 退出私有频道
    # if source_type == "2":
    #     await client(LeaveChannelRequest(input_channel))
    # if  target_type == "2":
    #     await client(LeaveChannelRequest(output_channel))

with client:
    client.loop.run_until_complete(main())
