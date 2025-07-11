#!/usr/bin/env python3
"""
User Management 主入口

統一包裝用戶註冊、登入、查詢功能，支援 OOP 調用與 CLI 測試。
符合 Google Clean Code 原則。
"""

from user_service import UserService
from typing import Optional, Dict
import argparse
import sys

class UserManager:
    """用戶管理 OOP 入口"""
    def __init__(self):
        self.service = UserService()

    def register(self, username: str, password: str, email: str) -> Dict:
        """用戶註冊"""
        return self.service.register_user(username, password, email)

    def login(self, username: str, password: str) -> Dict:
        """用戶登入"""
        return self.service.login_user(username, password)

    def query_user(self, user_id: str) -> Dict:
        """用戶查詢"""
        return self.service.get_user_by_id(user_id)


def main():
    parser = argparse.ArgumentParser(description="User Management CLI")
    subparsers = parser.add_subparsers(dest="command")

    # 註冊
    reg_parser = subparsers.add_parser("register", help="註冊新用戶")
    reg_parser.add_argument("--username", required=True)
    reg_parser.add_argument("--password", required=True)
    reg_parser.add_argument("--email", required=True)

    # 登入
    login_parser = subparsers.add_parser("login", help="用戶登入")
    login_parser.add_argument("--username", required=True)
    login_parser.add_argument("--password", required=True)

    # 查詢
    query_parser = subparsers.add_parser("query", help="查詢用戶")
    query_parser.add_argument("--user_id", required=True)

    args = parser.parse_args()
    manager = UserManager()

    if args.command == "register":
        result = manager.register(args.username, args.password, args.email)
        print(result)
    elif args.command == "login":
        result = manager.login(args.username, args.password)
        print(result)
    elif args.command == "query":
        result = manager.query_user(args.user_id)
        print(result)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 