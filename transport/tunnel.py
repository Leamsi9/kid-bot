from pyngrok import ngrok
import qrcode

async def start_tunnel():
    url = ngrok.connect(8000).public_url
    print(f"Tunnel: {url}")
    qr = qrcode.QRCode()
    qr.add_data(url)
    qr.print_ascii()
    return url
