import os
import urllib.request
import random
import scipy.special

import cv2
import numpy as np
from colorama import Fore, Style
from PIL import Image, ImageDraw
import random
from math import pi, sin, cos

try:
    from helpers import _r, _b, _g, _c, _m
except ImportError:
    from .helpers import _r, _b, _g, _c, _m


def _center_crop(image, aspect_ratio):
    image_aspect_ratio = image.shape[1] / image.shape[0]
    center = (image.shape[1] / 2, image.shape[0] / 2)

    if aspect_ratio > image_aspect_ratio:
        crop_width = image.shape[1]
        crop_height = crop_width / aspect_ratio
    else:
        crop_height = image.shape[0]
        crop_width = crop_height * aspect_ratio

    image = image[
        int(center[1] - crop_height / 2):int(center[1] + crop_height / 2),
        int(center[0] - crop_width / 2):int(center[0] + crop_width / 2)
    ]

    return image


def _adjust_image(image, black_point, white_point):
    a = image[:,:,3]
    image = image[:,:,0:3]

    # 将十六进制颜色转换为RGB   
    white_point = tuple(int(white_point[i:i+2], 16) for i in (4, 2, 0))
    black_point = tuple(int(black_point[i:i+2], 16) for i in (4, 2, 0))

    # 计算缩放和偏移量
    scale = (np.array(white_point) - np.array(black_point)) / 255.0
    offset = np.array(black_point)

    # 应用缩放和偏移量
    image = np.clip(image * scale + offset, 0, 255).astype(np.uint8)
    image = np.dstack((image, a))

    return image


def _read_image(image_path_or_url, fmt=cv2.IMREAD_UNCHANGED):
    if image_path_or_url.startswith('http'):
        try:
            resp = urllib.request.urlopen(image_path_or_url)
            image = np.asarray(bytearray(resp.read()), dtype="uint8")
            image = cv2.imdecode(image, fmt)
        except urllib.error.HTTPError:
            print(_r(f'Error fetching image: {image_path_or_url}'))
            exit(1)
    else:
        image = cv2.imread(image_path_or_url, fmt)
    return image


def _brightness(image, amount):
    a = image[:,:,3]
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    v = np.clip(v * amount, 0, 255).astype(np.uint8)
    final_hsv = cv2.merge((h, s, v))
    image = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
    image[:,:,3] = a
    return image


def _contrast(image, amount):
    a = image[:,:,3]
    amount = amount * 127 - 127
    f = 131*(amount + 127)/(127*(131-amount))
    image = cv2.addWeighted(image, f, image, 0, 127*(1-f))
    image[:,:,3] = a
    return image


def _over_composite(background, foreground):
    # 将前景的alpha通道转换为浮点数
    alpha_foreground = foreground[:,:,3] / 255.0

    # 调整颜色
    for color in range(0, 3):
        background[:,:,color] = alpha_foreground * foreground[:,:,color] + background[:,:,color] * (1 - alpha_foreground)
    return background


def _warn_for_different_aspect_ratios(ar1, ar2):
    if ar1 / ar2 > 1.1 or ar2 / ar1 > 1.1:
        print(_r(f'Warning: The screenshot was stretched significantly to fit the template.'))
        print(_r( "         Use --crop to crop the screenshot instead."))
        print()


def _mask_image(image, mask):
    # 将图像的alpha通道设置为遮罩的alpha通道
    image[:,:,3] = mask[:,:,3]
    return image


def save_image(image, output_file, default_name):
    # 获取扩展名(如果指定)
    extension = None
    if output_file:
        extension = os.path.splitext(output_file)[1]
        if extension:
            extension = extension[1:]

    # 保存模拟图
    if output_file:
        if extension:
            try: 
                cv2.imwrite(output_file, image, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
                print(f'保存模拟图为 {Fore.GREEN}{output_file}{Style.RESET_ALL}')
            except:
                print(_r(f'无效的输出文件扩�� "{extension}"'))
                return
        else:
            output_file = output_file + '_' + os.path.splitext(default_name)[0] + '.png'
            cv2.imwrite(output_file, image)
            print(f'保存模拟图为 {Fore.GREEN}{output_file}{Style.RESET_ALL}')
    else:
        cv2.imwrite(default_name, image)
        print(f'保存模拟图为 {Fore.GREEN}{default_name}{Style.RESET_ALL}')

def generate_mockup(mockup_dir, screenshot_file, mockup, output_width, crop, rotate, brightness, contrast, blur_background, blur_strength, geometric_background):
    # 加载截图和模板

    # 加载截图和模板
    screenshot = _read_image(screenshot_file, cv2.IMREAD_UNCHANGED)
    mockup_img_file = os.path.join(mockup_dir, mockup['base_file'])
    mockup_img = _read_image(mockup_img_file, cv2.IMREAD_UNCHANGED)

    # 确保截图和模板是有效的
    if screenshot is None:
        print(_r(f'Screenshot "{screenshot_file}" not found or invalid.'))
        return None
    if mockup_img is None:
        print(_r(f'Mockup base image "{mockup_img_file}" specified, but invalid. This is an issue with the mockup configuration.'))
        return None
    
    if screenshot.dtype == np.uint16:
        screenshot = (screenshot / 256).astype(np.uint8)
    if mockup_img.dtype == np.uint16:
        mockup_img = (mockup_img / 256).astype(np.uint8)

    if screenshot.shape[2] == 3:
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2BGRA)
    if mockup_img.shape[2] == 3:
        mockup_img = cv2.cvtColor(mockup_img, cv2.COLOR_BGR2BGRA)

    if screenshot.dtype != np.uint8:
        print(_r(f"Couldn't convert screenshot to uint8"))
        return None
    if mockup_img.dtype != np.uint8:
        print(_r(f"Couldn't convert mockup base image to uint8"))
        return None
    



    ### STEP 2: 放大和调整文件

    # 放大模板图像，如果它低于所需的输出宽度
    mockup_upscale_factor = 1
    if output_width and mockup_img.shape[0] < output_width:
        mockup_upscale_factor = output_width / mockup_img.shape[0]
        mockup_img = cv2.resize(mockup_img, (0, 0), fx=mockup_upscale_factor, fy=mockup_upscale_factor, interpolation=cv2.INTER_CUBIC)

    # 始终放大4倍以提高透视变换后的质量
    mockup_img = cv2.resize(mockup_img, (0, 0), fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    mockup_upscale_factor *= 4

    # 根据模板选项调整截图
    if "black_white_point" in mockup:
        screenshot = _adjust_image(screenshot, mockup['black_white_point'][0], mockup['black_white_point'][1])
    if "contrast" in mockup:
        screenshot = _contrast(screenshot, mockup['contrast'])
    if "brightness" in mockup:
        screenshot = _brightness(screenshot, mockup['brightness'])
    
    # 根据CLI选项调整截图
    if contrast:
        screenshot = _contrast(screenshot, contrast)
    if brightness:
        screenshot = _brightness(screenshot, brightness)
    if rotate:
        screenshot = np.rot90(screenshot, rotate)



    ### STEP 3: 遮罩截图

    if "mask_file" in mockup:
        # 加载遮罩
        mockup_mask = _read_image(os.path.join(mockup_dir, mockup['mask_file']), cv2.IMREAD_UNCHANGED)

        # 确保遮罩是有效的
        if mockup_mask is None:
            print(_r(f'Template mask image "{mockup_dir + mockup["mask_file"]}" specified, but invalid. This is an issue with the template configuration.'))
            return None

        # 将图像居中裁剪以匹配遮罩的纵横比
        if crop:
            screenshot = _center_crop(screenshot, (mockup_mask.shape[1] / mockup_mask.shape[0]))

        # 如果图像被拉伸很多，警告用户
        _warn_for_different_aspect_ratios((screenshot.shape[1] / screenshot.shape[0]), (mockup_mask.shape[1] / mockup_mask.shape[0]))

        # 将遮罩缩放到截图的大小
        mockup_mask = cv2.resize(mockup_mask, (screenshot.shape[1], screenshot.shape[0]))

        # 将遮罩应用到截图，但保留透明度
        masked_screenshot = _mask_image(screenshot, mockup_mask)

    elif "mask_aspect_ratio" in mockup:
        # 将图像居中裁剪以匹配遮罩的纵横比
        if crop:
            screenshot = _center_crop(screenshot, mockup['mask_aspect_ratio'])

        # 如果图像被拉伸很多，警告用户
        _warn_for_different_aspect_ratios((screenshot.shape[1] / screenshot.shape[0]), mockup['mask_aspect_ratio'])
        
        masked_screenshot = screenshot
    else:
        print(_r('No mask or mask aspect ratio specified in template. This is an issue with the template configuration.'))
        return None



    ### STEP 4: 透视变换截图

    # 透视变换截图到模板的透视
    mockup_points = np.array(mockup['screen_points'], dtype=np.float32) * mockup_upscale_factor

    screenshot_points = np.array([
        [0, 0],
        [0, masked_screenshot.shape[0]],
        [masked_screenshot.shape[1], masked_screenshot.shape[0]],
        [masked_screenshot.shape[1], 0]
    ], dtype=np.float32)

    matrix = cv2.getPerspectiveTransform(screenshot_points, mockup_points)

    warped_screenshot = cv2.warpPerspective(
        masked_screenshot,
        matrix,
        (mockup_img.shape[1], mockup_img.shape[0]),
        flags=cv2.INTER_NEAREST
    )

        ### STEP 5: 将截图合成到模板并调整大小

    # 将截图合成到模板
    mockup_img = _over_composite(mockup_img, warped_screenshot)

    # 缩放回4倍
    mockup_img = cv2.resize(mockup_img, (0, 0), fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)

    # 调整到指定的输出宽度
    if output_width:
        mockup_img = cv2.resize(mockup_img, (output_width, int(mockup_img.shape[0] * (output_width / mockup_img.shape[1]))), interpolation=cv2.INTER_AREA)
    
    if blur_background or geometric_background:
        if geometric_background:
            background = generate_geometric_background(mockup_img.shape[1], mockup_img.shape[0])
        else:
            # 确保 blur_strength 是奇数
            blur_strength = int(blur_strength)
            if blur_strength % 2 == 0:
                blur_strength += 1
            # 创建截图的模糊版本
            blurred_screenshot = cv2.GaussianBlur(screenshot, (blur_strength, blur_strength), 0)
            background = cv2.resize(blurred_screenshot, (mockup_img.shape[1], mockup_img.shape[0]))

        # 确保背景是不透明的
        if background.shape[2] == 3:
            background = cv2.cvtColor(background, cv2.COLOR_BGR2BGRA)
        background[:,:,3] = 255

        # 创建一个遮罩，用于平滑过渡
        mask = mockup_img[:,:,3].astype(float) / 255.0

        # 应用平滑过渡
        for c in range(3):  # 只处理RGB通道
            mockup_img[:,:,c] = mockup_img[:,:,c] * mask + background[:,:,c] * (1 - mask)

        # 单独处理alpha通道
        mockup_img[:,:,3] = mockup_img[:,:,3] * mask + background[:,:,3] * (1 - mask)

        mockup_img = np.clip(mockup_img, 0, 255).astype(np.uint8)
    return mockup_img


def generate_geometric_background(width, height):
    # 创建一个PIL图像
    im = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(im)

    # 定义网格大小，增加一些额外的行和列
    grid_size = 12
    cell_width = width // (grid_size - 2)
    cell_height = height // (grid_size - 2)

    # 创建顶点网格，扩展范围以覆盖整个图像
    vertices = []
    for i in range(grid_size + 1):
        for j in range(grid_size + 1):
            x = j * cell_width - cell_width + random.randint(-cell_width//2, cell_width//2)
            y = i * cell_height - cell_height + random.randint(-cell_height//2, cell_height//2)
            vertices.append((x, y))

    # 定义颜色渐变
    color1 = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    color2 = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    # 创建多边形并应用颜色渐变
    for i in range(grid_size):
        for j in range(grid_size):
            polygon = [
                vertices[i * (grid_size + 1) + j],
                vertices[i * (grid_size + 1) + j + 1],
                vertices[(i + 1) * (grid_size + 1) + j + 1],
                vertices[(i + 1) * (grid_size + 1) + j]
            ]

            # 计算多边形中心点的相对位置
            center_x = sum(p[0] for p in polygon) / (4 * width)
            center_y = sum(p[1] for p in polygon) / (4 * height)

            # 使用双线性插值创建更平滑的颜色渐变
            color = tuple(int(c1 * (1 - center_x) * (1 - center_y) + 
                              c2 * center_x * center_y + 
                              ((c1 + c2) / 2) * (center_x * (1 - center_y) + (1 - center_x) * center_y))
                          for c1, c2 in zip(color1, color2))

            # 绘制多边形
            draw.polygon(polygon, fill=color)

    # 将PIL图像转换为OpenCV格式
    background = np.array(im)
    background = cv2.cvtColor(background, cv2.COLOR_RGB2BGR)

    return background