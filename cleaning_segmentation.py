import os
path = 'gyu_manual_checked_cutwords/'
for F in os.listdir(path):
    print(F)
    with open(path+F, 'r', encoding='utf-8-sig') as content_file:
        content = content_file.read()
    # processing
    content = content.replace('+', ' ').replace('-', ' ').replace('!', '').replace('?', '')
    with open(path+F, 'w', encoding='utf-8-sig') as f:
        f.write(content)