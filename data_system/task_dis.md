

denghao， sync with yinsheng：
  测试在相机上运行的环境和接口；
  考虑怎么在相机上执行workflow；

haowei：
  ray任务调度优化
  对workflow执行引擎进行封装；

zejin：
  1，模型显示优化；
  2，自动标注；

王阳优化：
  3，项目版本简化，自动进入到一个标注版本，自动进入workspace
  2，标注优化，sync with zejin
    快捷键，配色
  1，视频流界面美观调整
  0，为什么视频流预览显示不了，在本地的100服务器，怎么能够正常看视频流；

linli：
  3，自定义block的存放：
    存放在workfspace下，存放为block代码的形式；

  2，准备block内容；
    1，roboflow inference block迁移，inference的block先实现简单版本；
    2，svap designer block 迁移；  
    3，做一些预设的workflow；

  1，模型推理block适配；

  2，通用workflow的存放；
    1，一个单独的表，是公共workflow，管理员可以将某个workflow设置为公共workflow；也可以删除某个公共workflow；
    2，用户可以从公共workflow中选择一个模板，基于这个开始开发；

  1，参数设置 parameter：
    1，基本数据类型，需要人工指定
    2，基本数据类型，需要选择，默认输入参数是当前workspace_id，选择项在函数中自定义；
    3，block特定前端怎么放；特定参数怎么设置；
    方案1：只在前端针对不同的block适配
    方案2：后端定义接口，前端动态实现；没必要，采用方案1即可；

haiyang:
  1，workflow 后端执行引擎优化，支持deepstream，多路rtsp视频流；

1，mqtt通信的部分，在workflow执行引擎中实现

2，用户登录，用户权限，收费方式的整体设计；
  1, 管理员界面可以配置用户权限，包括workspace的权限，project的权限，model的权限；
  通过数据库的表来实现；
  3，appstore，about data and model；
  
4，agent实现；

5，io dashboard，如果是管理员会显示，普通用户不会显示；
  包括ray的部分
  包括视频流的部分；

4，docker拆开的方式，通过 compose 来启动多个docker；





