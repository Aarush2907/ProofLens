"use client";

import { Suspense } from "react";
import { Mark } from "@/components/Mark";
import { NavLinks } from "@/components/NavLinks";

export function Sidebar() {
  return (
    <aside className="hidden border-r border-line bg-panel md:fixed md:inset-y-0 md:flex md:w-60 md:flex-col md:px-4 md:pb-20 md:pt-6">
      <div className="flex items-center gap-3 px-2">
        <Mark className="h-8 w-8 text-brass" />
        <div>
          <p className="font-serif text-lg leading-none text-foreground">ProofLens</p>
          <p className="mt-1 text-xs tracking-wide text-muted">Research desk</p>
        </div>
      </div>
      <div className="mt-8">
        <Suspense fallback={<p className="px-3 text-sm text-muted">Loading navigation…</p>}>
          <NavLinks />
        </Suspense>
      </div>
      <p className="mt-auto px-3 text-xs leading-5 text-muted">
        Milestone 1
        <br />
        Questions are saved. Research does not run yet.
      </p>
    </aside>
  );
}
