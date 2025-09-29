import base64
import io
from typing import Literal

import matplotlib.pyplot as plt
from PIL import Image

def fig_to_data_uri_under_limit(fmt: Literal["png", "webp"] = "png", max_bytes: int = 100_000) -> str:

    for attempt in range(3):
        buf = io.BytesIO()
        if fmt == "png":
            plt.tight_layout()
            plt.savefig(buf, format="png", bbox_inches="tight")
            mime = "image/png"
        else:
            plt.tight_layout()
            plt.savefig(buf, format="webp", bbox_inches="tight")
            mime = "image/webp"
        data = buf.getvalue()
        if len(data) <= max_bytes:
            return "data:%s;base64,%s" % (mime, base64.b64encode(data).decode("ascii"))

        if fmt == "png":
            fmt = "webp"
            continue

        buf.seek(0)
        img = Image.open(buf)
        w, h = img.size
        scale = 0.85
        new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
        img = img.resize(new_size, Image.LANCZOS)
        buf2 = io.BytesIO()
        img.save(buf2, format="WEBP")
        data2 = buf2.getvalue()
        if len(data2) <= max_bytes:
            return "data:image/webp;base64,%s" % base64.b64encode(data2).decode("ascii")

    tiny = Image.new("RGB", (2, 2), (255, 255, 255))
    buf = io.BytesIO()
    tiny.save(buf, format="PNG")
    return "data:image/png;base64,%s" % base64.b64encode(buf.getvalue()).decode("ascii")
