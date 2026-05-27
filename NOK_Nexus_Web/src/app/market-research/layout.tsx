import MainLayout from "../main-layout";

export default function MarketResearchLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <MainLayout>{children}</MainLayout>;
}
