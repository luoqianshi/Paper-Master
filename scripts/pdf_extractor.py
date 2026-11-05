#!/usr/bin/env python3
"""Compatibility entry point; all skills use the shared paper asset directory."""
import argparse
import json
from pathlib import Path
from paper_assets import ROOT, paper_dir, prepare, check, review_sheet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf_path')
    parser.add_argument('--paper', help='复用同一论文的稳定目录名；默认 PDF 文件名')
    parser.add_argument('--output-dir', help='兼容参数，仅接受 assets/paper-imgs/<paper>')
    parser.add_argument('--dpi', type=int, default=200)
    parser.add_argument('--render-pages', action='store_true', help='生成逐页核验对照页')
    parser.add_argument('--fallback-blind-crop', action='store_true', help='兼容旧调用；未定位项进入逐图补提队列')
    parser.add_argument('--clean', action='store_true', help='已停用；禁止清空共享素材')
    args = parser.parse_args()
    if args.clean:
        parser.error('--clean 已停用；请用 paper_assets.py extract --asset ID --force 逐图重提')
    paper = args.paper or (Path(args.output_dir).name if args.output_dir else Path(args.pdf_path).stem)
    try:
        if args.output_dir and Path(args.output_dir).resolve() != paper_dir(paper).resolve():
            raise ValueError('输出必须为 assets/paper-imgs/<paper>；所有 SKILL 共用该目录')
        data = prepare(paper, args.pdf_path, dpi=args.dpi)
        print(json.dumps(check(data), ensure_ascii=False, indent=2))
        if args.render_pages:
            print(review_sheet(data))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
