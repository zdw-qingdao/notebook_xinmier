

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

# --------- 6 模型推理block

autopipe/backend/workflow6/block_library/models 下删除原来的yolo_person_detection.py，模型block使用的需要是模型表中的某个模型；
创建一个 yolo_detection.py，实现一个 yolo_detection 的block；
block需要的参数：
  1，执行引擎设置；
  2，模型表中的id；
block的输入是image
block的输出是 ObjectDetection
在模型表中创建一个测试用的模型，进行测试并保证测试通过；使用包含yolo_detection推理的block进行workflow的整体测试并保证测试通过；测试完成后清理数据库中的测试数据；
如果有执行问题，记录到文档autopipe/doc/design_doc/workflow/v6/issue.md中说明原因和解决方法

# --------- 7 模型转换

对数据转换中心进行调整：
1, 数据库中增加一个模型转换表，包含模型id，模型转换类型，包含 svap 950 等，模型转换参数，模型转换状态；模型转换结果文件夹路径；转换结束时间；
2, 在模型页的模型转换中心点开后，选择一种要转换的模型后，下面有开始 停止 下载按钮，有状态显示：未开始 / 转换中 / 转换完成 / 转换失败
3, 未开始状态不能点击停止按钮；转换中不能点击开始按钮；在转换完成的状态才可以点击下载按钮；
4，点击开始后，可以退出这个页面，通过数据库来实现持久化；转换完成或失败要更新模型转换表；
5，同一种转换类型不同的参数对应的是不同的转换任务；
6, 增加对deepstream的支持，增加一项转换是trt转换，将这个模型页对应的best.pt，转换为deepstream运行推理需要的文件，需要的转换代码在 autopipe/backend/model/model_export 中新增一个文件；所有需要的参数都手动设置；
7，对trt转换的任务，task分配gpu为0.1；其他类型的不变
8，转换后的文件存放到 deployment/deepstream 下；deepstream下和之前其他的模型转换的文件夹命名相同；

config.txt preprocess.txt 中可以怎么设置batch，设置的batch需要怎么对应，设置batch后输入只能按照指定batch吗？怎么指定范围batch？engine中是否有batch的指定

# --------- 8 推理引擎

在 autopipe/backend/workflow6/inference_engine 中实现推理引擎的部分，

创建一个推理引擎的类，构造参数和 setup_inference_block 的参数相同，这个类根据输入的block类型和参数，完成deepstream graph的构建，根据视频流输入来指定输入，
输出是指定的mqtt topic；

在 autopipe/backend/workflow6/block_library/models/yolo_detection.py 中设置这个block可以选择 inference_engine 或 workflow_engine, 如果是 inference_engine，在这个block的 setup_deepstream 中包含设置 deepstream 推理以及输出需要的全部内容；deepstream需要的文件默认在模型文件夹下的 deployment/deepstream 文件夹下；

原本 autopipe/backend/workflow6/workflow_manager/inference_setup.py 要放到 autopipe/backend/workflow6/inference_engine 中；

setup_inference_block 增加一个参数，是否支持batch调整；默认是false；
setup_inference_block首先要判断输入的block和指定的参数，对应的模型文件夹下，是否有 deepstream需要的文件；如果没有则不进行后续操作，返回error；

setup_inference_block 获取输入后，如果不支持batch调整，将当前的输入作为一个batch加入到batch表，allow_batch_merge 是false，然后通过task启动 推理引擎；

如果支持batch调整，首先获取batch表中所有相同的block_type 和 block_param 且 allow_batch_merge 是true的行；假设有n行
每个batch输入最多支持m组，m是指定阈值；

首先判断是否要合batch：
  如果 n*m 大于n行batch中输入instance的数量+当前输入的instance的数量，那么执行合batch的操作；
  否则不执行合batch的操作；
如果不执行合batch：
  当前的输入作为一个单独的batch，通过task启动推理引擎；
如果执行合batch：
  将当前的输入合入到已有的batch中；如果能够不拆分合入，优先不拆分的方式合入，否则拆分合入到不同的batch中；
  如果某部分要合入到一个已有的batch，首先要停止这个batch的task，然后合并输入后通过task启动推理引擎；更新batch表；

先在 autopipe/doc/design_doc/workflow/v6/inference_engine.md 中写完善的设计文档，有不明白的问题问我，我review之后进行分步的实现与测试；
测试要包含各种可能的情况，创建一个模型和需要的deepstream文件来测试，测试完成后清理测试数据；

需要增加workflow instance停止的设计，
在workflow manager 中增加workflow停止的函数，该函数的输入是需要停止的workflow instance id 的list，函数中首先更新workflow实例表；
调用推理引擎的停止函数，输入同样是需要停止的workflow instance id 的list，这个函数中函数中关闭所有推理引擎相关的内容，batch表要同步更新，batch任务进行相应调整；
调用workflow执行引擎的停止函数，输入同样是需要停止的workflow instance id 的list，函数中关闭所有workflow执行引擎部分的内容，workflow实例表要更新；

@backend/model/model_export/model_packages.py:467-468 这里应该是自己编译得到的so文件，
在导出deepstream的时候要同时编译保存so文件，保存在生成的文件夹中，config文件中设置对应的路径
然后使用需要的so文件来进行prase，在yolo block中获取prase后的变量来转换成mqtt的topic；
要验证导出deepstream结果的时候so文件可以正常生成，运行推理后yolo block中可以正常获取prase后的变量并进行mqtt的topic输出


# --------- 9 启动器中 setup_camera_block

# --------- 10 block和前端联动的方式；

5，使用哪个deepstream的导出结果，目前是默认使用随机的一个文件夹；应该修改为根据数据库读取最新导出的；
  2，后续所有的部署都在一个edgeflow上，可以执行在其他部署edgeflow的设备上运行某些部分；
    那么需要支持一个workflow的输出是另一个workflow的输入；
    推理的部分要自动处理合batch的情况；
  3，使用现在的方式，workflow的输出可以作为其他workflow的输入；
    workflow的输出可以作为其他workflow的输入；
  在其他设备上执行相当于workflow的执行，推理batch自动处理；始终是8路的batch；


1，workflow的输出可以作为其他workflow的输入；
  这样一个workflow可以运行在不同的设备上；
  在这种情况下，怎么给workflow指定输入；同样的方式指定输入，可以是一路或多路输入；
  没必要：
    单独实现svap部署的栏，先临时取代svap部分；这阶段是svap+designer；
    svap有分流的功能，如果一个相机在不同的工位用到了，要提供分流的功能；
2，录像 拍照的支持；

3，gpu资源分配的问题；可以指定对某个block分配的gpu资源是多少，几个batch，每个batch的gpu数量是多少；

4，全局部署的跨机面板，可以编辑所有的部署面板；可以支持跨机的启动和关闭；




