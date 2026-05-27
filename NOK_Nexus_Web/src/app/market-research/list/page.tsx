"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { useMenuStore } from "@/stores/menuStore";
import { api } from "@/lib/api";
import {
  Table,
  Button,
  Space,
  Input,
  Select,
  Typography,
  message,
  Modal,
  Form,
  DatePicker,
  Popconfirm,
  Card,
  Row,
  Col,
  Tag,
} from "antd";
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";

const { Title } = Typography;
const { TextArea } = Input;

interface MarketResearch {
  id: number;
  user_id: number;
  city: string;
  manufacturer: string;
  product_name: string;
  price: string;
  research_date: string;
  remark: string;
  status: number;
  created_at: string;
  updated_at: string;
}

interface FormData {
  city: string;
  manufacturer: string;
  product_name: string;
  price: string;
  research_date: string;
  remark: string;
}

const COMMON_CITIES = [
  "北京",
  "上海",
  "广州",
  "深圳",
  "杭州",
  "南京",
  "成都",
  "武汉",
  "西安",
  "重庆",
];

export default function MarketResearchListPage() {
  const router = useRouter();
  const { checkAuth } = useAuth();
  const { permissionCodes } = useMenuStore();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<MarketResearch[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [filters, setFilters] = useState<{
    city?: string;
    manufacturer?: string;
    product_name?: string;
  }>({});
  const [modalOpen, setModalOpen] = useState(false);
  const [editingRecord, setEditingRecord] = useState<MarketResearch | null>(null);
  const [form] = Form.useForm<FormData>();
  const [confirmLoading, setConfirmLoading] = useState(false);

  // 权限检查
  const canView = permissionCodes.some((code) => code === "market_research:view");
  const canCreate = permissionCodes.some((code) => code === "market_research:create");
  const canEdit = permissionCodes.some((code) => code === "market_research:edit");
  const canDelete = permissionCodes.some((code) => code === "market_research:delete");

  // 加载数据
  const loadData = async () => {
    setLoading(true);
    try {
      const response = await api.marketResearch.list({
        page,
        page_size: pageSize,
        ...filters,
      });
      const data = (response.data as any) || {};
      setData(data.items || []);
      setTotal(data.total || 0);
    } catch (error: any) {
      message.error("加载数据失败：" + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuth().then((authenticated) => {
      if (!authenticated) {
        router.push("/login");
      } else {
        loadData();
      }
    });
  }, [page, pageSize, filters]);

  // 处理搜索
  const handleSearch = () => {
    setPage(1);
    loadData();
  };

  // 重置筛选
  const handleReset = () => {
    setFilters({});
    setPage(1);
  };

  // 打开创建/编辑弹窗
  const handleOpenModal = (record?: MarketResearch) => {
    if (record) {
      setEditingRecord(record);
      form.setFieldsValue({
        ...record,
        research_date: record.research_date,
      });
    } else {
      setEditingRecord(null);
      form.resetFields();
    }
    setModalOpen(true);
  };

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setConfirmLoading(true);

      const submitData = { ...values };

      if (editingRecord) {
        await api.marketResearch.update(editingRecord.id, submitData as Record<string, unknown>);
        message.success("更新成功");
      } else {
        await api.marketResearch.create(submitData as Record<string, unknown>);
        message.success("创建成功");
      }

      setModalOpen(false);
      form.resetFields();
      loadData();
    } catch (error: any) {
      if (!error.response) {
        message.error("请检查表单填写");
      }
    } finally {
      setConfirmLoading(false);
    }
  };

  // 删除记录
  const handleDelete = async (id: number) => {
    try {
      await api.marketResearch.delete(id);
      message.success("删除成功");
      loadData();
    } catch (error: any) {
      message.error("删除失败：" + (error.response?.data?.detail || error.message));
    }
  };

  // 表格列定义
  const columns: ColumnsType<MarketResearch> = [
    {
      title: "ID",
      dataIndex: "id",
      key: "id",
      width: 80,
      sorter: (a, b) => a.id - b.id,
    },
    {
      title: "城市",
      dataIndex: "city",
      key: "city",
      width: 120,
      filters: COMMON_CITIES.map((city) => ({ text: city, value: city })),
      onFilter: (value, record) => record.city === value,
    },
    {
      title: "厂商",
      dataIndex: "manufacturer",
      key: "manufacturer",
      width: 150,
      ellipsis: true,
    },
    {
      title: "商品名称",
      dataIndex: "product_name",
      key: "product_name",
      width: 180,
      ellipsis: true,
    },
    {
      title: "价格",
      dataIndex: "price",
      key: "price",
      width: 100,
      sorter: (a, b) => parseFloat(a.price) - parseFloat(b.price),
      render: (price: string) => `¥${parseFloat(price).toFixed(2)}`,
    },
    {
      title: "调研日期",
      dataIndex: "research_date",
      key: "research_date",
      width: 120,
      sorter: (a, b) => new Date(a.research_date).getTime() - new Date(b.research_date).getTime(),
    },
    {
      title: "备注",
      dataIndex: "remark",
      key: "remark",
      width: 200,
      ellipsis: true,
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 80,
      render: (status: number) => (
        <Tag color={status === 1 ? "green" : "red"}>
          {status === 1 ? "正常" : "已删除"}
        </Tag>
      ),
    },
    {
      title: "操作",
      key: "action",
      width: 150,
      fixed: "right",
      render: (_: unknown, record: MarketResearch) => (
        <Space size="small">
          {canEdit && record.status === 1 && (
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleOpenModal(record)}
            >
              编辑
            </Button>
          )}
          {canDelete && record.status === 1 && (
            <Popconfirm
              title="确认删除"
              description="确定要删除这条调研数据吗？"
              onConfirm={() => handleDelete(record.id)}
              okText="确认"
              cancelText="取消"
            >
              <Button
                type="link"
                size="small"
                danger
                icon={<DeleteOutlined />}
              >
                删除
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  if (!canView) {
    return (
      <div style={{ padding: 24, textAlign: "center" }}>
        <Typography.Text type="danger">
          暂无权限查看市场调研数据，请联系管理员分配权限
        </Typography.Text>
      </div>
    );
  }

  return (
    <div style={{ padding: 0 }}>
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col flex="auto">
            <Space size="middle" wrap>
              <Select
                placeholder="选择城市"
                allowClear
                style={{ width: 150 }}
                options={COMMON_CITIES.map((city) => ({ label: city, value: city }))}
                value={filters.city}
                onChange={(value) => setFilters({ ...filters, city: value })}
              />
              <Input
                placeholder="厂商名称"
                style={{ width: 150 }}
                value={filters.manufacturer}
                onChange={(e) => setFilters({ ...filters, manufacturer: e.target.value })}
                onPressEnter={handleSearch}
              />
              <Input
                placeholder="商品名称"
                style={{ width: 150 }}
                value={filters.product_name}
                onChange={(e) => setFilters({ ...filters, product_name: e.target.value })}
                onPressEnter={handleSearch}
              />
              <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
                搜索
              </Button>
              <Button icon={<ReloadOutlined />} onClick={handleReset}>
                重置
              </Button>
            </Space>
          </Col>
          {canCreate && (
            <Col>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
                新建调研
              </Button>
            </Col>
          )}
        </Row>
      </Card>

      <Card>
        <Table
          columns={columns}
          dataSource={data}
          loading={loading}
          rowKey="id"
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            pageSizeOptions: ["10", "20", "50", "100"],
            onChange: (page, pageSize) => {
              setPage(page);
              setPageSize(pageSize);
            },
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 创建/编辑弹窗 */}
      <Modal
        title={editingRecord ? "编辑调研数据" : "新建调研数据"}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={confirmLoading}
        width={600}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="city"
            label="调研城市"
            rules={[{ required: true, message: "请选择调研城市" }]}
          >
            <Select placeholder="请选择城市" options={COMMON_CITIES.map((city) => ({ label: city, value: city }))} />
          </Form.Item>

          <Form.Item
            name="manufacturer"
            label="厂商名称"
            rules={[{ required: true, message: "请输入厂商名称" }]}
          >
            <Input placeholder="请输入厂商名称" />
          </Form.Item>

          <Form.Item
            name="product_name"
            label="商品名称"
            rules={[{ required: true, message: "请输入商品名称" }]}
          >
            <Input placeholder="请输入商品名称" />
          </Form.Item>

          <Form.Item
            name="price"
            label="调研价格"
            rules={[
              { required: true, message: "请输入调研价格" },
              { pattern: /^\d+(\.\d{1,2})?$/, message: "请输入有效的价格（最多两位小数）" },
            ]}
          >
            <Input placeholder="请输入价格" prefix="¥" />
          </Form.Item>

          <Form.Item
            name="research_date"
            label="调研日期"
            rules={[{ required: true, message: "请选择调研日期" }]}
          >
            <DatePicker style={{ width: "100%" }} format="YYYY-MM-DD" />
          </Form.Item>

          <Form.Item name="remark" label="备注信息">
            <TextArea rows={3} placeholder="请输入备注信息（可选）" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
