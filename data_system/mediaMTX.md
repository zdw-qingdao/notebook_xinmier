

在autopipe中加入视频流的docker环境支持，数据库支持，后端接口支持，前端显示；

docker环境配置设计
  mediaMTX环境安装到一个docker中，通过dockerfile安装，在最后面安装，这样可以复用已经建好的docker层；通过 supervisord.confg 的配置启动
    在config.json中，增加mediaMTX项：
    1，dashboard的端口暴露出来，
    2，给浏览器转发的视频流接口暴露出来
    其他mediaMTX的内部使用，外部不需要使用的端口不需要暴露；

数据库的设计如下，注意所有数据库的后端代码都在 /home/zhongdawei/code/autopipe/backend/database 中实现，数据库的定义和操作的接口：
  Camera: 
    id, workspace_id, name,
    host,username, password, 
    note,
    created_at, updated_at

  视频流；
    CameraStream:
      id
      camera_id
      port
      source_path
      mtx_path
      metadata
      transport
      enabled
      last_checked_state，包含下面几种状态
        unknown
        online
        auth_error
        path_error
        first_frame_timeout
        unsupported_codec
      last_checked_at
      created_at, updated_at

视频流的后端代码在 /home/zhongdawei/code/autopipe/backend 下新建一个 videostream 的文件夹，在下面写视频流需要的后端代码；其他部分也通过这个来获取视频流，所有对视频流的后端操作都在这里实现，前端只调用后端的接口：
后端接口如下
  1，建立视频流连接
    输入：视频流所有需要的信息；
  2，查询视频流状态
    输入：视频流mtx_path
  3，获取转发视频流url；
    输入：视频流mtx_path
  4，关闭视频流连接
    输入：视频流mtx_path
  5，删除视频流；要调用数据库的操作来删除数据库中对应内容；
    输入：视频流mtx_path
  6，获取当前所有相机名称
  7，如果支持的话，自动获取局域网能够获取的rtsp相机列表

在前端的workspace界面，新增一栏部署，点进部署后有两栏，一栏是相机列表，一栏是算法部署；先实现相机列表栏，算法部署栏先空着；
默认是打开相机列表栏，下面是相机列表栏的描述：
  1，有一个按钮是添加视频流，点击后设置视频流的信息来添加，注意：
    1，可以手动设置所有信息来添加视频流，包括相机的信息
    2，可以选择已有相机，这时候相机的部分会填写为已有相机的内容，然后只需要设置剩余部分的信息即可；
  2，页面显示相机列表，每个相机下可以有一个或多个视频流
  3，视频流可以选择连接或关闭，点击连接后数据库中视频流的enabled字段修改为true，关闭则修改为false；；
  4，如果视频流的连接是选中的，则建立视频流的连接，显示视频流当前的状态，在这个页面5s更新一次状态，如果前端不在这个页面，不需要进行状态查询；这个参数在创建视频流的时候设置，默认是5s；点击视频流后会显示视频流的meta信息，再点击会折叠；
  5，点击预览显示视频流画面，右侧有个预览框，可以显示预览画面；是通过后端接口，根据 mtx_path 来获取转发的视频流链接，然后通过浏览器显示；
  6，在后端重启的时候，对于 enabled 的视频流会自动建立连接；这样点击预览的时候可以直接显示画面，不需要等待连接；

先在 /home/zhongdawei/code/autopipe/doc/design_doc/videostream/dev.md 中写完整的设计，有不清楚的地方要问我，有觉得设计不合理的地方要问我，在我review设计后进行完整的实现并测试通过；





