from PIL import Image
im = Image.open(r"D:\git\maa-ww\review\inbox\20261031-222801-goto-start.png").convert("RGB")
# sample around first row button ~ (1128, 271)
for y in range(250, 300, 5):
    for x in range(1080, 1180, 10):
        r,g,b = im.getpixel((x,y))
        if r > 140:
            print(x,y,r,g,b)
