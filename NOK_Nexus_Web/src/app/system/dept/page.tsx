"use client";

import { useState, useEffect } from "react";
import {
  Table, Button, Modal, Form, Input, message, Space,
  Popconfirm, Tag, Card, Typography, Tree, InputNumber, Select, Row, Col
} from "antd";
import {
  PlusOutlined, EditOutlined, DeleteOutlined, TeamOutlined
} from "@ant-design/icons";
import { api } from "@/lib/api";
import type { TableColumnsType } from "antd";
import type { DataNode } from "antd/es/tree";

const { Title } = Typography;

interface Department {
  id: number;
  name: string;
  parent_id: number;
  leader_name?: string;
  phone?: string;
  email?: string;
  sort_order: number;
  full_path: string;
  status: number;
  created_at: string;
  children?: Department[];
}

export default function DepartmentManagementPage() {
  const [loading, setLoading] = useState(false);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [messageApi, contextHolder] = message.useMessage();
  const [form] = Form.useForm();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingDept, setEditingDept] = useState<Department | null>(null);

  // 加载部门列表
  const loadDepartments = async () => {
    setLoading(true);
    try {
      const response = await api.departments.tree();
      setDepartments((response.data as any) || []);
    } catch (error: any) {
      messageApi.error(error.response?.data?.detail || "加载部门列表失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDepartments();
  }, []);

  // 打开创建/编辑弹窗
  const handleOpenModal = (dept?: Department) => {
    setEditingDept(dept || null);
    if (dept) {
      form.setFieldsValue(dept);
    } else {
      form.resetFields();
      form.setFieldsValue({
        parent_id: 0,
        sort_order: 0,
        status: 1,
      });
    }
    setIsModalOpen(true);
  };

  // 提交表单
  const handleSubmit = async (values: any) => {
    try {
      if (editingDept) {
        await api.departments.update(editingDept.id, values);
        messageApi.success("部门更新成功");
      } else {
        await api.departments.create(values);
        messageApi.success("部门创建成功");
      }
      setIsModalOpen(false);
      loadDepartments();
    } catch (error: any) {
      messageApi.error(error.response?.data?.detail || "操作失败");
    }
  };

  // 删除部门
  const handleDelete = async (deptId: number) => {
    try {
      await api.departments.delete(deptId);
      messageApi.success("部门删除成功");
      loadDepartments();
    } catch (error: any) {
      messageApi.error(error.response?.data?.detail || "删除失败");
    }
  };

  // 将部门转换为树形结构
  const buildDeptTree = (items: Department[], parentId: number = 0): DataNode[] => {
    return items
      .filter(item => item.parent_id === parentId)
      .map(item => ({
        key: item.id,
        title: (
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <TeamOutlined />
            <span>{item.name}</span>
            {item.leader_name && <Tag color="blue">{item.leader_name}</Tag>}
            {item.status !== 1 && <Tag color="error">禁用</Tag>}
          </div>
        ),
        children: buildDeptTree(items, item.id),
      }));
  };

  // 获取父部门名称
  const getParentName = (parentId: number): string => {
    if (parentId === 0) return "顶级部门";
    const parent = departments.find(d => d.id === parentId);
    return parent ? parent.name : "未知";
  };

  const treeData = buildDeptTree(departments);

  const columns: TableColumnsType<Department> = [
    {
      title: "ID",
      dataIndex: "id",
      width: 60,
    },
    {
      title: "部门名称",
      dataIndex: "name",
      width: 150,
    },
    {
      title: "负责人",
      dataIndex: "leader_name",
      width: 100,
    },
    {
      title: "联系电话",
      dataIndex: "phone",
      width: 130,
    },
    {
      title: "邮箱",
      dataIndex: "email",
      width: 180,
    },
    {
      title: "排序",
      dataIndex: "sort_order",
      width: 80,
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
            title="确定要删除此部门吗？"
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
        <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between" }}>
          <div>
            <Title level={4} style={{ margin: 0 }}>部门管理</Title>
          </div>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => handleOpenModal()}
          >
            新增部门
          </Button>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div>
            <Title level={5} style={{ marginBottom: 12 }}>部门树形结构</Title>
            <div style={{ background: "#fafafa", padding: 16, borderRadius: 8 }}>
              <Tree
                treeData={treeData}
                defaultExpandAll
                selectable={false}
              />
            </div>
          </div>

          <div>
            <Title level={5} style={{ marginBottom: 12 }}>部门列表</Title>
            <Table
              columns={columns}
              dataSource={departments}
              rowKey="id"
              loading={loading}
              pagination={false}
              size="small"
              scroll={{ y: 400 }}
            />
          </div>
        </div>
      </Card>

      {/* 创建/编辑部门弹窗 */}
      <Modal
        title={editingDept ? "编辑部门" : "新增部门"}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form
          form={form}
          onFinish={handleSubmit}
          layout="vertical"
          initialValues={{ sort_order: 0, status: 1, parent_id: 0 }}
        >
          <Form.Item
            name="parent_id"
            label="父级部门"
          >
            <Select placeholder="请选择父级部门">
              <Select.Option value={0}>顶级部门</Select.Option>
              {departments
                .filter(d => !editingDept || d.id !== editingDept.id)
                .map((dept) => (
                  <Select.Option key={dept.id} value={dept.id}>
                    {dept.name}
                  </Select.Option>
                ))}
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="部门名称"
                rules={[{ required: true, message: "请输入部门名称" }]}
              >
                <Input placeholder="如：技术部" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="sort_order" label="排序">
                <InputNumber min={0} style={{ width: "100%" }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="leader_name" label="负责人">
                <Input placeholder="请输入负责人姓名" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="phone" label="联系电话">
                <Input placeholder="请输入联系电话" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="email" label="邮箱">
            <Input placeholder="请输入部门邮箱" />
          </Form.Item>

          <Form.Item name="status" label="状态">
            <Select>
              <Select.Option value={1}>正常</Select.Option>
              <Select.Option value={0}>禁用</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
