#!/usr/bin/env python3
"""生成闲鱼商品主图：财会版（蓝色调）+ 老板版（红色调）"""
from PIL import Image, ImageDraw, ImageFont
import os, math

W, H = 720, 960  # 闲鱼竖图推荐
FONT_CN = '/mnt/c/Windows/Fonts/msyh.ttc'
FONT_BD = '/mnt/c/Windows/Fonts/msyhbd.ttc'

def get_font(size, bold=False):
    return ImageFont.truetype(FONT_BD if bold else FONT_CN, size)

def draw_memo(title, items, head_color, accent_color):
    img = Image.new('RGB', (W, H), '#f5f5f5')
    draw = ImageDraw.Draw(img)

    # === 顶部栏：微盘备忘录风格 ===
    draw.rectangle([0, 0, W, 52], fill='#2B2B2B')
    # 三色圆点
    for i, c in enumerate(['#FF5F57', '#FEBE2E', '#28C840']):
        draw.ellipse([16+i*22, 18, 16+i*22+14, 32], fill=c)
    draw.text((80, 14), '微盘备忘录', fill='#CCCCCC', font=get_font(16))

    # === 头像 ===
    head_size = 50
    head_x, head_y = 30, 78
    draw.ellipse([head_x, head_y, head_x+head_size, head_y+head_size], fill=head_color)
    draw.text((head_x+12, head_y+12), '洪', fill='white', font=get_font(22, bold=True))

    # === 用户信息 ===
    draw.text((head_x+head_size+14, head_y-2), '洪淳宇', fill='#222', font=get_font(18, bold=True))
    draw.text((head_x+head_size+14, head_y+24), '刚刚 · 宇守信财税', fill='#999', font=get_font(13))

    # === 标题 ===
    ty = 148
    tag_w = 80
    draw.rounded_rectangle([24, ty, 24+tag_w, ty+26], radius=4, fill=accent_color)
    draw.text((28, ty+2), '📋 工具包', fill='white', font=get_font(13))
    draw.text((24+tag_w+10, ty+1), title, fill='#1a237e', font=get_font(18, bold=True))

    # === 20个工具列表 3列 ===
    cols = 3
    cell_w = (W - 60) // cols
    cell_h = 32
    start_y = ty + 50
    start_x = 30

    # 表头
    draw.rounded_rectangle([start_x, start_y, start_x+cell_w*cols, start_y+30], radius=6, fill=accent_color)
    draw.text((start_x+10, start_y+4), '序号', fill='white', font=get_font(13))
    draw.text((start_x+90, start_y+4), '工具名称', fill='white', font=get_font(13))
    for i in range(1, cols):
        x = start_x + i*cell_w
        draw.rounded_rectangle([x, start_y, x+cell_w, start_y+30], radius=6, fill=accent_color)
        draw.text((x+10, start_y+4), f'第{i+1}列', fill='white', font=get_font(12))

    # 行数据 - 3列
    row_count = math.ceil(len(items) / cols)
    for idx, name in enumerate(items):
        col = idx % cols
        row = idx // cols
        x = start_x + col * cell_w
        y = start_y + 32 + row * cell_h
        bg = '#f8f9fa' if row % 2 == 0 else '#ffffff'
        draw.rectangle([x, y, x+cell_w-2, y+cell_h-1], fill=bg)
        num = idx+1
        draw.text((x+6, y+6), str(num), fill='#888', font=get_font(11))
        draw.text((x+32, y+6), name, fill='#333', font=get_font(11))

    # === 底部价格条 ===
    price_y = start_y + row_count * cell_h + 24
    draw.rounded_rectangle([24, price_y, W-24, price_y+70], radius=10, fill='#1a237e')
    draw.text((40, price_y+10), '💰 三人成团价', fill=(240,240,240), font=get_font(14))
    draw.text((40, price_y+34), '¥39', fill='#FFD700', font=get_font(24, bold=True))
    draw.text((160, price_y+38), '原价¥99', fill='#666', font=get_font(14))
    draw.text((280, price_y+36), '满3人退¥69 →', fill='#FFD700', font=get_font(13))

    # === 底部 ===
    draw.text((W//2-80, H-40), '—— 宇守信财税 · 洪淳宇', fill='#aaa', font=get_font(12))

    return img

# 财会版
items1 = ['税务提醒日历','税负计算器','发票管理台账','工资个税计算','社保核对表',
          '固定资产管理','存货管理表','费用报销控制','银行余额调节','现金流量表',
          '利润表分析','研发辅助账','汇算清缴辅助','稽查自查清单','凭证汇总表',
          '财务指标看板','跨年账务处理','会计凭证审核','月度结账清单','合同管理台账']
img1 = draw_memo('财会人员实务工具包 · 20个Excel', items1, '#1565c0', '#1565c0')
img1.save('/home/javis/yushouxin-group/xianyu/商品图_财会版.png')
print(f"财会版: {img1.size} ✓")

# 老板版
items2 = ['经营分析看板','盈亏平衡计算','成本费用控制','现金流预测','应收账款催收',
          '供应商评估','绩效考核评分','预算编制执行','现金流日报','投资决策测算',
          '银行贷款申请','股东分红测算','用工成本分析','税务风险预警','合同风险检查',
          '会议管理纪要','股权结构表','经营月报模板','预算执行跟踪','企业体检清单']
img2 = draw_memo('老板经营管理工具包 · 20个Excel', items2, '#c62828', '#c62828')
img2.save('/home/javis/yushouxin-group/xianyu/商品图_老板版.png')
print(f"老板版: {img2.size} ✓")
