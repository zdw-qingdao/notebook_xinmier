import pdb,sys

short_list=[]
command_list=[]
desp_list=[]

# ------------------------------------------------------- ssh relevant

short_list.append(['backupvscode'])
command_list.append("spec_backupvscode")
desp_list.append("backup vscode settings.json and keybindings.json")

short_list.append(['622'])
command_list.append("ssh zhongdawei@122.225.62.2")
desp_list.append("622")

short_list.append(['622w'])
command_list.append("ssh wangyang@122.225.62.2")
desp_list.append("622w")

short_list.append(['629'])
command_list.append("ssh zhongdawei@122.225.62.9")
desp_list.append("622")

short_list.append(['628'])
command_list.append("ssh zhongdawei@122.225.62.8")
desp_list.append("628")

short_list.append(['629a'])
command_list.append("ssh admin1@122.225.62.9")
desp_list.append("622a")

short_list.append(['622mount'])
command_list.append("sshfs zhongdawei@122.225.62.2:/mnt/data1/ /Users/abc/Documents/remote/622_data1")
desp_list.append("622mount")

short_list.append(['629mount'])
command_list.append("sshfs admin1@122.225.62.9:/mnt/data1/ /Users/abc/Documents/remote/629_data1")
desp_list.append("629mount")

short_list.append(['local'])
command_list.append("ssh ubuntu@192.168.31.100")
desp_list.append("local")



'''
python model_run.py -i -c config/model_train.json
python model_run.py -i -c config/model_inference.json

# Edit ~/.zshrc or ~/.bashrc  
# export ZENMUX_API_KEY="sk-ss-v1-f44104aa805e3c95e5a20623f01ded734e286c6a2266c41b3078a2b1de3ae772"

sudo mount -t nfs 192.168.200.20:/mnt/data1/data_server/collections /mnt/data1/data_server/collections
sudo mount -t nfs 192.168.200.20:/mnt/data1/data_server/models /mnt/data1/data_server/models
sudo mount -t nfs 192.168.200.20:/mnt/data1/data_server/code /mnt/data1/data_server/code
sudo mount -t nfs 192.168.200.20:/mnt/data1/data_server/datasets /mnt/data1/data_server/datasets
sudo mount -t nfs 192.168.200.20:/mnt/data1/data_server/info /mnt/data1/data_server/info

查看硬盘io
iostat -x 2 sdb


统计文件数量
ls -l | grep "^-" | wc -l


安装deb安装包：
mkdir -p ~/.config/mihomo
wget -O ~/.config/mihomo/config.yaml https://services.cu-te.cn/link?token=26b374511d3c6f8f254f020f860fdad7
not work, use claude to refine the format

后台运行：
nohup mihomo -d ~/.config/mihomo > ~/.config/mihomo/mihomo.log 2>&1 &


https://services.cu-te.cn/link?token=26b374511d3c6f8f254f020f860fdad7

alias qwe="python3 /Users/air/Documents/notebook_xinmier/env/command/commands.py"

'''


