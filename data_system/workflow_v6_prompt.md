

# --------- 1 
workflow2 workflow5中是workflow引擎的实现，设计文档分别在 /autopipe/doc/design_doc/workflow/v2 /autopipe/doc/design_doc/workflow/v5 中
要在 workflow6中做一版新的workflow；相关设计在 /autopipe/doc/design_doc/workflow/v6/design.md 中；
文件结构如下：
- data_type.py 是数据类型定义
- block_base.py 是block基类；
- workflow_engine 是执行引擎的部分
- utils 文件夹下放工具函数
- block_library 是各个block的具体实现
- inference_engine 是推理引擎的部分
- workflow_manager 是启动器的部分；其中调用了 inference_engine 和 workflow_engine，而且是通过任务调度的方式；
  对于运行在相机上的推理block，要调用camera_inference_setup函数，在 camera_inference_setup.py 中写这个函数，把输入参数都写上，先不进行实现；

data_type.py 参考v5实现一版，其中flowcontrol是其中一个类型，先只实现这个文件；

# --------- 2
继续实现 block_base.py，进行下面的调整：
  1，flowcontrol是都有的最后一个输入；默认值是true；
  2，参数设置可以是选项的方式，要提供的几个值中选择；
  3，去掉deepstream的部分；
  4，增加子block自定义的init函数，参数设置的部分增加一个更上层的init函数；
  5，run 需要先根据 get_input 检查类型，在上层在封装一下，自动检查类型是否正确，根据 get_input_defaults，对于没有default value的输入，必须有这一项
  6, execute 和 run 返回类型是 blockresult 或者 nodestop，如果是 valid_flag 是false，那么返回的是 nodestop

  7，增加函数接口，输出运行类型，是camera inference 还是普通block；默认是普通block；可以支持增加参数选择；这里要采用某种固定的方式；


# --------- 3
新版本需要数据库中新增表  @doc/design_doc/workflow/v6/design.md:100-173 ，根据这里的表的定义，更新 data_plan.md，并更新autopipe中数据库的部分

# --------- 4

在 workflow2 中有一套workflow的执行引擎，可以定义block，通过block组合成workflow，然后执行workflow；
workflow的执行逻辑是进行图的构建，逐层执行block；参考这套执行引擎，继续在 workflow_engine 中实现一版新的执行引擎；同样是进行图的构建，逐层执行block；
使用现在的block基类和逻辑，flowcontrol使用现在的方式，不单独处理，而是作为一个输入，如果execute返回了nodestop，那么停止这个block和后续的block的执行；代替之前的flowcontrol的功能；
workflow的json文件定义根据 @doc/design_doc/workflow/v6/design.md:26-67 
workflow执行引擎的调用根据 @doc/design_doc/workflow/v6/design.md:289-408 
支持单帧输入和流输入，如果输入中有一个是流，那么就使用流输入的形式；流支持mqtt和rtsp，rtsp只针对Image类型；
在workflow/test/ 下进行完整的测试，测试要涵盖每一种情况，保证测试通过，运行正常；测试docker：autopipe_docker_24_0
在 block_library 中参考 workflow5，制作一些block用于测试，注意基于新的基类；其中模型推理的block是yolo的人体检测；
流的输入，rtsp或者mqtt是根据数据库中的表来获取的相关信息，然后进行了数据获取；
测试的时候需要模拟视频流或mqtt topic，将相关信息写入表中；然后测试workflow执行引擎的运行；测试完成后清理测试数据；

先在 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/v6/workflow_engine.md 中写设计文档，有不明白的问题问我，我review之后再进行实现与测试

# --------- 5 启动器
在 workflow_manager 中实现启动器的部分，调用接口参考 @doc/design_doc/workflow/v6/design.md:213-235 
其中 setup_camera_block 函数先空着， setup_inference_block 的部分也先空着，先实现 start_workflow_engine 的部分；


# --------- 6 推理引擎
在 inference_engine 中实现推理引擎，接口定义根据：


# --------- 7 启动器中 setup_inference_block 的部分完成；



# --------- 7 模型推理block，完成的定义，和前端联动的方式；

先完成简单的模型推理的部分，支持deepstream，resize和crop后续再考虑；







