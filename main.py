# 导入必要的库
from fontTools.ttLib import TTFont  # 用于处理TTF字体文件
import svgwrite  # 用于创建SVG文件
from fontTools.pens.basePen import BasePen  # 用于绘制字形路径

# 定义SVG路径绘制类，用于将字形转换为SVG路径
class SVGPathPen(BasePen):
    def __init__(self, glyphSet):
        super().__init__(glyphSet)  # 初始化父类
        self.path_data = []  # 存储路径数据
    
    def _moveTo(self, p):
        x, y = p[0], -p[1]  # 翻转y坐标以匹配SVG坐标系（TTF使用数学坐标系）
        self.path_data.append(f'M {x:.2f} {y:.2f}')  # 添加移动命令
    
    def _lineTo(self, p):
        x, y = p[0], -p[1]  # 翻转y坐标
        self.path_data.append(f'L {x:.2f} {y:.2f}')  # 添加直线命令
    
    def _curveToOne(self, p1, p2, p3):
        # 处理贝塞尔曲线，需要三个控制点
        x1, y1 = p1[0], -p1[1]
        x2, y2 = p2[0], -p2[1]
        x3, y3 = p3[0], -p3[1]
        self.path_data.append(f'C {x1:.2f} {y1:.2f} {x2:.2f} {y2:.2f} {x3:.2f} {y3:.2f}')
    
    def _closePath(self):
        self.path_data.append('Z')  # 闭合路径命令
    
    def getSVGPath(self):
        return ' '.join(self.path_data)  # 将所有路径命令组合成一个字符串

def text_to_svg(text, font_path='ttfs/local.ttf', output_file='svgs/output.svg'):
    """将文本转换为SVG文件"""
    
    # 打开并读取TTF字体文件
    font = TTFont(font_path)
    
    # 获取字符映射表，用于将Unicode字符映射到字形
    cmap = font['cmap']
    unicode_map = cmap.getBestCmap()
    
    # 获取字体单位，用于计算实际大小
    unitsPerEm = font['head'].unitsPerEm
    
    # 获取字形表和字形集
    glyf_table = font['glyf']
    glyph_set = font.getGlyphSet()
    
    # 创建SVG文档
    dwg = svgwrite.Drawing(output_file)
    dwg.attribs['class'] = 'title-svg'  # 添加CSS类名
    
    # 初始化尺寸计算变量
    total_width = 0  # 总宽度
    max_height = 0  # 最大高度
    char_info = []  # 存储字符信息
    
    # 计算字间距
    spacing = unitsPerEm // 8  # 字间距为字体单位的1/8
    total_spacing = spacing * (len(text) - 1)  # 计算所有字符间距的总和
    
    # 第一遍遍历：计算尺寸和找出最大yMax
    for char in text:
        if ord(char) in unicode_map:  # 检查字符是否在字体中
            glyph_name = unicode_map[ord(char)]
            glyph = glyf_table[glyph_name]
            
            if hasattr(glyph, 'xMin'):  # 检查字形是否有有效的边界框
                width = glyph.width if hasattr(glyph, 'width') else unitsPerEm
                height = glyph.yMax - glyph.yMin
                char_info.append((glyph, width))
                total_width += width
                max_height = max(max_height, height)
            else:
                char_info.append((None, unitsPerEm))
                total_width += unitsPerEm
    
    # 将字间距添加到总宽度
    total_width += total_spacing
    
    # 第二遍遍历：绘制字符
    x_pos = 0  # 当前x位置
    baseline = max_height
    
    for i, glyph_info in enumerate(char_info):
        glyph, width = glyph_info
        if glyph is not None:
            # 创建路径绘制器
            pen = SVGPathPen(glyph_set)
            glyph.draw(pen, glyfTable=glyf_table)
            
            if pen.path_data:  # 如果有路径数据
                path = dwg.path(
                    d=pen.getSVGPath(),
                    transform=f'translate({x_pos}, {baseline})'  # 使用max_yMax作为基线
                )
                dwg.add(path)
        
        x_pos += width
        if i < len(char_info) - 1:
            x_pos += spacing
    
    # 设置SVG的视图框
    dwg.viewbox(
        0,          # x起点
        0,          # y起点
        total_width,  # 总宽度
        max_height + spacing # 总高度
    )
    
    # 保存SVG文件
    dwg.save(pretty=True)
    return True

# 主程序入口
if __name__ == "__main__":
    text = "工具集"  # 要转换的文本
    text_to_svg(text)  # 调用转换函数
