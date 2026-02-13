"""
PerceptionEngine: 多模态特征提取层
- 视觉特征: MediaPipe Face Landmarker (EAR, MAR, 头部姿态)
- 音频特征: openSMILE eGeMAPS (响度, 音调)
- 输出格式: 严格遵循项目协议
"""

import cv2
import opensmile
import numpy as np
from datetime import datetime
import os
import time

class PerceptionEngine:
    """婉晴的感知器官 - 特征工程核心类（适配新版MediaPipe）"""
    
    def __init__(self):
        """初始化感知引擎"""
        # ---------- 视觉模块初始化（新版MediaPipe Tasks API）----------
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python.vision import FaceLandmarker, FaceLandmarkerOptions, RunningMode
        import urllib.request
        import os
        
        self.mp = mp
        
        # 下载 Face Landmarker 模型（如果不存在）
        model_url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
        model_path = os.path.join(os.path.dirname(__file__), "face_landmarker.task")
        
        if not os.path.exists(model_path):
            print("📥 下载 Face Landmarker 模型（约 2MB）...")
            urllib.request.urlretrieve(model_url, model_path)
            print("✅ 模型下载完成")
        
        # 创建人脸特征点检测器
        options = FaceLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=model_path),
            running_mode=RunningMode.IMAGE,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
            num_faces=1
        )
        self.face_landmarker = FaceLandmarker.create_from_options(options)
        
        # ---------- 音频模块初始化 ----------
        try:
            self.smile = opensmile.Smile(
                feature_set=opensmile.FeatureSet.eGeMAPSv02,
                feature_level=opensmile.FeatureLevel.Functionals,
            )
            self.audio_ready = True
        except Exception as e:
            print(f"⚠️ openSMILE初始化失败: {e}")
            print("音频特征将返回默认值")
            self.audio_ready = False
        
        # ---------- 状态变量（自适应眨眼）----------
        self.ear_history = []          # EAR历史，用于阈值计算
        self.ear_baseline = 0.3        # 正常睁眼基线
        self.ear_threshold = 0.2       # 当前眨眼阈值
        self.blink_events = []         # 眨眼时间戳列表（1分钟窗口）
        self.last_ear = 0.0            # 上一帧EAR
        self.ear_history_size = 100    # 历史窗口大小（帧数）

    def extract_visual(self, image_path):
        """
        从图片提取视觉特征
        输入: 图片路径
        输出: 符合协议的visual字典
        """
        visual = {
            "ear": 0.0,
            "mar": 0.0,
            "blink_count": 0,
            "head_pose": {
                "pitch": 0.0,
                "yaw": 0.0,
                "roll": 0.0
            }
        }
        
        if not os.path.exists(image_path):
            return visual
        
        # 读取图片
        img = cv2.imread(image_path)
        if img is None:
            return visual
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]
        
        # 转换为MediaPipe图像格式
        mp_image = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=img_rgb)
        
        # 检测人脸特征点
        detection_result = self.face_landmarker.detect(mp_image)
        
        if detection_result.face_landmarks:
            face_landmarks = detection_result.face_landmarks[0]
                    
            # 计算EAR（双眼平均）
            left_ear = self._calculate_ear(face_landmarks, [33, 160, 158, 133, 153, 144], w, h)
            right_ear = self._calculate_ear(face_landmarks, [362, 385, 387, 263, 373, 380], w, h)
            current_ear = (left_ear + right_ear) / 2.0
            visual["ear"] = round(current_ear, 4)
            
            # 计算MAR
            visual["mar"] = round(self._calculate_mar_robust(face_landmarks, w, h), 4)
            
            # 更新眨眼计数
            blink_count = self._update_blink_count(current_ear)
            visual["blink_count"] = blink_count
            
            visual["head_pose"] = self._estimate_head_pose(face_landmarks, w, h)
        
        return visual
    
    def extract_audio(self, audio_path):
        """
        从音频提取声学特征（修正版）
        """
        audio = {
            "is_speaking": False,
            "loudness": 0.0,
            "pitch_avg": 0.0
        }
        
        if not self.audio_ready or not os.path.exists(audio_path):
            return audio
        
        try:
            features = self.smile.process_file(audio_path)
            
            if 'loudness_sma3_amean' in features.columns:
                raw_loudness = float(features['loudness_sma3_amean'].iloc[0])
                # print(f"  🔊 [Audio Debug] 原始响度: {raw_loudness:.4f}")
                
                # 针对低增益麦克风优化的阈值
                if raw_loudness < 0.02:  # 只有极小的波动才算绝对静音
                    loudness_norm = 0.0
                elif raw_loudness < 0.2: # 你的 0.11 会落在这里
                    # 映射 0.02~0.2 到 0.1~0.5 之间
                    loudness_norm = 0.1 + (raw_loudness - 0.02) / 0.18 * 0.4
                else:
                    # 超过 0.2 就算大声了
                    loudness_norm = min(1.0, 0.5 + (raw_loudness - 0.2) / 0.8)
                
                audio["loudness"] = round(float(loudness_norm), 4)
                
                # 判定说话的阈值也相应下调
                # 只要原始响度大于 0.05 且有音调，就认为是在说话
                audio["is_speaking"] = raw_loudness > 0.05
            
            # 2. 处理音调 (Pitch)
            if 'F0semitoneFrom27.5Hz_sma3nz_amean' in features.columns:
                pitch_semitone = float(features['F0semitoneFrom27.5Hz_sma3nz_amean'].iloc[0])
                # 如果 pitch_semitone 为 0，说明没检测到基频（可能只是杂音）
                if pitch_semitone > 0:
                    pitch_hz = 27.5 * (2 ** (pitch_semitone / 12))
                    audio["pitch_avg"] = round(pitch_hz, 2)
                    # 双重确认：有音调才算说话
                    if audio["loudness"] > 0.1:
                        audio["is_speaking"] = True
                
        except Exception as e:
            print(f"音频特征提取失败: {e}")
        
        return audio
    
    def analyze(self, image_path=None, audio_path=None):
        perception = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "visual": {
                "ear": 0.0,
                "mar": 0.0,
                "blink_count": 0,
                "head_pose": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0}
            },
            "audio": {
                "is_speaking": False,
                "loudness": 0.0,
                "pitch_avg": 0.0
            }
        }
        
        if image_path:
            perception["visual"] = self.extract_visual(image_path)  # 这里覆盖blink_count
        
        if audio_path:
            perception["audio"] = self.extract_audio(audio_path)
        
        return perception
    
    # ---------- 私有辅助方法 ----------
    def _calculate_ear(self, landmarks, eye_idx, w, h):
        """计算眼睛纵横比 (EAR)"""
        points = []
        for idx in eye_idx:
            lm = landmarks[idx]
            points.append([lm.x * w, lm.y * h])
        points = np.array(points)
        
        ear = (np.linalg.norm(points[1] - points[5]) + 
               np.linalg.norm(points[2] - points[4])) / \
              (2.0 * np.linalg.norm(points[0] - points[3]) + 1e-6)
        return ear
    
    def _calculate_mar_robust(self, landmarks, w, h):
        """
        鲁棒性MAR计算 - 6点平均 + IQR异常值剔除
        """
       # 上唇关键点（6个）- 包含内侧点308
        upper_points = [13, 312, 308, 318, 14]  # 308重复是为了对齐
        # 下唇关键点（6个）- 包含内侧点78
        lower_points = [14, 85, 78, 314, 13]    # 78是下唇内侧
        
        vertical_dists = []
        for up, low in zip(upper_points, lower_points):
            up_pt = np.array([landmarks[up].x * w, landmarks[up].y * h])
            low_pt = np.array([landmarks[low].x * w, landmarks[low].y * h])
            dist = np.linalg.norm(up_pt - low_pt)
            vertical_dists.append(dist)
        
        # IQR异常值剔除
        if len(vertical_dists) > 0:
            q1, q3 = np.percentile(vertical_dists, [25, 75])
            iqr = q3 - q1
            valid_dists = [d for d in vertical_dists 
                        if d > q1 - 1.5 * iqr and d < q3 + 1.5 * iqr]
            vertical = np.mean(valid_dists) if valid_dists else np.mean(vertical_dists)
        else:
            vertical = 0
        
        # 嘴角水平距离（不变）
        left_pt = np.array([landmarks[61].x * w, landmarks[61].y * h])
        right_pt = np.array([landmarks[291].x * w, landmarks[291].y * h])
        horizontal = np.linalg.norm(left_pt - right_pt)
        
        mar = vertical / (horizontal + 1e-6)
        return mar
    
    def _estimate_head_pose(self, face_landmarks, w, h):
        """
        头部姿态估计
        """
        # 1. 定义标准 3D 模型点 (以鼻尖为原点)
        # 采用更符合 MediaPipe 投影比例的坐标
        model_points = np.array([
            [0.0, 0.0, 0.0],             # 1. 鼻尖
            [0.0, 38.0, -15.0],          # 152. 下巴 (向下为正)
            [-28.0, -32.0, -25.0],       # 33. 左眼外角 (向上为负, 向左为负)
            [28.0, -32.0, -25.0],        # 263. 右眼外角
            [-20.0, 18.0, -15.0],        # 61. 左嘴角
            [20.0, 18.0, -15.0]          # 291. 右嘴角
        ], dtype=np.float64)

        # 2. 提取对应的 2D 像素点 (必须是 6 个)
        image_points = np.array([
            [face_landmarks[1].x * w, face_landmarks[1].y * h],
            [face_landmarks[152].x * w, face_landmarks[152].y * h],
            [face_landmarks[33].x * w, face_landmarks[33].y * h],
            [face_landmarks[263].x * w, face_landmarks[263].y * h],
            [face_landmarks[61].x * w, face_landmarks[61].y * h],
            [face_landmarks[291].x * w, face_landmarks[291].y * h]
        ], dtype=np.float64)

        # 3. 相机内参
        focal_length = w
        center = (w/2, h/2)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype="double")
        dist_coeffs = np.zeros((4, 1))

        # 4. 求解 PnP
        success, rot_vec, trans_vec = cv2.solvePnP(
            model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
        )

        if success:
            # 将旋转向量转换为旋转矩阵
            rmat, _ = cv2.Rodrigues(rot_vec)
            
            # 计算欧拉角 (Pitch, Yaw, Roll)
            # 使用更直接的三角函数分解，避免 decomposeProjectionMatrix 的多解干扰
            sy = np.sqrt(rmat[0,0] * rmat[0,0] +  rmat[1,0] * rmat[1,0])
            singular = sy < 1e-6

            if not singular:
                pitch = np.arctan2(rmat[2,1] , rmat[2,2]) * (180/np.pi)
                yaw = np.arctan2(-rmat[2,0], sy) * (180/np.pi)
                roll = np.arctan2(rmat[1,0], rmat[0,0]) * (180/np.pi)
            else:
                pitch = np.arctan2(-rmat[1,2], rmat[1,1]) * (180/np.pi)
                yaw = np.arctan2(-rmat[2,0], sy) * (180/np.pi)
                roll = 0

            return {
                "pitch": round(float(pitch), 2),
                "yaw": round(float(yaw), 2),
                "roll": round(float(roll), 2)
            }

        return {"pitch": 0.0, "yaw": 0.0, "roll": 0.0}
    
    def _update_blink_count(self, ear):
        """
        眨眼检测：自适应阈值 + 1分钟滑动窗口
        """
        current_time = time.time()
        
        # 1. 更新EAR历史
        self.ear_history.append(ear)
        if len(self.ear_history) > self.ear_history_size:
            self.ear_history.pop(0)
        
        # 2. 动态更新阈值（每30帧）
        if len(self.ear_history) >= 30:
            recent_ears = self.ear_history[-30:]
            self.ear_baseline = np.percentile(recent_ears, 75)
            self.ear_threshold = self.ear_baseline * 0.6
        
        # 3. 眨眼检测（下降沿触发）
        if ear < self.ear_threshold and self.last_ear >= self.ear_threshold:
            self.blink_events.append(current_time)
            # print(f"👁️ 眨眼: EAR={ear:.3f}, 阈值={self.ear_threshold:.3f}")
        
        # 4. 只保留最近60秒
        self.blink_events = [t for t in self.blink_events 
                            if current_time - t <= 60]
        
        self.last_ear = ear
        return len(self.blink_events)