import cv2
import numpy as np
from PySide6.QtCore import Qt, QTimer, QTime,QSettings
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QFileDialog, QComboBox, QLabel, QSlider,QProgressBar 

import cv2
import numpy as np
from PySide6.QtCore import Qt, QTimer, QTime
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QFileDialog, QComboBox, QLabel, QSlider
import json
from PySide6.QtCore import QThread, Signal
from functools import partial
from process_video import VideoProcessor

class VideoPlayer(QWidget):
    """自定义的视频播放组件，用于封装视频选择和预览框"""
    def __init__(self, parent=None, can_select_video=True):
        super().__init__(parent)

        # 视频显示框 (QLabel)
        self.video_label = QLabel(self)
        self.video_label.setFixedSize(270, 480)
        self.video_label.setAlignment(Qt.AlignCenter)

        # 播放/暂停按钮
        self.play_pause_button = QPushButton("播放", self)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)

        

        # 初始化视频状态
        self.is_playing = False
        self.cap = None

        # 当前时间标签
        self.current_time_label = QLabel("00:00", self)
        self.current_time_label.setAlignment(Qt.AlignCenter)

        # 总时间标签
        self.total_time_label = QLabel("00:00", self)
        self.total_time_label.setAlignment(Qt.AlignCenter)

        # 添加滑动条控件
        self.progress_slider = QSlider(Qt.Horizontal, self)
        self.progress_slider.setRange(0, 100)
        self.progress_slider.sliderMoved.connect(self.update_video_position)

        # 布局设置
        layout = QVBoxLayout()

            # 选择视频按钮
        self.select_video_button = QPushButton("选择视频", self)
        if can_select_video:
            self.select_video_button.isEnabled = True
            self.select_video_button.clicked.connect(self.load_video_dialog)
        else:
            self.select_video_button.isEnabled = False
        layout.addWidget(self.select_video_button)
        layout.addWidget(self.video_label)
        layout.addWidget(self.play_pause_button)

        # 当前时间、进度条、总时间布局
        time_layout = QHBoxLayout()
        time_layout.addWidget(self.current_time_label)
        time_layout.addWidget(self.progress_slider)
        time_layout.addWidget(self.total_time_label)

        layout.addLayout(time_layout)
        self.setLayout(layout)

        # 初始化定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        # 加载上次视频文件路径
        self.settings = QSettings("MyApp", "VideoPlayer")
        self.last_video_path = self.settings.value("last_video_path", "", type=str)

    def load_video_dialog(self):
        """打开文件选择对话框，选择视频文件"""
        # 如果有上次的视频路径，默认选择该路径
        video_path, _ = QFileDialog.getOpenFileName(self, "选择视频文件", self.last_video_path, "视频文件 (*.mp4 *.avi *.mov *.mkv)")
        if video_path:
            self.load_video(video_path)

    def load_video(self, video_path):
        """加载视频并准备播放"""
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            print("无法打开视频文件")
            return

        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))

        self.total_time = self.frame_count / self.fps  # 总时间（秒）

        # 更新总时间标签
        self.update_time_labels()
        self.update_frame()
        # self.timer.start(1000 // int(self.fps))  # 每秒播放一帧



    def update_frame(self):
        """定期更新视频显示"""
        if self.cap is None:
            return

        ret, frame = self.cap.read()
        if ret:
            # 将视频帧转换为 RGB 格式
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.update_video_frame(frame)

            # 更新进度条
            current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            progress_value = (current_frame / self.frame_count) * 100
            self.progress_slider.setValue(progress_value)

            # 更新当前时间标签
            current_time = current_frame / self.fps
            self.current_time_label.setText(QTime(0, 0).addSecs(int(current_time)).toString('mm:ss'))

    def update_video_frame(self, frame):
        """更新视频显示框的内容"""
        height, width, _ = frame.shape
        label_width = self.video_label.width()
        label_height = self.video_label.height()

        # 根据 QLabel 的尺寸调整视频帧的大小
        frame_resized = cv2.resize(frame, (label_width, label_height))

        # 转换为 QImage 对象
        height, width, channel = frame_resized.shape
        bytes_per_line = 3 * width
        qimg = QImage(frame_resized.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self.video_label.setPixmap(pixmap)

    def toggle_play_pause(self):
        """播放/暂停视频"""
        if self.is_playing:
            self.timer.stop()
            self.play_pause_button.setText("播放")
        else:
            self.timer.start(1000 // int(self.fps))  # 继续播放
            self.play_pause_button.setText("暂停")

        self.is_playing = not self.is_playing

    def update_video_position(self):
        """根据滑动条更新视频的播放位置"""
        if self.cap is None:
            return

        # 获取滑动条的值，转换为视频帧数
        slider_value = self.progress_slider.value()
        frame_position = int((slider_value / 100) * self.frame_count)

        # 设置视频播放的位置
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_position)

        # 更新视频显示
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.update_video_frame(frame)

            # 更新当前时间标签
            current_time = frame_position / self.fps
            self.current_time_label.setText(QTime(0, 0).addSecs(int(current_time)).toString('mm:ss'))

    def update_time_labels(self):
        """更新总时间标签"""
        self.total_time_label.setText(QTime(0, 0).addSecs(int(self.total_time)).toString('mm:ss'))

    def set_current_time(self, seconds):
        """
        设置视频播放的当前时间（秒）。
        :param seconds: 目标时间（单位：秒）
        """
        if self.cap is None:
            return
        
        # 将时间（秒）转换为帧数
        frame_position = int(seconds * self.fps)
        
        # 限制帧数范围
        frame_position = min(frame_position, self.frame_count - 1)
        
        # 设置视频播放的位置
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_position)
        
        # 更新视频显示
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.update_video_frame(frame)
        
        # 更新进度条
        progress_value = (frame_position / self.frame_count) * 100
        self.progress_slider.setValue(progress_value)

        # 更新当前时间标签
        self.current_time_label.setText(QTime(0, 0).addSecs(int(seconds)).toString('mm:ss'))

class VideoProcessingThread(QThread):
    progress_signal = Signal(int)  # 进度信号，传递百分比
    finished_signal = Signal()      # 任务完成信号

    def __init__(self, input_video_path, output_path, patch_color, opacity, frame_width,frame_height,):
        super().__init__()
        self.input_video_path = input_video_path
        self.output_path = output_path
        self.patch_color = patch_color
        self.opacity = opacity
        self.frame_width = frame_width
        self.frame_height = frame_height


        self.processor = VideoProcessor( input_video=self.input_video_path,output_video=self.output_path, patch_color=self.patch_color, opacity=self.opacity)
        
      

    def run(self):
        # 处理视频
        overlay_regions = [
            (0, 0, 150, 150),  # 左上角
            (self.frame_width - 150, 0, 150, 150),  # 右上角
            (0, self.frame_height - 150, 150, 150),  # 左下角
            (self.frame_width - 150, self.frame_height - 150, 150, 150),  # 右下角
            (self.frame_width // 2 - 75, self.frame_height // 2 - 75, 150, 150)  # 中心
        ]
        self.processor.add_overlay_to_regions(overlay_regions,process_callback=self.update_progress)
        

    def update_progress(self, progress):
        """ 更新进度条的进度 """
        self.progress_signal.emit(progress)

class VideoSplitterApp(QWidget):
    def __init__(self):
        super().__init__()

        # 设置界面
        self.setWindowTitle("视频分割器")
        self.setGeometry(100, 100, 480, 600)  # 调整窗口大小以适应两个视频框

        # 视频分割点存储
        self.split_points = []

        # 合成视频按钮
        self.process_button = QPushButton("处理视频", self)
        self.process_button.clicked.connect(lambda: self.process_video(self.video_player_1.video_path, "data/processed.mp4"))

        # 视频选择和预览组件
        self.video_player_1 = VideoPlayer(self,True)

        # 布局设置
        video_layout = QHBoxLayout()
        video_layout.addWidget(self.video_player_1)  # 第一个视频播放框
        video_layout.setAlignment(self.video_player_1, Qt.AlignCenter)

        control_layout = QHBoxLayout()
        control_layout.addWidget(self.process_button)
        self.progress_bar = QProgressBar(self)
        control_layout.addWidget(self.progress_bar)


        layout = QVBoxLayout()
        layout.addLayout(video_layout)  # 视频显示框布局
        layout.addLayout(control_layout)

        self.setLayout(layout)
    
    def process_video(self, input_video_path, output_path):
        self.process_thread = VideoProcessingThread( input_video_path=input_video_path,
            output_path=output_path,
            patch_color=(255, 240, 240),  # 浅粉色
            opacity=0.05,
            frame_width=self.video_player_1.frame_width,
            frame_height=self.video_player_1.frame_height,)
        self.process_thread.start()
        self.process_thread.progress_signal.connect(self.update_progress)
        self.process_thread.finished_signal.connect(self.on_finished)

    def update_progress(self, progress):
        """更新进度条"""
        self.progress_bar.setValue(progress)

    def on_finished(self):
        """任务完成后的处理"""
        print("视频处理已完成！")
        self.process_button.setEnabled(True)  # 处理完后重新启用按钮
        
if __name__ == "__main__":
    app = QApplication([])
    window = VideoSplitterApp()
    window.show()
    app.exec()
