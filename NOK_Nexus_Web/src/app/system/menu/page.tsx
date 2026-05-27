"use client";

import { useState, useEffect } from "react";
import {
  Table, Button, Modal, Form, Input, Select, message, Space,
  Popconfirm, Tag, Card, Typography, Tree, Drawer, InputNumber, Switch,
  Row, Col, Checkbox
} from "antd";
import {
  PlusOutlined, EditOutlined, DeleteOutlined, FolderOutlined,
  FileOutlined, LinkOutlined, SettingOutlined
} from "@ant-design/icons";
import { api } from "@/lib/api";
import type { TableColumnsType } from "antd";
import type { DataNode } from "antd/es/tree";

const { Title } = Typography;
const { TextArea } = Input;

interface Menu {
  id: number;
  name: string;
  code: string;
  parent_id: number;
  path?: string;
  component?: string;
  icon?: string;
  type: number;
  sort_order: number;
  visible: boolean;
  permission?: string;
  status: number;
  created_at: string;
  children?: Menu[];
}

interface Permission {
  id: number;
  name: string;
  code: string;
  description?: string;
}

const MENU_TYPE_LABELS: Record<number, string> = {
  1: "目录",
  2: "菜单",
  3: "外链",
};

const MENU_TYPE_ICONS: Record<number, React.ReactNode> = {
  1: <FolderOutlined />,
  2: <FileOutlined />,
  3: <LinkOutlined />,
};

export default function MenuManagementPage() {
  const [loading, setLoading] = useState(false);
  const [menus, setMenus] = useState<Menu[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [messageApi, contextHolder] = message.useMessage();
  const [form] = Form.useForm();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingMenu, setEditingMenu] = useState<Menu | null>(null);
  const [parentMenus, setParentMenus] = useState<Menu[]>([]);

  // 权限绑定相关状态
  const [isPermissionDrawerOpen, setIsPermissionDrawerOpen] = useState(false);
  const [currentMenuId, setCurrentMenuId] = useState<number | null>(null);
  const [currentMenuName, setCurrentMenuName] = useState<string>("");
  const [boundPermissionIds, setBoundPermissionIds] = useState<number[]>([]);

  // 加载菜单列表
  const loadMenus = async () => {
    setLoading(true);
    try {
      const response = await api.menus.list();
      const menuData = (response.data as any) || [];
      setMenus(menuData);
      // 后端已返回树形结构，直接使用
      // 获取顶级菜单作为父菜单选项
      setParentMenus(menuData.filter((m: Menu) => m.parent_id === 0));
    } catch (error: any) {
      messageApi.error(error.response?.data?.detail || "加载菜单列表失败");
    } finally {
      setLoading(false);
    }
  };

  // 加载权限列表
  const loadPermissions = async () => {
    try {
      const response = await api.permissions.list();
      setPermissions((response.data as any) || []);
    } catch (error: any) {
      console.error("加载权限列表失败:", error);
    }
  };

  useEffect(() => {
    loadMenus();
    loadPermissions();
  }, []);

  // 打开创建/编辑弹窗
  const handleOpenModal = (menu?: Menu) => {
    setEditingMenu(menu || null);
    if (menu) {
      form.setFieldsValue({
        ...menu,
        visible: menu.visible !== false,
        status: menu.status !== 0,
      });
    } else {
      form.resetFields();
      form.setFieldsValue({
        type: 2,
        sort_order: 0,
        visible: true,
        status: 1,
        parent_id: 0,
      });
    }
    setIsModalOpen(true);
  };

  // 提交表单
  const handleSubmit = async (values: any) => {
    try {
      if (editingMenu) {
        await api.menus.update(editingMenu.id, values);
        messageApi.success("菜单更新成功");
      } else {
        await api.menus.create(values);
        messageApi.success("菜单创建成功");
      }
      setIsModalOpen(false);
      loadMenus();
    } catch (error: any) {
      messageApi.error(error.response?.data?.detail || "操作失败");
    }
  };

  // 删除菜单
  const handleDelete = async (menuId: number) => {
    try {
      await api.menus.delete(menuId);
      messageApi.success("菜单删除成功");
      loadMenus();
    } catch (error: any) {
      messageApi.error(error.response?.data?.detail || "删除失败");
    }
  };

  // 打开权限绑定抽屉
  const handleOpenPermissionDrawer = async (menu: Menu) => {
    setCurrentMenuId(menu.id);
    setCurrentMenuName(menu.name);
    setIsPermissionDrawerOpen(true);
    // 加载已绑定的权限
    try {
      const response = await api.menus.getPermissions(menu.id);
      setBoundPermissionIds(((response.data as any) || []).map((p: Permission) => p.id));
    } catch (error) {
      console.error("加载已绑定权限失败:", error);
      setBoundPermissionIds([]);
    }
  };

  // 保存权限绑定
  const handleSavePermissions = async () => {
    if (!currentMenuId) return;
    try {
      await api.menus.bindPermissions(currentMenuId, boundPermissionIds);
      messageApi.success("权限绑定成功");
      setIsPermissionDrawerOpen(false);
    } catch (error: any) {
      messageApi.error(error.response?.data?.detail || "绑定失败");
    }
  };

  // 将菜单转换为树形结构用于展示
  const buildMenuTree = (items: Menu[]): DataNode[] => {
    return items.map(item => ({
      key: item.id,
      title: (
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          padding: "8px 12px",
          margin: "2px 4px",
          borderRadius: "6px",
          background: item.status !== 1 ? "#fafafa" : "#fff",
          border: "1px solid #e8e8e8",
          minWidth: 500,
        }}>
          <span style={{ fontSize: 14, color: "#1890ff", width: 20, textAlign: "center" }}>{MENU_TYPE_ICONS[item.type]}</span>
          <span style={{ fontWeight: 500, fontSize: 13, color: "#333", width: 100 }}>{item.name}</span>
          <span style={{ fontSize: 12, color: "#999", background: "#f5f5f5", padding: "2px 8px", borderRadius: "4px", width: 120, textAlign: "center", display: "inline-block" }}>{item.code}</span>
          <span style={{ fontSize: 12, color: "#bfbfbf", width: 120, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{item.path || "-"}</span>
          <Tag color={item.status === 1 ? "success" : "default"} style={{ fontSize: 11, margin: 0, width: 45, textAlign: "center" }}>
            {item.status === 1 ? "正常" : "禁用"}
          </Tag>
          {!item.visible && (
            <Tag color="warning" style={{ fontSize: 11, margin: 0, width: 40, textAlign: "center" }}>隐藏</Tag>
          )}
          {item.visible && <span style={{ width: 40 }} />}
          <Button
            type="link"
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              handleOpenPermissionDrawer(item);
            }}
            style={{ padding: 0, fontSize: 12 }}
          >
            权限
          </Button>
        </div>
      ),
      children: item.children ? buildMenuTree(item.children) : [],
    }));
  };

  // 获取父菜单名称
  const getParentName = (parentId: number): string => {
    if (parentId === 0) return "顶级菜单";
    const parent = menus.find(m => m.id === parentId);
    return parent ? parent.name : "未知";
  };

  const treeData = buildMenuTree(menus);

  return (
    <>
      {contextHolder}
      <style jsx global>{`
        .ant-tree-treenode {
          padding: 2px 0;
        }
        .ant-tree-node-content-wrapper {
          padding: 0;
        }
        .ant-tree-node-content-wrapper:hover {
          background: transparent;
        }
      `}</style>
      <Card>
        <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <Title level={4} style={{ margin: 0 }}>菜单管理</Title>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => handleOpenModal()}
          >
            新增菜单
          </Button>
        </div>

        <Tree
          treeData={treeData}
          defaultExpandAll
          selectable={false}
          showLine={{ showLeafIcon: false }}
        />
      </Card>

      {/* 创建/编辑菜单弹窗 */}
      <Modal
        title={editingMenu ? "编辑菜单" : "新增菜单"}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        onOk={() => form.submit()}
        width={700}
        destroyOnHidden
      >
        <Form
          form={form}
          onFinish={handleSubmit}
          layout="vertical"
          initialValues={{
            type: 2,
            sort_order: 0,
            visible: true,
            status: 1,
            parent_id: 0,
          }}
        >
          <Form.Item
            name="parent_id"
            label="父级菜单"
          >
            <Select placeholder="请选择父级菜单">
              <Select.Option value={0}>顶级菜单</Select.Option>
              {parentMenus.map((menu) => (
                <Select.Option key={menu.id} value={menu.id}>
                  {menu.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="菜单名称"
                rules={[{ required: true, message: "请输入菜单名称" }]}
              >
                <Input placeholder="如：用户管理" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="code"
                label="菜单编码"
                rules={[
                  { required: true, message: "请输入菜单编码" },
                  { pattern: /^[a-z_]+$/, message: "只能使用小写字母和下划线" }
                ]}
              >
                <Input placeholder="如：system_user" disabled={!!editingMenu} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="type"
                label="菜单类型"
                rules={[{ required: true, message: "请选择菜单类型" }]}
              >
                <Select>
                  <Select.Option value={1}>目录</Select.Option>
                  <Select.Option value={2}>菜单</Select.Option>
                  <Select.Option value={3}>外链</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="sort_order" label="排序">
                <InputNumber min={0} style={{ width: "100%" }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="path" label="路由路径">
            <Input placeholder="如：/system/user" addonBefore="/" />
          </Form.Item>

          <Form.Item
            name="component"
            label="组件路径"
            tooltip="前端组件文件路径，如：system/user/page"
          >
            <Input placeholder="如：system/user/page" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="icon" label="图标">
                <Input placeholder="如：user, setting" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="permission" label="权限标识">
                <Input placeholder="如：user:view" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="visible" label="是否显示" valuePropName="checked">
                <Switch checkedChildren="显示" unCheckedChildren="隐藏" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="status" label="状态" valuePropName="checked">
                <Switch checkedChildren="正常" unCheckedChildren="禁用" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* 权限绑定抽屉 */}
      <Drawer
        title={`绑定权限 - ${currentMenuName}`}
        placement="right"
        size="default"
        open={isPermissionDrawerOpen}
        onClose={() => setIsPermissionDrawerOpen(false)}
        extra={
          <Space>
            <Button onClick={() => setIsPermissionDrawerOpen(false)}>取消</Button>
            <Button type="primary" onClick={handleSavePermissions}>确定</Button>
          </Space>
        }
      >
        <div style={{ marginBottom: 16 }}>
          <p style={{ color: '#666', marginBottom: 8 }}>请选择要绑定到此菜单的权限：</p>
          <Checkbox.Group
            style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}
            value={boundPermissionIds}
            onChange={(value) => setBoundPermissionIds(value as number[])}
          >
            {permissions.map((perm) => (
              <Checkbox key={perm.id} value={perm.id}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span style={{ fontWeight: 500 }}>{perm.name}</span>
                  <span style={{ fontSize: '12px', color: '#999' }}>{perm.code}</span>
                </div>
              </Checkbox>
            ))}
          </Checkbox.Group>
        </div>
      </Drawer>
    </>
  );
}
