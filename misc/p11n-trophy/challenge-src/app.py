#!/usr/bin/python3
import sys
import os
import requests
import random
import string
import hashlib
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, send_file
app = Flask(__name__)

@app.route('/')
def hii():
    cert_fn = generate_cert()
    if cert_fn:
        return send_file(cert_fn, as_attachment=True)
    else:
        return 'There was a problem generating your certificate. Please open a support ticket on the x3CTF Discord server.'

def generate_cert():
    TEAM_NAME = "player"
    TEAM_NAME = "fakeplayer"
    try:
        team_id = os.environ['CHALLENGE_NAMESPACE'].replace("challenge-", "")
        TEAM_NAME = team_id
        TEAM_NAME = [x for x in requests.get("https://x3c.tf/api/v2/players").json() if x["id"] == team_id][0]["name"]
    except:
        pass

    cert_fn = f"/tmp/certificate_{''.join(filter(lambda x: x in set(string.ascii_letters + string.digits + '_'), TEAM_NAME.replace(' ','_')))[:64]}.pdf"
    if os.path.exists(cert_fn):
        return cert_fn

    try:
        SHA = hashlib.sha256(b"cert_" + TEAM_NAME.encode() + b"_mvm").hexdigest()

        url = f'https://x3c.tf/certs/{SHA}.pdf'
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(cert_fn, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        return cert_fn
    except:
        try:
            os.remove(cert_fn)
        except:
            pass
        pass

    TARGET_MVM_COUNT = 9336
    OTHER_MVMS = 3 + len(TEAM_NAME.lower().split("mvm"))-1
    
    random.seed(TEAM_NAME)
    
    font_size = 96
    font = ImageFont.truetype("MonsieurLaDoulaise-Regular.ttf", font_size)
    
    other_pats = [Image.open(fn) for fn in ["vvv_pattern.png", "wvw_pattern.png"]]
    
    pat_mvm     = Image.open("mvm_pattern.png")
    pat_mvm_p       = pat_mvm.load()
    im      = Image.open("x3_transparent.png")
    im_final= Image.open("x3_transparent.png")
    pix     = im.load()
    draw = ImageDraw.Draw(im)
    width, height = im.size
    mvm_count = 0
    mvms = []
    pat_w = 31
    pat_h = 11
    
    t_w = draw.textlength(TEAM_NAME, font=font)
    draw.text(xy=(2047 - (t_w/2), 1914 - 32 - font_size),text=TEAM_NAME,font=font, fill="#D25476")
    
    for h in range((height-pat_h)//pat_h):
        print(f"Generating: {(h*100)//(height//pat_h-2)}%")
        for w in range((width-pat_w)//pat_w):
            ok=True
            w_off = (2 - (h%3))*(pat_w//3)
            im_final.paste(random.choice(other_pats),(w*pat_w+w_off,h*pat_h))
            for x in range(pat_w):
                for y in range(pat_h):
                    if pix[(w*pat_w+x+w_off,h*pat_h+y)][3] > 0:
                        ok=False
                        break
                if not ok:
                    break
            if ok:
                mvm_count += 1
                mvms.append((w*pat_w+w_off,h*pat_h))
    
    random.shuffle(mvms)
    mvms = mvms[:TARGET_MVM_COUNT - OTHER_MVMS]
    
    for mvm in mvms:
        w = mvm[0]
        h = mvm[1]
        im.paste(pat_mvm,(w,h))
    im_final.paste(im, (0,0), im)
    pix_final = im_final.load()
    
    im_final.save(cert_fn, "PDF", resolution=300.0, quality=100.00)
    return cert_fn

if __name__ == "__main__":
    app.run(debug=False)
