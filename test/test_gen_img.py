#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import base64
import time
from datetime import datetime

# ============================================================================
# 配置区域
# ============================================================================
API_KEY = "sk-92UQaFsSeRLPwhbp44B33888D009425e995865652f951776"
API_URL = (
    "https://api.apiyi.com/v1beta/models/gemini-3-pro-image-preview:generateContent"
)

PROMPT = "一只可爱的小猫坐在花园里，油画风格，高清，细节丰富"
ASPECT_RATIO = "16:9"  # 可选: 1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3, 21:9, 5:4, 4:5
RESOLUTION = "2K"  # 可选: 1K, 2K, 4K
OUTPUT_FILE = f"NanoBananaPro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

# 超时配置
TIMEOUT_MAP = {"1K": 180, "2K": 300, "4K": 360}


def generate_image():
    """生成图片"""

    print(f"\n{'='*60}")
    print(f"🎨 开始生成图片")
    print(f"{'='*60}")
    print(f"📝 提示词: {PROMPT}")
    print(f"📐 宽高比: {ASPECT_RATIO}")
    print(f"🔍 分辨率: {RESOLUTION}")

    # 构建请求参数
    payload = {
        "contents": [{"parts": [{"text": PROMPT}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": ASPECT_RATIO, "imageSize": RESOLUTION},
        },
    }

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}

    # 发送请求
    print(f"\n⏳ 正在生成，预计 {TIMEOUT_MAP[RESOLUTION] // 60} 分钟...")
    start_time = time.time()

    try:
        response = requests.post(
            API_URL, json=payload, headers=headers, timeout=TIMEOUT_MAP[RESOLUTION]
        )

        elapsed = time.time() - start_time
        print(f"⏱️  实际用时: {elapsed:.1f} 秒")

        if response.status_code != 200:
            print(f"\n❌ API 错误 ({response.status_code}): {response.text}")
            return False

        # 解析响应
        data = response.json()
        image_base64 = data["candidates"][0]["content"]["parts"][0]["inlineData"][
            "data"
        ]

        # 保存图片
        image_bytes = base64.b64decode(image_base64)
        with open(OUTPUT_FILE, "wb") as f:
            f.write(image_bytes)

        print(f"\n✅ 生成成功！")
        print(f"📁 已保存至: {OUTPUT_FILE}")
        print(f"📦 文件大小: {len(image_bytes) / 1024:.1f} KB")
        return True

    except requests.Timeout:
        print(f"\n❌ 请求超时（超过 {TIMEOUT_MAP[RESOLUTION]} 秒）")
        print(f"💡 建议：尝试使用更低的分辨率（1K 或 2K）")
        return False
    except Exception as e:
        print(f"\n❌ 生成失败: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Gemini 3 Pro Image - 文本生成图片（简化版）")
    print("=" * 60)

    generate_image()

    print(f"\n{'='*60}")
    print("程序结束")
    print("=" * 60 + "\n")
