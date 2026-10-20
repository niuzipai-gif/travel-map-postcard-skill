# Travel Map Postcard · 旅行地图明信片

识别旅行照片中的地点，核对真实地理数据，在天空、海面等负空间叠加独立透明地图层，制作克制的杂志风明信片。默认保留照片的完整画幅、原始尺寸、主体、色彩和光影。

An agent skill for researched location identification and editorial map overlays. The host agent handles vision and research; deterministic Python helpers retrieve and draw real geography without regenerating the photograph.

## 安装

需要 Python 3.10+、Pillow，以及具备看图、联网检索和本地执行能力的 agent。无需图像生成 API 密钥；地图接口由使用者选择并遵守其服务条款。

**直接安装：** 从 [Releases](https://github.com/niuzipai-gif/travel-map-postcard-skill/releases/latest) 下载 `travel-map-postcard-v0.1.0.zip`，解压后将 `travel-map-postcard` 文件夹放入 agent 的 skills 目录。Codex 通常为 `~/.codex/skills/`；Windows 通常为 `%USERPROFILE%\.codex\skills\`。如果已有同名 skill，先备份再替换。

在解压得到的 skill 文件夹内安装依赖：

```bash
python -m pip install -r requirements.txt
```

**从源码安装：** 克隆本仓库，将 `skills/travel-map-postcard/` 复制到上述 skills 目录，再安装其中的 `requirements.txt`。

字体使用本机已获许可的字体，不随包分发。当地语言标题需要覆盖相应字形；缺字会明确报错，可通过 `--font` 指定兼容字体。

## 使用

附上旅行照片并输入：

> 使用 $travel-map-postcard 把这张旅行照片做成克制的杂志风地图明信片。先自动识别并核对地点，使用真实地图；完整保留原片，用独立透明图层合成。主标题使用当地语言，小标题使用英语。地图顺着背景光微微发光，重要位置的真实线条更亮一些，避开主体和文字。没有准确 GPS 就标大致区域。交付成品和地图透明层。

可以补充地点线索、偏好的配色或已知机位。当地标与机位不一致时分别记录；地点歧义会影响地图选择时，agent 会询问必要线索。识别结果是有来源支持的推断，不是精确相机定位。

## 视觉与交付

- 地图来自真实道路、海岸、建筑轮廓或步道；保持北向向上和等比投影，不编造等高线、路线或坐标。
- 重要轮廓与核心主路更清楚，外围细节更轻；可根据原片光源方向设置柔和微光。标题与主体留出空间。
- 主标题优先使用当地名称和文字，英语作为小标题；一组照片保持相近的标题节奏和层次。
- 交付原始显示尺寸的无损 `postcard.png`、全画幅透明 `map-overlay.png`，以及配置、来源、哈希与验收结果。原始文件不覆盖。
- 默认合成验证覆盖透明层之外及指定保护区域的像素不变，并检查合成结果可被独立重建。另行授权的照片修复属于不同处理，不宣称仍满足原片像素不变。

纯线稿可独立使用。可选的真实航拍与建筑实拍符号分别保留图层，按来源记录地理范围或地标位置。微调重点实景时可以只适配该实景的透明度，保持线稿和源 RGB 不变。建筑实拍符号明确为不按地图比例的标记。

日本 GSI 小范围航拍有内置下载器；其他地区需要适合且有来源的影像，不承诺全球高清覆盖。背景同色相纹理化为可选处理，只作用于影像图层，并记录处理方式。参见 [微光与实景](skills/travel-map-postcard/references/glow-and-aerial.md)。

## 脚本与资料

从 skill 文件夹运行：

```bash
python scripts/postcard.py inspect /path/to/photo.jpg
python scripts/postcard.py render --photo /path/to/photo.jpg --map /path/to/map.json --config /path/to/composition.json --out /path/to/new-version
python scripts/postcard.py verify --photo /path/to/photo.jpg --out /path/to/new-version
```

Windows 如遇默认编码问题可使用 `python -X utf8`。取数前阅读 [地图来源](skills/travel-map-postcard/references/maps.md)；配置字段与示例见 [配置说明](skills/travel-map-postcard/references/config.md)。下载有范围限制和本地缓存；不向地图服务上传原照片。

## 验证与范围

在仓库根目录运行：

```bash
python -m unittest discover -s tests -v
```

40 项测试使用合成数据，无需私人照片或实际网络请求。四张实际旅行照片的本地制作与验收记录摘要见 [TESTING.md](TESTING.md)。自动检查证明的是技术行为，视觉质量与地点判断需要另行核对。

Windows 已实际验证；macOS/Linux 字体查找有实现，但未在这两个系统上实际验证。没有独立视觉定位模型、DEM/等高线生成器或通用高清修复模块。公共地图服务不保证生产可用性。CMYK 或带透明通道的照片输入会明确拒绝。

## 许可与隐私

代码和文档采用 [MIT](LICENSE)。照片、字体、地图及航拍数据遵守各自许可；OSM 数据为 ODbL，输出保留相应署名与许可链接。航拍和实拍符号另需保留来源、编辑说明及其许可要求。

公开包仅含通用说明、代码和合成测试。用户照片、实际作品、地图下载缓存、私人坐标及密钥均不随仓库或安装包发布。
