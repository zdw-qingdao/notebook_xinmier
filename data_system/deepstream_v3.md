

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

# -----------------------  workflow5

在 workflow2 中有一套workflow的执行引擎，可以定义block，通过block组合成workflow，然后执行workflow；workflow的执行逻辑是进行图的构建，逐层执行block；这一套目前只支持单张图片的输入；
在 workflow3 中有改进版本，设计文档是 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/v3/dev.md
但是针对flow control的block处理不够好；下个版本需要针对batch输入flow control的情况进行优化处理；
/home/zhongdawei/code/autopipe/doc/design_doc/workflow/v5/dev.md 是新的设计方案；


在 workflow5 中实现一个新版本的workflow的执行引擎，执行逻辑，数据类型，代码结构可以参考workflow2 workflow3，代码要模块化，代码可读性要好，具体要需要满足下面的要求：
注意代码实现在 /home/zhongdawei/code/autopipe/backend/workflow5 文件夹，设计文档放在 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/v5/dev2.md 中

1，data_type.py 中定义一个 BatchData 类型变量；里面是一个字典，字典类型是这样： {batch_index:{input_name:input_value}}
  有类方法可以支持根据flowcontrol的结果来拆分新的BatchData；
  可以根据batch_index来获取一个具体的输入；

1，block类对 deepstream 和 多路输入的支持；block_base.py 中定义了block的基类，
  1，增加类方法 is_deepstream_supported，表示该block是否支持 deepstream；
  2，增加成员函数 init_deepstream() 如果该block支持deepstream，将构建deepstream图的操作放在这里，通过调用这个函数，可以构建deepstream的pipeline；
  3，增加成员函数 run_deepstream() 如果该block加入了deepstream的pipeline，run_deepstream函数从deepstream的流中fetch对应的执行结果；转换为BatchData,其中input_name input_value是 get_output指定的内容，是后续block的输入；如果是一路那么只有一个元素；run_deepstream() 不需要接受上游的输入，只从deepstream中fetch结果；run需要接受上游的输入，run_batch需要接受batch输入；
  3，增加成员函数 is_batch_supported()，表示该block是否支持batch输入的情况；在多rtsp视频流输入的情况下，会出现batch输入的情况；
  4，增加成员函数 run_batch()，如果该block支持batch输入，那么BatchData会直接输入到  run_batch 函数中；run_batch 的输入是BatchData变量，输出也是BatchData变量；输出的BatchData中也和get_output指定的类型对应；如果该block不支持batch输入，那么针对BatchData输入的情况，执行引擎会循环执行该block的run，再组装为BatchData；
    run_batch 的输入是BatchData变量，输出也是BatchData变量；
    如果遇到flow control的block，针对flowcontrol的输出情况，engine需要将batch拆分输入给flowcontrol block控制的block；
  5, run返回的都是data_type中定义的类型,即get_output指定的类型，run_deepstream 或者 run_batch 返回的都是 BatchData；
  6，run方法的输入是输入字典和index参数，如果是单张图片输入的情况，index始终是0，如果是batch循环输入的情况，index是当前输入在batch的索引；
  7，增加成员函数 is_debug，表示这个block是否是一个用户debug的block；workflow执行引擎可以选择执行debug block或忽略debug block；
  8, run_batch run_deepstream 返回值都是 BatchData 类型变量，其中数据是和 get_output 对应的，这部分由用户实现；即 BatchData 中 input_value 类型是 data_type.py 中定义的某种类型；

2，对执行引擎的部分进行调整：
  1，原本 engine/engine.py 中 run 函数进行单帧输入，获取单帧输出；输入字典key是输入名称，value是Image，中间进行各个block的运行；需要增加一个 run_stream 函数，run_stream 函数接受流输入；输入字典key是输入名称，value是rtsp视频流列表，里面可能是1个或多个rtsp视频流；如果是run_stream，需要进行下面的操作：
  在workflow初始化的时候，`Engine.init()` 完成静态 plan，`run_stream()` 的启动阶段调用 `init_deepstream()` 并build/start,deepstream的图单独构建并开始运行；对于当前workflow，从输入节点向下找，如果block is_deepstream_supported 是true，那么通过该block的 init_deepstream() 来加入deepstream pipeline；block is_deepstream_supported 是false，不加入 deepstream 的 pipeline，只执行init函数进行初始化，也不再从这个block向下找其他block来加入的deepstream pipeline；
  如果输入节点接了多个支持deepstream的block，都会加入到 deepstream的pipeline，如果一个block支持deepstream，但是上一个block不支持，那么这样的block也不加入deepstream的pipeline；
  换句话说，如果从输入一直到某个block，都可以走deepstream，那么都加入deepstream pipeline，剩下的部分不加入，走run或run_batch计算；
  engine的run执行的是单张image输入，其中能够复用run_stream的部分就复用；

  2，deepstream流构建好之后一直运行，然后循环进行workflow的执行；run_stream 是非阻塞式的，启动deepstream工作流和block执行部分后，不会阻塞；可以通过接口拿当前的输出结果；
  3，每个block只实例化一次；block实例内可以cache之前的某些状态，workflow执行引擎增加stop函数，执行则终止工作流的执行包括deepstream的部分，安全退出；

  4，在run_stream的情况下，执行到一个block时，有几种情况：
    1，对于已加入deepstream pipeline中的block，如果下游还是deepstream的block，那么这个block的执行直接跳过；
    2，对于已加入deepstream pipeline中的block，如果下游存在非deepstream的block或者接了输出节点，那么执行 run_deepstream 方法，即从deepstream中fetch对应的信息，然后输出；
    3，对于已加入deepstream pipeline中的block，执行 run_deepstream 方法是不需要输入参数的，是从deepstream流中fetch对应信息；
    4，对于没有加入deepstream pipeline中的block，如果 is_batch_supported() 返回true，那么执行run_batch，输入是BatchData变量，如果 is_batch_supported() 返回false，那么循环执行block的run方法，将输出再拼成BatchData

  5，在run_stream的情况下，对于图像输入节点，如果下游接的都是deepstream pipeline中的block，那么不需要进行处理；如果下游存在不在deepstream pipeline中的block，那么要从deepstream中取解码后的图像并转成BatchData，其中input value是Image类型的变量；来提供给下游block作为输入；

  6，对于debug_block，执行引擎增加函数 enable_debug_blocks() 和 disable_debug_blocks()，启动或关闭所有debug_block的执行；在debug_block启动的情况下，debug_block的输出都加入更新到一个字典中；可以通过这个字典访问当前的debug_block的输出结果；

  7，对flowcontrol情况的处理：
    1，如果遇到非flow control block，那么如果支持run_batch就执行run_batch，如果不支持run_batch，那么循环调用run，通过engine再将输出结果组合为BatchData变量
    2，如果遇到flowcontrl block，执行flowcontrol block的run或run_batch，获取控制结果，如果控制结果全是terminate，那么和单图输入的情况一下，下游的block终止；
      如果控制结果不全是terminate，那么说明下游的block还需要运行，在进行下游的block执行前，engine来根据flowcontrol的情况，将输入BatchData拆分成新BatchData，然后输入给下游的block；

3，deepstream pipeline建立与执行的部分放到一个单独的类中；里面有对deepstream整体的管理；

除了 workflow2/block_library 中的block要迁移过来，另外实现下面的支持deepstream的block：

1，yolo推理的bolck，实现所有类方法，支持单张图片输入，也支持batch输入，也支持 deepstream；init中载入了模型，run中通过torch的接口进行推理；run_batch 也通过torch的接口进行批量推理；
init_deepstream中加入到 deepstream 的 pipeline，run_deepstream 中从deepstream中fetch结果，fetch多路视频流的检测结果转换为 ObjectDetection 类型输出；
data_type.py 中 ObjectDetection 类型补充实现；

2，图像crop的block，改造 transformations/image_crop.py 中的block定义，除了原有的功能外，增加deepstream的部分；
2，图像resize的block，改造 transformations/image_resize.py 中的block定义，除了原有的功能外，增加deepstream的部分；

实现一个detection_vis_block，是一个debug block，输入是Image和ObjectDetection，run中实现在Image上画ObjectDetection的信息；

出一个完善的设计文档，放在 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/v5/dev2.md 中；有不确定的问题要问我；如果我的要求存在问题也要问我；让我先来review这个设计文档，文档review和调整结束后，进行整套系统的实现；

在 autopipe_docker_24_2:zdw_24 docker内进行测试；
通过构造workflow json数据进行测试，构造的json数据保存到test文件夹下，测试需要可复现；yolo推理需要的内容下载到 test/yolo 目录下；
构造测试需要的图片，保存到test路径下，多路rtsp视频流先通过本地文件模拟；
对完整的流程进行测试，测试要涵盖所有可能出现的情况，包括但不限于下面的情况：
  1，支持deepstream和不支持deepstream的block的组合；
  2，测试包含yolo模型推理block的workflow，包含单图推理的执行和多rtsp视频流输入的执行; 包含或不包含crop resize的block；包含 detection_vis_block 的打开或关闭；
确保测试正常；将测试用例运行指令，自定义block的教程都加到 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/v5/dev2.md 中；











