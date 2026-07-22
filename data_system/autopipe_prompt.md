

数据结构设计
进行数据平台的数据存储系统的设计，数据平台最终实现的功能参考 roboflow；
本来的文件系统是这样的： /Users/abc/Documents/notebook_xinmier/data_system/data_design2.md
其中标注的json文件有3种不同的形式，参考 /Users/abc/Documents/notebook_xinmier/json_example
修改为使用数据库和对象存储的方式，data_split下图片和视频放到对象存储中，目录结构不变；标注信息存到数据库中；meta.json的信息都放到数据库中；
datasets下 dataset_info.json 存到数据库中，除此之外所有model的内容全部放到对象存储中，目录结构不变；
另外用户权限的信息也在数据库中；除了用户自己的workspace外，可以指定用户对某些workspace下的某些project有权限；
将完整的设计写到  /Users/abc/Documents/notebook_xinmier/data_system/autopipe_design.md 中；
包含对象存储完整的目录结构和说明；数据库每个表的结构和说明；

基于ubuntu22.04做一个docker，docker的名称是 autopipe_docker;
dockerfile放在 /home/zhongdawei/code/autopipe/docker 目录下，将启动指令放在这个目录下一个sh脚本中；在docker内安装 PostgreSQL 和 MinIO 支持；安装minconda和vue支持；
安装各个需要的支持：
后端:
├── fastapi              # Web 框架
├── uvicorn              # ASGI 服务器
├── sqlalchemy           # ORM
├── psycopg2             # PostgreSQL 驱动
├── minio                # MinIO Python SDK
├── celery + redis       # 异步任务队列
└── minconda             # YOLO 训练/推理（按需）

前端:
├── vue 3                # 框架
├── vite                 # 构建工具
├── element-plus         # UI 组件库
├── axios                # HTTP 请求
├── pinia                # 状态管理
├── vue-router           # 路由
├── fabric.js / konva    # Canvas 标注画布
└── echarts              # 图表（训练指标可视化）
显示安装进度

你来运行 ./build_and_run.sh 并解决中间出现的问题

结构设计；
前端使用vue，后端使用fastAPI，
前后端尽量模块化，尽量分离；
先实现roboflow的界面

docker设置：
  1，不使用minio，修改为使用seaweedFS；要修改 /home/zhongdawei/code/autopipe/docker/Dockerfile /home/zhongdawei/code/autopipe/docker/build_and_run.sh /home/zhongdawei/code/autopipe/docker/supervisord.conf 等；
  2，/mnt/data2/autopipe/storage 挂载到docker内，目录是 /data1，/data1 传给 seaweedfs 来创建存储桶，创建存储桶后挂载到 docker 内 /data 后续作为一块硬盘来使用
  3，将docker 数据库 seaweedfs 的所有配置放到一个配置文件中，包括docker要开放哪些端口，所有的用户名和密码配置，端口配置，挂载路径的设置，通过一个配置文件控制所有；
    在启动docker的时候读取配置文件来进行全部设置；

@code/autopipe/config/config.json#L1-43 需要设置为环境变量的部分，设置为全部大写， @code/autopipe/docker/docker_run.sh#L7-40 这里在读取配置时，自动将所有的全部大写的变量读出来，不需要手动再指定

@code/autopipe/docker/docker_run.sh#L77 同样放到配置文件中，另外 @code/autopipe/config/config.json#L41 名称修改为 CONTAINER_DATA_PATH;host_paths 新增 HOST_DATA_PATH
seaweedfs 下增加一个标志 enable_flag，默认是 true；如果是 true，那么启动 seaweedfs服务，将 HOST_STORAGE_DIR 挂载为 CONTAINER_STORAGE_DIR，将 HOST_FILER_DIR 挂载为CONTAINER_FILER_DIR， 将存储桶挂载为 docker内的 CONTAINER_DATA_PATH；如果是 false，那么不启动 seaweedfs服务，直接将 HOST_DATA_PATH 挂载为 CONTAINER_DATA_PATH

3个点应该是竖着的，另外鼠标停留在3个点上时，出现一个包住3个点的背景圆；点击3个点后，除了删除还有修改状态，可以修改项目的状态

docker_run.sh 中判断，如果没有 config.json 的话，提示复制 example.json 为 config.json，在config.json 中修改配置

1, 可以指定docker的tag；

像roboflow这样的平台，后台训练和推理任务怎么进行的任务调度，使用的什么框架，不同框架的对比
将调研结果写到 /home/zhongdawei/code/autopipe/doc/design_doc/task_assige.md 中，选择合适的框架来进行任务调度

除了roboflow interfence，node red ，还有哪些开源的低代码平台，将对比的结果写到 /home/zhongdawei/code/autopipe/doc/design_doc/lowcode_platform.md 中，选择合适的平台

workflow的主要目的是，没有经验的人可以通过拖拽的方式来实现快速开发，实现workflow后可以直接在现场部署

autopipe上可以启动训练任务，启动推理任务，自定义workflow，workflow中有模型推理，会有多人使用；
对于训练任务或推理任务或自定义的workflow，需要实现任务调度，可以用的资源是多机多卡，也可能是单机多卡；
训练任务和推理任务是跑在gpu上的，workflow中除了模型的部分，有的部分是跑在cpu上的，
有的workflow的执行是要求实时一直运行的，有的workflow或训练任务，是可以排队的；可以调整任务的优先级；
选择什么样的框架，来实现多机多卡任务调度，包含模型训练，模型推理，workflow执行，可以指定任务优先级，可以指定某些任务是一定要运行的；
将设计思路写到 /home/zhongdawei/code/autopipe/doc/design_doc/task_assign2.md 

/home/zhongdawei/code/autopipe/doc/design_doc/task_assign4.md 中有设计的要求，选择合适的框架，不必参考其他文档中的设计，根据task_assign4.md中的要求进行设计

1，写清楚 ray 单机部署和多机部署具体的pipeline

1, /home/zhongdawei/code/autopipe/doc/design_doc/task_design 中增加一个设计文档 ray_design.md
通用的task，可能是有显卡调用或者没有显卡调用的，怎么使用ray，怎么在autopipe中使用ray，对于任务调度系统，应该怎么通过ray设计
搞个中间层抽象出来，后续如果框架替换容易修改；
单机运行的方式，没有任务调度；

1，多机多卡的指定方式；ray自动实现


3，先实现简单的单机执行，不包含任务调度，后续增加，这样不会block开发；通过进程启动即可；通过prompt实现；
2，中间层的设置

2，ray 和 yolo的训练方式，是否可以适配；

ultralytics 中ddp的训练，如果要通过ray来调度，需要做什么修改

1, sync with sufeng，确定任务调度的实现；代码位置，中间件框架；
  任务管理，做一个中间层,设计写到 /home/zhongdawei/code/autopipe/doc/design_doc/task_design/middle.md 
  通过一个类来实现，类中有这个任务的类型，任务需要的所有资源；任务的执行，log，状态判断等；
  每一个任务都要继承自这个基类，重写其中的run函数，这个函数是要具体执行的函数；
  任务调度管理是一个单独的类，有一个add_task 函数，每一个要执行的task通过add_task加入到任务管理中；
  任务管理要负责每个任务的运行，对每个任务进行管理；
  先预留接口，不进行实现；继承自不同的基类是使用了不同的方法；
  ray的管理有一个基类，
  先实现一版，然后sufeng进行优化测试；
  需要做中间层，中间层和管理器联动；
  1，中间层定义；
  2，管理器定义；

  重写init，run函数；
任务管理，做一个中间层,设计写到 /home/zhongdawei/code/autopipe/doc/design_doc/task_design/middle.md 
通过一个类来实现，类中有这个任务的类型，任务需要的所有资源；任务的执行，log，状态判断等；
用户自定义任务或者actor通过继承这个类来实现，需要重写的是init函数和run函数，run函数是执行的部分，init函数是初始化的部分；
无论是task还是actor，都通过这个基类来实现；
任务调度管理是一个单独的类，有一个add_task 函数，每一个要执行的task通过add_task加入到任务管理中；
任务管理要负责每个任务的运行，对每个任务进行管理；
先预留接口，不进行实现；把设计写到文档中；

参考 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/roboflow_inference_claude.md 中workflow的引擎，要在autopipe中实现一套workflow整个的引擎，设计一个迁移开发的流程，怎么逐步迁移逐步开发， 模块化，单独测试，然后和前端联动，先只实现后端的部分，后端有完整的测试，把过程设计写到 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/roboflow_dev_design.md

参考 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/roboflow_inference_claude.md
将 /home/zhongdawei/code/inference/inference/core/workflows 中workflow的实现在 /home/zhongdawei/code/autopipe/backend/workflow 中实现一份，先实现核心的逻辑，对原逻辑不进行调整，要实现的核心逻辑就是block定义，workflow定义和执行引擎；不需要的部分不要拿过来；
具体要求：
utils/tools.py 下放工具函数
block 文件夹下放block的基类和相关实现
workflow 文件夹下放workflow的基类和相关实现
engine 文件夹下放引擎的基类和相关实现；
blocks_library 下放一些设定好的block
test 文件夹下放所有的测试代码，通过构造json数据进行测试，构造的json数据保存到test文件夹下，测试可复现；对完整的流程进行测试，确保测试正常；多来几个不同的测试；测试要涵盖对blocks_library中的每个block；
将代码的接口设计，执行的流程，测试用例运行指令，自定义block的教程 都记录到 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/dev_v1.md 中

1，相关需要的库要加到 dockerfile 中；
2，autopipe/workflow中相关文件与 /home/zhongdawei/code/inference/inference/core/workflows 下的对应关系写到 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/roboflow_inference_relative.md中
3，autopipe/workflow中没有移植的功能在 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/roboflow_inference_functions.md 中进行界面，这些功能的作用是什么

1，模型训练的部分，
  定义模型训练的输入输出接口，输入会指定数据集的id，输入参数字典
  输出是在指定路径下的模型文件 配置log；
  后续的模型都要继承自这个类；在启动时指定数据集和参数字典；

在 /home/zhongdawei/code/autopipe/backend/models 下定义一个模型的base类，在base类中，输入参数是个字典；
包含一个数据读取函数；
包含train函数
包含validation函数
包含inference函数
base类包含一个log保存函数，输入参数是log字典；
包含一个模型参数保存函数，输入参数是模型参数和epoch数量；
先定义函数接口，不进行实现


针对 /home/zhongdawei/code/autopipe 项目，
参考 /home/zhongdawei/code/autopipe/doc/design_doc/task_design/middle.md 中的设计；在 /home/zhongdawei/code/autopipe/backend/task_manager 中进行实现；有下面几个要求：
1，实现 BaseTask 基类 和 TaskManager，分别放到不同的python文件中；通过连接到ray集群来使用ray；
2，ray环境在dockerfile中配置，在docker的启动文件中启动ray集群，目前只有一台8卡5090的机器，在启动docker时在这台机器上启动需要的ray环境；所有需要的参数写入到 /home/zhongdawei/code/autopipe/config/config.json 中，ray单独一部分；
3，通过运行 docker_run 重新打包docker；保证docker可以正常打包，保证需要的环境能够正常启动；
4，单独写一个test文件，写完善的测试用例，测试用例要测试各种不同的情况，在docker中进行测试并保证测试正常；


1，输入 输出 后处理 接口定义设计文档；
  原始输入格式：
  workflow输入格式：
    视频 / 图像 / 参数 string bool int float
  模型输入格式：
  
  模型输出格式：
    检测框
    分割结果
    关键点
    分类结果
  
  后处理输出：
    上面所有的结果

  后处理输出：
    string / bool / int / float

  api调用的角度是什么；

对于workflow的执行，需要对输入输出的接口，数据的形式进行设计，完成一个设计文档，说明下面的点；
写到 /home/zhongdawei/code/autopipe/doc/design_doc/输入输出接口.md
workflow的输入支持 视频流  视频 图像 参数，参数可以是 string bool int float类型
workflow的输出支持 模型结果，包含 检测框 分割结果 关键点 分类结果，也正常判断结果，包含 string bool int float类型
workflow中包含模型部分和后处理部分，
模型部分的输入包含图像 参数，workflow视频流 或 视频的输入会转换为图像输入给模型，输出包含 检测框 分割结果 关键点 分类结果；
后处理部分的输入支持workflow支持的输入和模型的输出；
后处理的输出支持 string bool int float类型 
通过流程图说明上面的过程；

输入方式：
相机数据获取模块，通过sdk或网络获取输入；
参数需要人工设定
如果输入图像或视频文件，需要人工指定文件

输出方式：
1，网络通信输出，mqtt / ros
2，硬件设备sdk调用


0，数据导入，准备模型训练需要的数据；  
  1,sft的数据和evaluation的数据导入;
    导入输入: 数据路径，标注版本；
    输出：数据库中数据；包括图片和标注；
  输入导入功能；

  输入：数据路径 标注版本
  输出：数据库导入结果；


/home/zhongdawei/code/autopipe/tools 下实现一个数据迁移脚本，输入是数据路径和标注版本，要迁移的workspace名称，project名称，
输出内容是将图片 可能有的视频 标注信息进行迁移到对应的数据库和本地存储路径；

源数据的格式参考 /@code/data_platform/doc/data_design.md#L6-32  
可以参考这个数据集的内容：/mnt/data1/data_server/collections/person_all_2_sft/group_0002__alarm_camera_0
在标注的json文件中 @code/data_platform/doc/data_design.md#L123-154 有label类别和标注类型的说明
其中标注结果txt文件中的格式是这样的：
# image_tag:[垂直俯视视角]
0 0.826474 0.157519 0.264479 0.312990 tag:[特征清晰可见]
# image_tag 这一行可能有也可能没有，image tag可能没有也可能有一个或多个，会通过逗号分开；
下面每一行是一个标注框，后面可能有也可能没有 tag，如果有tag的话，图像的标签可能是零个或多个；
前面的数字表示label类别，后面4个数字表示检测框，如果有5个数字那么第五个数字是置信度；如果没有就是没有置信度；

要迁移到的数据库和格式在这个文档中 /home/zhongdawei/code/autopipe/doc/design_doc/data_plan.md 其中 @code/autopipe/doc/design_doc/data_plan.md#L227-414 这部分是标注具体的数据库设计；
视频和图片的本地路径格式是这样的：@code/autopipe/doc/design_doc/data_plan.md#L33-48 

写一个脚本，要读取这些数据，将这些数据迁移到数据库中，图像和可能有的视频也保存到对应的路径；
代码要尽量模块化，便于对每个模块进行解释和测试；对源数据的读取部分通过一个单独的类来实现，便于后续的功能扩展；
对数据库的所有操作要使用这里的接口：/home/zhongdawei/code/autopipe/backend/database
如果 /home/zhongdawei/code/autopipe/backend/database 里面缺少功能要说明缺少的部分并进行补全；

如果数据库中没有这个workspace需要提示并退出；如果workspace中没有指定的proejct也需要提示并退出
先给一个设计文档 /home/zhongdawei/code/autopipe/doc/design_doc/data_transform_design.md，有不明白的地方要问我；
docker进入的方式是运行 docker_into.sh，写完脚本后在docker内运行测试，保证测试通过，然后删除测试数据；
使用的测试用户是 admin，已有workspace 11，这个workspace下已有项目 1；
同时将这个工具代码的文档放到 /home/zhongdawei/code/autopipe/doc/operation_doc/data_transform.md 中；包含具体的使用方法，测试方法和验证方式； 

这样是进行了一个数据转化
python3 migrate.py --data-path /mnt/data1/data_server/collections/person_all_2_sft/group_0019__dm_0/  --annotation-version det_manual_0_tag_qwen_checked --workspace 11 --project 1 --user admin
需要支持 data-folder-path，如果是data-folder-path，则对folder路径下的每个文件夹进行转化，统一使用指定的标注版本，如果某个数据下没有这个标注版本，那么输出这个数据的名称来提示；

python3 migrate.py --data-folder-path /mnt/data1/data_server/collections/person_all_2/ \
      --annotation-version det_manual_0_tag_qwen_checked \
      --workspace 11 --project 1 --user admin

1，数据获取层，输入是数据集名称，输出是获取数据的接口；
/home/zhongdawei/code/yolo_for_platform/run.py 中对 ultralytics 的yolo训练的数据读取进行了修改，在对label.txt 文件时，会读取后转换为cache，这个cache生成和使用的逻辑是什么；
第一次运行训练和后续运行训练有什么不同；在cache生成然后读取后，是不是都放到了内存里，在训练运行过程中是否还会读取cache文件；

1，是否还需要cache文件，使用数据库的情况下；
在标注都是通过txt存放的情况下，第一次运行建立cache文件，后续运行的时候直接load已有的cache文件，这样可以加快把所有标注信息载入内存；
autopipe的数据设计在 /home/zhongdawei/code/autopipe/doc/design_doc/data_plan.md 中，现在所有的标注信息都在数据库中，是否还有必要建立数据集的cache文件，从数据库读标注信息到内存的过程快不快
通过文本读取所有标注，通过数据库读取，通过cache读取，对比这3种方式的效率；

模型训练：
  输入
    数据集
    训练参数
  输出：
    weight：模型参数
    log：
      参数记录
      log记录
      过程记录
    inference
  直接通过大模型实现整个过程，测试运行结果是否一致即可；
  将训练数据导出，通过同样的方法判断训练结果是否一致；

图像存在这个路径 @code/autopipe/doc/design_doc/data_plan.md#L32-49 , 标注信息存在数据库中；
数据集定义的格式是： @code/autopipe/doc/design_doc/data_plan.md#L417-452 

2，先进行接口定义，然后定义一个空的模型

前端可以直接读取，来进行参数的设置，会显示模型参数；
1，通过annotated list的方式来实现，annotated的好处对python解释器透明，可以直接使用；
  需要的校验，default等信息，通过挂元数据来实现；
  通过元数据告诉前段，需要哪些参数，需要的格式是什么；前端设置之后可以作为参数传入，传入后可以直接对应到指定的参数；
  annotated
  没必要使用 annotated，没必要，没有看到明显的优势；
  不要用 annotated，把简单的事情搞复杂了；


1，在这里定义模型训练的基类；
  输入参数，是一个config字段；

 model
  init
    通过 basemodel 和 filed 来实现，便于进行序列化，便于获取参数；

  @static
  get_parameter

  train

  inference_dataset

  inference_batch

  inference_image

  save_weight

  save_log

  get_progress

  get_total_time

前后端调用的通用接口；

模型部分 图像处理部分 任务调度 前端调用

ray接入的部分： ray task基类 -> 模型基类 -> yolo类

/home/zhongdawei/code/autopipe/backend/task_manager/base_task.py 中是ray task的基类，
/home/zhongdawei/code/autopipe/backend/models/base.py 中是模型的基类，基于模型的基类可以创建具体模型的类；
模型要通过ray来运行，那么 /home/zhongdawei/code/autopipe/backend/models/base.py 中模型的基类是否应该继承自 ray task的基类

在 /home/zhongdawei/code/autopipe/backend/models/base.py 下定义一个模型训练推理的base类，将设计和实现逻辑记录到 /home/zhongdawei/code/autopipe/doc/design_doc/model/design.md

1，输入参数与构造函数：
在base类中，输入参数是一个字典；在构造函数中定义 name epoch pretrained_weight参数，后续还会增加其他的参数，要能够在前端知道这个类需要哪些参数，这样前端可以指定参数然后通过字典传入；
对于需要暴露到前端的参数，要指定数据类型，要指定是否有默认值；暴露到前端的方式，不必参考autopipe中其他地方的实现，直接用最合理的方式实现即可；
实现构造函数中参数赋值的部分，根据传入的config字段，进行所有的参数设置，config中有的字段赋值给对应的参数，对于有默认值的参数，config中可以没有，对于没有默认值的参数在config中如果没有则报error，如果存在类型不匹配，则报error；

2，训练和推理接口：
train函数，针对模型训练的整个过程；
validation函数，针对模型验证的过程，是跑val集或test集；
inference函数，针对单张图片的推理；
batch_inference函数，针对多张图片的推理；
数据读取函数，从数据库中读取标注数据，构造成模型训练需要的内容；
配置保存函数，保存实例化的所有配置；
log保存函数，运行时保存log，输入是一行string或一个字典，是否加入前端可视化的flag；
图片保存函数，运行时保存图片，输入是图片名称 图片，是否加入前端可视化的flag；
图片保存函数，输入参数是图片名称，图片，是否加入可视化；
模型结果保存函数，输入参数是模型参数和epoch数量；
先定义函数接口，不进行实现

3, 在 /home/zhongdawei/code/autopipe/backend/models/model_task.py 中 通过 /home/zhongdawei/code/autopipe/backend/task_manager/base_task.py 中的 BaseTask， 对模型中训练和推理进行封装；输入参数是实例化后的模型类；针对训练 单次推理 和 常驻推理任务 分别定义一个task；

4，/home/zhongdawei/code/autopipe/backend/models/test_model.py 中继承基类实现一个测试，这个类中不进行真实的训练和推理，在训练和推理中设置一个延时；
  前端要能够获取到有这个类，继而获取这个类需要的参数；这个类是用来测试的；

修改 /home/zhongdawei/code/autopipe/backend/models/base.py，使用 pydantic 的方式实现同样的功能，可以参考 /home/zhongdawei/code/autopipe/backend/workflow/block/base.py 中对 pydantic 的使用

/home/zhongdawei/code/autopipe/backend/workflow/engine/v1.py 参考 /home/zhongdawei/code/autopipe/backend/task_manager/base_task.py 中的设置, 给 ExecutionEngineV1 通过task封装一下，这样可以在ray的任务调度中使用 ExecutionEngineV1，区分运行一次和常驻的情况

在 /Users/abc/Documents/notebook_xinmier/deepstream.md 中介绍nvidia deepstream,
类似的平台有哪些，优缺点对比，和直接同pytroch推理有什么优缺点

/home/zhongdawei/code/autopipe/backend/workflow 中有workflow的执行引擎，workflow的执行中有模型推理的部分，模型推理现在是通过 /home/zhongdawei/code/autopipe/backend/models 里的模型类来实现，通过torch原接口实现的，也可能有其他的图像处理部分，怎么通过 deepstream 加速，将设计文档写到 /home/zhongdawei/code/deepstream_test/doc 中
尽量保持最少改动，模块解耦，可以通过原生python执行，也可以通过deepstream执行，并预估加速后执行能加速多少

@autopipe/doc/design_doc/database/data_plan.md#L148-174 除了工作空间成员表外，增加项目成员表，模型成员表，即有的项目对某个用户是可见的，某个模型对某个用户是可见的


1，可视化的整体设计，
  1，workflow测试时的可视化
    0，添加可视化模块
      多种输入的形式；
    1，选择输入
    2，显示图像
  0，workflow部署时的可视化
      如果打开可视化，那么将可视化模块的内容拿出来；在rtsp视频流解码的内容上显示；

  两种方案；
    1，block内定义debug; block中定义，太不灵活；
    2, 定义专用的debug block;采用这样的方式
    3, workflow编辑页面，执行运行测试时显示输出： 
      1，显示选择的debug block；
      2，显示选择的output的输出；  
      
      引擎部分：
        在workflow编辑页面测试运行阶段会运行debug block,在正式部署阶段不运行debug block；
    4，预览显示的功能：
      1，选择debug block；
        workflow引擎：
          在已执行的workflow中打开运行 debug block的运行，并缓存输出结果，前端获取输出结果进行显示；
        加速方式：
          执行到debug block时进行判断，如果输入是rtsp视频流，那么从浏览器直接拿已经解码的结果，不重复解码；

@autopipe/backend/workflow2/data_type.py#L35-87 输入可能是单张图片，也可能是batch输入，如果是batch输出，那么后续的处理也是基于batch的，最后的结果输出也是基于batch的，怎么进行适配，有什么不同的设计思路，将可行的方案写到 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/batch_input.md 中，是只进行变量类型的适配，还是workflow引擎就知道是多batch输入，还是有什么其他合适的方法

1，多路视频流的接入与使用方式：
  image类型输入支持：
    图片
    视频
    rtsp单路视频流
    rtsp多路视频流
  解析后对应 单张图片， batch图片；
  image默认就是batch的形式；后边进行适配；
  之后的执行都进行相应的适配；对于通用的block可以进行通用的封装；
  
  2，跟着图像走的结果，都加入图像中；没必要；

  1，组输入的形式，对于所有的batch输入进行封装
    输入的时候，image自动识别是batch输出；
    后续的所有类别，自动判断是batch输入；
    如果一开始是batch输入，

    首先变量类型进行适配；
    其次workflow知道当前有几个batch输入；

  方案1：
    batch数据类型
  方案2：
    提示引擎是batch输入；在执行block时进行优化，支持batch执行的block，需要单独写；
    不支持的，通过循环来实行，通过引擎来实现；
    采用方案2比较合适；
    2，model模块的设计；deepstream的接入与使用；
      workflow中多路推理的实现；deepstream的测试，tensorRT接口的测试；

1，mqtt通信的格式；将workflow运行结果pub出去；
  将output的结果通过workflow的执行引擎直接进行mqtt的pub；
  在正式部署的时候进行这样的pub；

1，deepedge在平台上的实现方法；包括相机部署的部分；这部分haowei负责；
  1，手动采集，标注，模型训练，结果导出；
  2，自动回流的部分；
    通过一个workflow来实现，
      输入：图像，mqtt结果
      模型block是sam3
      然后定义一个数据导入block；
      定义一个模型训练和结果导出block；
    然后还是人工走标注检查，模型训练，结果导出；

运行 /home/zhongdawei/code/autopipe/docker/docker_run.sh 基于 /home/zhongdawei/code/autopipe/docker/Dockerfile 创建docker，在一台服务器上有多个用户， @autopipe/config/config.json:3-5 每个用户创建的镜像tag和容器名称不同，一个用户创建完成后，其他用户在创建的时候速度回快吗？会复用docker层吗

/home/zhongdawei/code/autopipe/doc/design_doc/videostream/video.md 中详细写各种方案的对比，优缺点分析，并给出你的建议



