

prompt记录：
1, 点开工位的页面后，新增一个按钮 “创建自动标注”，点击按钮后，要指定某个 used_model，used_model 是 models 下的某个文件夹名称;
要指定 device，点击创建后在 tmp 下生成一个config文件，同样通过uuid4保证不重复，config文件中写入model_inference.json 中的字段，其中 code_config pretrained_model 从指定的 models 下模型的config/model_train.json 中找对应的，"data_path_list" 包含当前工位，其他的flag都是false，除了 add_annotation_flag 是 true，device根据设定的值；
生成完这个config后，运行 model_run.py -i -c 生成的config文件 来给这个工位生成标注文件；点开项目的页面后，同样新增一个按钮创建自动标注，逻辑和上面一样，不一样的是 "data_path_list" 中包含该项目的所有工位；

2, 点开工位的页面后，新增一个按钮 “创建手动标注”，点击按钮后，"parent" 为空或选择某个已有的标注版本，点击创建后在annotation下新建一个文件夹，文件夹命名是 manual_x,后边是递增的版本；如果manual模式parent非空，那么把 parent 标注版本下的label全部复制过来；否则创建label文件夹但是先空着；生成 meta.json；点开项目的页面后，同样新增一个按钮创建自动标注，则对项目下每个工位执行上面的逻辑

3, 在任务栏，有新建训练任务和新建推理任务，点开后把“开始训练”和“启动推理”修改为任务创建；创建任务后生成config文件，先不运行，在网页上显示这个任务，同时显示要运行的指定指令，即训练是 python model_run.py -c xxx.json，推理是 python model_run.py -i -c xxx.json ;有一个开始的button，点击之后才会开始运行；然后有一个按钮是查看log，一个按钮是停止运行，一个状态显示是 未运行 / 运行中 / 运行结束；

4，在任务界面，新增一栏入库任务；在项目的数据页面，把数据上传修改为创建入库任务，创建后不直接执行指令，也不进行跳转，停在原界面；这是在入库任务中新增一项，逻辑和训练与推理任务基本相同，在点到任务-入库任务后也需要显示每个入库任务的执行指令，执行状态，执行完成后的执行时间；也有一个按钮查看log；在入库任务栏增加一个按钮是执行全部，则自动依次执行所有未完成的入库任务；
在任务创建后，在入库任务栏，每个任务显示上传百分比，显示上传是否完成；如果上传没完成就执行入库，那么要等待上传完成；
在上传完成后，上传只指示栏要显示上传时间；

执行 model_run.py 时可以通过命令行指定用使的显卡id；
无论有没有指定，将这个信息传给 run.py;run.py中如果指定了某几个显卡，那么使用指定的显卡id，否则使用配置文件中的设置，每一步修改都要显示修改内容并问我是否通过;

在创建标注 训练 推理任务时, 不指定显卡id，而是指定使用显卡数量；
此时生成的config文件中默认设置使用从0开始的卡；

在执行训练和推理任务时，有两种方式：一种是根据当前执行中的任务用了哪些id的显卡，自动分配剩余的显卡，从0-7依次分配；在执行任务时通过命令行参数指定使用哪个显卡；开始执行后也要更新显示的执行指令; 另一种方式是在任务界面对要执行的任务手动指定使用哪几个显卡，0-7 8张卡可以选择；在执行任务时同样要更新显示的执行指令；默认是自动分配剩余显卡，可以切换为手动指定并进行指定；
在任务栏上方要显示一共有几张卡和当前的训练系统占用了哪几张卡；

对项目增加删除按钮，删除项目需要输入管理员密码，执行删除后删除整个项目文件夹；
对项目下的每个工位增加删除按钮，点击后询问是否删除，确认后删除这个工位对应的所有文件；

1，进行标注界面设计，包含标签设计；生成标注页面；  
  编辑tag有哪几类，修改后写入到meta.json中；
  选择当前图片的tag是哪一种，默认是第一种；
  选择类别，进行标注；调整标注，删除标注；

标注版本上增加修改按钮，修改按钮点击后上面是多个图片的缩略图，中间是当前选择图片的大图，如果有标注的话显示当前标注结果；点击已有标注可选中（高亮虚线），按 Delete 键删除，可以调整标注；右侧选择label，默认选择第一个，在图像上拖拽画框完成标注，框会自动显示对应颜色和 label；右侧有按钮 重置，点击则恢复本来的标注，还有一个按钮保存，点击则保存到本地对应位置；如果存在修改没有保存的情况下切换到下一张图片或离开这个界面，要弹窗询问是否保存，如果选是的话则保存，否则丢弃标注的修改；


编辑标注页面，图片预览的部分不放在左侧，而是放在上方，只显示10张，通过翻页的方式找其他的；

在数据采集页面，在新增项目按钮左侧增加一个tag编辑按钮；有两种tag，一种是针对图片的tag，一种是针对每个标注框的tag；点击tag编辑按钮后查看当前所有的tag，分别是针对图片的和标注框的，可以删除或新增，tag的定义放到 /mnt/data1/data_server/info/tag.json 中；每次修改tag定义都修改这个文件；

在编辑标注页面，图像上的标注框显示序号，右下角的标注也显示每个标注对应的序号，添加删除按钮，可以直接删除该标注；添加tag选择按钮，一个标注框可以选择多个tag；选择的tag在预览图像中画出来；在右下角的tag列表也显示出来；

在预览图像下方显示当前图片的路径和对应的label文件的路径；
在预览图像的下方增加一个针对图片的tag选择；同样是可以不选或选一个或多个；选择的tag要显示出来；

图像和标注框的tag也都保存到label.txt 中；保存方式：如果有image tag，在label.txt文件的第一行加上 # image_tag:[tag1,tag2]，否则不加这样；
如果某个标注框有一个或多个tag，在每个标注框的行后面加上 tag:[tag1,tag2] 如果没有tag则不添加；

在数据采集页面，在新增项目按钮左侧增加一个tag编辑按钮；有两种tag，一种是针对图片的tag，一种是针对每个标注框的tag；点击tag编辑按钮后查看当前所有的tag，分别是针对图片的和标注框的，可以删除或新增，tag的定义放到 /mnt/data1/data_server/info/tag.json 中；每次修改tag定义都修改这个文件；
在编辑标注页面，图像上的标注框显示序号，右下角的标注也显示每个标注对应的序号，添加删除按钮，可以直接删除该标注；添加tag选择按钮，一个标注框可以选择多个tag；选择的tag在预览图像中画出来；在右下角的tag列表也显示出来；
在预览图像下方显示当前图片的路径和对应的label文件的路径；
在预览图像的下方增加一个针对图片的tag选择；同样是可以不选或选一个或多个；选择的tag要显示出来；
图像和标注框的tag的修改和标注框的修改一样，也都需要保存到label.txt 中；保存方式：如果有image tag，在label.txt文件的第一行加上 # image_tag:[tag1,tag2]，否则不加这样；
如果某个标注框有一个或多个tag，在每个标注框的行后面加上 tag:[tag1,tag2] 如果没有tag则不添加；

把工作台的查看标注的页面内容直接放在工作台的图片预览部分，可以不选择或选择一个或多个标注来显示

在标注修改页面增加一个删除图像的按钮，如果点击删除图像，那么删除该图像和所有对应的label.txt 文件


/mnt/data1/zdw/code/data_platform/data_process/image_dedup.py  完成这个文件，

输入参数是一个json文件，json文件中有要处理的数据的路径,例如 @zdw/code/data_platform/config/model_inference.json#L4，找到对应的要处理的数据路径，判断路径下 images下的图片是否有完全重复的，


在 json文件中还有一个参数是 delete_image, delete_image 是false的时候输出重复的图像名称，

针对重复的图像，输出保留的图像名称和删除的图像名称；

如果有，那么删除重复的图像，并删除对应的label.txt 文件，针对重复的图像，输出保留的图像名称和删除的图像名称；


1, 数据清洗设计
  1，去重
    去掉完全重复的图片；
  2，基于图像去重去掉部分背景图；
  3，图像与标注框tag标注

2，模型训练与评测设计：

1，标注对比功能设计与开发
  选择对比项，设置阈值，查看区别图片与统计结果；
  1，选择要对比的标注，两个或多个
  2，设置对比项：
    1，标注框，阈值：20%
    2，图像tag
    3，标注框tag不同


每个对比项分别和参考项进行对比；
然后设置标注框不同的百分比阈值；
  对比项标注的每个标注框要找参考标注里最近的标注框，然后计算重叠区域站当前标注面积的百分比，如果超多阈值，那么选择这一帧；如果参考项没有标注框，对比项有，或者对比项没有标注框，参考项有，那么也选择该帧；
另外有两个可选项，分别是图像标签和标注框标签，选中图像标签后，图像标签不同则选择该帧；
选中标注框标签后，对于判断重叠的标注框，如果存在标签不同也选择该帧；
显示统计信息，
将所有显示的图片


前后端解耦的方式：

方法1，前后端解耦的方式；通过前后端解耦的方式，这样后续可以后端调用脚本；

写脚本 /mnt/data1/zdw/code/data_platform_test/data_platform/data_process/annotation_compare.py，输入是一个json文件，json文件中有项目/工作台的路径，例如 "person_all_2/group_0085__zhongtuo_0"，然后设定一个参考标注，例如 det_manual_0，设置一个或多个对比标注，例如 manual_0；还有标注框不同的百分比阈值，还有 image_tag_compare 和 box_tag_compare 两个flag；
这个脚本中，针对这个数据的不同版本的标注进行对比；每个对比标注分别和参考标注对比；要选择出来对比不同的帧；对于每个图像，对比标注的每个标注框要找参考标注里最近的标注框，然后计算重叠区域占当前标注面积的百分比，如果超过指定阈值，那么选择这一帧；如果参考项没有标注框，对比项有，或者对比项没有标注框，参考项有，那么也选择该帧；
如果 image_tag_compare 是true，那么图像标签不同也选择该帧；
如果 box_tag_compare 是true，那么对于判断重叠的标注框，如果存在标签不同也选择该帧；
将结果保存 /mnt/data1/data_server/tmp 路径下，保存为一个json文件，其中包含统计信息：
每个对比项相比参考项，有多少个图片筛选出来了，有多少个标注框认为不同；分别显示相对于图片总数和标注框总数的比例；另外有一个包含具体不同的图片的路径列表；

针对/mnt/data1/zdw/code/data_platform_test/data_platform/web_test 下的前后端进行修改，不要管 /mnt/data1/zdw/code/data_platform/web_test 路径； 
在工作台信息查看界面，增加一个标注对比的button，点击后跳转到标注对比页面，
针对已有的不同版本的标注，选择一个作为参考，可以选择一个或多个作为对比项；加一个button开始对比；点击开始对比后，在 /mnt/data1/data_server/tmp 路径下生成对应的config文件，调用 annotation_compare.py，界面上显示当前执行的指令，然后读取生成的 /mnt/data1/data_server/tmp 路径下的结果文件；显示统计信息；

另外将和参考项不同的图片显示出来，如果有多个对比项，只要有一个对比项和参考项不同，这样的图片就参与显示；首先是一个预览，每次显示10张，通过列表切换，选中一张后即显示对比结果，左侧是参考图，右侧是对应的一个或多个对比图；每个对比项的图片都显示；

针对 /mnt/data1/zdw/code/data_platform/web_test 下的前后端进行修改，不要管 /mnt/data1/zdw/code/data_platform_test/data_platform/web_test 路径；
模型结果存放在 /mnt/data1/data_server/models/，例如 /mnt/data1/data_server/models/yolo_train_test1，其中inference下存放的是推理的结果，对应的图片或视频是 /mnt/data1/data_server/collections 路径下；在模型结果查看页面，如果模型有inference结果，那么对于视频来说，通过下拉框选择显示哪个视频，选择后显示视频播放，其中推理的结果要显示到视频上；对于图片来说，通过下拉框选择哪个工位，然后上面一行是10张图片的预览，可以翻页，点击后显示图片和标注的结果；


python model_run.py -c config/model_train.json 是运行训练和测试，在 /mnt/data1/data_server/datasets/person_det_0.json 中指定了训练集和测试集分别是哪些；
/mnt/data1/zdw/code/data_platform/config/model_train.json 中增加了一个标志位 only_inference_flag，在这个标志位为true的时候，这时候不进行训练，仅运行测试集测试，生成和训练模式时同样的测试结果；

如果 only_inference_flag 是false，那么训练结束后，使用 best.pth 模型，
如果 inference_train_set 是 true，将所有train_set 的结果跑推理，保存到model结果的inference文件夹下，例如 /mnt/data1/data_server/models/yolo_train_test1/inference，新建文件夹 train_set,然后里面保存对应的label.txt
如果 inference_val_set,将所有val_set 的结果跑推理，保存到model结果的inference文件夹下，例如 /mnt/data1/data_server/models/yolo_train_test1/inference，新建文件夹 val_set,然后里面保存对应的label.txt

如果only_inference_flag 是 true，那么使用加载的预训练的模型，这时候不进行训练，仅运行测试集测试，生成和训练模式时同样的测试结果并保存；

如果 inference_train_set 是 true，将所有train_set 的结果跑推理，保存到model结果的inference文件夹下，例如 /mnt/data1/data_server/models/yolo_train_test1/inference，新建文件夹 train_set,然后里面保存对应的label.txt
如果 inference_val_set,将所有val_set 的结果跑推理，保存到model结果的inference文件夹下，例如 /mnt/data1/data_server/models/yolo_train_test1/inference，新建文件夹 val_set,然后里面保存对应的label.txt；

标注结果对比也可以服用；

model_inference.json 中新增一个字段，inference_flag: "data_inference"，inference_flag 是 ”data_inference“ 或者 ”dataset_inference“，在web上二选一，选择后只需要填写对应的内容即可，生成json文件时不选的部分设置为空

python model_run.py -i -c config/model_inference.json 是运行模型推理，如果 "inference_flag" 是 "data_inference", 那么使用当前 /mnt/data1/zdw/code/yolo_for_platform/run.py 中的推理逻辑，相关配置在 "data_inference": 中，如果  "inference_flag" 是 "dataset_inference"，使用  "dataset_config" 定义的数据集配置中的数据进行推理，这时候如果 inference_train_set 是true，那么运行训练集的推理，如果 inference_val_set 是true，那么运行测试集的推理；运行结果同样保存到 inference 文件夹下，例如如果使用的dataset是 person_det_0，那么数据定义在 /mnt/data1/data_server/datasets/person_det_0.json 文件中，运行结果保存到 data_server/models/yolo_train_test1/inference/person_det_0/train_set 或 data_server/models/yolo_train_test1/inference/person_det_0/val_set；

模型评测的设计：
  1，训练曲线图与示例图
  2，数据inference结果
  3，数据集inference结果
  4，对比标注结果；

针对 /mnt/data1/zdw/code/data_platform/web_test 下的前后端进行修改，不考虑data_platform/web下的实现；
在查看模型结果页面，在推理结果，除了视频 图片外，增加一个数据集，点击数据集后选择 /mnt/data1/data_server/models/yolo_train_test5/inference 路径下除了 collection_data 外的数据集的名称，并指定选择train_set 还是val_set，然后通过同样的方式显示图片，上面一行是预览，可以翻页，点击后显示标注结果

针对 /mnt/data1/zdw/code/data_platform/web_test 下的前后端进行修改，不考虑data_platform/web下的实现；
评测页面修改
  1，选择模型：选择两个或多个模型；
  2，选择对比内容：
    1，train_img 选项，如果选中 train_img，那么显示选择的多个模型的train_img下名称相同的图片的选项，选中则显示选中的模型的train_img文件夹中对应的图片进行对比；

    2，inference 选项，如果选中 inference，那么显示选择的多个模型下 inference 文件夹中相同名称的工作台和数据集；
      工作台可以选择一个或多个，数据集只能选一个，要么选工作塔，要么选数据集；
      选中后有个按钮是对比；先不进行对比按钮的实现

评测后端prompt：
实现 /mnt/data1/zdw/code/data_platform/data_process/detection_compare.py，输入是一个json文件，在 /mnt/data1/zdw/code/data_platform/config 下生成这个json文件,json文件中里包含 reference_datapath，是一个项目文件夹的路径列表，例如 ["/mnt/data1/data_server/collections/daming","/mnt/data1/data_server/collections/kate"] 或 ["/mnt/data1/data_server/models/yolo_train_test5/inference/collection_data/daming"] 可以是 data_server/collection 下的项目文件夹，也可以是 models/xxxxxx/inference 下的；如果是 data_server/collection下的项目文件夹，要指定使用的标注版本，
另外json文件中包含 compare_datapath_list，其中的每个元素是一个名称+一个列表，这个列表可以理解为是一个模型的运行结果，也是一个项目文件夹的路径列表；例如 "yolo_train_test5":["/mnt/data1/data_server/models/yolo_train_test5/inference/person_det_0/train_set/daming"]

循环处理 compare_datapath_list 中的每个列表，每个列表的处理方式是首先找到全部和 reference_datapath 中对应的label.txt，即 label.txt 同时存在在这两个路径下，然后选择出来不同的帧；对于每个图像，compare的每个标注框首先要经过置信度阈值过滤（这个置信度阈值也在 json文件中指定），然后找reference标注里最近的标注框，然后计算重叠区域占当前标注面积的百分比，如果超过指定阈值（这个重叠阈值也在json文件中指定），那么选择这一帧；如果参考项没有标注框，对比项有，或者对比项没有标注框，参考项有，那么也选择该帧；将结果保存 /mnt/data1/data_server/tmp 路径下，保存为一个json文件，其中包含统计信息：每个对比项相比参考项，有多少个图片筛选出来了，有多少个标注框认为不同；分别显示相对于图片总数和标注框总数的比例；另外有一个包含具体不同的图片的路径列表；

评测前后端结合的prompt：

在评测对比页面，选择1个或多个model，当对比内容选 inference后，在选择推理数据栏，
需要设定重叠判断阈值和置信度过滤阈值，
如果选择工作台，选中一个工作台后，要选择一个参考项，参考项可以选择选中的某一个模型，或者是 collections/项目/工作台 下某一个版本的标注；选择参考项后，可以点击对比按钮，这时候在 data_server/tmp/ 下生成对应的 json文件，并执行 /mnt/data1/zdw/code/data_platform/data_process/detection_compare.py 脚本，显示执行的指令，执行完成后输出结果也在 data_server/tmp 路径下，显示这个结果文件的路径，读取这个结果，显示其中的统计信息，对于对比项和参考项不同的图片进行显示，只要有一个对比项和参考项不同就取出来该图片，先是10张图片的预览，可以翻页，点击某个图片后显示对比结果，左侧是参考项，并列的是其他的对比项，显示标注或检测框的结果，如果有conf也显示出来；
如果参考项选择是某个版本的标注，对比项就是所有选中的model，可以是一个或多个，如果参考项是某个model，那么对比项就是剩余的选中的model

如果选择数据集，在下拉框需要具体选择数据集的train_set 还是 val_set，然后也要选择一个参考项，参考项可以选择选中的某一个模型，或者是 collections/项目/工作台 下某一个版本的标注，点击 对比按钮，这时候同样在 data_server/tmp/ 下生成对应的 json文件，其他操作和上面相同；

在标注对比页面，增加一个置信度阈值，在生成 ann_compare config json 文件时，写入这个阈值，在执行 /mnt/data1/zdw/code/data_platform_test/data_platform/data_process/annotation_compare.py 时读取这个阈值，通过这个阈值对检测框进行过滤；如果检测框有置信度，那么只保留大于置信度阈值的，如果没有置信度，那么默认保留；用过滤后的检测框进行不同图片的判断和统计指标计算；

在新建数据集添加来源时，来源采集也采用这样的选择方式，可以批量选择，范围指定通过百分比的形式，通过滑动指定是0到百分之几，或者是百分之几到百分之百；在生成数据集文件时，index项根据指定的百分比来计算对应工作台的index范围；对于0到百分之几的范围，计算的index减1然后向上取整，对于百分之几到百分之百的范围，计算的index直接向上取整；

另外除了要选择标注版本，对于训练集还要设置权重，对于训练集和测试集都要设置置信度阈值，另外要指定每个图像标签的权重和每种标注框的权重，生成的数据集文件参考 /mnt/data1/data_server/datasets/person_det_0_withtag.json

数据采集的工作台图片预览栏中，当选中显示标注时，如果该标注有conf，那么conf的值也显示出来；
在标注标记页面，同样如果有conf，那么conf的值也显示出来；

在模型结果 推理结果中，如果选择数据集，选择 train_set 或 val_set 后，然后选择一张图片，在这张图片下方显示该图片的路径和推理得到的label文件的路径

在推理结果栏选图像后，可以选择与不同版本的标注对比，在数据集的结果中也增加这个功能，可以选择不同版本的标注进行对比

在标注编辑页面，增加快捷键 A/D 分别是上一张，下一张；ctrl+s是保存；在选择保存或不保存的界面可以通过方向键和回车键选择；
通过按钮指定是选择模型还是画框模式，默认是画框模式，指定为选择模式后可以选择已有的框，然后移动位置，调整大小；


1, 新建代码配置中训练参数部分，改为自定义的形式，
在代码配置栏，对已有的代码配置增加一个复制按钮，点击后进入新建配置的编辑页面，不过里面的内容先预先填所点击的复制项的内容
新增的参数除了是value，也可以是列表或者字典的形式

在任务栏，在创建推理任务左侧新增一个创建数据处理任务，点击创建数据处理任务后，可以像新建推理任务中的 data_path_list 一样选择一个或多个工位，然后通过自定义的方式指定参数，可以是值或列表或字典；
需要选择一个数据处理方法，可选的数据处理方法的名称是 data_platform/data_process/web_task 路径以 task_ 开头的文件；点击创建任务后生成一个数据处理任务；增加一个数据处理任务栏，显示新建的数据处理任务，显示要执行的python代码，即选择的 task_ 开头的python脚本，参数是生成的配置文件，配置文件同样放到 tmp 路径下，同样有 开始 查看日志 删除 按钮，同样会显示运行状态和时间；

1，创建数据处理任务后，停留在数据处理任务栏，推理任务和训练任务同样是这样
2，数据处理任务 推理任务 训练任务 都增加一个按钮保存配置，点击后需要指定配置的名称，点击保存，然后会将配置文件保存到 data_server/info/task_config 路径下，文件名修改为指定的名称；
  在创建 数据处理任务 推理任务 训练任务 时可以选择已有配置，选择后直接在已有配置的基础上修改

1，平台更新：
  1，选择配置的时候要判断 type，只有符合的type才参与选择；
  2，保存的配置支持删除功能；

针对 /mnt/data1/zdw/code/data_platform/web_test 下的前后端进行修改，不考虑data_platform/web下的实现；
1，新建训练任务 新建推理任务 新建数据处理任务 时可以选择配置，只有对应type的配置才参与选择；
2，保存的配置支持删除功能，可以删除


3，增加终端，用于配置conda环境；
2，显卡占用通过显存来判断；
1，训练和推理任务通过后台进程来实现，防止系统的重启引起任务的终端，通过进程号可以判断任务的状态；其他逻辑保持相同；显示任务的进程号；

1，在任务栏增加一个按钮打开终端，打开之后是服务器的终端，可以用来查看任务运行，配置conda环境等；
2，现在的训练和推理任务通过通过python起一个进程来实现，有个问题是如果网页后端重启了，那么如果之前的训练任务没有运行完成也没了；应该修改为在系统后台启动，记录进程号来判断任务状态，同样可以查看运行log，如果网页后端重启了，再上来同样可以看到哪些进程正在运行，同样可以看log，可以中止该进程；
3，现在的显卡占用是根据当前平台使用了哪些显卡来判断的，另外新增一个显示，显示当前每张显卡的显存占用；


在 /mnt/data1/zdw/code/validation_tool 下进行开发，生成一个web界面，前端放到 frontend 中，后端放到 backend 中，前端使用vue，后端使用python，使用fastAPI作为python后端；
web界面左边栏是控制，一个滑动条调整相机高度；一个滑动条调整相机pitch角；一个滑动条调整相机yaw角，一个输入框设置相机fov；
右边是显示，右边上面是一个2d画布，表示地面，画布上是有格线，每个格子表示1米，在这个格子上可以绘制roi区域，选择一个点作为相机安装点；在这个点往上指定的高度安装相机；
右边中间是3d显示，显示包含地面和相机，会同步显示地面上绘制的roi区域；
右边下面是相机投影画面；
可以在画布上放置人的模型，在3d显示中会同步显示人的模型，人的身高是1米75，正常体态；

1，终端和ssh上去的不是一个终端；conda环境也不是一个conda环境；
终端栏启动的终端，运行 conda run -n base python -V 和通过ssh连上服务器后运行 conda run -n 环境名 python -V 输出的版本不同


修改 /media/hdd/data_pltform/web_test 下的网页，现在终端栏会报下面的错：
# >>>>>>>>>>>>>>>>>>>>>> ERROR REPORT <<<<<<<<<<<<<<<<<<<<<<

    Traceback (most recent call last):
      File "/home/wangyang/miniconda3/lib/python3.13/site-packages/conda/exception_handler.py", line 30, in __call__
        return func(*args, **kwargs)
      File "/home/wangyang/miniconda3/lib/python3.13/site-packages/conda/cli/main.py", line 89, in main_sourced
        result = activator.execute()
      File "/home/wangyang/miniconda3/lib/python3.13/site-packages/conda/activate.py", line 220, in execute
        response = getattr(self, self.command)()
      File "/home/wangyang/miniconda3/lib/python3.13/site-packages/anaconda_anon_usage/patch.py", line 52, in _new_activate
        return self._old_activate()
               ~~~~~~~~~~~~~~~~~~^^
      File "/home/wangyang/miniconda3/lib/python3.13/site-packages/conda/activate.py", line 183, in activate
        builder_result = self.build_activate(self.env_name_or_prefix)
      File "/home/wangyang/miniconda3/lib/python3.13/site-packages/conda/activate.py", line 337, in build_activate
        return self._build_activate_stack(env_name_or_prefix, False)
               ~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "/home/wangyang/miniconda3/lib/python3.13/site-packages/conda/activate.py", line 421, in _build_activate_stack
        deactivate_scripts = self._get_deactivate_scripts(old_conda_prefix)
      File "/home/wangyang/miniconda3/lib/python3.13/site-packages/conda/activate.py", line 787, in _get_deactivate_scripts
        for entry in os.scandir(join(prefix, "etc", "conda", "deactivate.d"))
                                ~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "<frozen posixpath>", line 77, in join
    TypeError: expected str, bytes or os.PathLike object, not NoneType

终端的输入字符超过一定长度后会自动从头显示，也没有换行到下一行，而是直接在当前行开头显示字符

1，查看日志的范围很小，web_test下网页的任务栏，点击查看日志后，显示的范围不够大， 应该支持显示全部范围，并在点击查看日志后，弹出来的页面上方显示log文件的路径


web_test 下的网页，在任务栏启，启动数据处理任务时，通过系统的conda环境中的base环境的python解释器来运行


/Users/abc/Documents/notebook_xinmier/code/sound_detect 在这里做一个web ui，前端用vue，后端用python，框架用 fastAPI，前端放到 frontend 文件夹，后端放到 backend文件夹，backend 文件夹中的 main.py 来启动整个web ui；端口用6173
做一个语音标注工具，可以载入音频，播放语音，可以暂停和继续播放，通过一个按钮点击可以在当前位置进行标注，可以删除已有的标注结果，点击保存后标注的结果保存到 /Users/abc/Documents/notebook_xinmier/code/sound_detect/anno/xxx.json 文件中，文件名称是对应的音频文件的名称；对应的音频文件保存到 /Users/abc/Documents/notebook_xinmier/code/sound_detect/sound 统一保存为mp3文件；
可以选择不同的音频进行载入，如果本地已经有了对应名称的 json 标注文件，那么显示标注的结果，在这个基础上可以进行调整；

有一个识别按钮，实现一个基于标注的语音识别；
基于 /Users/abc/Documents/notebook_xinmier/code/sound_detect/anno 下所有的标注文件和对应的 /Users/abc/Documents/notebook_xinmier/code/sound_detect/sound 下的音频文件；基于这些标注信息来进行语音识别，对当前音频的识别结果统计准确率和召回率；

数据量很小，只有1分钟的音频，只有7个标注结果，增加选择框，可以选择不采用模型训练的方法来进行识别，通过其他好用适合的方法来进行识别

可以支持用 0.25 或 0.5 倍速播放音频，可以支持播放标注列表前后窗口前后的音频，比如窗口是 0.5秒，那么播放标注点前 0.25秒到后0.25秒的音频，可以微调标注点位置，左右调整0.1秒，通过按键实现

现在标注了一个结果，直接用这个结果来训练或进行模板匹配，然后还用这个结果来测试，准确率差，基于这个标注结果提高准确率，用合适的方法，找合适的参数，因为数据量很小，不要过拟合

/mnt/data1/zdw/code/sound_detect/sound 中存放了音频文件，
/mnt/data1/zdw/code/sound_detect/anno 中存放的是每个音频文件对应的标注文件，其中的时间点表示标注结果，也就是希望检测出来的时间点；
要做一个检测器，希望在标注结果的位置输出true，其他位置输出false；
在 /mnt/data1/zdw/code/sound_detect/sound_detect/main.py 中实现，功能函数放到 /mnt/data1/zdw/code/sound_detect/sound_detect/utils.py 中；main.py 中先进行数据读取，时间窗口取0.3秒，将数据分为正样本，负样本，正样本是标注点前后0.3秒的窗口，负样本随机找其他位置0.3秒的窗口即可，负样本的数量是正样本两倍；输出正样本和负样本的数量；

然后将80%的正样本和负样本分别训练集，其他的分为测试集；
先测试一个mlp的方法，训练后输出在训练集和测试集的正确率

有什么开源的语音识别方法，要识别一个插孔的声音，提供一些插孔声音的片段后可以从一段语音中识别出来需要的声音？即在出现插孔声音的时候输出true


在 /mnt/data1/zdw/code/sound_detect/sound_detect/main.py 中增加一个模板匹配的方法，通过命令行参数指定用这种方法，通过互相关匹配来实现，通过聚类后多模板匹配来利用多个标注信息，然后测试在所有正样本和负样本上的正确率

在 /mnt/data1/zdw/code/sound_detect/sound_detect/method2.py 中参考 main.py 的数据载入，通过YAMNet + 微调来实现这个音频事件检测，利用80%的数据来微调，然后分开看训练集和剩下的测试集的正确率和召回率

1，使用更多的负样本，合理处理负样本数量远大于正样本的情况

前端增加一个训练按钮，选择使用的训练数据，输入模型名称，然后点击确定进行训练，训练完成后将模型结果保存 /mnt/data1/zdw/code/sound_detect/models/xxx_method/xxx.pt
增加一个下拉框，针对当前方法选择使用的本地模型，选择后使用该模型对当前数据进行识别
另外新建一个 inference.py 文件，通过命令行参数指定要使用的算法，指定要使用的模型，指定要进行识别的音频文件；
里面有一个函数，函数输入是时间窗的音频数据 使用算法 模型，输出是 true 和 false，
通过调用这个函数对整个音频文件进行判断，输出判断的结果；验证运行正常，然后给一条测试指令


拉取一个 ubuntu22.04的镜像，然后基于这个镜像创建一个新的镜像，把/mnt/data1/zdw/code/sound_detect
文件夹放到新的镜像中，其中这个镜像，在这个镜像中配置 /mnt/data1/zdw/code/sound_detect 中需要的全部环境

/mnt/data1/zdw/code/sound_detect/backend/inference_clip.py
现在 python inference_clip.py --method yamnet --model ../models/yamnet/6.pt --audio ../sound/june23_20.m4a --threshold 0.5
可以将音频的检测结果输出；
修改 inference_clip.py，输入的 audio 可以是一段音频信号，通过 xx,xx,xx 文本列表的形式输入，如果输入的是音频信号，那么直接输出inference的结果，结果是true或者false

/mnt/data1/zdw/code/sound_detect 中创建一个新的web页面，前端放在 web_user 文件夹下，后端写到 backend 文件夹中，通过 main_user.py 来启动；
这个页面可以选择系统的麦克风输入，选择之后点击开始监听可以获取麦克风的输入，然后调用 python inference_clip.py --method yamnet --model ../models/yamnet/6.pt --audio "0.1,0.2,-0.3,0.05,..." --threshold 0.5, 其中 audio信号是当前麦克风输入的时间窗，根据配置输入0.3秒的数据，采样后信号长度是4800.
然后获取 inference_clip.py 的输出，将输出实时显示在网页前端；


docker run --gpus all -it \
    -p 6175:6175 \
    -p 6176:6176 \
    -v /mnt/data1/zdw/code/sound_detect:/app/sound_detect \
    sound-detect

docker run --gpus all -it \
    -p 6175:6175 \
    -p 6176:6176 \
    -v /home/guest/zdw/sound_detect:/app/sound_detect \
    sound-detect


/home/guest/zdw/sound_detect/Dockerfile 创建的docker，这样进行启动 
docker run --gpus all -it \
    -p 6175:6175 \
    -p 6176:6176 \
    -v /home/guest/zdw/sound_detect:/app/sound_detect \
    sound-detect
启动后运行 python main_user.py 来启动网页，麦克风下拉框提示无法获取麦克风权限，怎么解决

修改前端显示，除了历史记录外，通过一个灯显示true还是false，如果是 true那么显示绿灯，否则显示灰色；
参考 /home/guest/zdw/sound_detect/sound_detect_method2/main.py 中对 /home/guest/zdw/sound_detect/sound_detect_method2/detect_plug_pulse_1s.py 中 detect_plug_pulse_1s的调用；
在前端增加一个方法显示，原来的方法是 model，新的方法是 filter，如果选择model那么调用原来的方法，时间窗和之前一样，参数和之前都一样；
如果选择 filer，那么通过 detect_plug_pulse_1s 来进行判断；detect_plug_pulse_1s 的输入参数 x1s 是1秒的音频数据序列，这个和原来的方法不同，另外要输入 fs 参数；
注意在使用麦克风输入的时候，输入的形式和选择音频文件要保持一致，采样率一致；当选择麦克风输入的时候，也根据一个音频文件来确定使用的采样率和fs参数；麦克风输入要保持一致的参数

在 check.py 中写个脚本，判断  /mnt/data1/data_server/collections/person_all_2 下的每个工位的annotation下，有哪些没有 det_manual_0_tag_qwen_dedup 这个版本

在check.py 中后面实现，如果没有 det_manual_0_tag_qwen_dedup 这个版本，那么把 det_manual_0_tag_qwen 版本复制一份命名为 det_manual_0_tag_qwen_dedup


122.225.62.2 上 /mnt/data1/data_server/collection 文件夹要传输到 admin1@122.225.62.9:/mnt/data1/data_server/ 下，通过什么指令或工具，如果断了还可以继续，可以显示百分比和剩余时间

rsync -avh --info=progress2 --partial -e ssh /mnt/data1/data_server/collections admin1@192.168.200.20:/mnt/data1/data_server/

rsync -ah --info=progress2 --no-inc-recursive --partial -e ssh /mnt/data1/data_server/collections admin1@192.168.200.20:/mnt/data1/data_server/


json文件中包含 image_tag 的列表，其中是一个或多个 image_tag
包含 annotation 的类型；类型可以是 detection segmentation keypoint detection_segmentation
然后包含 label 列表，表示每个label的id；
然后包含 annotaiton 列表；
每个annotation的元素是一个字典；
字典包含annotation的tag列表，label id，和标注信息；如果是detection，那么标注信息是box，如果是segmentation，标注信息是多边形；
如果是keypoint，标注信息是每个点的坐标；


1，生成示例数据，meta.json 中指定数据类型
  "type": "detection_txt",
  "type": "detection",
  "type": "segmentation",
  "type": "keypoint",

/mnt/data1/data_server/collections/daming/data_format_example/annotations 中生成另外3种类型的标注，类型分别是 detection segmentation keypoint，参考
/mnt/data1/zdw/code/data_platform/doc/data_example 下的3种格式；其中meta.json仿照 /mnt/data1/data_server/collections/daming/data_format_example/annotations/auto_yolo11l_official/meta.json，但是type要进行修改；同样是一张图片对应一个同名的标注文件

/mnt/data1/data_server/collections 下有数据集，数据集格式参考 /mnt/data1/zdw/code/data_platform/doc/data_design.md
有不同的项目，每个项目下有不同的工位，每个工位下可能有标注，标注会有不同版本，具体每个版本的标注都有一个meta.json文件;
写一个脚本，输入是一个项目的名称，然后将这个项目下的所有标注的 meta.json 中 "type":  修改为 "detection_txt"；
输出所有修改文件的名称


修改 /mnt/data1/zdw/code/data_platform/web_test_onsite 下的网页，当使用管理员用户登录时，是现在的情况；当使用普通用户登录时，
左侧的代码栏 模型结果栏 终端栏 资源监控 评测栏是不可见的，其中任务栏中，没有新建推理任务和新建数据处理任务，只有新建训练任务，在任务显示中只有训练任务和入库任务，没有推理任务和数据处理任务；
另外数据采集栏中项目的删除操作是不可选的；

