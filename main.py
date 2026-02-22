import argparse

from star_trails import create_star_trail, create_star_trail_video


def main():
    parser = argparse.ArgumentParser(description="星轨合成工具 - 将多张星空照片合成为星轨图像或视频")
    subparsers = parser.add_subparsers(dest="command")

    # gui 子命令
    subparsers.add_parser("gui", help="启动图形界面")

    # image 子命令
    img_parser = subparsers.add_parser("image", help="合成星轨图片")
    img_parser.add_argument("input", help="输入图像路径（支持通配符，如 'input/*.jpg'）")
    img_parser.add_argument("-o", "--output", default="star_trail.jpg", help="输出文件路径（默认: star_trail.jpg）")
    img_parser.add_argument("-p", "--preprocess", action="store_true", help="启用预处理（降噪+对比度增强）")
    img_parser.add_argument("-t", "--temp-dir", default=None, help="保存中间结果的目录（不指定则不保存）")

    # video 子命令
    vid_parser = subparsers.add_parser("video", help="生成星轨合成视频")
    vid_parser.add_argument("input", help="输入图像路径（支持通配符，如 'input/*.jpg'）")
    vid_parser.add_argument("-o", "--output", default="star_trail.mp4", help="输出视频路径（默认: star_trail.mp4）")
    vid_parser.add_argument("--fps", type=int, default=30, help="视频帧率（默认: 30）")
    vid_parser.add_argument("--frames", type=int, default=None, help="视频总帧数（默认: 与输入图像数量相同）")
    vid_parser.add_argument("-p", "--preprocess", action="store_true", help="启用预处理（降噪+对比度增强）")

    args = parser.parse_args()

    if args.command is None or args.command == "gui":
        from gui import run_gui
        run_gui()
    elif args.command == "image":
        create_star_trail(
            input_path=args.input,
            output_file=args.output,
            enable_preprocess=args.preprocess,
            temp_dir=args.temp_dir,
        )
    elif args.command == "video":
        create_star_trail_video(
            input_path=args.input,
            output_file=args.output,
            fps=args.fps,
            total_frames=args.frames,
            enable_preprocess=args.preprocess,
        )


if __name__ == "__main__":
    main()
