"use client";

import { Suspense } from "react";
import { ConnectionStatus } from "@/components/ConnectionStatus";
import { Mark } from "@/components/Mark";
import { NavLinks } from "@/components/NavLinks";
import { Sidebar } from "@/components/Sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <a
        href="#desk"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-20 focus:rounded-full focus:bg-brass focus:px-4 focus:py-2 focus:text-sm focus:text-ink"
      >
        Skip to content
      </a>
      <Sidebar />
      <div className="md:pl-60">
        <header className="sticky top-0 z-10 border-b border-line bg-ink/85 backdrop-blur">
          <div className="mx-auto flex max-w-5xl flex-col gap-2 px-4 py-3 sm:px-8 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 md:hidden">
                <Mark className="h-6 w-6 text-brass" />
                <span className="font-serif text-lg">ProofLens</span>
              </div>
              <div className="md:hidden">
                <Suspense fallback={null}>
                  <NavLinks />
                </Suspense>
              </div>
            </div>
            <ConnectionStatus />
          </div>
        </header>
        <main id="desk" className="mx-auto w-full max-w-5xl px-5 py-8 sm:px-8 sm:py-10">
          {children}
        </main>
      </div>
    </div>
  );
}
