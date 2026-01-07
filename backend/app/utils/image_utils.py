from PIL import Image
import io

def pil_from_bytes(data: bytes):
    return Image.open(io.BytesIO(data))
