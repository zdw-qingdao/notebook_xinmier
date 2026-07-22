

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



# ----------------------- prompt for workflow3

## ------------- 整体要求
在 workflow2 中有一套workflow的执行引擎，可以定义block，通过block组合成workflow，然后执行workflow；
其中数据类型有Image，表示单帧的图像输入； 在 workflow3 中实现一个新版本的workflow的执行引擎；需要满足下面的要求，先出一个完善的设计文档，放在 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/v3/dev.md 中；

## -------------- 具体要求如下：

/home/zhongdawei/code/autopipe/backend/workflow2/data_type.py 中的数据类型不需要调整，还是目前这些数据类型；视频流在具体运行中通过 Image 类型表示
/home/zhongdawei/code/autopipe/backend/workflow2/engine/engine.py 中 run 函数进行单帧输入，获取单帧输出；输入是Image类型，中间进行各个block的运行；
增加一个 run_stream 函数，输入是 rtsp 视频流列表，里面可能是1个或多个；如果是run_stream，需要进行下面的操作：

在workflow初始化的时候，deepstream的图单独构建并开始运行，对于当前workflow，从输入节点向下找，如果block is_deepstream_supported 是true，那么通过该block的 init_deepstream() 来加入deepstream pipeline；block is_deepstream_supported 是false，不加入 deepstream 的 pipeline，只执行init函数进行初始化，不再从这个block向下找其他block来加入的deepstream pipeline；
所以输入节点如果接了多了block都支持 deepsteam，都会加入到 deepstream的pipeline，如果一个block支持deepstream，但是上一个block不支持，那么这样的block也不加入deepstream的pipeline；

/home/zhongdawei/code/autopipe/backend/workflow2/block_base.py 是block的基类，增加类方法 is_deepstream_supported，说明该block是否支持 deepstream；
增加成员函数 init_deepstream() 将构建deepstream图的操作放在这里，通过调用这个函数，可以构建deepstream的图；
增加成员函数 run_deepstream() 从deepstream的流中fetch执行的结果；进行处理然后return，是下一个block的输入；
增加成员函数 run_batch() is_batch_supported()
对于多rtsp视频流的情况，在构建deepstream pipeline的时候同时构建，在执行block的时候，如果 is_batch_supported() 返回true，那么将输入组合为一个list，输入到 run_batch 函数中；
如果 is_batch_supported() 返回false，那么循环调用block的run方法来处理batch输入；
workflow中对于batch的支持，通过对每个block的执行来实现，可以循环执行一个block的run，再组装为batch，或直接执行一个block的run_batch；


将deepstream流构建好之后一直运行，block中流中fetch需要的信息；
  如果该block的下游接的都是deepstream中执行的block，那么这个block不需要输出了，因为deepstream中执行的block可以直接从deepstream中拿结果；
  对于在deepstream中的block，如果下游还是deepstream的block，那么这个block的执行直接跳过；如果下游接了非deepstream的block，那么执行 run_deepstream 方法，即从deepstream中fetch对应的信息，然后输出；如果deepstream中的block，下游有deepstream的block，也有非deepstream的block，那么这个block还是要执行run_deepstream方法，输出信息非deepstream的block需要用；

  如果从开始到某个block，都可以走deepstream，那么这部分走deepstream，剩下的部分走run计算；
  某个支持deepstream的block被隔开，也只能走run计算

run返回的都是data_type中定义的类型，或者run_stream 或者 run_batch 返回的都是列表，列表内是data_type中定义的类型；

run_stream 是非阻塞式的，启动deepstream工作流和block执行部分后，不会阻塞；可以通过接口拿输出结果；
如果是视频流的情况；workflow的执行是一个循环，每个block只实例化一次；block实例内可以cache之前的某些状态
workflow执行引擎增加stop函数，执行则终止工作流的执行包括deepstream的部分，安全退出；

实现一个yolo推理的block，对单帧图片推理和run_deepstream都支持；
init中载入了模型，run中通过torch的接口进行推理；
init_deepstream中加入到 deepstream 的 pipeline，run_deepstream 中从deepstream中fetch结果，如果是多路视频流，那么fetch批量的结果；然后转换为 ObjectDetection 类型；
data_type.py 中 ObjectDetection 类型补充实现；

实现一个debug block，对于debug block，is_debug 返回的是true；其他block返回的是false；
debug block接image输入，yolo推理block的输出结果；

对于输入节点的情况，如果输入节点是图像，接了不支持deepstream的block，那么要从deepstream中取解码后的图像并转成Image类型；

## ----------- 测试要求：
通过构造json数据进行测试，构造的json数据保存到test文件夹下，测试可复现；对完整的流程进行测试，确保测试正常；
yolo推理需要的内容下载到 test/yolo 目录下；
测试包含模型推理block的workflow，单图推理的执行和多rtsp视频流输入的执行，保证执行正常；
将测试用例运行指令，自定义block的教程都加到 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/v3/dev.md 中；


