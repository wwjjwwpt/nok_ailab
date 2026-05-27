"use client";

import { AntdRegistry } from "@ant-design/nextjs-registry";
import zhCN from "antd/locale/zh_CN";
import { ConfigProvider } from "antd";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className="h-full">
      <body className="h-full">
        <AntdRegistry>
          <ConfigProvider locale={zhCN}>
            {children}
          </ConfigProvider>
        </AntdRegistry>
      </body>
    </html>
  );
}
