import nextcord, re, httpx, certifi
from nextcord.ext import commands
import config
OWNERS = config.OWNERS
intents = nextcord.Intents.all()
bot = commands.Bot(help_command=None, intents=intents)
import json
from nextcord.ui import TextInput, Modal, View
import requests
import os
import datetime
from api_handler import send_topup, api_handler
from myserver import server_on

# logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API key from environment (recommended) or fallback to config.KEYAPI
try:
  API_KEY = os.environ.get('API_KEY')
except Exception:
  API_KEY = None

if not API_KEY:
  API_KEY = getattr(config, 'KEYAPI', None)

if API_KEY:
  try:
    api_handler.keyapi = API_KEY
    logger.info('API key loaded into api_handler from environment/config')
  except Exception:
    logger.exception('Failed to set API key on api_handler')

# Load API URL from config and set it on the handler
API_URL = getattr(config, 'API_URL', None)
if API_URL:
  try:
    api_handler.api_url = API_URL
    logger.info('API URL loaded into api_handler from config')
  except Exception:
    logger.exception('Failed to set API URL on api_handler')


def safe_set_thumbnail(embed: nextcord.Embed, user: nextcord.User | nextcord.Member | None):
  try:
    if user and getattr(user, 'avatar', None):
      # avatar may be Asset or None
      url = user.avatar.url if hasattr(user.avatar, 'url') else str(user.avatar)
      embed.set_thumbnail(url=url)
    else:
      # remove thumbnail or set to None (no-op)
      pass
  except Exception:
    logger.exception('safe_set_thumbnail failed')


def safe_set_author(embed: nextcord.Embed, name: str, user: nextcord.User | nextcord.Member | None):
  try:
    if user and getattr(user, 'avatar', None):
      url = user.avatar.url if hasattr(user.avatar, 'url') else str(user.avatar)
      embed.set_author(name=name, url="", icon_url=url)
    else:
      embed.set_author(name=name, url="")
  except Exception:
    logger.exception('safe_set_author failed')


async def safe_send(channel, embed: nextcord.Embed):
  try:
    if channel:
      await channel.send(embed=embed)
  except Exception:
    logger.exception('safe_send failed')


async def log_purchase(data: dict):
  """Create an embed for a purchase log and send it to the configured channel.

  Also persist the log into `logs/purchases.json` as an array.
  """
  try:
    status = data.get('status', 'unknown')
    color = nextcord.Color.green() if status == 'success' else nextcord.Color.red()

    embed = nextcord.Embed(
      title=f"Purchase Log - {status}",
      description=data.get('message', ''),
      color=color
    )

    embed.add_field(name='Amount', value=str(data.get('amount', '')), inline=True)
    embed.add_field(name='Phone', value=str(data.get('phone', '')), inline=True)
    embed.add_field(name='Owner', value=str(data.get('owner_profile', '')), inline=True)
    embed.add_field(name='Redeemer', value=str(data.get('redeemer_profile', '')), inline=True)
    embed.add_field(name='Gift Link', value=str(data.get('gift_link', '')), inline=False)
    embed.set_footer(text=str(data.get('time', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))

    # send to channel if configured
    channel_id = getattr(config, 'logbuy', None)
    channel = None
    if channel_id:
      try:
        channel = bot.get_channel(int(channel_id))
      except Exception:
        channel = None

    if channel:
      await channel.send(embed=embed)

    # persist to logs/purchases.json
    os.makedirs('logs', exist_ok=True)
    path = os.path.join('logs', 'purchases.json')
    try:
      if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
          arr = json.load(f)
      else:
        arr = []
    except Exception:
      arr = []

    arr.append(data)
    with open(path, 'w', encoding='utf-8') as f:
      json.dump(arr, f, ensure_ascii=False, indent=2)

  except Exception as e:
    print('log_purchase error:', e)
class topupModal(nextcord.ui.Modal):

  def __init__(self):
    super().__init__(title='🧧 เติมเงินผ่านซองอั่งเปา', timeout=None, custom_id='topup-modal')
    self.link = TextInput(
        label='🔗 วางลิงก์ซองอั่งเปา TrueMoney ที่นี่',
        placeholder='https://gift.truemoney.com/campaign/?v=xxxxxxxxxxxxxxx',
        style=nextcord.TextInputStyle.short,
        required=True)
    self.add_item(self.link)

  async def callback(self, interaction: nextcord.Interaction):
    ########################################################################################
    try:
        link = str(self.link.value).replace(' ', '')

        # ใช้ API Handler ที่สร้างขึ้น
        phone = getattr(config, 'TOPUP_PHONE_NUMBER', None)
        response_data = await send_topup(phone=phone, gift_link=link)

        status = response_data.get('status')
        message = response_data.get('message')
        amount = response_data.get('amount')
        amount = float(amount) if amount else 0
        phone = response_data.get('phone')
        gift_link = response_data.get('gift_link')
        time = response_data.get('time')

        # ตรวจสอบสถานะ
        if status != 'success':
          await interaction.response.send_message(
            embed=nextcord.Embed(
              title="❌ เกิดข้อผิดพลาด",
              description=f"**{message}**",
              color=nextcord.Color.red()
            ),
            ephemeral=True
          )
          return

        ########################################################################################
        message = await interaction.response.send_message(embed=config.loading,ephemeral=True)

        try:
            with open('database/users.json', 'r', encoding="utf-8") as file:
              user_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            # ถ้าไฟล์ไม่มีอยู่ หรือเป็นไฟล์ว่าง/ข้อมูลไม่ถูกต้อง ให้สร้าง dict ว่างขึ้นมาใหม่
            user_data = {}

        user_id = str(interaction.user.id)
        point = float(amount) # คำนวณ point ครั้งเดียว

        if user_id in user_data:
          print("เข้าสู่ระบบสำเร็จ")
          new_point = float(user_data[user_id]['point']) + float(point)
          user_data[user_id]['point'] = str(new_point) # อัปเดต point ปัจจุบัน
          new_point = float(user_data[user_id]['all-point']) + float(point)
          user_data[user_id]['all-point'] = str(new_point)
        else:
          print("ไม่พบผู้ใช้ในระบบ")
          user_data[user_id] = {
            "userId": int(user_id),
            "point": str(0 + float(point)),
            "all-point": str(0 + float(point)),
            "historybuy": [],
            "buyrole": [],
            "buymarket": []
          }
          print("สร้างผู้ใช้ใหม่เรียบร้อยแล้ว")

        with open('database/users.json', 'w', encoding="utf-8") as file:
          json.dump(user_data, file, indent=4)
        embed = nextcord.Embed(description=f'✅ **เติมเงินสำเร็จ!**\nยอดเงินของคุณเพิ่มขึ้น **{point:.2f}** บาท',
                    color=nextcord.Color.green())
        await message.edit(content=None, embed=embed)
        safe_set_thumbnail(embed, interaction.user)
        # Prepare purchase log data and call log function
        log_data = {
          "status": "success",
          "message": "สำเร็จ",
          "amount": f"{point:.2f}",
          "phone": phone,
          # Safely get owner profile, fallback to "N/A" if not set
          "owner_profile": "<@{}>".format(config.OWNERS[0]) if config.OWNERS else "N/A",
          "redeemer_profile": interaction.user.display_name,
          "gift_link": gift_link,
          "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        try:
          await log_purchase(log_data)
        except Exception as e:
          print('Failed to log purchase:', e)

    except Exception as e:
          embed = nextcord.Embed(title="❌ เกิดข้อผิดพลาด",
                                 description="ดูเหมือนว่าลิงก์ซองอั่งเปาจะไม่ถูกต้อง \nกรุณาตรวจสอบอีกครั้ง หรือติดต่อทีมงานครับ",
                                 color=nextcord.Color.red())
          await interaction.response.send_message(embed=embed, ephemeral=True)

class sellroleView(nextcord.ui.View):

  def __init__(self, message: nextcord.Message, value: str):
    super().__init__(timeout=None)
    self.message = message
    self.value = value

  @nextcord.ui.button(label='🛒 ยืนยันการสั่งซื้อ',
                      custom_id='already',
                      style=nextcord.ButtonStyle.primary,
                      row=1)
  async def already(self, button: nextcord.Button,
                    interaction: nextcord.Interaction):
    roleJSON = json.load(open('./database/roles.json', 'r', encoding='utf-8'))
    user_id_str = str(interaction.user.id)
    
    try:
        with open('./database/users.json', 'r', encoding='utf-8') as f:
            userJSON = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        userJSON = {}

    if user_id_str not in userJSON:
      embed = nextcord.Embed(description='**🏦 คุณยังไม่มีบัญชี!**\nกรุณากดปุ่ม "เติมเงิน" เพื่อเริ่มต้นใช้งานก่อนนะครับ', color=nextcord.Color.red())
    else:
      if int(float(userJSON[str(interaction.user.id)]['point'])) >= roleJSON[self.value]['price']:
        userJSON[str(interaction.user.id)]['point'] = str(float(userJSON[str(interaction.user.id)]['point']) - roleJSON[self.value]['price'])
        userJSON[str(interaction.user.id)]['buyrole'].append({
            "role": {
                "roleId": self.value,
                "time": str(datetime.datetime.now())
            }
        })
        json.dump(userJSON,
                  open('./database/users.json', 'w', encoding='utf-8'),
                  indent=4,
                  ensure_ascii=False)
        if ('package' in self.value):
          for roleId in roleJSON[self.value]['roleIds']:
            try:
              await interaction.user.add_roles(
                  nextcord.utils.get(interaction.user.guild.roles, id=roleId))
            except Exception as e:
              logger.error(f"Failed to add role {roleId} to user {interaction.user.id}: {e}")
              # อาจจะแจ้งเตือนแอดมินหรือผู้ใช้ว่ามีปัญหา
              
          embed = nextcord.Embed(
              description=f'🎉 **ยินดีด้วย!** คุณได้รับแพ็คเกจยศ **{roleJSON[self.value]["name"]}** เรียบร้อยแล้ว',
              color=nextcord.Color.green())
          
          # เพิ่มการส่ง Log และใบเสร็จ สำหรับการซื้อแบบ package
          transactions = userJSON.get(str(interaction.user.id), {}).get("point", "0")
          log_embed = nextcord.Embed(
              title="✅ การสั่งซื้อสำเร็จ! (Package)",
              description=(
                  f"```ansi\n"
                  f"[2;34m👤 ผู้ซื้อ: {interaction.user.name}[0m\n"
                  f"[2;32m🛒 สินค้า: {roleJSON[self.value]['name']}[0m\n"
                  f"[2;31m- ราคา: {roleJSON[self.value]['price']} บาท[0m\n"
                  f"[2;33m💰 ยอดเงินคงเหลือ: {transactions} บาท[0m\n"
                  "```"
              ),
              color=nextcord.Color.green()
          )
          safe_set_thumbnail(log_embed, interaction.user)
          log_embed.add_field(name="⭐ คำแนะนำ", value="ระบบได้ส่งใบเสร็จให้ทาง DM ของคุณแล้ว\nกรุณาเก็บไว้เพื่อเป็นหลักฐานในการติดต่อทีมงานนะครับ")
          
          await self.message.edit(embed=embed, view=None, content=None)
          await interaction.user.send(embed=log_embed)

        else:
            with open('database/users.json', encoding="utf-8") as f:
                            data_dict = json.load(f)
            transactions = data_dict[str(interaction.user.id)]["point"]
            embed = nextcord.Embed(
                                                        title="✅ การสั่งซื้อสำเร็จ!",
                                                        description=(
                                                            f"```ansi\n"
                                                            f"[2;34m👤 ผู้ซื้อ: {interaction.user.name}[0m\n"
                                                            f"[2;32m🛒 สินค้า: {roleJSON[self.value]['name']}[0m\n"
                                                            f"[2;31m- ราคา: {roleJSON[self.value]['price']} บาท[0m\n"
                                                            f"[2;33m💰 ยอดเงินคงเหลือ: {transactions} บาท[0m\n"
                                                            "```"
                                                        ),
                                                        color=nextcord.Color.green()
                                                    )

            # --- ส่ง Log ไปยัง Channel ---
            channel_log_id = getattr(config, 'logbuy', None)
            if channel_log_id:
                channel_log = bot.get_channel(int(channel_log_id))
                if channel_log:
                    await channel_log.send(embed=embed)
            # -----------------------------

            safe_set_thumbnail(embed, interaction.user)

            role = nextcord.utils.get(interaction.user.guild.roles,
                                        id=roleJSON[self.value]['roleId'])
            await interaction.user.add_roles(role)
            embed.add_field(name="⭐ คำแนะนำ", value="ระบบได้ส่งใบเสร็จให้ทาง DM ของคุณแล้ว\nกรุณาเก็บไว้เพื่อเป็นหลักฐานในการติดต่อทีมงานนะครับ")
            await self.message.edit(embed=embed, view=None, content=None)
            await interaction.user.send(embed=embed)
      else:
        embed = nextcord.Embed(
            description=f'⚠️ **ยอดเงินของคุณไม่เพียงพอ!**\nขาดอีก **{roleJSON[str(self.value)]["price"] - float(userJSON[str(interaction.user.id)]["point"]):.2f}** บาท',color=nextcord.Color.red())
    return await self.message.edit(embed=embed, view=None, content=None)

  @nextcord.ui.button(label='❌ ยกเลิก',
                      custom_id='cancel',
                      style=nextcord.ButtonStyle.red,
                      row=1)
  async def cancel(self, button: nextcord.Button,
                   interaction: nextcord.Interaction):
    return await self.message.edit(content='**รายการถูกยกเลิกแล้ว**',embed=None,view=None)

class sellroleselectmain(nextcord.ui.Select):
  def __init__(self):
    options = []
    roleJSON = json.load(open('./database/roles.json', 'r', encoding='utf-8'))
    for role in roleJSON:
      options.append(
          nextcord.SelectOption(label=roleJSON[role]['name'],
                                description=roleJSON[role]['description'],
                                value=role,
                                emoji=roleJSON[role]['emoji']))
    super().__init__(custom_id='select-role',
                     placeholder='เลือกชมยศและบทบาทพิเศษของคุณที่นี่!',
                     min_values=1,
                     max_values=1,
                     options=options,
                     row=2)

  async def callback(self, interaction: nextcord.Interaction):
    message = await interaction.response.send_message(
        content='⏳ กำลังโหลดข้อมูลสินค้า...', ephemeral=True)
    selected = self.values[0]
    if ('package' in selected):
      roleJSON = json.load(open('./database/roles.json', 'r',
                                encoding='utf-8'))
      embed = nextcord.Embed()
      embed.description = f'''
E {roleJSON[selected]['name']}**
'''
      await message.edit(content=None,
                         embed=embed,
                         view=sellroleView(message=message, value=selected))
    else:
      
      roleJSON = json.load(open('./database/roles.json', 'r',
                                encoding='utf-8'))
      
      embed = nextcord.Embed(title=f"{roleJSON[selected]['emoji']} {roleJSON[selected]['title']}", color=0x5865F2)
      embed.add_field(name="📜 รายละเอียด", value=f"```{roleJSON[selected]['embeddes']}```", inline=False)
      embed.add_field(name="💰 ราคา", value=f"**{roleJSON[selected]['price']}** บาท", inline=True)
      embed.add_field(name="🎁 สิ่งที่จะได้รับ", value=f"<@&{roleJSON[selected]['roleId']}>", inline=True)
      embed.set_image(url=roleJSON[selected]['image'])
      embed.set_footer(icon_url=config.emojidev, text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
      await message.edit(content="**✨ นี่คือรายละเอียดสินค้าที่คุณเลือก**",
                         embed=embed,
                         view=sellroleView(message=message, value=selected))


class buyrole(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(sellroleselectmain())

        
class menu(nextcord.ui.Select):
    def __init__(self):

        options = [
            nextcord.SelectOption(label="ซื้อยศ / BUY ROLE", description="เลือกซื้อยศสุดพิเศษเพื่อเพิ่มความโดดเด่น", emoji="💎", value="buy_role"),
            nextcord.SelectOption(label="ซื้อสคริปต์ / BUY SCRIPT", description="เลือกซื้อสคริปต์บอทคุณภาพ", emoji="🤖", value="buy_script"),
            nextcord.SelectOption(label="ยกเลิกการเลือก", description="ล้างการเลือกปัจจุบัน", emoji="❌", value="cancel"),
        ]

        super().__init__(custom_id='menu',
                        placeholder='🛒 สนใจสินค้าหมวดไหน เชิญเลือกได้เลยครับ!',
                        min_values=1,
                        max_values=1,
                        options=options,
                        row=1)

    async def callback(self, interaction: nextcord.Interaction):
        selected_values = self.values
        if "buy_role" in selected_values:
             await interaction.response.send_message(view=buyrole() , ephemeral=True)
        elif "buy_script"  in selected_values:
             await interaction.response.send_message(view=buybot() , ephemeral=True)
        else:
             await interaction.response.send_message("ยกเลิกการเลือกแล้ว", ephemeral=True, delete_after=5)


class buybot(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(sellmarketsellprogram())
class sellmarketsellprogram(nextcord.ui.Select):
  def __init__(self):
    options = []
    IDJSON = json.load(open('./database/market.json', 'r', encoding='utf-8'))
    for role in IDJSON:
      options.append(
          nextcord.SelectOption(label=IDJSON[role]['name'],
                                description=IDJSON[role]['description'],
                                value=role,
                                emoji=IDJSON[role]['emoji']))
    super().__init__(custom_id='sellmarketui',
                     placeholder='เลือกชมสคริปต์คุณภาพดีได้ที่นี่!',
                     min_values=1,
                     max_values=1,
                     options=options,
                     row=3)

  async def callback(self, interaction: nextcord.Interaction):
    message = await interaction.response.send_message(
        content='⏳ กำลังโหลดข้อมูลสินค้า...', ephemeral=True)
    selected = self.values[0]
    if ('package' in selected):
      IDJSON = json.load(open('./database/market.json', 'r',
                                encoding='utf-8'))
      embed = nextcord.Embed()
      embed.description = f'''
E {IDJSON[selected]['name']}**
'''
      await message.edit(content=None,
                         embed=embed,
                         view=sellmarket(message=message, value=selected))
    else:
      
      IDJSON = json.load(open('./database/market.json', 'r',
                                encoding='utf-8'))
      
      embed = nextcord.Embed(title=f"{IDJSON[selected]['emoji']} {IDJSON[selected]['title']}", color=0x5865F2)
      embed.add_field(name="📜 รายละเอียด", value=f"```{IDJSON[selected]['embeddes']}```", inline=False)
      embed.add_field(name="💰 ราคา", value=f"**{IDJSON[selected]['price']}** บาท", inline=True)
      embed.set_image(url=IDJSON[selected]['image'])
      embed.set_footer(icon_url=config.emojidev, text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
      await message.edit(content="**✨ นี่คือรายละเอียดสินค้าที่คุณเลือก**",
                         embed=embed,
                         view=sellmarket(message=message, value=selected))  
      
class sellmarket(nextcord.ui.View):
  def __init__(self, message: nextcord.Message, value: str):
    super().__init__(timeout=None)
    self.message = message
    self.value = value

  @nextcord.ui.button(label='🛒 ยืนยันการสั่งซื้อ',
                      custom_id='already',
                      style=nextcord.ButtonStyle.primary,
                      row=3)
  async def already(self, button: nextcord.Button,
                    interaction: nextcord.Interaction):
    IDJSON = json.load(open('./database/market.json', 'r', encoding='utf-8'))
    user_id_str = str(interaction.user.id)
    try:
        with open('./database/users.json', 'r', encoding='utf-8') as f:
            userJSON = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        userJSON = {}
    if user_id_str in userJSON:
      transactions = userJSON[user_id_str].get('point', '0')
    else:
      transactions = '0'
    if (str(interaction.user.id) not in userJSON):
      embed = nextcord.Embed(description='**🏦 คุณยังไม่มีบัญชี!**\nกรุณากดปุ่ม "เติมเงิน" เพื่อเริ่มต้นใช้งานก่อนนะครับ', color=nextcord.Color.red())
    else:
      if int(float(userJSON[str(interaction.user.id)]['point'])) >= IDJSON[self.value]['price']:
        userJSON[str(interaction.user.id)]['point'] = str(float(userJSON[str(interaction.user.id)]['point']) - IDJSON[self.value]['price'])
        userJSON[str(interaction.user.id)]['buymarket'].append({
            "market": {
                "market": IDJSON[self.value]['name'],
                "time": str(datetime.datetime.now()),
                "market" : IDJSON[self.value]['code']
            }
        })
        json.dump(userJSON,
                  open('./database/users.json', 'w', encoding='utf-8'),
                  indent=4,
                  ensure_ascii=False)
        if ('package' in self.value):
          for roleId in IDJSON[self.value]['roleIds']:
            try:
              role_to_add = nextcord.utils.get(interaction.user.guild.roles, id=roleId)
              if role_to_add:
                await interaction.user.add_roles(role_to_add)
            except Exception as e:
              logger.error(f"Failed to add role {roleId} to user {interaction.user.id} during package purchase: {e}")
          channelLog = bot.get_channel(config.logbuy)
          if channelLog:
            embed = nextcord.Embed(
              title="✅ การสั่งซื้อสำเร็จ!",
              description=(
                f"```ansi\n"
                f"[2;34m👤 ผู้ซื้อ: {interaction.user.name}[0m\n"
                f"[2;32m🛒 สินค้า: {IDJSON[self.value]['name']}[0m\n"
                f"[2;31m- ราคา: {IDJSON[self.value]['price']} บาท[0m\n"
                f"[2;33m💰 ยอดเงินคงเหลือ: {transactions} บาท[0m\n"
                "```"
              ),
              color=nextcord.Color.green()
            )
            await channelLog.send(embed=embed)
          embed = nextcord.Embed(
              description=
              f'🎉 **ยินดีด้วย!** คุณได้รับ <@&{IDJSON[self.value]["name"]}> เรียบร้อยแล้ว',
              color=nextcord.Color.green())
          await self.message.edit(embed=embed, view=None, content=None)
        else:
          channelLog = bot.get_channel(config.logbuy)
          transactions = userJSON.get(str(interaction.user.id), {}).get("point", "0")

          # Build embed for non-package purchase
          embed = nextcord.Embed(
            title="✅ การสั่งซื้อสำเร็จ!",
            description=(
              f"```ansi\n"
              f"[2;34m👤 ผู้ซื้อ: {interaction.user.name}[0m\n"
              f"[2;32m🛒 สินค้า: {IDJSON[self.value]['name']}[0m\n"
              f"[2;31m- ราคา: {IDJSON[self.value]['price']} บาท[0m\n"
              f"[2;33m💰 ยอดเงินคงเหลือ: {transactions} บาท[0m\n"
              "```"
            ),
            color=nextcord.Color.green()
          )

          safe_set_thumbnail(embed, interaction.user)

          # --- ส่ง Log ไปยัง Channel ---
          channel_log_id = getattr(config, 'logbuy', None)
          if channel_log_id:
              channel_log = bot.get_channel(int(channel_log_id))
              if channel_log:
                  await channel_log.send(embed=embed)
          # -----------------------------
          
          embed.add_field(name="🚀 รับสคริปต์ของคุณที่นี่!", value=f"คลิกเพื่อดาวน์โหลด: [**ดาวน์โหลดทันที!**]({IDJSON[self.value]['code']})\n*กรุณาเก็บลิงก์นี้ไว้ให้ดี*", inline=False)
          embed.add_field(name="⭐ คำแนะนำ", value="ระบบได้ส่งใบเสร็จและลิงก์ดาวน์โหลดให้ทาง DM ของคุณแล้ว\nกรุณาเก็บไว้เพื่อเป็นหลักฐานในการติดต่อทีมงานนะครับ",inline=False)
          await self.message.edit(embed=embed, view=None, content=None)
          await interaction.user.send(embed=embed)
      else:
        embed = nextcord.Embed(
            description=f'⚠️ **ยอดเงินของคุณไม่เพียงพอ!**\nขาดอีก **{IDJSON[str(self.value)]["price"] - float(userJSON[str(interaction.user.id)]["point"]):.2f}** บาท',color=nextcord.Color.red())
    return await self.message.edit(embed=embed, view=None, content=None)

  @nextcord.ui.button(label='❌ ยกเลิก',
                      custom_id='cancel',
                      style=nextcord.ButtonStyle.red,
                      row=3)
  async def cancel(self, button: nextcord.Button,
                   interaction: nextcord.Interaction):
    return await self.message.edit(content='**รายการถูกยกเลิกแล้ว**',embed=None,view=None)


@bot.event
async def on_ready():
    print(f'BOT NAME : {bot.user}')
    bot.add_view(mainui())



class mainui(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(menu())

    @nextcord.ui.button(label='เติมเงิน (อั่งเปา)',
                        emoji="💸",
                        custom_id='t1',
                        style=nextcord.ButtonStyle.blurple,
                        row=2)
    async def t1(self, button: nextcord.Button,
                        interaction: nextcord.Interaction):
            await interaction.response.send_modal(topupModal())
    @nextcord.ui.button(label='เช็คยอดเงิน',
                        emoji="💰",
                        custom_id='t2',
                        style=nextcord.ButtonStyle.blurple,
                        row=2)
    async def t2(self, button: nextcord.Button,
                        interaction: nextcord.Interaction):
        userJSON = json.load(open('./database/users.json', 'r', encoding='utf-8'))
        if (str(interaction.user.id) not in userJSON):
            embed = nextcord.Embed(description='**🏦 คุณยังไม่มีบัญชี!**\nกรุณากดปุ่ม "เติมเงิน" เพื่อเริ่มต้นใช้งานก่อนนะครับ',
                                color=nextcord.Color.red())
            safe_set_thumbnail(embed, interaction.user)
        else:
            embed = nextcord.Embed(
                description=
                f'╔═══════▣◎▣═══════╗\n\n💳﹒ยอดเงินคงเหลือ **__{userJSON[str(interaction.user.id)]["point"]}__** บาท\n\n╚═══════▣◎▣═══════╝',
                color=nextcord.Color.green())
            safe_set_thumbnail(embed, interaction.user)

        await interaction.response.send_message(embed=embed, ephemeral=True)
    @nextcord.ui.button(label='บันทึกยศปัจจุบัน',
                        emoji="💾",
                        custom_id='t3',
                        style=nextcord.ButtonStyle.green,
                        row=2)
    async def t3(self, button: nextcord.Button,
                        interaction: nextcord.Interaction):
                        user = interaction.user
                        role_data = [role.name for role in user.roles if "@everyone" not in role.name]
                        file_path = f"saveroles/role_{user.name}.json"

                        try:
                            with open(file_path, "w", encoding='utf-8') as f:
                                json.dump(role_data, f)
                        except Exception as e:
                            print(f"Error saving roles: {e}")
                            await interaction.response.send_message("An error occurred while saving roles.", ephemeral=True)
                            return

                        embed = nextcord.Embed(title="บันทึกยศที่เซฟ", color=0xdddddd)

                        safe_set_thumbnail(embed, interaction.user)
                        # Set author safely
                        safe_set_author(embed, "ระบบเชฟยศอัติโนมัติ", user)
                        formatted_roles = "\n".join(role_data)
                        embed.add_field(name="ยศที่เชฟเสร็จสิ้น", value=f"```\n{formatted_roles}```", inline=False)
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        
                        # แก้ไข: ดึง ID ของ channel จาก config
                        log_channel_id = getattr(config, 'logsaverole', None)
                        channel = None
                        if log_channel_id:
                            channel = bot.get_channel(int(log_channel_id))
                        log_embed = nextcord.Embed(title="บันทึกเรียบร้อย 📝", color=0xdddddd)
                        safe_set_thumbnail(log_embed, interaction.user)
                        log_embed.add_field(name="ยศที่เซฟ", value=f"```{formatted_roles}```", inline=False)
                        log_embed.add_field(name="ผู้เชฟ", value=f"> {interaction.user.mention}", inline=False)
                        # Only attempt to send the log if the channel exists
                        if channel:
                          await channel.send(embed=log_embed)
    @nextcord.ui.button(label='กู้คืนยศ',
                            emoji="🔄",
                            custom_id='t4',
                            style=nextcord.ButtonStyle.green,
                            row=2)
    async def t4(self, button: nextcord.Button,
                            interaction: nextcord.Interaction):
                    user = interaction.user
                    file_path = f"saveroles/role_{user.name}.json"
                    try:
                        with open(file_path, "r", encoding='utf-8') as f:
                            role_data = json.load(f)
                            for role_name in role_data:
                                roles = nextcord.utils.get(interaction.guild.roles, name=role_name)
                                await user.add_roles(roles)
                        await interaction.response.send_message("```diff\n+ คืนยศให้คุณเรียบร้อยแล้ว\n```", ephemeral=True)
                    except FileNotFoundError:
                        await interaction.response.send_message("```diff\n- ขออภัยไม่มีข้อมูลของคุณ```", ephemeral=True)
                    except Exception as e:
                        await interaction.response.send_message(f"```diff\n- เกิดข้อผิดพลาด: {e}\n```", ephemeral=True)
    @nextcord.ui.button(label='โปรไฟล์ของฉัน',
                            emoji="👤",
                            custom_id='t5',
                            style=nextcord.ButtonStyle.primary,
                            row=2)
    async def t5(self, button: nextcord.Button,
                            interaction: nextcord.Interaction):
                    user = interaction.user

                    created_since = (interaction.message.created_at - user.created_at).days
                    created_since_str = f"```{created_since} วันที่ผ่านมา```"

                    user_info_embed = nextcord.Embed(title=f"ข้อมูลของ {user.display_name}", color=0xffffff)
                    safe_set_thumbnail(user_info_embed, interaction.user)
                    user_info_embed.add_field(name="ID Discord", value=f"```{user.id}```", inline=False)
                    user_info_embed.add_field(name="วันที่สร้างบัญชี", value=created_since_str, inline=False)

                    if len(user.roles) > 1:
                        roles = "\n ".join([role.mention for role in user.roles[1:]])
                        user_info_embed.add_field(name="บทบาท", value=roles, inline=False)

                    if user.premium_since:
                        user_info_embed.add_field(name="Nitro Boost", value="เป็น Nitro Boost ตั้งแต่: " + user.premium_since.strftime("%Y-%m-%d"), inline=False)


                    await interaction.response.send_message(embed=user_info_embed, ephemeral=True)
    @nextcord.ui.button(label='ให้คะแนนร้านค้า',
                            emoji="⭐",
                            custom_id='a1',
                            style=nextcord.ButtonStyle.primary,
                            row=3)
    async def a1(self, button: nextcord.Button,
           interaction: nextcord.Interaction):
      thank_you_message = "ขอบคุณสำหรับการรีวิว!"

      await interaction.response.send_message(thank_you_message, ephemeral=True)
      user_id = str(interaction.user.id)
      user_review_file = f"Review/{user_id}.json"

      # Ensure the Review directory exists before writing the file
      review_dir = os.path.dirname(user_review_file)
      if review_dir and not os.path.exists(review_dir):
        os.makedirs(review_dir, exist_ok=True)

      if not os.path.exists(user_review_file):
        with open(user_review_file, "w", encoding='utf-8') as f:
          json.dump({"reviewed": True}, f)

        # Read review log channel from config (if set)
        try:
          reviewlog = getattr(config, 'review_log_channel', None)
        except Exception:
          reviewlog = None

        channel = None
        if reviewlog:
          try:
            # ensure integer
            channel_id = int(reviewlog)
            channel = bot.get_channel(channel_id)
          except Exception:
            channel = None
        log_embed = nextcord.Embed(
          title="> THANK FOR REVIEW   ",
          description=(f"__รายละเอียดการรีวิว__ \n\n 💕 ขอบคุณผู้ใช้งาน : {interaction.user.mention} \n\n"
                 " 💕         **THANK YOU** 💕 "),
          color=0x7289da
        )
        safe_set_thumbnail(log_embed, interaction.user)
        if channel:
          await channel.send(embed=log_embed)
      else:
        await interaction.followup.send("คุณรีวิวไปแล้วครับ!", ephemeral=True)
    @nextcord.ui.button(label='สถิติบันทึกยศ',
                            emoji="📊",
                            custom_id='a2',
                            style=nextcord.ButtonStyle.primary,
                            row=3)
    async def a2(self, button: nextcord.Button,
                            interaction: nextcord.Interaction):
        folder_path = "saveroles"  # ตั้งค่า path ของโฟลเดอร์ที่เก็บข้อมูล
        files = os.listdir(folder_path)
        saved_roles_count = len(files)
        embed = nextcord.Embed(title="ระบบเช็คจำนวนเชฟยศ" , description=saved_roles_count, color=0xffffff)
        safe_set_thumbnail(embed, interaction.user)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    @nextcord.ui.button(label='ยศทั้งหมดของฉัน',
                            emoji="📜",
                            custom_id='a4',
                            style=nextcord.ButtonStyle.primary,
                            row=3)
    async def a4(self, button: nextcord.Button,
                            interaction: nextcord.Interaction):
                    user = interaction.user

                    created_since = (interaction.message.created_at - user.created_at).days
                    created_since_str = f"```{created_since} วันที่ผ่านมา```"

                    user_info_embed = nextcord.Embed(title=f"ข้อมูลของ {user.display_name}", color=0xffffff)

                    if len(user.roles) > 1:
                      roles = "\n ".join([role.mention for role in user.roles[1:]])
                      user_info_embed.add_field(name="บทบาท", value=roles, inline=False)
                    await interaction.response.send_message(embed=user_info_embed, ephemeral=True)

@bot.slash_command( description="ติดตั้งได้หมด")
async def setup(interaction: nextcord.Interaction):

            embed=nextcord.Embed(title=f"⭐ 𝗬𝗼𝗸𝗙𝗿𝗲𝗲𝗳𝗼𝗿𝘆𝗼𝘂 - บริการร้านค้าอัตโนมัติ ⭐")
    
            des = '''```ansi
[2;34m[1;47m  🛒 WELCOME TO OUR AUTOMATED SHOP 🛒  [0m
```
```ansi
[2;32m✅ ช้อปยศ & ไอเทมได้ 24 ชั่วโมง ไม่มีวันหยุด[0m
[2;33m✨ เติมเงินง่ายๆ ผ่านซองอั่งเปา TrueMoney[0m
[2;36m🚀 ซื้อปุ๊บ ได้รับของทันที ไม่ต้องรอแอดมิน[0m
[2;35m💰 แค่เติมเงินครั้งแรก ก็เปิดบัญชีพร้อมช้อปได้เลย[0m
```'''
            embed.add_field(name="", value=des, inline=False)

            des = '''```diff
! ยินดีต้อนรับสู่ร้านค้าของเรา
ช้อปสนุกได้ทุกเวลา สินค้าคุณภาพดี อัปเดตตลอด
สนับสนุนร้านเรา รับรองไม่มีผิดหวังครับ!
```'''
            embed.add_field(name="`🛍️` เกี่ยวกับร้านค้า", value=des, inline=True)

            des = '''```diff
+ 1. กดปุ่ม [เติมเงิน] ด้านล่าง
+ 2. ใส่ลิงก์ซองอั่งเปา TrueMoney
+ 3. ระบบจะเติมเงินเข้าบัญชีให้อัตโนมัติ!
```'''
            embed.add_field(name="`💸` วิธีการเติมเงิน", value=des, inline=True)

            des = '''```diff
+ พบปัญหาการใช้งาน หรือต้องการความช่วยเหลือ?
  สามารถติดต่อทีมงานได้ทันที เราพร้อมดูแลคุณ
---
ขอให้สนุกกับการช้อปปิ้งครับ!
```'''
            embed.add_field(name="`💬` ข้อความจากทีมงาน", value=des, inline=False)

            embed.set_image(url="https://media.discordapp.net/attachments/1201027737004019782/1244129061194829897/unknown_3.jpg?ex=6923273a&is=6921d5ba&hm=2c895963b31fd00e41e47cc31bb495b2a40a8df68ad8cd8cd4fd792d2606ec7d&=&format=webp&width=1088&height=544")
            rent = await interaction.channel.send(embed=embed, view=mainui())

server_on()  # Start the server for uptime monitoring

if __name__ == "__main__":
  # Prefer token from environment for safety; fallback to config or hard-coded token if needed.
  token = os.environ.get('DISCORD_TOKEN')
  if token:
    bot.run(token)
  else:
    # If no env var provided, try to read from config (only if you intentionally set it there).
    try:
      import config
      token = getattr(config, 'DISCORD_TOKEN', None)
    except Exception:
      token = None

    if token:
      bot.run(token)
    else:
      print('DISCORD_TOKEN not set; skipping bot.run when imported for testing.')
