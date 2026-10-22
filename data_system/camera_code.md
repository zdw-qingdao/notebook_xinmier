
AR950--camera2d-rk3588--主分支：0611_track_bak
D950--safety-double-rk3588--主分支：ys_track_back_1280
相机前端--xme-app-event-cam-2d-self-setup-web-ui-201x--主分支：dev

750相机：
  代码位置：/home/simmir1/zdw/code/camera2d-rk1126
  编译工具链：/home/simmir1/zdw/gcc-arm-8.3-2019.03-x86_64-arm-linux-gnueabihf.tar
  相机用户名和ip，以及密码：root@192.168.10.133 ,密码是simmir123
760相机：
  代码位置：/home/simmir1/zdw/code/camera2d-rk3588
  编译工具链：/home/simmir1/zdw/RV1126B_LINUX6.1_SDK_RELEASE_V1.1.0_20250920.tgz
  相机用户名和ip，以及密码：root@192.168.10.116 ,密码是simmir123


git clone git@bitbucket.org:simmir-software/camera2d-rk1126.git
git clone git@bitbucket.org:simmir-software/camera2d-rk3588.git
git clone git@bitbucket.org:simmir-software/xme-app-event-cam-2d-self-setup-web-ui-201x.git
git clone git@bitbucket.org:simmir-software/safety-double-rk3588.git

前端：xme-app-event-cam-2d-self-setup-web-ui-201x 分支：ar960_start
后端: camera2d-rk3588 分支：ar960_start
编译打包执行：./deploy/a8550cm2/build-ar960-run-oneclick.sh

root@192.168.10.126
  P@ssw0rd
网页端登录
  http://192.168.10.126:58200/login
  网页用户名：sve
  网页登录密码：sve

1，内存碎片清理
2,后续预览分为同步预览和最新预览两种模式；
3，mqtt自动确定broker；每个设备都有一个broker level，broker level最高的启动broker；其他的都连接这个；

支持workflow的执行部署到其他相机；
增加模型压缩包上传，后端接口与前端按钮；

1，专门的profile；打开之后有明确的profile，通过可视化的形式，可以明确进行对比；
3  对比之后可以看出一个commit的优化会产生多大的效果；
  最好可以在线动态打开关闭profile，直接看当前的设备情况，资源占用情况，不同步骤的耗时情况；
------------------------------------------ todo:
测试环境和测试pipeline搭建

------------------------------------------------------------

/home/zhongdawei/code/camera_code/camera2d-rk3588 是相机上运行的后端程序；
/home/zhongdawei/code/camera_code/xme-app-event-cam-2d-self-setup-web-ui-201x 是相机上运行的前端；
在 /home/zhongdawei/code/camera_code/camera_doc 下写 summary.md
总结相机后端和前端代码；按照下面的要求：

1，首先说明代码使用的语言，框架，库；
2，总结所有的功能，按模块来说明；
3，重点总结所有控制相机的接口，单独总结一部分
4，重点总结模型推理的接口，单独总结一部分；

有不同的相机，即相机有不同的sdk接口；相机视频获取和推理运行在不同的平台上，即模型推理部分有不同的接口；
相机侧的所有功能 和 推理侧所有功能 都有什么，不同相机的sdk都有哪些接口；

不同的模块可以放到不同的md文档中；

/home/zhongdawei/code/camera_code/camera2d-rk3588 中正式运行有几个进程，每个进程的作用是什么；
/home/zhongdawei/code/camera_code/camera2d-rk3588 中怎么进行交叉编译；
/home/zhongdawei/code/camera_code/xme-app-event-cam-2d-self-setup-web-ui-201x 对后端接口的调用是什么
分别总结到 /home/zhongdawei/code/camera_code/camera_doc/ 中
/home/zhongdawei/code/camera_code/camera2d-rk3588 中数据存储是什么形式，登录账号的密码是怎么管理的，总结到 /home/zhongdawei/code/camera_code/camera_doc/ 中

/home/zhongdawei/code/camera_code/camera2d-rk3588 中交叉编译是指定编译到arm架构吗 是否需要厂家提供的什么东西；总结到 /home/zhongdawei/code/camera_code/camera_doc/ 中

要在/home/zhongdawei/code/camera_code/edgeflow_cam下做一个新版的在相机上运行的系统，文件夹架构如下，先创建文件夹和文件，不进行具体的实现；

frontend
backend
  routers
  stream_process
  monitor
modules
drivers
  camera_base.py
  inference_base.py
  deepstream
    camera.py
    inference.py    
  950
    camera.py
    inference.py
config
  system_config.json
  docker_config.json
docs
  design_doc
  operation_doc
docker
  DockerFile
  docker_run.sh
  docker_stop.sh
deployment
  build.sh  ----------> tar，可以直接通过前端更新，也可以scp到相机上，然后先运行 setup.sh 准备环境，然后运行 run.sh；config.json中需要指定相机平台；
  supervisord.conf
  run.sh
  setup.sh 不同的相机平台运行的环境下载和检查可能是不一样的；

--------------------------------------
docker环境的搭建：
在 docker_config.json 中增加docker相关的配置，目前只有docker名称和挂载路径
"docker": {
    "IMAGE_NAME": "edgeflow_cam",
    "CONTAINER_NAME": "edgeflow_cam_zdw",
},
"host_paths": {
    "HOST_DATA_DIR": "/mnt/data2/edgeflow_data",
},
"container_paths": {
    "CONTAINER_DATA_PATH": "/data",
    "CONTAINER_PROJECT_DIR": "/opt/autopipe/project"
}
DockerFile 中拉取 ubuntu22 的镜像，安装miniconda环境；安装fastAPI；
docker_stop.sh 是关闭docker
docker_run.sh 是先关闭已有容器，然后构建docker然后启动容器；
测试要完整docker的构建

/home/zhongdawei/code/camera_code/edgeflow_cam/docker 下的文件放到 ubuntu22子文件夹中，
生成镜像名称和容器名称的时候，使用配置文件中的名称加上文件夹的名称；
例如当前配置应该是 edgeflow_cam-ubuntu22 edgeflow_cam_zdw-ubuntu22
不需要imagetag
需要修改
    "CONTAINER_PROJECT_DIR": "/opt/autopipe/project"

--------------------------------------
技术框架，方案1：
1，前端用vue
2，后端 python
3，推理+后处理 python

技术框架，方案2：
1，前端用vue
2，后端 c++
3，推理+后处理进程 python

技术框架，方案3：
1，前端用vue
2，后端 c++
3，推理进程 c++
4，后处理进程 python

如果有内容必须要用c++，那么将c++函数编译为动态库，然后python载入和使用c++的库；
如果没有python解释器，那么python的部分全部使用c++；代码结构不变，只是进行c++的实现；
充分复用之前的代码，使用方案3，进程34之间通过共享内存通信即可；或者通过mqtt topic也行；

--------------------------------------

推理线程在启动后和相机主进程还有什么交互，相机主进程就是前端调用的后端进程吗；
主进程和推理线程存在持续的通信，这里需要注意通信方式是什么；
这里的通信方式在新版的python实现中应该怎么实现；
是否复用之前的c++代码；
方案1：纯python版本；
方案2：c++ 加 python后处理，后处理block部分通过共享内存和c++通信；
采用方案2；

--------------------------------------

/home/zhongdawei/code/camera_code/edgeflow_cam/config/system_config.json 这个配置文件中指定要使用的架构是什么，目前支持的有 pctest ，ar950,  ar750这3个
配置文件的使用；
2，代码中读取配置文件，判断使用的基类是哪个；
1，cmake读取配置文件，判断要编译哪部分；

--------------------------------------

需要做一个中间层，下面是驱动层，驱动层包含不同相机的sdk接口，不同平台的模型推理接口；
上面是应用层，不同相机不同平台上应用层的内容是相同的，应用层包含前端，后端等；
应用层通过中间层来控制相机硬件，进行模型推理；

根据 /home/zhongdawei/code/camera_code/camera_doc 中的文档
  /home/zhongdawei/code/camera_code/camera2d-rk3588 中的代码，
  /home/zhongdawei/code/camera_code/camera_doc/python_system_desing/middleware_design.md 中的设计；

在 /home/zhongdawei/code/camera_code/edgeflow_cam/docs/middle 中写中间层设计文档；中间层通过 base.cpp 中的基类来实现；

需要做一个相机的基类，其他各种不同的相机都继承自这个基类，基类包含所有的相机控制接口；
需要做一个模型推理的基类，torch的推理继承自这个基类，基类中包含所有模型推理需要的接口；
实现相机中间层基类后，子类实现一个模拟相机，模拟相机的视频流是通过播放一个视频；模拟全部的控制接口；
实现模型推理中间层基类，实现pytorch推理的子类；
中间层的基类只包含基础接口，基础接口上层的功能函数模块在 /home/zhongdawei/code/camera_code/edgeflow_cam/modules 中实现；后续增加新的相机或计算平台，只需要在drivers中增加新的子类；

使用c++代码，在 edgeflow_cam_zdw 容器中进行编译与测试；
中间层的方式就是基类；怎么指定使用哪款相机和哪种推理架构，通过配置文件指定，配置文件指定的结构才会进入编译，使用的时候也是使用指定的部分；
有不明白的问题要问我，先写设计文档，我review之后进行实现；
实现要分步骤进行，每次实现一步后我来review，review完成后进行下一阶段的开发；


--------------------------------------

/home/zhongdawei/code/camera_code/edgeflow_cam/CMakePresets.json 分阶段构建和测试
/home/zhongdawei/code/camera_code/edgeflow_cam/tests/smoke/cpp17_smoke.cpp 以及其他的cpp文件是怎么使用的，使用逻辑是什么；
总结到 /home/zhongdawei/code/camera_code/edgeflow_cam/docs/code_reading 中

-------------------------------------- 设计问题；

根据 /home/zhongdawei/code/camera_code/camera_doc 中的文档
  /home/zhongdawei/code/camera_code/camera2d-rk3588 中的代码，
PlaneInfo 的概念在 camera2d-rk3588 中有吗

-------------------------------------- cmake 设置方式；

这里没必要区分不同的开发stage，但是还是要保留preset的设置；
test 是专门的一项，会编译所有的测试用例；其他项不需要编译测试用例；
x86_dev 是一项，通过 RelWithDebInfo 模式编译；
cam950_release 是一项，进行针对嵌入式平台上的交叉编译；cam950_release这一项的内容先注释掉，后续再实现；

1，取消 api_version 的设计，不需要这部分；

2, 创建 Camera 实例
→ discoverDevices()（可选）
→ open()
→ info() / config() / controls()
→ validateConfig() / applyConfig()（可选）
→ applyControls()（可选）
→ start()
→ readFrame() / capture()
→ stop()
→ close()

传参方式：
  1，动态获取支持参数；
  2，固定接口与类型；要采用这样的方式，这样应用层才不需要考虑驱动层；

-------------------------------------- ui 设计
原版相机代码的路径和文档：
  原版相机前端： /home/zhongdawei/code/camera_code/xme-app-event-cam-2d-self-setup-web-ui-201x
  原版相机后端：/home/zhongdawei/camera_code/camera2d-rk3588
  原版相机代码总结文档：/home/zhongdawei/camera_code/camera_doc

edgeflow训练平台前端代码路径：/cfs/users/zdw/code/autopipe2/autopipe/frontend
访问 http://122.225.62.9:13700/ 可以登录edgeflow，账号是admin，密码是123456

edgeflow_cam 要实现一版新的前后端：
1，登录页面使用和edgeflow这个相同的登录页面ui设计；
2，登录后页面是和edgeflow登录后点到某个workspace页面下类似的页面，设计风格相同，左侧有三栏：相机配置，workflow，部署
  这3栏现在点开都是空的，后续再实现相关内容；
3，账号密码在system_config.json中明文写，账号是admin，密码是123456
4，frontend中实现前端，backend中实现后端；
  前端的代码框架使用 xme-app-event-cam-2d-self-setup-web-ui-201x 相同的框架；
  后端的代码使用 camera2d-rk3588 相同的框架，c++的后端；
先写完善的设计方案，不明白的问题问我，代码实现要模块化，避免过度设计，要分阶段实现所有的目标，我review之后进行分阶段的开发；设计文档放到 /home/zhongdawei/camera_code/edgeflow_cam/docs/ui 中

-------------------------------------- 相机配置页面

实现相机配置栏前端与后端；
可以配置相机的所有功能，可以启动，关闭相机，查看相机当前的信息；针对当前的中间层的接口设计信息显示，配置控制与启动；
相机启动后，要可以显示视频流，显示视频流的方式参考：
  原版相机前端： /home/zhongdawei/code/camera_code/xme-app-event-cam-2d-self-setup-web-ui-201x
  原版相机后端：/home/zhongdawei/camera_code/camera2d-rk3588
通过新的中间层拿到数据来进行显示；
先写完善的设计方案，不明白的问题问我，代码实现要模块化，避免过度设计，要分阶段实现所有的目标，我review之后进行分阶段的开发；设计文档放到 /home/zhongdawei/camera_code/edgeflow_cam/docs/ui/camera 中;

-------------------------------------- workflow编辑与运行，复用edgeflow的方法；
  相机部分，需要是统一的接口；分发模型以及workflow，使用统一的接口；先通过960实现；

增加一个模型转换脚本，输入是pt文件路径和要输出的导出模型文件路径；
转换脚本的路径在 /home/zhongdawei/camera_code/edgeflow_cam/tools 下
使用 /data/models/detector.pt 来测试，转换成 /data/models/detector_jit.pt
转换成 /home/zhongdawei/camera_code/edgeflow_cam/backend/drivers/inference/nv_torch/nv_torch.cpp 需要的模型

-------------------------------------- 驱动支持某款相机

做一个docker，可以进行交叉编译
中间层规划，上层分工
分布并行开发； 

方案1：优势是可以复用以前的一些c++代码；
前端
后端python，调用中间层和功能模块；
python主进程，调用中间层和功能模块；
功能模块可以是c++的，也可以是python，如果是c++的也需要有python接口；
中间层c++的；编译为动态库，上层使用的方法是动态库，有c++接口也有python接口；
驱动层，全部使用c++，以前的代码就是c++的；

到某个相机的运行方法：
  1，安装sdk环境
  2，安装python环境
  3，代码交叉编译，传到相机之后进行运行；

方案2： 优势是开发调试快；

全部用python；

先做一个docker，基于ubuntu22，在这个docker中做前端，后端，主进程，把中间层做好；
然后在这个docker中先把camera simulator做好；
然后丰富不同相机的驱动层；

到某个相机的运行方法：
  1，安装python基础环境
  2，安装sdk环境
  3，代码clone，然后运行；

后续开发方式：
  1，在docker中，通过camera simulator进行前后端主进程的开发，包括监护进程的开发；
  2，在相机上进行环境配置，环境配置脚本也要在代码仓库中；
  3，在相机上启动的脚本；是幂等的，后续的执行也同样是加入到自动启动中；
  4，存储使用什么内容；

1，进行前端的设计与实现，参考已有的设计风格；
2，功能模块的补充；直接进行功能的迁移；
3，workflow部分的适配，后续的算法方案都是workflow的形式；进行workflow算法的迁移；
4，已有方案适配为不同的workflow
5，相机和pc交互的接口；

------------------------------------------ 整体规划 

1，相机中间层接口         done
  相机变量出来可以接着进行模型推理；

2，推理中间层接口         done
  推理输入是cpu变量，不是直接解码得到的变量；

3，应用层接口
  1，对外接口的输入输出；
    输入：
      1，模型导入
      2，workflow导入
    输出：
      1，mqtt topic；
      2，运行状态

4，进程结构：
  1，前端
  2，后端
    1，camera线程
    2，推理线程
  3，监控进程

5，编译，部署，测试系统；



------------------------------------------ 架构重新设计；

  1，不需要streamrole，这部分是应用层要定义的；
  2，也不需要 streampurpose

  可能有一个或多个相机，每个相机有一个或多个流，其中有个流是用来推理的，有的驱动支持batch并行推理，解码和推理都在gpu上，有的不支持，需要先加码，然后在gpu上推理，在架构上怎么进行设计
  设计方案：
    2, 推理的部分修改为推理引擎，所有的推理都到推理引擎中进行处理；
    1, 相机采用注册机制，注册后，启动推理；
  先采用这样的方式：
    当前基类设计的问题，没有对多路推理，硬件直接推理的支持；
    在推理的部分可以支持并行推理，但是取变量还是取cpu上的变量；
    即 framerouter 进行合batch的操作，然后batch变量调用 inference_base 接口，直接进行batch推理；
    和batch的部分放到 framerouter 中，还是inference_base中；

  2，为什么需要 framerouter,为什么不直接绑定消费者；
    1，framerouter 是一个通用的生产者消费者的绑定，不只用于推理；
    2，后续在 framerouter 里可以进行合batch的操作；

  3，完整的编译和部署方案；不同的docker环境和cmake选项，得到build下不同的编译产物，编译产物直接上到相机上运行；
    指定 cmake选项 + 编译docker；
    则在指定的docker中，进行执行的编译；
    测试运行：可以直接运行
    相机：打包传到相机，然后解压缩并启动；

2，模型存放位置，workflow存放位置；修改 system.json 文件的配置；
  在system_config.json中不要有 camera inference 的配置，增加一个model文件夹的路径和workflow文件夹的路径；

----------------------------------------------------------------

相机栏中有“扫描相机”按钮，点击后显示扫描得到的所有相机；
每个相机有一个配置按钮，点击配置后会显示这个相机的所有配置；可以修改配置，打开关闭相机；
对于 video_sim 的情况来说，source_uri 中有几个视频文件，就显示有几个相机；

相机配置内容都存放到 config_directory 中 camera_config.json
如果存在 camera_config.json，在系统启动时读取 camera_config.json 中的内容添加相机，配置相机并打开相机；
如果没有，则需要手动扫描添加；
添加相机或对相机做的所有配置都保存到 camera_config.json 中，作为持久化的手段；

system_config.json 中 camera 改名为 camera_default，在新建相机是默认使用这个配置项；取消里面的 "id"，相机id默认生成 cam0 cam1...
  取消 driver_options 这一项
新增相机时临时打开设备并读取它的默认有效配置，而不是直接复制全局 1280×720 模板。否则不同分辨率的视频重新扫描后还可能生成无效配置。

相机栏已添加的相机增加一个删除按钮，在扫描添加相机后，相机支持的能力同样保存的camera_config.json中；
在配置相机时，基于相机的能力，进行下拉框的选择；

system_config.json 中 video_sim 的driver_options配置放到 video_sim.condig 中，在使用video_sim的时候，先读system_config.json，然后读 video_sim.config 进行覆盖和补充；

添加一个流，如果类型是 H264,
  可以选择是否是rtsp流；如果是，要设置rtsp流的topic；在启动后作为rtsp流pub出去；
  可以选择是否为录像流；如果是，启动录像后要录制这路流，保存到 saved_video_directory 中，文件名称是录制时间，精确到秒；
  rtsp流和录制图像需要的代码库工具可以参考 /home/simmir1/zdw/code/camera2d-rk3588

添加一个流，如果类型是 raw，可以选择是否为推理流，选择是否用于拍照；是否用于录像；
  如果用于录像，那么启动录像后录制这路流，保存到 saved_video_directory 中，文件名称是录制时间，精确到秒；
  只能有一路流用于录像，如果某个流启动了录像，之前启动录像的流会关闭录像功能；
  如果用于拍照，那么拍照后会将这路流最新的照片保存到 saved_image_directory，文件名称是拍照时间，精确到秒；

相机页增加一个录像按钮，可以启动录像，停止录制；如果没有一路流支持拍照，这个按钮是灰的，不能点击；
增加一个拍照按钮，可以拍照；如果有流支持拍照，例如有用于拍照的raw，那么通过raw流的图片进行拍照；否则调用capture接口获取拍照图像；
增加一个预览按钮，显示rtsp视频流；

raw流不需要支持录像和拍照；不要使用 gstreamer；
使用 /home/simmir1/zdw/code/camera2d-rk3588 中同样的基础库来进行rtsp流的转发和前端的预览；
将h264的流封装为rtsp来发布；将h264的流转成webrtc的流，前端使用这个流来可视化；

2，模拟器先实现一版，实现过程中逐步调整 system_config.json 中的内容；
  1，默认进行扫描相机并添加相机；显示当前有的相机；
  2，如果是模拟器那么根据视频的数量确定有几个相机；
  3，相机配置；
  4，可视化预览；
  5，多个同时预览；
  6，录像，拍照；

相机页上有推理按钮，如果没有支持推理的流这一项是灰色的，如果有可以启动，点击推理要选择使用的模型，即选择 model_directory 下的一个文件夹；
model_directory 下是当前所有的模型；选择后启动推理；
这时候点击预览可以显示推理的结果；推理结果可以选择显示或不显示；预览显示的是模型推理和视频流叠加显示的结果，只显示最新的；
mqtt的支持参考 /home/simmir1/zdw/code/camera2d-rk3588

实现workflow的部分，目前具体包含下面几个方面：

1，复用autopipe的类型定义，block定义方式和workflow_engine;
  基本上是将 /home/simmir1/zdw/code/autopipe/backend/workflow6/data_type.py；
  /home/simmir1/zdw/code/autopipe/backend/workflow6/block_base.py；
  /home/simmir1/zdw/code/autopipe/backend/workflow6/workflow_engine；
  复制到 /home/simmir1/zdw/code/edgeflow_cam/backend/workflow 下，对于 data_type.py block_base.py workflow_engine 需要的依赖也加入到utils中；
  同样创建 block_library/loader.py，但是 block_library 下现在是空的，没有block；

2，增加一个workflow栏，点开后显示当前的不同的workflow，右上角有创建workflow的按钮，可以新建和删除workflow；不需要有公共工作流和回收站；点击某个workflow后进入编辑画板；

3，点击进入编辑画板后，可以进行block的创建和连线，右键可以选择block来添加；
  启动了几个相机就有几个输入可以选择；分别对应启动的相机；
  有一个模型推理的block可以选择(这个block不是 block_library 中的，是额外的特定的一个)，这个block后有一个下拉框是模型选择，即选择model_directory中的模型，选择这个下拉框后输出类型也会确定；即根据模型的类型；detection类型模型对应的输出类型是 "ObjectDetection"
  然后可以选择 block_library 中定义的block；可以选择输出节点；输出节点的类型取决于它的输入；
  相机输入block只有一个输出，输出block只有一个输入，模型推理block有一个输入和换一个输出，其他block的输入输出是自身定义的，节点连线的数量也是根据block的输入输出来的；
  这里操作逻辑和 autopipe 相同；参考autopipe的操作和代码；

  右上角有json查看，执行按钮，保存；
  workflow json文件保存在 workflow_directory 中；workflow json的定义和使用方式和 autopipe 中相同；
  点击执行后，首先拆分block，将模型推理的部分拆分，然后模型推理的部分启动，将模型推理的结果作为mqtt的topic pub；
  多个相机运行同一个模型，要并行推理，如果模型本身max_batch_size 小于并行数量，那么再循环处理；
  然后将拆分后的workflow启动一个python进程，通过workflow执行引擎来执行，模型推理的输入是mqtt类型，用推理部分输出的mqtt对应的topic，最后workflow的输出也通过mqtt topic pub出来；如果模型推理的block后面没有其他block，直接接了输出节点，那么不需要启动workflow执行引擎；

4，代码实现参考 autopipe:
代码位置：/home/simmir1/zdw/code/autopipe
autopipe中workflow后端的位置:/home/simmir1/zdw/code/autopipe/backend/workflow6
autopipe中workflow设计文档的位置：/home/simmir1/zdw/code/autopipe/doc/design_doc/workflow/v6
autopipe访问：http://122.225.62.9:11860
账号：admin
密码：123456

先在 /home/simmir1/zdw/code/edgeflow_cam/docs/workflow 中生成完善的设计文档，有不明白的问题问我，设计分步骤的实现方案，我review后进行分步的实现；
创建 读取 保存 删除工作流应该通过 c++ 代码来实现，python代码只进行执行workflow engine；
在系统启动的时候读取所有的block library中所有block的输入输出和参数信息，即所有前端需要的信息，后续在编辑的时候不需要调用python，只有在执行的时候需要调用python

后续都是在 edgeflow_cam-ubuntu22 中编辑测试，复用已有的编译结果；

workflow python的部分，复用了autopipe的类型定义，block定义方式和workflow_engine，使用代码来自：
/home/simmir1/zdw/code/autopipe/backend/workflow6
/home/simmir1/zdw/code/autopipe/backend/workflow6 这里是老版本的workflow engine；
/home/simmir1/zdw/code/autopipe2/autopipe/backend/workflow6 中是最新版的workflow engine；
将 edgeflow_cam 中workflowengine 升级为 /home/simmir1/zdw/code/autopipe2/autopipe/backend/workflow6 中的方式；


edgeflow训练平台前端代码路径：/home/simmir1/zdw/code/autopipe/frontend
访问 http://127.0.0.1:10705/ 可以登录edgeflow，账号是admin，密码是123456

ui样例代码路径： /home/simmir1/zdw/code/EdgeFlow-Developer-Handoff-2026-08-27
访问 http://127.0.0.1:18000/ 可以登录该ui设计网页，账号是admin，密码是123456

edgeflow_cam 登录页面保持相同和 edgeflow(http://127.0.0.1:10705/)相同，登录后的页面也保持同样的ui风格；
参考 http://127.0.0.1:10705/ 和 http://127.0.0.1:18000
不一致的地方以 http://127.0.0.1:10705 为准；


system_config.json 中架构设置
  "cam_arch": "video_sim",
  "inference_arch": "nv_torch",
改为在 /home/simmir1/zdw/code/edgeflow_cam/CMakePresets.json 中指定；
编译时编译选项就确定了编译内容；

不需要 /home/simmir1/zdw/code/edgeflow_cam/deployment/pc_build_cam_package.sh
在 /home/simmir1/zdw/code/edgeflow_cam/CMakePresets.json 对每个编译选项指定是否进行打包；
指定打包名称，默认统一存放在 HOST_DATA_DIR 中 package 文件夹下，如果没有这个文件夹则创建；
如果已有同名包则覆盖；

在 /home/simmir1/zdw/code/edgeflow_cam/README.md 中总结下面内容：
  当前代码仓库文件夹的结构和作用，说明要简洁；
  开发规范是什么，中间层只保留最小的需要的接口；然后具体实现在驱动层；
  测试启动方式是什么，完整的流程；
  部署打包以及在相机项启动的完整流程是什么；
  所有的进程和线程，以及关系；

/home/simmir1/zdw/aidlux_ql_ubun2204.425.tar.gz 是一个docker文件，将这个docker导入到系统的docker中，后续需要基于这个docker创建新的docker；输出这个docker的名称

960相机驱动层实现和编译实现：
  1，/home/simmir1/zdw/code/camera2d-rk3588/ 中适配了960相机，参考/home/simmir1/zdw/code/camera2d-rk3588/ 中使用的api和编译方法，在 edgeflow_cam 中增加960相机的支持；编译选项是 cam960_release，基于 /home/simmir1/zdw/code/camera2d-rk3588/ 中相机和推理的api，实现960的驱动层；
  2，要用的docker是基于 aidlux_ql_ubun2204:425 创建的新docker，在/home/simmir1/zdw/code/edgeflow_cam/docker/下创建新的文件夹 ubuntu22_960，
  文件夹中的内容参考 /home/simmir1/zdw/code/edgeflow_cam/docker/ubuntu22 中的内容；在这个docker中才能正常进行960相机相关api的编译；
  先在 /home/simmir1/zdw/code/edgeflow_cam/docs/960/deiver.md 中写设计文档，有不明白的问题问我，有不同的阶段要分阶段，我review之后进行分阶段的开发

刷机与部署的脚本：
  参考 /home/simmir1/zdw/code/camera2d-rk3588/deploy/a8550cm2/build-ar960-run-oneclick.sh 脚本；参考其中的控制相机的方式；
  这是老版本代码的部署脚本；总结文档是 /home/simmir1/zdw/code/edgeflow_cam/docs/deployment/flash_original.md

/home/simmir1/zdw/code/edgeflow_cam/config 中增加一个 deployment_config.json
指定要部署的相机的用户名和密码是：
  root@192.168.10.126
  P@ssw0rd
指定部署的架构是什么，默认是 cam960_release;
/home/simmir1/zdw/code/edgeflow_cam/docker/ubuntu22 下创建一个刷机脚本：flash.sh
刷机脚本的作用类似老版本的 build-ar960-run-oneclick.sh
  1，进行编译和打包
  2，将打包内容传到相机上指定位置并解压
  3，将启动加到系统启动中，即开机自动启动；如果已经有了就不需要加了，参考 /home/simmir1/zdw/code/camera2d-rk3588/deploy/a8550cm2/build-ar960-run-oneclick.sh  的实现方式
  4，deployment_config.json 中加一个参数指定是否需要系统重启，需要的话会重启系统，重启后edgeflow_cam会自动启起来；不需要的话要重启edgeflow_cam系统

/home/simmir1/zdw/code/edgeflow_cam/docker/ubuntu22 下创建一个部署脚本；deployment.sh
部署脚本的作用：
  1，进行编译和打包
  2，将打包内容传到相机上指定位置并覆盖
  3，重新启动系统；

1，python10 python11的问题，为什么使用python10；

3，最后在960相机 root@192.168.10.126 上运行edgeflow_cam，能够正常进行系统的所有功能，能够通过脚本一键刷机，一键部署；
  先写设计文档，有不明白的问题问我，我review之后进行实现，如果有明确的阶段那么分阶段来实现；

现在 /home/simmir1/zdw/code/edgeflow_cam/docker/ 下有不同的docker文件夹，每个文件夹下有各自的启动，进入，编译等脚本；在外侧加统一的脚本；用来读取配置后调用内部的脚本；在 /home/simmir1/zdw/code/edgeflow_cam/docker/ 下添加以下脚本：
  docker_run.sh
  docker_into.sh
  docker_stop.sh
  system_build_start.sh
    如果编译选项是 x86_dev，那么编译并启动系统
    如果编译选项是相机相关的，例如 cam960_release，那么编译，打包，传到相机上覆盖原版本，并在相机上重新启动系统；
  flash.sh
    如果编译选项是 x86_dev，这个脚本直接退出，没有作用； 
    如果编译选项是相机相关的，例如 cam960_release，那么进行刷机过程，将需要的文件传到指定相机上，进行对应操作；执行编译打包，传到相机上覆盖原版本，将edgeflow_cam加入到系统启动中，然后重启相机，相机重启后edgeflow_cam也会启动起来；
 
1, 在 /home/simmir1/zdw/code/edgeflow_cam/config/platform.config 中指定使用哪个docker（ubuntu22 还是 ubuntu22_960），指定编译选项（例如 cam960_release）；
指定测试相机的用户名ip和密码；
（/home/simmir1/zdw/code/edgeflowcam_data/transed_model 下有转换过的能在960上运行的模型，可以用来测试；）

当前系统需要的模型文件夹中应该有哪些内容？在相机上创建需要的模型文件夹，并在文件夹中加入必需的内容

1，增加模型栏；可以上传模型，删除模型，上传的模型是压缩包的形式，上传后会解压，然后验证 info.json 和其中的文件是否正常，如果正常移动到指定位置，否则删除并告知问题；
2，软件包更新系统：参考 /home/zhongdawei/code/camera_code/camera2d-rk3588 中软件包更新的操作方式，在打包得到新的软件包后，可以将软件包通过前端拖入来更新系统；需要一个单独打包但不启动的脚本，打包得到的软件包就可以通过前端拖入来更新系统，也可以通过之前的方式用脚本来打包并直接更新系统；
3，录像存储，查看与下载；左侧增加结果查看栏，点击后可以查看或下载 录像和拍照的结果；

现在刷机过程，部署过程会在960上安装或者复制什么东西吗？除了打包的部署包还有什么其他的？python11的解释器是怎么来的，在哪一步来的；

flash.sh文件相对于 system_build_start.sh 多干了什么，是否有必要，是否需要重启；

这部分内容最后转换得到的模型文件夹放到 assets/cam960 下，作为安装时默认带的一个模型，安装时要将这个模型文件夹也安装；
同样有 assets/nv_torch，里面也放一个模型文件夹，在 system_build_start.sh 时默认将这个放到模型目录下，如果已经有了同名的就不需要了

预览画面上要分别显示图像帧率和推理结果的帧率

多节点系统的逻辑设计：

  3，多机的部分怎么确定中心节点
    现在用户需要打开系统设置，选择mqtt主阶段，设置相关信息，这里要进行操作逻辑上的优化；
    多个edgeflow_cam 的设备启动后，需要确定某一个节点是中心节点，
    怎么设计用户的交互逻辑，有哪些不同的方式，对比不同的方式：

  主节点的设置；可以发现局域网内所有的edgeflow 和 edgeflow_cam 设备；
  可以设置启动mqtt broker 或 连接到已有的broker；
  可以查看所有节点的连接关系；

  手动模式：默认启动broker，可以选择连接到其他启动了broker的设备；
    可以显示当前的拓扑图；

  自动模式：局域网内启动并能够发现的设备自动确定broker，根据设备的broker优先级确定broker；
    可以手动设置broker优先级；
    缺点是：不能分group，使用不同的broker，隔离环境；

  使用mDNS进行局域网内的设备发现；

  edgeflow可以设置是否是主节点，可以设置连接到主节点，然后每台设备都可以查看所有的节点的情况；

  只有主节点启动mqtt broker，从节点连接到主节点的mqtt broker；

设计形态：
  1，相机列表，主要是设置视频流获取；通过webrtc转发；先不需要这里设置相机参数，可以跳转到相机的设置页面；
    1，相机也可以拉取其他相机的视频流，例如960相机加一个没有推理能力的网络相机
    2，edgeflow上连接一个相机后则显示这个相机上所有的视频流；
    视频流有不同情况：
      1，存在相机硬件
      2，老版本相机发出的rtsp视频流
      3，其他相机的视频流；
      4，edgeflow 发出的webrtc视频流
      5，edgeflow_cam 发出的webrtc视频流；
      这是一种方式；
  2，通信设置，设置通信主节点，通过列表显示当前的节点情况，先实现这个；
  3，系统拓扑，每个运行中的workflow是一个block，显示整个系统所有运行中的workflow和所有用到的视频流；
    单进单出的方式即可；
    通过主节点进行信息汇总和查询

任务分工：
  1，相机本身设置
  2，组设置，发现局域网内所有设备，确定主节点，主节点启动broker，进行 mediamtx的转发；默认自身是一个主节点；   haiyang
  3，相机列表直接显示组内所有的视频流；                           haiyang
  4, 系统拓扑显示；                                          haiyang
  5，相机适配                                               haiyang

7，相机测试代码；保留以前的前端和新的前端，要有新的前端；
  后续的整体架构设计；
  后续整体设计；
6，实现当前系统在不同相机上的部署；
5，实现不同相机的基类；
4，功能模块中实现当前所有需要的功能；
3，进行ui设计与实现，后端要调用对应的中间层；
2，推理中间层的设计与实现，torch推理的实现；
1，相机中间层的设计与实现，模拟相机的实现；

专门的profile；打开之后有明确的profile，通过可视化的形式，可以明确进行对比；
  对比之后可以看出一个commit的优化会产生多大的效果；
  最好可以在线动态打开关闭profile，直接看当前的设备情况，资源占用情况，不同步骤的耗时情况；

增加profile功能，监控整个系统的资源使用,进程效率和延时等信息；具体如下

前端：
  增加系统监控栏，放在系统设置上方；点进入后显示全部信息；
  1，首先是系统资源使用信息，包括cpu占用，内存占用，显存占用，硬盘占用；网络速率；
  2，然后可以选择当前打开的某个相机某路流，显示该流的信息；该流的信息包括：
    取流帧率，推理帧率，每个环节的时延；
    可以整体打开或关闭相机流的profile；默认是关闭的；
  3，可以显示当前运行的workflow，各个环节的时延和帧率；
后端实现：
  1，系统资源使用的部分通过中间层来实现；包括cpu占用，内存占用，显存占用，硬盘占用；网络速率；在 inference 的 base.cpp 中增加查询接口，在每个子类中进行实现；
    验证每个平台上都能正常work；包括960平台，pc平台；950平台先不用测试；
  2，时间与帧率统计的部分单独实现，backend下有一个单独的profile模块，在其他部分使用的时候通过宏定义的方式来使用profile；
    尽量减少profile部分对其他代码的侵入性，尽量解耦；也支持前端一键打开和关闭profile功能；当关闭profile功能时，插入的宏定义相当于空的；在打开profile的时候，进行时间和帧率等统计；
先写设计文档，分阶段实现，有不明白的问题问我，我review之后进行每个阶段的实现；

系统监测进行调整：
  1，磁盘占用，统计 / 目录即可，不需要选择其他，取消这个选择；
  2，网卡选择放到网络速率的卡片上
  3，显存/加速器内存的卡片上加上加速器占用，加速器相关的放在一个卡片上，取消加速器选择，有几个加速器就显示几个卡片；

2，950相机的地址：root@192.168.10.118 
  密码：simmir
  进行950相机profile的适配和测试；

1，增加温度显示，同样通过中间层查询，950 和 960 调用温度显示的接口，nvtorch的温度返回空即可；

0，模型管理放到workfow栏上方
  软件更新放到系统设置上方；


适配750相机和760相机；适配驱动层，编译，默认模型，模型转换，配置文件等所有需要的部分；
需要适配的内容可以参考 /home/simmir1/zdw/code/edgeflow_cam/docs/code_dev/add_camera_platform.md
先适配750相机，适配完成后创建一个commit，然后适配760相机；完成后再创建一个commit；
注意要参考已有的950 960的适配方法，做好模块划分与隔离；
要参考下面的内容：
750相机：
  代码位置：/home/simmir1/zdw/code/camera2d-rk1126
  编译工具链：/home/simmir1/zdw/gcc-arm-8.3-2019.03-x86_64-arm-linux-gnueabihf.tar
  相机用户名和ip，以及密码：root@192.168.10.133 ,密码是simmir123
760相机：
  代码位置：/home/simmir1/zdw/code/camera2d-rk3588
  编译工具链：/home/simmir1/zdw/RV1126B_LINUX6.1_SDK_RELEASE_V1.1.0_20250920.tgz
  相机用户名和ip，以及密码：root@192.168.10.116 ,密码是simmir123
代码位置是老版相机代码的位置，参考其中的sdk接口；
编译工具链是交叉编译需要的文件，压缩包放到 /home/simmir1/zdw/code/edgeflow_cam/assets/compile 下，在编译使用的docker中挂载；
相机用户名ip密码是对应的测试相机，在这个相机上完成全部测试；


要设计外设调用的中间层，在驱动层进行具体实现，在应用层做一个外设测试页；注意以下几点：
1,老版相机代码位置：
  /home/simmir1/zdw/code/camera2d-rk1126
  /home/simmir1/zdw/code/camera2d-rk3588
  总结其中所有的外设调用，不同的开发板，相机的外设能力和范围是不同的，基于所有存在的外设调用设计中间层；
2，驱动层适配750 760 950 960的所有外设；
3，应用层在前端增加一个外设测试页，在外设测试页获取并显示当前的所有支持的外设，可以测试所有外设的使用；
有不明白的问题要问我，先在 /home/simmir1/zdw/code/edgeflow_cam/docs/middle/peripheral.md 写设计文档，我review之后进行实现；
实现要分步骤进行，每次实现一步后我来review，review完成后进行下一阶段的开发；







