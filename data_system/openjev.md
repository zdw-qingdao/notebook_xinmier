

35B-A3B 额外的mpl头的作用是什么，怎么训练的，有单独的训练数据吗？
内置NLI 3分类头的训练数据公开了吗？
这个分类头的训练是和语言主干的微调同时进行的吗？
不同大小的qwen3.5训练内置3分类头时使用了同样的数据吗？
问题+一个候选答案是什么样的形式？举个例子？
openjev类似的最新的开源的工作有哪些？
发布数据不包含图像原文件，那么对应的图像原文件在哪？

1, 已有jev加入到workflow中；
2，jev分类头训练支持；
3，可以选择自己训练的jev；

1，将openjev clone到本地，进行本地部署，给我部署后的端口；
关闭当前部署，提供启动和关闭部署的指令；

3，做一个jev block，里面调用jev模型，问题通过参数指定；
  jev block也是推理block，要单独处理，可以进行批处理；

2，单独一个脚本，载入模型，输入图像和问题，输出回答；

在 /home/zhongdawei/code/autopipe2/autopipe/backend/workflow6 下新增一个jev block，block的参数要选择用哪个模型，可以选的模型放在 /mnt/data2/autopipe_hzj/data/model/openjev 下；将下载的openjev模型复制一份放到这个位置 /mnt/data2/autopipe_hzj/data/model/openjev
类似 /home/zhongdawei/code/autopipe2/autopipe/backend/workflow6/block_library/models/yolo_detection.py,采用同样的方式设置gpu；
可以选择auto，也可以具体指定显卡和用量；如果是auto就是0.5张卡；
在workflow启动后，如果存在jev block，那么启动 SGLang，单独一个task，根据指定的显卡来分配任务用量；在启动的SGLang中也对应指定显卡数量和用量；
在jev block执行的时候，向 SGLang 发送请求并等待请求完成；
jev block的输入是一个图像，参数是一个或多个问题，可以灵活添加或删除问题，问题的数量对应输出的数量，输出是enum类型；有几个问题就输出几个enum；
先在 /home/zhongdawei/code/autopipe2/autopipe/doc/design_doc/workflow/v6 下生成设计文档，分阶段来实现整个过程，有不明白的问题问我，我review之后进行分阶段的实现；
其他也通过同样的方式来启动；




