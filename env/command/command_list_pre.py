import subprocess
import sys
import glob,pdb
import os
import re,signal


short_list=[]
command_list=[]
desp_list=[]

short_list.append(['bashrc'])
command_list.append("gedit /home/nv/.bashrc")
desp_list.append("bashrc")

short_list.append(['remove'])
command_list.append("cd /media/nv/data/running_results && rm -r ./*")
desp_list.append("remove ego")

short_list.append(['rmego'])
command_list.append("cd /media/nv/data/running_results/egomotion && rm -r ./*")
desp_list.append("remove ego")

short_list.append(['rmcam'])
command_list.append("cd /media/nv/data/running_results/camera_calibration && rm -r ./*")
desp_list.append("remove cam")

short_list.append(['rmradar'])
command_list.append("cd /media/nv/data/running_results/radar_calibration && rm -r ./*")
desp_list.append("remove cam")

short_list.append(['cl'])
command_list.append("git push origin HEAD:refs/for/av-dev-l2pp-2")
desp_list.append("remove cam")

# ------------------------------- egomotion
short_list.append(['111','ndas'])
command_list.append("python /media/nv/data/notebook/run_scripts/ndas_run.py")
desp_list.append("egomotion param1: data param2: out-path")

short_list.append(['csv'])
command_list.append("python /media/nv/data/notebook/draw_csv.py")
desp_list.append("tmp")


short_list.append(['amend'])
command_list.append("python /media/nv/data/notebook/run_scripts/ndas_run.py -n amend")
# command_list.append("echo \'dazel run //:format\'")
desp_list.append("amend")

short_list.append(['format'])
command_list.append("python /media/nv/data/notebook/run_scripts/ndas_run.py -n format")
# command_list.append("echo \'dazel run //:format\'")
desp_list.append("format")

short_list.append(['coverity'])
command_list.append("python /media/nv/data/notebook/run_scripts/ndas_run.py -n coverity")
desp_list.append("coverity")

short_list.append(['ut'])
command_list.append("python /media/nv/data/notebook/run_scripts/ndas_run.py -n ut")
desp_list.append("ut")

short_list.append(['contour'])
command_list.append("python /media/nv/data/notebook/run_scripts/ndas_run.py -n contour")
desp_list.append("contour")


short_list.append(['contour_test'])
command_list.append("python /media/nv/data/notebook/run_scripts/ndas_run.py -n contour_test")
desp_list.append("contour_test")

short_list.append(['contour_coverity'])
command_list.append("python /media/nv/data/notebook/run_scripts/ndas_run.py -n contour_coverity")
desp_list.append("contour_coverity")

short_list.append(['jupyter'])
command_list.append("python /media/nv/data/notebook/run_scripts/ndas_run.py -n jupyter")
desp_list.append("jupyter")

short_list.append(['format2'])
command_list.append("echo \'dazel run //:generate\'")
desp_list.append("format")

short_list.append(['format_check'])
command_list.append("echo \'dazel run //tools/validate_commit_message\'")
desp_list.append("remove cam")

short_list.append(['push'])
command_list.append("git push origin HEAD:refs/for/av-dev-l2pp-2")
desp_list.append("push_origin")


short_list.append(['author'])
command_list.append("git commit --amend --reset-author --no-edit")
desp_list.append("set author")

short_list.append(['kpi'])
command_list.append("echo \'open-loop us l2pp context fusion mapless rwd ---- open-loop us l2pp wait conditions false positives rwd\'")
desp_list.append("push_origin")

short_list.append(['teststudio1_kpi'])
command_list.append("maglev ts run --suites 019541ac-01f8-42c0-0730-7f90ecd2aaa0 --ndas-commit")
desp_list.append("studio1")

short_list.append(['teststudio2_kpi_fp'])
command_list.append("maglev ts run --suites 0194fe7e-9812-46dc-06d2-4f072c0f0149 --ndas-commit")
desp_list.append("studio1")

short_list.append(['cursor'])
command_list.append("/home/nv/Downloads/Cursor-0.48.8-x86_64.AppImage")
desp_list.append("studio1")


short_list.append(['22'])
command_list.append("python /media/nv/data/notebook/run_scripts/time_summary.py")
desp_list.append("tmp")


short_list.append(['55'])
command_list.append("python /media/nv/data/notebook/run_scripts/session_download.py")
desp_list.append("tmp")

short_list.append(['killrr'])
command_list.append("python /media/nv/data/notebook/run_scripts/kill_all_process.py")
desp_list.append("tmp")


short_list.append(['dnn'])
command_list.append("python /media/nv/data/notebook/run_scripts/ndas_run.py -n dnn")
desp_list.append("dnn")

short_list.append(['yellow'])
command_list.append("python /media/nv/data/notebook/run_scripts/ndas_run.py -n yellow")
# command_list.append("echo \'dazel run //:format\'")
desp_list.append("yellow")

short_list.append(['vans_tmp'])
command_list.append("python /media/nv/data/notebook/run_scripts/ndas_run.py -n vans_tmp")
# command_list.append("echo \'dazel run //:format\'")
desp_list.append("vans_tmp")

short_list.append(['mount'])
command_list.append("sudo maglev login && sudo maglev workflows2 mount nfs://scratch.avprediction-pdx /home/nv/Downloads/maglev_data/scratch.avprediction-pdx/")
desp_list.append("mount")

short_list.append(['cpu_mode'])
command_list.append("rm /home/nv/.slurm/config.json && cp /home/nv/.slurm/config.json_cpu /home/nv/.slurm/config.json")
desp_list.append("cpu mode")

short_list.append(['gpu_mode'])
command_list.append("rm /home/nv/.slurm/config.json && cp /home/nv/.slurm/config.json_gpu /home/nv/.slurm/config.json")
desp_list.append("gpu mode")

short_list.append(['ssh'])
command_list.append("ssh davzhong@cs-oci-ord-login-01")
desp_list.append("ssh")

short_list.append(['ssh3'])
command_list.append("ssh davzhong@cs-oci-ord-dc-03")
desp_list.append("ssh")


if len(sys.argv) == 4:
  short_list.append(['scp'])

  source_path = sys.argv[2]
  dest_path = sys.argv[3]

  if "/lustre" in source_path:
    source_path = "davzhong@cs-oci-ord-login-01:"+source_path
  if "/lustre" in dest_path:
    dest_path = "davzhong@cs-oci-ord-login-01:"+dest_path

  command_list.append("scp "+source_path+"  "+dest_path)
  # command_list.append("echo \'dazel run //:format\'")
  desp_list.append("scp path_source path_dest")

if len(sys.argv) == 5:
  short_list.append(['scp'])

  source_path = sys.argv[3]
  dest_path = sys.argv[4]

  if "/lustre" in source_path:
    source_path = "davzhong@cs-oci-ord-login-01:"+source_path
  if "/lustre" in dest_path:
    dest_path = "davzhong@cs-oci-ord-login-01:"+dest_path

  command_list.append("scp -r "+source_path+"  "+dest_path)
  # command_list.append("echo \'dazel run //:format\'")
  desp_list.append("scp path_source path_dest")


def kill_process(process_name, force_flag = False):
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
  subprocess.run(run_command,shell=True)

  # run_command = run_command.split(' ')
  # process = subprocess.Popen(run_command, preexec_fn=os.setsid)
  # try:
  #   # 等待进程结束
  #   process.wait()
  # except KeyboardInterrupt:
  #   # 捕获 Ctrl+C，发送信号到整个进程组
  #   os.killpg(os.getpgid(process.pid), signal.SIGINT)

if __name__ == "__main__":
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
  else:
    run_finished = False
    for i in range(len(short_list)):
      if sys.argv[1] in short_list[i]:
        if "spec_" not in command_list[i]:
          def command_combine(command_list):
            command = ""
            for ii in command_list:
              if len(command) == 0:
                command = ii
              else:
                command = command + " " + ii
            return command

          command = []
          command.append(command_list[i])
          if "scp" not in command_list[i]:
            for i in range(2,len(sys.argv)):
              command.append(sys.argv[i])

          execute_command(command_combine(command))
        else:
          if command_list[i]=="spec_1":
            pass
          elif command_list[i]=="spec_2":
            pass
        run_finished = True
        break
    if run_finished == False:
      print("command not supported")
