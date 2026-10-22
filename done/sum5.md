

4，下次发版要上线的内容：
  haowei：
    所有标注类型支持
  haiyang：
    设备发现与扫描，rtsp分流
    svap全部功能
  fangsong：
    svap测试；
    4090与3060推理效果测试；性能对比；
  zejin：
    数据同步系统
    收费系统；
  linli：
    docker拆分；


1，review the profile code
  1，profile 使用方式
  2，哪些地方使用了profile；
  3，前端显示内容怎么看；profile的信息是存储在哪里


1，下载速度很慢的问题，已解决；
2，http://120.48.26.246:10700/workspace/96/project/161/models/999 显示的问题；

devices-test分支上了。一共6个stage：
其中1-3是我们讨论过的内容，基本没问题；
4基本是复制的cameras页面功能，review过也没啥问题；
5是实现的录制功能，这块主要是架构设计：录制和下载副本、切换和重连broker时的设计。这块之前没跟你讨论过，但我感觉设计得还算周道，兼容了designer和edgeflow_camera，也没有增加系统复杂度，之后edgeflow_camera的实现还可以直接搬运现有逻辑。另外我顺便去掉了原先录制功能对deepstream的依赖，让没GPU的设备也能支持录像；
stage6改动比较多比较杂，我这里只粗看了一下各个改动方向基本都没问题，主要是其它功能模块对原cameras的依赖迁移，以及设备组与workflow的结合、录制block的实现，我这里先传上来了，是想着如果edgeflow_camera有开发需求可以先参考着，后续review改动应该不会很大，节后细看。目前效果也是可以在11860上看到。

1，xueying branch review；
  04851b16：明暗主题、启动页及公共组件
  4f5e3480：工作空间返回入口、Account 移至左下角、Projects 导航结构及工作空间列表调整
  5cfe8ff9：项目、相机、Dashboard 等页面样式与状态展示
  1，增加图标；
  2，工作空间栏
  3，增加背景色切换，在右下角用户里
  4，增加概览页，概览页调整；


代码：
  1，mediamtx转发内容是否也保存到数据库，这样mediamtx可以持久化；
    防止冲突，只保留转发内容
    {
      "id": "source-1",
      "name": "入口摄像头",
      "source_type": "network",
      "source_address": "rtsp://192.168.1.30/live",
      "enabled": true,
      "relay_mac": "AA:00:00:00:00:02"   不需要这一项，

    }
    在b的数据库中加入一项，复用即可；
    选择视频流时可以选择是a下的还是b下的；
    这样b重启也不影响；

    b增加视频流，可以选择其他设备已有的视频流；如果选择b下的视频流；

  2，不能持久化，
    "recording": {
      "recorder_mac": "AA:00:00:00:00:02",
      "copy_macs": ["AA:00:00:00:00:03"],
    各自配置自己的录像，各自录像到自己本地，录像不需要配置其他设备，不能持久化，通过mqtt消息通知也麻烦；
  先不用考虑workflow的部分，先把设备和视频流的部分实现；

1，haiyang branch review：
  1，认证做成一个按钮的样式；
  2，右上角不需要本机设置，刷新也不在右上角的位置；在搜索栏的位置；
  3，显示视频流的状态；

  2，后端实现：
    1，数据库中保存什么内容；
    2，mediamtx的地址是存在哪里的，查询的时候是怎么获取的；

  1, 前端操作形式：
    方式1：视频流指定分发设备
    方式2：设备添加需要转发的视频流；采用这样的方式；

1，录像功能的实现；

2，功能：
  1，预览页面，设备分组也可以支持折叠；
  2，工作流的预览缩略图显示整体；

xueying：
  1，入门引导改成折叠和打开的形式；
  2，概览说明文字不需要
  3，任务图标，两个绿圈
  4，左边栏背景色，太黑
  5，查看全部教程，跳转很慢

haiyang:
  1，stage6 先个人review，然后合入；
    1, camera-recording 为什么关闭
    2，转发流，括号是源主机；

linli：
  1，默认都是免费模式
  2，部署和在线的配置文件，放到代码仓库中；

3，zejin
  5，store 系统bug解决；

1，fanshihao:
  1，profile review；
    需要有npu，或显存的占用显示；

3，950修改与部署测试；
  3，950开启启动的管理方式兼容原版，如果更新失败可以回退到原版；

2，fanshihao:

0, 内存碎片情况展示
1, 内存管理优化，参考cosmoedge中内存池 内存处理管线的设计，只用固定的内存管理方式，对比前后的区别；
2，内存碎片自动清理
3, 帧率控制的优化，现在nv12的内存拷贝是满帧率的，如果实际没有用到这么搞的帧率，这部分内存拷贝可以进行优化

2，fangsong
  0，收费系统测试；
  1，edgeflow+designer 功能测试；
    edgeflow负责并行推理，designer负责后处理；
  2, 测试包括200个data-clip上传，创建数据集，训练，保证正常；

1，haiyang branch review
  6.5是事件录像播放时候的推理图层实现，为了在不改动原生mqtt和mediaMTX的情况下也能RTP对齐，额外做了个推理信息的录制recoder，用mediaMTX的RTP来对齐。试了一晚上感觉没有更好的办法；

本地可以放多个代码仓库；

1，xueying代码review：codex/13706-development-batches check the new branch；
  1，左边栏 工作流图标
  2，左边栏背景色，太淡，
  3，默认背景色，之前偏灰，现在太淡
  4，左边栏收起动画，感觉不太流畅
  5，项目栏收起动画没有动画
  6，标题栏，应该是项目 -> 123 -> 上传数据；
  7，浅色背景中有深色部分，深色背景有浅色部分；
  
1，
  2，sync with haiyang, 方松来测试；
  1，edgeflow_cam设备管理部分；sync with haiyang;

edgeflow+designer的部分如果没问题了，可以和方松对一下使用，他来测试下；这部分如果没问题了可以把edgeflow_cam跑起来，问下@戴振华 部署方法和使用方法，和 edgeflow也差不太多，都是通过docker，然后在pc上测试就行，实现同样的设备页的逻辑；

0，haowei修改review：
  122.225.62.2:20260

1，改了工作空间的展示与筛选，
2，自动标注的类别提示词，类别数量创建时更新

4，后续可以通过workflow配置；
3，edgeflow_cam profile开发；
2，主题修改review；
1，设备发现与管理代码review；

1, 两次卡主的问题：
  1，删除项目，会扫描硬盘中大量的文件;
    百度云cfs存储速度比ssd慢好多倍，在本地测试的时候没有出现这个问题；
  2，存在200多个图集的情况下，创建数据集的时候会把连接池占满；
  优化：
    1，代码合入的review；
    2, 批量检查文件扫描，数据库连接池的问题；
    3，缺少自动测试与风险检查；增加这部分的自动测试；

1，qinle 人员要求，目前是4人，希望加到5人；


测试
  秦乐 chengchan xuzhenwei 相机的测试
    平均每个人5-7个相机的测试，测2-3天    
    750 
    d950 linux 5.0 6.0
    ab940 ar950
    et750 et
    分体式叉车盒子，955 960相机；
  zhongbojia
    savp+designer的测试；
  edgeflow测试，每个人都测一部分；

7，edgeflow_cam device development
  1，编辑workflow，然后推送到某台设备；
    进行模型转换，进行workflow推送；需要有编译阶段；
    可以进行任意设备的workflow的编辑，编辑完成后运行需要有编译阶段；
  1，是否要支持在任意一台设备上编辑其他设备上运行的workflow；
    工作流页面显示设备选择，选择其他设备即直接切换到对应设备的工作流页面；
  2，怎么进行edgeflow_cam上模型的部署，模型页面部署按钮，可以选择某台设备，选择之后会发送到这台设备上； 
  阶段1：
    每台设备编辑自己的workflow，工作流总览只起到一个可视化和跳转的功能；
    模型页面部署按钮可以选择某台设备来部署；

功能summary:
  1，支持 obb pose的标注，模型训练，推理
  2，设备发现与管理
  3，svap功能，edgeflow+designer，多机发现与互联，编辑；
  3，新版相机端适配950 960相机；
  4，前端调整；浅色和深色主题；
  5，bug修复，继续排查；

  1，相机端：适配更多平台，与edgeflow的联动
  2，edgeflow：workflow部分完善使用；

development task：
  1，收费系统问题修复；
    3，全局管理员不能到其他域内发起训练等任务；  done
    2，单张标注，可能扣费；可能免费
    1，自动标注有的时候免费；

  2，系统排查卡顿问题，云端避免出现卡主的现象；修复了几个确实会导致卡主的问题；
    上传文件处理卡住同进程其他请求，以及处理文件时一直占着数据库连接。

  3，xueying 分支 review；
    1，背景色sync with jinzhi zhaowei；
      教程部分取消连接相机；修改为设备；
    2，其他需要的改动；
    将代码合入到dev；

  端侧推理框架edgeflow_cam开发，包括：
    1，驱动层多平台适配；包括公司的不同相机与nvidia相关平台；
    2，外设功能开发，支持plc等配置；
    3，性能优化，包括内存管理与推理；减少内存碎片，提高推理效率
    4，与通用训练与推理平台edgeflow的联动
    5，在已有的检测模型的基础上，适配更多的模型推理，包括分割，特征点等；

  1，development 设备页连接池问题优化；
  2，总结现在适配新的相机需要做哪些操作；
  3,750 760相机适配；750 760 adaptation code merge；
  4，收费问题的优化；小于1元后不能进行训练和标注；

2，同步系统设计 zejin
  0，在系统设置中进行云端账号认证；
  1，数据上传云端；
    数据池中数据可以单个或批量上传云端，选择workspace，project；如果没有认证首先提示进行云端账号认证；
  2，模型下载本地；选择workspace，project，模型；
  云端不显示这个接口；只有打包版本显示，通过配置文件指定；
  可以一键跳转到云端对应界面；

1, sync with jinzhi yinsheng 
  no good of the progress, so need to take part in.  
  no report
  meeting no notification, the result is promblemtic.
  1，相关内容需要参加
  2，go through the point

7, 编辑workflow，可以选择设备，默认是自己，可以选择别人；
  如果是其他设备的worklfow，通过分栏隔开；
  在编辑workflow后，可以不执行，可以在大的画板进行workflow的执行；直接进行连接，单独控制某个workflow是否执行；

0, 外设中间层设计;适配所有外设；

1，mdns的设备发现问题；网关阻拦的问题；
  1，手动添加地址的方式；手动添加成功后另一端也会添加；
  2，获取设别列表，可以指定通过另外一台设备进行发现；
    配置网络桥接，用于设备发现；可以通过扫描来选择桥接的设备；

0，task assignment of wangpei, optimization of the code of edgeflow_cam;
  sync with yinsheng and wangpei;

2，整理所有需要适配的型号；
  高通：
    QCS8550（AR960）
  瑞芯微：
    RK3588（AR950）、RV1126B（AR760）、RV1126（AR750）
  nvidia：  
    4090+linux
    thor
    4090+windows
    orin
  macos
  树莓派


0，标注使用问题；离线版；
  只能用于标注的离线版；@zejin；
  sync with zhaowei；

现在断网的情况下要标注的话，可以有两种方式：
1，安装edgeflow离线版，需要有wsl2的支持；
2，之前做过一个专门用户标注的edgeflow，不需要有wsl，直接安装就行，不过只有手动标注和效果明显差的自动标注；这个现在没更新了；
是否需要方式2呢？如果需要这个泽瑾可以再更新一下，这个安装会容易一些，不需要wsl2，更轻量；

1，设备发现设计；

1，训练模型种类除了PT以外还要支持跑在SVAP上，至少骨骼和obb是需要的;
  1，模型导出支持deepstream
  2，pose 和 obb block；

6，合适的训练数据收集系统设计；通过workflow来实现；
  产品设计：
    增加一个监督模型，指定监督模型是什么，指定数据收集位置是哪个project，哪个标注版本；
    监督模型通过torch来推理，推理帧率可以很低，对比推理结果；
    通过后处理来运行，执行显卡用量，指定帧率，输入包括当前在线的推理结果，根据这个结果来判断是否要保存数据；
  1，数据收集，模型训练，模型更新；
  2，通过workflow的形式；

1, sync with wanggang and xiaoye；

0，xueying 分支 review；
  codex/annotation-management-20261020
• 09398879：类别/标签页布局调整。
• b1c6e560：版本列表管理交互、创建按钮位置与当前标签样式。
尚未合入development，等待检查后再合并

4, pose obb seg deepstream并行推理支持，显卡设置支持；


