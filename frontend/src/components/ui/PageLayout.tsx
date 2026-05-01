import type { ReactNode } from 'react';

interface PageLayoutProps {
  title: string;
  actions?: ReactNode;
  children: ReactNode;
}

export function PageLayout({ title, actions, children }: PageLayoutProps) {
  return (
    <div className="page-wrapper">
      <div className="page-header">
        <h1>{title}</h1>
        {actions && <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>{actions}</div>}
      </div>
      <div className="page-content" style={{ paddingBottom: 40 }}>{children}</div>
    </div>
  );
}
