# 📚 API Handler Documentation

## 📋 ภาพรวม

ไฟล์ `api_handler.py` จัดการการเชื่อมต่อกับ API สำหรับการเติมเงินผ่านซองอังเปา (TrueWallet Gift Link)

---

## 🚀 วิธีการใช้งาน

### วิธีที่ 1: ใช้ฟังก์ชัน `send_topup` แบบง่าย

```python
from api_handler import send_topup

result = send_topup(
    phone="0630102037",
    gift_link="https://gift.truemoney.com/campaign/?v=xxxxxxxxxxxxxxx"
)

if result['status'] == 'success':
    print(f"เติมเงินสำเร็จ {result['amount']} บาท")
else:
    print(f"ผิดพลาด: {result['message']}")
```

### วิธีที่ 2: ใช้คลาส `APIHandler` โดยตรง

```python
from api_handler import APIHandler

handler = APIHandler()

result = handler.send_topup_request(
    phone="0630102037",
    gift_link="https://gift.truemoney.com/campaign/?v=xxxxxxxxxxxxxxx",
    keyapi="optional_api_key"
)
```

### วิธีที่ 3: ใช้ instance global

```python
from api_handler import api_handler

result = api_handler.send_topup_request(
    phone="0630102037",
    gift_link="https://gift.truemoney.com/campaign/?v=xxxxxxxxxxxxxxx"
)
```

---

## 📤 Parameters

| พารามิเตอร์ | ประเภท | จำเป็น | คำอธิบาย |
|------------|--------|--------|----------|
| `keyapi` | `str` | ❌ | API Key (ถ้า API ต้องการ) |
| `phone` | `str` | ✅ | เบอร์รับเงิน (เช่น 0657425404) |
| `gift_link` | `str` | ✅ | ลิ้งซองของขวัญ TrueWallet |

---

## 📥 Response Format

### Response สำเร็จ:

```json
{
    "status": "success",
    "message": "ข้อความจาก API",
    "amount": 100.00,
    "phone": "0630102037",
    "gift_link": "https://gift.truemoney.com/campaign/?v=xxx",
    "time": "2025-11-23 10:30:00",
    "data": { "raw": "api response" }
}
```

### Response ผิดพลาด:

```json
{
    "status": "error",
    "message": "หมดเวลาตอบสนอง - ลองใหม่อีกครั้ง",
    "amount": 0,
    "phone": "",
    "gift_link": "",
    "time": "",
    "data": {}
}
```

---

## ✅ ฟังก์ชันตรวจสอบข้อมูล

### ตรวจสอบเบอร์โทรศัพท์

```python
from api_handler import api_handler

phone = "0630102037"
if api_handler.validate_phone(phone):
    print("✅ เบอร์ถูกต้อง")
else:
    print("❌ เบอร์ไม่ถูกต้อง")
```

**รูปแบบเบอร์ที่ยอมรับ:** `0xxxxxxxxx` (10 หลัก)

### ตรวจสอบลิ้งค์ซองของขวัญ

```python
gift_link = "https://gift.truemoney.com/campaign/?v=xxxxxxxxxxxxxxx"
if api_handler.validate_gift_link(gift_link):
    print("✅ ลิ้งค์ถูกต้อง")
else:
    print("❌ ลิ้งค์ไม่ถูกต้อง")
```

---

## 🔧 ตั้งค่า API

### เปลี่ยน API URL

```python
from api_handler import APIHandler

handler = APIHandler(
    api_url="https://your-custom-api.com/endpoint"
)
```

### เปลี่ยน Timeout

```python
from api_handler import api_handler

api_handler.timeout = 15  # ตั้งเป็น 15 วินาที
```

---

## 🛡️ Error Handling

API Handler จัดการ error ต่อไปนี้:

| Error Type | Description | Action |
|-----------|-------------|--------|
| `Timeout` | หมดเวลาตอบสนองจาก API | ลองใหม่อีกครั้ง |
| `ConnectionError` | ไม่สามารถเชื่อมต่อ | ตรวจสอบการเชื่อมต่ออินเทอร์เน็ต |
| `JSONDecodeError` | ไม่สามารถอ่าน JSON | ตรวจสอบ API response |
| `General Exception` | ข้อผิดพลาดอื่น ๆ | ดูใน log |

---

## 📝 ตัวอย่างใน Discord Bot

### ในภาษาคำสั่ง Modal:

```python
from api_handler import send_topup

class topupModal(nextcord.ui.Modal):
    async def callback(self, interaction: nextcord.Interaction):
        link = str(self.link.value).strip()
        phone = "0630102037"
        
        # เรียก API
        result = send_topup(phone=phone, gift_link=link)
        
        # ตรวจสอบผลลัพธ์
        if result['status'] == 'success':
            embed = nextcord.Embed(
                description=f"✅ เติมเงินสำเร็จ {result['amount']} บาท",
                color=nextcord.Color.green()
            )
        else:
            embed = nextcord.Embed(
                description=f"❌ {result['message']}",
                color=nextcord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
```

---

## 📊 Logging

API Handler ใช้ Python logging module:

```python
import logging

logging.basicConfig(level=logging.INFO)

# ตัวอักษรต่อไปนี้จะปรากฏใน console:
# INFO: ส่งคำขอ API
# ERROR: ปัญหาการเชื่อมต่อ
```

---

## 🔐 ความปลอดภัย

- **ไม่เก็บ credentials ในโค้ด** - ใช้ environment variables
- **ใช้ HTTPS** - ข้อมูลถูกเข้ารหัส
- **Timeout Protection** - ป้องกัน hang request
- **Input Validation** - ตรวจสอบรูปแบบข้อมูล

---

## ⚠️ หมายเหตุสำคัญ

1. **เบอร์โทร:** ต้องเป็นเบอร์ไทยที่มี 10 หลัก (เริ่มต้นด้วย 0)
2. **ลิ้งค์:** ต้องเป็นลิ้งค์ TrueWallet ที่ถูกต้อง
3. **API Rate Limiting:** อาจมีการจำกัดจำนวน request ต่อนาที
4. **Error Handling:** ควรมี try-except เสมอเมื่อใช้ API

---

## 📞 Support

สำหรับปัญหาการใช้งาน ให้ตรวจสอบ:
- ไฟล์ log ของ API Handler
- ตัวอย่างในไฟล์ `example_api_usage.py`
- เอกสารประกอบของ API endpoint
