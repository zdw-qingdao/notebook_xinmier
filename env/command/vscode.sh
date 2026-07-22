#!/bin/bash


#xclip_tmp=$(xclip -o)
# xdotool key ctrl+c

currnet_dir_path=$(xclip -o -sel clipboard)
code  ${currnet_dir_path}


  
#echo ”Hello: ${currnet_dir_path}” >> /home/luvision/Documents/environment/t.txt  

# path=`pwd`
# echo ” ${path}” >> /home/luvision/Documents/environment/t.txt
