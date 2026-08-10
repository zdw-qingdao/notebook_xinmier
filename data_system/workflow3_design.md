


# -------- deepstream docker环境的安装：
在 /home/zhongdawei/code/autopipe2/autopipe/docker/Dockerfile 中后面加上 deepstream9.0 的支持，
测试要求：
1，通过 /home/zhongdawei/code/autopipe2/autopipe/docker/docker_run.sh 能够正常构建容器 
2，在容器内要能够正常使用 deepstream9.0

# ------- 测试代码的生成：
在 /home/zhongdawei/code/autopipe2/autopipe/tools/deepstream_test2 下写一个python脚本，测试多路视频流通过deepstream进行并行的图像解码和yolo模型的推理；
1，在docker环境内执行，已安装deepstream9.0;
2，不用参考其他的代码风格，其他地方没有deepstream相关的内容，只考虑在 deepstream_test2 中生成测试脚本即可;
3，进入docker的方式是执行 /home/zhongdawei/code/autopipe2/autopipe/docker/docker_into.sh，对应的docker是 autopipe_docker_zdw_24_2
4，测试视频使用deepstream镜像中自带的视频；
5，需要从网络下载需要的yolo模型的权重，转换为 deepstream 需要的格式；

对block来说，输入就是一帧帧的图像，不需要输入视频流；
data_type.py 中的数据类型不需要调整，还是目前这些数据类型；视频流在具体运行中通过 Image 类型表示

# -----------------------  workflow3

在 workflow2 中有一套workflow的执行引擎，可以定义block，通过block组合成workflow，然后执行workflow；workflow的执行逻辑是进行图的构建，逐层执行block；这一套目前只支持单张图片的输入；
在 workflow3 中实现一个新版本的workflow的执行引擎，执行逻辑，数据类型，代码结构可以沿用workflow2，代码要模块化，代码可读性要好，要实现一些额外的功能；
具体要需要满足下面的要求：

1，block类对 deepstream 和 多路输入的支持；block_base.py 中定义了block的基类，
  1，增加类方法 is_deepstream_supported，表示该block是否支持 deepstream；
  2，增加成员函数 init_deepstream() 如果该block支持deepstream，将构建deepstream图的操作放在这里，通过调用这个函数，可以构建deepstream的pipeline；
  3，增加成员函数 run_deepstream() 如果该block加入了deepstream的pipeline，run_deepstream函数从deepstream的流中fetch对应的执行结果；转换为get_output指定的类型 list return，是后续block的输入；
    因为可能是一路或者多路，所以输出是list；如果是一路那么只有一个元素；run_deepstream() 不需要接受上游的输入，只从deepstream中fetch结果；run需要接受上游的输入，run_batch需要接受batch输入；
  3，增加成员函数 is_batch_supported()，表示该block是否支持batch输入的情况；在多rtsp视频流输入的情况下，会出现batch输入的情况；
  4，增加成员函数 run_batch()，如果该block支持batch输入，那么batch输入会直接输入到  run_batch 函数中；输出也是 get_output指定的类型 的列表形式；
    如果该block不支持batch输入，那么针对batch输入的情况，执行引擎会循环执行该block的run，再组装为batch；
  5, run返回的都是data_type中定义的类型,即get_output指定的类型，run_deepstream 或者 run_batch 返回的都是指定类型的列表；
  6，run方法增加一个参数，index，如果是单张图片输入的情况，index始终是0，如果是batch循环输入的情况，index是当前输入在batch的索引；
  7，增加成员函数 is_debug，表示这个block是否是一个用户debug的block；workflow执行引擎可以选择执行debug block或忽略debug block；

2，对执行引擎的部分进行调整：
  1，原本 engine/engine.py 中 run 函数进行单帧输入，获取单帧输出；输入是Image类型，中间进行各个block的运行；需要增加一个 run_stream 函数，输入是 rtsp 视频流列表，里面可能是1个或多个rtsp视频流；如果是run_stream，需要进行下面的操作：
  在workflow初始化的时候，deepstream的图单独构建并开始运行；对于当前workflow，从输入节点向下找，如果block is_deepstream_supported 是true，那么通过该block的 init_deepstream() 来加入deepstream pipeline；block is_deepstream_supported 是false，不加入 deepstream 的 pipeline，只执行init函数进行初始化，也不再从这个block向下找其他block来加入的deepstream pipeline；
  如果输入节点接了多个支持deepstream的block，都会加入到 deepstream的pipeline，如果一个block支持deepstream，但是上一个block不支持，那么这样的block也不加入deepstream的pipeline；
  换句话说，如果从输入一直到某个block，都可以走deepstream，那么都加入deepstream pipeline，剩下的部分不加入，走run或run_batch计算；

  2，deepstream流构建好之后一直运行，然后循环进行workflow的执行；run_stream 是非阻塞式的，启动deepstream工作流和block执行部分后，不会阻塞；可以通过接口拿当前的输出结果；
  3，每个block只实例化一次；block实例内可以cache之前的某些状态，workflow执行引擎增加stop函数，执行则终止工作流的执行包括deepstream的部分，安全退出；

  4，在run_stream的情况下，执行到一个block时，有几种情况：
    1，对于已加入deepstream pipeline中的block，如果下游还是deepstream的block，那么这个block的执行直接跳过；
    2，对于已加入deepstream pipeline中的block，如果下游存在非deepstream的block或者接了输出节点，那么执行 run_deepstream 方法，即从deepstream中fetch对应的信息，然后输出；
    3，对于已加入deepstream pipeline中的block，执行 run_deepstream 方法是不需要输入参数的，是从deepstream流中fetch对应信息；
    4，对于没有加入deepstream pipeline中的block，如果 is_batch_supported() 返回true，那么执行run_batch，输入是list，如果 is_batch_supported() 返回false，那么将输入list循环执行block的run方法，将输出再拼成list；

  5，在run_stream的情况下，对于图像输入节点，如果下游接的都是deepstream pipeline中的block，那么不需要进行处理；如果下游存在不在deepstream pipeline中的block，那么要从deepstream中取解码后的图像并转成Image类型的list；来提供给下游block作为输入；

  6，对于debug_block，执行引擎增加函数 enable_debug_blocks() 和 disable_debug_blocks()，启动或关闭所有debug_block的执行；在debug_block启动的情况下，debug_block的输出都加入更新到一个字典中；可以通过这个字典访问当前的debug_block的输出结果；

除了 workflow2/block_library 中的block要迁移过来，另外实现下面的支持deepstream的block：

1，yolo推理的bolck，实现所有类方法，支持单张图片输入，也支持batch输入，也支持 deepstream；init中载入了模型，run中通过torch的接口进行推理；run_batch 也通过torch的接口进行批量推理；
init_deepstream中加入到 deepstream 的 pipeline，run_deepstream 中从deepstream中fetch结果，fetch多路视频流的检测结果转换为 ObjectDetection 类型输出；
data_type.py 中 ObjectDetection 类型补充实现；

2，图像crop的block，改造 transformations/image_crop.py 中的block定义，除了原有的功能外，增加deepstream的部分；
2，图像resize的block，改造 transformations/image_resize.py 中的block定义，除了原有的功能外，增加deepstream的部分；


实现一个detection_vis_block，是一个debug block，输入是Image和ObjectDetection，run中实现在Image上画ObjectDetection的信息；

出一个完善的设计文档，放在 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/v3/dev.md 中；有不确定的问题要问我；如果我的要求存在问题也要问我；让我先来review这个设计文档，文档review和调整结束后，进行整套系统的实现；

通过构造workflow json数据进行测试，构造的json数据保存到test文件夹下，测试需要可复现；yolo推理需要的内容下载到 test/yolo 目录下；
构造测试需要的图片，保存到test路径下，多路rtsp视频流先通过本地文件模拟；
对完整的流程进行测试，测试要涵盖所有可能出现的情况，包括但不限于下面的情况：
  1，支持deepstream和不支持deepstream的block的组合；
  2，测试包含yolo模型推理block的workflow，包含单图推理的执行和多rtsp视频流输入的执行; 包含或不包含crop resize的block；包含 detection_vis_block 的打开或关闭；
确保测试正常；将测试用例运行指令，自定义block的教程都加到 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/v3/dev.md 中；




1，workflow 部分细化接口，输入输出；
  实例化与调用过程，分别不同的文件夹，分别进行测试，最后再接起来；
  具体设计完成，进行初版实现；


4. workflow执行引擎中，每次都是处理单帧的情况；
  首先有一步是获取输入，在这一步会获取mqtt topic，或者将视频流拆为图片；
  在执行引擎有一步准备输入的过程，最后执行的时候输入都是单帧的形式；
3. 每个block都有 get_online_info，写到数据库，前端通过数据库可以显示运行结果；
2. 每个变量类型都可以是mqtt topic；封装一下
1. 不需要有单独的video类型，只有一个image类型即可；所有的类型定义都是单帧的；video是image类型的序列化情况

6，deepstream引擎设计；

5，deepstream合并器设计；

4，workflow执行引擎设计；

4，通信模块设计，支持不同的数据类型；
  topic名称定义方式；

3，block定义设计；是否支持相机，是否支持deepstream；

2，数据表设计，包含运行结果的部分；通过json来记录；

1，拆分器设计，第一阶段可以先只允许一个推理block，后续可以该成级联的方式；
  拆分器在workflow保存插表的时候就保存在表中；在表中本身就包含拆分的结果；拆分结果不需要包含输入信息；

1，先进行workflow的拆分：

3，在拆分之前，先调整block的定义，说明对不同引擎的执行情况；

添加某个实例
关闭某个实例
调整实例并重新启动；

后续不再需要往相机传模型；


