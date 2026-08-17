export function PageHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div className="space-y-3">
      <p className="text-xs font-medium uppercase tracking-[0.3em] text-[var(--muted)]">{eyebrow}</p>
      <div className="max-w-4xl space-y-3">
        <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">{title}</h2>
        <p className="text-base leading-7 text-[var(--muted)] sm:text-lg">{description}</p>
      </div>
    </div>
  );
}
