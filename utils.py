import os
from dotenv import dotenv_values


def load_env():
    # 自动搜索加载 .env 文件
    return dotenv_values()


if __name__ == "__main__":
    load_env()
