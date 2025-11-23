import nextcord
OWNERS = [1333335390181920771]

# --- Top-up Settings ---
API_URL = "https://www.planariashop.com/api/truewallet.php" # URL สำหรับ API เติมเงิน
TOPUP_PHONE_NUMBER = "0630102037" # เบอร์โทรศัพท์สำหรับรับเงิน TrueMoney

# Icon URL สำหรับ footer ใน embed
# ใช้ URL ภาพที่ถูกต้อง (PNG, JPG, GIF)
emojidev = "https://cdn-icons-png.flaticon.com/512/4436/4436481.png"  # icon URL

loading = embed=nextcord.Embed(description="🔃 กำลังตรวจสอบ")

# --- Bot Secrets ---
# !! เพื่อความปลอดภัย ไม่ควรใส่ค่า Token หรือ API Key ลงในไฟล์นี้โดยตรง !!
# ควรตั้งค่าเป็น Environment Variables บนเครื่องที่จะรันบอทแทน
#
# วิธีตั้งค่า Environment Variable (ตัวอย่างบน Windows Command Prompt):
#   setx DISCORD_TOKEN "YourDiscordTokenHere"
#   setx API_KEY "YourApiKeyHere"

# Channel ID where review logs should be sent
review_log_channel = 1441848163618263301

# Channel ID where purchase logs should be sent (log buy)
logbuy = 1441821266741952666