"use client";

import { useState, useEffect } from "react";
import {
  Table, Button, Modal, Form, Input, Select, message, Space,
  Popconfirm, Tag, Card, Typography, Drawer, Tree, Divider, Checkbox
} from "antd";
import {
  PlusOutlined, EditOutlined, DeleteOutlined, SettingOutlined
} from "@ant-design/icons";
import { api } from "@/lib/api";
import type { TableColumnsType } from "antd";
import type { DataNode } from "antd/es/tree";
import type { CheckboxChangeEvent } from "antd/es/checkbox";

const { Title } = Typography;
const { TextArea } = Input;

interface Role {
  id: number;
  name: string;
  code: string;
  description?: string;
  is_system: boolean;
  status: number;
  created_at: string;
}

interface Menu {
  id: number;
  name: string;
  code: string;
  parent_id: number;
  children?: Menu[];
}

interface Permission {
  id: number;
  name: string;
  code: string;
  menu_id: number;
}

export default function RoleManagementPage() {
  const [loading, setLoading] = useState(false);
  const [roles, setRoles] = useState<Role[]>([]);
  const [messageApi, contextHolder] = message.useMessage();
  const [form] = Form.useForm();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);

  const [menus, setMenus] = useState<Menu[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [checkedMenus, setCheckedMenus] = useState<number[]>([]);
  const [checkedPermissions, setCheckedPermissions] = useState<number[]>([]);
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([]);

  // 加载角色列表
  const loadRoles = async () => {
    setLoading(true);
    try {
      const response = await api.roles.list();
      setRoles((response.data as any) || []);
    } catch (error: any) {
      messageApi.error(error.response?.data?.detail || "加载角色列表失败");
    } finally {
      setLoading(false);
    }
  };

  // 加载所有菜单
  const loadMenus = async () => {
    try {
      const response = await api.menus.list();
      const menuData = (response.data?.data as any) || [];
      setMenus(menuData);
      // 自动展开所有一级菜单
      const parentMenus = menuData.filter((m: Menu) => m.parent_id === 0);
      setExpandedKeys(parentMenus.map((m: Menu) => m.id));
    } catch (error) {
      console.error("加载菜单列表失败:", error);
    }
  };

  // 加载所有权限
  const loadPermissions = async () => {
    try {
      const response = await api.permissions.list();
      setPermissions((response.data?.data as any) || []);
    } catch (error) {
      console.error("加载权限列表失败:", error);
    }
  };

  // 加载角色权限
  const loadRolePermissions = async (roleId: number) => {
    try {
      const response = await api.roles.getPermissions(roleId);
      const data = (response.data?.data as any) || [];
      // 获取菜单 ID 和权限 ID
      const menuIds = data.map((item: any) => item.id);
      const permissionIds = data.map((item: any) => item.id);
      setCheckedMenus(menuIds);
      setCheckedPermissions(permissionIds);
    } catch (error) {
      console.error("加载角色权限失败:", error);
    }
  };

  useEffect(() => {
    loadRoles();
  }, []);

  // 打开创建/编辑弹窗
  const handleOpenModal = (role?: Role) => {
    setEditingRole(role || null);
    if (role) {
      form.setFieldsValue(role);
    } else {
      form.resetFields();
    }
    setIsModalOpen(true);
  };

  // 打开权限分配抽屉
  const handleOpenPermissionDrawer = async (role: Role) => {
    setSelectedRole(role);
    await loadMenus();
    await loadPermissions();
    await loadRolePermissions(role.id);
    setIsDrawerOpen(true);
  };

  // 提交表单
  const handleSubmit = async (values: any) => {
    try {
      if (editingRole) {
        await api.roles.update(editingRole.id, values);
        messageApi.success("角色更新成功");
      } else {
        await api.roles.create(values);
        messageApi.success("角色创建成功");
      }
      setIsModalOpen(false);
      loadRoles();
    } catch (error: any) {
      messageApi.error(error.response?.data?.detail || "操作失败");
    }
  };

  // 删除角色
  const handleDelete = async (roleId: number) => {
    try {
      await api.roles.delete(roleId);
      messageApi.success("角色删除成功");
      loadRoles();
    } catch (error: any) {
      messageApi.error(error.response?.data?.detail || "删除失败");
    }
  };

  // 保存权限分配
  const handleSavePermissions = async () => {
    if (!selectedRole) return;
    try {
      // 合并菜单 ID 和权限 ID（去重）
      const allIds = [...new Set([...checkedMenus, ...checkedPermissions])];
      await api.roles.assignPermissions(selectedRole.id, allIds);
      messageApi.success("权限分配成功");
      setIsDrawerOpen(false);
      loadRoles();
    } catch (error: any) {
      messageApi.error(error.response?.data?.detail || "分配失败");
    }
  };

  // 菜单树勾选
  const onCheckMenus = (checked: any) => {
    setCheckedMenus(checked.checked || checked);
  };

  // 权限列表勾选
  const onCheckPermissions = (e: React.ChangeEvent<HTMLInputElement>, permissionId: number) => {
    if (e.target.checked) {
      setCheckedPermissions([...checkedPermissions, permissionId]);
    } else {
      setCheckedPermissions(checkedPermissions.filter(id => id !== permissionId));
    }
  };

  // 将菜单转换为树形结构
  const buildMenuTree = (items: Menu[], parentId: number = 0): DataNode[] => {
    return items
      .filter(item => item.parent_id === parentId)
      .map(item => ({
        key: item.id,
        title: item.name,
        children: buildMenuTree(items, item.id),
      }));
  };

  const columns: TableColumnsType<Role> = [
    {
      title: "ID",
      dataIndex: "id",
      width: 60,
    },
    {
      title: "角色名称",
      dataIndex: "name",
      width: 150,
    },
    {
      title: "角色编码",
      dataIndex: "code",
      width: 120,
    },
    {
      title: "描述",
      dataIndex: "description",
      ellipsis: true,
    },
    {
      title: "类型",
      dataIndex: "is_system",
      width: 100,
      render: (isSystem) => (
        <Tag color={isSystem ? "red" : "blue"}>
          {isSystem ? "系统角色" : "自定义"}
        </Tag>
      ),
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
      title: "创建时间",
      dataIndex: "created_at",
      width: 160,
      render: (text) => new Date(text).toLocaleString("zh-CN"),
    },
    {
      title: "操作",
      key: "action",
      width: 200,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<SettingOutlined />}
            onClick={() => handleOpenPermissionDrawer(record)}
          >
            分配权限
          </Button>
          {!record.is_system && (
            <>
              <Button
                type="link"
                size="small"
                icon={<EditOutlined />}
                onClick={() => handleOpenModal(record)}
              >
                编辑
              </Button>
              <Popconfirm
                title="确定要删除此角色吗？"
                onConfirm={() => handleDelete(record.id)}
                okText="确定"
                cancelText="取消"
              >
                <Button type="link" size="small" danger icon={<DeleteOutlined />}>
                  删除
                </Button>
              </Popconfirm>
            </>
          )}
        </Space>
      ),
    },
  ];

  return (
    <>
      {contextHolder}
      <Card>
        <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between" }}>
          <Title level={4} style={{ margin: 0 }}>角色管理</Title>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => handleOpenModal()}
          >
            新增角色
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={roles}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1000 }}
        />
      </Card>

      {/* 创建/编辑角色弹窗 */}
      <Modal
        title={editingRole ? "编辑角色" : "新增角色"}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form
          form={form}
          onFinish={handleSubmit}
          layout="vertical"
          initialValues={{ status: 1, is_system: false }}
        >
          <Form.Item
            name="name"
            label="角色名称"
            rules={[{ required: true, message: "请输入角色名称" }]}
          >
            <Input placeholder="请输入角色名称" />
          </Form.Item>

          <Form.Item
            name="code"
            label="角色编码"
            rules={[
              { required: true, message: "请输入角色编码" },
              { pattern: /^[a-z_]+$/, message: "只能使用小写字母和下划线" }
            ]}
          >
            <Input placeholder="如：admin, user" disabled={!!editingRole?.is_system} />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <TextArea rows={3} placeholder="请输入角色描述" />
          </Form.Item>

          <Form.Item name="status" label="状态">
            <Select>
              <Select.Option value={1}>正常</Select.Option>
              <Select.Option value={0}>禁用</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* 分配权限抽屉 */}
      <Drawer
        title={`分配权限 - ${selectedRole?.name}`}
        placement="right"
        size="large"
        open={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        extra={
          <Space>
            <Button onClick={() => setIsDrawerOpen(false)}>取消</Button>
            <Button type="primary" onClick={handleSavePermissions}>确定</Button>
          </Space>
        }
      >
        <div style={{ marginBottom: 16 }}>
          <Title level={5}>菜单权限</Title>
          <Tree
            checkable
            checkedKeys={checkedMenus}
            onCheck={onCheckMenus}
            treeData={buildMenuTree(menus)}
            defaultExpandAll
          />
        </div>

        <Divider />

        <div>
          <Title level={5}>功能权限</Title>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {permissions.map((perm) => (
              <Form.Item key={perm.id} style={{ marginBottom: 0 }}>
                <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <input
                    type="checkbox"
                    checked={checkedPermissions.includes(perm.id)}
                    onChange={(e) => onCheckPermissions(e, perm.id)}
                  />
                  <Tag>{perm.code}</Tag>
                  <span>{perm.name}</span>
                </label>
              </Form.Item>
            ))}
          </div>
        </div>
      </Drawer>
    </>
  );
}
