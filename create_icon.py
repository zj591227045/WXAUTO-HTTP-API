"""
创建微信风格的图标
"""

import os
from PIL import Image, ImageDraw, ImageFont
import io

def create_wechat_style_icon(output_path="icons/wxauto_icon.ico", sizes=[16, 32, 48, 64, 128, 256]):
    """
    创建微信风格的图标
    
    Args:
        output_path (str): 输出路径
        sizes (list): 图标尺寸列表
    """
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 创建不同尺寸的图标
    images = []
    for size in sizes:
        # 创建一个正方形图像，绿色背景
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 绘制绿色圆形背景
        circle_margin = int(size * 0.05)
        circle_size = size - 2 * circle_margin
        circle_pos = (circle_margin, circle_margin)
        draw.ellipse(
            [circle_pos[0], circle_pos[1], 
             circle_pos[0] + circle_size, circle_pos[1] + circle_size], 
            fill=(7, 193, 96)  # 微信绿色
        )
        
        # 绘制白色"W"字母
        font_size = int(size * 0.6)
        try:
            # 尝试使用Arial字体
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            # 如果找不到Arial，使用默认字体
            font = ImageFont.load_default()
        
        # 计算文本位置，使其居中
        text = "W"
        try:
            # PIL 9.0.0及以上版本
            text_width, text_height = font.getbbox(text)[2:]
        except (AttributeError, TypeError):
            try:
                # PIL 8.0.0及以上版本
                text_width, text_height = font.getsize(text)
            except (AttributeError, TypeError):
                # 旧版本PIL
                text_width, text_height = draw.textsize(text, font=font)
        
        text_pos = (
            circle_pos[0] + (circle_size - text_width) // 2,
            circle_pos[1] + (circle_size - text_height) // 2
        )
        
        # 绘制文本
        draw.text(text_pos, text, fill=(255, 255, 255), font=font)
        
        # 添加到图像列表
        images.append(img)
    
    # 保存为ICO文件
    images[0].save(
        output_path,
        format='ICO',
        sizes=[(size, size) for size in sizes],
        append_images=images[1:]
    )
    
    print(f"图标已创建: {output_path}")
    return output_path

if __name__ == "__main__":
    create_wechat_style_icon()
