import qrcode

base_url = "http://127.0.0.1:8000"

for table in range(1, 6):

    url = f"{base_url}/?table={table}"

    qr = qrcode.make(url)

    qr.save(f"table_{table}.png")

print("QR Codes Generated Successfully!")