import cv2
import numpy as np
from PySide6.QtCore import Qt, QTimer, QTime
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QFileDialog, QComboBox, QLabel, QSlider

class VideoSplitterApp(QWidget):
    def __init__(self):
        super().__init__()

        # 设置界面
        self.setWindowTitle("视频分割器")
        self.setGeometry(100, 100, 640, 600)  # 调整窗口大小以适应两个视频框

        # 视频分割点存储
        self.split_points = []

        # 创建标签选择框
        self.label_combo = QComboBox(self)
        self.label_combo.addItem("镜头切换")
        self.label_combo.addItem("场景切换")
        self.label_combo.addItem("过渡")

        # 标记分割点按钮
        self.mark_button = QPushButton("标记分割点", self)
        self.mark_button.clicked.connect(self.set_split_point)

        # 切分视频按钮
        self.split_button = QPushButton("切分视频", self)
        self.split_button.clicked.connect(self.split_video)

        # 合成视频按钮
        self.combine_button = QPushButton("合成视频", self)
        self.combine_button.clicked.connect(self.combine_video)

        # 视频显示框（QLabel） 左侧视频框
        self.video_label = QLabel(self)
        self.video_label.setFixedSize(320, 480)  # 设定视频显示框大小
        self.video_label.setAlignment(Qt.AlignCenter)

        # 对比视频框 右侧视频框
        self.compare_video_label = QLabel(self)
        self.compare_video_label.setFixedSize(320, 480)  # 设定对比视频框大小
        self.compare_video_label.setAlignment(Qt.AlignCenter)

        # 视频选择按钮
        self.select_video_button = QPushButton("选择视频", self)
        self.select_video_button.clicked.connect(self.load_video_dialog)

        # 时间显示标签
        self.current_time_label = QLabel("当前时间: 00:00", self)
        self.total_time_label = QLabel("总时间: 00:00", self)

        # 滑动条
        self.progress_slider = QSlider(Qt.Horizontal, self)
        self.progress_slider.setRange(0, 100)
        self.progress_slider.sliderMoved.connect(self.update_video_position)

        # 布局设置
        video_layout = QHBoxLayout()
        video_layout.addWidget(self.video_label)  # 左侧视频框
        video_layout.addWidget(self.compare_video_label)  # 右侧对比视频框

        control_layout = QHBoxLayout()
        control_layout.addWidget(self.split_button)
        control_layout.addWidget(self.combine_button)

        slice_layout = QHBoxLayout()
        slice_layout.addWidget(QLabel("选择分割类型"))
        slice_layout.addWidget(self.label_combo)
        slice_layout.addWidget(self.mark_button)

        time_layout = QHBoxLayout()
        time_layout.addWidget(self.current_time_label)
        time_layout.addWidget(self.progress_slider)
        time_layout.addWidget(self.total_time_label)

        layout = QVBoxLayout()
        layout.addWidget(self.select_video_button)  # 视频选择按钮
        layout.addLayout(video_layout)  # 视频显示框布局
        layout.addLayout(slice_layout)
        layout.addLayout(control_layout)
        layout.addLayout(time_layout)

        self.setLayout(layout)

        # 初始化计时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

    def load_video_dialog(self):
        """打开文件选择对话框，选择视频文件"""
        video_path, _ = QFileDialog.getOpenFileName(self, "选择视频文件", "", "视频文件 (*.mp4 *.avi *.mov *.mkv)")
        if video_path:
            self.load_video(video_path)

    def load_video(self, video_path):
        """加载视频并播放"""
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
        self.update_time_labels()  # 更新总时间标签

        self.timer.start(1000 // int(self.fps))  # 每秒播放一帧

    def update_frame(self):
        """定期更新视频显示"""
        ret, frame = self.cap.read()
        if ret:
            # 将视频帧转换为 RGB 格式
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # 更新左侧视频框
            self.update_video_frame(frame, self.video_label)

            # 更新右侧对比视频框
            self.update_video_frame(frame, self.compare_video_label)

            # 更新滑动条的位置
            current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            progress = (current_frame / self.frame_count) * 100
            self.progress_slider.setValue(progress)

            # 更新当前时间标签
            current_time = current_frame / self.fps
            self.current_time_label.setText(f"当前时间: {QTime(0, 0).addSecs(int(current_time)).toString('mm:ss')}")

        else:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 重新播放视频

    def update_video_frame(self, frame, video_label):
        """更新视频显示框的内容"""
        height, width, _ = frame.shape
        qimg = QImage(frame.data, width, height, 3 * width, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        video_label.setPixmap(pixmap)

    def update_video_position(self):
        """更新视频播放位置"""
        value = self.progress_slider.value()
        frame_position = int((value / 100) * self.frame_count)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_position)

    def update_time_labels(self):
        """更新总时间标签"""
        self.total_time_label.setText(f"总时间: {QTime(0, 0).addSecs(int(self.total_time)).toString('mm:ss')}")

    def set_split_point(self):
        """记录当前播放时间并添加标签"""
        current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        current_time = current_frame / self.fps  # 当前时间（秒）
        split_label = self.label_combo.currentText()  # 获取当前选择的标签
        self.split_points.append((current_time, split_label))
        print(f"分割点：{current_time}秒, 标签：{split_label}")

    def split_video(self):
        """根据分割点切分视频"""
        if not self.split_points:
            print("没有标记分割点")
            return

        # 打开视频文件
        cap = cv2.VideoCapture(self.video_path)
        output_files = []
        for idx, (time_point, label) in enumerate(self.split_points):
            start_frame = int(time_point * self.fps)
            output_filename = f"split_{str(idx + 1).zfill(3)}_{label}.mp4"
            output_files.append(output_filename)

            # 定义输出视频的编解码器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_filename, fourcc, self.fps, (self.frame_width, self.frame_height))

            # 设置视频的起始帧
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

            # 写入片段
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)

            out.release()
            print(f"已切分：{output_filename}")

        cap.release()

    def combine_video(self):
        """合成视频"""
        if not self.split_points:
            print("没有标记分割点")
            return

        # 使用 cv2.VideoCapture 读取所有切割后的片段
        output_filename = "output_video.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_filename, fourcc, self.fps, (self.frame_width, self.frame_height))

        for idx, (time_point, label) in enumerate(self.split_points):
            split_filename = f"split_{str(idx + 1).zfill(3)}_{label}.mp4"
            cap = cv2.VideoCapture(split_filename)

            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)
            cap.release()

        out.release()
        print(f"合成完成，生成 {output_filename}")

if __name__ == "__main__":
    app = QApplication([])
    window = VideoSplitterApp()
    window.show()
    app.exec()
