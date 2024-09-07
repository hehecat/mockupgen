# mockupgen
一个从截图生成3D设备模型的工具。

阅读我的文章了解[它是如何工作的](https://www.rohanmenon.com/projects/mockupgen/)!

<br>

![](https://www.rohanmenon.com/media/example.png)

从源代码安装:
```
git clone https://github.com/rmenon1008/mockupgen.git
cd mockupgen
pip install .
```

# Usage
```
mockupgen [OPTION...] screenshot_file

options:
  -h, --help            show this help message and exit
  -t TEMPLATE           模板编号、名称或标识
  -o OUTFILE            输出文件名(使用扩展名指定格式)
  -w WIDTH              输出宽度(将尝试放大)
  --crop                裁剪而不是拉伸截图以适应模板
  --rotate R            将截图逆时针旋转90度的次数
  --brightness B        屏幕亮度调整(默认: 1.0)
  --contrast C          屏幕对比度调整(默认: 1.0)
  --blur-background     对背景应用高斯模糊效果
  --blur-strength S     背景模糊强度 (范围: 3.0-51.0, 默认: 21.0)
  --list                列出可用模板
  --custom-templates PATH/URL
                        指定自定义模板目录(参见 README.md)
  --geometric-background
                        使用随机几何图形作为背景

```

# Templates
[`mockupgen-templates`](https://github.com/rmenon1008/mockupgen-templates)仓库包含`mockupgen`使用的默认模板。大多数基于[Anthony Boyd](https://www.anthonyboyd.graphics/)的出色作品。你可以使用`mockupgen --list`查看可用的模板。

## Custom templates
除了使用默认模板,你还可以通过指定`--custom-templates`来提供自己的模板。目录或URL应包含一个index.json文件,格式如下:
```jsonc
// index.json
// Note: All paths are relative to this file

// index.json
// 注意: 所有路径都相对于此文件
{
"index_version": 1.0, // 模板索引的版本
"templates": [
{
// 必填字段
"name": "Macbook Pro 16 Silver (Green Background)",
"slug": "mbp-16-silver-green", // 尝试遵循设备-尺寸-颜色-背景格式
"base_file": "base.png", // 设备模板图像
"screen_points": [ // 屏幕4个角的像素位置
[896, 224], // 从左上角开始,逆时针方向
[896, 654],
[1471, 985],
[1471, 555]
],
// 以下两个选项中必须指定一个
"mask_file": "mask.png", // 用于遮罩截图的图像(使用alpha通道)
// 或
"mask_aspect_ratio": 1.0, // 遮罩截图的宽高比(假设为矩形)
// 可选字段
"black_white_point": ["292826", "D9DCDD"], // 用于颜色校正的黑点和白点
"brightness": 1.0, // 截图的亮度调整
"contrast": 1.0 // 截图的对比度调整
},
...
]
}
```

# About
创建模型通常需要昂贵且速度缓慢的图像处理工具。虽然这些工具可以创建逼真的模型,但它们非常手动,而且对于我想创建的博客文章缩略图来说通常是过度的。

该工具使用opencv对截图进行遮罩、变形和合成到模板上。目前,它不进行任何光照或阴影效果处理。
