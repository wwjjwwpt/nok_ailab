"use client";

import { useState, useEffect } from "react";
import {
  Table, Card, Typography, Tabs, Tag, Space, Select
} from "antd";
import { FileTextOutlined, SafetyCertificateOutlined } from "@ant-design/icons";
import { api } from "@/lib/api";
import type { TableColumnsType } from "antd";

const { Title } = Typography;

interface LoginLog {
  id: number;
  user_id?: number;
  username: string;
  ip_address: string;
  user_agent: string;
  login_status: string;
  fail_reason?: string;
  login_time: string;
}

interface OperationLog {
  id: number;
  user_id?: number;
  username: string;
  module: string;
  operation: string;
  method: string;
  request_url: string;
  request_params: string;
  ip_address: string;
  duration_ms: number;
  status: string;
  error_msg?: string;
  operation_time: string;
}

export default function LogManagementPage() {
  const [loading, setLoading] = useState(false);
  const [loginLogs, setLoginLogs] = useState<LoginLog[]>([]);
  const [operationLogs, setOperationLogs] = useState<OperationLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [activeTab, setActiveTab] = useState("login");

  // 加载登录日志
  const loadLoginLogs = async () => {
    setLoading(true);
    try {
      const response = await api.logs.login({ page, page_size: pageSize });
      const data = (response.data as any) || {};
      setLoginLogs(data.items || []);
      setTotal(data.total || 0);
    } catch (error: any) {
      console.error("加载登录日志失败:", error);
    } finally {
      setLoading(false);
    }
  };

  // 加载操作日志
  const loadOperationLogs = async () => {
    setLoading(true);
    try {
      const response = await api.logs.operation({ page, page_size: pageSize });
      const data = (response.data as any) || {};
      setOperationLogs(data.items || []);
      setTotal(data.total || 0);
    } catch (error: any) {
      console.error("加载操作日志失败:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "login") {
      loadLoginLogs();
    } else {
      loadOperationLogs();
    }
  }, [activeTab, page, pageSize]);

  // 登录日志列
  const loginColumns: TableColumnsType<LoginLog> = [
    {
      title: "ID",
      dataIndex: "id",
      width: 60,
    },
    {
      title: "用户名",
      dataIndex: "username",
      width: 120,
    },
    {
      title: "登录 IP",
      dataIndex: "ip_address",
      width: 140,
    },
    {
      title: "状态",
      dataIndex: "login_status",
      width: 100,
      render: (status) => (
        <Tag color={status === "success" ? "success" : "error"}>
          {status === "success" ? "成功" : "失败"}
        </Tag>
      ),
    },
    {
      title: "失败原因",
      dataIndex: "fail_reason",
      ellipsis: true,
      render: (text) => text || "-",
    },
    {
      title: "User Agent",
      dataIndex: "user_agent",
      ellipsis: true,
      width: 300,
    },
    {
      title: "登录时间",
      dataIndex: "login_time",
      width: 160,
      render: (text) => new Date(text).toLocaleString("zh-CN"),
    },
  ];

  // 操作日志列
  const operationColumns: TableColumnsType<OperationLog> = [
    {
      title: "ID",
      dataIndex: "id",
      width: 60,
    },
    {
      title: "用户名",
      dataIndex: "username",
      width: 100,
    },
    {
      title: "模块",
      dataIndex: "module",
      width: 100,
    },
    {
      title: "操作",
      dataIndex: "operation",
      width: 100,
    },
    {
      title: "方法",
      dataIndex: "method",
      width: 80,
      render: (method) => (
        <Tag color={
          method === "GET" ? "blue" :
          method === "POST" ? "green" :
          method === "PUT" ? "orange" :
          method === "DELETE" ? "red" : "default"
        }>
          {method}
        </Tag>
      ),
    },
    {
      title: "请求 URL",
      dataIndex: "request_url",
      ellipsis: true,
      width: 200,
    },
    {
      title: "状态",
      dataIndex: "status",
      width: 80,
      render: (status) => (
        <Tag color={status === "success" ? "success" : "error"}>
          {status === "success" ? "成功" : "失败"}
        </Tag>
      ),
    },
    {
      title: "耗时 (ms)",
      dataIndex: "duration_ms",
      width: 90,
      render: (ms) => (
        <Tag color={ms > 1000 ? "red" : ms > 500 ? "orange" : "green"}>
          {ms}ms
        </Tag>
      ),
    },
    {
      title: "操作时间",
      dataIndex: "operation_time",
      width: 160,
      render: (text) => new Date(text).toLocaleString("zh-CN"),
    },
  ];

  return (
    <Card>
      <div style={{ marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>日志管理</Title>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: "login",
            label: (
              <Space>
                <SafetyCertificateOutlined />
                登录日志
              </Space>
            ),
            children: (
              <Table
                columns={loginColumns}
                dataSource={loginLogs}
                rowKey="id"
                loading={loading}
                pagination={{
                  current: page,
                  pageSize,
                  total,
                  showSizeChanger: true,
                  showTotal: (t) => `共 ${t} 条`,
                  onChange: (p, s) => {
                    setPage(p);
                    setPageSize(s);
                  },
                }}
                scroll={{ x: 1200 }}
              />
            ),
          },
          {
            key: "operation",
            label: (
              <Space>
                <FileTextOutlined />
                操作日志
              </Space>
            ),
            children: (
              <Table
                columns={operationColumns}
                dataSource={operationLogs}
                rowKey="id"
                loading={loading}
                pagination={{
                  current: page,
                  pageSize,
                  total,
                  showSizeChanger: true,
                  showTotal: (t) => `共 ${t} 条`,
                  onChange: (p, s) => {
                    setPage(p);
                    setPageSize(s);
                  },
                }}
                scroll={{ x: 1200 }}
              />
            ),
          },
        ]}
      />
    </Card>
  );
}
