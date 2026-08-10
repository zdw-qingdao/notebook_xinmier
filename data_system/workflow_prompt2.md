

弃用设计：
  workflow引擎不使用batch：
    batch变量的类型，字典，batch index + 字典，字典也就是流转的输入输出变量；

流转变量的类型，统一指定
  类型的部分需要加上特定的通信类型；

  flowcontrol类型变量，是true或者false，表示后续的block是否执行；
  flowcontrol类型变量的特别在于，控制的block是没有单独写这一项输入的；
  block默认有这个这个输入；如果block接受到这个输入，那么这个block终止；
  block中止的方式：返回 block_stop，包含stop信息；
  flowcontrol作为一个输入，每个block默认都有这个输入，默认输入都是true；
  这样的方式好处在于，不需要单独处理很多东西；

  有不同的情况可能会调用block_stop，只要调用block_stop，那么engine就停止执行下面的；
  如果执行有异常也可以直接停止；

  这样的方式好处在于
    1，flowcontrol就是一个普通的输入；不需要单独处理
    2，flowcontrol和其他的node_stop统一处理；不需要再分开处理；
    block中返回的blockstop要加上原因，这样engine知道是什么原因退出的，正常的还是异常的；

    可视化输出：
      是输出解码叠加显示的图片，还是只输出draw的内容，在浏览器上叠加显示；
      目前只输出draw的内容即可；

原方案：
  workflow支持batch输入，某些block支持deepstream，自动将这样的block加入到deepstream的graph；
  存在过度设计，实现过于繁琐，推理引擎功能支持不够好；

新方案：
  1，视频流直接接deepstream block，deepstream block 不支持级联；
  2，workflow每次都是单路输出来执行，不需要支持batch；没这个必要；需要支持batch的操作放到推理引擎中做；不使用batch也会充分利用多核多进程的能力；
  3，deepstream的部分在一个block中实现，说明是deepstream block，需要在支持deepstream的电脑上运行；
  4，其他block都通过workflow执行引擎实现；



3，mqtt topic管理方式；
  mqtt topic表，当前的所有topic都要记录到这个表中；
    运行类型：相机 / 推理引擎 / workflow执行引擎
    相机id，workflow执行引擎的输出没有这一项；
    workflow实例id
    显示名称
    topic名称
    topic类型
    状态  no_pub with_pub_no_sub with_sub

    1，workflow执行输入如果要求是mqtt，要指定mqtt的行号；
    2，推理引擎输出要求是mqtt，要根据指定方式进行输出；
    3，topic名称的命名方式：
      运行类型+相机id+workflow实例id+显示名称+topic类型+序号；





