

数据打tag前端与后端开发，手动进行打tag；

大模型自动打tag测试；

ultralytics yolo模型训练对打tag数据的适配；
  1，数据过滤通过get_label，cache中加入tag信息，并支持进行过滤；cache是过滤前的内容；
  2，数据频次，通过 dataloader WeightedRandomSampler指定频次；
  3，tag过滤，通过 get_label
  4, tag loss 设定，通过修改loss function；

5，进行数据标注；看怎么分配标注任务，进行批量标注；
  先组内分工；

6, haowei liuzan: 通过大模型进行打tag，进行批量标注；person_all2 数据；

5, 方松脚本放到 repo 中；

6，基于数据平台进行数据清洗
  1, 清新：去掉完全重复的图片
  2，大模型打tag结果；对比人工打的结果；
  1，dataloader进行适配；
  0，tag存放的形式；标注可以修改标签；
    标注审查不需要不同的版本，作为不同的标注版本即可；  
    可以指定删除哪些tag，添加哪些tag

5 支持单独跑validation；模型对比的查看方式；
  怎么对比inference的结果；

1，sync with wangyang, web_test

  6，迁移优先级低，目前没有明显收益，后续有需求这个优先级再提上来；
    目前先用 web_test 的版本，最近新功能也开发较多，目前这个版本可以满足需求；

  5，设计现场人员使用的版本；

  4，数据库设计，目的和设计方式；针对可能出现的问题进行的设计，数据量多和使用人数多，会出现什么问题？
    8，定时或手动触发重建某个项目的数据库，用于检索功能；
    目的是什么；针对的场景是什么；

  3，文件权限的问题，怎么自动判断并解决；

  2, 定时增量备份；在web_test 上新增；
    通过一个表格显示，最近10次的结果；执行时间，更新文件数量，执行花费时间；

  1，使用文档; 熟悉整个过程；
    前端使用
    对应的后端

2, sync:
  1, platform现状
    1，saip平台的问题和功能，现场人员使用的版本
    2，其他类型的数据；

  2，数据整理，数据自动打签，数据分类
    高度重复数据的去重，重复数据的打签；

  3，模型测试

  4，模型训练发版流程
    不同的预训练模型
  
  5，人员安排
    数据分类方法，清洗方法，要做哪些实验；发版过程通过文档或

  6，时间节点，月底
    1，平台研发版本和现场使用版本；
    2，完成一版数据清洗与整理，完成一版yolo模型的测试；
    3，从现在的项目出发，看清洗数据的效果；看新版数据下模型的效果；
    4，特征点标注；
    5，推进研发使用新版工具；

3, sync with jinzhi linli wangyang;
  1, following:
    数据侧：
      1, all data migration
      2, data cleaning
    模型侧：
      1, 算法集中管理与评测
    平台：
      对其他数据格式的支持；对其他任务的支持；
      检索功能，多人使用；
      现场人员使用的版本；

1, sync with linli about platform design and development;
  with wangyang;
  先和王阳分工；

1，新代码入库的具体流程，模板库的使用； 这部分交给石子平，然后推进数据入库和代码入库；
  1，新建代码仓库，复制模板；
  2，代码中，输入是什么，输出是什么，定义其中的部分；

2，创建代码配置文件，代码配置文件中增加conda环境名称；
3，运行根据指定的conda环境来运行 run.py 文件；
  code_config 中可能含有 conda_env 的配置，如果有的话，那么使用指定的 conda_env 的python解释器；

1，人员安排
  1，平台：现场人员使用的版本 wangyang linli
    多机训练的问题；    
    多硬盘的问题；
  2，训练：基于清洗后的数据进行训练测试 huayu shiziping；两人合作还是只有一人；
  3，shiziping：可以基于现有的系统对行为类任务进行测试；
  3，数据：saip数据入库，相关项目入库 fangsong 
  4，代码：代码统一管理；并分别进行推理测试，记录测试结果；each one;
  5, 数据：shiziping，数据入库；
  6，项目：每个项目的数据和过程进行入库； quchen chengzhen huayu
  7，售前工具：liuzan
  8，大模型打签测试，代码合入：liuzan
  9，haowei：deepedge 代码流程，进行重构；
  精力在主线执行上；

3，文档与培训，将使用的代码都接入到平台；
  1，segmentation chengzhen
  2，yolo pose quchen，不同的yolo pose的版本，所有测试的版本；相关的数据也进行接入；
  3，liuzan llm relative
  4，haowei llm relative
  5，sam3，shiziping 加入平台
  6，yoloe 接入平台；

  培训过程现场演示，现场新建一个项目，然后进行整个过程；  

2，当前项目的数据与代码，接入平台，训练结果记录；
  1, huayu
  2，chengzhen
  3，quchen

2，数据去重测试效果，进行去重tag操作；
  先后端运行，然后前端运行；


1，培训数据平台的使用，项目过程入库，相关代码入库；要录制会议视频；
  1，数据入库方式
    通过前端
    通过后端直接操作，按照指定的格式，需要修改文件权限，sudo chmod 777 -R *
  2，代码入库方式
    1，配置conda环境
    2，新建代码仓库，基于代码模板编写；增加 train inference 和结果保存的部分；
    3，新建code_config
    4, 根据运行指令来测试
    5，测试完成后更新git代码，更新code_config 的commit id；
    任务管理界面除了 model_run 的指令，还要显示 run.py 的指令；显示在log中即可；可以新加一个按钮，显示run指令，便于debug；
  4，数据处理培训；
  3，评测方式；
  4，项目记录文档，要包含使用的数据，代码，和评测结果，链接到数据平台；


0，方松：数据去重进行操作；
1，liuzan：售前工具，需要进一步优化；

2，shiziping：
  1，更多数据集入库
  2，先找出来评测集，先找一个版本；with fangsong

3，haowei：
  总结当前大模型打tag的效果；

1, wangyang：当前修改和后续计划；
  1，在另一台服务器上进行部署；数据挂载，代码挂载，这样只需要更新一个地方；使用完全一致，可以用更多的卡；
    文件权限；
  2，现场人员使用的版本；
  3，目前是针对单块硬盘，适配多块硬盘的情况；
    要看所有 server_info 中路径的使用，所有的使用有哪些，后续多块硬盘适配怎么设计；
  4，数据库，要解决什么问题；

曲晨，耀能项目；

刘赞：大模型finetune测试；

chengzhen:
  https://bitbucket.org/simmir-software/sound_detect/src/main/
  1，部署
  2，增加的设计，指定一部分数据作为训练，一部分数据作为测试；
  3，其他语音数据的测试；


平台bug：
  1，数据处理任务，在全部运行结束后log才会写入；
  2，时间统计不对；

1, 平台使用文档，完成后进行培训，接入到模型；
  https://alidocs.dingtalk.com/i/nodes/X6GRezwJlY93kXy7Uga2OwBy8dqbropQ

2，自动打tag可靠性检查

1, 数据集比例的问题，因为图片数量少导致的，不影响使用；

4，huayu：
  验证新的数据载入方式是没问题的，启动训练

1，huayu：将之前的公开数据集的数据也加入到当前的平台中；

1，音频信息处理的问题，程振；

2，qingxin：图片去重脚本优化时间；通过hash的方法；
  这个优先级不高；

0，数据处理任务log显示的问题查看；可以通过一个任务进行测试；王阳解决；

2，数据进行检查，增加一个版本的标注，方松来进行；评估下需要多少人，然后开始搞

liuzan qingxin: finetune sam3 / 大模型；


mlp方法：
[Train Set]
  TP=146  FP=0  FN=0  TN=292
  Accuracy:  1.0000 (100.00%)
  Precision: 1.0000 (100.00%)
  Recall:    1.0000 (100.00%)

[Test Set]
  TP=35  FP=7  FN=2  TN=67
  Accuracy:  0.9189 (91.89%)
  Precision: 0.8333 (83.33%)
  Recall:    0.9459 (94.59%)

互信息方法:
[Train Set]
  TP=104  FP=24  FN=42  TN=268
  Accuracy:  0.8493 (84.93%)
  Precision: 0.8125 (81.25%)
  Recall:    0.7123 (71.23%)
  F1:        0.7591 (75.91%)

Computing test set scores...

[Test Set]
  TP=26  FP=7  FN=11  TN=67
  Accuracy:  0.8378 (83.78%)
  Precision: 0.7879 (78.79%)
  Recall:    0.7027 (70.27%)
  F1:        0.7429 (74.29%)

python inference.py --method yamnet --model ../models/yamnet/6.pt --audio ../sound/june23_20.m4a --threshold 0.5

wangyang:
  3，优先部署服务器，时间的问题可以慢慢优化；


1，优先解决语音的问题；下午5点进行同步；宋博+王冉，然后出一个当前版本的方法；
0, 62.9 文件夹挂载，不稳定？

1, 启动镜像，启动程序，看能否正常运行，如果可以的话，docker 传输，作为第一个版本

3，内存问题，怎么进行优化；可以先用8张卡一块训练；任务并行来训练；为什么不用8张卡；

2，dedup数据的问题，查看哪些数据是缺少 dedup 的；
是否执行过删除操作，没有，本来就没有这个文件夹；

1，平台培训，项目过程平台化；
  1，本地测试，怎么在自己的账号进行测试；
    1，本地测试的时候，也通过 model_run 来启动；
      指定自己的代码路径
  2，本地测试完成后，加入到平台中；
  2，进行培训；
  当前的代码入库方式，后续也要教会其他人；
  进行培训，后端部分huayu来维护；
  前端部分王阳；
  当前的项目内容加入到现在的数据平台中；

代码接入：
  5，quchen liuzan：
    yoloe sam3 代码接入到数据平台；

  3，大模型打签和打框的代码：liuzan haowei
    代码 接入到数据平台；

6，模型finetune：
  liuzan + qingxin
  1，sam3 yoloe 评测与finetune；将训练过程也接入平台；
    sam3 yoloe finetune 或者 训练 yolo26x 来作为 deepedge 的标注模型；
  2，调研一下视频reasoning的模型有哪些，怎么用qwen之类的大模型对视频进行解释；怎么finetune大模型；
    平台
    数据
    部署模型 标注模型
    yolo yoloe sam3 qwen for tag;

3, project optimization；项目的block项是什么；
  chengzhen
  quchen
  huayu  
  项目部分：
    想一想当前的项目的数据 训练 评测，对数据平台有什么需求；
    怎么通过平台和pipeline来加快项目的迭代构成；
    增强模型的评测能力，减少现场问题；
    后续大模型的微调和评测，行为分析类的任务也会统一在平台上进行；

    然后看项目具体的问题，从项目出来看怎么从平台来系统解决；
      人体关键点的标注，通过yolo-pose跑了之后，再人工调整；
  后续通过平台来跟踪项目进展；

progress：
  1，厦门项目：声音检测项目；声音事件检测训练与评测平台；后续可以快速验证这样的问题
  2，耀能项目：现场沟通看客服能接受什么，然后采集数据来测试；
  3，售前camera验证工具
  4，数据清洗与打tag，数据分类 模型训练第一版；正在训练；
  5，推进研发侧项目进展平台化；

行为类模型发版；
  1，通过少量数据进行finetune
  2，通过finetune后的模型进行标注
  3，训练

2，alarm 数据，文件不对的问题；不对的原因是什么；跑了一个这个文件夹，测试的时候只跑了一半；导致后续跑的时候直接跳过了

3，戴浩慰那有一个 RK3588+1828协处理器的开发板，1828可以支持跑一个3B的大模型。



磁盘冷缓存。/mnt/data1/data_server/ 目录下的文件不在内存缓存中时，每次 os.path.isfile() 和 open() 都要等磁盘寻道。get_image_files() 需要 listdir 并扫描300张图片文件名，加上600个标签文件的 isfile 检查 — 冷缓存下每次磁盘访问都是几十到几百毫秒。
这是机械硬盘在冷缓存下读取大量小文件的典型表现。热缓存下 44ms，冷缓存下 60+ 秒。
解决方案：不需要改脚本逻辑，问题在磁盘。目前前端已经改成了先显示命令再执行，用户能看到进度。如果想从根本上加速，可以：
把 collections 数据放 SSD — 最有效
预热缓存 — 启动后台任务定期 find 一遍保持文件在内存缓存中
跳过 get_image_files — 直接遍历 labels 目录而不是 images 目录，减少一半磁盘访问

1，音频任务：训练一个新的模型；然后提供给他们


1，sync with 王阳
  找到原因了。wangyang 在跑 Ultralytics DDP 训练，光前两个进程就各占 ~10GB RSS，后面还有十几个每个 ~3.4GB。这些训练进程不断分配释放内存，Linux 内核为了给它们腾空间会不断驱逐页面缓存（buff/cache）。
  所以你的文件刚被访问过放入缓存，过一会就被训练进程挤掉了，下次访问又要从 HDD 读，就又慢了。
  总结：1TB 内存虽然大，但 DDP 训练进程吃掉了大量内存，页面缓存不断被挤出，导致小文件的随机读取反复回到 HDD。这不是脚本的问题，是内存竞争。

  1，文件读取问题的解决方法：
    1, 数据读取上有问题吗；
    2，标注对比的问题的查看；
      触发磁盘等待；
  用ssd来测试；

售前工具优化，目前的使用问题：
  1，用户登录界面
  2，多用户同时使用的问题
  3，除了人的显示比例，增加像素区域的判断；
  多个人使用的问题，为什么点不到指定的位置；

1，sound_detect 代码合入，传到62.2 直接commit然后push即可；
3，测试后更新文档；同步现场


4，数量不对问题的查看，查看所有数量不对的问题；
  标注数量不同的
  http://122.225.62.2:5173/collections/person_all_2_eval/group_0010__caterpillar_0
  /mnt/data1/data_server/collections/person_all_2_eval/group_0010__caterpillar_0/annotations/det_manual_0_tag_qwen_checked/meta.json
  3, 石子平进行了一些数量抽取，数量是不一样的，meta.json 没写对，问题不大；
    /mnt/data1/data_server/collections/person_all_2/group_0010__caterpillar_0
    /mnt/data1/data_server/collections/person_all_2_eval/group_0010__caterpillar_0

2，模型训练的bug查看
  1，不行就通过构建数据集的方式；
    先通过这样的方式来进行训练；新建一套代码；
    方式1：当前代码的bug；
    目前来看没有明显debug；

1，alarm 数据完成去重；

1，ssd 数据迁移；

测试：
  1.5个研发，2-3周时间；可以先用一个类似的麦克风来测试，最后还是需要做出来实际的硬件来测；
现场实验：
  1个研发出差到现场，2周时间；
  
1, group_0002__alarm_camera_0 还是需要重新进行数据处理；还是存在这个问题；目前已解决；
  scp -r /mnt/data1/data_server0/collections/person_all_2/group_0002__alarm_camera_0/annotations/det_manual_0_tag_qwen_dedup admin1@192.168.200.20:/mnt/data1/data_server/collections/person_all_2/group_0002__alarm_camera_0/annotations

2，sync with liang，厦门项目后续安排；

2，haowei
  1，打签测试不同的方法，形成一个指标
  2，sam3 sft，后续集成进deepedge；

1，程振 曲晨 项目内容加到数据平台；1周时间；
  曲晨调研声音识别的方法，本地进行测试；
  程振接一部分方松的工作；数据整理；

1, 数据整理与标注调整
2，声音识别调研
3，项目内容加到数据平台；
4，不同打签方法的评测形成指标
5，sam3 sft 测试，后续集成进deepedge；

1，硬盘速度的问题：
  3，同步石子平 huayu，开始训练任务，要填写文档：
    https://alidocs.dingtalk.com/i/nodes/QBnd5ExVEabrKp1wtgLd641DVyeZqMmz
  2，62.2 同样起服务，通过文件夹挂载的方式；
  1, 62.9 上起服务，将 tmp 和 models 放到其他路径下；

1，quchen, 语音项目；
  1，当前情况；
  2，进行测试
    1，搭建测试系统；
    2，进行评估；

3，qingxin：数据去重脚本合入；直接在数据平台上合入；通过登录wangyang用户，临时的测试方法；

5，deepedge代码跟进，后续通过finetune的大模型或者sam3来进行打签；

4，模型评测华煜；
  2, 当前的实验结论；
  1，自动根据上次的结果继续跑；

3，开源数据训练情况的对比；目前开源数据的训练对结果起到了负面效果，因为存在大量误标；可以通过大模型打签来优化；


2，sam3打签的数据需要进行过滤，需要进行置信度的过滤，sync with 石子平 
  看sam3的输出，有什么过滤的方式；

1，对其他格式的数据的支持；数据格式设计；
  1，通过coco json来存储segmentation图片，载入的时候可以进行cache；
  2，keypoints也通过coco json
  3，后续 detection 也通过coco json
  4，通过 coco json 统一来存储所有类型的数据；
    1，将所有的数据通过 coco json 统一存放；
  视频数据存放格式：
    1，clip文件
    2，对应的parquet文件；sheet

开源数据打签的问题 haowei；
  1，重新用sam3打，保留置信度
  2，创建新版本标注的时候，进行置信度过滤，然后对这个版本的数据进行打签；有空闲的卡可以先跑着；
  3, 可以测试一下如果用api打签的话，需要的时间和费用，如果很便宜的话可以考虑用api来打

模型结果查看，目前看比较正常

1，准备正确的示例数据
  1，segmentation：
    chengzhen
  2，keypoint
    quchen
  3，detection
    fangsong，数据转换的脚本，先转换一个数据来看；

1, 批量修改 meta.json 中的 type；

1，当前yolo的模型训练： @huayu
  1，训练结果的保存；修改为始终按照同样的方式保存；
  2，随时可以resume，继续训练；点开始运行自动resume；自动判断是否已有weight；通过修改配置文件可以修改配置；
    自动判断是否已有训练结果；
  3，yolo训练数据读取适配json文件的格式
  4，自动标注，生成的结果修改为json的形式；可以通过参数设置，默认是保存为json的格式；
  

1, sync
  1，现场人员使用的版本设计；  目前看优先级不高；
    1，用户登录
    2，新建项目 / 选择已有项目，
      用户可见的项目范围是设定的，自己添加的默认是可见的；
    3，数据上传； 
      除了当前的视频数据上传外：可以支持标注后的数据上传；
                    做一个标注工具，在断网的情况下可以进行标注；可以是纯html的标注工具；
    4，使用已有模型进行自动标注； 使用比较大的模型；
    5，进行人工标注调整，调整少部分数据；
    6，创建数据集；可以只选择当前数据或包含其他数据；
    7，进行标注模型训练； 训练一个比较大的模型；
    8，使用标注模型进行自动标注，
    9，编辑自动标注效果；
    10，创建新的数据集；
    11，进行部署模型训练；
    12，进行模型部署； 

  2，不同格式的标注的可视化与编辑

  3，新建训练任务；
    增加 epoch 设置，默认是50，将 epoch 设置和 resume 参数都放到 json 文件中；

0，简单做一个现场用的版本；

1，sync jinzhi zhaowei，web端用户的平台是否需要；
  目前研发用版本屏蔽一部分就是现场用版本，当前是这样，但是真正上线需要经过现场测试不同情况的使用；
  收益是：
    1，不需要安装客户端
    2，开发迭代快
    3，和研发数据平台后端一致，研发可以快速查看数据，标注，标注人进行的调整；
    3, 目前版本中saip没有的功能：
      1，有标注版本的管理；可以监控人进行标注调整的部分
      3，功能简化；
    4，目前版本中没有而saip有的功能：
      1，视频编辑功能；
  缺点：
    1，现场人员需要重新学习；

  先不着急，模拟一份 roboflow；先做设计，然后从终极方案出发；做整套的设计；


0，roboflow， overview ai
  数据回流
    把不确定样本、有争议样本和误报样本返回训练集，形成第一版闭环
  部署管理
  端侧推理
  1，研发测试
  2，现场闭环

  支持web，也支持api；

  方案设计，开发时间和人员预期；

  自动标注，可以针对单张图片使用不同的方法；
    启动自动标注服务，标注单证，关闭某个自动标注服务；
    可以启动多个自动标注服务；

  roboflow的所有功能，架构设计；模仿一份，适配端侧的情况；需要评估时间和人力；

2，sync，sft的1w数据周五前才能标好；
  周三可以先起一个训练来看；先用比较少的sft的数据；
  先判断目前哪个模型的效果最好，然后基于这个模型通过sft的数据进行训练；

1，华煜 曲晨项目，程振项目，通过roboflow平台来实现，测试；

0，低代码平台；sync
  1，架构设计
  2，分工与时间预期；

1，内存kill的问题；先不影响网站后端；
1, 完整试用roboflow

暂时不需要了，后续通过一站式平台来解决这些问题；
  svap的了解；后续开发整体的替代版本即可；
  deepedge的代码和运行方法；
  后处理代码的情况

1，确定数据格式的设计
0，曲晨文档更新后发给赵伟；
1, 售前工具部署与交付，文档优化


0，数据清洗，第一版模型，评测还在进行中；
1，售前工具
2，现场用版本的简单开发，后续不使用这个方案；
3，roboflow测试与后续的设计；目前基本完成数据和训练部分的设计；

2, 相机安装位置评估工具，然后直接后端更新即可；
  1，里面再加一个框，相机能够看到的区域；
  2，可见比例不太对；完善这个计算；

1, 行为类文档更新, quchen
  1，怎么看训练曲线；训练多少轮；
  2，300张，

3，每个人设定自己的端口，个人测试不影响其他人使用；使用的端口记录到文档中；
  在每个人自己的路径下创建文件，写入端口号，每个人的运行不影响他人使用；
2，代码模块化，防止干扰；  
1，代码仓库同步设计文档，开发过程可回溯；设计文档包含 设计prompt + 完整的设计文档；

0，根据周报同步每个人的进度；
  用新训练的模型进行自动标注，看是否这个模型会有更好的效果；
  4，训练不同大小的yolo模型，对比评测；
  3，查看当前评测的效果，评测的部分如果对前端有什么需求，可以填到需求表中；
  2，启动后训练
  1，sft图片继续标注；

shiziping：
  1，design experiment
  2，evaluation
  3，test other algorithm
  4，sam3 and other sft；


任务分配：
  进展跟踪表，将prompt与相关设计进行记录；
  1，docker，环境配置；        
  2，数据库与存储，数据格式              shiziping
      所有的接口定义；
      多存储桶的情况；怎么在数据的层面进行适配；
      数据迁移的脚本；

  3，界面前端，标注界面实现；             wangyang linli
    1，标注首先设置选择不同的标注版本，然后每个版本都使用roboflow的逻辑；

  4，模型训练与推理统一接口；支持在线运行；热启动；   huayu
  5，任务管理与调度；多机训练系统          haowei
  6，workflow后端设计与实现；            sufeng
  7，workflow前端；                    liuyu
  8, agent                            haiyang

2，roboflow 项目测试； 后续可以正式开始开发； quchen chengzhen;

1，roboflow 拆解； zdw

1，数据引擎，有一套工具链，高效的工具链； shiziping;

2, 通过标志位定义使用本地存储还是对象存储；
1，路径的设计；

1，测试两种方式，对象存储和本地存储；验证运行正常；
  1, 当前本地运行：使用挂载文件夹的形式；
  2，后续本地拓展：采用对象存储；
  3，后续到云上之后，通过挂载文件夹的形式，直接挂载对象存储的存储桶；

1，个人端口自定义文件，里面的文件要通过读总的配置文件；
0，数据库的内容是否会覆盖；确认数据库中的内容是持久存在的；

1，其他用户使用，数据库，docker，存储，文件权限的问题；
  1, 如果要操作online的，通过我的账号；
  2，否则，使用自己的账号，路径，端口；

1，数据库的可视化；通过vscode插件或其他的方式都可以；

liuzan:
  相机检测工具的优化：
    1，人员再加个矩形检测框
    2,再补充个人员姿态调整的，比如伸手的，蹲下的

huayu：模型训练
shiziping：开源数据
fangsong：数据标注
haowei：deepedge



11:00 sync with jinzhi liuyu sufeng wangyang linli
  前端 wangyang linli
  多机 liuyu
  workflow zdw liuyu


数据平台2.0分工：
  5，排期，workflow的部分，一周摸清楚，一周来实现；初步暂定；
  5，共同开发方式
  4，人员分工上
  3，框架选择
  2，pipeline上，实现pipeline；
  1, 使用上 copy roboflow

11，workflow的实现；
10，model train的实现；需要先进行设计，需要完善的支持多机的机制；
9，标注的部分实现，通过一套prompt直接实现全部；
8, 多机任务管理调度；
  sufeng
7，workflow， 支持数据回流的workflow；
  liuyu
  zdw
  可以是端侧的workflow，也可以是加服务器的workflow；
6，yolo模型训练适配，huayu；
5，模型接口定义与管理，zdw
4，标注部分实现，wangyang；

3，部署上的难度
2，不支持的部分，有什么缺点；
1，模型推理的部分
0，对比的方案

低代码平台调研与选型;
  1，node-red 和除了 roboflow inference外的方案对比；
    1，已有开发经验，已有很多开发的block
    2，其他方案没有明显优势
    3，node-red 适合现场任务，对数据输入，结果输出，运行效率的支持比较好；
  2，node-red 和 roboflow inference 对比
    1，roboflow inference 对模型推理适配更好，node-red需要单独写模型推理服务；
    2，roboflow inference 通过python实现，可用库更丰富，自定义block更容易；

1，任务调度调研与选型；
  1，任务执行单元是什么，一段python代码，可能需要占用gpu资源，如果需要占用gpu资源，那么指定卡的数量，对于指定的卡
  0，先实现简单版本，先通过简单版本运行，后续通过同样的接口，扩展为任务调度的版本；

0，怎么定义一个任务，需要哪些输入参数
  执行的函数，指定的参数；
  使用ray

任务调度：ray
workflow：roboflow inference

任务挂起与继续执行，需要通过checkout point载入的逻辑来自己实现；

1，任务管理的选型与代码结构设计；后续sufeng进行实现；

1，数据平台的修改，石子平来直接改即可；通过自定义端口来测试，没问题之后王阳来重新发布即可；

1，roboflow inference使用的pipeline；迁移使用的方法；

1，workflow 的测试方式；
  1，代码都放到 /home/zhongdawei/code/autopipe/backend/workflow 中；
    通过什么样的方式来开发和测试；

2, workflow 的部分进行开发；实现初版的workflow；进行测试，后续workflow在这个基础上进行调整；

liuyu 基于roboflow inference的简化版本来进行开发；zdw进行自研测试；

0，根据 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/dev_v1.md 来看执行过程；
  1，代码过一遍
  2，测试用例运行
  3，代码再过一遍

3，售前工具优化；

2，安全类模型
  1，在评测集性能有一定提升，准确率和召回率；
    做了什么事情：
      1，加入开源数据；
      2，数据清洗，目前对准确率有明显提高，对召回率有轻微下降；
  2，对美国现场的数据，对比0605模型，不会出现误报；
  3，发现了更多数据问题；需要通过自动+手动的方式进行进一步清洗，然后模型能力应该会进一步提升；
    同时训练的大尺寸yolo模型可以加入deepedge，理想的话可以取消手工标注过程；
    1, 用sam3运行得到标注
    2，对比人工的结果，然后人工来批量调整；
    3，finetune sam3 和 yolox

1, saip2.0技术选型，架构设计；初版已实现一部分；预计还需要3-4个周实现除agent外的roboflow复刻版本；
  1，存储与数据库设计，应对大容量情况；
  2，workflow;
  3，任务调度;
  4，初版前端；

0，先支持yolo模型的训练，先不考虑其他模型的训练；

0，任务调度，先实现一个简单版本；
  基于大模型实现一个版本；先基于当前的设计文档实现一个版本；
  先把这个版本用起来，本身就是中间层；先使用这个版本；
  目前不需要所有的函数使用这套，只需要模型训练的部分使用这个即可；
  其他的部分通过 fastapi和多进程即可；
  可以通过中间层先实现一个简单的版本；目前的任务调度可以通过来的时间顺序实现；

liuyu来考虑实现roboflow inference的版本，前端也直接实现，后续也可以屏蔽；

1，task执行的部分，代码过一遍，测试过一遍；后续sufeng来维护；
  2，task中设置优先级的设置，这部分先不实现，可以sufeng来实现；
  0，任务依赖的部分可以保留

1，测试效果
  python3 migrate.py --data-path /mnt/data1/data_server/collections/person_all_2_sft/group_0019__dm_0/  --annotation-version det_manual_0_tag_qwen_checked --workspace 11 --project 1 --user admin

0，进行批量迁移，然后测试效果，训练模型后看评测集指标；
  python3 migrate.py --data-folder-path /mnt/data1/data_server/collections/person_all_2/ \
        --annotation-version det_manual_0_tag_qwen_dedup \
        --workspace 11 --project person_all_2 --user admin

1，当前数据库中对于hash重复图片的处理，先忽略这部分，只保留hash值，不进行hash去重；
1，数据迁移的脚本，person_all_2 进行数据迁移；
  目前存在的一个问题，对于一个数据不能执行两次迁移，如果执行两次，图片还是一份，db的部分会再做一套；

不需要生成cache，先简化这个问题，直接从数据库读取即可；目前不需要考虑太远，后续出现问题再进行针对性优化；

docker 前端 环境部署 现场部署：huzejin, wangyang linli 配合，yinsheng配合；
workflow引擎 任务调度：haiyang，sufeng liuyu 配合
模型接口，模型训练：haowei，huayu配合


下周任务：
  1，华煜：根据新的接口，适配yolo训练
  2，huzejin wangyang linli：
    1，多人标注管理
    2，模型训练，模型结果的展示部分
    3，现场标注工具的设计与实现；
    4，用户名称，workspace名称重复的问题；workspace给其他用户添加权限的操作
    5，数据库 redis部分docker拆解，部署与测试方式
    6，workflow前段实现
  3，sufeng：任务调度完成所有功能
  4，liuyu：
    workflow部分搞清楚，目前roboflow inference一共有哪些block
    将模型推理的部分加入到workflow中；
    通过ray运行workflow，进行测试，写完善的测试；
  5, zdw: 现场运行的设计，选择一个workflow执行
    1，获取所有相机，对每个相机指定一个workflow执行；通过ray进行任务调度，资源管理；

需要做的是定义接口，定义接口后，接口的上游和下游也就有了目标，责任人有了目标就有了验收标准；基于验收标注可以push，查看进度；
这样人力可以组织；

1，需要定义好接口，这周需要开发好；我只把接口定义好；整理到钉钉文档；拉群 autopipe2.0小分队；
  做这套系统的目的
  现状
  分工：
    1，huzejin：
      0, docker环境配置设计与优化了
      1，模型训练的前端，包括相关可视化；
      2，前段通过模型结果json文件来显示所有需要显示的内容；
      3，workflow前端，基于中间层；
      现场标注设计与实现
    2，huayu：
      1，模型训练的后端，需要的结果保存到指定的位置；
      2，前端需要展示的信息通过json文件说明；
      需要独立测试
    3，sufeng：
      ray engine，需要独立测试
    4，linli liuyu：
      workflow engine，需要独立测试；
      1，详细阅读代码，理解每一部分
      2，详细的流程图和文档，说明当前的workflow的完整逻辑过程；
      3，进行测试，验证正常
      4，对比 roboflow inference中缺少的部分，这些缺少的部分功能是什么，哪些我们可以加上；在当前的基础上逐步添加；
      5，当前有哪些blocks，解释每一个的实现逻辑，roboflow inference中所有的迁移过来；

    6，wangyang：
      现场部署页面设计与初版实现
    7，haowei：
      deepedge整理实现逻辑标准化，暴露明确的接口；需要独立测试；
      基于现有的接口定义，数据
      这部分后续再说，直接把deepedge的经验拿过来重新开发即可；
    8，后续 haiyang：
      agent部分设计与实现
  合作开发的方式
    1，docker
    2，设计文档，使用的prompt保存
      1，便于后续调整
      2，后续基于这些内容可以构建知识库，实现agent的部分
    3，接口定义，独立文件夹，独立测试

没必要，有时候也需要使用别人打好的docker：
  便于合作开发
    2，默认使用自己用户名创建路径，需要修改的只有端口；
    1，docker，默认使用自己的用户名创建docker

1，模型训练与推理的接口定义；
2，workflow在原来的基础上修改即可，没必要新起一套；理解原来的部分，在这个基础上修改； 
3，model的部分也要用 basemodel的方法；使用同样的思路和方法，一致的方法比较好；

1，数据接口部分，kind的定义使用；
  /home/zhongdawei/code/autopipe/backend/workflow/block/entities.py
  这里是make sense的；


4，workflow实现，自研版本，先写设计，然后直接大模型直接实现，通过测试验证；通过测试验证和roboflowinference的结果没有性能的不同；
0，workflow执行和ray联动的部分；通过ray的方式执行workflow；
  执行单次和执行多次的情况；
  没必要: 自研workflow引擎设计，简化当前的代码，设计过于繁琐，不够清晰；

deepedge优化： 
1，评测，效果可视化
2，软件测试；

3，断网使用的情况，只有数据标注，标注部分是完全一致的，然后通过上传数据集的方式上传结果；
  数据格式使用数据平台的格式；先支持自有格式；
  先进行这部分的设计，通过大模型进行设计；
  统一的设计方式，最好能直接复用当前的代码，在断网的情况下通过docker启动；顺便解决现场docker启动的问题；

3，模型训练部分完成，进行简单的实现，看能否work，华煜进行测试验证；要保证训练结果是正常的；
7，模型训练的部分,后端需要能够独立完成；
  /home/zhongdawei/code/autopipe/backend/models/base.py
  包括模型推理

5，yolo模型训练的部分
  1，获取数据的接口封装
  2，yolo训练进行适配 @华煜

没必要：
  2, 是否自研workflow引擎
    block类
      预设的block
      自定义block
      需要指定必要输入 可选输入 输出
    基于json的graph构建
    graph执行

没必要，石子平统一生成:
  查看当前的标注版本，sync with haowei；

2，svap的现场推理；视频流的接入，wangyang 来实现视频流接入；

1，模型训练 workflow 任务调度 前端交互
  先进行接口的设计，各部分可以基于接口进行开发；
  视频数据处理
  模型训练
  模型推理
  前端：
    读取当前支持的所有block；
    拖拽式开发；
  workflow的部分先用当前的逻辑；





