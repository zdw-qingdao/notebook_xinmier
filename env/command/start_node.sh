# support newline between commands
# The following example starts three commands
commands=(
    ssh nerv@192.168.110.150
    
    "watch -n 1 'date'"

    "watch -n 1 'date'"
    
    "watch -n 1 'date'"
)

TOP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
echo "TOP_DIR: $TOP_DIR"
is_tmux_install=`which tmux`

if [ -z "$is_tmux_install" ];then
    sudo apt install -y -q tmux
fi

arch=`uname -i`
if [ $arch != "aarch64" ];then
    if [ -z $1 ];then
        echo "x86 env must set ROS_DOMAIN_ID!!!"
        echo "Usage: $0 <ROS_DOMAIN_ID>"
        exit 1
    fi
    ROS_DOMAIN_ID=$1
    LOCAL_ONLY=1
else
    host=${hostname:-1}
    ROS_DOMAIN_ID="10$host"
    LOCAL_ONLY=0

    if [ "$host" == "2" ];then
        ROS_DOMAIN_ID=90
    elif [ "$host" == "3" ];then
        ROS_DOMAIN_ID=102
    fi

fi

export ROS_DOMAIN_ID=$ROS_DOMAIN_ID
echo " !!!! Use ROS_DOMAIN_ID: [ ${ROS_DOMAIN_ID} ] !!!!"
echo " !!!! Use ROS_DOMAIN_ID: [ ${ROS_DOMAIN_ID} ] !!!!"
echo " !!!! Use ROS_DOMAIN_ID: [ ${ROS_DOMAIN_ID} ] !!!!"

source /opt/ros/humble/setup.bash
source ${HOME}/ros2_ws/install/stup.bash
source ${TOP_DIR}/src/install/setup.bash
export ROS_LOCALHOST_ONLY=$LOCAL_ONLY
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=${TOP_DIR}/anyverse/config/cyclonedds.xml

session_name="dev_start_nodes"

tmux new-session -d -s "$session_name"
#tmux new-session -d -s $session_name -n "window0" "${commands[0]}"
# 循环创建剩余窗口
total_commands=${#commands[@]}

echo "total_command: ${total_commands}"
h_t=$((total_commands/2))
v_t=$((total_commands/2))
echo "total_commands ${total_commands} h:${h_t} v:${v_t}"

cur_windows=1
for i in $(seq 1 $h_t); do
    echo "h ${i}"
    tmux split-window -v -t "$session_name"
    let cur_windows+=1
    if [ $cur_windows -ge $h_t ];then
        break
    fi
done

v=0
for i in $(seq 0 $v_t); do
    if [ $cur_windows -ge $total_commands ];then
        break
    fi

    echo "v ${i}"
    tmux select-pane -t $v
    tmux split-window -h -t "$session_name"
    let v+=2
    let cur_windows+=1
done

i=0
while [ $i -lt $total_commands ];do
    tmux select-pane -t $i
    tmux send-keys "export ROS_DOMAIN_ID=$ROS_DOMAIN_ID && \
        export ROS_LOCALHOST_ONLY=$LOCAL_ONLY && \
        source /opt/ros/humble/setup.bash && \
        export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && \
        export CYCLONEDDS_URI=${TOP_DIR}/config/cyclonedds.xml && \ 
        ${commands[$i]}" C-m
#    tmux send-keys "${commands[$i]}" C-m
    let i+=1
done

tmux attach -t $session_name
