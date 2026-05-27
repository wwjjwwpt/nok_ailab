"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { Spin, Typography } from "antd";

const { Title } = Typography;

export default function DashboardPage() {
  const router = useRouter();
  const { checkAuth } = useAuth();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth().then((authenticated) => {
      if (!authenticated) {
        router.push("/login");
      }
      setLoading(false);
    });
  }, [checkAuth, router]);

  if (loading) {
    return (
      <div style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center"
      }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <Title level={3}>欢迎使用 NOK AI Lab</Title>
    </div>
  );
}
