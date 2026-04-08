import type { Metadata } from "next";
import { History } from "@/features/research/History";

export const metadata: Metadata = {
  title: "Research history",
};

export default function HistoryPage() {
  return <History />;
}
