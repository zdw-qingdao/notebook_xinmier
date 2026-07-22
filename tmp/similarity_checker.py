"""
相似度检测器模块 —— 基类 + 可扩展子类。

使用方法：
    from similarity_checker import PixelDiffChecker

    checker = PixelDiffChecker(threshold=5.0)
    feat = checker.extract_features("image.png")
    if checker.compare(feat1, feat2):
        print("相似")
"""

from abc import ABC, abstractmethod

import hashlib
import cv2
import numpy as np


class BaseSimilarityChecker(ABC):
    """相似度检测器抽象基类。

    子类需要实现:
      - extract_features(image_path) -> features
      - compare(features1, features2) -> bool
      - name 属性
    """

    @abstractmethod
    def extract_features(self, image_path: str):
        """从图片路径提取特征向量，供后续比较复用。"""
        ...

    @abstractmethod
    def compare(self, features1, features2) -> bool:
        """比较两个特征向量，返回 True 表示判定为相似/重复。"""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """检测器名称，用于 JSON 报告中记录方法。"""
        ...


class PixelDiffChecker(BaseSimilarityChecker):
    """基于像素差均值的相似度检测器（与参考代码一致）。

    算法：
      1. 将图片转为灰度图并缩放到 resize（默认 32x32）
      2. 计算两张图缩放后的像素均值差（absdiff 后取 mean）
      3. 若差值 < threshold，判为相似

    配置文件中使用: "method": "pixel_diff"
    """

    def __init__(self, resize: tuple = (32, 32), threshold: float = 5.0):
        self._resize = resize
        self._threshold = threshold

    def extract_features(self, image_path: str):
        img = cv2.imread(image_path)
        if img is None:
            return None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        small = cv2.resize(gray, self._resize)
        return small.astype(np.float32)

    def compare(self, features1, features2) -> bool:
        if features1 is None or features2 is None:
            return False
        diff = np.abs(features1 - features2).mean()
        return diff < self._threshold

    @property
    def name(self) -> str:
        return "pixel_diff"

    @property
    def threshold(self) -> float:
        return self._threshold


class PixelMaxDiffChecker(BaseSimilarityChecker):
    """基于像素差最大值的相似度检测器。

    算法：
      1. 将图片转为灰度图并缩放到 resize（默认 32x32）
      2. 计算两张图缩放后所有 1024 个格子中差异最大的那个
      3. 若最大差值 < threshold，判为相似

    与 pixel_diff 的区别：
      - pixel_diff 看平均差异，允许局部有大变化但整体相近
      - pixel_max_diff 看最坏情况，只要有一个格子差异超过阈值就判为不重复

    配置文件中使用: "method": "pixel_max_diff"
    """

    def __init__(self, resize: tuple = (32, 32), threshold: float = 5.0):
        self._resize = resize
        self._threshold = threshold

    def extract_features(self, image_path: str):
        img = cv2.imread(image_path)
        if img is None:
            return None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        small = cv2.resize(gray, self._resize)
        return small.astype(np.float32)

    def compare(self, features1, features2) -> bool:
        if features1 is None or features2 is None:
            return False
        diff = np.abs(features1 - features2).max()
        return diff < self._threshold

    @property
    def name(self) -> str:
        return "pixel_max_diff"

    @property
    def threshold(self) -> float:
        return self._threshold


class ExactMatchChecker(BaseSimilarityChecker):
    """精确匹配检测器 —— 基于文件 MD5 哈希。

    算法：
      1. 读取文件原始字节，计算 MD5 哈希
      2. 哈希相同即判为完全相同

    配置文件中使用: "method": "exact"
    注意: 此方法不使用 threshold 参数，任何 threshold 值均忽略。
    """

    def __init__(self, resize: tuple = None, threshold: float = 0):
        self._threshold = None  # 不使用阈值

    def extract_features(self, image_path: str):
        try:
            with open(image_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except OSError:
            return None

    def compare(self, features1, features2) -> bool:
        if features1 is None or features2 is None:
            return False
        return features1 == features2

    @property
    def name(self) -> str:
        return "exact"

    @property
    def threshold(self):
        return self._threshold