
6，数据平台json文件适配的问题，看是否每一部分都进行了适配；华煜 linli fangsong 林立 需要确定责任人；

4，说明书，整个的执行过程；分为几种不同的情况；
  web训练+web部署
  web训练+现场部署
  现场训练+现场部署；
  有网dockerhub；没网通过u盘；

后续：
  1，现场docker的搭建；怎么在windows电脑上搭建；
  2，用户名称，workspace名称重复的问题；
  3，dataset 名称重复的问题
  4，model 名称重复的问题
  参考数据保存，数据保存通过文件名称分开，名称不能重复；
  5，数据版本管理；
    1，创建数据集的时候，可以选择把标注和图片路径cache下来；生成cache文件，训练可以直接读取cache文件；在训练的时候，如果有cache文件那么使用cache，如果没有cache那么实时读取；

7，删除项目
  包括删除权限的引用；
  包括模型表的删除；

5，测试下目前的dataload时间和cache方法的差异

zenmux报销；
水壶

6，agent实现
  先进行设计，端口预留，交互逻辑；

5，用户登录，用户权限，收费方式的整体设计；
  1, 管理员界面可以配置用户权限，包括workspace的权限，project的权限，model的权限；

4，ray MediaMTX 的 dashboard
  1，如果是admin，要显示dashboard；
    1，资源占用情况
    2，ray任务调度的情况
    3，视频流情况
    4，部署情况；

3，workflow通过任务调度封装一层；

6，厦门项目的测试工件，不需要，拿到硬件实验室；

zejin：
  1，离线客户端的编译过程
  2，代码适配的方式
  3，模型调用的方式；单独写一套？使用sam2或者yolo；

5，多路运行测试；可视化开发与测试；

2，haiyang进行workflow测试，细节调整；linli进行前端接入；
  规定好接口；

1，review架构设计方案，zejin haiyang linli
  sync with linli, zejin，wangyang, how to use the video stream.
  1，其他部分获取rtsp视频流的方法，怎么和相机列表的部分联动；
    方案1：所有的视频流都通过相机列表获取，连接，其他的部分只能选择已连接的视频流；
    方案2：后续除了已连接的视频流外，可以另外指定其他视频流；先采用方案1即可；
  0，workflow的后端，前端调用后端的方法；

7，背景优化

5，模型推理block，需要有模型文件转换；
  后端 haiyang
  前端 林立
4，linli，前后端接口；
  1，使用workflow5；
  2，flowcontrol block;
3，保存结果查看与下载；
1，模型结果展示部分查看效果；

8，用户计费逻辑设计与实现；资源点的消耗方式；
  消耗行为：
    数据上传
    保存
    模型训练
    使用store中的数据或模型

7，完善block和workflow生态的方法

6，workflow部署部分：
  3，视频流测试；
  输入形式说明
  数据流转形式说明
  batch输入支持
  deepstream支持
  端侧部署支持，预留接口；
  数据保存block实现，保存图片；
  定时执行单次的逻辑；
  deepstream缓存10秒视频的逻辑，触发时保存；
  可视化block实现；
  通过文档说明设计，目前的说明方式解释太费劲
  实现要点优先级说明；

  显示的内容：
    1，debug block，完全自定义显示，在cpu上进行图像绘制；
    2，通用的单张图片显示变量，通过这个类型的变量进行显示；自定义draw函数；
      浏览器上在rtsp上叠加显示的方式，这样的问题是可能不同步；

# ------------------- 

3，go through the system, check what do we need? 

2，实现监督模型的部分；

1，design the ray framework;
  1，所有对ray的使用，排队情况的查看；现在有几个任务在执行，显卡占用的情况；
  2，模型训练
  3，模型推理
  对旋转框的标注和训练支持；

5，workflow后端引擎；

# ----------- thursday
doc about the current progress and the following plan.

# ----------- 开始测试

5，模型store，也可以加入到自己的模型列表中，可以进行推理的预览；

周一：
1，曲晨，叉车盒子+相机，找杜工或者袁伟国，通过slam的方法判断前进还是后退；
2，workflow的部分，相机侧，分工来看怎么搞，相机侧可以嵌入式来搞；

1，sync with haiyang；
  2，workflow的重新设计
    2，直接接入到当前的软件中；
    1，直接把designer的部分拿过来；直接把svap的部分拿过来；
    0, 获取workflow运行中数据的方式：
        1，通过redis队列；
        2，通过mqtt通信；
  1，针对需要的工况重新设计；

  0，workflow的事情：
    1，workflow的调用接口；
    2，workfow的可视化方法；输出指定的可视化topic，直接叠加到rtsp视频流；
    这样对于前端来说，输入和输出都指定了；
    是输出解码叠加显示的图片，还是只输出draw的内容，在浏览器上叠加显示；


1，update the ray part;
  这部分后续再适配；
  启动指定推理，自动判断有没有，没有的话创建，有的话复用的函数，直接调用这个函数来使用sam3的推理；








