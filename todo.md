
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

4，haiyang进行workflow测试，细节调整；linli进行前端接入；

3，生成3.0版本代码；

2，review架构设计方案，zejin haiyang linli
  sync with linli, zejin，wangyang, how to use the video stream.
  1，其他部分获取rtsp视频流的方法，怎么和相机列表的部分联动；
    方案1：所有的视频流都通过相机列表获取，连接，其他的部分只能选择已连接的视频流；
    方案2：后续除了已连接的视频流外，可以另外指定其他视频流；先采用方案1即可；

1，workflow设计整合，代码生成; 整合设计；写明所有的设计要点，然后完整整体design；



