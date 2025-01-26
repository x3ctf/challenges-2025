from PIL import Image

pat_mvm     = Image.open("mvm_pattern.png")
pat_mvm_p       = pat_mvm.load()
im      = Image.open("000.jp2")
pix     = im.load()
width, height = im.size
mvm_count = 0
mvms = []

for h in range(height-30):
    print(f"Checking: {(h*100)//(height-31)}%")
    for w in range(width-11):
        ok=True
        for x in range(1,30):
            for y in range(11):
                if pix[(w+x,h+y)] != pat_mvm_p[(x,y)]:
                    ok=False
                    break
            if not ok:
                break
        if ok:
            last_ok_w = w
            mvm_count += 1
            mvms.append((w,h))

print(f"Counted {mvm_count} mvms!")
