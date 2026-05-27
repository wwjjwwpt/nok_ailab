"use client";

import { useState, useEffect, useMemo } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Layout, Menu, Avatar, Dropdown, Typography, theme, Spin } from "antd";
import type { MenuProps } from "antd";
import {
  DashboardOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  TeamOutlined,
  MenuOutlined,
  SafetyOutlined,
  ApartmentOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  PieChartOutlined,
  TableOutlined,
} from "@ant-design/icons";
import { useAuth } from "@/hooks/useAuth";
import { useMenuStore } from "@/stores/menuStore";
import { api } from "@/lib/api";

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

interface MenuItem {
  id: number;
  name: string;
  code: string;
  parent_id: number;
  path?: string;
  icon?: string;
  type: number;
  sort_order: number;
  visible: boolean;
  children?: MenuItem[];
}

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const { menus, setMenus } = useMenuStore();
  const [collapsed, setCollapsed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [openKeys, setOpenKeys] = useState<string[]>([]);
  const {
    token: { colorBgContainer },
  } = theme.useToken();

  // 加载菜单
  useEffect(() => {
    const loadMenus = async () => {
      try {
        const response = await api.menus.tree();
        // API 直接返回数组，没有外层 data 包装
        setMenus((response.data as any[]) || []);
      } catch (error) {
        console.error("加载菜单失败:", error);
      } finally {
        setLoading(false);
      }
    };
    loadMenus();
  }, [setMenus]);

  // 根据当前路径自动打开对应的父菜单
  useEffect(() => {
    // 等待菜单加载完成后再设置 openKeys
    if (!loading) {
      if (pathname.startsWith("/market-research/")) {
        setOpenKeys(["/market-research"]);
      } else if (pathname.startsWith("/system/")) {
        setOpenKeys(["/system"]);
      } else {
        setOpenKeys([]);
      }
    }
  }, [pathname, loading]);

  // 将 Ant Design 图标名称映射到组件
  const getIcon = (iconName?: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      "user": <UserOutlined />,
      "User": <UserOutlined />,
      "setting": <SettingOutlined />,
      "Settings": <SettingOutlined />,
      "dashboard": <DashboardOutlined />,
      "Dashboard": <DashboardOutlined />,
      "team": <TeamOutlined />,
      "Team": <TeamOutlined />,
      "menu": <MenuOutlined />,
      "Menu": <MenuOutlined />,
      "safety": <SafetyOutlined />,
      "Safety": <SafetyOutlined />,
      "apartment": <ApartmentOutlined />,
      "Apartment": <ApartmentOutlined />,
      "database": <DatabaseOutlined />,
      "Database": <DatabaseOutlined />,
      "file": <FileTextOutlined />,
      "File": <FileTextOutlined />,
      "lock": <SafetyOutlined />,
      "Lock": <SafetyOutlined />,
      "users": <TeamOutlined />,
      "Users": <TeamOutlined />,
      "piechart": <PieChartOutlined />,
      "PieChart": <PieChartOutlined />,
      "table": <TableOutlined />,
      "Table": <TableOutlined />,
    };
    if (iconName && iconMap[iconName]) {
      return iconMap[iconName];
    }
    return <SettingOutlined />;
  };

  // 构建菜单项
  const buildMenuItems = useMemo(() => {
    const items: MenuProps["items"] = [];

    // 仪表板菜单（始终显示）
    items.push({
      key: "/dashboard",
      icon: <DashboardOutlined />,
      label: "仪表板",
    });

    // 递归构建子菜单，如果没有任何可见子菜单则不显示父菜单
    const buildChildren = (items: MenuItem[]): any[] => {
      return items
        .filter(m => m.visible === true)
        .map(item => {
          const children = item.children && item.children.length > 0
            ? buildChildren(item.children)
            : undefined;
          return {
            key: item.path || `/system/${item.code}`,
            icon: getIcon(item.icon),
            label: item.name,
            children,
          };
        })
        .filter(item => {
          // 如果有子菜单但子菜单数组为空，说明没有可见的子菜单，过滤掉父菜单
          if (item.children && item.children.length === 0) {
            return false;
          }
          return true;
        });
    };

    // 动态菜单（从后端加载的所有菜单）
    if (menus.length > 0) {
      const dynamicItems = buildChildren(menus);
      items.push(...dynamicItems);
    }

    return items;
  }, [menus]);

  const handleMenuClick: MenuProps["onClick"] = ({ key }) => {
    if (key === "/system") {
      setOpenKeys(["/system"]);
      router.push("/system/user");
    } else if (key === "/market-research") {
      // 采购管理点击时跳转到第一个子菜单
      setOpenKeys(["/market-research"]);
      router.push("/market-research/list");
    } else if (key === "profile") {
      router.push("/system/profile");
    } else {
      router.push(key);
    }
  };

  const logoutItems: MenuProps["items"] = [
    {
      key: "profile",
      icon: <UserOutlined />,
      label: "个人信息",
      onClick: () => router.push("/system/profile"),
    },
    {
      type: "divider",
    },
    {
      key: "logout",
      icon: <LogoutOutlined />,
      label: "退出登录",
      onClick: () => {
        logout();
        router.push("/login");
      },
    },
  ];

  if (loading) {
    return (
      <Layout style={{ minHeight: "100vh", alignItems: "center", justifyContent: "center" }}>
        <Spin size="large" />
      </Layout>
    );
  }

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={(value) => setCollapsed(value)}
        style={{
          background: "#001529",
          overflow: "auto",
          height: "100vh",
          position: "fixed",
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div
          style={{
            height: 64,
            display: "flex",
            alignItems: "center",
            justifyContent: collapsed ? "center" : "center",
            gap: 8,
            background: "#002140",
          }}
        >
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              backgroundColor: "rgba(255,255,255,0.2)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          {!collapsed && <Text style={{ fontSize: 16, fontWeight: 600, color: "white" }}>NOK AI Lab</Text>}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[pathname]}
          openKeys={openKeys}
          onOpenChange={setOpenKeys}
          items={buildMenuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 200, transition: "all 0.2s" }}>
        <Header
          style={{
            background: colorBgContainer,
            padding: "0 24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            position: "sticky",
            top: 0,
            zIndex: 1,
            boxShadow: "0 1px 4px rgba(0,21,41,0.08)",
          }}
        >
          <Text strong style={{ fontSize: 16 }}>
            {pathname === "/dashboard" ? "仪表板" :
             pathname === "/system/user" ? "用户管理" :
             pathname === "/system/role" ? "角色管理" :
             pathname === "/system/menu" ? "菜单管理" :
             pathname === "/system/permission" ? "权限管理" :
             pathname === "/system/dept" ? "部门管理" :
             pathname === "/system/data-scope" ? "数据权限" :
             pathname === "/system/log" ? "日志管理" :
             pathname === "/market-research/list" ? "调研数据" :
             pathname === "/market-research/research" ? "市场调研" :
             pathname.startsWith("/market-research") ? "市场调研" :
             pathname.startsWith("/system/") ? "系统管理" : "系统管理"}
          </Text>
          <Dropdown menu={{ items: logoutItems }} placement="bottomRight" arrow>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                cursor: "pointer",
                padding: "4px 8px",
                borderRadius: 8,
              }}
            >
              <Avatar style={{ backgroundColor: "#1890ff" }} icon={<UserOutlined />} size={32} />
              <Text>{user?.nickname || user?.username || "管理员"}</Text>
            </div>
          </Dropdown>
        </Header>
        <Content
          style={{
            margin: 24,
            padding: 24,
            background: colorBgContainer,
            borderRadius: 8,
            minHeight: "calc(100vh - 112px)",
          }}
        >
          {children}
        </Content>
      </Layout>
    </Layout>
  );
}
