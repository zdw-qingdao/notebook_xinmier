"""
标注文件查找、删除 与 tag 标签管理工具模块。

功能：
  1. 依据图片路径自动发现 annotations 目录
  2. 镜像查找/删除对应的 label 文件
  3. 复制 annotation 版本
  4. 为图片添加 # image_tag:[...] 标签行

目录结构支持两种：
  A: images/<batch>/<name>.png   <=>  annotations/<version>/labels/<batch>/<name>.txt
  B: images/<name>.png           <=>  annotations/<version>/labels/<name>.txt
"""

import os
import shutil

LABEL_EXT = ".txt"
TAG_PREFIX = "# image_tag:"


def find_annotations_root(source_dir: str, max_up: int = 3) -> str | None:
    """从 source_dir 向上查找 annotations 目录。

    对 source_dir 的 1..max_up 级父目录，依次检查是否存在 annotations/ 子目录，
    找到即返回。

    例: source_dir = ".../images/20260512_112506/"
         → 检查 .../images/../annotations/ → 命中返回
    """
    for i in range(1, max_up + 1):
        candidate = os.path.join(source_dir, *([".."] * i), "annotations")
        candidate = os.path.normpath(candidate)
        if os.path.isdir(candidate):
            return candidate
    return None


def delete_labels_for_image(image_path: str, annotations_root: str, dry_run: bool = False) -> list:
    """根据图片路径，删除 annotations_root 下所有版本中对应的 label 文件。

    Args:
        image_path: 图片的绝对路径，如 ".../images/20260512_112506/000001.png"
        annotations_root: annotations 根目录
        dry_run: True 时只返回路径列表不执行删除

    Returns:
        已删除（或将要删除）的 label 文件路径列表
    """
    image_stem = os.path.splitext(os.path.basename(image_path))[0]
    parent_name = os.path.basename(os.path.dirname(image_path))

    deleted = []
    for version in os.listdir(annotations_root):
        labels_dir = os.path.join(annotations_root, version, "labels")
        if not os.path.isdir(labels_dir):
            continue

        # 结构 A: labels/<batch>/<name>.txt
        if parent_name != "images":
            label_a = os.path.join(labels_dir, parent_name, f"{image_stem}{LABEL_EXT}")
            if os.path.isfile(label_a):
                if not dry_run:
                    os.remove(label_a)
                deleted.append(label_a)

        # 结构 B: labels/<name>.txt
        label_b = os.path.join(labels_dir, f"{image_stem}{LABEL_EXT}")
        if os.path.isfile(label_b):
            if not dry_run:
                os.remove(label_b)
            deleted.append(label_b)

    return deleted


def copy_annotation_version(annotations_root: str, parent_version: str, new_version: str):
    """复制 annotation 版本。

    将 annotations_root/<parent_version>/ 复制到 annotations_root/<new_version/>。
    如果 parent_version 为空，则仅创建空的 new_version 目录结构。
    """
    new_dir = os.path.join(annotations_root, new_version)
    if parent_version:
        src_dir = os.path.join(annotations_root, parent_version)
        if os.path.isdir(src_dir):
            if os.path.exists(new_dir):
                shutil.rmtree(new_dir, ignore_errors=True)
            shutil.copytree(src_dir, new_dir)
            return True
        else:
            print(f"  [WARN] 父版本不存在: {src_dir}")
            return False
    else:
        # 无父版本，创建空的 labels 目录
        os.makedirs(os.path.join(new_dir, "labels"), exist_ok=True)
        return True


def add_tag_to_label(label_path: str, tag_name: str):
    """为 label 文件添加 # image_tag:[tag_name] 行。

    三种情况：
      1. label 文件不存在 → 新建，写入 # image_tag:[tag_name]
      2. label 存在但没有 # image_tag: 行 → 在第一行插入
      3. label 已有 # image_tag:[...] → 追加 ,tag_name

    返回: True 表示成功修改，False 表示无需修改或失败
    """
    tag_line = f"# image_tag:[{tag_name}]"
    tag_line_new = tag_line + "\n"

    if not os.path.isfile(label_path):
        # 情况 1: 文件不存在，新建
        os.makedirs(os.path.dirname(label_path), exist_ok=True)
        with open(label_path, "w", encoding="utf-8") as f:
            f.write(tag_line_new)
        return True

    with open(label_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if line.startswith(TAG_PREFIX):
            # 情况 3: 已有 tag 行，追加 tag_name
            stripped = line.rstrip("\n").rstrip("\r")
            if tag_name in stripped:
                return False  # tag 已存在，跳过
            lines[i] = stripped + f",{tag_name}]\n"
            with open(label_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            return True

    # 情况 2: 没有 tag 行，在第一行插入
    lines.insert(0, tag_line_new)
    with open(label_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return True


def find_label_path(image_path: str, annotations_root: str, version: str) -> str | None:
    """在指定 annotation 版本中查找图片对应的 label 文件路径。

    返回 label 路径（可能不存在），或 None 表示无法确定路径。
    """
    image_stem = os.path.splitext(os.path.basename(image_path))[0]
    parent_name = os.path.basename(os.path.dirname(image_path))

    labels_dir = os.path.join(annotations_root, version, "labels")

    # 结构 A: labels/<batch>/<name>.txt
    if parent_name != "images":
        return os.path.join(labels_dir, parent_name, f"{image_stem}{LABEL_EXT}")

    # 结构 B: labels/<name>.txt
    return os.path.join(labels_dir, f"{image_stem}{LABEL_EXT}")
