"use client";

import { useState, useMemo, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Layout, Menu, Typography, Avatar, Dropdown, theme, Spin } from "antd";
import {
  SettingOutlined,
  DashboardOutlined,
  UserOutlined,
  TeamOutlined,
  MenuOutlined as MenuIcon,
  SafetyOutlined,
  ApartmentOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from "@ant-design/icons";
import { useAuth } from "@/hooks/useAuth";
import { useMenuStore } from "@/stores/menuStore";
import { api } from "@/lib/api";

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

// 默认菜单配置（后备）
const DEFAULT_MENUS = [
  { key: "/dashboard", icon: <DashboardOutlined />, label: "仪表板" },
  {
    key: "system",
    icon: <SettingOutlined />,
    label: "系统管理",
    children: [
      { key: "/system/user", icon: <UserOutlined />, label: "用户管理" },
      { key: "/system/role", icon: <TeamOutlined />, label: "角色管理" },
      { key: "/system/menu", icon: <MenuIcon />, label: "菜单管理" },
      { key: "/system/permission", icon: <SafetyOutlined />, label: "权限管理" },
      { key: "/system/dept", icon: <ApartmentOutlined />, label: "部门管理" },
      { key: "/system/data-scope", icon: <DatabaseOutlined />, label: "数据权限" },
      { key: "/system/log", icon: <FileTextOutlined />, label: "日志管理" },
    ],
  },
];

interface MenuItem {
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
  children?: MenuItem[];
}

export default function SystemLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const { menus: storeMenus, setMenus } = useMenuStore();
  const [collapsed, setCollapsed] = useState(false);
  const [loading, setLoading] = useState(true);
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  // 使用 store 的 menus
  const menus = storeMenus.length > 0 ? storeMenus : [];

  // 加载用户可访问的菜单
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

  // 将 Ant Design 图标名称映射到组件
  const getIcon = (iconName?: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      "user": <UserOutlined />,
      "User": <UserOutlined />,
      "team": <TeamOutlined />,
      "Team": <TeamOutlined />,
      "users": <TeamOutlined />,
      "Users": <TeamOutlined />,
      "menu": <MenuIcon />,
      "Menu": <MenuIcon />,
      "safety": <SafetyOutlined />,
      "Safety": <SafetyOutlined />,
      "lock": <SafetyOutlined />,
      "Lock": <SafetyOutlined />,
      "apartment": <ApartmentOutlined />,
      "Apartment": <ApartmentOutlined />,
      "database": <DatabaseOutlined />,
      "Database": <DatabaseOutlined />,
      "file": <FileTextOutlined />,
      "File": <FileTextOutlined />,
      "filetext": <FileTextOutlined />,
      "FileText": <FileTextOutlined />,
      "setting": <SettingOutlined />,
      "Settings": <SettingOutlined />,
      "dashboard": <DashboardOutlined />,
      "Dashboard": <DashboardOutlined />,
    };
    if (iconName && iconMap[iconName]) {
      return iconMap[iconName];
    }
    return <MenuIcon />;
  };

  // 构建菜单项
  const buildMenuItems = (items: MenuItem[]): any[] => {
    return items
      .filter(m => m.visible === true)
      .map(item => {
        const itemKey = item.path || `/system/${item.code}`;
        return {
          key: itemKey,
          icon: getIcon(item.icon),
          label: item.name,
          children: item.children && item.children.length > 0 ? buildMenuItems(item.children) : undefined,
        };
      });
  };

  // 当前选中的菜单
  const selectedKey = useMemo(() => {
    return pathname;
  }, [pathname]);

  // 打开的菜单 - 需要匹配菜单项的 key
  const openKeys = useMemo(() => {
    // 检查菜单树，找到包含当前路径的父菜单
    const findParentKey = (items: MenuItem[], path: string): string | null => {
      for (const item of items) {
        const itemKey = item.path || `/system/${item.code}`;
        if (item.children && item.children.length > 0) {
          // 检查当前路径是否是该父菜单下的子菜单
          const isChildPath = item.children.some(child => {
            const childKey = child.path || `/system/${child.code}`;
            return path === childKey;
          });
          if (isChildPath) {
            return itemKey;
          }
        }
      }
      return null;
    };

    // 根据当前路径找到对应的父菜单
    const parentKey = findParentKey(menus, pathname);
    return parentKey ? [parentKey] : [];
  }, [pathname, menus]);

  // 菜单点击处理
  const handleMenuClick = ({ key }: { key: string }) => {
    if (key === "/market-research") {
      // 采购管理点击时跳转到第一个子菜单
      router.push("/market-research/list");
    } else if (key === "/system") {
      // 系统管理点击时跳转到第一个子菜单
      router.push("/system/user");
    } else {
      router.push(key);
    }
  };

  // 用户下拉菜单
  const userMenuItems: any[] = [
    {
      key: "profile",
      icon: <UserOutlined />,
      label: "个人信息",
      onClick: () => router.push("/system/profile"),
    },
    {
      type: "divider",
      key: "divider",
    },
    {
      key: "logout",
      icon: <LogoutOutlined />,
      label: "退出登录",
      onClick: logout,
    },
  ];

  // 构建菜单项（始终定义，避免 Hook 顺序问题）
  const menuItems = useMemo(() => {
    const items: any[] = [];

    // 仪表板菜单（始终显示）
    items.push({
      key: "/dashboard",
      icon: <DashboardOutlined />,
      label: "仪表板",
    });

    // 动态菜单（只有有菜单时才显示，不显示后备菜单）
    if (menus.length > 0) {
      const dynamicItems = buildMenuItems(menus);
      items.push(...dynamicItems);
    }

    return items;
  }, [menus]);

  // 如果没有系统管理菜单权限，重定向到仪表板
  useEffect(() => {
    if (!loading && menus.length === 0 && pathname.startsWith("/system/")) {
      router.push("/dashboard");
    }
  }, [loading, menus, pathname, router]);

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
        trigger={null}
        collapsible
        collapsed={collapsed}
        breakpoint="lg"
        collapsedWidth={48}
        width={160}
        onBreakpoint={(broken) => setCollapsed(broken)}
        style={{
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
            height: 40,
            display: "flex",
            alignItems: "center",
            justifyContent: collapsed ? "center" : "flex-start",
            gap: 8,
            padding: "0 10px",
            color: "white",
            fontSize: 13,
            fontWeight: 600,
            background: "#002140",
          }}
        >
          <div
            style={{
              width: 22,
              height: 22,
              borderRadius: 5,
              backgroundColor: "rgba(255,255,255,0.2)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <svg width="12" height="12" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          {!collapsed && <span style={{ fontSize: 12, overflow: 'hidden', whiteSpace: 'nowrap' }}>NOK AI Lab</span>}
        </div>

        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          openKeys={openKeys}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ fontSize: 12 }}
          inlineIndent={12}
        />
      </Sider>

      <Layout style={{ marginLeft: collapsed ? 48 : 160, transition: "all 0.2s" }}>
        <Header
          style={{
            padding: "0 12px",
            height: 40,
            background: colorBgContainer,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            position: "sticky",
            top: 0,
            zIndex: 1,
            boxShadow: "0 1px 4px rgba(0,21,41,0.08)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            {collapsed ? (
              <MenuUnfoldOutlined
                onClick={() => setCollapsed(false)}
                style={{ fontSize: 14, cursor: "pointer" }}
              />
            ) : (
              <MenuFoldOutlined
                onClick={() => setCollapsed(true)}
                style={{ fontSize: 14, cursor: "pointer" }}
              />
            )}
            <Text strong style={{ fontSize: 13 }}>
              {pathname.startsWith("/system/") ? "系统管理" : "仪表板"}
            </Text>
          </div>

          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight" arrow>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                cursor: "pointer",
                padding: "3px 6px",
                borderRadius: 4,
                transition: "background 0.2s",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "#f5f5f5")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
            >
              <Avatar
                style={{ backgroundColor: "#1890ff" }}
                icon={<UserOutlined />}
                size={22}
              />
              <Text strong style={{ fontSize: 12 }}>
                {user?.nickname || user?.username}
              </Text>
            </div>
          </Dropdown>
        </Header>

        <Content
          style={{
            margin: 8,
            padding: 12,
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
            minHeight: "calc(100vh - 56px)",
          }}
        >
          {children}
        </Content>
      </Layout>
    </Layout>
  );
}
