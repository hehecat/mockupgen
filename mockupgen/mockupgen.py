import os
import json
import urllib.request

from colorama import init as colorama_init
from colorama import Fore, Style

try:
    from helpers import _r, _b, _g, _c, _m, ColoredArgParser
    from image_processing import generate_mockup, save_image
except ImportError:
    from .helpers import _r, _b, _g, _c, _m, ColoredArgParser
    from .image_processing import generate_mockup, save_image


colorama_init()

DEFAULT_TEMPLATE_DIR = "https://raw.githubusercontent.com/rmenon1008/mockupgen-templates/main"

def get_valid_template(mockups, mockup):
    if not mockup:
        return None
    if mockup.isnumeric():
        mockup = int(mockup)
        if mockup > 0 and mockup <= len(mockups):
            selected = mockups[mockup - 1]
            return selected
    else:
        for m in mockups:
            if m['name'].lower() == mockup.lower() or m['slug'].lower() == mockup.lower():
                return m
    print(_r('Invalid template selection'))
    print()
    return None

def get_template_index(templates_path_or_url):
    if templates_path_or_url.startswith('http'):
        index_url = templates_path_or_url.rstrip('/') + '/index.json'
        try:
            with urllib.request.urlopen(index_url) as f:
                try:
                    template_index = json.load(f)
                except json.JSONDecodeError:
                    print(_r(f'Error parsing template index: {index_url}'))
                    exit(1)
        except urllib.error.HTTPError:
            print(_r(f'Error fetching template index: {index_url}'))
            exit(1)
    else:
        index_path = os.path.join(templates_path_or_url, 'index.json')
        try:
            with open(index_path, 'r') as f:
                try:
                    template_index = json.load(f)
                except json.JSONDecodeError:
                    print(_r(f'Error parsing template index: {index_path}'))
                    exit(1)
        except (NotADirectoryError, FileNotFoundError):
            print(_r(f'Error loading template index: {index_path}'))
            exit(1)
    version = template_index.get('index_version', "unspecified")
    return template_index["templates"], version, templates_path_or_url

def print_template_list(template_list):
    # 按类别分组模板
    categories = {}
    for template in template_list:
        category = template.get('category', 'Uncategorized')
        if category not in categories:
            categories[category] = []
        categories[category].append(template)
    
    # 打印模板
    i = 1
    for category in categories:
        print(_b(category+":"))
        for template in categories[category]:
            print(f"  {i}. {template['name']}")
            i += 1

def main():
    # 解析参数
    parser = ColoredArgParser(description='在设备框架中模拟一个或多个截图', prog='mockupgen')
    parser.add_argument('screenshots', metavar="SCREENSHOT", nargs='+', type=str, help='一个或多个截图文件路径(支持通配符)')
    parser.add_argument('-t', metavar="TEMPLATE", help='模板编号、名称或标识')
    parser.add_argument('-o', metavar="OUTFILE", type=str, default=None, help='输出文件名(使用扩展名指定格式)')
    parser.add_argument('-w', metavar="WIDTH", type=int, default=None, help='输出宽度(将尝试放大)')
    parser.add_argument('--crop', action='store_true', help='裁剪而不是拉伸截图以适应模板', default=False)
    parser.add_argument('--rotate', metavar="R", type=int, default=0, help='将截图逆时针旋转90度的次数')
    parser.add_argument('--brightness', metavar="B", type=float, default=1.0, help='屏幕亮度调整(默认: 1.0)')
    parser.add_argument('--contrast', metavar="C", type=float, default=1.0, help='屏幕对比度调整(默认: 1.0)')
    parser.add_argument('--blur-background', action='store_true', help='对背景应用高斯模糊效果', default=False)
    parser.add_argument('--blur-strength', metavar="S", type=float, default=21.0, help='背景模糊强度 (范围: 3.0-51.0, 默认: 21.0)')
    parser.add_argument('--list', action='store_true', help='列出可用模板', default=False)
    parser.add_argument('--custom-templates', metavar="PATH/URL", type=str, default=None, help='指定自定义模板目录(参见 README.md)')
    parser.add_argument('--geometric-background', action='store_true', help='使用随机几何图形作为背景', default=False)
    args = parser.parse_args()

    # 接受模板 URL 或路径
    if args.custom_templates:
        template_list, template_version, template_dir = get_template_index(args.custom_templates)
        print(f'使用自定义模板目录: {_b(args.custom_templates)} (版本 {_b(template_version)})')
    else:
        template_list, template_version, template_dir = get_template_index(DEFAULT_TEMPLATE_DIR)
        print(f'使用 {_b("mockupgen-templates")} (版本 {_b(template_version)})')

    # 如果请求,列出模板
    if args.list:
        print_template_list(template_list)
        exit(0)

    # 处理通配符并获取所有匹配的文件
    import glob
    screenshot_files = []
    for pattern in args.screenshots:
        screenshot_files.extend(glob.glob(pattern))

    # 确保至少有一个截图存在
    if not screenshot_files:
        print(_r('未找到匹配的截图文件'))
        print()
        parser.print_help()
        exit(1)

    # 获取模板
    template = get_valid_template(template_list, args.t)
    while not template:
        print_template_list(template_list)
        template = get_valid_template(template_list, input(f'{_m("选择一个: ")}'))

    print()
    print(f'使用模板 {_b(template["name"])} - {_b(template["slug"])}')

    if 'author' in template:
        print(f'模板创建者 {_g(template["author"])}')
    if 'backlink' in template:
        print(f'原始模板: {_g(template["backlink"])}')
    print()

    # 处理每个截图
    for screenshot in screenshot_files:
        if not os.path.isfile(screenshot):
            print(_r(f'截图未找到: {screenshot}'))
            continue

        print(f'正在处理截图: {_b(screenshot)}')

        # 生成模拟图
        generated_mockup = generate_mockup(template_dir, screenshot, template, args.w, args.crop, args.rotate, args.brightness, args.contrast, args.blur_background, args.blur_strength, args.geometric_background)
        if generated_mockup is None:
            print(_r(f'生成模拟图时出错: {screenshot}'))
            continue

        default_name = os.path.splitext(os.path.basename(screenshot))[0] + '_mockup.png'
        save_image(generated_mockup, args.o, default_name)

        print()

if __name__ == '__main__':
    main()
