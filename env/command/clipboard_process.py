import subprocess
import os
from pykeyboard import PyKeyboard
# from pymouse import *
import time
import pdb

# pip install PyUserInput pykeyboard

def get_clipboard_data():
    p = subprocess.Popen(["xclip", "-selection", "clipboard", "-o"], stdout=subprocess.PIPE)
    retcode = p.wait()
    data = p.stdout.read()
    return data

def set_clipboard_data(data):
    data = bytes(data, "utf-8")
    p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
    p.stdin.write(data)
    p.stdin.close()
    retcode = p.wait()

def test():
    # our string data
    data = "Today is a nice day!"
    
    # Set the data
    set_clipboard_data(data)
    
    # Get the new data
    new_data = get_clipboard_data()
    
    # Print it out
    print(new_data)

def copy_image_write_str():

    if 1:
        image_path="/media/nv/data/notebook/.vscode/markdown_image"

        CMD_XCLIP = {
            "has_jpg"   : "xclip -selection clipboard -t TARGETS -o | grep image/jpeg",  
            "has_png"   : "xclip -selection clipboard -t TARGETS -o | grep image/png",
            "has_txt"   : "xclip -selection clipboard -t TARGETS -o | grep text/plain;charset=utf-8",
            "save_jpg"  : "xclip -selection clipboard -t image/jpeg -o > ",
            "save_png"  : "xclip -selection clipboard -t image/png -o > ",
            "get_txt"   : "xclip -selection clipboard -t text/plain -o",
        }

        proc = subprocess.run(CMD_XCLIP['has_png'],
                                    shell=True,
                                    # stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE)
        if proc.stdout!=b'image/png\n':
            return

        with open(os.path.join(image_path,"num"), "r") as f:
            num_=int(f.read().split('\n')[0])
        with open(os.path.join(image_path,"num"), "w") as f:
            f.write(str(num_+1))
        pic_name_=os.path.join(image_path,str(num_+1)+".png")

        if 0:
            os.system("xclip -selection clipboard -t image/png -o > "+pic_name_)

        proc = subprocess.run(CMD_XCLIP['save_png']+pic_name_,
                                    shell=True,
                                    # stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE)
    else:
        pic_name_="test"

    # pic_name_2=os.path.join("",str(num_+1)+".png")
    time.sleep(0.3)
    k = PyKeyboard()

    # 无论当前输入法为 英文 / 中文-中文 / 中文-英文， 始终保证最后输入法为 英文
    k.tap_key(k.shift_l_key) # 中文-中文 / 英文
    k.tap_key(k.shift_r_key) # 中文-英文 / 英文
    k.tap_key(k.shift_l_key) # 中文-中文 / 中文
    k.tap_key(k.shift_l_key) # 英文 / 英文
    
    k.type_string("<img src=\""+pic_name_+"\" style=\"zoom:60%;\" />")

    # 关闭终端
    k = PyKeyboard()

copy_image_write_str()




