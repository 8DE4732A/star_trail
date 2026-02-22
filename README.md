# Star Trails - 星轨合成工具

将多张星空照片通过最大值叠加法合成为星轨图像或视频。

![示例图像](star_trail.jpg)

![示例图像](star_trail2.jpg)

<video src="star_trail.mp4" controls width="640" height="360"></video>

## 原理

对每张输入图像的每个像素位置取最大亮度值，星星在不同时刻的位置被保留下来，最终形成连续的星轨效果。视频模式下，逐步叠加图像并将每个阶段写入视频帧，呈现星轨从无到有的生长过程。

## 安装

```bash
uv sync
```

## 使用

### 图形界面（GUI）

直接运行即可启动图形界面：

```bash
uv run python main.py
```

或显式指定：

```bash
uv run python main.py gui
```

GUI 提供以下功能：
- 选择图像目录和文件格式
- 切换图片/视频输出模式
- 配置视频帧率和总帧数
- 启用预处理选项
- 实时进度条显示

### 命令行（CLI）

工具提供 `image` 和 `video` 两个子命令。

#### 合成星轨图片

```bash
uv run python main.py image 'photos/*.jpg' -o star_trail.jpg
```

| 参数 | 说明 |
|------|------|
| `input` | 输入图像路径，支持通配符（如 `'photos/*.jpg'`） |
| `-o, --output` | 输出文件路径，默认 `star_trail.jpg` |
| `-p, --preprocess` | 启用预处理（降噪 + CLAHE 对比度增强） |
| `-t, --temp-dir` | 保存中间合成结果的目录，便于观察合成过程 |

#### 生成星轨视频

```bash
uv run python main.py video 'photos/*.jpg' -o star_trail.mp4
```

| 参数 | 说明 |
|------|------|
| `input` | 输入图像路径，支持通配符 |
| `-o, --output` | 输出视频路径，默认 `star_trail.mp4` |
| `--fps` | 视频帧率，默认 `30` |
| `--frames` | 视频总帧数，默认与输入图像数量相同 |
| `-p, --preprocess` | 启用预处理（降噪 + CLAHE 对比度增强） |

支持的视频格式：`.mp4`、`.avi`、`.mov`、`.mkv`

### 示例

合成图片：

```bash
uv run python main.py image 'input/*.jpg'
```

启用预处理并保存中间结果：

```bash
uv run python main.py image 'input/*.jpg' -o result.jpg -p -t temp/
```

生成 60fps、共 300 帧的视频：

```bash
uv run python main.py video 'input/*.jpg' -o result.mp4 --fps 60 --frames 300
```
