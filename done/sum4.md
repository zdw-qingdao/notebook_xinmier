

request：
  more general camera product, cooperation with edgeflow. consistency of edge cloud and pc. multi products and camera from other companys.
  confirm or not.

response from jz
  into to product. be responsible for the product.
  confirm or not

response from ys:
  many times ask for sync. no suggestionable response. only ai doc, no self comprehention
  no report to me about the current progress and the following plan.
  some working going, not sure what, not sure the top design. 
  the current situation, confirm or not.
  not sure the demand from yang to you. not sure if support the new version plan, not sure what's on the progress about the migration. no sure the report line.
  the current situation, confirm or not.

question to confirm：
  1，progress and plan for the camera product.
  2, the relationship. report line.
  your idea and request, and following fomulation.
  seems like we algorithm, you camera. is this or not?

1，测试可以用这个： http://demo.edgeflowos.com:10000

---------------------------------------------

0，产品提交需求，我来分配任务；
1，组会前每个人给自己名下的任务排期，以周二为节点；
2，组会对上周进展和下周计划；
3，双周二封板，林立在62.9创建离线与在线测试版本；在线版本在62.9部署；
4，方松组织进入测试，周三完成；
5，周四林立发版；云端和在线版本；

1, sync with haiyang and linli; task assignment and timeline setup.

面试：
  态度很谦逊，讲问题重点不是特别清晰；
  研究生项目很水；
  做的项目深度很一般；
  做的项目讲的不是特别清楚；
  讲问题逻辑不够清楚；
  对ai coding的使用，章法一般；
  可以作为普通员工招聘；

1, fix the bug;
  复现
  修复
  合入
  development rebase

1，明确后续发版流程
2，账号到期功能
3，分割标注与训练功能；
4，windows安装包
5，workspace project删除；
6，workflow输出topic可以在designer中接入，其他功能还有待完善；
7，saip可以设置某个账号禁止训练；

1，saip迁移过来的模型为什么不能部署，因为 {run_storage}/dataset/images/train/ 下没有图片，不能进行量化操作；
2，通过数据库迁移脚本来实现；

5，cosmoedge 后端架构，survey，if we need use this.

周四提；交接人huzejin；
todo任务：
  2，模型不能训练的问题解决；
  1，saip版本更新；

1，it：嘉善服务器账号统一管理，所有账号修改密码，删除ssh-key，需要添加的ssh-key统一找it进行，后续申请使用和人员离职需要维护账号；

打包设置：
  1，轻量包，包含代码
  2，模型包
  3，nv推理包；

3，新版本ray资源调度方式：
  1，资源占用是维护记录在哪里的；
  2，task_resource_config.json 现在是否work
  3，收费机制是否正常；
  4，对全部 YOLO 强制同节点
  5，多节点的情况；
  6，代码耦合；
  7，资源管理页面，显示每个gpu的份额占用；

2，显卡设置方式；ensure current usage is normal.

1，拆出来的好处是什么，两种方式，默认有一个worker，如果启动单独的worker容器，那么关闭本身的worker；
  linli

2，画框方式，需要怎么调整；根据xueying建议进行调整，detection进行调整，其他的还是需要先选择类别；

做一个系统，有下面的要求：

生成设计文档，有不明白的问题问我，分阶段实现整个系统；等我review；

7，局域网内设备发现，分组，mqtt broker，视频流转发，视频流列表；
5，先能发现局域网内设备，设置mqtt broker，然后考虑视频流转发
4，发现局域网内其他设备的方法；

1, 朱慧玲，叉车盒子： sync with jinzhi
  疲劳 电话 抽烟 离岗 没有安全带
  人脸识别，判断是这个人；
  quchen

1，sync with daizhenhua；
  ar950的适配；

7，fanshihao;
  1, 系统profile
  2，dashboard 查看profile；

6，千问进行行为分析；
  http://122.225.62.9:12860/

6，人 手 头 模型训练；

5，骨架标注与训练已完成，暂时不上线

4，新版相机开发中；
  http://192.168.10.126/

3，可以取代svap推理功能，可以接designer；下个版本可以上线；

2，设备互联互通开发中
  http://122.225.62.9:11860/

1, 分割功能支持
  http://122.225.62.9:10000/






