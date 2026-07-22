"""
图片去重脚本 —— 读入配置文件，递归扫盘，聚类去重，支持缓存、删除、tag 标签。

用法：
    python dedup_images.py config.json

配置文件格式见 sample.json。

流程：
  1. 解析 config，从 data_path_list 递归扫描所有图片文件夹
  2. 查找所有 data_path 的公共祖先，用于缓存目录结构
  3. 根据 cache_flag 计算 / 保存 / 加载聚类结果
  4. 若 del_flag=1，删除重复图片及 label
  5. 若 generate_tag=1，创建 annotation 版本并打 tag 标签
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime

from similarity_checker import PixelDiffChecker, PixelMaxDiffChecker, ExactMatchChecker
from label_utils import (
    find_annotations_root,
    delete_labels_for_image,
    copy_annotation_version,
    add_tag_to_label,
    find_label_path,
)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
SKIP_DIRS = {"dup_group_", "__pycache__", ".git", "annotations", "labels", "video"}


# ============================================================
#  配置解析
# ============================================================

def parse_config(config_path):
    """解析新格式的配置文件。"""
    with open(config_path, "r", encoding="utf-8-sig") as f:
        cfg = json.load(f)

    task = cfg.get("task_config", {})
    params = task.get("params", {})

    data_path_list = task.get("data_path_list", [])
    if not data_path_list:
        print("错误: data_path_list 为空")
        sys.exit(1)

    cache_flag = params.get("cache_flag", "cal_no_cache")
    if cache_flag not in ("cal_no_cache", "cal_save_cache", "load_cache"):
        print(f"错误: cache_flag 无效 —— {cache_flag}")
        sys.exit(1)

    dup_method = params.get("dup_method", "pixel_max_diff")
    dup_param = float(params.get("dup_param", 5.0))

    return {
        "data_path_list": data_path_list,
        "cache_flag": cache_flag,
        "cache_folder_path": params.get("cache_folder_path", ""),
        "del_flag": int(params.get("del_flag", 0)),
        "generate_tag": int(params.get("generate_tag", 0)),
        "parent_annotation_version": params.get("parent_annotation_version", ""),
        "annotation_name": params.get("annotation_name", ""),
        "tag_name": params.get("tag_name", ""),
        "dup_method": dup_method,
        "dup_param": dup_param,
    }


# ============================================================
#  扫盘
# ============================================================

def has_images(directory):
    try:
        for f in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, f)) and os.path.splitext(f)[1].lower() in IMAGE_EXTS:
                return True
    except OSError:
        pass
    return False


def should_skip(dirname):
    for s in SKIP_DIRS:
        if s in dirname.lower():
            return True
    return False


def find_image_folders(root_dir):
    """递归查找所有直接包含图片的文件夹（叶子截断）。"""
    folders = []
    try:
        entries = sorted(os.listdir(root_dir))
    except OSError:
        return folders
    for entry in entries:
        full = os.path.join(root_dir, entry)
        if not os.path.isdir(full) or should_skip(entry):
            continue
        if has_images(full):
            folders.append(full)
        else:
            folders.extend(find_image_folders(full))
    return folders


def scan_all(data_path_list):
    """扫描所有 data_path，返回图片文件夹列表。"""
    all_folders = []
    for dp in data_path_list:
        root = os.path.abspath(dp)
        if not os.path.isdir(root):
            print(f"  [WARN] 路径不存在，跳过: {dp}")
            continue
        folders = find_image_folders(root)
        all_folders.extend(folders)
    all_folders.sort()
    return all_folders


def find_common_ancestor(paths):
    """找到所有路径的公共祖先目录。"""
    abs_paths = [os.path.abspath(p) for p in paths if p and os.path.exists(os.path.abspath(p))]
    if not abs_paths:
        return ""
    if len(abs_paths) == 1:
        return os.path.dirname(abs_paths[0])
    return os.path.commonpath(abs_paths)


# ============================================================
#  去重核心逻辑
# ============================================================

def find_images(root_dir):
    images = []
    try:
        for f in os.listdir(root_dir):
            fpath = os.path.join(root_dir, f)
            if os.path.isfile(fpath) and os.path.splitext(f)[1].lower() in IMAGE_EXTS:
                images.append(fpath)
    except OSError:
        pass
    images.sort(key=lambda p: os.path.basename(p))
    return images


def cluster_images(image_paths, checker):
    groups, group_features = [], []
    for path in image_paths:
        feat = checker.extract_features(path)
        if feat is None:
            print(f"  [WARN] 无法读取图片，跳过: {path}")
            continue
        matched = False
        for i, gf in enumerate(group_features):
            if checker.compare(feat, gf):
                groups[i]["members"].append(path)
                matched = True
                break
        if not matched:
            groups.append({"representative": path, "members": [path]})
            group_features.append(feat)
    return groups


def get_checker(method, threshold):
    m = method.lower()
    if m == "pixel_diff":
        return PixelDiffChecker(threshold=threshold)
    elif m == "pixel_max_diff":
        return PixelMaxDiffChecker(threshold=threshold)
    elif m == "exact":
        return ExactMatchChecker()
    else:
        print(f"不支持的检测方法: {method}")
        sys.exit(1)


def run_dedup_on_folder(image_folder, checker):
    """对单个图片文件夹执行去重聚类，返回 groups 列表。"""
    images = find_images(image_folder)
    if not images:
        return None, None
    groups = cluster_images(images, checker)
    dup_groups = [g for g in groups if len(g["members"]) >= 2]
    return groups, dup_groups


# ============================================================
#  缓存系统
# ============================================================

def get_cache_path(image_folder, common_ancestor, cache_root):
    """计算图片文件夹对应的缓存路径。"""
    rel = os.path.relpath(image_folder, common_ancestor)
    return os.path.join(cache_root, rel)


def save_cache(image_folder, groups, dup_groups, checker, cache_path):
    """将聚类结果保存到缓存目录。

    groups: 全部分组（含唯一图）
    dup_groups: 仅重复分组
    """
    os.makedirs(cache_path, exist_ok=True)

    # 清理旧结果
    for name in os.listdir(cache_path):
        p = os.path.join(cache_path, name)
        if os.path.isfile(p) and os.path.splitext(name)[1].lower() in IMAGE_EXTS:
            os.remove(p)
        elif os.path.isdir(p) and name.startswith("dup_group_"):
            shutil.rmtree(p, ignore_errors=True)

    # 唯一图直接放进缓存根目录
    dup_members = set()
    for g in dup_groups:
        for mp in g["members"]:
            dup_members.add(mp)
    unique_count = 0
    for g in groups:
        if len(g["members"]) == 1:
            mp = g["members"][0]
            if mp not in dup_members:
                try:
                    shutil.copy2(mp, os.path.join(cache_path, os.path.basename(mp)))
                    unique_count += 1
                except OSError as e:
                    print(f"  [ERROR] 复制唯一图失败: {mp}: {e}")

    # 重复分组放 dup_group_* 子文件夹

    report_groups = []
    for idx, g in enumerate(dup_groups):
        sf_name = f"dup_group_{idx + 1:04d}"
        sf_path = os.path.join(cache_path, sf_name)
        os.makedirs(sf_path, exist_ok=True)
        name_counter = {}
        for mp in g["members"]:
            fname = os.path.basename(mp)
            dst = os.path.join(sf_path, fname)
            if os.path.exists(dst):
                base, ext = os.path.splitext(fname)
                name_counter[base] = name_counter.get(base, 0) + 1
                dst = os.path.join(sf_path, f"{base}_{name_counter[base]}{ext}")
            try:
                shutil.copy2(mp, dst)
            except OSError as e:
                print(f"  [ERROR] 复制失败: {mp} -> {dst}: {e}")
        report_groups.append({
            "group_id": idx + 1, "subfolder": sf_name,
            "representative": os.path.basename(g["representative"]),
            "members": [os.path.basename(m) for m in g["members"]],
            "count": len(g["members"]) - 1,
        })

    report = {
        "source_path": os.path.abspath(image_folder),
        "method": checker.name,
        "threshold": getattr(checker, "threshold", None),
        "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_images": sum(len(g["members"]) for g in dup_groups),
        "group_count": len(dup_groups),
        "duplicate_groups": report_groups,
    }
    rpt = os.path.join(cache_path, "dedup_report.json")
    with open(rpt, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


def load_cache_results(image_folder, common_ancestor, cache_root):
    """从缓存中读取聚类结果，返回 groups 列表。

    从 dedup_report.json 中读取分组信息，并与缓存 dup_group_* 文件夹中
    实际存在的图片做交集。用户从 dup_group_* 中移除的图不会被删。
    Returns: list of {"representative": path, "members": [path, ...]}
    """
    cache_path = get_cache_path(image_folder, common_ancestor, cache_root)
    report_path = os.path.join(cache_path, "dedup_report.json")
    if not os.path.isfile(report_path):
        print(f"  [WARN] 缓存报告不存在: {report_path}")
        return []

    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    source_path = report.get("source_path", image_folder)
    groups = []
    for dg in report.get("duplicate_groups", []):
        sf_name = dg.get("subfolder", "")
        rep_name = dg.get("representative", "")

        # 从缓存文件夹读实际存在的图片名（用户可能手动移除了一些）
        sf_path = os.path.join(cache_path, sf_name)
        kept_names = set()
        if os.path.isdir(sf_path):
            for f in os.listdir(sf_path):
                if os.path.isfile(os.path.join(sf_path, f)) and \
                   os.path.splitext(f)[1].lower() in IMAGE_EXTS:
                    kept_names.add(f)

        rep_path = os.path.join(source_path, rep_name) if rep_name else ""
        member_paths = []
        for mn in dg.get("members", []):
            # 只保留源图和缓存中同时存在的
            if mn not in kept_names:
                continue
            mp = os.path.join(source_path, mn)
            if os.path.isfile(mp):
                member_paths.append(mp)

        if not member_paths:
            continue

        # 如果原代表图已被移出缓存，换第一个成员作为新代表
        if rep_name not in kept_names or not os.path.isfile(rep_path):
            rep_path = member_paths[0]

        groups.append({
            "representative": rep_path,
            "members": member_paths,
        })
    return groups


# ============================================================
#  删除逻辑
# ============================================================

def delete_duplicates(all_dup_groups):
    """删除所有重复图片（非代表图）及其 label。

    all_dup_groups: [(image_folder, dup_groups), ...]
    """
    total_images = total_labels = 0
    for image_folder, dup_groups in all_dup_groups:
        aroot = find_annotations_root(image_folder)
        for g in dup_groups:
            rep = g["representative"]
            for mp in g["members"]:
                if mp == rep:
                    continue
                try:
                    os.remove(mp)
                    total_images += 1
                except OSError as e:
                    print(f"  [ERROR] 删除图片失败: {mp}: {e}")
                    continue
                if aroot:
                    for lp in delete_labels_for_image(mp, aroot, dry_run=True):
                        try:
                            os.remove(lp)
                            total_labels += 1
                        except OSError:
                            pass
    return total_images, total_labels


# ============================================================
#  Tag 标签生成
# ============================================================

def generate_tags(all_dup_groups, parent_version, annotation_name, tag_name):
    """为重复图片打 tag 标签。

    对每组重复图片，给非代表图（n-1 张）在 annotation_name 版本中添加 tag。
    """
    total_tagged = 0
    copied_roots = set()  # 避免重复复制 annotation 版本

    for image_folder, dup_groups in all_dup_groups:
        aroot = find_annotations_root(image_folder)
        if not aroot:
            print(f"  [WARN] 未找到 annotations: {image_folder}")
            continue

        # 每个 annotations root 只复制一次版本
        if aroot not in copied_roots:
            copy_annotation_version(aroot, parent_version, annotation_name)
            copied_roots.add(aroot)

        for g in dup_groups:
            rep = g["representative"]
            for mp in g["members"]:
                if mp == rep:
                    continue
                label_path = find_label_path(mp, aroot, annotation_name)
                if label_path:
                    if add_tag_to_label(label_path, tag_name):
                        total_tagged += 1
    return total_tagged


# ============================================================
#  主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="图片去重 —— 新 config 格式")
    parser.add_argument("config", help="配置文件路径 (JSON)")
    args = parser.parse_args()

    if not os.path.isfile(args.config):
        print(f"错误: 配置文件不存在 —— {args.config}")
        sys.exit(1)

    cfg = parse_config(args.config)

    print(f"配置: cache={cfg['cache_flag']}, del={cfg['del_flag']}, "
          f"tag={cfg['generate_tag']}, method={cfg['dup_method']}, "
          f"param={cfg['dup_param']}")

    # ---- 扫盘 ----
    print(f"\n扫描 data_path_list ({len(cfg['data_path_list'])} 条)...")
    image_folders = scan_all(cfg["data_path_list"])
    if not image_folders:
        print("未找到任何图片文件夹。")
        sys.exit(0)
    print(f"找到 {len(image_folders)} 个图片文件夹")

    # ---- 公共祖先 ----
    common_ancestor = find_common_ancestor(cfg["data_path_list"])
    print(f"公共祖先: {common_ancestor}")

    # ---- 缓存 / 计算 ----
    cache_flag = cfg["cache_flag"]
    cache_root = os.path.abspath(cfg["cache_folder_path"]) if cfg["cache_folder_path"] else ""

    all_dup_groups = []  # [(image_folder, dup_groups), ...]
    checker = get_checker(cfg["dup_method"], cfg["dup_param"])

    if cache_flag == "load_cache":
        if not cache_root:
            print("错误: load_cache 模式需要指定 cache_folder_path")
            sys.exit(1)
        print(f"\n从缓存加载: {cache_root}")
        for i, folder in enumerate(image_folders):
            print(f"[{i+1}/{len(image_folders)}] {folder}")
            dup_groups = load_cache_results(folder, common_ancestor, cache_root)
            if dup_groups:
                all_dup_groups.append((folder, dup_groups))
                print(f"  加载 {len(dup_groups)} 组重复")
            else:
                print(f"  无重复 / 无缓存")
    else:
        # cal_no_cache 或 cal_save_cache
        if cache_flag == "cal_save_cache" and cache_root:
            # 清理旧缓存
            if os.path.isdir(cache_root):
                print(f"清理旧缓存: {cache_root}")
                shutil.rmtree(cache_root, ignore_errors=True)
            print(f"缓存目录: {cache_root}")

        for i, folder in enumerate(image_folders):
            print(f"\n[{i+1}/{len(image_folders)}] {folder}")
            groups, dup_groups = run_dedup_on_folder(folder, checker)
            if groups is None:
                print(f"  无图片文件")
                continue
            unique = len(groups) - len(dup_groups)
            print(f"  {len(groups)} 组, {len(dup_groups)} 组重复, {unique} 唯一")
            if dup_groups:
                all_dup_groups.append((folder, dup_groups))

            if cache_flag == "cal_save_cache" and cache_root and dup_groups:
                cache_path = get_cache_path(folder, common_ancestor, cache_root)
                save_cache(folder, groups, dup_groups, checker, cache_path)

    # ---- 统计 ----
    total_groups = sum(len(dg) for _, dg in all_dup_groups)
    total_dups = sum(sum(len(g["members"]) - 1 for g in dg) for _, dg in all_dup_groups)

    # ---- Tag 标签 ----
    # 删除和打 tag 互斥：删除优先级最高，开了 del 就不打 tag
    # （图片都没了，label 没有意义，且违背有 label 必须有图片的原则）
    tagged = 0
    if cfg["generate_tag"] and not cfg["del_flag"] and all_dup_groups:
        print(f"\n{'='*60}")
        print("打 tag 标签...")
        tagged = generate_tags(
            all_dup_groups,
            cfg["parent_annotation_version"],
            cfg["annotation_name"],
            cfg["tag_name"],
        )

    # ---- 删除 ----
    del_img = del_lbl = 0
    if cfg["del_flag"] and all_dup_groups:
        print(f"\n{'='*60}")
        print("执行删除...")
        del_img, del_lbl = delete_duplicates(all_dup_groups)

    # ---- 汇总 ----
    print(f"\n{'='*60}")
    print(f"全部完成。")
    print(f"  图片文件夹:   {len(image_folders)}")
    print(f"  重复分组数:   {total_groups}")
    print(f"  重复图片数:   {total_dups}")
    if del_img or del_lbl:
        print(f"  已删图片:     {del_img}")
        print(f"  已删 label:   {del_lbl}")
    if tagged:
        print(f"  已打 tag:     {tagged}")


if __name__ == "__main__":
    main()
