"""
ตัวอย่างการใช้งาน API Handler
"""

import asyncio
from api_handler import send_topup, api_handler

# ตัวอย่างที่ 1: ส่งคำขอเติมเงินแบบง่าย
print("=" * 60)
print("ตัวอย่างที่ 1: ส่งคำขอเติมเงินแบบง่าย")
print("=" * 60)

result = asyncio.run(send_topup(
    phone="0630102037",
    gift_link="https://gift.truemoney.com/campaign/?v=xxxxxxxxxxxxxxx"
))

print(f"Status: {result['status']}")
print(f"Message: {result['message']}")
print(f"Amount: {result['amount']}")
print(f"Phone: {result['phone']}")
print(f"Time: {result['time']}")


# ตัวอย่างที่ 2: ส่งคำขอพร้อม API Key
print("\n" + "=" * 60)
print("ตัวอย่างที่ 2: ส่งคำขอพร้อม API Key")
print("=" * 60)

result = asyncio.run(send_topup(
    phone="0630102037",
    gift_link="https://gift.truemoney.com/campaign/?v=xxxxxxxxxxxxxxx",
    keyapi="your_api_key_here"
))

print(f"Status: {result['status']}")
print(f"Message: {result['message']}")
print(f"Amount: {result['amount']}")


# ตัวอย่างที่ 3: ตรวจสอบรูปแบบเบอร์และลิ้งค์ก่อนส่ง
print("\n" + "=" * 60)
print("ตัวอย่างที่ 3: ตรวจสอบรูปแบบก่อนส่ง")
print("=" * 60)

phone = "0630102037"
gift_link = "https://gift.truemoney.com/campaign/?v=xxxxxxxxxxxxxxx"

if api_handler.validate_phone(phone):
    print(f"✅ เบอร์ถูกต้อง: {phone}")
else:
    print(f"❌ เบอร์ไม่ถูกต้อง: {phone}")

if api_handler.validate_gift_link(gift_link):
    print(f"✅ ลิ้งค์ถูกต้อง: {gift_link}")
else:
    print(f"❌ ลิ้งค์ไม่ถูกต้อง: {gift_link}")


# ตัวอย่างที่ 4: จัดการ response ที่มี error
print("\n" + "=" * 60)
print("ตัวอย่างที่ 4: จัดการ Response แบบละเอียด")
print("=" * 60)

result = asyncio.run(send_topup(
    phone="0630102037",
    gift_link="https://gift.truemoney.com/campaign/?v=xxxxxxxxxxxxxxx"
))

if result['status'] == 'success':
    print(f"✅ เติมเงินสำเร็จ")
    print(f"   จำนวนเงิน: {result['amount']} บาท")
    print(f"   เบอร์รับเงิน: {result['phone']}")
    print(f"   เวลา: {result['time']}")
else:
    print(f"❌ เติมเงินล้มเหลว")
    print(f"   เหตุผล: {result['message']}")
