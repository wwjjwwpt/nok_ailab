"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { message, Form, Input, Button, Card, Typography, Row, Col, Space } from "antd";
import { UserOutlined, LockOutlined, MailOutlined, SafetyOutlined, LoadingOutlined } from "@ant-design/icons";
import { api } from "@/lib/api";

const { Title, Text } = Typography;

export default function RegisterPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [messageApi, contextHolder] = message.useMessage();
  const [sendCodeLoading, setSendCodeLoading] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [form] = Form.useForm();

  const handleSendCode = async () => {
    try {
      const email = form.getFieldValue("email");
      if (!email) {
        messageApi.warning("请先输入邮箱");
        form.validateFields(["email"]);
        return;
      }

      // 邮箱格式验证
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) {
        messageApi.warning("请输入正确的邮箱格式");
        return;
      }

      setSendCodeLoading(true);
      await api.auth.sendVerifyCode({ email, type: "verify" });
      messageApi.success("验证码已发送到您的邮箱");

      // 开始倒计时
      setCountdown(60);
      const timer = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (error: any) {
      messageApi.error(error.response?.data?.detail || "发送失败");
    } finally {
      setSendCodeLoading(false);
    }
  };

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      await api.auth.register({
        username: values.username,
        password: values.password,
        email: values.email,
        verify_code: values.verify_code,
      });

      messageApi.success("注册成功！");
      setTimeout(() => router.push("/login"), 1000);
    } catch (error: any) {
      messageApi.error(error.response?.data?.detail || "注册失败，请稍后重试");
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
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "#f0f2f5",
        padding: "24px"
      }}>
        <Card style={{ width: "100%", maxWidth: "440px", boxShadow: "0 2px 8px rgba(0,0,0,0.08)" }}>
          <div style={{ marginBottom: "24px", textAlign: "center" }}>
            <Title level={2} style={{ marginBottom: "4px" }}>用户注册</Title>
            <Text type="secondary">创建您的账号</Text>
          </div>

          <Form
            form={form}
            onFinish={handleSubmit}
            layout="vertical"
            size="large"
            autoComplete="off"
          >
            <Form.Item
              name="username"
              label="用户名"
              rules={[
                { required: true, message: "请输入用户名" },
                { min: 3, max: 20, message: "用户名长度 3-20 个字符" }
              ]}
            >
              <Input
                prefix={<UserOutlined style={{ color: "#bfbfbf" }} />}
                placeholder="请输入用户名"
              />
            </Form.Item>

            <Form.Item
              name="email"
              label="邮箱"
              rules={[
                { required: true, message: "请输入邮箱" },
                { type: "email", message: "邮箱格式不正确" }
              ]}
            >
              <Input
                prefix={<MailOutlined style={{ color: "#bfbfbf" }} />}
                placeholder="请输入邮箱"
              />
            </Form.Item>

            <Form.Item
              name="verify_code"
              label="验证码"
              rules={[
                { required: true, message: "请输入验证码" },
                { len: 6, message: "验证码为 6 位数字" }
              ]}
            >
              <Space.Compact style={{ width: "100%" }}>
                <Input
                  prefix={<SafetyOutlined style={{ color: "#bfbfbf" }} />}
                  placeholder="请输入验证码"
                  style={{ flex: 1 }}
                />
                <Button
                  type="default"
                  onClick={handleSendCode}
                  disabled={countdown > 0}
                  style={{ minWidth: "110px" }}
                >
                  {countdown > 0 ? `${countdown}s 后重试` : "获取验证码"}
                </Button>
              </Space.Compact>
            </Form.Item>

            <Form.Item
              name="password"
              label="密码"
              rules={[
                { required: true, message: "请输入密码" },
                { min: 6, message: "密码长度至少 6 位" }
              ]}
            >
              <Input.Password
                prefix={<LockOutlined style={{ color: "#bfbfbf" }} />}
                placeholder="请输入密码"
              />
            </Form.Item>

            <Form.Item
              name="confirm_password"
              label="确认密码"
              dependencies={["password"]}
              rules={[
                { required: true, message: "请确认密码" },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue("password") === value) {
                      return Promise.resolve();
                    }
                    return Promise.reject(new Error("两次输入的密码不一致"));
                  },
                }),
              ]}
            >
              <Input.Password
                prefix={<LockOutlined style={{ color: "#bfbfbf" }} />}
                placeholder="请再次输入密码"
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
                {loading ? "注册中..." : "注册"}
              </Button>
            </Form.Item>
          </Form>

          <div style={{
            textAlign: "center",
            paddingTop: "16px",
            borderTop: "1px solid #f0f0f0"
          }}>
            <Text type="secondary" style={{ fontSize: "14px" }}>
              已有账号？
            </Text>
            <Button type="link" onClick={() => router.push("/login")} style={{ padding: "0 8px" }}>
              立即登录
            </Button>
          </div>
        </Card>
      </div>
    </>
  );
}
