import type { ReactNode } from "react";

interface Props {
  eyebrow: string;
  title: string;
  note: string;
  children: ReactNode;
  wide?: boolean;
  className?: string;
  badge?: string;
}

export default function Panel({
  eyebrow,
  title,
  note,
  children,
  wide,
  className = "",
  badge,
}: Props) {
  return (
    <article className={`panel ${wide ? "panel--wide" : ""} ${className}`}>
      <header className="panel__header">
        <div>
          <span className="eyebrow">{eyebrow}</span>
          <h3>{title}</h3>
        </div>
        {badge && <span className="panel__badge">{badge}</span>}
      </header>
      <p className="panel__note">{note}</p>
      <div className="panel__body">{children}</div>
    </article>
  );
}
