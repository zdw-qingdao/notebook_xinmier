

  数据：方松
  自动标注：刘赞
  模型训练：华煜
  前端：王阳

1，inference 结果放在模型路径下；
  这样对于没用的测试模型可以一起删除；
  进行annotation通过单独的方式

2，module design：
  1，数据部分：
    输入：视频 + config文件
    输出：入库的数据；
    1，先进行数据入库操作，meta.json中记录预处理的版本；
    2，创建多个工厂的多个数据，一共10个即可；

  2，模型部分 python通过起进程来起训练任务；
    1，train：
      输入：
        python model_train.py -c config/model_train.yaml
          model_config.json 
          dataset_config.json   需要适配 dataloader 的部分
          other flag 
      输出：
        model 文件夹

    3，inference输入输出：
      输入：
        python model_inference.py -c config/model_inference.yaml
          output: 
            video inference results
            image inference results
            annotation results.
      输出：
        model文件夹下的inference结果；视频和图片
        annotation结果


  3，前端设计：
    1，暂时没必要：配置文件中，如果字段加ui前缀，那么在web界面自动设置；通过字符串或者下拉框设置；
  
  4, 训练时候指定是否要保留训练集和测试集的inference结果；
    单独inference的时候可以指定是否只是运行训练集或测试集；

  方松：
    1，格式转换；
    2，其他格式的数据；

2，临时的作为demo，wangyang进行长期开发，保证质量，运行效率
  1, 先开发一版；后续再开发一版；


  先看哪里指定了类别；首先搞清楚类别定义是在哪里；
  1，训练数据annotation只有一个类别；所以训练得到的模型只有一个类别；
    inference也就只有一个类别，得到的annotation也就只有一个类别；
    手动标注在这个基础上也就只有一个类别

1，commit合入操作
  1，数据格式的问题，不通过创建软链接的方式，通过dataloader的方式；
    通过修改 dataloader 来实现；

后端的问题，自定义dataloader，单卡多卡的问题；

1，标注tag存储设计：tag存放在label.txt 中，这样并行标注不会出现问题，比较容易设计；
  检索的部分单独通过数据库进行；以本地数据为主，数据库从本地进行同步；
  支持某个项目重建数据库或所有项目重建数据库；

qingxing：
  图像去重；  
  1，去重方法，目前先去掉重复度很高的；参考 data_filter.py 中的去重方法 
  2，去重图片列表与可视化
    参考图，去重图；通过生成链接的形式；然后进行人工复核，复核之后判断哪些需要删掉
  3，进行去重，需要同步删除图片和标注文件；

王阳：
  1，同步前端需求和时间节点；
    1，部署；
    2，标注功能优化；
    3，数据库 与 标签检索设计；
    4，数据库 与 标签检索实现；

带tag的混合训练方式：
  图片tag过滤或指定采样权重
  标注框tag过滤或指定训练loss

2，去重的部分；实现；这个先我来实现；

1，华煜开发：
  1，数据过滤通过get_label，cache中加入tag信息，并支持进行过滤；cache是过滤前的内容；
  2，tag过滤，通过 get_label
  3，数据频次，通过 dataloader WeightedRandomSampler指定频次；
  4, tag loss 设定，通过修改loss function；
  
cache的问题：
  1，生成一个指定的cache文件，放到 tmp 中，名称增加一个 hash 值，判断这个 hash 值的cache文件是否存在；
  2， get_label 可以进行box tag的过滤；作为一个后处理；
  3， 在 collect_images 里进行train.txt图像的操作；需要先处理cache文件的问题；
    val.txt 也进行同样的处理，val 默认工作台的权重是1；
  4，使用一个 cache 文件来读取label，判断这个cache文件是否发生变化，需要处理列表的问题；


怎么评测：
  1，原来训练的模型
  2，通过tag分类训练的模型；
  测试集是tag分类后的数据；

3，inference结果在模型界面查看，查看video和image结果；

1, 单独跑测试集
  测试结果放到model下；可以在模型结果页面显示；
  修改model_train 文件，直接让claude写；

1，创建数据集修改：
  1，批量选择工作台
  2，指定标签权重
  3，百分比指定index
  4，指定置信度阈值


2，对比方法：
  指定数据的tag：
    看之前的模型在 inference 的效果
    看用新tag训练的模型在 inference 上的效果；

  目前还缺什么：
    1，huayu：dataloader
    2，批量标注的结果；


待测试内容：
  1，测试不同大小的模型的效果对比，形成测试报告；
    不同尺寸的yolo模型，现在的训练数据集和测试数据集；
    不同尺寸的yolo模型，过滤后的训练数据集和测试数据集；
  2，测试不同的训练数据集，过滤前和过滤后，在同样的测试数据集上的对比，形成测试报告；

测试报告内容：
  1，测试集指标
  2，测试集结果分析；

发版报告，对应发版流程：
  针对工作台 / 针对工作区域  分别发版，因为训的不是同样的模型：
    1，数据变化，怎么划分训练集和测试集；

    2，数据变化前后的模型结果对比，在训练集和测试集的对比结果；证明数据变化代码的增益；
    
    3，不同尺寸的yolo模型的训练结果和对应的评测结果；
  
特定场景交付：
  1，选择合适的发版模型
  2，选择合适的训练数据，和新增的标注数据混合训练，得到交付模型；

1, 创建自定义任务，选择数据集，指定运行脚本，指定运行参数；

0, sync with qingxin
  1，去重部分脚本加入到自定义任务中；可以设置是删除还是打tag；打tag可以是统一的方式来打；一定会输出删除信息 
    1，判断删除文件
      1，是否载入已有文件夹
        1，载入已有的文件夹
        2，计算删除列表
      2，输出汇总信息
      3，执行操作；
        1，执行删除操作
        2，打tag
        3，生成文件夹，如果这个文件夹存在，那么跳过；

    1, 设计参数形式，然后qingxin进行适配；
    2, 服务器进行测试；

    1，参数形式设计，直接给参数文件；
      1，处理数据
      2，是否载入已有文件夹
      3，已有文件夹路径
      4，是否执行删除操作
      5，是否生成tag，生成的tag是什么，针对哪个标注版本生成；是否加入该标注版本中，还是创建新版本的标注；
      6，是否生成文件夹；
      7，去重方法是什么
      8，去重参数是什么；

    {
      "type": "data_process",
      "task_config": {
        "data_path_list": [
          "daming/12344",
          "daming/test123",
          "daming/tets1111111",
          "daming/workstationA_0",
          "daming/workstationA_1"
        ],
        "params": { 
          "cache_flag": "cal_no_cache" / "cal_save_cache" / "load_cache",
          "cache_folder_path": "/mnt/data1/data_server/tmp/dup_image/test1",
          "del_flag": 0,
          "generate_tag": 0,
          "parent_annotation_version": "",
          "annotation_name": "",
          "tag_name": "",
          "dup_method": "",
          "dup_param": ""
        }
      },
      "script": "task_test.py"
    }

1, sync with haowei;
  图像标签 工作台 生成图片；
  对整个person_all 的数据进行打签

2, sync with shiziping and huayu
  1，data;
  2，模型训练；




