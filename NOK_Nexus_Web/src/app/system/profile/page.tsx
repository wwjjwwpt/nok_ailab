"use client";

import { Card, Descriptions, Tag, Space, Divider, Typography } from "antd";
import { UserOutlined, MailOutlined, PhoneOutlined, TeamOutlined, SafetyOutlined, ClockCircleOutlined } from "@ant-design/icons";
import { useAuth } from "@/hooks/useAuth";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { User } from "@/types";

const { Title } = Typography;

export default function ProfilePage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [userData, setUserData] = useState<User | null>(null);

  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const response = await api.auth.getCurrentUser();
        const data = (response.data?.data as any)?.user || response.data?.data;
        setUserData(data as unknown as User);
      } catch (error) {
        console.error("获取用户信息失败:", error);
      } finally {
        setLoading(false);
      }
    };

    if (!user) {
      fetchUserInfo();
    } else {
      setUserData(user);
      setLoading(false);
    }
  }, [user]);

  if (loading) {
    return <div style={{ padding: 24, textAlign: "center" }}>加载中...</div>;
  }

  if (!userData) {
    return <div style={{ padding: 24, textAlign: "center" }}>无法获取用户信息</div>;
  }

  return (
    <div style={{ padding: "12px" }}>
      <Card>
        <div style={{ marginBottom: 24 }}>
          <Title level={4}>个人信息</Title>
        </div>

        <Descriptions
          column={{ xxl: 2, xl: 2, lg: 2, md: 2, sm: 1, xs: 1 }}
          bordered
          size="middle"
        >
          <Descriptions.Item
            label={
              <Space>
                <UserOutlined />
                <span>用户名</span>
              </Space>
            }
            span={2}
          >
            {userData.username}
          </Descriptions.Item>

          <Descriptions.Item
            label={
              <Space>
                <UserOutlined />
                <span>昵称</span>
              </Space>
            }
            span={2}
          >
            {userData.nickname || "-"}
          </Descriptions.Item>

          <Descriptions.Item
            label={
              <Space>
                <MailOutlined />
                <span>邮箱</span>
              </Space>
            }
            span={2}
          >
            {userData.email || "-"}
          </Descriptions.Item>

          <Descriptions.Item
            label={
              <Space>
                <PhoneOutlined />
                <span>手机号</span>
              </Space>
            }
            span={2}
          >
            {userData.phone || "-"}
          </Descriptions.Item>

          <Descriptions.Item
            label={
              <Space>
                <TeamOutlined />
                <span>部门</span>
              </Space>
            }
            span={2}
          >
            {userData.dept_id ? `部门 ID: ${userData.dept_id}` : "-"}
          </Descriptions.Item>

          <Descriptions.Item
            label={
              <Space>
                <SafetyOutlined />
                <span>状态</span>
              </Space>
            }
          >
            <Tag color={userData.status === 1 ? "success" : "default"}>
              {userData.status === 1 ? "启用" : "禁用"}
            </Tag>
          </Descriptions.Item>

          <Descriptions.Item
            label={
              <Space>
                <ClockCircleOutlined />
                <span>创建时间</span>
              </Space>
            }
          >
            {userData.created_at
              ? new Date(userData.created_at).toLocaleString("zh-CN")
              : "-"}
          </Descriptions.Item>
        </Descriptions>

        <Divider />

        <div style={{ marginTop: 16 }}>
          <Title level={5}>账号 ID：{userData.id}</Title>
        </div>
      </Card>
    </div>
  );
}
