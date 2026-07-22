


1，rapid模式使用，使用教师模型自动识别，人工检查，进行训练，deployment；
  相当于deepedge中加了人工检查那一步；

2, 相机的接入，输入输出的接口定义，通过一个文档来定义明确的接口；是一个标准化的东西；
  和嵌入式联动的部分
  1，输入部分：
    王阳先来服用saip的接口，获取相机视频数据；
  2，输出部分，先通过mqtt来指定格式内容；可以参考roboflow可以输出的部分；
    这里没必要搞复杂，输出接口：topic 名称 类型 数据；


3, linli+liuyu one week, then it depends on the progress;
  1，roboflow inference 数据类型定义，这里怎么直接用来作为标准定义；
  2，workflow 中使用model的block，先只考虑推理的block；
    block库；
    整体的接口对接方式，详细的流程图；

增加cpu->gpu gpu->cpu转换block
如果一个block支持通过deepstream运行，那么优先通过deepstream执行；

1，deepstream 调研；workflow的执行支持通过deepstream加速；
  对数据接入和模型推理的部分使用 deepstream；其他的部分可以自动

5，厦门音频项目跟进

视频解码和推理技术选型：
  1, deepstream 问题
    1，是否用了graph界面
    2，c++代码，除了调用 deepstream 的部分，还写了什么部分；
    3，多路推流的情况是怎么设计的，有没有测试过效率对比；
    我们通常一台机器带几台相机，合流的情况带来的增益有多大；

    2，写python代码，在docker环境中测试；先通过视频来测试；
    1，docker中配置 deepstream 的环境；
    1，怎么优化batch运行和数据输入的部分；

  1，deepstream deside，技术选型；
  2，视频解码和模型推理使用 deepstream 9.0的python接口；
  3，workflow支持单独运行或通过deepstream加速；
    可以指定多个workflow的合并运行；
    如果合并运行，那么多个workflow通过一个进程来跑，通过deepstream来进行batch加速；

deepstream的接入；
  deepstream的使用方式，多workflow的合并方式
  推理引擎可以重新设计

  1，workflow执行引擎，现场部署的时候不需要走任务调度；也可以通过任务调度来启动；一样；
    根据卡进行进程分配；
    单卡内单进程，单卡运行的workflow合并，在workflow step执行的时候通过 deepstream进行处理；
    需要设计前端页面；
    workflow引擎需要进行适配，后续再处理这个，实现方法：
    1，多workflow合并
    2，同层的推理任务并行处理，这样是自己手写的方式；
    3，当遇到要走deepstream的block时，通过deepstream合流处理；
    4，通过deepstream的方式，先集中处理deepstream的部分，然后再执行workflow；

    推理引擎的部分需要单独设计；
      1，通过deepstream来获取推理结果
      2，跑workflow；

    对workflow，可以直接支持batch输入；

summary:
  1, deployment design:
    相机列表
    workflow列表，可以添加输入相机源，如果需要1一个相机，一次添加一个相机；可以添加多次；
    如果需要两个相机，一次添加两个相机，同样添加多次；
    一个添加的workflow是一个进程，进程内对多组输入进行批量处理，目前可以先考虑一个相机的情况；

训练版本带来的增益：
  1，基于web；
  2，自动标注更好用；
  3，标注版本管理；
  4，界面美观；
  5，训练结果展示；

输入：rtsp视频流
输出：mqtt topic，name type value

haiyang:
  1，模型训练和推理，结果保存；

1，增加一个模型结果表，表里有模型名称，模型路径，训练用户
2，@autopipe/doc/design_doc/database/data_plan.md#L108-129 
  增加每个用户可见的项目
  增加每个用户可见的模型

workflow的执行单进程即可，不需要搞进程池，通常都是串行的

sync with haiyang and huzejin:
  6，创建数据集，支持批量选择；

  5，前端模型训练和结果展示；
    1，怎么判断有哪些模型；
    2，怎么判断要指定哪些参数；
    3，怎么判断要显示哪些结果；

  2，模型训练时前端选择的依据：
    dataset_id              当前项目数据集 + 开放数据集
    model_id     当前项目模型 + 开放模型
    对应后台项目输入，是一个数据集id和模型id；

  1，模型导入的功能，管理员支持模型导入功能；验证是pt文件，复制为 last.pt best.pt;
    导入方式，在数据集页面加一个模型导入；

1, 重构workflow的部分；


haiyang:
  1, add sam3
  2, 训练和推理的接口，都通过ray的任务调度，目前默认用一张卡；
  3, 参数和展示内容的设置；

2，workflow部分：
  2，sync with haiyang, linli;
    haiyang 后端
    linli 前端；
    可以专注做后端的部分；前端的部分linli，后端的部分haiyang;
    1，前端获取有哪些block，通过block的注册；
    2，前端获取block的 输入 参数 输出；
      1，如果是模型参数，要选择已有模型；输入是模型的名称；
    3，前端构建block后，生成json文件，保存到指定位置；
    4，执行的时候，选择已有workflow，指定输入；通过ray的封装来执行；
    5，workflow执行的可视化；
    6，前段进行workflow执行的测试；

九重问题：
  2，结果评测；
  1，数据采集和标注，评估；
  0，标注效率

  图片标注数量：
    100张有效果，500张以内完成模型；
  1， 基础功能拖拽，复杂的也要开发代码，效率高；
  1，标注质量问题
  1-3天搭建
  5-7天上线

  1，评估项目难度
  2，基础模型+finetune
    标注标准问题；

-----------------------------------------

1，自动标注的逻辑；
  加上自动标注功能；自动标注是调用推理接口，将返回结果进行保存；这里用的是固定的置信度；
  人工设置一个置信度；

2，训练代码 -> 模型结果 的关联，
  1，BaseModel 加一个静态方法，返回模型名称；没必要，通过register的方法即可；
  2，模型结果数据库的表中，加一项是 模型名称；在选择预训练模型的时候，要找对应的模型来选择；log中也加上；
  3，保存meta信息：
    1，label定义；pt文件里有
    2，代码路径；表里加了一项；
  4，上传模型的时候，设置模型名称，选择模型类型，上传到指定位置；在训练的时候可以选择这个模型，也可以选择其他模型；
  5，yolo启动训练的时候，除了表中的模型，来看有无内建模型；通过名称来区分文件夹；

1,内建模型存放；
  /data
    model/ 
      sam3
      yolo

2，创建标注版本的问题；怎么搞成更易用的；
  目前创建标注版本的使用有点复杂；
  新增数据的标注不又好；
  1，先选择标注版本，再具体看数据；在标注的表里放是否reviewed；不同标注版本是独立的；
  2，数据集的创建，首先选择标注版本，然后选择数据；
  1，数据库修改，迁移脚本修改；

  1，sam3不支持训练
  2，加一个静态方法，是否支持训练；sam3不支持训练，这样的任务目前只进行推理

  3，自动标注的时候，sam3模型用内建模型；
  4，如果选择自己的模型，从表里选择；

  3，跑inference的逻辑：
    1，选择模型：
      所有的内建模型，自己训练的模型都可以选择；
    2，选择模型后，判断模型是什么代码；
      读表判断是哪个代码
    3，sam3：传入内容包含label；手动指定label，预览，通过调置信度来显示当前的情况；确定置信度，执行inference；

    4，yolo：
      1，显示定义好的label，从模型的pt文件中读取；
      2，预览
      3，执行inference

    执行inference的过程：
      1，选择模型之后，点generate之后，load模型（ray任务调度，执行init），执行单张infernece，返回inference给前端；
        
      2，触发自动标注：
        1，前端给后端传什么：
          image_list, 对应图像表的id；
    ，前端给后端传入的内容：
      只传图片；
    5，写数据库的部分；


1，需要修改数据库的接口，需要修改迁移文件；包括标注的写入，统一修改；
  #### images — 图片表
  | 字段 | 类型 | 说明 |
  |------|------|------|
  | id | SERIAL PRIMARY KEY | 图片 ID |
  | data_clip_id | INT REFERENCES data_clips(id) | 所属数据批次 |
  | video_source | TEXT | 来源视频名称（如"20260601_0900"） |
  | file_name | TEXT NOT NULL | 文件名（如"000001.jpg"） |
  | storage_key | TEXT NOT NULL | 对象存储完整路径 |
  | width | INT | 图片宽度 |
  | height | INT | 图片高度 |
  | hash | TEXT | 文件哈希（普通索引，非唯一；仅供查询，迁移不做去重） |
  | tag_ids | INT[] | 图片级 tag ID 列表（引用 tag_definitions 中 scope='image' 的记录） |
  | status | TEXT DEFAULT 'raw' | 状态：raw / annotated / reviewed |           需要删除这个；
  | created_at | TIMESTAMP DEFAULT NOW() | 创建时间 | 

   问题是这样的话，不同版本的设计；

  #### annotations — 标注信息表

  对应 JSON 中每张图片的每个标注实例。使用统一的 `data` 字段存储标注数据，根据所属标注版本的 `annotation_type` 决定数据格式。

  | 字段 | 类型 | 说明 |
  |------|------|------|
  | id | SERIAL PRIMARY KEY | 标注 ID |
  | image_id | INT REFERENCES images(id) | 所属图片 |
  | version_id | INT REFERENCES annotation_versions(id) | 所属标注版本 |
  | label_id | INT REFERENCES labels(id) | 标签 ID |
  | tag_ids | INT[] | 标注级 tag ID 列表（引用 tag_definitions 中 scope='annotation' 的记录） |
  | confidence | REAL | 置信度（0-1，手动标注可为 NULL，模型推理时有值） |
  | data | JSONB NOT NULL | 标注数据，格式由标注版本的 annotation_type 决定（见下方说明） |
  | created_at | TIMESTAMP DEFAULT NOW() | 创建时间 |

  标注信息加 状态，是否review； data 如果是 null，那么就是没有信息；如果没有这一条就是没有数据，有但是json为空也是没有数据；
  如果操作过这张图片，就是标注过；review过需要手动点击reviewd；
  reviewed
  raw annotated reviewed;
  创建数据集的时候，需要首先选择标注版本，然后选择数据；先不考虑选择其他标注版本；

2，支持删除图片，数据库删除还是打个标签，这个可以后续再看；
  1，存储里，图片删除
  2，标注删除
  3，数据集调整；
    数据集的表中，现在是index的范围，修改为index的百分比；修改为比例；

  1，前端和数据库修改
  2，代码载入修改，注意开闭区间问题；
  3，代码载入的时候，如果图片上 raw的，需要报警； 写到log中，error字段：

1，训练结果的展示：
  1，loss曲线 train val
  2，val 指标的表格；
  3，test图片展示；
    1，对图片在线运行inference，可以调整置信度来过滤；

week progress:
  4，部署页面；
  3，workflow前端页面；
  2，标注与基本逻辑，模型训练；
  1, web工具；
  0，现场标注工具；

1，haowei：deepedge的情况
  1，ray调度的部分
    1，进行测试
    2，优先级机制
    3，添加超时关闭；
    4，多机多卡测试



2，linli，后端和前端的接口；
  1, 后端和前端的接口
  2，前端现状；

2，相机部分的代码合入

1，离线标注工具
2，模型训练 http://122.225.62.9:10860
3，相机图像查看；
4，workflow部分；
  前端和后端；

厦门项目，自己的手套，自己的麦克风；


1，rtsp视频流接入的逻辑；
  1，可以选择连接或者断开；
  2，如果连接的话，后端一直连接；前端切换页面，关闭也不影响；
  3，相机信息需要写入数据库；
  4，后端重启后，点击具体某个workspace的部署后，再读数据库获取相机信息，默认是断开状态；

3，项目，数据采集，数据标注，模型训练检查；方松执行

0， conda环境为什么采用这样的方式，调整成简单直接的方式；没必要，有需要最后再调整即可

docker的问题：
1，为什么不同人的docker需要重新打；

还是采用方案2：
  方案1：
  1，添加相机；
    给相机添加视频流；
  方案2：
  2，直接添加视频流，使用完整的url

针对一个相机
  1，信息：ip 用户名 密码
  2，需要指定：path
  3，针对某个path的相机的动作：
    1，判断相机能否建立连接，建立连接
    2，通过指定端口获取不同信息；



2, rtsp视频流的接入，采用统一的方式；统一的后端接口，这样各个模块都可以用，
  其他部分对这部分是无感的；

  4，docker环境的配置
  3，整体方案的设计；包括数据库和后端接口；
    1，后端对rtsp视频流的处理要单独一个文件夹，单独进行测试；测试的时候模拟一个rtsp视频流；
    3，建立连接，判断状态，获取数据；关闭连接等接口；
    4，通过一个视频流管理类管理所有的视频流；
  2，mediaMTX的使用；
  1，后端框架的选择，mediaMTX;

1，加入视频流的部分，wangyang测试这部分；
1, generate the mediaMTX code; test in local machine. sync with wangyang 



权限系统调研与设计；   zejin
model推理block支持；  haiyang
model推理block batch支持； haiyang
workflow batch支持； haiyang
debug block支持；workflow支持； haiyang
workflow运行ray调度支持；haiyang
ray调度支持优先级，支持超时退出；haowei
自定义block实现； zdw
block前端支持，怎么通过后端完全自定义，解耦前端的逐个适配；自定义block也方便；zdw
算法部署设计与实现，包括后端数据库 zdw



• 已生成配置文件：tools/deepstream_test2/config_infer_yolo11n_b4.txt。
  配置说明：
![alt text](markdown_assets/image-2.png)


  它复用 test3 已生成的 yolo11n.engine，配置为 batch=4。运行时传入恰好 4 路视频：



在 autopipe_docker_24_2 docker内，怎么执行这个测试：
/home/zhongdawei/code/autopipe2/autopipe/tools/deepstream_test2/multistream_yolo.py
测试指令是什么

进入 autopipe_docker_24_2 docker后，执行 
cd /opt/autopipe/project/tools/deepstream_test2 && CUDA_VISIBLE_DEVICES=0  python multistream_yolo.py \
    --infer-config config_infer_yolo11n_b4.txt \
    /opt/nvidia/deepstream/deepstream/samples/streams/sample_1080p_h264.mp4 \
    /opt/nvidia/deepstream/deepstream/samples/streams/sample_1080p_h264.mp4 \
    /opt/nvidia/deepstream/deepstream/samples/streams/sample_1080p_h264.mp4 \
    /opt/nvidia/deepstream/deepstream/samples/streams/sample_1080p_h264.mp4

  它支持多路本地视频或 RTSP/HTTP 流，通过 GPU 解码、nvstreammux 批处理并行送入 YOLO 的 nvinfer 配置推理；无显示模式默认
  使用 fakesink，可加 --display 显示拼接画面。

1，deepstream 简单测试；了解使用方法；

1，worlflow需要适配：yolo crop人，图片resize，使用大模型进行推理；

1, docker可以正常启动，运行网站和deepstream

