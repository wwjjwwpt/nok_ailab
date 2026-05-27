"use client";

import { useState, useEffect } from "react";
import {
  Table, Button, Modal, Form, Input, message, Space,
  Popconfirm, Tag, Card, Typography
} from "antd";
import {
  PlusOutlined, EditOutlined, DeleteOutlined
} from "@ant-design/icons";
import { api } from "@/lib/api";
import type { TableColumnsType } from "antd";

const { Title } = Typography;
const { TextArea } = Input;

interface Permission {
  id: number;
  name: string;
  code: string;
  menu_ids?: number[];
  description?: string;
  status: number;
  created_at: string;
}

interface Menu {
  id: number;
  name: string;
  code: string;
  children?: Menu[];
}

export default function PermissionManagementPage() {
  const [loading, setLoading] = useState(false);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [menus, setMenus] = useState<Menu[]>([]);
  const [messageApi, contextHolder] = message.useMessage();
  const [form] = Form.useForm();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingPermission, setEditingPermission] = useState<Permission | null>(null);

  // 加载权限列表
  const loadPermissions = async () => {
    setLoading(true);
    try {
      const response = await api.permissions.list();
      setPermissions((response.data as any) || []);
      // 加载菜单列表用于显示
      const menuResponse = await api.menus.list();
      const treeData = (menuResponse.data as any) || [];
      const flattenMenus: Menu[] = [];
      const flatten = (items: Menu[]) => {
        items.forEach(item => {
          flattenMenus.push(item);
          if (item.children && item.children.length > 0) {
            flatten(item.children);
          }
        });
      };
      flatten(treeData);
      setMenus(flattenMenus);
    } catch (error: any) {
      messageApi.error(error.response?.data?.detail || "加载权限列表失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPermissions();
  }, []);

  // 打开创建/编辑弹窗
  const handleOpenModal = (permission?: Permission) => {
    setEditingPermission(permission || null);
    if (permission) {
      form.setFieldsValue({
        name: permission.name,
        code: permission.code,
        description: permission.description,
      });
    } else {
      form.resetFields();
    }
    setIsModalOpen(true);
  };

  // 提交表单
  const handleSubmit = async (values: any) => {
    try {
      if (editingPermission) {
        await api.permissions.update(editingPermission.id, values);
        messageApi.success("权限更新成功");
      } else {
        await api.permissions.create(values);
        messageApi.success("权限创建成功");
      }
      setIsModalOpen(false);
      loadPermissions();
    } catch (error: any) {
      messageApi.error(error.response?.data?.detail || "操作失败");
    }
  };

  // 删除权限
  const handleDelete = async (permissionId: number) => {
    try {
      await api.permissions.delete(permissionId);
      messageApi.success("权限删除成功");
      loadPermissions();
    } catch (error: any) {
      messageApi.error(error.response?.data?.detail || "删除失败");
    }
  };

  const columns: TableColumnsType<Permission> = [
    {
      title: "ID",
      dataIndex: "id",
      width: 60,
    },
    {
      title: "权限名称",
      dataIndex: "name",
      width: 150,
    },
    {
      title: "权限编码",
      dataIndex: "code",
      width: 180,
      render: (code) => <Tag color="blue">{code}</Tag>,
    },
    {
      title: "绑定菜单",
      dataIndex: "menu_ids",
      width: 200,
      render: (menuIds) => {
        if (!menuIds || menuIds.length === 0) return <span style={{ color: "#999" }}>未绑定菜单</span>;
        const menuNames = menuIds.map((id: number) => {
          const menu = menus.find(m => m.id === id);
          return menu ? menu.name : `ID:${id}`;
        });
        return <span>{menuNames.join(", ")}</span>;
      },
    },
    {
      title: "描述",
      dataIndex: "description",
      ellipsis: true,
    },
    {
      title: "状态",
      dataIndex: "status",
      width: 80,
      render: (status) => (
        <Tag color={status === 1 ? "success" : "error"}>
          {status === 1 ? "正常" : "禁用"}
        </Tag>
      ),
    },
    {
      title: "操作",
      key: "action",
      width: 150,
      fixed: "right",
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除此权限吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
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
      <Card>
        <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <Title level={4} style={{ margin: 0 }}>权限管理</Title>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => handleOpenModal()}
          >
            新增权限
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={permissions}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1000 }}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      {/* 创建/编辑权限弹窗 */}
      <Modal
        title={editingPermission ? "编辑权限" : "新增权限"}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        onOk={() => form.submit()}
        width={500}
      >
        <Form
          form={form}
          onFinish={handleSubmit}
          layout="vertical"
        >
          <Form.Item
            name="name"
            label="权限名称"
            rules={[{ required: true, message: "请输入权限名称" }]}
          >
            <Input placeholder="如：用户管理权限" />
          </Form.Item>

          <Form.Item
            name="code"
            label="权限编码"
            rules={[
              { required: true, message: "请输入权限编码" },
              { pattern: /^[a-z_:]+$/, message: "只能使用小写字母、下划线和冒号" }
            ]}
          >
            <Input placeholder="如：user:manage" disabled={!!editingPermission} />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <TextArea rows={3} placeholder="请输入权限描述" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
