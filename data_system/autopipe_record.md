

autopipe

roboflow缺点：
  1，没有多个标注版本的管理；
  2，没有整个工作流的workflow；完整管理整个生产流程；

后端
  1，数据存储，先基于现有的方式；
  2，用户管理； zdw
  3，workflow框架 liuyu


0，先出完整的设计；然后出开发pipeline与排期；
1，先把整体界面留好；把数据留好；然后可以共同开发，数据全部用于测试，可以任意修改；

1，数据存储要支持多文件夹；可以无限扩容；
  1，新建项目时自动指定路径；
  2，对自己权限开放的路径可见；

  1，项目下有dataset和model；

2，模型训练支持多机任务调度；

1，管理员账户登录后
  1，增加用户权限管理
  2，增加io监控
  3，有dataset栏；用户只能编辑自己项目下的dataset，管理员可以编辑全部的dataset；

1，agent页面，海洋；

2，project界面，王阳
  1，数据标注版本管理还是要有；
  2，数据集创建在这里进行；先创建当前的数据集;
  3，模型训练在这里来进行；可以选择单个或多个数据集，如果选择多个数据集，那么会组合;

3，models，林立

4，worlflow，刘宇+，
  1, 后端逻辑
  2，前端界面
  3，服务器运行某个workflow；
  4，部署到端侧设备，直接在端侧设备中运行workflow；

3, sync with jinzhi;

2，界面简单开发，留空，做整体的需求和开发文档;

3，多机训练任务调度的设计；

2，数据格式的设计
  按project分的好处是纯粹的分布式，缺点是跨project的数据集设置和模型结果比较，有的模型是不同的project的数据训练的，放在哪个project中都不合适；
  通过workspace来划分，用户的 workspace下分别project，dataset models；
  这样可以实现跨 project 的 dataset，和跨project的 models；

  project，属于某个用户，权限管理比较方便，用户拥有这个project下所有的东西，包括dataset和model；
    set1
      anno1
      anno2
    set2
      anno1
      anno2

  3，dataset 和 model 是对应的；一个model一定属于一个dataset，一个dataset可以对应多个model；
  2，一个model一定对应一个项目；
    完全根据 project的方法来管理；
  1，首先根据workspace划分，workspace下有project；project下有 collections 
      dataset，dataset下有models；

    在设置dataset的时候，支持选择其他project的dataset，这样支持多project的数据进行训练，但是训练结果还是针对某个project的；

  1，一个用户有自己workspace下的全部访问权限，在定义数据集时，可以有其他的访问权限；

  采用这样的方案：
    混合方案：Dataset/Model 属于 Project，但支持 Workspace 级视图
    Workspace
    ├── Project A
    │   ├── Collections
    │   ├── Datasets      ← 物理归属在 Project 下
    │   └── Models
    ├── Project B
    │   ├── Collections
    │   ├── Datasets
    │   └── Models

1，多机任务调度实现，这是比较独立的模块；可以先通过62.2和62.9来实现；


