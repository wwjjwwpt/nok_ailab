"use client";

import { useState, useEffect } from "react";
import {
  Table, Button, Modal, Form, Input, message, Space,
  Popconfirm, Tag, Card, Typography, Select, Tree, InputNumber, Row, Col
} from "antd";
import {
  PlusOutlined, EditOutlined, DeleteOutlined, DatabaseOutlined
} from "@ant-design/icons";
import { api } from "@/lib/api";
import type { TableColumnsType } from "antd";
import type { DataNode } from "antd/es/tree";

const { Title } = Typography;
const { TextArea } = Input;

interface DataScope {
  id: number;
  name: string;
  code: string;
  scope_type: number;
  scope_config?: any;
  description?: string;
  status: number;
  created_at: string;
}

interface Department {
  id: number;
  name: string;
  parent_id: number;
  children?: Department[];
}

const SCOPE_TYPE_LABELS: Record<number, string> = {
  1: "全部数据",
  2: "本部门及子部门",
  3: "本部门",
  4: "仅本人",
  5: "自定义范围",
};

export default function DataScopeManagementPage() {
  const [loading, setLoading] = useState(false);
  const [dataScopes, setDataScopes] = useState<DataScope[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [messageApi, contextHolder] = message.useMessage();
  const [form] = Form.useForm();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingScope, setEditingScope] = useState<DataScope | null>(null);
  const [selectedDeptIds, setSelectedDeptIds] = useState<number[]>([]);

  // 加载数据权限列表
  const loadDataScopes = async () => {
    setLoading(true);
    try {
      // 注意：后端可能需要添加这个接口
      const response = await api.departments.list();
      // 暂时使用部门列表模拟，实际应该调用 /data-scopes 接口
      setDataScopes([]);
    } catch (error: any) {
      console.error("加载数据权限列表失败:", error);
    } finally {
      setLoading(false);
    }
  };

  // 加载部门树
  const loadDepartments = async () => {
    try {
      const response = await api.departments.tree();
      setDepartments((response.data as any) || []);
    } catch (error) {
      console.error("加载部门列表失败:", error);
    }
  };

  useEffect(() => {
    loadDataScopes();
    loadDepartments();
  }, []);

  // 打开创建/编辑弹窗
  const handleOpenModal = (scope?: DataScope) => {
    setEditingScope(scope || null);
    if (scope) {
      form.setFieldsValue(scope);
      if (scope.scope_config?.dept_ids) {
        setSelectedDeptIds(scope.scope_config.dept_ids);
      }
    } else {
      form.resetFields();
      form.setFieldsValue({
        scope_type: 1,
        status: 1,
      });
      setSelectedDeptIds([]);
    }
    setIsModalOpen(true);
  };

  // 提交表单
  const handleSubmit = async (values: any) => {
    try {
      // 如果是自定义范围，添加部门配置
      if (values.scope_type === 5) {
        values.scope_config = { dept_ids: selectedDeptIds };
      }

      if (editingScope) {
        // await api.dataScopes.update(editingScope.id, values);
        messageApi.success("数据权限更新成功");
      } else {
        // await api.dataScopes.create(values);
        messageApi.success("数据权限创建成功");
      }
      setIsModalOpen(false);
      loadDataScopes();
    } catch (error: any) {
      messageApi.error(error.response?.data?.detail || "操作失败");
    }
  };

  // 构建部门树
  const buildDeptTree = (items: Department[], parentId: number = 0): DataNode[] => {
    return items
      .filter(item => item.parent_id === parentId)
      .map(item => ({
        key: item.id,
        title: item.name,
        children: buildDeptTree(items, item.id),
      }));
  };

  const columns: TableColumnsType<DataScope> = [
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
      title: "范围类型",
      dataIndex: "scope_type",
      width: 150,
      render: (type) => <Tag>{SCOPE_TYPE_LABELS[type] || "未知"}</Tag>,
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
            title="确定要删除此数据权限吗？"
            onConfirm={() => {}}
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

  const deptTreeData = buildDeptTree(departments);

  return (
    <>
      {contextHolder}
      <Card>
        <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between" }}>
          <div>
            <Title level={4} style={{ margin: 0 }}>数据权限管理</Title>
            <Space style={{ marginTop: 8 }}>
              <Tag color="green">全部数据</Tag>
              <Tag color="blue">本部门及子部门</Tag>
              <Tag color="cyan">本部门</Tag>
              <Tag color="orange">仅本人</Tag>
              <Tag color="purple">自定义范围</Tag>
            </Space>
          </div>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => handleOpenModal()}
            disabled
          >
            新增数据权限
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={dataScopes}
          rowKey="id"
          loading={loading}
          pagination={false}
        />

        <Card type="inner" title="数据权限说明" style={{ marginTop: 16 }}>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            <li><strong>全部数据：</strong>可访问系统中的全部数据</li>
            <li><strong>本部门及子部门：</strong>可访问本部门及所有下级部门的数据</li>
            <li><strong>本部门：</strong>仅可访问本部门的数据</li>
            <li><strong>仅本人：</strong>仅可访问自己创建的数据</li>
            <li><strong>自定义范围：</strong>可指定特定的部门范围</li>
          </ul>
        </Card>
      </Card>

      {/* 创建/编辑数据权限弹窗 */}
      <Modal
        title={editingScope ? "编辑数据权限" : "新增数据权限"}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        onOk={() => form.submit()}
        width={700}
      >
        <Form
          form={form}
          onFinish={handleSubmit}
          layout="vertical"
          initialValues={{ scope_type: 1, status: 1 }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="权限名称"
                rules={[{ required: true, message: "请输入权限名称" }]}
              >
                <Input placeholder="如：全部数据" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="code"
                label="权限编码"
                rules={[
                  { required: true, message: "请输入权限编码" },
                  { pattern: /^[a-z_]+$/, message: "只能使用小写字母和下划线" }
                ]}
              >
                <Input placeholder="如：all" disabled={!!editingScope} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="scope_type"
            label="范围类型"
            rules={[{ required: true, message: "请选择范围类型" }]}
          >
            <Select>
              <Select.Option value={1}>全部数据</Select.Option>
              <Select.Option value={2}>本部门及子部门</Select.Option>
              <Select.Option value={3}>本部门</Select.Option>
              <Select.Option value={4}>仅本人</Select.Option>
              <Select.Option value={5}>自定义范围</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="description" label="描述">
            <TextArea rows={2} placeholder="请输入数据权限描述" />
          </Form.Item>

          <Form.Item name="status" label="状态">
            <Select>
              <Select.Option value={1}>正常</Select.Option>
              <Select.Option value={0}>禁用</Select.Option>
            </Select>
          </Form.Item>

          {form.getFieldValue("scope_type") === 5 && (
            <Form.Item label="选择部门范围">
              <Tree
                checkable
                checkedKeys={selectedDeptIds}
                onCheck={(checked: any) => setSelectedDeptIds(checked.checked || checked)}
                treeData={deptTreeData}
                defaultExpandAll
              />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </>
  );
}
