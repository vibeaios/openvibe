import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { ThreadPanel } from "@/components/layout/thread-panel";
import { WorkspaceInit } from "@/components/workspace-init";

export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <WorkspaceInit />

      {/* Zone 1: Left sidebar */}
      <Sidebar />

      {/* Zone 2: Main content area with header */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto bg-surface">{children}</main>
      </div>

      {/* Zone 3: Detail panel (hidden by default) */}
      <ThreadPanel />
    </div>
  );
}
