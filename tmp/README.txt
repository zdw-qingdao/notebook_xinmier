PicUnique —— 图片去重工具
============================

用于工厂固定摄像机拍摄的训练图片去重。
递归扫盘、聚类去重，支持缓存、删除重复、打 tag 标签。

————————————————————————————————————————————
环境要求
————————————————————————————————————————————
  Python 3.6+
  安装依赖:  pip install opencv-python

————————————————————————————————————————————
文件说明
————————————————————————————————————————————
  dedup_images.py         主脚本 —— 读配置、扫盘、去重、删图、打 tag
  similarity_checker.py   检测算法模块（依赖）
  label_utils.py          标注工具模块（依赖）
  sample.json             示例配置文件

————————————————————————————————————————————
快速开始
————————————————————————————————————————————

1. 编写配置文件（参考 sample.json）

{
    "type": "data_process",
    "task_config": {
        "data_path_list": [
            "/data/path1/",
            "/data/path2/"
        ],
        "params": {
            "cache_flag": "cal_no_cache",
            "cache_folder_path": "",
            "del_flag": 0,
            "generate_tag": 0,
            "parent_annotation_version": "",
            "annotation_name": "",
            "tag_name": "",
            "dup_method": "pixel_max_diff",
            "dup_param": "20"
        }
    },
    "script": "dedup_images.py"
}

2. 运行

  python dedup_images.py config.json

————————————————————————————————————————————
配置参数说明
————————————————————————————————————————————

  data_path_list           图片根目录列表，支持多条路径，递归查找图片文件夹
  cache_flag               缓存模式：
                             cal_no_cache    不缓存，直接计算（默认）
                             cal_save_cache  计算并保存聚类结果到 cache_folder_path
                             load_cache      从 cache_folder_path 读取已有结果
  cache_folder_path        缓存目录（cal_save_cache / load_cache 时必填）
  del_flag                 是否删除重复图片和 label（0=否，1=是）
  generate_tag             是否对重复图片打 tag 标签（0=否，1=是）
  parent_annotation_version 父 annotation 版本（复制到新版本的基础）
  annotation_name           新 annotation 版本名称
  tag_name                  tag 标签名
  dup_method               去重方法：pixel_diff / pixel_max_diff / exact
  dup_param                去重阈值

————————————————————————————————————————————
三种检测算法
————————————————————————————————————————————

  method         算法说明                      threshold 含义
  ──────────────────────────────────────────────────────────
  pixel_diff     32x32 灰度缩略图，逐格差     平均值 < threshold
                 取平均，允许局部差异           推荐 1.0 ~ 3.0

  pixel_max_diff 32x32 灰度缩略图，逐格差     最大值 < threshold
                 取最大值，要求全局相近         推荐 10.0 ~ 30.0

  exact          MD5 文件哈希，字节级比对     忽略 threshold
                 只有文件内容完全相同才判重复

————————————————————————————————————————————
三种效果的关系
————————————————————————————————————————————

三种效果：缓存、删除、打 tag。使用互不冲突。

  缓存（cache_flag）          始终执行，不依赖另两个。

  打 tag（generate_tag=1）   在 annotations/<annotation_name>/ 下新建版本，
                             给重复图片打 # image_tag:[tag_name] 标签。
                             不影响原图。

  删除（del_flag=1）          删除重复图片及其所有 annotation 版本的 label。
                             删除和打 tag 互斥：
                             开了 del_flag=1 则 generate_tag 被忽略。
                             逻辑：图片都没了，label 没有意义，
                             违背"有 label 必须有对应图片"的原则。

————————————————————————————————————————————
两种工作流程
————————————————————————————————————————————

流程 A: 先看再删（安全，推荐第一次用）
  1. cache_flag: "cal_save_cache", del_flag: 0, generate_tag: 0
     → 计算去重，保存缓存到 cache_folder_path
  2. 人工查看缓存目录下的 dup_group_* 分组，移除不想删的图片
  3. cache_flag: "load_cache", del_flag: 1
     → 基于缓存执行删除

  load_cache 删除时仅针对缓存 dup_group_* 中实际存在的图片。
  用户手动移除的图不会被删，被移除的图会自动顶替代表图。

流程 B: 直接删（已验证参数后可放心使用）
  cache_flag: "cal_no_cache", del_flag: 1
  → 扫盘 + 去重 + 删图 一条龙

流程 C: 只打 tag 不删（保留标注记录）
  cache_flag: "cal_no_cache", del_flag: 0, generate_tag: 1
  → 扫盘 + 去重 + 新建 annotation 版本 + 打 tag
  → 图片不受影响，仅在 label 中标注重复

————————————————————————————————————————————
缓存目录结构
————————————————————————————————————————————

多个 data_path 会找公共祖先，在 cache_folder_path 下镜像还原目录结构：

  cache_folder_path/
    <相对路径>/
      dup_group_0001/    每组重复图片的副本
        dedup_report.json  去重报告

————————————————————————————————————————————
Tag 标签记录
————————————————————————————————————————————

generate_tag=1 且 del_flag=0 时，在 annotations/<annotation_name>/ 下为重复图片打标签。

如果指定了 parent_annotation_version，会先复制父版本的内容到新版本。

给每组重复图片中非代表图（n-1 张）的 label 添加：
  # image_tag:[tag_name]

三种情况：
  1. label 不存在 → 新建文件，写入 # image_tag:[tag_name]
  2. label 存在但无 tag 行 → 第一行插入 # image_tag:[tag_name]
  3. label 已有 tag 行 → 追加逗号，变为 # image_tag:[old,tag_name]
代表图和独立图不会被打 tag。
