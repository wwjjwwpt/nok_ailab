"use client";

import { useState, useEffect } from "react";
import {
  Table, Button, Modal, Form, Input, Select, message, Space,
  Popconfirm, Tag, Card, Typography, Drawer, Switch, Row, Col
} from "antd";
import {
  PlusOutlined, EditOutlined, DeleteOutlined,
  SettingOutlined, UserAddOutlined
} from "@ant-design/icons";
import { api } from "@/lib/api";
import type { TableColumnsType } from "antd";

const { Title } = Typography;
const { TextArea } = Input;

// 紧凑表格样式
const compactTableStyle = {
  fontSize: 13,
};

const compactCellStyle = {
  padding: '8px 12px',
};

interface User {
  id: number;
  username: string;
  email: string;
  phone?: string;
  nickname: string;
  dept_id?: number;
  status: number;
  email_verified: boolean;
  phone_verified: boolean;
  created_at: string;
  roles?: any[];
}

interface Role {
  id: number;
  name: string;
  code: string;
}

interface Dept {
  id: number;
  name: string;
}

export default function UserManagementPage() {
  const [loading, setLoading] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [depts, setDepts] = useState<Dept[]>([]);
  const [messageApi, contextHolder] = message.useMessage();
  const [form] = Form.useForm();
  const [roleForm] = Form.useForm();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isRoleDrawerOpen, setIsRoleDrawerOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [userRoles, setUserRoles] = useState<number[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // 加载用户列表
  const loadUsers = async () => {
    setLoading(true);
    try {
      const response = await api.users.list({ page, page_size: pageSize });
      const data = (response.data as any);
      setUsers(data?.items || []);
      setTotal(data?.total || 0);
    } catch (error: any) {
      messageApi.error(error.response?.data?.detail || "加载用户列表失败");
    } finally {
      setLoading(false);
    }
  };

  // 加载角色列表
  const loadRoles = async () => {
    try {
      const response = await api.roles.list();
      setRoles((response.data as any) || []);
    } catch (error) {
      console.error("加载角色列表失败:", error);
    }
  };

  // 加载部门列表
  const loadDepts = async () => {
    try {
      const response = await api.departments.tree();
      setDepts((response.data as any) || []);
    } catch (error) {
      console.error("加载部门列表失败:", error);
    }
  };

  // 加载用户角色
  const loadUserRoles = async (userId: number) => {
    try {
      const response = await api.users.getRoles(userId);
      const userRoleIds = ((response.data as any) || []).map((r: any) => r.id);
      setUserRoles(userRoleIds);
    } catch (error) {
      console.error("加载用户角色失败:", error);
    }
  };

  useEffect(() => {
    loadUsers();
    loadRoles();
    loadDepts();
  }, [page, pageSize]);

  // 打开创建/编辑弹窗
  const handleOpenModal = (user?: User) => {
    setEditingUser(user || null);
    if (user) {
      form.setFieldsValue(user);
    } else {
      form.resetFields();
    }
    setIsModalOpen(true);
  };

  // 打开角色分配抽屉
  const handleOpenRoleDrawer = async (user: User) => {
    setSelectedUser(user);
    await loadUserRoles(user.id);
    setIsRoleDrawerOpen(true);
  };

  // 提交表单
  const handleSubmit = async (values: any) => {
    try {
      if (editingUser) {
        await api.users.update(editingUser.id, values);
        messageApi.success("用户更新成功");
      } else {
        await api.users.create(values);
        messageApi.success("用户创建成功");
      }
      setIsModalOpen(false);
      loadUsers();
    } catch (error: any) {
      messageApi.error(error.response?.data?.detail || "操作失败");
    }
  };

  // 删除用户
  const handleDelete = async (userId: number) => {
    try {
      await api.users.delete(userId);
      messageApi.success("用户删除成功");
      loadUsers();
    } catch (error: any) {
      messageApi.error(error.response?.data?.detail || "删除失败");
    }
  };

  // 分配角色
  const handleAssignRoles = async () => {
    if (!selectedUser) return;
    try {
      await api.users.assignRoles(selectedUser.id, userRoles);
      messageApi.success("角色分配成功");
      setIsRoleDrawerOpen(false);
      loadUsers();
    } catch (error: any) {
      messageApi.error(error.response?.data?.detail || "分配失败");
    }
  };

  const columns: TableColumnsType<User> = [
    {
      title: "ID",
      dataIndex: "id",
      width: 50,
      ellipsis: true,
    },
    {
      title: "用户名",
      dataIndex: "username",
      width: 90,
      ellipsis: true,
    },
    {
      title: "昵称",
      dataIndex: "nickname",
      width: 80,
      ellipsis: true,
    },
    {
      title: "邮箱",
      dataIndex: "email",
      width: 140,
      ellipsis: true,
      render: (email, record) => (
        <span>
          {email}
          {record.email_verified && (
            <Tag color="success" style={{ marginLeft: 4, fontSize: 10, padding: '0 4px' }}>已验证</Tag>
          )}
        </span>
      ),
    },
    {
      title: "手机号",
      dataIndex: "phone",
      width: 110,
      ellipsis: true,
      render: (phone, record) => (
        <span>
          {phone || "-"}
          {record.phone_verified && (
            <Tag color="success" style={{ marginLeft: 4, fontSize: 10, padding: '0 4px' }}>已验证</Tag>
          )}
        </span>
      ),
    },
    {
      title: "状态",
      dataIndex: "status",
      width: 60,
      render: (status) => (
        <Tag color={status === 1 ? "success" : "error"} style={{ fontSize: 10, padding: '0 4px' }}>
          {status === 1 ? "正常" : "禁用"}
        </Tag>
      ),
    },
    {
      title: "创建时间",
      dataIndex: "created_at",
      width: 140,
      render: (text) => new Date(text).toLocaleString("zh-CN", { hour12: false }),
    },
    {
      title: "操作",
      key: "action",
      width: 180,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<SettingOutlined />}
            onClick={() => handleOpenRoleDrawer(record)}
            style={{ padding: 0, fontSize: 11 }}
          >
            分配角色
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
            style={{ padding: 0, fontSize: 11 }}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除此用户吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />} style={{ padding: 0, fontSize: 11 }}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      {contextHolder}
      <Card style={{ padding: 8 }}>
        <div style={{ marginBottom: 8, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <Title level={5} style={{ margin: 0, fontSize: 14 }}>用户管理</Title>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            size="small"
            onClick={() => handleOpenModal()}
            style={{ height: 28, padding: '0 10px', fontSize: 12 }}
          >
            新增用户
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={users}
          rowKey="id"
          loading={loading}
          size="small"
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
            pageSizeOptions: ['10', '20', '50'],
            size: 'small',
          }}
          scroll={{ x: 900 }}
          style={compactTableStyle}
          rowClassName={() => 'compact-row'}
        />
      </Card>

      {/* 创建/编辑用户弹窗 */}
      <Modal
        title={editingUser ? "编辑用户" : "新增用户"}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        onOk={() => form.submit()}
        width={520}
      >
        <Form
          form={form}
          onFinish={handleSubmit}
          layout="vertical"
          initialValues={{ status: 1 }}
          size="small"
          style={{ padding: '12px 16px' }}
        >
          <Row gutter={[12, 0]}>
            <Col span={12}>
              <Form.Item
                name="username"
                label="用户名"
                rules={[
                  { required: true, message: "请输入用户名" },
                  { min: 3, max: 20, message: "用户名长度 3-20 个字符" }
                ]}
              >
                <Input placeholder="请输入用户名" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="nickname" label="昵称">
                <Input placeholder="请输入昵称" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={[12, 0]}>
            <Col span={12}>
              <Form.Item
                name="email"
                label="邮箱"
                rules={[
                  { type: "email", message: "邮箱格式不正确" }
                ]}
              >
                <Input placeholder="请输入邮箱" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="phone" label="手机号">
                <Input placeholder="请输入手机号" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={[12, 0]}>
            <Col span={12}>
              <Form.Item name="dept_id" label="部门">
                <Select placeholder="请选择部门" allowClear>
                  {depts.map((dept) => (
                    <Select.Option key={dept.id} value={dept.id}>
                      {dept.name}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="status" label="状态">
                <Select>
                  <Select.Option value={1}>正常</Select.Option>
                  <Select.Option value={0}>禁用</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          {!editingUser && (
            <Form.Item
              name="password"
              label="密码"
              rules={[
                { required: true, message: "请输入密码" },
                { min: 6, message: "密码长度至少 6 位" }
              ]}
            >
              <Input.Password placeholder="请输入密码" />
            </Form.Item>
          )}
        </Form>
      </Modal>

      {/* 分配角色抽屉 */}
      <Drawer
        title={`分配角色 - ${selectedUser?.username}`}
        placement="right"
        size="default"
        open={isRoleDrawerOpen}
        onClose={() => setIsRoleDrawerOpen(false)}
        extra={
          <Space>
            <Button size="small" onClick={() => setIsRoleDrawerOpen(false)}>取消</Button>
            <Button type="primary" size="small" onClick={handleAssignRoles}>确定</Button>
          </Space>
        }
        styles={{ body: { padding: '12px 16px' } }}
      >
        <Form form={roleForm} layout="vertical" size="small">
          <Form.Item label="选择角色">
            <Select
              mode="multiple"
              placeholder="请选择角色"
              value={userRoles}
              onChange={setUserRoles}
              style={{ width: "100%" }}
            >
              {roles.map((role) => (
                <Select.Option key={role.id} value={role.id}>
                  {role.name} ({role.code})
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Drawer>
    </>
  );
}
