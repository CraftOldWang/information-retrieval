#!/usr/bin/env python3
"""
调试版Elasticsearch连接测试
提供详细的错误信息和调试输出
"""


def test_es_with_debug():
    """详细调试Elasticsearch连接"""
    try:
        from elasticsearch import Elasticsearch

        print("✅ Elasticsearch包导入成功")

        # 打印连接参数
        print("🔍 连接参数:")
        print("   主机: localhost:9200")
        print("   协议: HTTP")
        print("   SSL验证: 禁用")

        # 创建连接
        es = Elasticsearch(
            ["http://localhost:9200"],
            verify_certs=False,
            ssl_show_warn=False,
            request_timeout=30,
        )
        print("✅ Elasticsearch客户端创建成功")

        # 详细的ping测试
        print("🔍 执行ping测试...")
        try:
            ping_result = es.ping()
            print(f"   Ping结果: {ping_result}")

            if ping_result:
                print("✅ Elasticsearch ping成功！")

                # 获取详细信息
                try:
                    info = es.info()
                    print("📊 集群信息:")
                    print(f"   版本: {info['version']['number']}")
                    print(f"   集群名: {info['cluster_name']}")
                    print(f"   节点名: {info['name']}")
                    print(f"   构建类型: {info['version']['build_flavor']}")

                    # 健康状态
                    health = es.cluster.health()
                    print("🏥 集群健康:")
                    print(f"   状态: {health['status']}")
                    print(f"   节点数: {health['number_of_nodes']}")
                    print(f"   数据节点: {health['number_of_data_nodes']}")
                    print(f"   活跃分片: {health['active_shards']}")

                    return True

                except Exception as info_e:
                    print(f"⚠️ 获取集群信息失败: {info_e}")
                    import traceback

                    traceback.print_exc()
                    return False

            else:
                print("❌ Elasticsearch ping失败")

                # 尝试获取更多信息
                print("🔍 尝试直接info请求...")
                try:
                    info = es.info()
                    print(f"   Info成功! 集群: {info['cluster_name']}")
                    print(f"   但ping失败，可能是配置问题")
                except Exception as info_e:
                    print(f"⚠️ Info请求也失败: {info_e}")
                    print("   可能的原因:")
                    print("   - Elasticsearch未启动")
                    print("   - 端口不正确")
                    print("   - 网络连接问题")
                    print("   - 安全配置问题")

                return False

        except Exception as ping_e:
            print(f"❌ Ping测试异常: {ping_e}")
            import traceback

            traceback.print_exc()
            return False

    except ImportError as ie:
        print(f"❌ 导入错误: {ie}")
        print("请确保已安装elasticsearch包: pip install elasticsearch")
        return False

    except Exception as e:
        print(f"❌ 未预期的错误: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_network_connectivity():
    """测试网络连接"""
    print("\n🌐 测试网络连接...")
    try:
        import requests

        # 测试HTTP连接
        response = requests.get("http://localhost:9200", timeout=10)
        print(f"✅ HTTP请求成功: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"   集群名: {data.get('cluster_name', 'N/A')}")
            print(f"   版本: {data.get('version', {}).get('number', 'N/A')}")
            return True
        else:
            print(f"❌ HTTP响应错误: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 网络连接失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🧪 Elasticsearch连接调试测试")
    print("=" * 50)

    # 检查基本环境
    import sys

    print(f"🐍 Python版本: {sys.version.split()[0]}")
    print(
        f"   虚拟环境: {'✅ 已激活' if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else '❌ 未激活'}"
    )

    # 网络连接测试
    network_ok = test_network_connectivity()

    # Elasticsearch客户端测试
    print("\n" + "=" * 50)
    es_ok = test_es_with_debug()

    # 总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"   网络连接: {'✅ 正常' if network_ok else '❌ 失败'}")
    print(f"   ES客户端: {'✅ 正常' if es_ok else '❌ 失败'}")

    if network_ok and es_ok:
        print("🎉 所有测试通过！Elasticsearch连接正常！")
        return True
    elif network_ok and not es_ok:
        print("⚠️ 网络正常但ES客户端有问题，可能是Python客户端配置问题")
        return False
    else:
        print("❌ 连接失败，请检查Elasticsearch服务状态")
        return False


if __name__ == "__main__":
    main()
