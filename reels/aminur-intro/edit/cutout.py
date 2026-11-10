import sys, os
from rembg import new_session, remove
from PIL import Image, ImageFilter
s=new_session("u2net_human_seg")
A=os.environ.get("REEL_ASSETS", os.path.dirname(os.path.abspath(__file__))+"/assets")
for i in list(range(0,66))+list(range(1200,1315)):
    o=f"{A}/cut/c_{i:04d}.png"
    if os.path.exists(o): continue
    im=Image.open(f"{A}/raw/f_{i:04d}.jpg")
    m=remove(im,session=s,only_mask=True,post_process_mask=False)
    m=m.filter(ImageFilter.GaussianBlur(1.2))
    im=im.convert("RGBA"); im.putalpha(m); im.save(o,compress_level=3)
print("CUTDONE")
