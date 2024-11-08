import cv2
import numpy as np

class VideoProcessor:
    def __init__(self, input_video: str, output_video: str, patch_color=(173, 216, 230), opacity=0.3):
        """
        初始化视频处理类。

        参数：
        - input_video (str): 输入视频的路径。
        - output_video (str): 输出视频的路径。
        - patch_color (tuple): 贴片颜色，格式为(B, G, R)。
        - opacity (float): 贴片透明度，0到1之间的值。
        """
        self.input_video = input_video
        self.output_video = output_video
        self.patch_color = patch_color
        self.opacity = opacity

    def add_overlay_to_regions(self, overlay_regions, process_callback=None):
        """
        在视频的自定义区域添加浅色透明贴片，并处理视频。

        参数：
        - overlay_regions (list of tuples): 每个元组包含区域坐标(x, y, width, height)。
        - process_callback (function): 进度回调函数，用于更新进度条。
        """
        process_callback = process_callback or (lambda x: None)
        
        # 打开输入视频
        cap = cv2.VideoCapture(self.input_video)
        if not cap.isOpened():
            raise ValueError(f"无法打开输入视频: {self.input_video}")

        # 获取视频的属性
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # 定义输出视频编写器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.output_video, fourcc, fps, (frame_width, frame_height))

        # 逐帧处理视频
        current_frame = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # 遍历每个自定义区域，叠加透明贴片
            for region in overlay_regions:
                x, y, width, height = region

                # 创建一个带透明度的贴片，尺寸为区域大小
                patch = np.full((height, width, 3), self.patch_color, dtype=np.uint8)
                patch = cv2.addWeighted(patch, self.opacity, np.zeros_like(patch), 1 - self.opacity, 0)

                if x + width <= frame_width and y + height <= frame_height:
                    frame[y:y+height, x:x+width] = cv2.addWeighted(
                        frame[y:y+height, x:x+width], 1 - self.opacity, patch, self.opacity, 0)

            # 写入处理后的帧到输出视频
            out.write(frame)
            current_frame += 1

            # 计算进度并通过回调更新进度
            progress = (current_frame / frame_count) * 100
            process_callback(progress)

        # 释放资源
        cap.release()
        out.release()
        print("视频处理完成，输出路径:", self.output_video)
