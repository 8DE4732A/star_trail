import cv2
import numpy as np
import glob
import os


def pre_process(img):
    """对图像进行降噪和对比度增强预处理"""
    img = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    img = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)
    return img


def create_star_trail(input_path, output_file, enable_preprocess=False, temp_dir=None,
                      on_progress=None):
    """
    合成星轨图像

    :param input_path: 输入图像路径（支持通配符，如 'input/*.jpg'）
    :param output_file: 输出文件名
    :param enable_preprocess: 是否启用预处理（降噪+对比度增强）
    :param temp_dir: 临时中间结果保存目录，为 None 时不保存
    :param on_progress: 进度回调函数 (current, total) -> None
    """
    img_files = sorted(glob.glob(input_path))
    if not img_files:
        print("未找到输入图像，请检查路径是否正确")
        return

    if temp_dir is not None:
        os.makedirs(temp_dir, exist_ok=True)

    total = len(img_files)
    print(f"找到 {total} 张图像，开始合成...")

    star_trail = None

    for idx, file in enumerate(img_files):
        img = cv2.imread(file)
        if img is None:
            print(f"警告：无法读取图像 {file}，已跳过")
            continue

        if enable_preprocess:
            img = pre_process(img)

        if star_trail is None:
            star_trail = img.copy().astype(np.float32)
        else:
            star_trail = np.maximum(star_trail, img.astype(np.float32))

        print(f"已处理 {idx + 1}/{total} 张图像", end='\r')
        if on_progress:
            on_progress(idx + 1, total)

        if temp_dir is not None:
            temp = np.clip(star_trail, 0, 255).astype(np.uint8)
            cv2.imwrite(os.path.join(temp_dir, f"{idx}.jpg"), temp)

    if star_trail is None:
        print("错误：未找到有效输入图像")
        return

    star_trail = np.clip(star_trail, 0, 255).astype(np.uint8)
    cv2.imwrite(output_file, star_trail)
    print(f"\n星轨合成完成！结果已保存至 {output_file}")


FOURCC_MAP = {
    ".mp4": "mp4v",
    ".avi": "MJPG",
    ".mov": "mp4v",
    ".mkv": "XVID",
}


def create_star_trail_video(
    input_path,
    output_file,
    fps=30,
    total_frames=None,
    enable_preprocess=False,
    on_progress=None,
):
    """
    生成星轨合成过程的视频

    :param input_path: 输入图像路径（支持通配符）
    :param output_file: 输出视频文件路径
    :param fps: 视频帧率
    :param total_frames: 视频总帧数，为 None 时等于输入图像数量
    :param enable_preprocess: 是否启用预处理
    :param on_progress: 进度回调函数 (current, total) -> None
    """
    img_files = sorted(glob.glob(input_path))
    if not img_files:
        print("未找到输入图像，请检查路径是否正确")
        return

    num_images = len(img_files)
    if total_frames is None:
        total_frames = num_images

    print(f"找到 {num_images} 张图像，将生成 {total_frames} 帧 / {fps}fps 的视频...")

    # 根据输出文件扩展名选择编码器
    ext = os.path.splitext(output_file)[1].lower()
    fourcc_str = FOURCC_MAP.get(ext)
    if fourcc_str is None:
        print(f"不支持的视频格式 '{ext}'，支持的格式: {', '.join(FOURCC_MAP.keys())}")
        return
    fourcc = cv2.VideoWriter_fourcc(*fourcc_str)

    # 读取第一张图像以获取尺寸
    first_img = cv2.imread(img_files[0])
    if first_img is None:
        print(f"错误：无法读取图像 {img_files[0]}")
        return
    h, w = first_img.shape[:2]

    writer = cv2.VideoWriter(output_file, fourcc, fps, (w, h))
    if not writer.isOpened():
        print(f"错误：无法创建视频文件 {output_file}")
        return

    # 计算每一帧对应应叠加到第几张图像
    # 例如 100 张图像生成 200 帧，则每张图像产出 2 帧
    # 例如 500 张图像生成 100 帧，则每 5 张图像产出 1 帧
    frame_to_img_idx = [
        int(round((f + 1) / total_frames * num_images)) for f in range(total_frames)
    ]

    star_trail = None
    current_img_idx = 0
    frame_written = 0

    for _, target_img_idx in enumerate(frame_to_img_idx):
        # 叠加图像直到达到该帧所需的图像索引
        while current_img_idx < target_img_idx:
            img = cv2.imread(img_files[current_img_idx])
            if img is None:
                print(f"警告：无法读取图像 {img_files[current_img_idx]}，已跳过")
                current_img_idx += 1
                continue

            if enable_preprocess:
                img = pre_process(img)

            if star_trail is None:
                star_trail = img.copy().astype(np.float32)
            else:
                star_trail = np.maximum(star_trail, img.astype(np.float32))

            current_img_idx += 1

        if star_trail is not None:
            frame = np.clip(star_trail, 0, 255).astype(np.uint8)
            writer.write(frame)
            frame_written += 1

        print(f"已写入 {frame_written}/{total_frames} 帧", end='\r')
        if on_progress:
            on_progress(frame_written, total_frames)

    writer.release()
    duration = total_frames / fps
    print(f"\n视频生成完成！{total_frames} 帧，{duration:.1f} 秒，已保存至 {output_file}")