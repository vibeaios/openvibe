"use client";

import { usePathname } from "next/navigation";

export function Header() {
  const pathname = usePathname();
  const channelSlug = pathname.split("/").filter(Boolean)[0] ?? "general";

  return (
    <header className="flex h-12 items-center border-b border-border bg-surface px-4">
      <div className="flex items-center gap-2">
        <span className="text-muted-foreground">#</span>
        <h2 className="text-sm font-semibold text-foreground">{channelSlug}</h2>
      </div>
    </header>
  );
}
