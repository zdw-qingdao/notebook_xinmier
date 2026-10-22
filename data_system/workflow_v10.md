

平台侧：
  1, svap function
  2, design function
  3, multi device cooperation.


多机器协同3种方式：
1，
  主机：ray客户端
  从机：edgeflow平台
2，主机：edgeflow平台
  从机：访问web页面；通过单独的程序来控制外设；
3，主机：edgeflow平台
  从机：edgeflow平台
  也可以有独立gpu计算节点；
  这样的方式中，相机 server pc 都是edgeflow平台的载体；server 和 pc运行的edgeflow是同样的；相机上运行的是嵌入式版本，workflow执行引擎的部分是一样的；
  可以分别独立编辑，也支持协同编辑；需要指定主节点是哪个；
  可以在主节点上进行协同编辑，也可以在从机上进行独立编辑；
  从机上的edgeflow就相当于客户端；
  显示当前的部署情况，只显示一个，这个没有workflow那种多个的概念；
  实现方式：  
    每个都向主节点发送当前执行的workflow；
    可以从主节点获取当前最新的完整部署情况；

相机侧：
  1，workflow version1
  2, run in 960
  3, run in other devices








