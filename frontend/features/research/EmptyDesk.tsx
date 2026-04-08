import { Mark } from "@/components/Mark";

export function EmptyDesk({
  title,
  body,
}: {
  title: string;
  body: string;
}) {
  return (
    <div className="rounded-2xl border border-dashed border-line bg-panel/60 px-6 py-10 text-center">
      <Mark className="mx-auto h-10 w-10 text-brass/80" />
      <h2 className="mt-4 font-serif text-2xl text-foreground">{title}</h2>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted">{body}</p>
    </div>
  );
}
