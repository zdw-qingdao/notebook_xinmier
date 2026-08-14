

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

在 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/v6/workflow_engine_codereading.md 中完整的介绍当前 workflow_engine 的实现；
不同变量的作用，每个文件每个函数的功能，调用的关系

在 /home/zhongdawei/code/autopipe/backend/workflow6/data_type.py 中针对每个类型的变量加入 decode_mqtt 和 encode_mqtt，不通过 /home/zhongdawei/code/autopipe/backend/workflow6/workflow_engine/mqtt.py 中针对每个类型进行适配；mqtt.py 中针对普通类型直接编码和解码，对于有 decpde_mqtt 和 encode_mqtt 函数的类型，调用执行类型自定义的编解码函数；

/home/zhongdawei/code/autopipe/backend/workflow6/data_type.py  除了Image类型外，不同类型的encode 和 decode 尽量采用同样的方式，在不改变功能的情况下，代码保持一致，基本都是将类变量编码解码，尽量采用统一一致的方式

engine的执行在 /home/zhongdawei/code/autopipe/backend/task_manager_3/adapter 中进行封装，封装为oncetask；

# --------- 5 启动器

在 /home/zhongdawei/code/autopipe/backend/workflow6/workflow_manager 中实现启动器的部分
调用接口参考 @doc/design_doc/workflow/v6/design.md:213-235 

启动器首先更新workflow实例表；

如果存在 camera_engine 或 inference_engine block，
  将输入的workflow进行拆分，拆分方式是判断workflow中的block是否有 engine 参数，如果有 engine 参数，只能是 camera_engine inference_engine workflow_engine 中的一个；拆分后分为 camera_engine block 和 对应的输入； inference_engine block 和对应的输入；去除两种block后，新的workflow json和对应的输入；
  拆分过程中要更新 mqtt 消息表；拆分后的输入输出通过mqtt topic来对应；

  对于 camera_engine 的block，要循环调用 setup_camera_block 函数，函数输入是block实例的json信息 和 这个block的输入信息；
  每次调用 setup_camera_block，是针对一个block实例加一个相机输入；setup_camera_block函数的实现先空着；
  这个block是要运行在相机上的；setup_camera_block 中后续要实现的内容是将block的内容部署在输入相机上；消息表中指定的topic是指定的名称格式；
  camera_engine的block实例，输入中存在且只存在一个rstp视频流，即一个相机，也就是要运行在这个相机上；每个相机也最多接一个camera_engine的block；即每个相机最多运行一个推理block；

  对于 inference_engine 的block，要循环调用 setup_inference_block，多个inference_engine block在类型相同，参数相同，只有name不同的时候认为是同种block；
  输入是同种block的json信息（不包含block名称）和所有使用到这个类型的block的输入（也包含对应block名称）；对于一种的block（类型相同而且参数相同），调用一次 setup_inference_block，setup_inference_block 的实现也先空着；后续 setup_inference_block 中同种block，要在deepstream引擎上batch执行；batch执行的结果写入到batch表中；

  去除了上面两种block后得到新的workflow json和更新后的input json；

针对每个workflow实例，循环调用 start_workflow_engine；输入是当前的workflow json，和input json（如果存在camera_engine block或 inference_engine block，那么workflow json 和 input json是更新过的），每个workflow实例启动一个task；
进行测试并保证测试通过，测试workflow中先都不包含 camera_engine 和 inference_engine 的block；先不实现 setup_camera_block 和 setup_inference_block 函数内的部分；

先在 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/v6/workflow_manager.md 中写设计文档，有不明白的问题问我，我review之后再进行实现与测试

# --------- 6 推理引擎

在 /home/zhongdawei/code/autopipe/backend/workflow6/inference_engine 中实现推理引擎的部分
调用接口参考 @doc/design_doc/workflow/v6/design.md:277-296 

在 /home/zhongdawei/code/autopipe/backend/workflow6/block_library/models/yolo_person_detection.py 中设置这个block可以选择 inference_engine 或 workflow_engine, 如果是 inference_engine，在这个block的 setup_deepstream 中包含设置 deepstream 推理需要的内容；

在 setup_inference_block 中通过任务调度启动 inference_engine；同步要写推理batch表；
目前先不进行batch的合并，只对输入的batch中可以合并的合并；不修改已经运行的部分；

先在 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/v6/inference_engine.md 中写设计文档，有不明白的问题问我，我review之后再进行分布的实现与测试；


# --------- 7 启动器中 setup_inference_block 的部分完成；


# --------- 8 模型推理block，完成的定义，和前端联动的方式；

5，前后端联合测试；
4，所有暴露给前端的接口

3，相机推理部署实现；
2，模型推理测试block实现，支持推理引擎； 推理引擎实现；
1，starter进行主模块的实现和对workflow执行引擎的调用；

2，如果对应到输入，那么不需要pub；

7，单帧的情况下，可视化怎么实现；
  同样通过mqtt topic的方式，获取一帧的输出；

6，实现推理引擎的部分；

go through the manager parts;

1，相机引擎不知道要pub的topic是什么，在这里是否传入要pub的topic，还是单独解析；
  setup_camera_block
  setup_inference_block 函数

  按照现有的方法还有没有必要写mqtt topic的表？有，前端需要通过这个表来获取相关信息；

6，推理block，默认都是一个gpu？gpu分配的问题；动态调整batch的问题；

5，可视化的适配

4，前端的适配；

2，相机部分的定义；需要相机端进行适配；这部分进行适配；

1，推理引擎的实现，结合模型推理block的补充，设置为deepstream引擎；再进行测试；

0，模型推理block的实现，设置为普通引擎，先进行整套系统的测试；
  1，先不指定输入参数，load固定路径的模型；
  2，通过数据库索引载入指定模型；需要先有训练好的模型，传入的是模型表的id；
    前端block需要进行适配；




