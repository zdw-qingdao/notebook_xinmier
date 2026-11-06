

总结 /home/simmir1/zdw/code/designer/vision-control-project 的内容，写到 /home/simmir1/zdw/code/designer/summary_doc 中；
要包含使用逻辑，代码框架等详细内容，用于后续ai修改代码，ai修改代码前可以先通过阅读这个文档来获取该项目的全部信息；

designer项目：
  /home/simmir1/zdw/code/designer/vision-control-project 是项目目录
  /home/simmir1/zdw/code/designer/vision-control-project/low-code-platform/node-red 是使用的低代码开发的框架
  其中 /home/simmir1/zdw/code/designer/vision-control-project/low-code-platform/plugin-nodes 是designer的block的定义
  /home/simmir1/zdw/code/designer/summary_doc 是这个项目的总结；
  启动方式：目前已经启动了；
  访问方式：

edgeflow项目：
  /home/simmir1/zdw/code/autopipe2/autopipe 是项目目录；
  其中 /home/simmir1/zdw/code/autopipe2/autopipe/backend/workflow6 是workflow部分的后端代码；
  /home/simmir1/zdw/code/autopipe2/autopipe/doc/design_doc/workflow/v6 是workflow部分的设计文档；
  启动方式：./docker/docker_run.sh，目前已经启动了
  访问方式：

xxxx.json是designer中运行的一个工程，导入后可以运行；现在要把这个工程的实现迁移到 edgeflow 项目中；做下面几个事情；
1，实现 xxxx.json 的整个流程，先不关注前面板的ui，重点进行block的迁移，实现workflow的运行功能；将需要的block迁移到workflow6中；不要修改原有的workflow的执行逻辑，只进行block的迁移，然后将block拼接实现一个workflow，复刻 xxx.json 的功能；
2，不能只通过迁移block实现的功能要问我，给出建议，我来决定怎么实现；
3，对于每个迁移的block，迁移的时候要分阶段实现，具体告诉我迁移了哪些block，迁移的block实现的功能是什么；
4, 告诉我还缺少哪些功能，后续怎么分阶段实现；

先写设计文档，有不明白的问题问我，分阶段实现；我review后进行开发；另外给我提供一套后续迁移指定算子或pipeline工程的prompt；后续如果有其他需要迁移的内容通过这个prompt来进行迁移；

将自定义可视化面板的功能迁移到中，支持自由排列和自动排版；





