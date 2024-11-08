import cv2
import os
import matplotlib.pyplot as plt

def load_and_compute_features(image_path):
    """加载基准帧并计算其 ORB 特征"""
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    orb = cv2.ORB_create()
    kp, des = orb.detectAndCompute(image, None)
    return kp, des

def extract_and_save_similar_frames(video_path, reference_des, output_folder, threshold=0.99):
    """提取视频帧并与基准帧特征进行比较，保存相似的帧"""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)  # 获取视频的帧率
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)  # 创建输出文件夹
    orb = cv2.ORB_create()
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    frame_index = 0
    saved_frame_count = 0
    match_counts = []  # 用于记录每帧的匹配点数量

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        kp, des = orb.detectAndCompute(gray_frame, None)

        # 跳过空特征帧
        if des is None:
            frame_index += 1
            match_counts.append(0)  # 无匹配点
            continue

        # 比对基准帧和当前帧的特征
        matches = bf.match(reference_des, des)
        similar_matches = [m for m in matches if m.distance < threshold * 100]
        match_counts.append(len(similar_matches))  # 记录匹配点数量

        # 如果匹配数量足够多，认为该帧与基准帧相似，保存该帧
        print(f"帧 {frame_index}：匹配数量 {len(similar_matches)}")
        if len(similar_matches) > 100:  # 调整匹配数量阈值
            current_time = frame_index / fps  # 计算时间点
            output_filename = os.path.join(output_folder, f"frame_{saved_frame_count}_{current_time:.2f}s.jpg")
            cv2.imwrite(output_filename, frame)  # 保存相似帧到文件夹
            saved_frame_count += 1
            print(f"保存相似帧：{output_filename}，时间点：{current_time:.2f} 秒")

        frame_index += 1

    cap.release()
    print(f"共保存了 {saved_frame_count} 张相似帧到文件夹 '{output_folder}'")

    # 绘制匹配度图表
    plt.figure(figsize=(12, 6))
    plt.plot(match_counts, label="Matching Points per Frame", color='b')
    plt.xlabel("Frame Index")
    plt.ylabel("Matching Points")
    plt.title("Frame-by-Frame Matching Points with Reference Frame")
    plt.legend()
    plt.grid(True)
    plt.show()

# 主程序
video_path = 'input.mp4'
reference_image_path = 'input.png'  # 基准帧的路径
output_folder = 'similar_frames'  # 保存相似帧的文件夹

# 1. 加载基准帧并计算其特征
ref_kp, ref_des = load_and_compute_features(reference_image_path)

# 2. 逐帧提取视频帧并比对，保存相似帧并绘制匹配度图
extract_and_save_similar_frames(video_path, ref_des, output_folder)
