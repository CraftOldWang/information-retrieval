"""
启动南开大学爬虫的脚本
支持设置爬取限制和日志记录
"""

import os
import sys
import argparse
from datetime import datetime
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    """启动爬虫的主函数"""
    parser = argparse.ArgumentParser(description="启动南开大学网站爬虫")

    parser.add_argument(
        "--max-items",
        type=int,
        default=1000000,
        help="最大爬取的页面数量 (默认: 1000000)",
    )

    parser.add_argument(
        "--download-delay", type=float, default=2.0, help="下载延迟，单位秒 (默认: 2.0)"
    )

    parser.add_argument(
        "--logfile",
        type=str,
        default=f'logs/crawler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
        help="日志文件路径",
    )

    parser.add_argument(
        "--loglevel",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别 (默认: INFO)",
    )

    args = parser.parse_args()

    # 创建日志目录
    log_dir = os.path.dirname(args.logfile)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 获取项目设置
    settings = get_project_settings()

    # 更新设置
    settings.update(
        {
            "CLOSESPIDER_ITEMCOUNT": args.max_items,
            "DOWNLOAD_DELAY": args.download_delay,
            "LOG_FILE": args.logfile,
            "LOG_LEVEL": args.loglevel,
            "LOG_ENABLED": True,
        }
    )

    # 配置进程日志
    logging.basicConfig(
        level=getattr(logging, args.loglevel),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.FileHandler(args.logfile), logging.StreamHandler()],
    )

    logger = logging.getLogger(__name__)
    logger.info(
        f"爬虫启动，设置为: 最大爬取数量={args.max_items}, 下载延迟={args.download_delay}秒"
    )

    # 创建爬虫进程
    process = CrawlerProcess(settings)

    # 添加爬虫
    process.crawl("nku_main")

    # 启动爬虫
    process.start()

    logger.info("爬虫已完成")


if __name__ == "__main__":
    main()
