import type { ReactNode } from 'react';

interface PageLayoutProps {
  title: string;
  actions?: ReactNode;
  children: ReactNode;
}

export function PageLayout({ title, actions, children }: PageLayoutProps) {
  return (
    <div className="page-wrapper">
      <div className="page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h1>{title}</h1>
        {actions && <div style={{ display: 'flex', gap: 8 }}>{actions}</div>}
      </div>
      <div className="page-content">{children}</div>
    </div>
  );
}
