

1，ray 方案选型；
  采用数据库的方式，log写到文件中；
  统一采用数据库的方式，单词任务直接通过ray来运行；常驻任务通过handler的方式来调用；
  1，数据库越来越长的问题，后续再说，可以删除10天以前的非常驻任务；
  怎么看排队情况，数据库中写入字段即可；
  我们自己写了一个ray的调度系统，连接ray集群，针对提交的任务进行调度，如果存在优先级那么进行优先级的排序，可以支持超时销毁等，
  网站的fastAPI后端怎么和这个ray的调度系统交互，提交任务，查看任务执行进度等；
  1，fastAPI直接启动管理进程；在管理进程中通过管理ray的任务调度；

重写init，run函数；
任务管理，做一个中间层,设计写到 /home/zhongdawei/code/autopipe/doc/design_doc/task_design/middle.md 
通过一个类来实现，类中有这个任务的类型，任务需要的所有资源；任务的执行，log，状态判断等；
用户自定义任务或者actor通过继承这个类来实现，需要重写的是init函数和run函数，run函数是执行的部分，init函数是初始化的部分；
无论是task还是actor，都通过这个基类来实现；
任务调度管理是一个单独的类，有一个add_task 函数，每一个要执行的task通过add_task加入到任务管理中；
任务管理要负责每个任务的运行，对每个任务进行管理；
先预留接口，不进行实现；把设计写到文档中；

实现一个新版的基于ray的任务调度，设计文档写在 /home/zhongdawei/code/autopipe/doc/design_doc/task_design/v2/ray_desing.md 中；
1，网站后端fastAPI 不直接调用ray，有另外的进程 scheduler 来进行ray任务的提交，优先级管理，超时销毁等策略；scheduler通过 /home/zhongdawei/code/autopipe/docker/supervisord.conf 来启动；在 ray_desing.md 中写明重启方式；
2，优先级管理的方式：优先级是不同的数字，数字越大则优先级越大；找到优先级最大的一个或多个任务，根据创建时间排序，依次判断能否加入到任务执行；可以加入则加入执行；如果存在优先级最大的任务在排队，那么优先级小的任务一直等待，即使当前资源足够执行；
2，fastAPI通过数据库来向 scheduler 提交任务，scheduler通过查询数据库来获取要执行的任务，提交到ray集群；
3，fastAPI既可以提交单次任务，也可以提交常驻任务，如果提交常驻任务，可以执行时调用单次执行的接口；如果是常驻任务，可以指定超时参数，如果超过指定时间没有调用run，那么销毁；
4，原 /home/zhongdawei/code/autopipe/backend/task_manager 中是单进程的实现方式，可以参考；新版同样在 /home/zhongdawei/code/autopipe/backend/task_manager 中实现；
5，要设计清楚怎么定义一个task，其他模块可以很方便的定义自己的task；可以指定任务的类型，任务需要的所有资源；通用的任务的执行，log，状态判断，执行进度等接口；在设计文档中写清楚怎么自定义一个task；怎么调用一个task；
7，在 /home/zhongdawei/code/autopipe/backend/task_manager/test 下写测试代码，要完整测试所有可能出现的情况，保证测试通过；在 autopipe_docker_24_2:zdw_24 docker内进行完成的测试；
  要有yolo ddp的单机多卡训练测试，保证测试通过；yolo中自己实现了ddp的部分，通过ray的actor来实现即可，不需要用ray的train api；
8，fastAPI支持获取当前的排队情况，如果一个任务在排队，那么可以知道前面排了哪几个任务；
9，ray的dashboard可以访问；系统在 autopipe_docker_24_2:zdw_24 中启动，ray的dashboard可以支持docker外访问；
10，先不考虑多机多卡的情况，先考虑单机多卡的实现；
11，系统中使用了原来的ray task的内容，需要根据新的接口进行适配；
12，在 /home/zhongdawei/code/autopipe/doc/design_doc/database/data_plan.md 中加入数据库的设计；



1. **同优先级 backfill**  
   本文理解“按创建时间依次判断能否加入”为：较早 task 资源不满足时，仍继续判断同一
   优先级的后续 task；只要最高优先级仍有 task 排队，就绝不检查低优先级。是否确认？
    确认；

2. **低优先级可能永久饥饿**  
   本文严格执行优先级，不做 aging。持续存在高优先级任务时，低优先级可能永远不执行。
   是否确认？
    确认；
3. **不抢占运行中任务**  
   新到达的高优先级任务不会杀死已经运行的低优先级任务，只等待资源。是否确认？
    确认；
4. **常驻 task 串行调用**  
   第一版每个 resident task 同时只执行一个 invocation；busy 时的新调用进入数据库 FIFO。
   是否需要单个 resident actor 支持并发 run？
  单actor串行即可；

5. **空闲超时**  
   idle timeout 只在 `ready` 且没有 queued/running invocation 时计时，不中断正在执行的
   invocation。是否确认？
   确认；

6. **Scheduler 重启恢复**  
   本文使用 named detached actors/placement groups，使只重启 Scheduler 时继续原任务，
   而不是销毁所有任务。是否确认？
    确认；

7. **优先级范围**  
   建议使用 PostgreSQL `INTEGER`，默认 `0`，API 限制
   `-1_000_000_000 <= priority <= 1_000_000_000`。是否接受？
    接受；

8. **YOLO DDP 测试 GPU**  
   完整测试至少需要两张空闲 GPU。请确认允许测试使用的宿主机 GPU 编号；容器若仅映射
   GPU 7，则无法完成多卡测试。
  使用GPU6 GPU7测试

9. **YOLO DDP 入口**  
   实现前需要确认现有 YOLO 自有 DDP 的模块路径、调用参数、进度回调和 checkpoint
   位置；如果当前还没有统一入口，将按第 15.3 节增加 adapter。
  使用ultralytics yolo的接口；


10. **等待依赖的高优先级 task 是否阻塞低优先级**  
    本文只把“依赖已满足、retry backoff 已结束”的 task 视为 runnable。一个 P100 task
    正在等待依赖时，不阻止 P90 task；但 P100 仅因资源不足而排队时会阻止 P90。
    是否符合预期？如果要求任何 queued 的 P100 都阻止 P90，需要修改 runnable 定义。
    符合预期；

11. **常驻 task 的资源与 invocation 优先级**  
    本文在 resident task 初始化时一次性执行优先级准入，之后它持续占用资源；其
    invocation 只在该 actor 内 FIFO，不再与全局一次性任务竞争优先级。是否确认？
    确认
    
2，先写设计文档，在我review设计文档后进行实现，有不明白的问题要问我，有不合理的地方要问我，代码要模块化好，易于测试，易于自定义task；

1，多docker的问题；每个人需要用不同的数据库；不同人不能用同样的数据库；
/home/zhongdawei/code/autopipe/config/config.json ray的部分中增加一个scheduler名称 ray_scheduler_name， 在 data_plan.md 的task表中加入 ray_scheduler_name；
ray的task管理的所有行为，只和数据库表中和当前 ray_scheduler_name 相同的有关系，和当前 ray_scheduler_name 不同的表的内容无关；将设计写入到 /home/zhongdawei/code/autopipe/doc/design_doc/task_design/v2/ray_desing.md

和训练任务的联动方式；后续再考虑这个；
训练任务表中需要加上对应任务表的id，完善 /home/zhongdawei/code/autopipe/doc/design_doc/task_design/v2/ray_desing.md 中的

decide this first:
1，是否需要常驻sam3，是否和其他模型的处理方式不同；
  不需要，目前先不考虑常驻sam3，需要的时候载入即可；
  如果不同人同时使用sam3，那么分别载入，分别启动任务；
2，是否采用actor直接调用的方式，还是通过gateway;
  目前没必要实现的太复杂；直接调用actor的方式即可；

总结：
  1，自动标注任务，单独启动一次性任务
  2，标注任务，使用常驻sam3，需要的时候载入即可，不需要一开始载入；
  3，调用常驻任务，直接通过actor调用即可；
  4，不同的人调用常驻任务，建立不同的actor任务即可，后续有需要再考虑复用的情况；复用的时候也可以在这个任务的run方法内服用，不一定需要走redis通道之类的；







