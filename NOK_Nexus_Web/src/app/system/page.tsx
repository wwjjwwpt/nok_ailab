"use client";

import { Card, Col, Row, Statistic, Typography } from "antd";
import {
  UserOutlined,
  TeamOutlined,
  SafetyOutlined,
  MenuOutlined,
  ApartmentOutlined,
  DatabaseOutlined,
  FileTextOutlined,
} from "@ant-design/icons";
import { useRouter } from "next/navigation";

const { Title, Text } = Typography;

// 系统管理模块卡片数据
const modules = [
  {
    title: "用户管理",
    description: "管理系统用户、账号和基本信息",
    icon: <UserOutlined />,
    color: "#1890ff",
    path: "/system/user",
  },
  {
    title: "角色管理",
    description: "配置系统角色和权限分配",
    icon: <TeamOutlined />,
    color: "#722ed1",
    path: "/system/role",
  },
  {
    title: "菜单管理",
    description: "配置系统菜单和导航结构",
    icon: <MenuOutlined />,
    color: "#52c41a",
    path: "/system/menu",
  },
  {
    title: "权限管理",
    description: "管理功能权限和数据权限",
    icon: <SafetyOutlined />,
    color: "#faad14",
    path: "/system/permission",
  },
  {
    title: "部门管理",
    description: "配置组织架构和部门信息",
    icon: <ApartmentOutlined />,
    color: "#13c2c2",
    path: "/system/dept",
  },
  {
    title: "数据权限",
    description: "配置数据访问范围和规则",
    icon: <DatabaseOutlined />,
    color: "#eb2f96",
    path: "/system/data-scope",
  },
  {
    title: "日志管理",
    description: "查看系统操作日志和登录日志",
    icon: <FileTextOutlined />,
    color: "#2f54eb",
    path: "/system/log",
  },
];

export default function SystemPage() {
  const router = useRouter();

  return (
    <div style={{ padding: "12px 0" }}>
      <div style={{ marginBottom: 20 }}>
        <Title level={4} style={{ margin: 0 }}>
          系统管理
        </Title>
        <Text type="secondary">配置和管理系统的各项功能模块</Text>
      </div>

      <Row gutter={[16, 16]}>
        {modules.map((module) => (
          <Col xs={24} sm={12} lg={8} xl={6} key={module.path}>
            <Card
              hoverable
              onClick={() => router.push(module.path)}
              style={{
                height: "100%",
                transition: "all 0.3s",
                cursor: "pointer",
              }}
              bodyStyle={{ padding: 16 }}
            >
              <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: 8,
                    backgroundColor: `${module.color}15`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 24,
                    color: module.color,
                    flexShrink: 0,
                  }}
                >
                  {module.icon}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <Title
                    level={5}
                    style={{ margin: "0 0 8px 0", fontSize: 15 }}
                  >
                    {module.title}
                  </Title>
                  <Text type="secondary" style={{ fontSize: 12, lineHeight: 1.5 }}>
                    {module.description}
                  </Text>
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <Card
        style={{ marginTop: 16 }}
        title="快速入门"
        size="small"
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <Text>1. <strong>用户管理</strong>：创建和管理系统用户账号</Text>
          <Text>2. <strong>角色管理</strong>：定义角色并分配权限</Text>
          <Text>3. <strong>菜单管理</strong>：配置系统导航菜单</Text>
          <Text>4. <strong>权限管理</strong>：设置功能访问权限</Text>
          <Text>5. <strong>部门管理</strong>：建立组织架构</Text>
        </div>
      </Card>
    </div>
  );
}
