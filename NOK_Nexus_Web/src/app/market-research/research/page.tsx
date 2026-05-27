"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { useMenuStore } from "@/stores/menuStore";
import { api } from "@/lib/api";
import {
  Card,
  Row,
  Col,
  Select,
  Typography,
  Spin,
  Statistic,
  Table,
  Empty,
} from "antd";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { ColumnsType } from "antd/es/table";

const { Title, Text } = Typography;

interface MarketResearch {
  id: number;
  city: string;
  manufacturer: string;
  product_name: string;
  price: string;
  research_date: string;
}

interface ChartData {
  name: string;
  value: number | string;
  avgPrice?: number;
  count?: number;
}

interface SummaryStats {
  totalRecords: number;
  avgPrice: number;
  maxPrice: number;
  minPrice: number;
  totalManufacturers: number;
  totalProducts: number;
  totalCities: number;
}

const COLORS = [
  "#1890ff",
  "#722ed1",
  "#52c41a",
  "#fa8c16",
  "#13c2c2",
  "#eb2f96",
  "#2f54eb",
  "#fa541c",
  "#1890ff",
  "#722ed1",
];

export default function MarketResearchAnalysisPage() {
  const router = useRouter();
  const { checkAuth } = useAuth();
  const { permissionCodes } = useMenuStore();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<MarketResearch[]>([]);

  // 筛选状态
  const [selectedProduct, setSelectedProduct] = useState<string>();
  const [selectedManufacturer, setSelectedManufacturer] = useState<string>();
  const [selectedCity, setSelectedCity] = useState<string>();

  // 图表数据
  const [productPriceData, setProductPriceData] = useState<ChartData[]>([]);
  const [manufacturerData, setManufacturerData] = useState<ChartData[]>([]);
  const [cityDistributionData, setCityDistributionData] = useState<ChartData[]>([]);
  const [trendData, setTrendData] = useState<ChartData[]>([]);

  // 汇总统计
  const [summaryStats, setSummaryStats] = useState<SummaryStats | null>(null);

  // 权限检查 - 使用菜单 code 作为权限码
  const canAnalyze = permissionCodes.some((code) => code === "market_research_analysis");

  // 加载数据
  const loadData = async () => {
    setLoading(true);
    try {
      const response = await api.marketResearch.list({
        page: 1,
        page_size: 100,
        product_name: selectedProduct || undefined,
        manufacturer: selectedManufacturer || undefined,
        city: selectedCity || undefined,
      });

      const listData = (response.data as any)?.items || [];
      setData(listData);
      processChartData(listData);
    } catch (error: any) {
      console.error("加载数据失败:", error);
    } finally {
      setLoading(false);
    }
  };

  // 处理图表数据
  const processChartData = (rawData: MarketResearch[]) => {
    if (!rawData || rawData.length === 0) {
      setProductPriceData([]);
      setManufacturerData([]);
      setCityDistributionData([]);
      setTrendData([]);
      setSummaryStats(null);
      return;
    }

    // 按产品分组 - 平均价格和数量
    const productMap = new Map<string, { total: number; count: number }>();
    rawData.forEach((item) => {
      const price = parseFloat(item.price);
      if (!productMap.has(item.product_name)) {
        productMap.set(item.product_name, { total: 0, count: 0 });
      }
      const data = productMap.get(item.product_name)!;
      data.total += price;
      data.count += 1;
    });

    const productData: ChartData[] = Array.from(productMap.entries()).map(([name, data]) => ({
      name,
      value: (data.total / data.count).toFixed(2),
      avgPrice: data.total / data.count,
      count: data.count,
    })).sort((a, b) => (b.avgPrice || 0) - (a.avgPrice || 0)).slice(0, 10);
    setProductPriceData(productData);

    // 按厂商分组 - 平均价格和数量
    const manufacturerMap = new Map<string, { total: number; count: number }>();
    rawData.forEach((item) => {
      const price = parseFloat(item.price);
      if (!manufacturerMap.has(item.manufacturer)) {
        manufacturerMap.set(item.manufacturer, { total: 0, count: 0 });
      }
      const data = manufacturerMap.get(item.manufacturer)!;
      data.total += price;
      data.count += 1;
    });

    const manufacturerChartData: ChartData[] = Array.from(manufacturerMap.entries()).map(([name, data]) => ({
      name,
      value: data.count,
      avgPrice: data.total / data.count,
    })).sort((a, b) => b.value - a.value).slice(0, 10);
    setManufacturerData(manufacturerChartData);

    // 按城市分组 - 数据分布
    const cityMap = new Map<string, number>();
    rawData.forEach((item) => {
      cityMap.set(item.city, (cityMap.get(item.city) || 0) + 1);
    });

    const cityData: ChartData[] = Array.from(cityMap.entries()).map(([name, value]) => ({
      name,
      value,
    })).sort((a, b) => b.value - a.value);
    setCityDistributionData(cityData);

    // 按月份趋势
    const monthMap = new Map<string, { total: number; count: number }>();
    rawData.forEach((item) => {
      const month = item.research_date.substring(0, 7); // YYYY-MM
      const price = parseFloat(item.price);
      if (!monthMap.has(month)) {
        monthMap.set(month, { total: 0, count: 0 });
      }
      const data = monthMap.get(month)!;
      data.total += price;
      data.count += 1;
    });

    const trendChartData: ChartData[] = Array.from(monthMap.entries())
      .map(([name, data]) => ({
        name,
        value: name,
        avgPrice: data.total / data.count,
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
    setTrendData(trendChartData);

    // 汇总统计
    const prices = rawData.map((item) => parseFloat(item.price));
    const manufacturers = new Set(rawData.map((item) => item.manufacturer));
    const products = new Set(rawData.map((item) => item.product_name));
    const cities = new Set(rawData.map((item) => item.city));

    setSummaryStats({
      totalRecords: rawData.length,
      avgPrice: prices.reduce((a, b) => a + b, 0) / prices.length,
      maxPrice: Math.max(...prices),
      minPrice: Math.min(...prices),
      totalManufacturers: manufacturers.size,
      totalProducts: products.size,
      totalCities: cities.size,
    });
  };

  useEffect(() => {
    checkAuth().then((authenticated) => {
      if (!authenticated) {
        router.push("/login");
      } else {
        loadData();
      }
    });
  }, [selectedProduct, selectedManufacturer, selectedCity]);

  // 获取唯一的产品列表
  const uniqueProducts = [...new Set(data.map((item) => item.product_name))];
  const uniqueManufacturers = [...new Set(data.map((item) => item.manufacturer))];
  const uniqueCities = [...new Set(data.map((item) => item.city))];

  // 表格列定义
  const columns: ColumnsType<MarketResearch> = [
    {
      title: "城市",
      dataIndex: "city",
      key: "city",
      width: 100,
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
      render: (price: string) => `¥${parseFloat(price).toFixed(2)}`,
    },
    {
      title: "调研日期",
      dataIndex: "research_date",
      key: "research_date",
      width: 120,
    },
  ];

  if (!canAnalyze) {
    return (
      <div style={{ padding: 24, textAlign: "center" }}>
        <Typography.Text type="danger">
          暂无权限查看市场调研，请联系管理员分配权限
        </Typography.Text>
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ padding: 48, textAlign: "center" }}>
        <Spin size="large" tip="加载数据中..." />
      </div>
    );
  }

  return (
    <div style={{ padding: 0 }}>
      {/* 筛选器 */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col>
            <Text strong>筛选条件：</Text>
          </Col>
          <Col>
            <Select
              placeholder="选择产品"
              allowClear
              style={{ width: 180 }}
              options={uniqueProducts.map((p) => ({ label: p, value: p }))}
              value={selectedProduct}
              onChange={setSelectedProduct}
            />
          </Col>
          <Col>
            <Select
              placeholder="选择厂商"
              allowClear
              style={{ width: 180 }}
              options={uniqueManufacturers.map((m) => ({ label: m, value: m }))}
              value={selectedManufacturer}
              onChange={setSelectedManufacturer}
            />
          </Col>
          <Col>
            <Select
              placeholder="选择城市"
              allowClear
              style={{ width: 150 }}
              options={uniqueCities.map((c) => ({ label: c, value: c }))}
              value={selectedCity}
              onChange={setSelectedCity}
            />
          </Col>
        </Row>
      </Card>

      {/* 汇总统计卡片 */}
      {summaryStats && (
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col xs={24} sm={12} md={8} lg={4}>
            <Card>
              <Statistic
                title="数据总量"
                value={summaryStats.totalRecords}
                suffix="条"
                valueStyle={{ color: "#1890ff" }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={8} lg={4}>
            <Card>
              <Statistic
                title="平均价格"
                value={summaryStats.avgPrice.toFixed(2)}
                prefix="¥"
                valueStyle={{ color: "#52c41a" }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={8} lg={4}>
            <Card>
              <Statistic
                title="最高价格"
                value={summaryStats.maxPrice.toFixed(2)}
                prefix="¥"
                valueStyle={{ color: "#fa541c" }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={8} lg={4}>
            <Card>
              <Statistic
                title="最低价格"
                value={summaryStats.minPrice.toFixed(2)}
                prefix="¥"
                valueStyle={{ color: "#722ed1" }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={8} lg={4}>
            <Card>
              <Statistic
                title="厂商数量"
                value={summaryStats.totalManufacturers}
                suffix="家"
                valueStyle={{ color: "#13c2c2" }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={8} lg={4}>
            <Card>
              <Statistic
                title="产品种类"
                value={summaryStats.totalProducts}
                suffix="种"
                valueStyle={{ color: "#eb2f96" }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={8} lg={4}>
            <Card>
              <Statistic
                title="覆盖城市"
                value={summaryStats.totalCities}
                suffix="个"
                valueStyle={{ color: "#2f54eb" }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 图表区域 */}
      {data.length === 0 ? (
        <Card style={{ minHeight: 400 }}>
          <Empty description="暂无调研数据" />
        </Card>
      ) : (
        <>
          {/* 产品价格对比图 + 厂商分布图 */}
          <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
            <Col xs={24} xl={12}>
              <Card title="产品平均价格对比（Top 10）">
                <ResponsiveContainer width="100%" height={350}>
                  <BarChart data={productPriceData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="name"
                      angle={-45}
                      textAnchor="end"
                      interval={0}
                      height={100}
                    />
                    <YAxis label={{ value: "价格 (¥)", angle: -90, position: "insideLeft" }} />
                    <Tooltip
                      formatter={(value: any) => [`¥${value}`, "平均价格"]}
                      labelFormatter={(label) => `产品：${label}`}
                    />
                    <Bar dataKey="value" fill="#1890ff" name="平均价格" />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </Col>
            <Col xs={24} xl={12}>
              <Card title="厂商数据量分布（Top 10）">
                <ResponsiveContainer width="100%" height={350}>
                  <BarChart data={manufacturerData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="name"
                      angle={-45}
                      textAnchor="end"
                      interval={0}
                      height={100}
                    />
                    <YAxis label={{ value: "数据量 (条)", angle: -90, position: "insideLeft" }} />
                    <Tooltip
                      formatter={(value: any) => [value, "数据量"]}
                      labelFormatter={(label) => `厂商：${label}`}
                    />
                    <Bar dataKey="value" fill="#722ed1" name="数据量" />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          </Row>

          {/* 城市分布饼图 + 价格趋势图 */}
          <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
            <Col xs={24} xl={12}>
              <Card title="城市数据分布">
                <ResponsiveContainer width="100%" height={350}>
                  <PieChart>
                    <Pie
                      data={cityDistributionData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {cityDistributionData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: any) => [value, "数据量"]} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </Card>
            </Col>
            <Col xs={24} xl={12}>
              <Card title="平均价格月度趋势">
                <ResponsiveContainer width="100%" height={350}>
                  <LineChart data={trendData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" label={{ value: "月份", position: "insideBottom", offset: -10 }} />
                    <YAxis label={{ value: "价格 (¥)", angle: -90, position: "insideLeft" }} />
                    <Tooltip
                      formatter={(value: any) => [`¥${value}`, "平均价格"]}
                      labelFormatter={(label) => `月份：${label}`}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="avgPrice"
                      stroke="#52c41a"
                      strokeWidth={2}
                      name="平均价格"
                      activeDot={{ r: 8 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          </Row>
        </>
      )}

      {/* 数据明细表 */}
      <Card title="数据明细">
        <Table
          columns={columns}
          dataSource={data.slice(0, 100)}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${Math.min(total, 100)} 条（显示前 100 条）`,
          }}
          scroll={{ x: 600 }}
        />
      </Card>
    </div>
  );
}
