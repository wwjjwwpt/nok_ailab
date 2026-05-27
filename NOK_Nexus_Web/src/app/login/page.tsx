"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { message, Form, Input, Button, Card, Typography } from "antd";
import { UserOutlined, LockOutlined, LoadingOutlined, EyeOutlined, EyeInvisibleOutlined } from "@ant-design/icons";

const { Title, Text } = Typography;

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);
  const [messageApi, contextHolder] = message.useMessage();

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      console.log("开始登录:", values.username);
      const result = await login(values.username, values.password);
      console.log("登录结果:", result);
      if (result.success) {
        messageApi.success("登录成功！");
        setTimeout(() => router.push("/dashboard"), 500);
      } else {
        console.log("登录失败，显示错误:", result.error);
        messageApi.error(result.error || "登录失败，请检查账号密码");
      }
    } catch (err) {
      console.error("登录异常:", err);
      messageApi.error("登录失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {contextHolder}

      <div style={{
        minHeight: "100vh",
        display: "flex",
        backgroundColor: "#f0f2f5"
      }}>
        {/* 左侧品牌区 */}
        <div style={{
          width: "400px",
          background: "linear-gradient(180deg, #1890ff 0%, #096dd9 100%)",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "48px",
          color: "white",
          position: "relative",
          overflow: "hidden"
        }}>
          {/* 背景装饰 */}
          <div style={{
            position: "absolute",
            top: "-100px",
            right: "-100px",
            width: "200px",
            height: "200px",
            backgroundColor: "rgba(255,255,255,0.1)",
            borderRadius: "50%",
            filter: "blur(40px)"
          }} />
          <div style={{
            position: "absolute",
            bottom: "-100px",
            left: "-100px",
            width: "200px",
            height: "200px",
            backgroundColor: "rgba(255,255,255,0.15)",
            borderRadius: "50%",
            filter: "blur(40px)"
          }} />

          <div style={{ position: "relative", zIndex: 1 }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "32px" }}>
              <div style={{
                width: "40px",
                height: "40px",
                borderRadius: "8px",
                backgroundColor: "rgba(255,255,255,0.2)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center"
              }}>
                <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                </svg>
              </div>
              <span style={{ fontSize: "18px", fontWeight: 600 }}>NOK AI Lab</span>
            </div>

            <Title level={2} style={{ color: "white", marginBottom: "8px" }}>欢迎登录</Title>
            <Text style={{ color: "rgba(255,255,255,0.85)", fontSize: "14px" }}>企业级人工智能平台</Text>

            <div style={{ marginTop: "40px", display: "flex", flexDirection: "column", gap: "12px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <div style={{ width: "6px", height: "6px", borderRadius: "50%", backgroundColor: "rgba(255,255,255,0.6)" }} />
                <Text style={{ color: "rgba(255,255,255,0.85)", fontSize: "14px" }}>智能驱动</Text>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <div style={{ width: "6px", height: "6px", borderRadius: "50%", backgroundColor: "rgba(255,255,255,0.6)" }} />
                <Text style={{ color: "rgba(255,255,255,0.85)", fontSize: "14px" }}>安全可靠</Text>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <div style={{ width: "6px", height: "6px", borderRadius: "50%", backgroundColor: "rgba(255,255,255,0.6)" }} />
                <Text style={{ color: "rgba(255,255,255,0.85)", fontSize: "14px" }}>高效协同</Text>
              </div>
            </div>
          </div>
        </div>

        {/* 右侧表单区 */}
        <div style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "24px"
        }}>
          <Card style={{ width: "100%", maxWidth: "400px", boxShadow: "0 2px 8px rgba(0,0,0,0.08)" }}>
            <div style={{ marginBottom: "24px" }}>
              <Title level={3} style={{ marginBottom: "4px" }}>账号登录</Title>
              <Text type="secondary" style={{ fontSize: "14px" }}>请输入您的账号信息</Text>
            </div>

            <Form onFinish={handleSubmit} layout="vertical" size="large">
              <Form.Item
                name="username"
                label="用户名"
                rules={[{ required: true, message: "请输入用户名" }]}
              >
                <Input
                  prefix={<UserOutlined style={{ color: "#bfbfbf" }} />}
                  placeholder="请输入用户名"
                  size="large"
                />
              </Form.Item>

              <Form.Item
                name="password"
                label="密码"
                rules={[{ required: true, message: "请输入密码" }]}
              >
                <Input.Password
                  prefix={<LockOutlined style={{ color: "#bfbfbf" }} />}
                  placeholder="请输入密码"
                  size="large"
                  iconRender={visible => visible ? <EyeOutlined /> : <EyeInvisibleOutlined />}
                />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  size="large"
                  style={{
                    width: "100%",
                    height: "40px",
                    fontSize: "16px"
                  }}
                >
                  {loading ? "登录中..." : "登录"}
                </Button>
              </Form.Item>
            </Form>

            <div style={{
              textAlign: "center",
              paddingTop: "16px",
              borderTop: "1px solid #f0f0f0"
            }}>
              <Text type="secondary" style={{ fontSize: "12px" }}>默认管理员账号</Text>
              <div style={{
                marginTop: "8px",
                padding: "8px 16px",
                backgroundColor: "#f5f5f5",
                borderRadius: "4px",
                display: "inline-block"
              }}>
                <code style={{ fontSize: "12px", color: "#333" }}>admin / admin123</code>
              </div>
            </div>

            <div style={{
              textAlign: "center",
              marginTop: "16px"
            }}>
              <Text type="secondary" style={{ fontSize: "14px" }}>
                还没有账号？
              </Text>
              <Button type="link" onClick={() => router.push("/register")} style={{ padding: "0 8px" }}>
                立即注册
              </Button>
            </div>
          </Card>

          <div style={{
            position: "absolute",
            bottom: "24px",
            textAlign: "center",
            width: "100%"
          }}>
            <Text type="secondary" style={{ fontSize: "12px" }}>
              © 2025 NOK AI Lab. All rights reserved.
            </Text>
          </div>
        </div>
      </div>
    </>
  );
}
