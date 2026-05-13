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
        {actions && <div className="page-layout-actions">{actions}</div>}
      </div>
      <div className="page-content page-content-pb">{children}</div>
    </div>
  );
}
