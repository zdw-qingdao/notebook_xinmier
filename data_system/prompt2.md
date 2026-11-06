

--------------------------------------------------------------------- 相机中间层 prompt:

做一个隔离不同平台相机取流与推理的中间层：
  1，下面是驱动层，驱动层包含不同相机的sdk接口，不同平台的模型推理接口；上面是应用层，不同相机不同平台上应用层的内容是相同的，应用层包含前端，后端等；应用层通过中间层来控制相机硬件，进行模型推理；
  2，中间层通过 base.cpp 中的基类来实现
    需要做一个相机的基类，其他各种不同的相机都继承自这个基类，基类包含所有的相机控制接口；
    需要做一个模型推理的基类，torch的推理继承自这个基类，基类中包含所有模型推理需要的接口；
  3，实现相机中间层基类后，子类实现一个模拟相机，模拟相机的视频流是通过播放一个视频；模拟全部的控制接口；
    实现模型推理中间层基类，实现pytorch推理的子类；
    中间层的基类只包含基础接口，基础接口上层的功能函数模块在 /home/zhongdawei/code/camera_code/edgeflow_cam/modules 中实现；后续增加新的相机或计算平台，只需要在drivers中增加新的子类；
  4，怎么指定使用哪款相机和哪种推理架构，通过配置文件指定，配置文件指定的结构才会进入编译，使用的时候也是使用指定的部分；
参考内容：
  原版系统代码与文档，根据其中的sdk api调用来进行中间层的设计：
    代码：/home/zhongdawei/code/camera_code/camera2d-rk3588
    文档：/home/zhongdawei/code/camera_code/camera_doc
参考设计方案：
  /home/zhongdawei/code/camera_code/camera_doc/python_system_desing/middleware_design.md

测试要求：
  在 edgeflow_cam_zdw 容器中进行编译与测试；复用编译内容；

在 /home/zhongdawei/code/camera_code/edgeflow_cam/docs/middle 中写新的中间层设计文档，实现要分步骤进行；有不明白的问题要问我，我review之后进行分阶段实现；

--------------------------------------------------------------------- 相机上workflow prompt:

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
5，创建 读取 保存 删除工作流应该通过 c++ 代码来实现，python代码只进行执行workflow engine；
6，在系统启动的时候读取所有的block library中所有block的输入输出和参数信息，即所有前端需要的信息，后续在编辑的时候不需要调用python，只有在执行的时候需要调用python

测试要求：
  本机测试在 edgeflow_cam-ubuntu22 容器中进行，复用已有的编译结果；
  相机测试在 edgeflow_cam-ubuntu22_960 容器中编译，在960相机（root@192.168.10.126）上进行；

在 /home/simmir1/zdw/code/edgeflow_cam/docs/workflow 中生成设计文档，不确定的问题问我，设计分步骤的实现方案，我review后进行分步的实现；

----------------- 代码
  说明 xxxxx 文件修改的原因，使用逻辑，调用pipeline；
  review完成，创建commit后，进行下一阶段开发，开发完成后等我review；

/home/simmir1/zdw/code/autopipe/backend/device_discover/ 下每个文件的作用，通过pipeline图来说明

在我们反复讨论的问题背后，有没有一个更深的问题，我们一直在绕着它走，却没有真正问出来；


以前的产品非常重要；这个时间点也必须去做一些改变；不仅是合理的，也是必须的；

1，pipeline：
  0，产品设计
  1，技术方案与过程拆解，有几种不同的实现方式，优缺点是什么；
  2，写详细的prompt，尽可能的详细，生成设计文档
  3，逐阶段开发review，边开发边review；同时在不同的窗口进行提问
  4，通过流程图的方式来说明运行的链路；
  5，操作层面的自动化测试；

better for better;

1，理解能力，设计能力，技术设计与产品设计；
  理解ai开发的内容；
  打磨的能力，要不断challenge；

2，直接许愿；需要有设计有理解；
3，一直等执行；需要并行；ai在跑了，时间就饱和了；





