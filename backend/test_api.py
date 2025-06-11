#!/usr/bin/env python3
"""
NKU搜索引擎后端API测试脚本
"""
import asyncio
import httpx
import json
from typing import Dict, Any

BASE_URL = "http://127.0.0.1:8000"

class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.token = None
        
    async def test_health_check(self):
        """测试健康检查接口"""
        print("🔍 测试健康检查...")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 健康检查通过: {data['message']}")
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return False
    
    async def test_user_registration(self):
        """测试用户注册"""
        print("👤 测试用户注册...")
        
        user_data = {
            "username": "test_user",
            "email": "test@nankai.edu.cn",
            "password": "test123456",
            "college": "计算机学院",
            "major": "计算机科学与技术",
            "grade": "2021"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/users/register",
                json=user_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data['access_token']
                print(f"✅ 用户注册成功: {data['user']['username']}")
                return True
            else:
                print(f"❌ 用户注册失败: {response.status_code}, {response.text}")
                return False
    
    async def test_user_login(self):
        """测试用户登录"""
        print("🔐 测试用户登录...")
        
        login_data = {
            "username": "test_user",
            "password": "test123456"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/users/login",
                json=login_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data['access_token']
                print(f"✅ 用户登录成功: {data['user']['username']}")
                return True
            else:
                print(f"❌ 用户登录失败: {response.status_code}, {response.text}")
                return False
    
    async def test_search_api(self):
        """测试搜索API"""
        print("🔍 测试搜索API...")
        
        search_params = {
            "q": "南开大学",
            "page": 1,
            "page_size": 10,
            "search_type": "normal"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/search/",
                params=search_params
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 搜索成功，共找到 {data['total']} 条结果")
                if data['results']:
                    print(f"   首条结果: {data['results'][0]['title']}")
                return True
            else:
                print(f"❌ 搜索失败: {response.status_code}, {response.text}")
                return False
    
    async def test_search_suggestions(self):
        """测试搜索建议API"""
        print("💡 测试搜索建议...")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/search/suggest",
                params={"q": "南开", "limit": 5}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 搜索建议成功，获得 {len(data['suggestions'])} 条建议")
                return True
            else:
                print(f"❌ 搜索建议失败: {response.status_code}, {response.text}")
                return False
    
    async def test_document_search(self):
        """测试文档搜索API"""
        print("📄 测试文档搜索...")
        
        search_params = {
            "q": "课程表",
            "page": 1,
            "page_size": 5
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/documents/",
                params=search_params
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 文档搜索成功，共找到 {data['total']} 条结果")
                return True
            else:
                print(f"❌ 文档搜索失败: {response.status_code}, {response.text}")
                return False
    
    async def test_with_auth(self):
        """测试需要认证的API"""
        if not self.token:
            print("⚠️ 跳过认证测试，未获得token")
            return False
            
        print("🔒 测试认证API...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        async with httpx.AsyncClient() as client:
            # 测试获取用户信息
            response = await client.get(
                f"{self.base_url}/api/v1/users/me",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 用户信息获取成功: {data['username']}")
                
                # 测试搜索历史
                response = await client.get(
                    f"{self.base_url}/api/v1/history/",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ 搜索历史获取成功，共 {data['total']} 条记录")
                    return True
                else:
                    print(f"❌ 搜索历史获取失败: {response.status_code}")
                    return False
            else:
                print(f"❌ 用户信息获取失败: {response.status_code}")
                return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始API测试...")
        print("=" * 50)
        
        tests = [
            self.test_health_check,
            self.test_search_api,
            self.test_search_suggestions,
            self.test_document_search,
            self.test_user_registration,
            self.test_user_login,
            self.test_with_auth,
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if await test():
                    passed += 1
                print("-" * 30)
            except Exception as e:
                print(f"❌ 测试异常: {e}")
                print("-" * 30)
        
        print("=" * 50)
        print(f"📊 测试结果: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有测试通过！")
        else:
            print("⚠️ 部分测试失败，请检查服务配置")

async def main():
    """主函数"""
    print("NKU搜索引擎后端API测试")
    print(f"测试服务器: {BASE_URL}")
    
    tester = APITester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
