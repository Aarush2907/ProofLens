import type { Metadata } from "next";
import { Desk } from "@/features/research/Desk";

export const metadata: Metadata = {
  title: "Research desk",
};

export default function HomePage() {
  return <Desk />;
}
