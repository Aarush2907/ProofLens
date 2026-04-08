"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Desk", hint: "Save a question" },
  { href: "/history", label: "History", hint: "Saved questions" },
];

export function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <nav className="flex gap-2 md:flex-col" aria-label="Primary">
      {links.map((link) => {
        const active = link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
        return (
          <Link
            key={link.href}
            href={link.href}
            aria-current={active ? "page" : undefined}
            onClick={onNavigate}
            className={`rounded-xl px-3 py-2 text-sm transition-colors ${
              active
                ? "bg-raised text-foreground"
                : "text-muted hover:bg-raised/70 hover:text-foreground"
            }`}
          >
            <span className="block font-medium">{link.label}</span>
            <span className="mt-0.5 hidden text-xs text-muted md:block">{link.hint}</span>
          </Link>
        );
      })}
    </nav>
  );
}
