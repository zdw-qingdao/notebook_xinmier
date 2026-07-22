

图片的输入始终是string形式，可以是图片本地路径，视频本地路径，或者rtsp的链接；
block中要定义输入输出，block的声明还是采用拆分的方式；


/home/zhongdawei/code/autopipe/backend/workflow 中参考 /home/zhongdawei/code/inference/inference/core/workflows 实现了一套精简的workflow引擎，包含测试，测试已经通过；开发文档在 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/v1/dev_v1.md; 对应的roboflow inference的实现参考 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/v1/roboflow_inference_relative.md； 但是这个实现代码可读性不好；要在/home/zhongdawei/code/autopipe/backend/workflow2 中重新实现一套同样功能逻辑的workflow引擎；
设计要求：
采用模块化的实现方式，避免冗余设计；数据类型和输入输出定义简单一些，不要做的太复杂；在不影响执行逻辑的效率的情况下，简化设计，不用把类型校验做的很复杂，不利于代码阅读和维护与升级；
在 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/v2/dev.md 中写完整的设计；在我review设计之后完成整套系统，实现同样的功能，保证通过全部的测试用例；保证整体代码的模块化和可读性很强；有不确定的问题要问我；有合适的其他实现方案要问我怎么实现；如果下面的具体要求存在问题也要问我；

具体要求如下：
1，输入workflow的定义按照这样的格式:
不需要保留version字段，目前只有一版engine实现；
input字段里的内容定义和之前相同；
step里每一项对应一个block，一个block里是 type，name，parameters,inputs，
    parameters 放所有的参数；
    inputs 放所有的输入，通过同样的方式修饰来自input或者其他step的输入；
outputs下只写source字段，对应之前 selector字段的内容，即 "$steps.detector.count" 说明对应的step输出是什么；

2，data_type.py 中是数据类型的实现，所有的数据类型都定义在这里；数据类型定义的方式是一个全局字典；
字典中key是类型名称，value是具体的类型，先定义 int float string bool 类型；其他的类型是自定义的类；
例如 字典是 DATA_TYPE, DATA_TYPE['int'] =  int,
class ImageInput:
  ...
DATA_TYPE['ImageInput'] =  ImageInput
workflow和block所有支持的输入输出都通过这样的方式来定义；

3，block_base.py 中是block基类的实现，通过一个类来实现block基类；
类方法 get_input 可以返回输入字典；
类方法 get_parameter 可以返回参数字典；
类方法 get_output 返回输出字典；
输入字典key是输入名称，value是类型名称；参数字典和输出字典也是同样的；类型名称对应 数据类型字典的key的名称
在不实例化类的时候，可以通过类方法来获取输入输出的字典，前端可以用来获取block信息；
单独定义init方法，要单独调用init方法完成初始化；即实例化的时候不执行init，init需要单独执行；这样类实例化的成本很低；需要实例化的时候也不会占用很多资源；
init函数的输入是字典，key对应参数字典的key，value是实际的参数value
run函数的输入也是字典，key对应的输入字典的key，value是实际的输入value；输出是字典，key是输出字典的key，value是实际的输出vlaue；

4，engine文件夹下是engine的实现，目前不考虑多版本的问题；
  engine.py 中是 engine执行引擎的实现，通过一个类来实现，执行的部分和 coordinator的部分 都放到执行引擎中；
  graph.py 中还是运行图的定义，和原来的逻辑保持相同
  compiler.py 中构建graph；block之前还是通过输入输出的名称来进行连接；和原来的逻辑保持相同
  task.py 中是通过ray的basetask进行的workflow执行的封装；

block_library文件夹中是不同的block的实现
utils文件夹下是工具函数的实现
test文件夹下放的是测试代码
通过构造json数据进行测试，构造的json数据保存到test文件夹下，测试可复现；对完整的流程进行测试，确保测试正常；测试要涵盖对blocks_library中的每个block；
将测试用例运行指令，自定义block的教程都加到 /home/zhongdawei/code/autopipe/doc/design_doc/workflow/v2/dev.md 中；

进行下面的调整：
@autopipe/backend/workflow2/engine/graph.py#L70-75 InputNode 进行调整
selector 和 name 冗余了，通过函数来获取；增加类型 type:str ,去掉 is_iamge，不需要对图像类型单独处理；

@autopipe/backend/workflow2/engine/graph.py:78-86 StepNode selector和name冗余；修改为通过函数获取
@autopipe/backend/workflow2/engine/graph.py:89-92 selector冗余了，不需要，可以写函数来通过source获取；

@autopipe/backend/workflow2/test/workflows/classification_expression.json#L4  input 的类型定义应该是 /home/zhongdawei/code/autopipe/backend/workflow2/data_type.py 中的一种；
不单独在定义输入数据类型

调整完成后检查整体的逻辑，保证正常，运行测试保证测试通过；如果我的调整有不合理的地方，询问我调整意见



