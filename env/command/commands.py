import subprocess
import sys
import glob,pdb
import os
import re,signal,shutil
from command_list import *


def get_scp_command(sys_argv):
  scp_commnad = None
  if len(sys.argv)<2:
    return ""
  if sys.argv[1]=='scp' and sys.argv[2] !='-r':
    scp_commnad = "scp"
    source_path = sys.argv[2]
    dest_path = sys.argv[3]
  elif sys.argv[1]=='scp' and sys.argv[2]=='-r':
    scp_commnad = "scp -r"
    source_path = sys.argv[3]
    dest_path = sys.argv[4]
  else:
    return "scp command not support"

  source_device = source_path.split(":")[0]
  dest_device = dest_path.split(":")[0]

  source_file = source_path[source_path.find(":")+1:]
  dest_file = dest_path[dest_path.find(":")+1:]

  ip_dict = {}
  ip_dict['local'] = ""
  ip_dict['robot1'] = 'nerv@192.168.111.50:'
  ip_dict['robot1wifi'] = 'nerv@192.168.110.150:'
  ip_dict['robot2'] = 'nerv@192.168.112.60:'
  ip_dict['pc1'] = 'wujie@192.168.110.90:'
  command = scp_commnad + " " + ip_dict[source_device] + source_file + " " + ip_dict[dest_device] + dest_file
  return command

def kill_process(process_name, force_flag = True):
  temp=subprocess.check_output("ps aux|grep "+process_name,shell=True)
  temp=str(temp).split('\\n')
  temp=[i for i in temp if process_name in i]

  for process_one in temp:
    if "grep" in process_one:
      continue

    ii = re.split(r" +",process_one)[1]
    print(ii)
    print("kill "+ii)

    if force_flag:
      subprocess.run("kill -9 "+ii,shell=True)
    else:
      subprocess.run("kill "+ii,shell=True)

def execute_command(run_command):

  if "source" in run_command:
    from pynput.keyboard import Key, Controller
    keyboard = Controller()
    keyboard.type(run_command)
  else:
    subprocess.run(run_command,shell=True)


  # subprocess.run(
  #     ["bash", "-c", run_command],
  #     executable="/bin/bash"
  # )

  # run_command = run_command.split(' ')
  # process = subprocess.Popen(run_command, preexec_fn=os.setsid)
  # try:
  #   # 等待进程结束
  #   process.wait()
  # except KeyboardInterrupt:
  #   # 捕获 Ctrl+C，发送信号到整个进程组
  #   os.killpg(os.getpgid(process.pid), signal.SIGINT)

def backup_vscode():
  src_dir = os.path.expanduser("~/Library/Application Support/Code/User")
  dst_dir = "/Users/abc/Documents/notebook_xinmier/env/vscode"
  os.makedirs(dst_dir, exist_ok=True)
  for filename in ["settings.json", "keybindings.json"]:
    src = os.path.join(src_dir, filename)
    if not os.path.exists(src):
      print(f"{src} not found, skipping")
      continue
    existing = glob.glob(os.path.join(dst_dir, filename + ".*"))
    max_idx = 0
    for f in existing:
      try:
        idx = int(f.rsplit(".", 1)[-1])
        max_idx = max(max_idx, idx)
      except ValueError:
        pass
    dst = os.path.join(dst_dir, f"{filename}.{max_idx + 1}")
    shutil.copy2(src, dst)
    print(f"backed up: {dst}")

def help_func():
  print_len=12
  if len(sys.argv)==1 or (sys.argv[1]=='h'):
    for i in range(len(short_list)):
      cur_len=0
      for ii in short_list[i]:
        print(ii+" ",end="")
        cur_len=cur_len+len(ii)+1
      for ii in range(cur_len,print_len):
        print(" ",end='')

      if i<len(desp_list):
        print(": "+desp_list[i])
      else:
        print("\n")
      if len(sys.argv)>1:
        if sys.argv[1]=='h':
          for ii in range(print_len+4):
            print(" ",end='')
          print(command_list[i])
    return True
  return False

if __name__ == "__main__":
  if help_func() == False:
    run_finished = False
    for i in range(len(short_list)):
      if sys.argv[1] in short_list[i]:

        command_str = command_list[i]
        if "spec_" not in command_str:

          for placeholder_idx in range(1,20):
            placeholder = f'{{{placeholder_idx}}}'
            if placeholder in command_str:
              if len(sys.argv) > placeholder_idx + 1:
                command_str = command_str.replace(
                    placeholder, sys.argv[placeholder_idx + 1]
                )
              else:
                print(f"missing argument for placeholder {placeholder}")
                break
            else:
              break
              
          print(command_str)
          if sys.argv[-1] !='-p':
            execute_command(command_str)
        else:
          if command_str=="spec_1":
            kill_process(sys.argv[-1])
          elif command_str=="spec_backupvscode":
            backup_vscode()
          elif command_str=="spec_2":
            pass
        run_finished = True
        break
    if run_finished == False:
      print("command not supported")
