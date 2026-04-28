import { Component, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 24,
          }}
        >
          <div
            style={{
              maxWidth: 480,
              width: '100%',
              textAlign: 'center',
            }}
          >
            <h1
              style={{
                fontSize: 48,
                fontWeight: 700,
                color: '#F26522',
                marginBottom: 16,
                lineHeight: 1,
              }}
            >
              Ошибка
            </h1>
            <p
              style={{
                fontSize: 15,
                color: 'var(--color-gray-7)',
                marginBottom: 24,
                lineHeight: 1.5,
              }}
            >
              Что-то пошло не так. Попробуйте обновить страницу или вернуться позже.
            </p>
            <button
              onClick={() => window.location.reload()}
              style={{
                padding: '10px 24px',
                borderRadius: 8,
                border: 'none',
                background: '#F26522',
                color: '#fff',
                fontSize: 14,
                fontWeight: 500,
                cursor: 'pointer',
              }}
            >
              Обновить страницу
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
